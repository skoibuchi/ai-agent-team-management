from flask import Blueprint, request, jsonify
from app.tools import ToolRegistry
from app.tools.dynamic_tool_generator import DynamicToolGenerator
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama

tools_bp = Blueprint('tools', __name__)


@tools_bp.route('', methods=['GET'])
def get_tools():
    """ツール一覧を取得（ToolRegistryから）"""
    try:
        # クエリパラメータでフィルタリング
        category = request.args.get('category')
        
        # ToolRegistryから全ツール情報を取得
        tools_info = ToolRegistry.get_tools_info()
        
        # カテゴリでフィルタリング
        if category:
            tools_info = [t for t in tools_info if t['category'] == category]
        
        return jsonify({
            'success': True,
            'data': tools_info
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tools_bp.route('/<string:tool_name>', methods=['GET'])
def get_tool(tool_name):
    """特定のツールを取得"""
    try:
        tool = ToolRegistry.get_tool(tool_name)
        if not tool:
            return jsonify({
                'success': False,
                'error': f'Tool not found: {tool_name}'
            }), 404
        
        # ツール情報を取得
        tools_info = ToolRegistry.get_tools_info()
        tool_info = next((t for t in tools_info if t['name'] == tool_name), None)
        
        if not tool_info:
            return jsonify({
                'success': False,
                'error': f'Tool info not found: {tool_name}'
            }), 404
        
        return jsonify({
            'success': True,
            'data': tool_info
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tools_bp.route('/categories', methods=['GET'])
def get_categories():
    """ツールカテゴリ一覧を取得"""
    try:
        # ToolRegistryから全ツールを取得してカテゴリを抽出
        tools_info = ToolRegistry.get_tools_info()
        categories = list(set(t['category'] for t in tools_info))
        
        # カテゴリ情報を整形
        categories_data = [
            {
                'value': cat,
                'label': cat.replace('_', ' ').title(),
                'count': sum(1 for t in tools_info if t['category'] == cat)
            }
            for cat in sorted(categories)
        ]
        
        return jsonify({
            'success': True,
            'data': categories_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tools_bp.route('/<string:tool_name>/test', methods=['POST'])
def test_tool(tool_name):
    """ツールをテスト実行"""
    try:
        tool = ToolRegistry.get_tool(tool_name)
        if not tool:
            return jsonify({
                'success': False,
                'error': f'Tool not found: {tool_name}'
            }), 404
        
        data = request.get_json() or {}
        parameters = data.get('parameters', {})
        
        # ツールを実行
        result = tool.invoke(parameters)
        
        return jsonify({
            'success': True,
            'data': {
                'tool_name': tool_name,
                'parameters': parameters,
                'result': result
            },
            'message': 'Tool test completed'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# MCP関連のエンドポイント（将来の拡張用）
@tools_bp.route('/mcp', methods=['GET'])
def get_mcp_tools():
    """MCPツール一覧を取得"""
    try:
        tools_info = ToolRegistry.get_tools_info()
        mcp_tools = [t for t in tools_info if t.get('is_mcp', False)]
        
        return jsonify({
            'success': True,
            'data': mcp_tools
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tools_bp.route('/mcp', methods=['POST'])
def register_mcp_tool():
    """MCPツールを登録（将来の実装）"""
    return jsonify({
        'success': False,
        'error': 'MCP tool registration is not yet implemented'
    }), 501


@tools_bp.route('/generate', methods=['POST'])
def generate_tool():
    """AIを使用してツールを動的に生成"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        description = data.get('description')
        if not description:
            return jsonify({
                'success': False,
                'error': 'description is required'
            }), 400
        
        category = data.get('category', 'custom')
        provider = data.get('provider')  # オプション: 使用するLLMプロバイダー
        
        # LLM設定を取得
        from app.models.llm_setting import LLMSetting
        if provider:
            # 指定されたプロバイダーを使用
            llm_setting = LLMSetting.query.filter_by(provider=provider, is_active=True).first()
            if not llm_setting:
                return jsonify({
                    'success': False,
                    'error': f'LLM provider "{provider}" not found or inactive'
                }), 400
        else:
            # デフォルト: 最初のアクティブなLLM設定を使用
            llm_setting = LLMSetting.query.filter_by(is_active=True).first()
            if not llm_setting:
                return jsonify({
                    'success': False,
                    'error': 'No active LLM setting found. Please configure an LLM provider in Settings.'
                }), 400
        
        # LangChain LLMインスタンスを作成
        llm = _create_llm_instance(llm_setting)
        
        # DynamicToolGeneratorを使用してツールを生成
        generator = DynamicToolGenerator(llm)
        
        # asyncメソッドを同期的に実行
        import asyncio
        tool_instance, tool_code = asyncio.run(
            generator.generate_tool_from_description(
                description=description,
                user_requirements={"category": category}
            )
        )
        
        # ToolRegistryに登録
        ToolRegistry.register(
            tool_instance=tool_instance,
            category=category,
            metadata={
                'is_builtin': False,
                'is_mcp': False,
                'is_dynamic': True,
                'description': description
            }
        )
        
        # 生成されたツール情報を返す
        tools_info = ToolRegistry.get_tools_info()
        tool_info = next((t for t in tools_info if t['name'] == tool_instance.name), None)
        
        return jsonify({
            'success': True,
            'data': tool_info,
            'message': f'Tool "{tool_instance.name}" generated successfully'
        }), 201
        
    except ValueError as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Validation error: {str(e)}'
        }), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tools_bp.route('/register', methods=['POST'])
def register_custom_tool():
    """手動でツールコードを登録"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        tool_code = data.get('code')
        if not tool_code:
            return jsonify({
                'success': False,
                'error': 'code is required'
            }), 400
        
        category = data.get('category', 'custom')
        
        # アクティブなLLM設定を取得（検証用）
        from app.models.llm_setting import LLMSetting
        default_setting = LLMSetting.query.filter_by(is_active=True).first()
        if not default_setting:
            return jsonify({
                'success': False,
                'error': 'No active LLM setting found. Please configure an LLM provider in Settings.'
            }), 400
        
        llm = _create_llm_instance(default_setting)
        generator = DynamicToolGenerator(llm)
        
        # コードを検証
        is_valid, error_msg = generator._validate_code(tool_code)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'Code validation failed: {error_msg}'
            }), 400
        
        # ツールインスタンスを作成（tool_specはNoneでOK）
        tool_instance = generator._create_dynamic_tool(None, tool_code)
        
        # ToolRegistryに登録
        ToolRegistry.register(
            tool_instance=tool_instance,
            category=category,
            metadata={
                'is_builtin': False,
                'is_mcp': False,
                'is_dynamic': True,
                'is_custom': True,
                'description': tool_instance.description
            }
        )
        
        # 生成されたツール情報を返す
        tools_info = ToolRegistry.get_tools_info()
        tool_info = next((t for t in tools_info if t['name'] == tool_instance.name), None)
        
        return jsonify({
            'success': True,
            'data': tool_info,
            'message': f'Tool "{tool_instance.name}" registered successfully'
        }), 201
        
    except ValueError as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Validation error: {str(e)}'
        }), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _create_llm_instance(llm_setting):
    """
    LLM設定からLangChain LLMインスタンスを作成
    
    Args:
        llm_setting: LLMSetting モデルインスタンス
        
    Returns:
        LangChain LLMインスタンス
    """
    provider = llm_setting.provider
    api_key = llm_setting.get_api_key()
    model = llm_setting.default_model
    temperature = llm_setting.config.get('temperature', 0.7) if llm_setting.config else 0.7
    max_tokens = llm_setting.config.get('max_tokens', 2000) if llm_setting.config else 2000
    
    if provider == "openai":
        kwargs = {
            "model": model or "gpt-4",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": api_key
        }
        if llm_setting.base_url:
            kwargs["base_url"] = llm_setting.base_url
        return ChatOpenAI(**kwargs)
    
    elif provider == "anthropic":
        return ChatAnthropic(
            model=model or "claude-3-5-sonnet-20241022",
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key
        )
    
    elif provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=model or "gemini-2.0-flash-exp",
            temperature=temperature,
            max_output_tokens=max_tokens,
            google_api_key=api_key
        )
    
    elif provider == "ollama":
        return ChatOllama(
            model=model or "llama2",
            temperature=temperature,
            base_url=llm_setting.base_url or "http://localhost:11434"
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
