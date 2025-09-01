# GameController.py
import json
import os
import time
from typing import List, Dict, Any, Optional

from PySide6.QtCore import QObject, Signal, QMutex, QWaitCondition

# 假设这些类存在于您的项目结构中
from core.ModelLinker import ModelLinker
from manager.model_config_manager import ModelConfigManager


class GameController(QObject):
    """
    一个强大的游戏流程控制器，能够加载、运行、保存和继续基于JSON定义的工作流。
    此类被设计为在工作线程中运行，通过信号与主UI线程通信。
    """
    # --- UI通信信号 ---
    # MODIFICATION: 移除了 log_message 信号，调试信息将使用 print
    # log_message = Signal(str)
    ai_response = Signal(str)
    input_requested = Signal(str)
    game_finished = Signal()

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

    def _load_workflows(self, file_path: str) -> Dict[str, Any]:
        """从文件加载所有工作流。"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # MODIFICATION: 使用 print 输出错误
            print(f"[Controller] 错误: 无法加载或解析工作流文件: {file_path} - {e}")
            return {}

    # --- 公共槽函数(Slots)，由UI线程调用以启动游戏 ---
    def run(self, workflow_name: str):
        """槽函数：开始一个全新的游戏流程。"""
        self.is_stopped = False
        workflow_id = self._find_workflow_by_name(workflow_name)
        if not workflow_id:
            # MODIFICATION: 使用 print 输出错误
            print(f"[Controller] 错误：找不到名为 '{workflow_name}' 的流程。")
            self.game_finished.emit()
            return

        self._setup_game_state(workflow_id)
        # MODIFICATION: 使用 print 输出调试信息
        print(f"[Controller] 开始新游戏: '{self.current_workflow_name}'...")
        self._game_loop()

    def load_and_run(self, workflow_name: str, slot_name: str = "autosave"):
        """槽函数：加载一个已保存的游戏并从断点处继续。"""
        self.is_stopped = False
        workflow_id = self._find_workflow_by_name(workflow_name)
        if not workflow_id:
             # MODIFICATION: 使用 print 输出错误
            print(f"[Controller] 错误：找不到名为 '{workflow_name}' 的流程。")
            self.game_finished.emit()
            return

        self._setup_game_state(workflow_id)
        save_file = os.path.join(self.base_path, "saves", f"{slot_name}.json")
        if not os.path.exists(save_file):
            # MODIFICATION: 使用 print 输出错误
            print(f"[Controller] 错误：在 '{self.current_workflow_name}' 中找不到存档 '{slot_name}'。")
            self.game_finished.emit()
            return

        try:
            with open(save_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            self.current_node_index = save_data.get("current_node_index", 0)
            self.context = save_data.get("context", [])
            # MODIFICATION: 使用 print 输出调试信息
            print(f"[Controller] 成功加载游戏: '{self.current_workflow_name}' (存档: {slot_name})...")
            self._game_loop()
        except Exception as e:
            # MODIFICATION: 使用 print 输出错误
            print(f"[Controller] 加载存档失败: {e}")
            self.game_finished.emit()

    def stop_game(self):
        """停止游戏循环。"""
        self.is_stopped = True
        self.wait_condition.wakeAll()

    def submit_user_input(self, text: str):
        """槽函数：接收来自UI的用户输入并唤醒游戏循环。"""
        self.mutex.lock()
        self.user_input = text
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    # --- 核心游戏逻辑 ---
    def _game_loop(self):
        """游戏的主循环，根据当前状态索引执行节点。"""
        nodes = self.current_workflow_data.get("nodes", {})
        self.node_keys = list(nodes.keys())

        while self.current_node_index < len(self.node_keys):
            if self.is_stopped:
                break

            node_key = self.node_keys[self.current_node_index]
            node_data = nodes[node_key]
            # MODIFICATION: 使用 print 输出调试信息
            print(f"[Controller] ==> 进入节点: {node_data.get('name', '未命名')}")
            self._execute_node(node_data)

            self.current_node_index += 1
            if not self.is_stopped:
                self.save_game("autosave")

            time.sleep(0.02)

        if not self.is_stopped:
            # MODIFICATION: 使用 print 输出调试信息
            print("[Controller] 流程执行完毕。")
        else:
            # MODIFICATION: 使用 print 输出调试信息
            print("[Controller] 流程被用户停止。")
        self.game_finished.emit()

    def _execute_node(self, node_data: Dict[str, Any]):
        """执行单个节点内的所有步骤，处理并行与顺序逻辑。"""
        while True:
            if self.is_stopped: break
            steps = node_data.get("steps", [])

            parallel_steps = [s for s in steps if s.get("parallel_execution", False)]
            sequential_steps = [s for s in steps if not s.get("parallel_execution", False)]

            if parallel_steps:
                # MODIFICATION: 使用 print 输出调试信息
                print(f"[Controller] -> 开始并行执行 {len(parallel_steps)} 个步骤...")
                for step in parallel_steps:
                    if self.is_stopped: break
                    self._execute_step(step)
                # MODIFICATION: 使用 print 输出调试信息
                print("[Controller] -> 并行步骤执行完毕。")

            if self.is_stopped: break

            for step in sequential_steps:
                if self.is_stopped: break
                self._execute_step(step)

            if not node_data.get("loop", False):
                break

    def _execute_step(self, step_data: Dict[str, Any]):
        step_name = step_data.get('name', '未命名')
        # MODIFICATION: 使用 print 输出调试信息
        print(f"[Controller] ----> 执行步骤: {step_name}...")

        messages, user_content_for_context = self._build_messages(step_data)
        if messages is None:
            return

        if not messages or messages[-1].get("role") != "user":
            # MODIFICATION: 使用 print 输出调试信息
            print(
                f"[Controller] 步骤 '{step_name}' 被跳过：没有有效的用户提示可发送给AI。")
            return

        ai_response = self.model_linker.create_completion(
            messages=messages,
            provider_name=step_data.get("provider"),
            model=step_data.get("model")
        )

        if not ai_response:
            # MODIFICATION: 使用 print 输出调试信息
            print(f"[Controller] 步骤 '{step_name}' 未能从AI获取响应。请检查API密钥和网络连接。")
            return

        # 这是唯一保留的信号，用于将AI回复发送给UI
        if step_data.get("output_to_console", True):
            self.ai_response.emit(ai_response)

        if step_data.get("save_to_file"):
            self._write_file(step_data["save_to_file"], ai_response)

        if step_data.get("save_to_context", False):
            self.context.append({"role": "user", "content": user_content_for_context})
            self.context.append({"role": "assistant", "content": ai_response})
            self._save_context_file()

    def _get_user_input(self, prompt_message: str) -> Optional[str]:
        self.mutex.lock()
        self.user_input = None
        self.input_requested.emit(prompt_message)
        self.wait_condition.wait(self.mutex)
        result = self.user_input
        self.mutex.unlock()
        return result

    def _build_messages(self, step_data: Dict[str, Any]):
        messages = []
        prompt_parts = []

        if step_data.get("use_context"):
            messages.extend(self.context)

        prompt_parts.append(step_data.get("prompt", ""))

        file_to_read = step_data.get("read_from_file")
        if file_to_read:
            content = self._read_file(file_to_read)
            if content:
                prompt_parts.append(f"\n--- 参考资料: {file_to_read} ---\n{content}")

        if step_data.get("use_user_context", False):
            user_input = self._get_user_input("请输入你的行动:")
            if self.is_stopped: return None, None

            user_input = user_input or ""
            prompt_parts.append(f"\n--- 玩家行动 ---\n{user_input}")

        final_prompt = "\n".join(prompt_parts).strip()
        if final_prompt:
            messages.append({"role": "user", "content": final_prompt})

        return messages, final_prompt

    def save_game(self, slot_name: str = "autosave"):
        if not self.current_workflow_name: return
        save_dir = os.path.join(self.base_path, "saves")
        os.makedirs(save_dir, exist_ok=True)
        save_file = os.path.join(save_dir, f"{slot_name}.json")
        save_data = {"workflow_name": self.current_workflow_name, "current_node_index": self.current_node_index,
                     "context": self.context}
        try:
            with open(save_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            # MODIFICATION: 使用 print 输出错误
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
            # MODIFICATION: 使用 print 输出警告
            print(f"[Controller] 警告: 读取文件失败，路径不存在: {file_path}")
            return None

    def _write_file(self, filename: str, content: str):
        file_path = os.path.join(self.base_path, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f: f.write(content)
        # MODIFICATION: 使用 print 输出文件操作信息
        print(f"[Controller] [文件操作] -> 已将内容写入 {file_path}")

    def _save_context_file(self):
        context_path = os.path.join(self.base_path, "context.json")
        with open(context_path, 'w', encoding='utf-8') as f: json.dump(self.context, f, ensure_ascii=False, indent=4)
