# AI Agent Team Manager - Frontend

React + TypeScript + Material-UIで構築されたモダンなフロントエンドアプリケーション

## 📋 概要

このフロントエンドアプリケーションは、AIエージェントチームを管理するための直感的なユーザーインターフェースを提供します。リアルタイムでタスクの進捗を追跡し、エージェントと対話しながらタスクを遂行できます。

## 🛠️ 技術スタック

- **React 18.2** - UIフレームワーク
- **TypeScript 5.2** - 型安全性
- **Vite 4.5** - 高速ビルドツール
- **Material-UI 5.14** - UIコンポーネントライブラリ
- **Zustand 4.4** - 軽量な状態管理
- **Socket.IO Client 4.7** - WebSocketによるリアルタイム通信
- **Axios 1.5** - HTTP通信
- **React Router DOM 6.16** - ルーティング
- **React Markdown 9.0** - Markdown表示

## 📁 プロジェクト構造

```
frontend/
├── src/
│   ├── components/          # 再利用可能なコンポーネント
│   │   ├── TaskExecutionDialog.tsx    # タスク実行ダイアログ
│   │   ├── ToolApprovalDialog.tsx     # ツール承認ダイアログ
│   │   └── layout/
│   │       └── MainLayout.tsx         # メインレイアウト
│   ├── pages/              # ページコンポーネント
│   │   ├── Dashboard.tsx   # ダッシュボード
│   │   ├── Agents.tsx      # エージェント管理
│   │   ├── Tasks.tsx       # タスク管理
│   │   ├── Tools.tsx       # ツール管理
│   │   └── Settings.tsx    # 設定
│   ├── services/           # APIクライアント
│   │   ├── api.ts          # REST API
│   │   └── websocket.ts    # WebSocket
│   ├── store/              # Zustand状態管理
│   │   └── index.ts        # グローバルストア
│   ├── types/              # TypeScript型定義
│   │   ├── index.ts        # 基本型
│   │   └── interaction.ts  # インタラクション型
│   ├── App.tsx             # ルートコンポーネント
│   ├── main.tsx            # エントリーポイント
│   └── index.css           # グローバルスタイル
├── public/                 # 静的ファイル
├── index.html              # HTMLテンプレート
├── vite.config.ts          # Vite設定
├── tsconfig.json           # TypeScript設定
└── package.json            # 依存関係
```

## 🚀 セットアップ

### 前提条件

- Node.js 18 LTS以上
- npm 9以上

### インストール

```bash
# 依存関係のインストール
npm install
```

### 開発サーバーの起動

```bash
# 開発モードで起動（ホットリロード有効）
npm run dev
```

ブラウザで `http://localhost:5173` を開きます。

### ビルド

```bash
# 本番用ビルド
npm run build

# ビルド結果のプレビュー
npm run preview
```

### コード品質

```bash
# ESLintでコードチェック
npm run lint

# Prettierでコード整形
npm run format
```

## 📱 主要機能

### 1. ダッシュボード

システム全体の概要を表示：
- エージェント数
- タスク統計（完了、実行中、失敗）
- 最近のアクティビティ
- システムステータス

### 2. エージェント管理

AIエージェントの作成・管理：
- エージェントの作成・編集・削除
- 役割と説明の設定
- デフォルトツールの割り当て
- エージェント一覧の表示

**主要コンポーネント**: `src/pages/Agents.tsx`

### 3. タスク管理

タスクの作成・実行・監視：
- タスクの作成（タイトル、説明、優先度）
- タスク分析とツール推奨
- エージェントの選択（手動/自動）
- タスクの実行・キャンセル・削除
- ステータス別フィルタリング
- リアルタイム進捗表示

**ステータス**:
- 待機中 (pending)
- 実行中 (running)
- 入力待ち (waiting_input)
- 承認待ち (waiting_approval)
- 完了 (completed)
- 失敗 (failed)
- キャンセル済み (cancelled)

**主要コンポーネント**: `src/pages/Tasks.tsx`

### 4. タスク実行ダイアログ

タスク実行中の対話インターフェース：
- チャット形式の会話表示
- リアルタイムログ更新
- ユーザー入力フォーム（常時表示）
- 対話/自動モード切り替え
- タスクキャンセル

**特徴**:
- WebSocketによるリアルタイム更新
- 差分取得による効率的なログ表示
- Markdown対応のメッセージ表示
- スクロール位置の自動調整

**主要コンポーネント**: `src/components/TaskExecutionDialog.tsx`

### 5. ツール管理

ツールの管理と生成：
- 利用可能なツール一覧
- AI生成ツール（自然言語から自動生成）
- 手動ツール登録（Pythonコード直接入力）
- ツールの検索・フィルタリング
- カテゴリ別表示

**主要コンポーネント**: `src/pages/Tools.tsx`

### 6. 設定

LLMプロバイダーの設定：
- OpenAI、Anthropic、Gemini、watsonx.ai、Ollama
- APIキーの設定
- モデルの選択
- アクティブプロバイダーの切り替え
- 接続テスト

**主要コンポーネント**: `src/pages/Settings.tsx`

## 🔌 API統合

### REST API

`src/services/api.ts`で定義されたAPIクライアント：

```typescript
// エージェント
api.getAgents()
api.createAgent(data)
api.updateAgent(id, data)
api.deleteAgent(id)

// タスク
api.getTasks(params)
api.createTask(data)
api.executeTask(id)
api.cancelTask(id)
api.deleteTask(id)

// ツール
api.getTools(params)
api.generateTool(data)
api.registerTool(data)

// 設定
api.getLLMSettings()
api.createLLMSetting(data)
api.updateLLMSetting(provider, data)

// インタラクション
api.getInteractions(taskId, params)
api.sendUserMessage(taskId, message)
```

### WebSocket

`src/services/websocket.ts`でWebSocket接続を管理：

**イベント**:
- `task_update` - タスク状態の更新
- `task_log` - 新しいログエントリ
- `task_interaction` - 新しいインタラクション
- `agent_update` - エージェント状態の更新

**使用例**:
```typescript
import { connectWebSocket, disconnectWebSocket } from '@/services/websocket'

// 接続
connectWebSocket()

// 切断
disconnectWebSocket()
```

## 📊 状態管理

Zustandを使用したグローバル状態管理：

```typescript
// src/store/index.ts
interface AppState {
  // データ
  agents: Agent[]
  tasks: Task[]
  tools: Tool[]
  
  // ローディング状態
  loading: boolean
  
  // アクション
  fetchAgents: () => Promise<void>
  fetchTasks: () => Promise<void>
  addTask: (task: Task) => void
  updateTask: (id: number, updates: Partial<Task>) => void
  removeTask: (id: number) => void
  // ...
}

// 使用例
const { tasks, fetchTasks, updateTask } = useStore()
```

## 🎨 スタイリング

Material-UIのテーマシステムを使用：

- **カラーパレット**: プライマリ、セカンダリ、エラー、警告、情報、成功
- **タイポグラフィ**: 見出し、本文、キャプション
- **コンポーネント**: ボタン、カード、ダイアログ、テーブルなど
- **レスポンシブ**: モバイル、タブレット、デスクトップ対応

## 🔧 設定ファイル

### vite.config.ts

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:5000',
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true
      }
    }
  }
})
```

### tsconfig.json

TypeScript設定：
- `strict: true` - 厳格な型チェック
- パスエイリアス: `@/*` → `src/*`
- JSX: React 18の新しいJSX変換

## 🐛 デバッグ

### ブラウザ開発者ツール

- **Console**: ログとエラーメッセージ
- **Network**: API呼び出しとWebSocket通信
- **React DevTools**: コンポーネント階層と状態

### ログ出力

```typescript
// タスク更新のログ
console.log('[Tasks] Received updated tasks:', tasks)

// WebSocketイベントのログ
console.log('[WebSocket] Task update:', data)
```

## 📝 コーディング規約

### TypeScript

- 明示的な型定義を使用
- `any`の使用を避ける
- インターフェースで型を定義

### React

- 関数コンポーネントを使用
- Hooksを活用（useState、useEffect、useCallback）
- propsの型を明示的に定義

### ファイル命名

- コンポーネント: PascalCase（例: `TaskExecutionDialog.tsx`）
- ユーティリティ: camelCase（例: `api.ts`）
- 型定義: PascalCase（例: `Task`, `Agent`）

## 🚀 パフォーマンス最適化

### 実装済み

- **差分更新**: タスク一覧の差分取得（`updated_since`パラメータ）
- **ポーリング最適化**: 3秒間隔、完了タスクのみの場合は停止
- **楽観的更新**: ボタンクリック時の即座のUI更新
- **二度押し防止**: 実行ボタンの無効化

### 今後の改善

- コンポーネントのメモ化（React.memo）
- 仮想スクロール（長いリスト）
- コード分割（React.lazy）
- 画像の遅延読み込み

## 🧪 テスト

```bash
# テストの実行（未実装）
npm run test

# カバレッジレポート
npm run test:coverage
```

## 📦 ビルド最適化

本番ビルドの最適化：
- コード分割
- Tree shaking
- 圧縮とミニファイ
- ソースマップ生成

## 🔐 セキュリティ

- APIキーはバックエンドで管理
- XSS対策（React標準のエスケープ）
- CSRF対策（バックエンドで実装）

## 📚 参考リンク

- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Material-UI Documentation](https://mui.com/)
- [Vite Documentation](https://vitejs.dev/)
- [Zustand Documentation](https://github.com/pmndrs/zustand)

---

**AI Agent Team Manager Frontend** - モダンで使いやすいUIでAIエージェントを管理