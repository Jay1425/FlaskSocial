import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'vb69n83n89sv49es98e59889e9n6g'
    
    # Database configuration for Render.com production
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        # Render.com provides postgres:// but SQLAlchemy 1.4+ requires postgresql://
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLAlchemy engine options to fix threading issues
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0,
        'pool_size': 5
    }
    
    # Production settings for Render.com
    if os.environ.get('RENDER'):
        # Force HTTPS in production
        PREFERRED_URL_SCHEME = 'https'
        SESSION_COOKIE_SECURE = True
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = 'Lax'