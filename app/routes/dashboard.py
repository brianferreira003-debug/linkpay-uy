"""
LinkPay - Dashboard del usuario (gestion de links, ver estadisticas)
CSS inline, sin Jinja, sin archivos externos.
"""

from flask import Blueprint, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from app.models import Link, Payment, PageView, ClickEvent
from app import db
from zoo_analytics import track_event
from datetime import datetime, timedelta, date
from sqlalchemy import func
import json

dash_bp = Blueprint('dashboard', __name__)

CSS = """<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#eee;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;display:flex;min-height:100vh}
.sb{width:200px;background:#111;border-right:1px solid #222;padding:20px 0;display:flex;flex-direction:column;flex-shrink:0;position:fixed;height:100vh;overflow-y:auto}
.sb .logo{font-size:24px;font-weight:700;color:#0f8;text-align:center;padding:10px 0 20px;border-bottom:1px solid #222;margin-bottom:10px}
.sb a{padding:10px 20px;color:#eee;text-decoration:none;font-size:13px;opacity:.6;display:block}
.sb a:hover,.sb a.ac{opacity:1;background:#1a1a1a;color:#0f8}
.sb .bottom{margin-top:auto;border-top:1px solid #222;padding-top:10px}
.main{flex:1;padding:30px;margin-left:200px;overflow-y:auto;max-width:900px}
h1{font-size:20px;margin-bottom:20px}
.card{background:#111;border:1px solid #222;border-radius:12px;padding:20px;margin-bottom:16px;position:relative}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:#0f8;border-radius:12px 12px 0 0}
.card h3{font-size:13px;opacity:.6;margin-bottom:12px;text-transform:uppercase;letter-spacing:1px}
.add-form{display:flex;gap:8px;flex-wrap:wrap}
.add-form input{flex:1;min-width:120px;padding:10px;border-radius:8px;border:1px solid #333;background:#0a0a0a;color:#eee;font-size:13px}
.add-form input:focus{border-color:#0f8;outline:none}
.add-form button{padding:10px 20px;background:#0f8;color:#000;border:none;border-radius:8px;font-weight:600;cursor:pointer}
.add-form button:hover{background:#0c6}
.table{width:100%;border-collapse:collapse}
.table th,.table td{padding:8px 12px;text-align:left;border-bottom:1px solid #1a1a1a;font-size:12px}
.table th{opacity:.5;font-weight:normal;font-size:10px;text-transform:uppercase;letter-spacing:1px}
tr:hover td{background:#111}
.url{color:#0f8;text-decoration:none;font-size:11px}
.btn-sm{padding:4px 8px;border-radius:4px;border:none;cursor:pointer;font-size:11px}
.btn-danger{background:#f443;color:#f44}
.empty{opacity:.4;font-size:13px;padding:10px 0}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.stat-card{background:#111;border:1px solid #222;border-radius:12px;padding:16px;text-align:center;position:relative}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:#f80;border-radius:12px 12px 0 0}
.stat-card h3{font-size:10px;opacity:.5;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px}
.stat-card .big{font-size:28px;font-weight:700;color:#0f8}
.stat-card .sub{font-size:11px;opacity:.5;margin-top:4px}
label{display:block;font-size:11px;opacity:.5;margin-bottom:4px;margin-top:12px}
textarea{width:100%;padding:10px;border-radius:8px;border:1px solid #333;background:#0a0a0a;color:#eee;font-size:13px;font-family:inherit;resize:vertical;box-sizing:border-box}
select{padding:10px;border-radius:8px;border:1px solid #333;background:#0a0a0a;color:#eee;font-size:13px;width:100%;box-sizing:border-box}
.btn{display:inline-block;padding:8px 16px;background:#0f8;color:#000;border-radius:8px;text-decoration:none;font-size:13px;font-weight:600;border:none;cursor:pointer}
.btn:hover{background:#0c6}
.alert{background:#f443;padding:10px;border-radius:8px;margin-bottom:12px;font-size:13px;color:#f44}
canvas{width:100%!important}
@media(max-width:768px){.sb{width:60px}.sb a span,.sb .logo span{display:none}.main{margin-left:60px}}
</style>"""

def render_page(title, content, active='links'):
    """Renderiza una pagina del dashboard con el layout base."""
    nav_items = [
        ('links', '/dashboard', 'Links'),
        ('pagos', '/dashboard/pagos', 'Pagos'),
        ('stats', '/dashboard/stats', 'Estadisticas'),
        ('settings', '/dashboard/settings', 'Config'),
    ]
    nav_html = ''
    for key, url, label in nav_items:
        cls = ' class="ac"' if active == key else ''
        nav_html += f'<a href="{url}"{cls}>{label}</a>'
    
    user = current_user
    page_url = f'/{user.username}'
    
    html = f"""<!DOCTYPE html><html lang="es"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} | LinkPay</title>{CSS}</head><body>
<div class="sb">
<div class="logo">LP</div>
{nav_html}
<div class="bottom">
<a href="{page_url}" target="_blank">Ver pagina</a>
<a href="/auth/logout">Salir</a>
</div>
</div>
<div class="main">
"""
    # Flash messages
    from flask import get_flashed_messages
    msgs = get_flashed_messages()
    for msg in msgs:
        html += f'<div class="alert">{msg}</div>'
    
    html += content
    html += '</div></body></html>'
    return html

@dash_bp.route('/')
@login_required
def index():
    links = current_user.links.order_by(Link.position).all()
    track_event('page.view', user_id=current_user.id, metadata={'path': '/dashboard'})
    
    content = '<h1>Mis Links</h1>'
    content += '<div class="card"><h3>Nuevo link</h3>'
    content += '<form method="POST" action="/dashboard/link/add" class="add-form">'
    content += '<input type="text" name="title" placeholder="Titulo" required>'
    content += '<input type="url" name="url" placeholder="https://..." required>'
    content += '<input type="text" name="icon" placeholder="Icono (emoji)" maxlength="2">'
    content += '<button type="submit">Agregar</button>'
    content += '</form></div>'
    
    content += f'<div class="card"><h3>Tus links ({len(links)})</h3>'
    
    if links:
        content += '<table class="table"><thead><tr><th>#</th><th>Titulo</th><th>URL</th><th>Clicks</th><th></th></tr></thead><tbody>'
        for link in links:
            content += f'<tr><td>{link.position + 1}</td>'
            content += f'<td>{(link.icon or "") + " " + link.title}</td>'
            content += f'<td><a href="{link.url}" target="_blank" class="url">{link.url[:40]}...</a></td>'
            content += f'<td>{link.click_count}</td>'
            content += f'<td><form method="POST" action="/dashboard/link/{link.id}/delete" style="display:inline">'
            content += f'<button class="btn-sm btn-danger" onclick="return confirm(\'Borrar?\')">X</button>'
            content += '</form></td></tr>'
        content += '</tbody></table>'
    else:
        content += '<p class="empty">No tenes links aun. Agrega el primero arriba.</p>'
    
    content += '</div>'
    return render_page('Links', content, 'links')

@dash_bp.route('/link/add', methods=['POST'])
@login_required
def add_link():
    title = request.form.get('title', '').strip()
    url = request.form.get('url', '').strip()
    icon = request.form.get('icon', '').strip()
    if not title or not url:
        flash('Titulo y URL son obligatorios')
        return redirect(url_for('dashboard.index'))
    link = Link(user_id=current_user.id, title=title, url=url, icon=icon or None, position=current_user.links.count())
    db.session.add(link)
    db.session.commit()
    track_event('action.created', user_id=current_user.id, metadata={'type': 'link', 'title': title})
    return redirect(url_for('dashboard.index'))

@dash_bp.route('/link/<int:link_id>/delete', methods=['POST'])
@login_required
def delete_link(link_id):
    link = Link.query.filter_by(id=link_id, user_id=current_user.id).first_or_404()
    db.session.delete(link)
    db.session.commit()
    track_event('action.deleted', user_id=current_user.id, metadata={'type': 'link', 'id': link_id})
    return redirect(url_for('dashboard.index'))

@dash_bp.route('/stats')
@login_required
def stats():
    username = current_user.username
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    views_today = PageView.query.filter(PageView.username == username, func.date(PageView.created_at) == today).count()
    views_7d = PageView.query.filter(PageView.username == username, func.date(PageView.created_at) >= week_ago).count()
    views_total = PageView.query.filter_by(username=username).count()
    link_count = current_user.links.filter_by(is_active=True).count()
    
    vpd = db.session.query(func.date(PageView.created_at), func.count(PageView.id)).filter(
        PageView.username == username, func.date(PageView.created_at) >= week_ago
    ).group_by(func.date(PageView.created_at)).order_by(func.date(PageView.created_at)).all()
    
    top_links = current_user.links.order_by(Link.click_count.desc()).limit(5).all()
    
    vlabels = json.dumps([str(d[0])[-5:] for d in vpd])
    vvalues = json.dumps([d[1] for d in vpd])
    
    content = '<h1>Estadisticas</h1>'
    content += '<div class="stats-grid">'
    content += f'<div class="stat-card"><h3>Hoy</h3><div class="big">{views_today}</div><div class="sub">Visitas</div></div>'
    content += f'<div class="stat-card"><h3>7 dias</h3><div class="big">{views_7d}</div><div class="sub">Visitas</div></div>'
    content += f'<div class="stat-card"><h3>Total</h3><div class="big">{views_total}</div><div class="sub">Visitas</div></div>'
    content += f'<div class="stat-card"><h3>Links</h3><div class="big">{link_count}</div><div class="sub">Activos</div></div>'
    content += '</div>'
    
    content += '<div class="card"><h3>Visitas por dia (7d)</h3><canvas id="vc" height="150"></canvas></div>'
    
    content += '<div class="card"><h3>Top links por clicks</h3>'
    if top_links:
        content += '<table class="table"><thead><tr><th>Link</th><th>Clicks</th></tr></thead><tbody>'
        for link in top_links:
            content += f'<tr><td>{link.title}</td><td>{link.click_count}</td></tr>'
        content += '</tbody></table>'
    else:
        content += '<p class="empty">Sin datos aun</p>'
    content += '</div>'
    
    # Chart JS
    content += f"""<script>
var c=document.getElementById('vc'),x=c.getContext('2d'),w=c.parentElement.clientWidth-40,h=130;
c.width=w;c.height=h;x.clearRect(0,0,w,h);
var labels={vlabels},values={vvalues};
if(!values.length){{x.fillStyle='#333';x.font='12px monospace';x.fillText('Sin datos aun',10,h/2);return}}
var mx=Math.max.apply(null,values);
values.forEach(function(v,i){{var bh=v/mx*(h-20);x.fillStyle='#0f8';x.fillRect(i*((w-10)/values.length)+2,h-bh-15,(w-10)/values.length-4,bh);x.fillStyle='#555';x.font='9px monospace';x.fillText(labels[i],i*((w-10)/values.length)+2,h-3)}});
</script>"""
    
    return render_page('Estadisticas', content, 'stats')

@dash_bp.route('/settings')
@login_required
def settings():
    content = '<h1>Configuracion</h1>'
    content += '<div class="card"><h3>Perfil</h3>'
    content += '<form method="POST" action="/dashboard/settings/update">'
    content += f'<label>Nombre visible</label><input type="text" name="display_name" value="{current_user.display_name or ""}">'
    content += f'<label>Bio</label><textarea name="bio" rows="3" maxlength="300">{current_user.bio or ""}</textarea>'
    content += '<label>Tema</label><select name="theme">'
    content += f'<option value="dark" {"selected" if current_user.theme == "dark" else ""}>Oscuro</option>'
    content += f'<option value="light" {"selected" if current_user.theme == "light" else ""}>Claro</option>'
    content += '</select>'
    content += '<button type="submit" class="btn" style="margin-top:12px">Guardar</button>'
    content += '</form></div>'
    
    content += '<div class="card"><h3>Tu pagina</h3>'
    content += f'<p style="font-size:13px;word-break:break-all">linkpay.uy/{current_user.username}</p>'
    content += f'<a href="/{current_user.username}" target="_blank" class="btn">Ver pagina publica</a>'
    content += '</div>'
    
    return render_page('Configuracion', content, 'settings')

@dash_bp.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    current_user.display_name = request.form.get('display_name', '').strip() or current_user.username
    current_user.bio = request.form.get('bio', '').strip()[:300]
    current_user.theme = request.form.get('theme', 'dark')
    db.session.commit()
    track_event('user.profile_updated', user_id=current_user.id)
    flash('Perfil actualizado')
    return redirect(url_for('dashboard.settings'))

@dash_bp.route('/pagos')
@login_required
def pagos():
    payments = current_user.payments.order_by(Payment.created_at.desc()).limit(20).all()
    content = '<h1>Pagos</h1>'
    content += '<div class="card"><h3>Historial de pagos</h3>'
    if payments:
        content += '<table class="table"><thead><tr><th>Fecha</th><th>Monto</th><th>Estado</th><th>Descripcion</th></tr></thead><tbody>'
        for p in payments:
            status_color = {'completed':'#0f8','pending':'#fa0','failed':'#f44'}.get(p.status,'#888')
            content += f'<tr><td>{p.created_at.strftime("%d/%m %H:%M") if p.created_at else "-"}</td>'
            content += f'<td>${p.amount} {p.currency}</td>'
            content += f'<td style="color:{status_color}">{p.status}</td>'
            content += f'<td>{p.description or "-"}</td></tr>'
        content += '</tbody></table>'
    else:
        content += '<p class="empty">Sin pagos aun</p>'
    content += '</div>'
    
    # Boton de cobro rapido
    content += '<div class="card"><h3>Generar link de pago</h3>'
    content += '<form method="POST" action="/api/payment/create" class="add-form">'
    content += '<input type="number" name="amount" placeholder="Monto UYU" min="1" step="0.01" required>'
    content += '<input type="text" name="description" placeholder="Descripcion">'
    content += '<button type="submit">Generar link</button>'
    content += '</form></div>'
    
    return render_page('Pagos', content, 'pagos')
