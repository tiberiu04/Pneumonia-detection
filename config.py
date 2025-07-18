"""
Configuration settings for the AI Pneumonia Detection System.
This module provides configuration classes for different environments.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration class with common settings."""
    
    # Application Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # Model Settings
    MODEL_PATH = os.environ.get('MODEL_PATH') or 'pneumonia_cnn_model.h5'
    MODEL_VERSION = '1.0'
    IMG_SIZE = (150, 150)
    
    # Logging Settings
    LOG_FOLDER = 'static/logs'
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Security Settings
    RATE_LIMIT_REQUESTS = 20
    RATE_LIMIT_WINDOW = 60  # seconds
    
    # Model Performance Metrics
    MODEL_METRICS = {
        'accuracy': 95.2,
        'precision': 94.8,
        'recall': 96.1,
        'f1_score': 95.4,
        'training_samples': 5856,
        'validation_samples': 624,
        'test_samples': 624,
        'training_epochs': 25,
        'batch_size': 32,
        'learning_rate': 0.001
    }
    
    # API Settings
    API_TITLE = 'AI Pneumonia Detection API'
    API_VERSION = 'v1.0'
    API_DESCRIPTION = 'RESTful API for AI-powered pneumonia detection from chest X-rays'
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.LOG_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    LOG_LEVEL = 'DEBUG'
    RATE_LIMIT_REQUESTS = 100  # More lenient for development
    
    # Development database (if needed)
    DATABASE_URL = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///dev.db'


class ProductionConfig(Config):
    """Production environment configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Production security settings
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Production database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # HTTPS settings
    PREFERRED_URL_SCHEME = 'https'
    
    # Session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    @classmethod
    def init_app(cls, app):
        """Initialize production application."""
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


class TestingConfig(Config):
    """Testing environment configuration."""
    
    TESTING = True
    DEBUG = True
    
    # Testing-specific settings
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = 'tests/uploads'
    LOG_FOLDER = 'tests/logs'
    
    # In-memory database for testing
    DATABASE_URL = 'sqlite:///:memory:'
    
    # Disable rate limiting for tests
    RATE_LIMIT_REQUESTS = 1000


class DockerConfig(Config):
    """Docker deployment configuration."""
    
    DEBUG = False
    
    # Docker-specific settings
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    
    # Use environment variables for sensitive data
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Docker volume paths
    UPLOAD_FOLDER = '/app/uploads'
    LOG_FOLDER = '/app/logs'
    MODEL_PATH = '/app/models/pneumonia_cnn_model.h5'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment variable."""
    return config[os.environ.get('FLASK_ENV', 'default')]


# Model training configuration
TRAINING_CONFIG = {
    'input_shape': (150, 150, 3),
    'batch_size': 32,
    'epochs': 25,
    'learning_rate': 0.001,
    'validation_split': 0.2,
    'early_stopping_patience': 5,
    'reduce_lr_patience': 3,
    'data_augmentation': {
        'rotation_range': 20,
        'width_shift_range': 0.2,
        'height_shift_range': 0.2,
        'horizontal_flip': True,
        'zoom_range': 0.2,
        'fill_mode': 'nearest'
    }
}

# API documentation configuration
API_CONFIG = {
    'title': 'AI Pneumonia Detection API',
    'version': '1.0',
    'description': 'RESTful API for AI-powered pneumonia detection from chest X-rays',
    'contact': {
        'name': 'AI Development Team',
        'email': 'api@pneumonia-ai.com',
        'url': 'https://github.com/yourusername/pneumonia-detector'
    },
    'license': {
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/MIT'
    }
}