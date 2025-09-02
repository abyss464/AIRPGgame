# AI-Powered Text RPG Framework

An extensible desktop application for creating and running dynamic text-based RPGs powered by Large Language Models (LLMs).

[**English**](#english) | [**简体中文**](#chinese) | [**日本語**](#japanese)

---

<a name="english"></a>

## English

### An AI-Powered Text RPG Framework

This is a highly extensible desktop application built with PySide6 for creating and running dynamic text-based Role-Playing Games (RPGs) powered by Large Language Models (LLMs). It's more than just a game; it's a powerful framework that allows users to design complex game logic and AI interactions through a visual flow editor, all without writing a single line of code.

### ✨ Core Features

*   **Modular Architecture**: Adopts an MVC-like (Model-View-Controller) design pattern, clearly separating the UI (Views), application logic (Controllers), and data management (Managers) for easy maintenance and extension.
*   **Workflow-Driven Game Logic**: The core game flow is not hard-coded but defined by a flexible, hierarchical JSON structure. Users can create their own "scripts."
*   **Powerful Workflow Editor**:
    *   **Hierarchical Structure**: `Workflow -> Node -> Step`, providing a clear logical flow.
    *   **Advanced Flow Control**: Supports **conditional loops** at both the **Node** and **Step** levels. The AI determines whether the loop should continue based on the context, enabling complex logic (e.g., "loop this node until the player has equipped the 'Holy Sword'").
    *   **Parallel & Sequential Execution**: Steps can be configured to run in parallel (for handling multiple tasks simultaneously) or sequentially.
*   **Deep AI Integration**:
    *   **Multi-Model/Multi-Provider Support**: Easily configure and switch between different LLM providers (like OpenAI, DeepSeek, Groq, or a local Ollama instance) through `models_config.json` and the settings UI.
    *   **Dynamic Prompt Building**: Provides a global prompt library (`PromptManager`). Users can create reusable prompt snippets and combine them into a complete System Prompt using the `PromptBuilderDialog` in the flow editor.
    *   **AI-Powered Data Parsing**: The game can read character attributes from a file. This file can be structured JSON or even **natural language descriptions**. The framework will automatically call an AI to normalize it into standard JSON data.
*   **Asynchronous, Non-Blocking Operations**: The core game controller (`GameController`) runs in a separate `QThread`, ensuring that complex AI requests and logic processing do not freeze the user interface. UI and background logic communicate safely through Qt's signal and slot mechanism.
*   **Modern User Interface (PySide6)**:
    *   Features a stylish dark theme.
    *   Smoothly switches between the main menu, game interface, and flow editor using a "card-based" design (`AppController`).
    *   A color-highlighted log output panel clearly displays messages from the system, player, and AI.
*   **Data Persistence**:
    *   All workflows, API configurations, and prompt libraries are saved locally in JSON format, making them easy to back up and share.
    *   Game progress supports automatic saving and loading.

### 🏛️ Project Architecture

The project follows the principle of separation of concerns, divided into three main parts:

1.  **Views (in `windows` & `cards` directories)**
    *   `mainWindow.py`: The main program window, providing a basic docking layout.
    *   `settingWindow.py`: The settings dialog for API providers.
    *   `start_card.py`: The main menu card.
    *   `game_card.py`: The main game interface card, responsible for displaying attributes and handling player input.
    *   `flow_manage_card.py`: The core, full-featured workflow editor card.

2.  **Controllers (in `core` directory)**
    *   `AppController.py`: The **main application controller**. Manages and switches between different UI "cards," serving as the core of UI navigation.
    *   `GameController.py`: The **game logic controller**. Runs in a background thread, responsible for parsing and executing workflows, interacting with the AI, managing game state (context, saves), and communicating with `game_card.py` via signals.

3.  **Managers (in `manager` directory) & Core Linker (`core`)**
    *   `JsonWorkflowManager.py`: Handles CRUD (Create, Read, Update, Delete) operations for workflow data (`workflow_data.json`).
    *   `ModelConfigManager.py`: Manages API provider configurations (`models_config.json`).
    *   `PromptManager.py`: Manages the global prompt library (`prompts.json`).
    *   `ModelLinker.py`: Encapsulates calls to OpenAI-compatible APIs, simplifying communication with LLMs.
    *   `ContextBuilder.py`: Dynamically builds a formatted system prompt based on selected prompt names.

### 🚀 Quick Start

#### 1. Prerequisites

*   Python 3.8 or higher.
*   An API key for one or more LLMs (e.g., an OpenAI API Key).

#### 2. Installation

1.  Clone this repository to your local machine:
    ```bash
    git clone https://github.com/abyss464/AIRPGgame.git
    cd AIRPGgame
    ```

2.  (Recommended) Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  Install the required dependencies:
    ```
    # requirements.txt
    PySide6
    requests
    openai
    ```
    Run the installation command:
    ```bash
    pip install -r requirements.txt
    ```

#### 3. Configuration

1.  Run the application:
    ```bash
    python main.py
    ```
    On the first run, the program will automatically create the necessary JSON configuration files in the root directory if they don't exist:
    *   `models_config.json`: Stores API provider information.
    *   `prompts.json`: Stores the prompt library.
    *   `workflow_data.json`: Stores your game workflows.

2.  **Configure API Provider (The most important step!)**:
    *   In the main window, click the **Settings button (⚙️)** in the bottom-left corner.
    *   In the "Model Provider Configuration" window that appears, click "➕ Add New."
    *   Fill in the following information:
        *   **Name**: Give your provider a name (e.g., `my_openai`).
        *   **API Key**: Enter your API key.
        *   **Base URL**: Enter the API endpoint URL (e.g., `https://api.openai.com/v1`).
        *   **Default Model**: Enter the ID of the model you want to use by default (e.g., `gpt-4o`).
    *   Click "💾 Save Changes."
    *   (Optional) Click "🔄 Fetch Model List" to populate the available models dropdown.
    *   (Optional) Select a provider and click "⭐ Set as Default."

#### 4. Usage Guide

1.  **Create a Game Workflow**:
    *   From the main menu, click "Create New Game Flow."
    *   In the flow editor, click "Add Workflow" and enter a name (e.g., `My Adventure Story`).
    *   Select the workflow you created, then click "Add Node" to create a scene node (e.g., `Village Entrance`).
    *   Select the node, then click "Add Step" to create an AI dialogue step (e.g., `Talk to the Guard`).
    *   In the details panel on the right, enter a **Prompt** for the **Step** you created. For example: "You are a village guard, gruff on the outside but kind-hearted. An adventurer has just arrived at the village gate. Talk to them."
    *   Click "Save Changes."

2.  **Start the Game**:
    *   Click "🔙 Back to Main Menu" in the top-left corner.
    *   Click "Start Game."
    *   On the game screen, select the workflow you just created, `My Adventure Story`, from the dropdown menu.
    *   Click "Start New Game."
    *   The game will begin, and the AI will role-play based on your prompt. You can enter your actions in the input box at the bottom.

### 📁 Project File Structure

```
.
├── aifiles/                # Directory for files generated or read by the AI during gameplay
├── cards/                  # Contains the main UI cards (QWidget)
│   ├── game_card.py
│   ├── start_card.py
│   └── flow_manage_card.py
├── core/                   # Contains core controllers and logic modules
│   ├── AppController.py
│   ├── GameController.py
│   ├── ModelLinker.py
│   └── context_builder.py
├── manager/                # Contains various data managers
│   ├── json_flow_manager.py
│   ├── model_config_manager.py
│   └── prompt_manager.py
├── windows/                # Contains the main window and settings window
│   ├── mainWindow.py
│   └── settingWindow.py
├── main.py                 # Application entry point
├── models_config.json      # (Auto-generated) API provider configurations
├── prompts.json            # (Auto-generated) Prompt library
├── workflow_data.json      # (Auto-generated) Game workflow data
└── requirements.txt        # Python dependencies
```

---

<a name="chinese"></a>

## 简体中文

### AI-Powered Text RPG Framework

这是一个基于 PySide6 构建的高度可扩展的桌面应用程序，用于创建和运行由大型语言模型（LLM）驱动的动态文本角色扮演游戏（RPG）。它不仅仅是一个游戏，更是一个强大的框架，允许用户通过可视化的流程编辑器设计复杂的游戏逻辑和AI交互，而无需编写任何代码。

### ✨ 核心特性

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

### 🏛️ 项目架构

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

### 🚀 快速开始

#### 1. 环境准备

*   Python 3.8 或更高版本。
*   一个或多个LLM的API密钥（例如 OpenAI API Key）。

#### 2. 安装

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

#### 3. 配置

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

#### 4. 使用指南

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


### 📁 项目文件结构

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

<a name="japanese"></a>

## 日本語

### AI駆動型テキストRPGフレームワーク

これはPySide6で構築された、高度に拡張可能なデスクトップアプリケーションです。大規模言語モデル（LLM）によって駆動されるダイナミックなテキストベースのロールプレイングゲーム（RPG）を作成し、実行するために使用されます。単なるゲームではなく、ユーザーがコードを一切書かずに、視覚的なフローエディタを通じて複雑なゲームロジックやAIとのインタラクションを設計できる強力なフレームワークです。

### ✨ 主な特徴

*   **モジュラーアーキテクチャ**: MVC（モデル-ビュー-コントローラ）ライクな設計パターンを採用し、UI（ビュー）、アプリケーションロジック（コントローラ）、データ管理（マネージャ）を明確に分離。保守と拡張が容易です。
*   **ワークフロー駆動のゲームロジック**: ゲームのコアフローはハードコーディングされておらず、柔軟で階層的なJSON構造によって定義されます。ユーザーは独自の「シナリオ」を作成できます。
*   **強力なワークフローエディタ**:
    *   **階層構造**: `ワークフロー (Workflow) -> ノード (Node) -> ステップ (Step)`という明確な論理構造。
    *   **高度なフロー制御**: **ノード**と**ステップ**の両レベルで**条件付きループ**をサポート。AIが文脈に基づいてループを続行すべきか判断し、「プレイヤーが'聖剣'を装備するまでこのノードをループする」といった複雑なロジックを実現します。
    *   **並列・直列実行**: ステップは並列実行（複数のタスクを同時に処理）または直列実行に設定可能です。
*   **高度なAI統合**:
    *   **マルチモデル/マルチプロバイダー対応**: `models_config.json`と設定画面を通じて、異なるLLMプロバイダー（OpenAI、DeepSeek、Groq、またはローカルのOllamaなど）を簡単に設定・切り替えできます。
    *   **動的なプロンプト構築**: グローバルなプロンプトライブラリ（`PromptManager`）を提供。ユーザーは再利用可能なプロンプトスニペットを作成し、フローエディタの`PromptBuilderDialog`でそれらを組み合わせて完全なシステムプロンプトを構築できます。
    *   **AIによるデータ解析**: ゲームはファイルからキャラクターの属性を読み取ることができます。このファイルは構造化されたJSONだけでなく、**自然言語の記述**でも構いません。フレームワークが自動的にAIを呼び出し、標準的なJSONデータに正規化します。
*   **非同期・ノンブロッキング処理**: コアとなるゲームコントローラ（`GameController`）は独立した`QThread`で実行され、複雑なAIリクエストやロジック処理がUIをフリーズさせないことを保証します。UIとバックグラウンドロジックはQtのシグナル＆スロット機構で安全に通信します。
*   **モダンなユーザーインターフェース (PySide6)**:
    *   スタイリッシュなダークテーマを採用。
    *   「カードベース」の設計（`AppController`）により、メインメニュー、ゲーム画面、フローエディタ間をスムーズに切り替え。
    *   色分けされたログ出力パネルで、システム、プレイヤー、AIからのメッセージを明確に表示します。
*   **データの永続化**:
    *   すべてのワークフロー、API設定、プロンプトライブラリはJSON形式でローカルに保存され、バックアップや共有が容易です。
    *   ゲームの進行状況は自動保存とロードに対応しています。

### 🏛️ プロジェクトアーキテクチャ

プロジェクトは関心の分離の原則に従い、主に3つの部分に分かれています：

1.  **ビュー (Views / `windows` & `cards` ディレクトリ)**
    *   `mainWindow.py`: プログラムのメインウィンドウ。基本的なドッキングレイアウトを提供。
    *   `settingWindow.py`: APIプロバイダー設定用のダイアログ。
    *   `start_card.py`: メインメニューのカード。
    *   `game_card.py`: ゲーム進行中のメイン画面カード。属性表示とプレイヤー入力を担当。
    *   `flow_manage_card.py`: コアとなる、全機能搭載のワークフローエディタカード。

2.  **コントローラ (Controllers / `core` ディレクトリ)**
    *   `AppController.py`: **アプリケーション全体のコントローラ**。異なるUI「カード」の管理と切り替えを行い、UIナビゲーションの中核を担う。
    *   `GameController.py`: **ゲームロジックのコントローラ**。バックグラウンドスレッドで実行され、ワークフローの解析と実行、AIとの対話、ゲーム状態（コンテキスト、セーブデータ）の管理を行い、シグナルを通じて`game_card.py`と通信する。

3.  **マネージャ (Managers / `manager` ディレクトリ) & コアリンカ (`core`)**
    *   `JsonWorkflowManager.py`: ワークフローデータ（`workflow_data.json`）のCRUD操作（作成、読み取り、更新、削除）を担当。
    *   `ModelConfigManager.py`: APIプロバイダー設定（`models_config.json`）の管理を担当。
    *   `PromptManager.py`: グローバルなプロンプトライブラリ（`prompts.json`）の管理を担当。
    *   `ModelLinker.py`: OpenAI互換APIへの呼び出しをカプセル化し、LLMとの通信を簡素化。
    *   `ContextBuilder.py`: 選択されたプロンプト名に基づき、フォーマットされたシステムプロンプトを動的に構築。

### 🚀 クイックスタート

#### 1. 環境準備

*   Python 3.8 以降。
*   1つ以上のLLMのAPIキー（例：OpenAI APIキー）。

#### 2. インストール

1.  このリポジトリをローカルにクローンします：
    ```bash
    git clone https://github.com/abyss464/AIRPGgame.git
    cd AIRPGgame
    ```

2.  （推奨）仮想環境を作成して有効化します：
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  必要なライブラリをインストールします：
    ```
    # requirements.txt
    PySide6
    requests
    openai
    ```
    インストールコマンドを実行します：
    ```bash
    pip install -r requirements.txt
    ```

#### 3. 設定

1.  プログラムを実行します：
    ```bash
    python main.py
    ```
    初回実行時、プログラムはルートディレクトリに以下のJSON設定ファイルを自動的に作成します（存在しない場合）：
    *   `models_config.json`: APIプロバイダー情報を保存。
    *   `prompts.json`: プロンプトライブラリを保存。
    *   `workflow_data.json`: ゲームのワークフローを保存。

2.  **APIプロバイダーの設定（最重要ステップ！）**:
    *   メインウィンドウの左下にある**設定ボタン (⚙️)** をクリックします。
    *   表示された「モデルプロバイダー設定」ウィンドウで、「➕ 新規追加」をクリックします。
    *   以下の情報を入力します：
        *   **名称**: プロバイダーに名前を付けます（例：`my_openai`）。
        *   **API Key**: あなたのAPIキーを入力します。
        *   **Base URL**: APIのエンドポイントURLを入力します（例：`https://api.openai.com/v1`）。
        *   **デフォルトモデル**: デフォルトで使用したいモデルのIDを入力します（例：`gpt-4o`）。
    *   「💾 変更を保存」をクリックします。
    *   （任意）「🔄 モデルリストを取得」をクリックして、利用可能なモデルのドロップダウンメニューを更新します。
    *   （任意）プロバイダーを選択し、「⭐ デフォルトに設定」をクリックします。

#### 4. 使用ガイド

1.  **ゲームフローの作成**:
    *   メインメニューで「新規ゲームフローを作成」をクリックします。
    *   フローエディタで「ワークフローを追加」をクリックし、名前を入力します（例：`私の冒険物語`）。
    *   作成したワークフローを選択し、「ノードを追加」をクリックしてシーンノードを作成します（例：`村の入り口`）。
    *   ノードを選択し、「ステップを追加」をクリックしてAIとの対話ステップを作成します（例：`衛兵と話す`）。
    *   右側の詳細設定パネルで、作成した**ステップ**に**プロンプト**を入力します。例：「あなたは村の衛兵で、態度はぶっきらぼうだが心は優しい。一人の冒険者が村の入り口に来たので、彼と対話しなさい。」
    *   「変更を保存」をクリックします。

2.  **ゲームの開始**:
    *   左上の「🔙 メインメニューに戻る」をクリックします。
    *   「ゲームを開始」をクリックします。
    *   ゲーム画面で、ドロップダウンメニューから先ほど作成したワークフロー`私の冒険物語`を選択します。
    *   「新規ゲームを開始」をクリックします。
    *   ゲームが開始され、AIがプロンプトに基づいてキャラクターを演じます。下部の入力ボックスにあなたの行動を入力できます。

### 📁 プロジェクトのファイル構成

```
.
├── aifiles/                # ゲームプレイ中にAIが生成または読み取るファイルを格納するディレクトリ
├── cards/                  # 主要なUIカード（QWidget）を格納
│   ├── game_card.py
│   ├── start_card.py
│   └── flow_manage_card.py
├── core/                   # コアとなるコントローラとロジックモジュールを格納
│   ├── AppController.py
│   ├── GameController.py
│   ├── ModelLinker.py
│   └── context_builder.py
├── manager/                # 各種データマネージャを格納
│   ├── json_flow_manager.py
│   ├── model_config_manager.py
│   └── prompt_manager.py
├── windows/                # メインウィンドウと設定ウィンドウを格納
│   ├── mainWindow.py
│   └── settingWindow.py
├── main.py                 # アプリケーションのエントリーポイント
├── models_config.json      # (自動生成) APIプロバイダー設定
├── prompts.json            # (自動生成) プロンプトライブラリ
├── workflow_data.json      # (自動生成) ゲームのワークフローデータ
└── requirements.txt        # Pythonの依存関係
```
