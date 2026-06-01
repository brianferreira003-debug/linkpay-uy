"""
LinkPay - Dashboard del usuario (gestion de links, ver estadisticas)
"""

from flask import Blueprint, render_template_string, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Link, Payment, PageView, ClickEvent
from app import db
from zoo_analytics import track_event
from datetime import datetime, timedelta, date
from sqlalchemy import func

dash_bp = Blueprint('dashboard', __name__)

DASH_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Dashboard | LinkPay</title>
<link rel="stylesheet" href="/static/css/dash.css">
</head>
<body>
<div class="sb">
    <div class="logo">LP</div>
    <a href="/dashboard" class="ac">Links</a>
    <a href="/dashboard/pagos">Pagos</a>
    <a href="/dashboard/stats">Estadisticas</a>
    <a href="/dashboard/settings">Config</a>
    <div class="bottom">
        <a href="{{ current_user.page_url }}" target="_blank">Ver pagina</a>
        <a href="/auth/logout">Salir</a>
    </div>
</div>
<div class="main">
    {% with msgs = get_flashed_messages() %}
    {% for msg in msgs %}<div class="alert">{{ msg }}</div>{% endfor %}
    {% endwith %}
    {{ content }}
</div>
</body>
</html>
"""

LINKS_CONTENT = """
<h1>Mis Links</h1>
<div class="card">
    <h3>Nuevo link</h3>
    <form method="POST" action="/dashboard/link/add" class="add-form">
        <input type="text" name="title" placeholder="Titulo" required>
        <input type="url" name="url" placeholder="https://..." required>
        <input type="text" name="icon" placeholder="Icono (emoji)" maxlength="2">
        <button type="submit">Agregar</button>
    </form>
</div>
<div class="card">
    <h3>Tus links ({{ links | length }})</h3>
    {% if links %}
    <table class="table">
        <thead><tr><th>#</th><th>Titulo</th><th>URL</th><th>Clicks</th><th></th></tr></thead>
        <tbody>
        {% for link in links %}
        <tr>
            <td>{{ loop.index }}</td>
            <td>{{ link.icon or '' }} {{ link.title }}</td>
            <td><a href="{{ link.url }}" target="_blank" class="url">{{ link.url[:40] }}...</a></td>
            <td>{{ link.click_count }}</td>
            <td>
                <form method="POST" action="/dashboard/link/{{ link.id }}/delete" style="display:inline">
                    <button class="btn-sm btn-danger" onclick="return confirm('Borrar?')">X</button>
                </form>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p class="empty">No tenes links aun. Agrega el primero arriba.</p>
    {% endif %}
</div>
"""

STATS_CONTENT = """
<h1>Estadisticas</h1>
<div class="stats-grid">
    <div class="stat-card"><h3>Hoy</h3><div class="big">{{ views_today }}</div><div class="sub">Visitas</div></div>
    <div class="stat-card"><h3>7 dias</h3><div class="big">{{ views_7d }}</div><div class="sub">Visitas</div></div>
    <div class="stat-card"><h3>Total</h3><div class="big">{{ views_total }}</div><div class="sub">Visitas</div></div>
    <div class="stat-card"><h3>Links</h3><div class="big">{{ link_count }}</div><div class="sub">Activos</div></div>
</div>
<div class="card">
    <h3>Visitas por dia (7d)</h3>
    <canvas id="vc" height="150"></canvas>
</div>
<div class="card">
    <h3>Top links por clicks</h3>
    {% if top_links %}
    <table>
        {% for link in top_links %}
        <tr><td>{{ link.title }}</td><td>{{ link.click_count }} clicks</td></tr>
        {% endfor %}
    </table>
    {% else %}<p class="empty">Sin datos aun</p>{% endif %}
</div>
<script>
var c=document.getElementById('vc'),ctx=c.getContext('2d'),w=c.parentElement.clientWidth-30,h=130;
c.width=w;c.height=h;
var labels={{ vlabels | safe }},values={{ vvalues | safe }};
if(!values.length||Math.max.apply(null,values)===0){ctx.fillStyle='#333';ctx.fillText('Sin datos aun',10,h/2)}
else{var max=Math.max.apply(null,values);values.forEach(function(v,i){var bh=v/max*(h-20);ctx.fillStyle='#0f8';ctx.fillRect(i*((w-10)/values.length)+2,h-bh-15,(w-10)/values.length-4,bh);ctx.fillStyle='#555';ctx.font='9px monospace';ctx.fillText(labels[i],i*((w-10)/values.length)+2,h-3)})}
</script>
"""

SETTINGS_CONTENT = """
<h1>Configuracion</h1>
<div class="card">
    <h3>Perfil</h3>
    <form method="POST" action="/dashboard/settings/update">
        <label>Nombre visible</label>
        <input type="text" name="display_name" value="{{ current_user.display_name or '' }}">
        <label>Bio</label>
        <textarea name="bio" rows="3" maxlength="300">{{ current_user.bio or '' }}</textarea>
        <label>Tema</label>
        <select name="theme">
            <option value="dark" {{ 'selected' if current_user.theme=='dark' }}>Oscuro</option>
            <option value="light" {{ 'selected' if current_user.theme=='light' }}>Claro</option>
        </select>
        <button type="submit">Guardar</button>
    </form>
</div>
<div class="card">
    <h3>Tu pagina</h3>
    <p>linkpay.uy/{{ current_user.username }}</p>
    <a href="{{ current_user.page_url }}" target="_blank" class="btn">Ver pagina publica</a>
</div>
"""

DASH_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#eee;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;display:flex;min-height:100vh}
.sb{width:200px;background:#111;border-right:1px solid #222;padding:20px 0;display:flex;flex-direction:column;flex-shrink:0}
.sb .logo{font-size:24px;font-weight:700;color:#0f8;text-align:center;padding:10px 0 20px;border-bottom:1px solid #222;margin-bottom:10px}
.sb a{padding:10px 20px;color:#eee;text-decoration:none;font-size:13px;opacity:.6;display:block}
.sb a:hover,.sb a.ac{opacity:1;background:#1a1a1a;color:#0f8}
.sb .bottom{margin-top:auto;border-top:1px solid #222;padding-top:10px}
.main{flex:1;padding:30px;overflow-y:auto}
h1{font-size:20px;margin-bottom:20px}
.card{background:#111;border:1px solid #222;border-radius:12px;padding:20px;margin-bottom:16px}
.card h3{font-size:13px;opacity:.6;margin-bottom:12px;text-transform:uppercase;letter-spacing:1px}
.add-form{display:flex;gap:8px;flex-wrap:wrap}
.add-form input{flex:1;min-width:120px;padding:10px;border-radius:8px;border:1px solid #333;background:#0a0a0a;color:#eee;font-size:13px}
.add-form button{padding:10px 20px;background:#0f8;color:#000;border:none;border-radius:8px;font-weight:600;cursor:pointer}
.table{width:100%;border-collapse:collapse}
.table th,.table td{padding:8px 12px;text-align:left;border-bottom:1px solid #1a1a1a;font-size:12px}
.table th{opacity:.5;font-weight:normal;font-size:10px;text-transform:uppercase}
.url{color:#0f8;text-decoration:none}
.btn-sm{padding:4px 8px;border-radius:4px;border:none;cursor:pointer;font-size:11px}
.btn-danger{background:#f443;color:#f44}
.empty{opacity:.4;font-size:13px}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.stat-card{background:#111;border:1px solid #222;border-radius:12px;padding:16px;text-align:center}
.stat-card h3{font-size:10px;opacity:.5;margin-bottom:8px}
.stat-card .big{font-size:28px;font-weight:700;color:#0f8}
.stat-card .sub{font-size:11px;opacity:.5;margin-top:4px}
label{display:block;font-size:11px;opacity:.5;margin-bottom:4px;margin-top:12px}
textarea{width:100%;padding:10px;border-radius:8px;border:1px solid #333;background:#0a0a0a;color:#eee;font-size:13px;font-family:inherit;resize:vertical}
select{padding:10px;border-radius:8px;border:1px solid #333;background:#0a0a0a;color:#eee;font-size:13px}
.btn{display:inline-block;padding:8px 16px;background:#0f8;color:#000;border-radius:8px;text-decoration:none;font-size:13px;font-weight:600}
.alert{background:#f443;padding:10px;border-radius:8px;margin-bottom:12px;font-size:13px;color:#f44}
@media(max-width:768px){.sb{width:60px}.sb a span,.sb .logo span{display:none}}
"""

@dash_bp.route('/')
@login_required
def index():
    links = current_user.links.order_by(Link.position).all()
    track_event('page.view', user_id=current_user.id, metadata={'path': '/dashboard'})
    content = render_template_string(LINKS_CONTENT, links=links)
    return render_template_string(DASH_TEMPLATE, content=content)

@dash_bp.route('/link/add', methods=['POST'])
@login_required
def add_link():
    title = request.form.get('title', '').strip()
    url = request.form.get('url', '').strip()
    icon = request.form.get('icon', '').strip()
    
    if not title or not url:
        flash('Titulo y URL son obligatorios')
        return redirect(url_for('dashboard.index'))
    
    link = Link(
        user_id=current_user.id,
        title=title,
        url=url,
        icon=icon or None,
        position=current_user.links.count()
    )
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
    
    views_today = PageView.query.filter(
        PageView.username == username,
        func.date(PageView.created_at) == today
    ).count()
    
    views_7d = PageView.query.filter(
        PageView.username == username,
        func.date(PageView.created_at) >= week_ago
    ).count()
    
    views_total = PageView.query.filter_by(username=username).count()
    link_count = current_user.links.filter_by(is_active=True).count()
    
    # Visitas por dia
    vpd = db.session.query(
        func.date(PageView.created_at),
        func.count(PageView.id)
    ).filter(
        PageView.username == username,
        func.date(PageView.created_at) >= week_ago
    ).group_by(func.date(PageView.created_at)).order_by(func.date(PageView.created_at)).all()
    
    # Top links
    top_links = current_user.links.order_by(Link.click_count.desc()).limit(5).all()
    
    vlabels = json.dumps([str(d[0])[-5:] for d in vpd])
    vvalues = json.dumps([d[1] for d in vpd])
    
    content = render_template_string(
        STATS_CONTENT,
        views_today=views_today,
        views_7d=views_7d,
        views_total=views_total,
        link_count=link_count,
        top_links=top_links,
        vlabels=vlabels,
        vvalues=vvalues,
    )
    return render_template_string(DASH_TEMPLATE, content=content)

@dash_bp.route('/settings')
@login_required
def settings():
    content = render_template_string(SETTINGS_CONTENT)
    return render_template_string(DASH_TEMPLATE, content=content)

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

# CSS estatico
@dash_bp.route('/static/css/dash.css')
def dash_css():
    from flask import Response
    return Response(DASH_CSS, mimetype='text/css')

import json
