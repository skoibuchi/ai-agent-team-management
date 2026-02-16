from flask import Blueprint, request, jsonify
from app import db
from app.models import LLMSetting

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/llm', methods=['GET'])
def get_llm_settings():
    """LLM設定一覧を取得"""
    try:
        settings = LLMSetting.query.all()
        return jsonify({
            'success': True,
            'data': [setting.to_dict() for setting in settings]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/llm/<string:provider>', methods=['GET'])
def get_llm_setting(provider):
    """特定のLLM設定を取得"""
    try:
        setting = LLMSetting.query.filter_by(provider=provider).first_or_404()
        return jsonify({
            'success': True,
            'data': setting.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@settings_bp.route('/llm', methods=['POST'])
def create_llm_setting():
    """新しいLLM設定を作成"""
    try:
        data = request.get_json()
        
        # 必須フィールドのチェック
        if 'provider' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: provider'
            }), 400
        
        # 既存の設定をチェック
        existing = LLMSetting.query.filter_by(provider=data['provider']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'Provider already exists'
            }), 400
        
        # 設定の作成
        setting = LLMSetting(
            provider=data['provider'],
            base_url=data.get('base_url'),
            default_model=data.get('default_model'),
            config=data.get('config', {}),
            is_active=data.get('is_active', True)
        )
        
        # APIキーの設定
        if 'api_key' in data and data['api_key']:
            setting.set_api_key(data['api_key'])
        
        db.session.add(setting)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': setting.to_dict(),
            'message': 'LLM setting created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/llm/<string:provider>', methods=['PUT'])
def update_llm_setting(provider):
    """LLM設定を更新"""
    try:
        setting = LLMSetting.query.filter_by(provider=provider).first_or_404()
        data = request.get_json()
        
        # 更新可能なフィールド
        if 'base_url' in data:
            setting.base_url = data['base_url']
        if 'default_model' in data:
            setting.default_model = data['default_model']
        if 'config' in data:
            setting.config = data['config']
        if 'is_active' in data:
            setting.is_active = data['is_active']
        if 'api_key' in data and data['api_key']:
            setting.set_api_key(data['api_key'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': setting.to_dict(),
            'message': 'LLM setting updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/llm/<string:provider>', methods=['DELETE'])
def delete_llm_setting(provider):
    """LLM設定を削除"""
    try:
        setting = LLMSetting.query.filter_by(provider=provider).first_or_404()
        
        db.session.delete(setting)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'LLM setting deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/llm/<string:provider>/models', methods=['GET'])
def get_available_models(provider):
    """利用可能なモデル一覧を取得"""
    try:
        setting = LLMSetting.query.filter_by(provider=provider).first_or_404()
        models = setting.get_available_models()
        
        return jsonify({
            'success': True,
            'data': models
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/llm/<string:provider>/test', methods=['POST'])
def test_llm_connection(provider):
    """
    LLM接続をテスト
    
    リクエストボディから設定を受け取るか、DBから取得してテストします。
    これにより、保存前にテストが可能になります。
    """
    try:
        data = request.get_json() or {}
        
        # リクエストボディに設定がある場合はそれを使用
        if data.get('api_key') or data.get('base_url'):
            # 一時的な設定でテスト
            test_config = {
                'provider': provider,
                'api_key': data.get('api_key'),
                'base_url': data.get('base_url'),
                'default_model': data.get('default_model'),
                'config': data.get('config', {})
            }
        else:
            # DBから設定を取得
            setting = LLMSetting.query.filter_by(provider=provider).first()
            if not setting:
                return jsonify({
                    'success': False,
                    'error': f'No configuration found for provider: {provider}. Please provide api_key in request body.'
                }), 404
            
            test_config = {
                'provider': provider,
                'api_key': setting.get_api_key(),
                'base_url': setting.base_url,
                'default_model': setting.default_model,
                'config': setting.config or {}
            }
        
        # 接続テスト
        from app.services.llm_service import LLMService
        llm_service = LLMService()
        
        result = llm_service.test_connection_with_config(test_config)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Connection test completed successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/providers', methods=['GET'])
def get_providers():
    """利用可能なLLMプロバイダー一覧を取得"""
    try:
        providers = [
            {
                'value': 'openai',
                'label': 'OpenAI',
                'description': 'GPT-4o, GPT-4, GPT-3.5 Turbo',
                'requires_api_key': True
            },
            {
                'value': 'anthropic',
                'label': 'Anthropic',
                'description': 'Claude 3.5 Sonnet, Claude 3 Opus',
                'requires_api_key': True
            },
            {
                'value': 'gemini',
                'label': 'Google Gemini',
                'description': 'Gemini 2.0, Gemini 1.5 Pro',
                'requires_api_key': True
            },
            {
                'value': 'watsonx',
                'label': 'IBM watsonx.ai',
                'description': 'Granite, Llama 2',
                'requires_api_key': True
            },
            {
                'value': 'ollama',
                'label': 'Ollama (Local)',
                'description': 'Llama 3, Mistral, Mixtral',
                'requires_api_key': False
            }
        ]
        
        return jsonify({
            'success': True,
            'data': providers
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
