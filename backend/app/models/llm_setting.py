from datetime import datetime
from app import db
from cryptography.fernet import Fernet
import os


class LLMSetting(db.Model):
    """LLM設定モデル"""
    
    __tablename__ = 'llm_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False, unique=True)  # openai, anthropic, watsonx, ollama
    api_key_encrypted = db.Column(db.Text)
    base_url = db.Column(db.String(200))
    default_model = db.Column(db.String(100))
    config = db.Column(db.JSON)  # その他の設定
    is_active = db.Column(db.Boolean, default=True)
    
    # タイムスタンプ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LLMSetting {self.provider}>'
    
    @staticmethod
    def _get_cipher():
        """暗号化用のCipherを取得"""
        import base64
        key = os.getenv('ENCRYPTION_KEY', 'dev-encryption-key-change-in-production')
        # キーを32バイトに調整してbase64エンコード
        key_bytes = key.encode()[:32].ljust(32, b'0')
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        return Fernet(fernet_key)
    
    def set_api_key(self, api_key: str):
        """APIキーを暗号化して保存"""
        if api_key:
            cipher = self._get_cipher()
            self.api_key_encrypted = cipher.encrypt(api_key.encode()).decode()
    
    def get_api_key(self) -> str:
        """APIキーを復号化して取得"""
        if self.api_key_encrypted:
            cipher = self._get_cipher()
            return cipher.decrypt(self.api_key_encrypted.encode()).decode()
        return ''
    
    def to_dict(self, include_api_key=False):
        """辞書形式に変換"""
        data = {
            'id': self.id,
            'provider': self.provider,
            'base_url': self.base_url,
            'default_model': self.default_model,
            'config': self.config,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'has_api_key': bool(self.api_key_encrypted)
        }
        
        if include_api_key:
            data['api_key'] = self.get_api_key()
        
        return data
    
    def get_available_models(self):
        """利用可能なモデル一覧を取得"""
        # プロバイダーごとのモデル一覧（最新版）
        models = {
            'openai': [
                'gpt-4o',
                'gpt-4o-mini',
                'gpt-4-turbo',
                'gpt-4',
                'gpt-3.5-turbo'
            ],
            'anthropic': [
                'claude-3-5-sonnet-20241022',
                'claude-3-5-haiku-20241022',
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307'
            ],
            'gemini': [
                'gemini-2.0-flash-exp',
                'gemini-1.5-pro',
                'gemini-1.5-flash',
                'gemini-1.0-pro'
            ],
            'watsonx': [
                'ibm/granite-13b-chat-v2',
                'ibm/granite-13b-instruct-v2',
                'ibm/granite-20b-multilingual',
                'meta-llama/llama-3-70b-instruct',
                'meta-llama/llama-3-8b-instruct',
                'meta-llama/llama-2-70b-chat',
                'meta-llama/llama-2-13b-chat',
                'mistralai/mistral-large',
                'mistralai/mixtral-8x7b-instruct-v01',
                'mistralai/mistral-medium-2505',
                'google/flan-t5-xxl',
                'google/flan-ul2',
                'codellama/codellama-34b-instruct-hf'
            ],
            'ollama': [
                'llama3.1',
                'llama3',
                'llama2',
                'mistral',
                'mixtral',
                'codellama',
                'phi3',
                'gemma2'
            ]
        }
        
        return models.get(self.provider, [])
