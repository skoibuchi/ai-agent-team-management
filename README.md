# **注意** 
* 全部AIエージェントに書かせたAIエージェント管理ツールです。皮肉なものです。
    * 実験作で自分が遊ぶためのものです。
    * 開発してる感がなかったり、とはいえAIエージェント時代の開発に慣れないとなと思ったり。
* まだ未完成です。色々荒いです。構成色々ぐちゃぐちゃな気がする。
* やはりコンテキストウィンドウの制約が鬼門。

# AI Agent Team Manager

複数のAIエージェントをチームとして管理し、様々なタスクを効率的に遂行できる汎用的なGUIツール  

## 📋 プロジェクト概要

AI Agent Team Managerは、複数のAIエージェントを部下として管理し、自然言語でタスクを指示できる革新的なシステムです。エージェントは必要なツールを自動で選定・生成し、単独またはチームで協調してタスクを遂行します。

### 主要な特徴

- 🤖 **複数エージェント管理**: 複数のAIエージェントを作成・管理し、それぞれに役割とツールを割り当て
- 💬 **Human-in-the-Loop**: エージェントとリアルタイムで対話しながらタスクを進行
- 🔧 **動的ツール生成**: 自然言語でツールを説明するだけで、AIが自動的にツールコードを生成
- 🎯 **柔軟なツール管理**: エージェントやタスクごとに使用するツールを選択可能
- 👥 **対話/自動モード**: タスク実行中にモードを切り替え可能
- 📊 **リアルタイム進捗管理**: WebSocketによるリアルタイムなタスク状態更新
- 🌐 **マルチLLM対応**: OpenAI、Anthropic、Google Gemini、watsonx.ai、Ollamaに対応
- 🎨 **直感的なUI**: Material-UIベースのモダンで使いやすいインターフェース
- 💾 **永続的な会話履歴**: LangGraphのSqliteSaverによる会話履歴の保存

## 🎯 ユースケース

- **対話的なタスク実行**: 「今日のニュースを要約して」→ エージェントが質問 → ユーザーが回答 → タスク完了
- **ツールの動的生成**: 「株価を取得するツールを作って」→ AIが自動的にツールコードを生成
- **カスタムエージェント**: 特定の役割に特化したエージェントを作成し、専用ツールを割り当て
- **チーム協調**: 複数のエージェントが協力して複雑なタスクを遂行
- **長期タスク**: 数日かかるタスクでも、会話履歴を保持して継続実行

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────────┐
│    Frontend (React + TypeScript + MUI)  │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │Dashboard │  │  Agents  │  │ Tasks  ││
│  │          │  │  Tools   │  │Settings││
│  └──────────┘  └──────────┘  └────────┘│
│         WebSocket (Real-time Updates)    │
└─────────────────────────────────────────┘
                    │
            REST API / WebSocket
                    │
┌─────────────────────────────────────────┐
│      Backend (Flask + LangGraph)        │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │  Agent   │  │   Task   │  │  Tool  ││
│  │ Service  │  │ Service  │  │Registry││
│  └──────────┘  └──────────┘  └────────┘│
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │   LLM    │  │Execution │  │Dynamic ││
│  │ Gateway  │  │  Engine  │  │ToolGen ││
│  └──────────┘  └──────────┘  └────────┘│
│  ┌──────────────────────────────────┐  │
│  │  LangGraph (create_react_agent)  │  │
│  │  + SqliteSaver (Conversation)    │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│    LLM Services & External APIs         │
│  OpenAI | Anthropic | Gemini | watsonx  │
│  Ollama (Local LLM)                     │
└─────────────────────────────────────────┘
```

## 🛠️ 技術スタック

### フロントエンド
- **React 18.2** - UIフレームワーク
- **TypeScript 5.2** - 型安全性
- **Zustand 4.4** - 状態管理
- **Material-UI 5.14** - UIコンポーネント
- **Socket.IO Client 4.7** - WebSocket通信
- **Axios 1.5** - HTTP通信
- **Vite 4.5** - ビルドツール

### バックエンド
- **Python 3.9+** - プログラミング言語
- **Flask 2.0.1** - Webフレームワーク
- **Flask-SocketIO** - WebSocket対応
- **SQLAlchemy 2.0** - ORM
- **LangChain 0.3** - LLM統合フレームワーク
- **LangGraph 0.2** - エージェント実行エンジン
- **SQLite 3** - データベース（開発・本番）

### LLMプロバイダー
- **OpenAI** (GPT-4, GPT-4o, GPT-3.5)
- **Anthropic** (Claude 3.5 Sonnet, Claude 3 Opus/Haiku)
- **Google Gemini** (Gemini 1.5 Pro/Flash)
- **IBM watsonx.ai** (Granite, Llama)
- **Ollama** (ローカルLLM - Llama 3, Mistral, etc.)

## 📁 プロジェクト構造

```
organization-app/
├── frontend/              # フロントエンドアプリケーション
│   ├── src/
│   │   ├── components/   # Reactコンポーネント
│   │   │   ├── TaskExecutionDialog.tsx  # タスク実行ダイアログ
│   │   │   └── layout/   # レイアウトコンポーネント
│   │   ├── pages/        # ページコンポーネント
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Agents.tsx
│   │   │   ├── Tasks.tsx
│   │   │   ├── Tools.tsx
│   │   │   └── Settings.tsx
│   │   ├── store/        # Zustand状態管理
│   │   ├── services/     # APIクライアント
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   └── types/        # TypeScript型定義
│   └── package.json
├── backend/              # バックエンドアプリケーション
│   ├── app/
│   │   ├── models/       # データモデル
│   │   │   ├── agent.py
│   │   │   ├── task.py
│   │   │   ├── task_interaction.py
│   │   │   └── llm_setting.py
│   │   ├── services/     # ビジネスロジック
│   │   │   ├── agent_service.py
│   │   │   ├── task_service.py
│   │   │   ├── execution_service.py
│   │   │   └── task_analyzer.py
│   │   ├── api/          # APIエンドポイント
│   │   │   ├── agents.py
│   │   │   ├── tasks.py
│   │   │   ├── tools.py
│   │   │   ├── task_interactions.py
│   │   │   └── settings.py
│   │   ├── llm/          # LLMプロバイダー統合
│   │   │   ├── openai_provider.py
│   │   │   ├── anthropic_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   ├── watsonx_provider.py
│   │   │   └── ollama_provider.py
│   │   ├── tools/        # ツールシステム
│   │   │   ├── __init__.py (ToolRegistry)
│   │   │   ├── dynamic_tool_generator.py
│   │   │   ├── human_input_tool.py
│   │   │   ├── file_tool.py
│   │   │   └── web_search_tool.py
│   │   ├── agents/       # エージェント実装
│   │   │   └── langgraph_agent.py
│   │   └── websocket/    # WebSocketイベント
│   │       └── events.py
│   ├── data/             # データファイル
│   │   └── agent_memory.db  # LangGraph会話履歴
│   ├── requirements.txt
│   └── run.py
└── README.md
```

## 🚀 クイックスタート

### 前提条件

- Python 3.9以上
- Node.js 18 LTS以上
- Git

### インストール

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd organization-app
```

2. **バックエンドのセットアップ**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **環境変数の設定**
```bash
cd backend
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

必要な環境変数：
```env
# 使用するLLMプロバイダーのAPIキーを設定
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
WATSONX_API_KEY=your_watsonx_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id

# Flask設定
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
```

4. **フロントエンドのセットアップ**
```bash
cd frontend
npm install
```

5. **アプリケーションの起動**

**バックエンド**（ターミナル1）
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python run.py
```

**フロントエンド**（ターミナル2）
```bash
cd frontend
npm run dev
```

6. **ブラウザで開く**
```
http://localhost:3000
```

## 💡 使い方

### 1. LLM設定

1. 「設定」ページに移動
2. 使用したいLLMプロバイダーを選択
3. APIキーとモデルを設定
4. 「アクティブ」に設定

### 2. エージェント作成

1. 「エージェント」ページに移動
2. 「新規作成」ボタンをクリック
3. エージェント名、役割、説明を入力
4. 使用するツールを選択（オプション）
5. 作成

### 3. ツール管理

**既存ツールの使用**
- 「ツール」ページで利用可能なツールを確認
- エージェント作成時に必要なツールを選択

**新しいツールの生成**
1. 「ツール」ページの「AI生成」タブ
2. ツールの説明を自然言語で入力
3. 「生成」ボタンをクリック
4. AIが自動的にツールコードを生成
5. 生成されたコードを確認・編集
6. 「登録」ボタンで保存

**手動でツールを登録**
1. 「ツール」ページの「手動登録」タブ
2. Pythonコードを直接入力
3. 「登録」ボタンで保存

### 4. タスク実行

**基本的な流れ**
1. 「タスク」ページに移動
2. 「新規作成」ボタンをクリック
3. タスクの詳細を入力
4. （オプション）「タスクを分析してツールを推奨」で必要なツールを自動提案
5. エージェントを選択（手動モード）または自動選択
6. タスクを作成
7. 「実行」ボタンでタスク開始

**対話モード**
- エージェントが質問してきたら、チャット形式で回答
- 「自動モード」トグルをONにすると、質問をスキップして自動実行

**タスク管理**
- タブで状態別にフィルタリング（待機中、実行中、入力待ち、完了、失敗、キャンセル済み）
- 実行中のタスクはキャンセル可能
- 完了/失敗したタスクは削除可能
- ログアイコンでタスクの実行履歴を確認

## 🔧 主要機能

### Human-in-the-Loop (HITL)

エージェントとリアルタイムで対話しながらタスクを進行できます：

- **質問応答**: エージェントが不明点を質問し、ユーザーが回答
- **対話/自動モード切り替え**: タスク実行中にモードを変更可能
- **チャット形式UI**: 会話履歴を見やすく表示
- **リアルタイム更新**: WebSocketによる即座の状態反映

### 動的ツール生成

自然言語でツールを説明するだけで、AIが自動的にツールコードを生成：

```
説明例：
「指定されたURLからHTMLを取得して、
タイトルとメタディスクリプションを抽出するツール」

→ AIが自動的にPythonコードを生成
→ 必要な依存関係も自動インストール
```

### ツール割り当て

- **エージェントレベル**: エージェント作成時にデフォルトツールを設定
- **タスクレベル**: タスクごとに追加ツールを指定
- **柔軟な管理**: ツール未指定時は空リストで実行（LLMの判断のみ）

### タスク分析

タスクの内容を分析し、必要なツールを自動推奨：

1. タスク作成時に「タスクを分析」ボタンをクリック
2. LLMがタスクを分析
3. 推奨ツールのリストを表示
4. 必要なツールを選択して登録

### 会話履歴の永続化

LangGraphの`SqliteSaver`により、エージェントとの会話履歴を永続化：

- タスクごとに独立した会話スレッド
- サーバー再起動後も会話を継続可能
- 長期タスクの実行をサポート

## 📖 ドキュメント

詳細なドキュメントはプロジェクトルートにあります：

- [SETUP.md](docs/SETUP.md) - セットアップガイド
- [TOOLS_EXPLANATION.md](docs/TOOLS_EXPLANATION.md) - ツールシステムの詳細
- [HUMAN_IN_THE_LOOP_DESIGN.md](docs/HUMAN_IN_THE_LOOP_DESIGN.md) - HITL機能の設計
- [TEST_GUIDE.md](docs/TEST_GUIDE.md) - テストガイド

## 🗺️ 実装状況

### ✅ 完了済み機能

- ✅ 基本的なエージェント管理（CRUD）
- ✅ タスク管理とリアルタイム実行
- ✅ マルチLLM対応（OpenAI、Anthropic、Gemini、watsonx.ai、Ollama）
- ✅ LangGraph統合（create_react_agent）
- ✅ ツールレジストリシステム
- ✅ 動的ツール生成（AI Powered）
- ✅ 手動ツール登録
- ✅ Human-in-the-Loop機能
- ✅ 対話/自動モード切り替え
- ✅ WebSocketによるリアルタイム更新
- ✅ タスク分析とツール推奨
- ✅ エージェント・タスクへのツール割り当て
- ✅ 会話履歴の永続化（SqliteSaver）
- ✅ タスクキャンセル機能
- ✅ 詳細ステータス管理（入力待ち、承認待ちなど）

### 🚧 今後の予定

- 📅 チーム協調機能（複数エージェントの連携）
- 📅 ツール承認システムの完全実装
- 📅 エージェントスキル学習機能
- 📅 プラグインシステム
- 📅 パフォーマンス最適化
- 📅 Electronデスクトップアプリ化

## 🤝 コントリビューション

コントリビューションを歓迎します！

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📝 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 🙏 謝辞

このプロジェクトは以下のオープンソースプロジェクトを使用しています：

- [React](https://reactjs.org/)
- [Flask](https://flask.palletsprojects.com/)
- [LangChain](https://www.langchain.com/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [Material-UI](https://mui.com/)
- その他多数

---

**AI Agent Team Manager** で、AIエージェントチームを効率的に管理しましょう！