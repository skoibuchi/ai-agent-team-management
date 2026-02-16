import os
from datetime import timedelta
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()


class Config:
    """基本設定"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///ai_agent_team.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    # LLM API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    WATSONX_API_KEY = os.getenv('WATSONX_API_KEY', '')
    WATSONX_PROJECT_ID = os.getenv('WATSONX_PROJECT_ID', '')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Security
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'dev-encryption-key-change-in-production')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # WebSocket
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = CORS_ORIGINS
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)


class DevelopmentConfig(Config):
    """開発環境設定"""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # SQLクエリログを無効化（必要な場合はTrueに）


class ProductionConfig(Config):
    """本番環境設定"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """テスト環境設定"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 環境に応じた設定を選択
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """現在の環境に応じた設定を取得"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
