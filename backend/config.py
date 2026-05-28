import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key_placement_portal_123')
    
    # Database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # /backend
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'placement_portal.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session management
    SESSION_TYPE = 'filesystem'
    
    # Redis Caching
    CACHE_TYPE = 'RedisCache'
    REDIS_URL = 'redis://localhost:6379/0'
    CACHE_REDIS_URL = 'redis://localhost:6379/1'
    
    # Celery settings
    broker_url = 'redis://localhost:6379/2'
    result_backend = 'redis://localhost:6379/2'
    
    # Upload limits/paths (points to backend/static/uploads)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit
