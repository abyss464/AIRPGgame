# GameController.py
import json
import os
from typing import List, Dict, Any, Optional, Tuple

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

        self.pending_user_input: Optional[str] = None

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
            print(f"[Controller] 流程 {status}。")
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

        # ======== 新增/修改的逻辑：处理节点循环 ========
        loop_until_condition = node_data.get("loop_until_condition_met", False)
        loop_condition = node_data.get("loop_condition")

        if loop_until_condition and loop_condition:
            # 情况1: 条件循环
            print(f"[Controller] 正在检查节点 '{node_data.get('name', '未命名')}' 的循环条件: '{loop_condition}'")
            condition_met = self._check_loop_condition(loop_condition)
            if condition_met:
                self.current_node_index += 1
                print(f"[Controller] ✅ 条件满足，节点循环结束，准备进入下一节点。")
            else:
                # 索引保持不变，以重复当前节点
                print(f"[Controller] ❌ 条件未满足，将重复执行当前节点。")
        elif node_data.get("loop", False):
            # 情况2: 无限循环 (旧逻辑)
            # 索引保持不变
            print(f"[Controller] 节点 '{node_data.get('name', '未命名')}' 将无限循环执行。")
        else:
            # 情况3: 非循环节点
            self.current_node_index += 1
            print("[Controller] 节点执行完成，准备进入下一个节点。")

        # ===============================================

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
        """
        【V4.1 逻辑】执行一个单独的步骤，遵循“输出 -> 输入”模型。
        1. AI首先根据上下文和提示生成内容并输出。
        2. 然后，根据步骤配置（loop 或 use_user_context），决定是否等待用户输入。
        3. 用户的输入将被保存到上下文中，供下一个步骤无缝使用。
        """
        step_name = step_data.get('name', '未命名')
        print(f"[Controller] ----> 执行步骤: {step_name}...")

        # --- 1. AI生成与输出阶段 ---
        messages, is_new_turn = self._build_messages(step_data)

        # 如果没有任何可执行内容（例如，只有一个空的system prompt），则跳过AI
        if len(messages) <= 1 and not any(m['role'] == 'user' for m in messages):
            print(f"[Controller] 步骤 '{step_name}' 无可执行内容，跳过AI生成。")
            ai_response = None
        else:
            ai_response = self.model_linker.create_completion(
                messages=messages,
                provider_name=step_data.get("provider"),
                model=step_data.get("model")
            )

        save_context_flag = step_data.get("save_to_context", False)

        if ai_response:
            if step_data.get("output_to_console", True):
                self.ai_response.emit(ai_response)
            if step_data.get("save_to_file"):
                self._write_file(step_data["save_to_file"], ai_response)

            # 保存AI响应到上下文（合并或新增）
            if save_context_flag:
                if is_new_turn:
                    # 如果是真实用户输入开启的新回合，则添加新的assistant消息
                    self.context.append({"role": "assistant", "content": ai_response})
                    print("[Controller] [Context] 已追加新的 assistant 对话。")
                else:
                    # 否则，与上一条assistant消息合并
                    if self.context and self.context[-1].get("role") == "assistant":
                        self.context[-1]["content"] += f"\n\n{ai_response}"
                        print("[Controller] [Context] 已将AI响应合并到上一条助理消息中。")
                    else:
                        # 如果是第一条消息，则直接添加
                        self.context.append({"role": "assistant", "content": ai_response})
                        print("[Controller] [Context] 已添加首条 assistant 对话。")

        # --- 2. 用户输入处理阶段 ---
        user_input_for_next_step: Optional[str] = None

        # 情况A: 条件循环
        if step_data.get("loop_until_condition_met", False):
            loop_condition = step_data.get("loop_condition")
            if not loop_condition:
                print(f"[Controller] 错误: 循环步骤 '{step_name}' 缺少 'loop_condition'。")
                return

            iteration = 1
            while not self.is_stopped:
                print(f"[Controller] ----> 等待用户输入以满足条件 '{loop_condition}' (第 {iteration} 次尝试)...")
                user_input = self._get_user_input("请输入你的行动:")
                if self.is_stopped or user_input is None: return

                # 临时将输入放入一个字典中，以便条件检查器工作
                temp_context_for_check = self.context + [{"role": "user", "content": user_input}]
                if self._check_loop_condition(loop_condition, temp_context_for_check):
                    print(f"[Controller] ✅ 条件被用户输入满足！结束循环。")
                    user_input_for_next_step = user_input
                    break  # 成功，退出while循环
                else:
                    print(f"[Controller] ❌ 条件未被满足，请重试。")
                    # 可选：可以输出一个固定的重试提示
                    self.ai_response.emit("这似乎不对，再试试其他方法。")
                iteration += 1

        # 情况B: 普通的用户输入请求
        elif step_data.get("use_user_context", False):
            user_input_for_next_step = self._get_user_input("请输入你的行动:")
            if self.is_stopped: return

        # --- 3. 保存用户输入并结束步骤 ---
        if user_input_for_next_step is not None and save_context_flag:
            self.context.append({"role": "user", "content": user_input_for_next_step})
            print("[Controller] [Context] 已追加用户输入，将用于下一步骤。")

        if save_context_flag:
            self._save_context_file()

    # --- 辅助方法 ---

    def _check_loop_condition(self, condition: str, context_to_check: Optional[List[Dict[str, str]]] = None) -> bool:
        """
        【全新辅助方法】
        调用AI模型来判断给定的循环条件是否在当前上下文中得到满足。

        Args:
            condition (str): 需要检查的条件文本。
            context_to_check (Optional[List[Dict[str, str]]]): 用于检查的特定上下文。如果为None，则使用 self.context。
        """
        # 决定使用哪个上下文进行检查：如果传入了临时上下文，则使用它，否则使用实例的默认上下文。
        current_context = context_to_check if context_to_check is not None else self.context

        if not current_context:
            print("[Controller] [LoopCheck] 上下文为空，无法判断条件，默认返回 False。")
            return False

        # 构造一个专门用于判断的、临时的消息列表
        prompt = f"请问以上对话中：“{condition}”这个条件是否已经完成？你只需要回答 True 或者 False，禁止回答其他任何内容。"

        # 使用指定的上下文，并附加我们的判断问题
        messages_for_check = current_context + [{"role": "user", "content": prompt}]

        print(f"[Controller] [LoopCheck] 向AI发送条件检查请求...")

        # 为了节约成本和提高速度，可以使用一个比较轻量级的模型进行判断
        # 如果未指定，则使用默认模型
        response = self.model_linker.create_completion(messages=messages_for_check,
                                                       provider_name=self.modelmanager.get_default_provider_name(),
                                                       model=self.modelmanager.get_default_provider_model())

        if not response:
            print("[Controller] [LoopCheck] 未能从AI获取条件检查的响应，默认返回 False。")
            return False

        # 对AI的回答进行严格解析
        cleaned_response = response.strip().lower()
        print(f"[Controller] [LoopCheck] AI对条件的判断结果为: '{cleaned_response}'")

        return cleaned_response == 'true'

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

    def _build_messages(self, step_data: Dict[str, Any]) -> Tuple[List[Dict[str, str]], bool]:
        """
        【V4.1 逻辑】构建发送给AI的消息列表。
        - 它的核心职责是准备AI的“思考材料”。
        - 新增逻辑：如果上下文中最后一条消息是AI的，它会自动插入一个占位符用户消息来驱动AI。
        - 返回值：(消息列表, 是否是真实用户开启的回合)
        """
        messages = []
        is_following_real_user_input = False

        # 1. 构建系统提示 (逻辑不变)
        system_prompt_parts = []
        prompt_content = step_data.get("prompt", "")
        if prompt_content:
            system_prompt_parts.append(prompt_content)

        file_to_read = step_data.get("read_from_file")
        if file_to_read:
            content = self._read_file(file_to_read)
            if content:
                system_prompt_parts.append(f"\n--- 参考资料: {file_to_read} ---\n{content}")

        final_system_prompt = "\n".join(filter(None, system_prompt_parts)).strip()
        if final_system_prompt:
            messages.append({"role": "system", "content": final_system_prompt})

        # 2. 加载历史对话上下文
        if step_data.get("use_context"):
            messages.extend(self.context)

        # 3. 决定是否需要占位符
        #    检查上下文中最后一条消息是否来自用户。
        if self.context and self.context[-1].get("role") == "user":
            is_following_real_user_input = True
        else:
            # 如果没有历史，或者最后一条是AI说的，我们需要一个占位符来让AI继续
            # 只有当有实际的prompt需要AI响应时，才添加占位符
            if prompt_content or file_to_read:
                placeholder = step_data.get("placeholder_prompt", "继续。")
                messages.append({"role": "user", "content": placeholder})
                print(f"[Controller] [Context] 上下文末尾非用户输入，已自动添加占位符: '{placeholder}'")
            is_following_real_user_input = False

        return messages, is_following_real_user_input


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
