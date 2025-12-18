"""Application configuration settings"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class AppConfig:
    """Application configuration"""
    debug: bool = False
    secret_key: str = os.getenv('SECRET_KEY', 'dev-secret-key')
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    api_host: str = '0.0.0.0'
    api_port: int = 8000
    cors_origins: list = None

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ['http://localhost:3000']

def get_config(env: Optional[str] = None) -> AppConfig:
    """Get configuration for specified environment"""
    env = env or os.getenv('ENVIRONMENT', 'development')

    if env == 'production':
        return AppConfig(
            debug=False,
            api_host='0.0.0.0',
            api_port=80
        )
    elif env == 'testing':
        return AppConfig(
            debug=True,
            database_url='sqlite:///:memory:'
        )
    else:  # development
        return AppConfig(debug=True)
