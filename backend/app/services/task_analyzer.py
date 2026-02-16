"""
タスク分析サービス
タスクの説明から必要なツールを自動推奨
"""
import json
import re
from typing import Dict, Any, List
from langchain_core.language_models import BaseChatModel
from app.tools import ToolRegistry


class TaskAnalyzer:
    """
    タスクを分析して必要なツールを推奨
    """
    
    def __init__(self, llm: BaseChatModel):
        """
        Args:
            llm: タスク分析に使用するLLM
        """
        self.llm = llm
    
    async def analyze_task(self, task_description: str) -> Dict[str, Any]:
        """
        タスクを分析して必要なツールを推奨
        
        Args:
            task_description: タスクの説明
            
        Returns:
            Dict[str, Any]: 分析結果
                - task_type: タスクの種類
                - complexity: 複雑度
                - recommended_tools: 推奨ツール名のリスト
                - reasoning: 推奨理由
        """
        # 利用可能なツールの情報を取得
        available_tools = self._get_available_tools_description()
        
        # プロンプトを作成
        prompt = f"""あなたはタスク分析の専門家です。以下のタスクを分析して、必要なツールを推奨してください。

タスク:
{task_description}

利用可能なツール:
{available_tools}

以下のJSON形式で回答してください（JSONのみ、説明不要）:
{{
    "task_type": "research/analysis/writing/coding/data_processing/communication",
    "complexity": "simple/medium/complex",
    "recommended_tools": ["tool_name1", "tool_name2"],
    "reasoning": "なぜこれらのツールが必要か（日本語で簡潔に）"
}}

注意:
- recommended_toolsには、利用可能なツールの中から最適なものを選んでください
- 必要最小限のツールのみを推奨してください（多くても5個まで）
- ツール名は正確に記載してください
"""
        
        # LLMで分析
        response = await self.llm.ainvoke(prompt)
        
        # レスポンスの型に応じて内容を取得
        # ChatモデルはAIMessageオブジェクト、WatsonxLLMは文字列を返す
        if isinstance(response, str):
            content = response
        else:
            content = response.content
        
        # JSONを抽出
        try:
            # マークダウンのコードブロックを削除
            content = re.sub(r'```json\n?', '', content)
            content = re.sub(r'```\n?', '', content)
            content = content.strip()
            
            # JSONをパース
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = json.loads(content)
            
            # 推奨ツールが実際に存在するか確認
            valid_tools = []
            all_tool_names = [tool.name for tool in ToolRegistry.get_all_tools()]
            
            for tool_name in analysis.get('recommended_tools', []):
                if tool_name in all_tool_names:
                    valid_tools.append(tool_name)
            
            analysis['recommended_tools'] = valid_tools
            
            return analysis
            
        except (json.JSONDecodeError, KeyError) as e:
            # パースに失敗した場合はデフォルト値を返す
            return {
                'task_type': 'unknown',
                'complexity': 'medium',
                'recommended_tools': [],
                'reasoning': f'タスク分析に失敗しました: {str(e)}'
            }
    
    def _get_available_tools_description(self) -> str:
        """
        利用可能なツールの説明を取得
        
        Returns:
            str: ツールの説明（フォーマット済み）
        """
        tools = ToolRegistry.get_all_tools()
        
        descriptions = []
        for tool in tools:
            descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(descriptions)
    
    def get_tools_by_names(self, tool_names: List[str]) -> List[Any]:
        """
        ツール名のリストから実際のツールオブジェクトを取得
        
        Args:
            tool_names: ツール名のリスト
            
        Returns:
            List[Any]: ツールオブジェクトのリスト
        """
        all_tools = ToolRegistry.get_all_tools()
        selected_tools = []
        
        for tool in all_tools:
            if tool.name in tool_names:
                selected_tools.append(tool)
        
        return selected_tools
