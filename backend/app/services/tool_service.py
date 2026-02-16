from app import db
from app.models import Tool


class ToolService:
    """ツール管理サービス"""
    
    def register_tool(self, name, category, type, description=None, config=None):
        """ツールを登録"""
        # 既存のツールをチェック
        existing = Tool.query.filter_by(name=name).first()
        if existing:
            raise ValueError(f'Tool {name} already exists')
        
        tool = Tool(
            name=name,
            category=category,
            description=description,
            type=type,
            config=config or {},
            is_builtin=False,
            is_active=True
        )
        
        db.session.add(tool)
        db.session.commit()
        
        return tool
    
    def get_tool(self, tool_id):
        """ツールを取得"""
        return Tool.query.get(tool_id)
    
    def get_tool_by_name(self, name):
        """名前でツールを取得"""
        return Tool.query.filter_by(name=name).first()
    
    def update_tool(self, tool_id, **kwargs):
        """ツールを更新"""
        tool = Tool.query.get(tool_id)
        if not tool:
            raise ValueError(f'Tool {tool_id} not found')
        
        # 組み込みツールは編集不可
        if tool.is_builtin:
            raise ValueError('Cannot edit built-in tools')
        
        for key, value in kwargs.items():
            if hasattr(tool, key) and key != 'is_builtin':
                setattr(tool, key, value)
        
        db.session.commit()
        return tool
    
    def delete_tool(self, tool_id):
        """ツールを削除"""
        tool = Tool.query.get(tool_id)
        if not tool:
            raise ValueError(f'Tool {tool_id} not found')
        
        # 組み込みツールは削除不可
        if tool.is_builtin:
            raise ValueError('Cannot delete built-in tools')
        
        db.session.delete(tool)
        db.session.commit()
    
    def list_tools(self, category=None, is_active=None):
        """ツール一覧を取得"""
        query = Tool.query
        
        if category:
            query = query.filter_by(category=category)
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        return query.all()
    
    def select_tools_for_task(self, task_description):
        """タスクに適したツールを選定"""
        # TODO: LLMを使ってタスクを分析し、適切なツールを選定
        # 現在は簡易実装（すべてのアクティブなツールを返す）
        return Tool.query.filter_by(is_active=True).all()
    
    def execute_tool(self, tool_id, parameters):
        """ツールを実行"""
        tool = Tool.query.get(tool_id)
        if not tool:
            raise ValueError(f'Tool {tool_id} not found')
        
        if not tool.is_active:
            raise ValueError(f'Tool {tool.name} is not active')
        
        # TODO: 実際のツール実行ロジックを実装
        # 現在は簡易実装
        return {
            'success': True,
            'tool': tool.name,
            'parameters': parameters,
            'result': 'Tool execution placeholder'
        }
    
    def test_tool(self, tool_id, parameters):
        """ツールをテスト実行"""
        tool = Tool.query.get(tool_id)
        if not tool:
            raise ValueError(f'Tool {tool_id} not found')
        
        try:
            # テスト実行
            result = self.execute_tool(tool_id, parameters)
            return {
                'success': True,
                'message': 'Tool test successful',
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Tool test failed: {str(e)}'
            }
    
    def initialize_builtin_tools(self):
        """組み込みツールを初期化"""
        builtin_tools = [
            {
                'name': 'file_operations',
                'category': 'file_system',
                'description': 'Read, write, and manage files',
                'type': 'builtin',
                'config': {
                    'operations': ['read', 'write', 'delete', 'list']
                }
            },
            {
                'name': 'web_search',
                'category': 'web',
                'description': 'Search the web for information',
                'type': 'builtin',
                'config': {
                    'search_engine': 'duckduckgo'
                }
            },
            {
                'name': 'code_execution',
                'category': 'code',
                'description': 'Execute Python code safely',
                'type': 'builtin',
                'config': {
                    'timeout': 30,
                    'max_memory': '512MB'
                }
            }
        ]
        
        for tool_data in builtin_tools:
            existing = Tool.query.filter_by(name=tool_data['name']).first()
            if not existing:
                tool = Tool(
                    name=tool_data['name'],
                    category=tool_data['category'],
                    description=tool_data['description'],
                    type=tool_data['type'],
                    config=tool_data['config'],
                    is_builtin=True,
                    is_active=True
                )
                db.session.add(tool)
        
        db.session.commit()
