"""
Web検索ツール（LangChain標準）
"""
from typing import Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    """Web検索ツールの入力スキーマ"""
    query: str = Field(description="検索クエリ")
    num_results: int = Field(
        default=5,
        description="取得する検索結果の数（1-10）",
        ge=1,
        le=10
    )


class WebSearchTool(BaseTool):
    """
    Web検索ツール
    
    Google検索APIまたは他の検索エンジンを使用してWeb検索を実行します。
    LangChain標準のBaseToolを継承し、Function Callingに対応しています。
    """
    
    name: str = "web_search"
    description: str = (
        "インターネット上の情報を検索します。"
        "最新のニュース、技術情報、一般的な知識などを調べる際に使用してください。"
        "検索クエリと取得する結果数を指定できます。"
    )
    args_schema: Type[BaseModel] = WebSearchInput
    
    def _run(self, query: str, num_results: int = 5) -> str:
        """
        Web検索を実行（同期版）
        
        Args:
            query: 検索クエリ
            num_results: 取得する結果数
            
        Returns:
            str: 検索結果（テキスト形式）
        """
        try:
            # TODO: 実際の検索API統合（Google Custom Search API、Bing Search API等）
            # 現在はモックデータを返す
            results = []
            for i in range(min(num_results, 5)):
                results.append(
                    f"{i+1}. タイトル: Search Result {i+1} for '{query}'\n"
                    f"   URL: https://example.com/result{i+1}\n"
                    f"   概要: This is a snippet for result {i+1} about {query}..."
                )
            
            output = f"検索クエリ: {query}\n"
            output += f"結果数: {len(results)}\n\n"
            output += "\n\n".join(results)
            
            return output
            
        except Exception as e:
            return f"エラー: Web検索に失敗しました - {str(e)}"
    
    async def _arun(self, query: str, num_results: int = 5) -> str:
        """
        Web検索を実行（非同期版）
        
        Args:
            query: 検索クエリ
            num_results: 取得する結果数
            
        Returns:
            str: 検索結果（テキスト形式）
        """
        # 非同期実装は同期版を呼び出す
        # 実際の実装では非同期HTTPクライアントを使用
        return self._run(query, num_results)

