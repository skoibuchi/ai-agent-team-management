from typing import Iterator, Optional
from app.llm.base_provider import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLMプロバイダー（GitHub Models等のカスタムURL対応）"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize OpenAI provider
        
        Args:
            api_key: OpenAI API key
            base_url: Custom base URL (e.g., for GitHub Models)
            model: Default model name
        """
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = model or 'gpt-4'
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """OpenAIクライアントを初期化"""
        try:
            from openai import OpenAI
            
            # カスタムbase_urlがある場合は使用（GitHub Models等）
            if self.base_url:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            else:
                self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package is not installed. Run: pip install openai")
    
    def generate(self, prompt: str, config: dict) -> str:
        """レスポンスを生成"""
        if not self.client:
            raise ValueError("OpenAI client not initialized")
        
        model = config.get('model', self.default_model)
        temperature = config.get('temperature', 0.7)
        max_tokens = config.get('max_tokens', 2000)
        
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def stream_generate(self, prompt: str, config: dict) -> Iterator[str]:
        """ストリーミングレスポンスを生成"""
        if not self.client:
            raise ValueError("OpenAI client not initialized")
        
        model = config.get('model', self.default_model)
        temperature = config.get('temperature', 0.7)
        max_tokens = config.get('max_tokens', 2000)
        
        stream = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def estimate_cost(self, tokens: int) -> float:
        """コストを推定（USD）"""
        # GPT-4の概算コスト（入力トークン）
        cost_per_1k_tokens = 0.03
        return (tokens / 1000) * cost_per_1k_tokens
