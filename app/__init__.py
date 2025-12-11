"""
Flask application factory and initialization.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()


def create_app(config_object=None):
    """
    Application factory pattern.
    
    Args:
        config_object: Configuration object to use
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_object is None:
        from config import get_config
        config_object = get_config()
    
    app.config.from_object(config_object)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*'))
    
    # Register blueprints
    with app.app_context():
        from app.routes import geo, health, docs
        
        app.register_blueprint(geo.bp)
        app.register_blueprint(health.bp)
        app.register_blueprint(docs.bp)
    
    return app
