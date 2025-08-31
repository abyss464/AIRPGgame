# main.py

from manager.prompt_manager import PromptManager
from manager.context_builder import ContextBuilder


def run_demo():
    print("--- 1. 初始化提示词管理器 ---")
    # 每次运行时都会加载（如果存在）或准备创建 prompts.json
    manager = PromptManager("prompts.json")

    print("\n--- 2. 添加一些示例提示词 ---")
    manager.add_prompt(
        name="gm_persona",
        prompt_type="goal",
        content="你是一位经验丰富、富有想象力的游戏主持人（GM），负责引导一场中世纪奇幻冒险。",
        description="定义AI的核心角色"
    )
    manager.add_prompt(
        name="world_setting",
        prompt_type="core_content",
        content="故事发生在一个名为'艾瑞多'的王国，魔法正在衰退，古老的邪恶正在苏醒。",
        description="游戏的基本世界观"
    )
    manager.add_prompt(
        name="no_breaking_character",
        prompt_type="prohibitions",
        content="绝对不要以AI助手的身份说话。始终保持你作为GM的身份。",
        description="关键的角色扮演规则"
    )
    manager.add_prompt(
        name="json_output_format",
        prompt_type="response_structure",
        content="你的回复必须是严格的JSON格式，包含'description'和'choices'两个键。",
        description="规定AI的输出格式以方便程序解析"
    )
    manager.add_prompt(
        name="combat_rules",
        prompt_type="core_content",
        content="战斗采用简化的回合制。玩家行动后，怪物会立即反击。",
        description="游戏的核心规则"
    )

    # 保存到文件
    manager.save_prompts()
    print("已添加5个提示词并保存到 prompts.json")

    print("\n--- 3. 初始化提示词构造器 ---")
    builder = ContextBuilder(manager)

    print("\n--- 4. 构造一个用于'探索场景'的系统提示词 ---")
    # 我们选择需要的提示词名称
    exploration_prompt_names = [
        "gm_persona",
        "world_setting",
        "no_breaking_character",
        "json_output_format"
    ]

    final_system_prompt = builder.build(exploration_prompt_names)

    print("=" * 50)
    print("生成的系统提示词 (默认顺序):")
    print("=" * 50)
    print(final_system_prompt)
    print("=" * 50)

    print("\n--- 5. 构造一个用于'战斗场景'的系统提示词（包含更多内容）---")
    combat_prompt_names = [
        "gm_persona",
        "world_setting",
        "combat_rules",  # <-- 添加了战斗规则
        "no_breaking_character",
        "json_output_format"
    ]

    final_combat_prompt = builder.build(combat_prompt_names)

    print("=" * 50)
    print("生成的战斗系统提示词:")
    print("=" * 50)
    print(final_combat_prompt)
    print("=" * 50)

    print("\n--- 6. 演示自定义顺序 ---")
    custom_order = ["response_structure", "goal", "core_content", "prohibitions"]
    custom_order_prompt = builder.build(combat_prompt_names, custom_order=custom_order)

    print("=" * 50)
    print("生成的系统提示词 (自定义顺序):")
    print("=" * 50)
    print(custom_order_prompt)
    print("=" * 50)


if __name__ == "__main__":
    run_demo()
