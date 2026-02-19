# Human-in-the-Loop (HITL) 機能設計

## 概要

エージェントがタスク実行中にユーザーと対話できる機能を実装します。

## 目標

1. **リアルタイム実行ログ表示** - エージェントの思考過程を可視化
2. **対話的実行** - エージェントがユーザーに質問して情報を収集
3. **ステップバイステップ実行** - 各ステップで進行確認

## アーキテクチャ

### 1. バックエンド

#### 1.1 データモデル

**TaskInteraction（新規）**
```python
class TaskInteraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    interaction_type = db.Column(db.String(50))  # 'question', 'info', 'tool_call', 'result'
    content = db.Column(db.Text)
    metadata = db.Column(db.JSON)
    requires_response = db.Column(db.Boolean, default=False)
    response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)
```

#### 1.2 LangGraphカスタムノード

**HumanInputNode**
- エージェントがユーザーに質問
- 実行を一時停止
- ユーザーの回答を待つ

**実装方法:**
```python
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

def create_hitl_agent(llm, tools):
    # カスタムグラフを作成
    workflow = StateGraph(AgentState)
    
    # ノードを追加
    workflow.add_node("agent", agent_node)
    workflow.add_node("human_input", human_input_node)
    workflow.add_node("tools", tool_node)
    
    # エッジを追加
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "human_input": "human_input",
            "end": END
        }
    )
    
    return workflow.compile()
```

#### 1.3 WebSocket通信

**リアルタイム通信:**
- タスク実行状況をリアルタイム配信
- ユーザーの回答を即座に受信

**イベント:**
- `task_started` - タスク開始
- `agent_thinking` - エージェント思考中
- `tool_calling` - ツール実行中
- `human_input_required` - ユーザー入力待ち
- `task_completed` - タスク完了

#### 1.4 API エンドポイント

**新規エンドポイント:**
```
POST /api/tasks/{id}/execute-interactive  # 対話的実行開始
POST /api/tasks/{id}/respond              # ユーザー回答送信
GET  /api/tasks/{id}/interactions         # 対話履歴取得
POST /api/tasks/{id}/pause                # 実行一時停止
POST /api/tasks/{id}/resume               # 実行再開
```

### 2. フロントエンド

#### 2.1 TaskExecutionDialog（新規コンポーネント）

**機能:**
- チャット形式のUI
- リアルタイム実行ログ表示
- ユーザー入力フォーム
- 進行状況インジケーター

**構成:**
```tsx
<Dialog>
  <DialogTitle>タスク実行中: {task.title}</DialogTitle>
  <DialogContent>
    {/* 実行ログ・チャット表示 */}
    <Box sx={{ height: 400, overflow: 'auto' }}>
      {interactions.map(interaction => (
        <InteractionMessage 
          key={interaction.id}
          interaction={interaction}
        />
      ))}
    </Box>
    
    {/* ユーザー入力フォーム */}
    {waitingForInput && (
      <TextField
        fullWidth
        placeholder="回答を入力..."
        onSubmit={handleSubmit}
      />
    )}
    
    {/* 進行状況 */}
    <LinearProgress />
  </DialogContent>
</Dialog>
```

#### 2.2 WebSocket接続

```typescript
const socket = io('http://localhost:5000')

socket.on('task_event', (event) => {
  switch(event.type) {
    case 'agent_thinking':
      addInteraction({ type: 'info', content: event.message })
      break
    case 'human_input_required':
      setWaitingForInput(true)
      addInteraction({ type: 'question', content: event.question })
      break
    case 'task_completed':
      setTaskCompleted(true)
      break
  }
})
```

## 実装フェーズ

### Phase 1: リアルタイム実行ログ表示（1-2日）

**目標:** エージェントの動作を可視化

**実装内容:**
1. TaskInteractionモデル作成
2. ExecutionServiceでログ記録
3. WebSocketイベント配信
4. フロントエンドでログ表示

**成果物:**
- エージェントの思考過程が見える
- ツール実行状況が分かる
- 進行状況が把握できる

### Phase 2: Human-in-the-Loop基本機能（2-3日）

**目標:** エージェントがユーザーに質問できる

**実装内容:**
1. HumanInputToolの実装
2. LangGraphカスタムノード追加
3. 対話APIエンドポイント実装
4. チャット形式UI実装

**成果物:**
- エージェントが質問を投げかける
- ユーザーが回答を入力
- 会話履歴が残る

### Phase 3: 高度な対話機能（2-3日）

**目標:** より柔軟な対話

**実装内容:**
1. 複数選択肢の提示
2. ファイルアップロード
3. 実行の一時停止・再開
4. ステップバイステップモード

## 技術的課題と解決策

### 課題1: LangGraphの実行を一時停止

**解決策:**
- `interrupt_before`/`interrupt_after`を使用
- カスタムノードで実行を中断
- ユーザー入力後に再開

### 課題2: WebSocketとFlaskの統合

**解決策:**
- Flask-SocketIOを使用
- 既存のWebSocket実装を拡張

### 課題3: 非同期実行の管理

**解決策:**
- Celeryタスクとして実行
- タスクIDで状態管理
- WebSocketで進捗通知

## 使用例

### 例1: ファイル要約タスク

```
User: 「ファイルを読み取り、要約して、出力する」

Agent: タスクを開始します...
Agent: ファイルを読み取るために、ファイルパスが必要です。
Agent: [質問] どのファイルを要約しますか？ファイルパスを教えてください。

User: /path/to/document.txt

Agent: ファイルを読み取っています...
Agent: [ツール実行] read_file('/path/to/document.txt')
Agent: ファイルの内容を取得しました。要約を生成しています...
Agent: [完了] 要約が完成しました。

結果: [要約内容]
```

### 例2: データ分析タスク

```
User: 「売上データを分析して、レポートを作成」

Agent: タスクを開始します...
Agent: [質問] どの期間のデータを分析しますか？
  1. 今月
  2. 先月
  3. カスタム期間

User: 2

Agent: 先月のデータを取得しています...
Agent: [ツール実行] fetch_sales_data(period='last_month')
Agent: データを分析しています...
Agent: [質問] グラフの種類を選択してください：
  1. 棒グラフ
  2. 折れ線グラフ
  3. 円グラフ

User: 2

Agent: レポートを生成しています...
Agent: [完了] レポートが完成しました。
```

## まとめ

Human-in-the-Loop機能により、エージェントとユーザーが協力してタスクを完了できるようになります。

**メリット:**
- タスクの透明性向上
- 柔軟な情報収集
- エラーの早期発見
- ユーザーの安心感

**次のステップ:**
Phase 1から順次実装を開始します。