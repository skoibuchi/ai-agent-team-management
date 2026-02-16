from typing import Iterator, Optional
from langchain_ibm import WatsonxLLM
from app.llm.base_provider import BaseLLMProvider


class WatsonxProvider(BaseLLMProvider):
    """IBM watsonx.ai LLMプロバイダー"""
    
    def __init__(self, api_key: str, config: dict):
        """
        watsonx.aiプロバイダーを初期化
        
        Args:
            api_key: IBM Cloud APIキー
            config: 設定（url, project_id, model, temperatureなど）
        """
        self.api_key = api_key
        self.config = config
        
        # 必須パラメータの取得
        self.url = config.get('url', 'https://us-south.ml.cloud.ibm.com')
        self.project_id = config.get('project_id')
        
        if not self.project_id:
            raise ValueError("watsonx.ai requires 'project_id' in config")
        
        # モデルパラメータ
        self.model_id = config.get('model', 'ibm/granite-13b-chat-v2')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2000)
        self.top_p = config.get('top_p', 1.0)
        self.top_k = config.get('top_k', 50)
        
        # LangChain WatsonxLLMクライアントの初期化
        self.client = WatsonxLLM(
            model_id=self.model_id,
            url=self.url,
            apikey=self.api_key,
            project_id=self.project_id,
            params={
                'temperature': self.temperature,
                'max_new_tokens': self.max_tokens,
                'top_p': self.top_p,
                'top_k': self.top_k,
            }
        )
    
    def generate(self, prompt: str, config: Optional[dict] = None) -> str:
        """
        レスポンスを生成
        
        Args:
            prompt: プロンプト
            config: 追加設定（オプション）
        
        Returns:
            生成されたテキスト
        """
        try:
            # 設定のマージ
            params = {
                'temperature': self.temperature,
                'max_new_tokens': self.max_tokens,
                'top_p': self.top_p,
                'top_k': self.top_k,
            }
            
            if config:
                if 'temperature' in config:
                    params['temperature'] = config['temperature']
                if 'max_tokens' in config:
                    params['max_new_tokens'] = config['max_tokens']
                if 'top_p' in config:
                    params['top_p'] = config['top_p']
                if 'top_k' in config:
                    params['top_k'] = config['top_k']
            
            # 一時的にパラメータを更新
            self.client.params = params
            
            # 生成
            response = self.client.invoke(prompt)
            return response
            
        except Exception as e:
            raise Exception(f"watsonx.ai generation failed: {str(e)}")
    
    def stream_generate(self, prompt: str, config: Optional[dict] = None) -> Iterator[str]:
        """
        ストリーミングレスポンスを生成
        
        Args:
            prompt: プロンプト
            config: 追加設定（オプション）
        
        Yields:
            生成されたテキストのチャンク
        """
        try:
            # 設定のマージ
            params = {
                'temperature': self.temperature,
                'max_new_tokens': self.max_tokens,
                'top_p': self.top_p,
                'top_k': self.top_k,
            }
            
            if config:
                if 'temperature' in config:
                    params['temperature'] = config['temperature']
                if 'max_tokens' in config:
                    params['max_new_tokens'] = config['max_tokens']
                if 'top_p' in config:
                    params['top_p'] = config['top_p']
                if 'top_k' in config:
                    params['top_k'] = config['top_k']
            
            # 一時的にパラメータを更新
            self.client.params = params
            
            # ストリーミング生成
            for chunk in self.client.stream(prompt):
                yield chunk
                
        except Exception as e:
            raise Exception(f"watsonx.ai streaming failed: {str(e)}")
    
    def estimate_cost(self, tokens: int) -> float:
        """
        コストを推定（USD）
        
        Args:
            tokens: トークン数
        
        Returns:
            推定コスト（USD）
        """
        # watsonx.aiの概算コスト（モデルによって異なる）
        # Granite: $0.01 per 1K tokens
        # Llama-2: $0.015 per 1K tokens
        # Llama-3: $0.02 per 1K tokens
        
        if 'granite' in self.model_id.lower():
            cost_per_1k_tokens = 0.01
        elif 'llama-3' in self.model_id.lower():
            cost_per_1k_tokens = 0.02
        elif 'llama' in self.model_id.lower():
            cost_per_1k_tokens = 0.015
        elif 'mistral' in self.model_id.lower():
            cost_per_1k_tokens = 0.025
        else:
            cost_per_1k_tokens = 0.01  # デフォルト
        
        return (tokens / 1000) * cost_per_1k_tokens
