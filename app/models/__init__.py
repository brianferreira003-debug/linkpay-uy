"""
LinkPay - Modelos de Datos
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'lp_users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(120))
    bio = db.Column(db.String(300))
    avatar_url = db.Column(db.String(500))
    theme = db.Column(db.String(20), default='dark')
    plan = db.Column(db.String(20), default='free')
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    links = db.relationship('Link', backref='owner', lazy='dynamic', order_by='Link.position')
    payments = db.relationship('Payment', backref='owner', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def page_url(self):
        return f'/{self.username}'
    
    @property
    def active_links(self):
        return self.links.filter_by(is_active=True).all()


class Link(db.Model):
    __tablename__ = 'lp_links'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('lp_users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    position = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    click_count = db.Column(db.Integer, default=0)
    icon = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payment(db.Model):
    __tablename__ = 'lp_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('lp_users.id'), nullable=False)
    mp_preference_id = db.Column(db.String(100))
    mp_payment_id = db.Column(db.String(100))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='UYU')
    description = db.Column(db.String(200))
    payer_name = db.Column(db.String(120))
    payer_email = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)


class PageView(db.Model):
    __tablename__ = 'lp_page_views'
    
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(80), nullable=False, index=True)
    ip_hash = db.Column(db.String(64))
    referer = db.Column(db.String(500))
    user_agent = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class ClickEvent(db.Model):
    __tablename__ = 'lp_clicks'
    
    id = db.Column(db.BigInteger, primary_key=True)
    link_id = db.Column(db.Integer, db.ForeignKey('lp_links.id'))
    username = db.Column(db.String(80), nullable=False)
    ip_hash = db.Column(db.String(64))
    referer = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Exports
__all__ = ['User', 'Link', 'Payment', 'PageView', 'ClickEvent']
