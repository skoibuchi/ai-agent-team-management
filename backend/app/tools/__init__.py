"""
ツールモジュール（LangChain標準）
"""
from typing import List, Dict, Any
from langchain_core.tools import BaseTool
from app.tools.web_search_tool import WebSearchTool
from app.tools.file_tool import FileReadTool, FileWriteTool, FileListTool
from app.tools.human_input_tool import HumanInputTool, create_human_input_tool


class ToolRegistry:
    """
    ツールレジストリ
    
    LangChain標準のツールを管理します。
    すべてのツールはlangchain_core.tools.BaseToolを継承しています。
    """
    
    _tools: List[BaseTool] = []
    _tool_metadata: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register(cls, tool_instance: BaseTool, category: str = "general", metadata: Dict[str, Any] | None = None):
        """
        ツールを登録
        
        Args:
            tool_instance: ツールのインスタンス
            category: ツールのカテゴリ
            metadata: 追加のメタデータ
        """
        cls._tools.append(tool_instance)
        cls._tool_metadata[tool_instance.name] = {
            "category": category,
            "is_builtin": True,
            "is_mcp": False,
            **(metadata or {})
        }
    
    @classmethod
    def register_mcp_tool(cls, tool_instance: BaseTool, category: str = "mcp", metadata: Dict[str, Any] | None = None):
        """
        MCPツールを登録
        
        Args:
            tool_instance: ツールのインスタンス
            category: ツールのカテゴリ
            metadata: 追加のメタデータ
        """
        cls._tools.append(tool_instance)
        cls._tool_metadata[tool_instance.name] = {
            "category": category,
            "is_builtin": False,
            "is_mcp": True,
            **(metadata or {})
        }
    
    @classmethod
    def get_tool(cls, name: str) -> BaseTool:
        """
        名前でツールを取得
        
        Args:
            name: ツール名
            
        Returns:
            BaseTool: ツールインスタンス
        """
        for tool in cls._tools:
            if tool.name == name:
                return tool
        return None
    
    @classmethod
    def get_all_tools(cls) -> List[BaseTool]:
        """
        すべてのツールを取得
        
        Returns:
            List[BaseTool]: ツールのリスト
        """
        return cls._tools.copy()
    
    @classmethod
    def get_tools_info(cls) -> List[Dict[str, Any]]:
        """
        すべてのツール情報を取得（フロントエンド用）
        
        Returns:
            List[Dict]: ツール情報のリスト
        """
        tools_info = []
        for tool in cls._tools:
            metadata = cls._tool_metadata.get(tool.name, {})
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "category": metadata.get("category", "general"),
                "is_builtin": metadata.get("is_builtin", True),
                "is_mcp": metadata.get("is_mcp", False),
                "is_active": True,
            })
        return tools_info
    
    @classmethod
    def get_tools_by_names(cls, names: List[str]) -> List[BaseTool]:
        """
        名前のリストでツールを取得
        
        Args:
            names: ツール名のリスト
            
        Returns:
            List[BaseTool]: ツールのリスト
        """
        return [tool for tool in cls._tools if tool.name in names]
    
    @classmethod
    def get_tools_by_category(cls, category: str) -> List[BaseTool]:
        """
        カテゴリでツールを取得
        
        Args:
            category: カテゴリ名
            
        Returns:
            List[BaseTool]: ツールのリスト
        """
        return [
            tool for tool in cls._tools
            if cls._tool_metadata.get(tool.name, {}).get("category") == category
        ]
    
    @classmethod
    def clear(cls):
        """すべてのツールをクリア"""
        cls._tools = []
        cls._tool_metadata = {}


# 基本ツールを登録
ToolRegistry.register(WebSearchTool(), category="research")
ToolRegistry.register(FileReadTool(), category="file_operations")
ToolRegistry.register(FileWriteTool(), category="file_operations")
ToolRegistry.register(FileListTool(), category="file_operations")

# HumanInputToolを登録（ダミーのtask_id=0で登録、実際の使用時は動的に生成）
# これによりツール一覧に表示され、エージェント作成時に選択可能になる
ToolRegistry.register(
    create_human_input_tool(task_id=0),
    category="interaction",
    metadata={
        "description": "対話モードでユーザーに質問するためのツール。実行時に自動的に追加されます。",
        "auto_added": True  # 実行時に自動追加されることを示すフラグ
    }
)


__all__ = [
    'ToolRegistry',
    'WebSearchTool',
    'FileReadTool',
    'FileWriteTool',
    'FileListTool',
    'HumanInputTool',
    'create_human_input_tool'
]
