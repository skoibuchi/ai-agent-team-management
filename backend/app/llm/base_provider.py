from abc import ABC, abstractmethod
from typing import Iterator


class BaseLLMProvider(ABC):
    """LLMプロバイダーの基底クラス"""
    
    @abstractmethod
    def generate(self, prompt: str, config: dict) -> str:
        """レスポンスを生成"""
        pass
    
    @abstractmethod
    def stream_generate(self, prompt: str, config: dict) -> Iterator[str]:
        """ストリーミングレスポンスを生成"""
        pass
    
    @abstractmethod
    def estimate_cost(self, tokens: int) -> float:
        """コストを推定"""
        pass
