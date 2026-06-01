"""
ZOO Analytics - Dashboard routes
"""

import json
from datetime import datetime, timedelta, date
from flask import Blueprint, render_template_string, jsonify, request

admin_bp = Blueprint('admin', __name__)

CSS = """<style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#0a0a0a;color:#0f8;font-family:monospace;font-size:13px}
.hd{background:#111;padding:12px 20px;border-bottom:2px solid #0f8}.hd h1{font-size:14px;color:#0f8}
.c{padding:15px;max-width:1100px;margin:0 auto}.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:15px}
.card{background:#111;border:1px solid #222;padding:12px;position:relative}.card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:#0f8}
.card h3{font-size:10px;opacity:.6;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}
.big{font-size:24px;font-weight:bold}.sub{font-size:11px;opacity:.6;margin-top:4px}
.chart{background:#111;border:1px solid #222;padding:12px;margin-bottom:12px;position:relative}.chart::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:#f80}
.chart h3{font-size:10px;opacity:.6;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}canvas{width:100%}
table{width:100%;border-collapse:collapse}th,td{padding:6px 10px;text-align:left;border-bottom:1px solid #1a1a1a;font-size:11px}
th{opacity:.5;font-size:9px;text-transform:uppercase}tr:hover td{background:#0d0d0d}
</style>"""

JS_TEMPLATE = """
var c=document.getElementById('ec'),x=c.getContext('2d'),w=c.parentElement.clientWidth-24,h=120;
c.width=w;c.height=h;x.clearRect(0,0,w,h);
var labels=__EL__,values=__EV__;
if(!values.length){x.fillStyle='#333';x.fillText('Sin datos aun',10,h/2);return}
var mx=Math.max.apply(null,values);
values.forEach(function(v,i){var bh=v/mx*(h-20);x.fillStyle='#0f8';x.fillRect(i*(w/values.length)+1,h-bh-15,w/values.length-3,bh);x.fillStyle='#555';x.font='8px monospace';x.fillText(labels[i]||' ',i*(w/values.length)+1,h-3)});
"""

@admin_bp.route('/api/health')
def api_health():
    from zoo_analytics import _current_db
    try:
        _current_db.session.execute(_current_db.text('SELECT 1'))
        return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': str(e)}), 500

@admin_bp.route('/dashboard')
def dashboard():
    from zoo_analytics import _current_db, _project_slug
    today = date.today()
    week = today - timedelta(days=7)

    te = _current_db.session.execute(_current_db.text(
        "SELECT COUNT(*) FROM za_events WHERE DATE(created_at)=:d AND project_id=(SELECT id FROM za_projects WHERE slug=:s)"
    ), {'d':today,'s':_project_slug}).scalar() or 0

    tu = _current_db.session.execute(_current_db.text(
        "SELECT COUNT(DISTINCT user_id) FROM za_events WHERE project_id=(SELECT id FROM za_projects WHERE slug=:s) AND user_id IS NOT NULL"
    ), {'s':_project_slug}).scalar() or 0

    er = _current_db.session.execute(_current_db.text(
        "SELECT COUNT(*) FROM za_events WHERE DATE(created_at)=:d AND event_type LIKE '%error%' AND project_id=(SELECT id FROM za_projects WHERE slug=:s)"
    ), {'d':today,'s':_project_slug}).scalar() or 0

    epd = _current_db.session.execute(_current_db.text(
        "SELECT DATE(created_at),COUNT(*) FROM za_events WHERE created_at>=:w AND project_id=(SELECT id FROM za_projects WHERE slug=:s) GROUP BY 1 ORDER BY 1"
    ), {'w':week,'s':_project_slug}).fetchall()

    recent = _current_db.session.execute(_current_db.text(
        "SELECT event_type,user_id,metadata,created_at FROM za_events WHERE project_id=(SELECT id FROM za_projects WHERE slug=:s) ORDER BY created_at DESC LIMIT 20"
    ), {'s':_project_slug}).fetchall()

    rows = ''
    for r in recent:
        rows += '<tr><td>' + str(r[0]) + '</td><td>' + str(r[1] or '-') + '</td><td>' + (r[2] or '')[:60] + '</td><td>' + (r[3].strftime('%H:%M') if r[3] else '-') + '</td></tr>'

    el = json.dumps([str(r[0])[-5:] for r in epd])
    ev = json.dumps([r[1] for r in epd])

    js = JS_TEMPLATE.replace('__EL__', el).replace('__EV__', ev)

    html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>ZOO Analytics</title>'
    html += CSS
    html += '</head><body>'
    html += '<div class="hd"><h1>ZOO ANALYTICS</h1></div>'
    html += '<div class="c"><div class="g">'
    html += '<div class="card"><h3>Eventos hoy</h3><div class="big">' + str(te) + '</div></div>'
    html += '<div class="card"><h3>Usuarios</h3><div class="big">' + str(tu) + '</div></div>'
    html += '<div class="card"><h3>MRR</h3><div class="big">-</div></div>'
    html += '<div class="card"><h3>Errores</h3><div class="big" style="color:#f44">' + str(er) + '</div></div>'
    html += '</div>'
    html += '<div class="chart"><h3>Eventos por dia (7d)</h3><canvas id="ec" height="140"></canvas></div>'
    html += '<div class="chart"><h3>Ultimos eventos</h3><table><thead><tr><th>Tipo</th><th>Usuario</th><th>Metadata</th><th>Hora</th></tr></thead><tbody>'
    html += rows
    html += '</tbody></table></div>'
    html += '</div>'
    html += '<script>' + js + '</script>'
    html += '</body></html>'

    return html
