# AI Agent Team Manager - セットアップガイド

## 概要
このドキュメントでは、AI Agent Team Managerの開発環境のセットアップ方法を説明します。

## 前提条件
- Python 3.11以上
- Node.js 18以上
- npm または yarn

## バックエンドのセットアップ

### 1. 仮想環境の作成と有効化
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
```

### 2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定
`.env.example`をコピーして`.env`ファイルを作成し、必要な環境変数を設定します。

```bash
cp .env.example .env
```

`.env`ファイルを編集して、以下の設定を行います：
- `SECRET_KEY`: ランダムな文字列を設定
- `DATABASE_URL`: データベースのURL（開発環境ではデフォルトのSQLiteを使用）
- LLMプロバイダーのAPIキー（使用する場合）

### 4. データベースの初期化
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"
```

### 5. バックエンドサーバーの起動
```bash
python run.py
```

バックエンドサーバーは http://localhost:5000 で起動します。

## フロントエンドのセットアップ

### 1. 依存関係のインストール
```bash
cd frontend
npm install
```

### 2. フロントエンドサーバーの起動
```bash
npm run dev
```

フロントエンドサーバーは http://localhost:3000 で起動します。

## 開発の開始

1. バックエンドサーバーを起動（ターミナル1）
```bash
cd backend
source venv/bin/activate
python run.py
```

2. フロントエンドサーバーを起動（ターミナル2）
```bash
cd frontend
npm run dev
```

3. ブラウザで http://localhost:3000 にアクセス

## プロジェクト構造

```
organization-app/
├── backend/                 # バックエンド（Flask）
│   ├── app/
│   │   ├── __init__.py     # アプリケーションファクトリ
│   │   ├── config.py       # 設定
│   │   ├── models/         # データモデル
│   │   ├── api/            # APIエンドポイント
│   │   ├── services/       # ビジネスロジック
│   │   └── llm/            # LLMプロバイダー
│   ├── requirements.txt    # Python依存関係
│   └── run.py             # エントリーポイント
│
├── frontend/               # フロントエンド（React + TypeScript）
│   ├── src/
│   │   ├── components/    # Reactコンポーネント
│   │   ├── pages/         # ページコンポーネント
│   │   ├── services/      # APIクライアント
│   │   ├── store/         # 状態管理（Zustand）
│   │   └── types/         # TypeScript型定義
│   ├── package.json       # Node.js依存関係
│   └── vite.config.ts     # Vite設定
│
└── docs/                   # ドキュメント
    ├── requirements.md     # 要件定義
    ├── architecture.md     # アーキテクチャ設計
    ├── ui-wireframe.md     # UI/UXワイヤーフレーム
    ├── tech-stack.md       # 技術スタック
    └── implementation-plan.md  # 実装計画
```

## 主要な機能

### 1. エージェント管理
- エージェントの作成、編集、削除
- LLMプロバイダーとモデルの設定
- エージェントのステータス管理

### 2. タスク管理
- タスクの作成、実行、キャンセル
- 手動/自動/チームモードの選択
- タスクの進捗追跡

### 3. ツール管理
- カスタムツールの登録
- ツールのカテゴリ管理
- ツールの有効/無効切り替え

### 4. LLM設定
- 複数のLLMプロバイダーのサポート
  - OpenAI (GPT-4, GPT-3.5)
    - GitHub Models対応（無料でGPT-4o等を使用可能）
    - Azure OpenAI対応
  - Anthropic (Claude 3)
  - Google Gemini (Gemini Pro, Gemini 1.5)
  - IBM watsonx.ai
  - Ollama (ローカルLLM)
- カスタムベースURL対応
- モデル名の柔軟な指定
- APIキーの安全な管理
- 接続テスト機能

## トラブルシューティング

### データベースエラー
データベースファイルを削除して再初期化：
```bash
cd backend
rm instance/app.db
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### ポート競合
別のポートを使用する場合：

バックエンド（`backend/run.py`）:
```python
app.run(debug=True, port=5001)  # ポート番号を変更
```

フロントエンド（`frontend/vite.config.ts`）:
```typescript
server: {
  port: 3001,  // ポート番号を変更
  proxy: {
    '/api': {
      target: 'http://localhost:5001',  // バックエンドのポートに合わせる
      // ...
    }
  }
}
```

### 依存関係の問題
依存関係を再インストール：

バックエンド:
```bash
cd backend
pip install --force-reinstall -r requirements.txt
```

フロントエンド:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 次のステップ

1. LLM設定ページでAPIキーを設定
2. エージェントを作成
3. タスクを作成して実行
4. 実行ログを確認

詳細なドキュメントは`docs/`ディレクトリを参照してください。

## GitHub Modelsの使用方法（無料でGPT-4oを使用）

GitHub Modelsを使用すると、GitHubアカウントで無料でGPT-4o、GPT-4o-mini、Phi-3などのモデルを使用できます。

### 1. GitHub Personal Access Tokenの取得
1. GitHubにログイン
2. Settings → Developer settings → Personal access tokens → Tokens (classic)
3. "Generate new token (classic)" をクリック
4. スコープは不要（チェックなしでOK）
5. トークンをコピー

### 2. AI Agent Team Managerで設定
1. 設定ページで「LLM設定を追加」
2. プロバイダー: **OpenAI**
3. APIキー: GitHubのPersonal Access Token
4. ベースURL: `https://models.inference.ai.azure.com`
5. デフォルトモデル: `gpt-4o` または `gpt-4o-mini`
6. 「接続テスト」で確認
7. 「作成」をクリック

### 3. 利用可能なモデル
- `gpt-4o` - 最新のGPT-4 Omni
- `gpt-4o-mini` - 軽量版
- `Phi-3-medium-128k-instruct` - Microsoftの小型モデル
- `Phi-3-small-128k-instruct`
- `Phi-3-mini-128k-instruct`

詳細: https://github.com/marketplace/models

### 制限事項
- レート制限: 1分あたり15リクエスト、1日あたり150リクエスト
- 商用利用不可（開発・テスト用途のみ）
- プロダクション環境では通常のOpenAI APIを使用してください
