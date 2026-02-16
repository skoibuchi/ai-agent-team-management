from typing import Iterator
from app.llm.base_provider import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """Ollama (ローカルLLM) プロバイダー"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    def generate(self, prompt: str, config: dict) -> str:
        """レスポンスを生成"""
        # TODO: 実装
        raise NotImplementedError("Ollama provider not yet implemented")
    
    def stream_generate(self, prompt: str, config: dict) -> Iterator[str]:
        """ストリーミングレスポンスを生成"""
        # TODO: 実装
        raise NotImplementedError("Ollama provider not yet implemented")
    
    def estimate_cost(self, tokens: int) -> float:
        """コストを推定（ローカルなので0）"""
        return 0.0
