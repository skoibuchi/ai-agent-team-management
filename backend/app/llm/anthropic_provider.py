from typing import Iterator
from app.llm.base_provider import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Anthropic (Claude) LLMプロバイダー"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        # TODO: Anthropic クライアントの初期化
    
    def generate(self, prompt: str, config: dict) -> str:
        """レスポンスを生成"""
        # TODO: 実装
        raise NotImplementedError("Anthropic provider not yet implemented")
    
    def stream_generate(self, prompt: str, config: dict) -> Iterator[str]:
        """ストリーミングレスポンスを生成"""
        # TODO: 実装
        raise NotImplementedError("Anthropic provider not yet implemented")
    
    def estimate_cost(self, tokens: int) -> float:
        """コストを推定（USD）"""
        # Claude 3 Opusの概算コスト
        cost_per_1k_tokens = 0.015
        return (tokens / 1000) * cost_per_1k_tokens
