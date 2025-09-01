# GameController.py
import json
import os
from typing import List, Dict, Any, Optional

from PySide6.QtCore import QObject, Signal, QMutex, QWaitCondition, Slot

from core.ModelLinker import ModelLinker
from manager.model_config_manager import ModelConfigManager


class GameController(QObject):
    """
    一个强大的游戏流程控制器，能够加载、运行、保存和继续基于JSON定义的工作流。
    此类被设计为在工作线程中运行，通过信号与主UI线程通信，并使用非阻塞的事件驱动循环。
    """
    ai_response = Signal(str)
    input_requested = Signal(str)
    game_finished = Signal()

    _process_next_node_signal = Signal()

    def __init__(self, workflow_file_path: str = "workflows.json"):
        super().__init__()
        self.modelmanager = ModelConfigManager()
        self.model_linker = ModelLinker(self.modelmanager)
        self.workflows = self._load_workflows(workflow_file_path)

        # 游戏状态变量
        self.current_workflow_name: Optional[str] = None
        self.current_workflow_data: Optional[Dict] = None
        self.base_path: Optional[str] = None
        self.context: List[Dict[str, str]] = []

        # 用于断点续玩的状态索引
        self.node_keys: List[str] = []
        self.current_node_index: int = 0

        # --- 线程同步机制 ---
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.user_input: Optional[str] = None
        self.is_stopped = False
        self._process_next_node_signal.connect(self._process_next_node)

    def _load_workflows(self, file_path: str) -> Dict[str, Any]:
        """从文件加载所有工作流。"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Controller] 错误: 无法加载或解析工作流文件: {file_path} - {e}")
            return {}

    # --- 公共槽函数(Slots)，由UI线程通过信号调用 ---
    def run(self, workflow_name: str):
        """槽函数：开始一个全新的游戏流程。"""
        self.is_stopped = False
        workflow_id = self._find_workflow_by_name(workflow_name)
        if not workflow_id:
            print(f"[Controller] 错误：找不到名为 '{workflow_name}' 的流程。")
            self.game_finished.emit()
            return

        self._setup_game_state(workflow_id)
        self.node_keys = list(self.current_workflow_data.get("nodes", {}).keys())
        print(f"[Controller] 开始新游戏: '{self.current_workflow_name}'...")
        # 【关键】启动事件驱动的流程
        self._process_next_node_signal.emit()

    def load_and_run(self, workflow_name: str, slot_name: str = "autosave"):
        """槽函数：加载一个已保存的游戏并从断点处继续。"""
        self.is_stopped = False
        workflow_id = self._find_workflow_by_name(workflow_name)
        if not workflow_id:
            print(f"[Controller] 错误：找不到名为 '{workflow_name}' 的流程。")
            self.game_finished.emit()
            return

        self._setup_game_state(workflow_id)
        self.node_keys = list(self.current_workflow_data.get("nodes", {}).keys())

        save_file = os.path.join(self.base_path, "saves", f"{slot_name}.json")
        if not os.path.exists(save_file):
            print(f"[Controller] 错误：在 '{self.current_workflow_name}' 中找不到存档 '{slot_name}'。将开始新游戏。")
            self._process_next_node_signal.emit()
            return

        try:
            with open(save_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            self.current_node_index = save_data.get("current_node_index", 0)
            self.context = save_data.get("context", [])
            print(f"[Controller] 成功加载游戏: '{self.current_workflow_name}' (存档: {slot_name})...")
            # 【关键】从加载点启动事件驱动的流程
            self._process_next_node_signal.emit()
        except Exception as e:
            print(f"[Controller] 加载存档失败: {e}")
            self.game_finished.emit()

    def stop_game(self):
        """优雅地停止游戏循环。"""
        self.is_stopped = True
        self.wait_condition.wakeAll()  # 确保如果卡在输入等待，也能被唤醒并停止

    def submit_user_input(self, text: str):
        """接收来自UI的用户输入并唤醒等待的_get_user_input方法。"""
        self.mutex.lock()
        self.user_input = text
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    # --- 核心游戏流程 ---
    @Slot()
    def _process_next_node(self):
        """
        游戏流程的核心驱动。
        处理单个节点，然后通过信号异步地调度下一次调用，从而避免阻塞线程。
        """
        # 检查游戏是否应该结束
        if self.is_stopped or self.current_node_index >= len(self.node_keys):
            status = "被用户停止" if self.is_stopped else "执行完毕"
            print(f"[Controller] 流程{status}。")
            self.game_finished.emit()
            return

        node_key = self.node_keys[self.current_node_index]
        node_data = self.current_workflow_data.get("nodes", {})[node_key]
        print(f"[Controller] ==> 进入节点: {node_data.get('name', '未命名')} (索引: {self.current_node_index})")

        # 执行当前节点内的所有同步任务
        self._execute_node(node_data)

        # 如果在节点执行期间被停止，则立即退出
        if self.is_stopped:
            print("[Controller] 流程在节点执行中被停止。")
            self.game_finished.emit()
            return

        # 检查当前节点是否需要循环。如果不需要，则将索引指向下一个节点。
        is_loop_node = node_data.get("loop", False)
        if not is_loop_node:
            self.current_node_index += 1
            print("[Controller] 节点执行完成，准备进入下一个节点。")
        else:
            print(f"[Controller] 节点 '{node_data.get('name', '未命名')}' 将循环执行。")

        self.save_game("autosave")

        self._process_next_node_signal.emit()

    def _execute_node(self, node_data: Dict[str, Any]):
        """
        执行单个节点内的所有步骤。此函数是同步的，执行完毕后返回。
        """
        if self.is_stopped: return

        steps = node_data.get("steps", [])
        parallel_steps = [s for s in steps if s.get("parallel_execution", False)]
        sequential_steps = [s for s in steps if not s.get("parallel_execution", False)]

        if parallel_steps:
            print(f"[Controller] -> 开始并行执行 {len(parallel_steps)} 个步骤...")
            for step in parallel_steps:
                if self.is_stopped: break
                self._execute_step(step)
            print("[Controller] -> 并行步骤执行完毕。")

        if self.is_stopped: return

        for step in sequential_steps:
            if self.is_stopped: break
            self._execute_step(step)

    def _execute_step(self, step_data: Dict[str, Any]):
        """执行一个单独的步骤，包括构建提示、调用AI、处理结果等。"""
        step_name = step_data.get('name', '未命名')
        print(f"[Controller] ----> 执行步骤: {step_name}...")

        messages, user_input_for_context = self._build_messages(step_data)

        if messages is None:  # 在等待用户输入时游戏被停止
            return

        if not any(msg['role'] == 'user' for msg in messages):
            print(f"[Controller] 步骤 '{step_name}' 被跳过：没有可执行的提示或用户交互。")
            return

        ai_response = self.model_linker.create_completion(
            messages=messages,
            provider_name=step_data.get("provider"),
            model=step_data.get("model")
        )

        if not ai_response:
            print(f"[Controller] 步骤 '{step_name}' 未能从AI获取响应。")
            return

        if step_data.get("output_to_console", True):
            self.ai_response.emit(ai_response)

        if step_data.get("save_to_file"):
            self._write_file(step_data["save_to_file"], ai_response)

        if step_data.get("save_to_context", False):
            if user_input_for_context is not None:
                # 情况 1: 存在真实的用户输入。
                # 行为: 像之前一样，保存标准的 user/assistant 对话轮次。
                self.context.append({"role": "user", "content": user_input_for_context})
                self.context.append({"role": "assistant", "content": ai_response})
                print("[Controller] [Context] 已追加新的 user/assistant 对话轮次。")
            else:
                # 情况 2: 不存在真实的用户输入（即使用了系统占位符）。
                # 我们需要将此AI响应合并到上一个AI响应中，或创建一个新的AI响应。
                if self.context and self.context[-1].get("role") == "assistant":
                    # 子情况 2a: 上一条历史记录是AI的回复。
                    # 行为: 将本次AI的回复追加到上一次回复的末尾。这对于AI的多步骤自我思考很有用。
                    self.context[-1]["content"] += f"\n\n{ai_response}"
                    print("[Controller] [Context] 已将AI响应合并到上一条助理消息中。")
                else:
                    # 子情况 2b: 上下文为空，或上一条不是AI的回复（例如，是一个user的回复）。
                    # 行为: 创建一个全新的、以AI回复开始的历史记录。
                    self.context.append({"role": "assistant", "content": ai_response})
                    print("[Controller] [Context] 已添加一条新的、仅包含AI的对话历史。")

            self._save_context_file()

    def _get_user_input(self, prompt_message: str) -> Optional[str]:
        """向UI请求输入，并使用QWaitCondition阻塞当前工作线程直到获得输入。"""
        self.mutex.lock()
        self.user_input = None
        self.input_requested.emit(prompt_message)
        # 阻塞并等待，直到UI线程调用submit_user_input并唤醒它
        self.wait_condition.wait(self.mutex)
        result = self.user_input
        self.mutex.unlock()
        return result

    def _build_messages(self, step_data: Dict[str, Any]) -> (Optional[List[Dict[str, str]]], Optional[str]):
        messages = []
        system_prompt_parts = []
        user_input_for_context: Optional[str] = None
        has_actionable_prompt = False

        # 1. 构建系统提示
        prompt_content = step_data.get("prompt", "")
        if prompt_content:
            has_actionable_prompt = True
            system_prompt_parts.append(prompt_content)

        file_to_read = step_data.get("read_from_file")
        if file_to_read:
            content = self._read_file(file_to_read)
            if content:
                has_actionable_prompt = True
                system_prompt_parts.append(f"\n--- 参考资料: {file_to_read} ---\n{content}")

        final_system_prompt = "\n".join(filter(None, system_prompt_parts)).strip()
        if final_system_prompt:
            messages.append({"role": "system", "content": final_system_prompt})

        # 2. 加载历史对话上下文
        if step_data.get("use_context"):
            messages.extend(self.context)

        # 3. 获取用户输入 或 使用占位符
        if step_data.get("use_user_context", False):
            # 情况 A: 需要真实的用户输入
            user_input_content = self._get_user_input("请输入你的行动:")
            if self.is_stopped:
                return None, None

            if user_input_content is not None:
                user_input_for_context = user_input_content
                messages.append({"role": "user", "content": user_input_content})

        elif has_actionable_prompt:
            # 【全新逻辑】
            # 情况 B: 不需要用户输入，但有系统提示，说明AI应主动行动。
            # 我们使用一个占位符来触发AI的响应。
            # 这个占位符可以从JSON配置，否则使用默认值。
            placeholder = step_data.get("placeholder_prompt", "继续。")
            messages.append({"role": "user", "content": placeholder})
            # 关键：此时 user_input_for_context 仍然是 None，所以这个占位符不会被存入历史。

        return messages, user_input_for_context

    # --- 辅助方法 ---
    def save_game(self, slot_name: str = "autosave"):
        if not self.current_workflow_name: return
        try:
            save_dir = os.path.join(self.base_path, "saves")
            os.makedirs(save_dir, exist_ok=True)
            save_file = os.path.join(save_dir, f"{slot_name}.json")
            save_data = {
                "workflow_name": self.current_workflow_name,
                "current_node_index": self.current_node_index,
                "context": self.context
            }
            with open(save_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Controller] 保存游戏失败: {e}")

    def _find_workflow_by_name(self, name: str) -> Optional[str]:
        for wf_id, wf_data in self.workflows.items():
            if wf_data.get("name") == name: return wf_id
        return None

    def _setup_game_state(self, workflow_id: str):
        self.current_workflow_data = self.workflows[workflow_id]
        self.current_workflow_name = self.current_workflow_data['name']
        self.base_path = os.path.join("aifile", self.current_workflow_name)
        os.makedirs(self.base_path, exist_ok=True)
        self.context = []
        self.current_node_index = 0

    def _read_file(self, filename: str) -> Optional[str]:
        file_path = os.path.join(self.base_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"[Controller] 警告: 读取文件失败，路径不存在: {file_path}")
            return None

    def _write_file(self, filename: str, content: str):
        file_path = os.path.join(self.base_path, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f: f.write(content)
        print(f"[Controller] [文件操作] -> 已将内容写入 {file_path}")

    def _save_context_file(self):
        context_path = os.path.join(self.base_path, "context.json")
        with open(context_path, 'w', encoding='utf-8') as f: json.dump(self.context, f, ensure_ascii=False, indent=4)
        print("[Controller] [文件操作] -> 已更新 context.json")
