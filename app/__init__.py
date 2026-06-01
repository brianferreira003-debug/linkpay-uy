"""
LinkPay Uruguay - MVP
Link-in-bio con pagos MercadoPago integrados.
Metricas integradas desde el dia 1 via zoo_analytics.
"""

import os
import secrets
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()

@login.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

def create_app(config=None):
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///linkpay.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    
    # MercadoPago
    app.config['MP_PUBLIC_KEY'] = os.environ.get('MP_PUBLIC_KEY', '')
    app.config['MP_ACCESS_TOKEN'] = os.environ.get('MP_ACCESS_TOKEN', '')
    
    if config:
        app.config.update(config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    login.login_view = 'auth.login'
    
    # Inicializar metricas
    from zoo_analytics import Analytics
    analytics = Analytics(app, db, project_slug='linkpay')
    
    # Registrar blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dash_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dash_bp, url_prefix='/dashboard')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    with app.app_context():
        db.create_all()
    
    return app
