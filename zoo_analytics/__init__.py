"""
ZOO Analytics - Modulo simple de metricas para Flask.
Cada proyecto define sus propias tablas. Zoo-analytics solo trackea eventos.

Tabla requerida (se crea automaticamente):
    CREATE TABLE za_events (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id  INTEGER NOT NULL,
        user_id     INTEGER,
        event_type  VARCHAR(50) NOT NULL,
        metadata    TEXT DEFAULT '{}',
        ip_hash     VARCHAR(64),
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

Uso:
    from zoo_analytics import track_event, track_page_view, Analytics
    analytics = Analytics(app, db, project_slug='linkpay')
    track_event('user.registered', user_id=1)
"""

import json
import time
import hashlib
import threading
import datetime
from functools import wraps
from flask import request, g, current_app

_event_buffer = []
_buffer_lock = threading.Lock()
_current_db = None
_project_slug = None

def _hash_ip(ip):
    if not ip: return None
    return hashlib.sha256(ip.encode()).hexdigest()[:16]

def _flush_buffer():
    global _event_buffer
    with _buffer_lock:
        if not _event_buffer: return
        events = list(_event_buffer)
        _event_buffer = []
    try:
        for e in events:
            _current_db.session.execute(_current_db.text(
                "INSERT INTO za_events (project_id, user_id, event_type, metadata, ip_hash, created_at) VALUES (:p,:u,:t,:m,:i,:c)"
            ), {'p':e['project_id'],'u':e['user_id'],'t':e['event_type'],'m':e['metadata'],'i':e['ip_hash'],'c':str(e['created_at'])})
        _current_db.session.commit()
    except Exception as ex:
        current_app.logger.error(f'Analytics: {ex}')
        try: _current_db.session.rollback()
        except: pass

def _periodic_flush():
    while True:
        time.sleep(30)
        try: _flush_buffer()
        except: pass

threading.Thread(target=_periodic_flush, daemon=True).start()

def _add_buffer(e):
    with _buffer_lock:
        _event_buffer.append(e)
        if len(_event_buffer) >= 50:
            _flush_buffer()

def track_event(event_type, user_id=None, metadata=None):
    pid = getattr(g, '_analytics_project_id', None)
    if not pid: return
    m = json.dumps({k:str(v)[:200] for k,v in (metadata or {}).items()})[:1024]
    ip = request.remote_addr if request else None
    _add_buffer({'project_id':pid,'user_id':user_id,'event_type':event_type,'metadata':m,'ip_hash':_hash_ip(ip),'created_at':datetime.datetime.utcnow()})

def track_page_view(path=None, user_id=None):
    if path is None and request: path = request.path
    track_event('page.view', user_id=user_id, metadata={'path':str(path)[:100]})

def track(event_type, metadata_func=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            try:
                track_event(event_type, user_id=getattr(g,'user_id',None), metadata=metadata_func(result) if metadata_func else {})
            except: pass
            return result
        return wrapper
    return decorator

class Analytics:
    def __init__(self, app=None, db=None, project_slug=None):
        global _current_db
        _current_db = db
        if app: self.init_app(app, db, project_slug)

    def init_app(self, app, db, project_slug):
        global _current_db, _project_slug
        _current_db = db
        _project_slug = project_slug

        with app.app_context():
            db.session.execute(db.text(
                "CREATE TABLE IF NOT EXISTS za_events (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, user_id INTEGER, event_type VARCHAR(50) NOT NULL, metadata TEXT DEFAULT '{}', ip_hash VARCHAR(64), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            ))
            db.session.execute(db.text(
                "CREATE TABLE IF NOT EXISTS za_projects (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(100) NOT NULL, slug VARCHAR(50) NOT NULL UNIQUE)"
            ))
            existing = db.session.execute(db.text("SELECT id FROM za_projects WHERE slug = :s"), {'s': project_slug}).fetchone()
            if not existing:
                db.session.execute(db.text("INSERT INTO za_projects (name, slug) VALUES (:n, :s)"), {'n': project_slug.title(), 's': project_slug})
            db.session.commit()

        @app.before_request
        def _set_pid():
            g._analytics_project_id = None
            try:
                row = _current_db.session.execute(_current_db.text("SELECT id FROM za_projects WHERE slug = :s"), {'s': _project_slug}).fetchone()
                if row: g._analytics_project_id = row[0]
            except: pass

        from zoo_analytics.dashboard import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
