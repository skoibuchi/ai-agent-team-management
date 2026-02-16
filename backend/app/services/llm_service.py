from app.models import LLMSetting


class LLMService:
    """LLM統合サービス"""
    
    def __init__(self):
        self.providers = {}
    
    def get_provider(self, provider_name):
        """プロバイダーを取得"""
        # キャッシュから取得
        if provider_name in self.providers:
            return self.providers[provider_name]
        
        # データベースから設定を取得
        setting = LLMSetting.query.filter_by(provider=provider_name).first()
        if not setting or not setting.is_active:
            raise ValueError(f'Provider {provider_name} not found or inactive')
        
        # プロバイダーを初期化
        provider = self._initialize_provider(setting)
        self.providers[provider_name] = provider
        
        return provider
    
    def _initialize_provider(self, setting):
        """プロバイダーを初期化"""
        if setting.provider == 'openai':
            from app.llm.openai_provider import OpenAIProvider
            return OpenAIProvider(
                api_key=setting.get_api_key(),
                base_url=setting.base_url,
                model=setting.default_model
            )
        elif setting.provider == 'anthropic':
            from app.llm.anthropic_provider import AnthropicProvider
            return AnthropicProvider(setting.get_api_key())
        elif setting.provider == 'watsonx':
            from app.llm.watsonx_provider import WatsonxProvider
            # configのコピーを作成
            config = dict(setting.config) if setting.config else {}
            # base_urlをconfigに追加（デフォルト値も設定）
            if setting.base_url:
                config['url'] = setting.base_url
            elif 'url' not in config:
                # base_urlが設定されていない場合はデフォルト値を使用
                config['url'] = 'https://us-south.ml.cloud.ibm.com'
            # default_modelもconfigに追加
            if setting.default_model:
                config['model'] = setting.default_model
            # project_idが必須なので、configに含まれていることを確認
            if 'project_id' not in config:
                raise ValueError("watsonx.ai requires 'project_id' in config")
            return WatsonxProvider(setting.get_api_key(), config)
        elif setting.provider == 'ollama':
            from app.llm.ollama_provider import OllamaProvider
            return OllamaProvider(setting.base_url)
        elif setting.provider == 'gemini':
            from app.llm.gemini_provider import GeminiProvider
            return GeminiProvider(
                api_key=setting.get_api_key(),
                model=setting.default_model or 'gemini-pro',
                **setting.config if setting.config else {}
            )
        else:
            raise ValueError(f'Unknown provider: {setting.provider}')
    
    def generate_response(self, provider_name, prompt, config=None):
        """レスポンスを生成"""
        provider = self.get_provider(provider_name)
        return provider.generate(prompt, config or {})
    
    def stream_response(self, provider_name, prompt, config=None):
        """ストリーミングレスポンスを生成"""
        provider = self.get_provider(provider_name)
        return provider.stream_generate(prompt, config or {})
    
    def test_connection(self, provider_name):
        """接続をテスト（DBから設定を取得）"""
        try:
            provider = self.get_provider(provider_name)
            # 簡単なテストプロンプト
            result = provider.generate("Say 'Hello'", {'max_tokens': 10})
            return {
                'success': True,
                'message': 'Connection successful',
                'response': result
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}'
            }
    
    def test_connection_with_config(self, config):
        """
        設定を直接指定して接続をテスト
        
        Args:
            config: テスト用の設定
                - provider: プロバイダー名
                - api_key: APIキー
                - base_url: ベースURL（オプション）
                - default_model: デフォルトモデル（オプション）
                - config: 追加設定（オプション）
        
        Returns:
            dict: テスト結果
        """
        try:
            provider_name = config.get('provider')
            api_key = config.get('api_key')
            base_url = config.get('base_url')
            default_model = config.get('default_model')
            provider_config = config.get('config', {})
            
            # プロバイダーを一時的に初期化
            if provider_name == 'openai':
                from app.llm.openai_provider import OpenAIProvider
                provider = OpenAIProvider(
                    api_key=api_key,
                    base_url=base_url,
                    model=default_model
                )
            elif provider_name == 'anthropic':
                from app.llm.anthropic_provider import AnthropicProvider
                provider = AnthropicProvider(api_key)
            elif provider_name == 'watsonx':
                from app.llm.watsonx_provider import WatsonxProvider
                # base_urlとdefault_modelもconfigに追加
                if base_url:
                    provider_config['url'] = base_url
                if default_model:
                    provider_config['model'] = default_model
                provider = WatsonxProvider(api_key, provider_config)
            elif provider_name == 'ollama':
                from app.llm.ollama_provider import OllamaProvider
                provider = OllamaProvider(base_url)
            elif provider_name == 'gemini':
                from app.llm.gemini_provider import GeminiProvider
                provider = GeminiProvider(
                    api_key=api_key,
                    model=default_model or 'gemini-pro',
                    **provider_config
                )
            else:
                raise ValueError(f'Unknown provider: {provider_name}')
            
            # 簡単なテストプロンプト
            result = provider.generate("Say 'Hello'", {'max_tokens': 10})
            
            return {
                'success': True,
                'message': 'Connection successful',
                'response': result
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}'
            }
    
    def get_available_models(self, provider_name):
        """利用可能なモデル一覧を取得"""
        provider = self.get_provider(provider_name)
        return provider.get_available_models()
    
    def estimate_cost(self, provider_name, tokens):
        """コストを推定"""
        provider = self.get_provider(provider_name)
        return provider.estimate_cost(tokens)
