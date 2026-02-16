# AI Agent Team Manager - Backend

AIエージェントチーム管理システムのバックエンドAPI

## セットアップ

### 1. 仮想環境の作成

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
cp .env.example .env
```

`.env`ファイルを編集して、必要なAPIキーを設定してください：

```env
# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Anthropic (オプション)
ANTHROPIC_API_KEY=your-anthropic-api-key

# IBM watsonx.ai (オプション)
WATSONX_API_KEY=your-watsonx-api-key
WATSONX_PROJECT_ID=your-project-id
```

### 4. データベースのセットアップ

```bash
python setup.py
```

これにより以下が実行されます：
- データベーステーブルの作成
- 組み込みツールの初期化

## 起動

### 開発サーバー

```bash
python run.py
```

サーバーは `http://localhost:5000` で起動します。

### Redis（Celery用、オプション）

```bash
redis-server
```

### Celery Worker（非同期タスク処理、オプション）

```bash
celery -A app.celery worker --loglevel=info
```

## API エンドポイント

### エージェント管理

- `GET /api/agents` - エージェント一覧取得
- `POST /api/agents` - エージェント作成
- `GET /api/agents/{id}` - エージェント詳細取得
- `PUT /api/agents/{id}` - エージェント更新
- `DELETE /api/agents/{id}` - エージェント削除
- `GET /api/agents/{id}/statistics` - エージェント統計取得

### タスク管理

- `GET /api/tasks` - タスク一覧取得
- `POST /api/tasks` - タスク作成
- `GET /api/tasks/{id}` - タスク詳細取得
- `PUT /api/tasks/{id}` - タスク更新
- `DELETE /api/tasks/{id}` - タスク削除
- `POST /api/tasks/{id}/execute` - タスク実行
- `GET /api/tasks/{id}/logs` - タスクログ取得
- `POST /api/tasks/{id}/cancel` - タスクキャンセル

### ツール管理

- `GET /api/tools` - ツール一覧取得
- `POST /api/tools` - ツール作成
- `GET /api/tools/{id}` - ツール詳細取得
- `PUT /api/tools/{id}` - ツール更新
- `DELETE /api/tools/{id}` - ツール削除
- `GET /api/tools/categories` - カテゴリ一覧取得
- `POST /api/tools/{id}/test` - ツールテスト

### 設定管理

- `GET /api/settings/llm` - LLM設定一覧取得
- `POST /api/settings/llm` - LLM設定作成
- `GET /api/settings/llm/{provider}` - LLM設定取得
- `PUT /api/settings/llm/{provider}` - LLM設定更新
- `DELETE /api/settings/llm/{provider}` - LLM設定削除
- `GET /api/settings/llm/{provider}/models` - 利用可能モデル一覧
- `POST /api/settings/llm/{provider}/test` - 接続テスト
- `GET /api/settings/providers` - プロバイダー一覧取得

## WebSocket イベント

### クライアント → サーバー

- `connect` - 接続
- `disconnect` - 切断
- `join_task` - タスクルームに参加
- `leave_task` - タスクルームから退出
- `join_agent` - エージェントルームに参加
- `leave_agent` - エージェントルームから退出

### サーバー → クライアント

- `connected` - 接続完了
- `task_started` - タスク開始
- `task_progress` - タスク進捗
- `task_completed` - タスク完了
- `task_failed` - タスク失敗
- `agent_status_changed` - エージェントステータス変更
- `log_message` - ログメッセージ

## プロジェクト構造

```
backend/
├── app/
│   ├── __init__.py          # アプリケーション初期化
│   ├── config.py            # 設定
│   ├── models/              # データモデル
│   │   ├── agent.py
│   │   ├── task.py
│   │   ├── tool.py
│   │   ├── execution_log.py
│   │   └── llm_setting.py
│   ├── services/            # ビジネスロジック
│   │   ├── agent_service.py
│   │   ├── task_service.py
│   │   ├── tool_service.py
│   │   ├── llm_service.py
│   │   └── execution_service.py
│   ├── api/                 # APIエンドポイント
│   │   ├── agents.py
│   │   ├── tasks.py
│   │   ├── tools.py
│   │   └── settings.py
│   ├── llm/                 # LLMプロバイダー
│   │   ├── base_provider.py
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── watsonx_provider.py
│   │   └── ollama_provider.py
│   ├── tools/               # ツール実装
│   └── websocket/           # WebSocketイベント
│       └── events.py
├── tests/                   # テスト
├── migrations/              # データベースマイグレーション
├── requirements.txt         # 依存関係
├── setup.py                 # セットアップスクリプト
├── run.py                   # メイン実行ファイル
└── README.md
```

## 開発

### テストの実行

```bash
pytest
```

### コードフォーマット

```bash
black app/
isort app/
```

### リンター

```bash
flake8 app/
mypy app/
```

## トラブルシューティング

### データベースのリセット

```bash
rm ai_agent_team.db
python setup.py
```

### ポートが使用中

別のポートで起動：

```bash
PORT=5001 python run.py
```

## ライセンス

MIT License