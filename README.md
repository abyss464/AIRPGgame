# AI-Powered Text RPG Framework

这是一个基于 PySide6 构建的高度可扩展的桌面应用程序，用于创建和运行由大型语言模型（LLM）驱动的动态文本角色扮演游戏（RPG）。它不仅仅是一个游戏，更是一个强大的框架，允许用户通过可视化的流程编辑器设计复杂的游戏逻辑和AI交互，而无需编写任何代码。

## ✨ 核心特性

*   **模块化架构**: 采用类MVC（模型-视图-控制器）的设计模式，将UI（Views）、应用逻辑（Controllers）和数据管理（Managers）清晰分离，易于维护和扩展。
*   **工作流驱动的游戏逻辑**: 游戏的核心流程不是硬编码的，而是通过一个灵活的、分层的JSON结构来定义。用户可以创建自己的“剧本”。
*   **强大的工作流编辑器**:
    *   **分层结构**: `流程 (Workflow) -> 节点 (Node) -> 流节点 (Step)`，逻辑清晰。
    *   **高级流程控制**: 支持在**节点**和**流节点**两个层面设置**条件循环**。AI会根据上下文判断循环是否应继续，实现复杂的逻辑判断（例如，“循环此节点直到玩家装备了‘圣剑’为止”）。
    *   **并行与串行**: 步骤可以配置为并行执行（用于同时处理多个任务）或串行执行。
*   **深度AI集成**:
    *   **多模型/多服务商支持**: 通过`models_config.json`和设置界面，可以轻松配置和切换不同的LLM服务商（如 OpenAI, DeepSeek, Groq, 或本地的Ollama）。
    *   **动态提示词构建**: 提供一个全局的提示词库（`PromptManager`），用户可以创建可复用的提示词片段，并在流程编辑器中通过`PromptBuilderDialog`将它们组合成一个完整的系统提示（System Prompt）。
    *   **AI赋能的数据解析**: 游戏可以从文件中读取角色的属性。该文件可以是结构化的JSON，也可以是**自然语言描述**。框架会自动调用AI将其规范化为标准的JSON数据。
*   **异步非阻塞操作**: 核心游戏控制器（`GameController`）运行在独立的`QThread`中，确保复杂的AI请求和逻辑处理不会冻结用户界面。UI与后台逻辑通过Qt的信号与槽机制安全通信。
*   **现代化用户界面 (PySide6)**:
    *   采用时尚的深色主题。
    *   通过“卡片式”设计（`AppController`）在主菜单、游戏界面和流程编辑器之间流畅切换。
    *   带有颜色高亮的日志输出面板，清晰地展示系统、玩家和AI的消息。
*   **数据持久化**:
    *   所有工作流、API配置和提示词库都以JSON格式保存在本地，易于备份和分享。
    *   游戏进度支持自动保存和加载。

## 🏛️ 项目架构

项目遵循关注点分离的原则，主要分为三个部分：

1.  **视图 (Views / `windows` & `cards`目录)**
    *   `mainWindow.py`: 程序主窗口，提供基本的停靠布局。
    *   `settingWindow.py`: API服务商的设置弹窗。
    *   `start_card.py`: 主菜单卡片。
    *   `game_card.py`: 游戏进行中的主界面卡片，负责显示属性和处理玩家输入。
    *   `flow_manage_card.py`: 核心的、功能完备的工作流编辑器卡片。

2.  **控制器 (Controllers / `core`目录)**
    *   `AppController.py`: **应用总控制器**。负责管理和切换不同的UI“卡片”，是UI导航的核心。
    *   `GameController.py`: **游戏逻辑控制器**。在后台线程中运行，负责解析和执行工作流、与AI交互、管理游戏状态（上下文、存档），并通过信号与`game_card.py`通信。

3.  **管理器 (Managers / `manager`目录) & 核心链接器 (`core`)**
    *   `JsonWorkflowManager.py`: 负责工作流数据（`workflow_data.json`）的CRUD（增删改查）操作。
    *   `ModelConfigManager.py`: 负责API服务商配置（`models_config.json`）的管理。
    *   `PromptManager.py`: 负责全局提示词库（`prompts.json`）的管理。
    *   `ModelLinker.py`: 封装了对OpenAI兼容API的调用，简化了与LLM的通信。
    *   `ContextBuilder.py`: 根据选择的提示词名称，动态构建格式化的系统提示。

## 🚀 快速开始

### 1. 环境准备

*   Python 3.8 或更高版本。
*   一个或多个LLM的API密钥（例如 OpenAI API Key）。

### 2. 安装

1.  克隆本仓库到本地：
    ```bash
    git clone https://github.com/abyss464/AIRPGgame.git
    cd AIRPGgame
    ```

2.  (推荐) 创建并激活一个虚拟环境：
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  安装所需的依赖库：
    ```
    # requirements.txt
    PySide6
    requests
    openai
    ```
    执行安装命令：
    ```bash
    pip install -r requirements.txt
    ```

### 3. 配置

1.  直接运行程序：
    ```bash
    python main.py
    ```
    首次运行时，程序会自动在根目录创建所需的JSON配置文件（如果它们不存在的话）：
    *   `models_config.json`: 存储API服务商信息。
    *   `prompts.json`: 存储提示词库。
    *   `workflow_data.json`: 存储你的游戏流程。

2.  **配置API服务商（最重要的一步！）**:
    *   在主窗口中，点击左下角的 **设置按钮 (⚙️)**。
    *   在弹出的“模型服务商配置”窗口中，点击“➕ 新增”。
    *   填写以下信息：
        *   **名称**: 给你的服务商起个名字（例如 `my_openai`）。
        *   **API Key**: 填入你的API密钥。
        *   **Base URL**: 填入API的地址（例如 `https://api.openai.com/v1`）。
        *   **默认模型**: 填入你希望默认使用的模型ID（例如 `gpt-4o`）。
    *   点击“💾 保存更改”。
    *   （可选）点击“🔄 获取模型列表”来填充可用模型下拉菜单。
    *   （可选）选中一个服务商，点击“⭐ 设为默认”。

### 4. 使用指南

1.  **创建游戏流程**:
    *   在主菜单，点击“新建游戏流程”。
    *   在流程编辑器中，点击“添加流程”，输入一个名称（如 `我的冒险故事`）。
    *   选中你创建的流程，点击“添加节点”，创建一个场景节点（如 `村庄入口`）。
    *   选中节点，点击“添加流节点”，创建一个AI对话步骤（如 `与守卫对话`）。
    *   在右侧的详细配置中，为你创建的**流节点**填入**提示词(Prompt)**，例如：“你是一个村庄的守卫，性格粗鲁但内心善良。一个冒险者刚刚来到村庄门口，与他对话。”
    *   点击“保存更改”。

2.  **开始游戏**:
    *   点击左上角的“🔙 返回主菜单”。
    *   点击“开始游戏”。
    *   在游戏界面，从下拉菜单中选择你刚刚创建的流程`我的冒险故事`。
    *   点击“开始新游戏”。
    *   游戏将开始运行，AI会根据你的提示词扮演角色，你可以在下方的输入框中输入你的行动。

## 📁 项目文件结构

```
.
├── aifiles/                # 游戏运行时AI生成或读取的文件的存放目录
├── cards/                  # 存放主要UI卡片（QWidget）
│   ├── game_card.py
│   ├── start_card.py
│   └── flow_manage_card.py
├── core/                   # 存放核心控制器和逻辑模块
│   ├── AppController.py
│   ├── GameController.py
│   ├── ModelLinker.py
│   └── context_builder.py
├── manager/                # 存放各类数据管理器
│   ├── json_flow_manager.py
│   ├── model_config_manager.py
│   └── prompt_manager.py
├── windows/                # 存放主窗口和设置窗口
│   ├── mainWindow.py
│   └── settingWindow.py
├── main.py                 # 应用程序入口
├── models_config.json      # (自动生成) API服务商配置
├── prompts.json            # (自动生成) 提示词库
├── workflow_data.json      # (自动生成) 游戏流程数据
└── requirements.txt        # Python依赖
```

---
