# ツールシステムの説明

## ツールとは？

**ツール（Tool）**は、AIエージェントが実際の作業を行うための「機能」や「能力」です。
人間で例えると、「道具」や「スキル」のようなものです。

## 現在の実装での位置づけ

### Agentの動作フロー

```
ユーザー: "Pythonのチュートリアルを検索して、結果をファイルに保存して"
    ↓
Agent（LangGraphAgent）:
    1. Analyze: タスクを分析
       → "検索が必要" + "ファイル保存が必要"
    
    2. Plan: 実行計画を作成
       → "まずWeb検索、次にファイル書き込み"
    
    3. Think: 次のアクションを決定
       → "web_searchツールを使う"
    
    4. Act: ツールを実行
       → WebSearchTool.execute(query="Python tutorial")
    
    5. Observe: 結果を確認
       → "検索結果を取得した"
    
    6. Think: 次のアクションを決定
       → "write_fileツールを使う"
    
    7. Act: ツールを実行
       → FileWriteTool.execute(file_path="results.txt", content="...")
    
    8. Reflect: 完了を確認
       → "タスク完了"
```

## 実装済みのツール

### 1. WebSearchTool（Web検索）
**用途:** インターネット上の情報を検索

**例:**
```python
# Agentが自動的に使用
result = WebSearchTool().execute(
    query="Python チュートリアル",
    num_results=5
)
# → 検索結果のリストを返す
```

**実際の使用例:**
- 「最新のPythonニュースを調べて」
- 「React 18の新機能について教えて」
- 「東京の天気を調べて」

### 2. FileReadTool（ファイル読み込み）
**用途:** ファイルの内容を読み取る

**例:**
```python
result = FileReadTool().execute(
    file_path="/path/to/file.txt",
    encoding="utf-8"
)
# → ファイルの内容を返す
```

**実際の使用例:**
- 「config.jsonの内容を確認して」
- 「README.mdを読んで要約して」
- 「ログファイルからエラーを抽出して」

### 3. FileWriteTool（ファイル書き込み）
**用途:** ファイルにデータを書き込む

**例:**
```python
result = FileWriteTool().execute(
    file_path="/path/to/output.txt",
    content="Hello, World!",
    mode="write"  # または "append"
)
# → ファイルに書き込む
```

**実際の使用例:**
- 「検索結果をresults.txtに保存して」
- 「レポートをreport.mdとして作成して」
- 「ログをlog.txtに追記して」

### 4. FileListTool（ファイル一覧）
**用途:** ディレクトリ内のファイルを一覧表示

**例:**
```python
result = FileListTool().execute(
    directory="/path/to/dir",
    pattern="*.py",
    recursive=True
)
# → ファイルのリストを返す
```

**実際の使用例:**
- 「このディレクトリのPythonファイルを全部リストアップして」
- 「プロジェクト内のMarkdownファイルを探して」
- 「最近変更されたファイルを教えて」

## ツールの特徴

### 1. 自動選択
Agentがタスクの内容から必要なツールを**自動的に選択**します。

```
ユーザー: "Reactの情報を調べてファイルに保存"
    ↓
Agent: "web_searchとwrite_fileが必要だな"
    ↓
自動的に両方のツールを使用
```

### 2. パラメータ自動決定
ツールのパラメータもAgentが**自動的に決定**します。

```
ユーザー: "Pythonチュートリアルを5件検索"
    ↓
Agent: web_search(query="Python tutorial", num_results=5)
```

### 3. エラーハンドリング
ツール実行が失敗しても、Agentが**別の方法を試します**。

```
ファイル書き込み失敗
    ↓
Agent: "ディレクトリが存在しないようだ。作成してから再試行しよう"
```

### 4. 連鎖実行
複数のツールを**順番に実行**できます。

```
1. web_search → 検索
2. read_file → 既存データ読み込み
3. write_file → 結果を統合して保存
```

## ツールの拡張性

### 新しいツールの追加が簡単

```python
# backend/app/tools/my_custom_tool.py
from app.tools.base_tool import BaseTool, ToolParameter

class MyCustomTool(BaseTool):
    name = "my_custom_tool"
    description = "カスタムツールの説明"
    category = "custom"
    parameters = [
        ToolParameter(
            name="param1",
            type="string",
            description="パラメータの説明",
            required=True
        )
    ]
    
    def execute(self, **kwargs):
        param1 = kwargs.get("param1")
        # 実際の処理
        return {
            "success": True,
            "result": "処理結果"
        }

# ToolRegistryに登録
from app.tools import ToolRegistry
ToolRegistry.register(MyCustomTool)
```

## 今後追加予定のツール

### 優先度: 高

1. **CodeExecutionTool（コード実行）**
   - Pythonコードを実行
   - 結果を取得
   - セキュアなサンドボックス環境

2. **APICallTool（API呼び出し）**
   - REST APIを呼び出し
   - レスポンスを解析
   - 認証対応

3. **DatabaseQueryTool（データベース操作）**
   - SQLクエリ実行
   - データ取得・更新
   - 安全なクエリ実行

### 優先度: 中

4. **EmailTool（メール送信）**
   - メール送信
   - 添付ファイル対応
   - テンプレート機能

5. **CalendarTool（カレンダー操作）**
   - イベント作成・取得
   - リマインダー設定
   - Google Calendar連携

6. **SlackTool（Slack連携）**
   - メッセージ送信
   - チャンネル管理
   - ファイルアップロード

7. **GitHubTool（GitHub操作）**
   - リポジトリ操作
   - Issue/PR作成
   - コードレビュー

### 優先度: 低

8. **ImageGenerationTool（画像生成）**
   - DALL-E/Stable Diffusion連携
   - 画像編集
   - OCR機能

9. **DataAnalysisTool（データ分析）**
   - Pandas操作
   - グラフ生成
   - 統計分析

10. **BrowserAutomationTool（ブラウザ自動化）**
    - Selenium/Playwright連携
    - Webスクレイピング
    - フォーム入力

## ツールとFunction Callingの関係

### Function Calling
OpenAIやAnthropicのFunction Calling機能と統合されています。

```python
# ツールがFunction Calling形式に自動変換される
tool.to_function_schema()
# ↓
{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "num_results": {
                    "type": "number",
                    "description": "Number of results"
                }
            },
            "required": ["query"]
        }
    }
}
```

これにより、LLMが**最適なツールとパラメータを自動選択**できます。

## まとめ

### ツールの役割
- ✅ Agentの「手足」として実際の作業を実行
- ✅ 自動選択・自動実行
- ✅ エラーハンドリング
- ✅ 拡張可能な設計

### 現在の状態
- ✅ 基本的な4つのツールを実装
- ✅ ToolRegistryで一元管理
- ✅ Function Calling対応
- ✅ LangGraphAgentと統合

### 次のステップ
- 追加ツールの実装
- Function Calling完全統合
- ツール実行の最適化
- セキュリティ強化

---

**ツールは、Agentが「考える」だけでなく「実行する」ための重要な機能です！**