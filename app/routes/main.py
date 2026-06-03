"""
LinkPay - Routes principales (pagina publica)
"""

from flask import Blueprint, render_template_string, request, redirect, abort
from app.models import User, Link, PageView, ClickEvent
from app import db
from zoo_analytics import track_event
import hashlib

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return redirect('/auth/register')

@main_bp.route('/<username>')
def public_page(username):
    user = User.query.filter_by(username=username, is_active_user=True).first_or_404()
    links = user.active_links
    
    # Trackear visita
    ip = request.remote_addr
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16] if ip else None
    try:
        pv = PageView(username=username, ip_hash=ip_hash, referer=request.referrer, user_agent=request.headers.get('User-Agent', '')[:300])
        db.session.add(pv)
        db.session.commit()
    except Exception:
        db.session.rollback()
    
    # Metricas (no rompe si falla)
    try:
        track_event('page.view', user_id=user.id, metadata={'path': f'/{username}', 'referer': request.referrer or 'direct'})
    except Exception:
        pass
    
    # Render con CSS inline (sin Jinja para evitar conflicto con CSS braces)
    theme = user.theme or 'dark'
    bg = '#1a1a2e' if theme == 'dark' else '#f5f5f5'
    fg = '#eee' if theme == 'dark' else '#333'
    card_bg = '#16213e' if theme == 'dark' else '#fff'
    border = '#0f83' if theme == 'dark' else '#ddd'
    shadow = '#0f82' if theme == 'dark' else '#0002'
    initial = (user.display_name or user.username)[0].upper()
    
    links_html = ''
    for i, link in enumerate(links):
        bt = ' bt' if i == 0 else ''
        icon = link.icon or ''
        links_html += f'<a href="{link.url}" class="link{bt}" target="_blank" rel="noopener">{icon} {link.title}</a>'
    
    bio_html = f'<div class="bio">{user.bio}</div>' if user.bio else ''
    avatar_html = f'<div class="avatar">{initial}</div>'
    
    html = f'''<!DOCTYPE html><html lang="es"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{(user.display_name or user.username)} | LinkPay</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:{bg};color:{fg};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:40px 20px}}
.avatar{{width:96px;height:96px;border-radius:50%;background:#0f8;display:flex;align-items:center;justify-content:center;font-size:36px;font-weight:bold;margin-bottom:16px;overflow:hidden;color:#000}}
.name{{font-size:22px;font-weight:600;margin-bottom:8px}}
.bio{{font-size:14px;opacity:.7;margin-bottom:24px;text-align:center;max-width:400px}}
.links{{width:100%;max-width:480px;display:flex;flex-direction:column;gap:12px}}
.link{{display:block;padding:14px 20px;background:{card_bg};border-radius:12px;text-decoration:none;color:inherit;font-size:15px;font-weight:500;text-align:center;border:1px solid {border};transition:transform .15s,box-shadow .15s}}
.link:hover{{transform:translateY(-2px);box-shadow:0 4px 12px {shadow}}}
.bt{{border-color:#0f8}}
.footer{{margin-top:30px;font-size:11px;opacity:.4}}
.footer a{{color:inherit}}
</style></head><body>
{avatar_html}
<div class="name">{(user.display_name or user.username)}</div>
{bio_html}
<div class="links">
{links_html}
</div>
<div class="footer">Powered by <a href="/">LinkPay</a></div>
</body></html>'''
    
    return html
