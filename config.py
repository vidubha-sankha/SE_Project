"""
Configuration file for Road Damage Detection System
Sri Lanka Road Maintenance Monitoring
"""
import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sri-lanka-road-damage-2025-secret-key'
    
    # Database settings
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database', 'road_damage.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}
    
    # Model settings
    MODEL_PATH = os.path.join(BASE_DIR, 'model', 'road_damage_detector.h5')
    CLASS_INDICES_PATH = os.path.join(BASE_DIR, 'model', 'class_indices.json')
    METADATA_PATH = os.path.join(BASE_DIR, 'model', 'model_metadata.json')
    
    # Image processing settings
    IMG_SIZE = 224
    
    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.90
    MEDIUM_CONFIDENCE_THRESHOLD = 0.70
    
    # Severity mapping based on confidence
    SEVERITY_MAPPING = {
        'critical': {'min': 0.95, 'color': '#dc3545', 'label': 'Critical'},
        'high': {'min': 0.85, 'color': '#fd7e14', 'label': 'High'},
        'medium': {'min': 0.70, 'color': '#ffc107', 'label': 'Medium'},
        'low': {'min': 0.0, 'color': '#28a745', 'label': 'Low'}
    }
    
    # Pagination
    REPORTS_PER_PAGE = 20
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Sri Lanka GPS bounds (for validation)
    SL_LAT_MIN = 5.9
    SL_LAT_MAX = 9.9
    SL_LON_MIN = 79.5
    SL_LON_MAX = 82.0