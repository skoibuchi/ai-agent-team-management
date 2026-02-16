"""
タスク分析API
タスクから必要なツールを自動推奨
"""
import asyncio
from flask import Blueprint, request, jsonify
from app.services.task_analyzer import TaskAnalyzer
from app.models import LLMSetting
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama

task_analysis_bp = Blueprint('task_analysis', __name__)

# Watsonxは条件付きインポート
try:
    from langchain_ibm import WatsonxLLM
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False


def _create_llm(llm_setting: LLMSetting):
    """
    LLM設定からLangChain LLMインスタンスを作成
    """
    provider = llm_setting.provider
    api_key = llm_setting.get_api_key()
    model = llm_setting.default_model
    config = llm_setting.config or {}
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 2000)
    
    if provider == "openai" or provider == "github":
        # OpenAI または GitHub Models (OpenAI互換)
        kwargs = {
            "model": model or "gpt-4",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": api_key
        }
        # base_urlが設定されている場合は追加（GitHub Models用）
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
    elif provider == "watsonx":
        if not WATSONX_AVAILABLE:
            raise ValueError("langchain_ibm is not installed")
        
        # URLの設定（優先順位: base_url > config['url'] > デフォルト値）
        url = llm_setting.base_url or config.get("url") or "https://us-south.ml.cloud.ibm.com"
        
        # project_idの必須チェック
        project_id = config.get("project_id")
        if not project_id:
            raise ValueError("watsonx.ai requires 'project_id' in config")
        
        return WatsonxLLM(
            model_id=model or "ibm/granite-13b-chat-v2",
            url=url,
            apikey=api_key,
            project_id=project_id,
            params={
                "temperature": temperature,
                "max_new_tokens": max_tokens
            }
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


@task_analysis_bp.route('/analyze', methods=['POST'])
def analyze_task():
    """
    タスクを分析して必要なツールを推奨
    
    Request Body:
        {
            "task_description": "タスクの説明",
            "provider": "openai" (optional)
        }
    
    Response:
        {
            "success": true,
            "data": {
                "task_type": "research",
                "complexity": "medium",
                "recommended_tools": ["web_search", "calculator"],
                "reasoning": "推奨理由"
            }
        }
    """
    try:
        data = request.get_json()
        
        # 必須フィールドのチェック
        if 'task_description' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: task_description'
            }), 400
        
        task_description = data['task_description']
        provider = data.get('provider')
        
        # LLM設定を取得
        if provider:
            llm_setting = LLMSetting.query.filter_by(
                provider=provider,
                is_active=True
            ).first()
        else:
            llm_setting = LLMSetting.query.filter_by(is_active=True).first()
        
        if not llm_setting:
            return jsonify({
                'success': False,
                'error': 'No active LLM configuration found'
            }), 404
        
        # LLMインスタンスを作成
        llm = _create_llm(llm_setting)
        
        # タスク分析
        analyzer = TaskAnalyzer(llm)
        analysis = asyncio.run(analyzer.analyze_task(task_description))
        
        return jsonify({
            'success': True,
            'data': analysis
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@task_analysis_bp.route('/recommend-tools', methods=['POST'])
def recommend_tools():
    """
    タスクに基づいてツールを推奨し、ツールオブジェクトも返す
    
    Request Body:
        {
            "task_description": "タスクの説明",
            "provider": "openai" (optional)
        }
    
    Response:
        {
            "success": true,
            "data": {
                "analysis": {...},
                "tools": [
                    {
                        "name": "web_search",
                        "description": "...",
                        "category": "research"
                    }
                ]
            }
        }
    """
    try:
        data = request.get_json()
        
        if 'task_description' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: task_description'
            }), 400
        
        task_description = data['task_description']
        provider = data.get('provider')
        
        # LLM設定を取得
        if provider:
            llm_setting = LLMSetting.query.filter_by(
                provider=provider,
                is_active=True
            ).first()
        else:
            llm_setting = LLMSetting.query.filter_by(is_active=True).first()
        
        if not llm_setting:
            return jsonify({
                'success': False,
                'error': 'No active LLM configuration found'
            }), 404
        
        # LLMインスタンスを作成
        llm = _create_llm(llm_setting)
        
        # タスク分析
        analyzer = TaskAnalyzer(llm)
        analysis = asyncio.run(analyzer.analyze_task(task_description))
        
        # 推奨ツールの詳細情報を取得
        recommended_tool_names = analysis.get('recommended_tools', [])
        tools = analyzer.get_tools_by_names(recommended_tool_names)
        
        # ツール情報を辞書形式に変換
        tools_data = []
        for tool in tools:
            tools_data.append({
                'name': tool.name,
                'description': tool.description,
                'category': getattr(tool, 'category', 'custom')
            })
        
        return jsonify({
            'success': True,
            'data': {
                'analysis': analysis,
                'tools': tools_data
            }
        }), 200
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in recommend_tools: {error_details}")
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details
        }), 500
