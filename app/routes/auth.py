"""
LinkPay - Autenticacion (registro, login, logout)
"""

from flask import Blueprint, render_template_string, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from zoo_analytics import track_event

auth_bp = Blueprint('auth', __name__)

BASE_STYLE = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#eee;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center}
.c{width:100%;max-width:380px;padding:40px 30px}
h1{font-size:28px;font-weight:700;text-align:center;margin-bottom:8px}
h1+p{text-align:center;opacity:.6;margin-bottom:24px;font-size:14px}
form{display:flex;flex-direction:column;gap:12px}
input,button{padding:12px 16px;border-radius:8px;border:1px solid #333;background:#111;color:#eee;font-size:14px;font-family:inherit}
input:focus{border-color:#0f8;outline:none}
button{background:#0f8;color:#000;font-weight:600;cursor:pointer;border:none}
button:hover{background:#0c6}
.small{text-align:center;margin-top:16px;font-size:12px;opacity:.5}
.small a{color:#0f8}
.alert{background:#f443;padding:10px;border-radius:8px;margin-bottom:12px;font-size:13px;color:#f44}
"""

REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Crear cuenta | LinkPay</title>
<style>""" + BASE_STYLE + """</style>
</head>
<body>
<div class="c">
    <h1>Link<span style="color:#0f8">Pay</span></h1>
    <p>Crea tu pagina de links con pagos</p>
    {% with msgs = get_flashed_messages() %}
    {% for msg in msgs %}<div class="alert">{{ msg }}</div>{% endfor %}
    {% endwith %}
    <form method="POST">
        <input type="email" name="email" placeholder="Email" required>
        <input type="text" name="username" placeholder="Tu link: linkpay.uy/tu-nombre" required pattern="[a-z0-9_-]+" minlength="3" maxlength="30">
        <input type="text" name="display_name" placeholder="Nombre visible">
        <input type="password" name="password" placeholder="Contrasena" required minlength="6">
        <button type="submit">Crear cuenta</button>
    </form>
    <p class="small">Ya tienes cuenta? <a href="/auth/login">Entra</a></p>
</div>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Entrar | LinkPay</title>
<style>""" + BASE_STYLE + """</style>
</head>
<body>
<div class="c">
    <h1>Link<span style="color:#0f8">Pay</span></h1>
    {% with msgs = get_flashed_messages() %}
    {% for msg in msgs %}<div class="alert">{{ msg }}</div>{% endfor %}
    {% endwith %}
    <form method="POST">
        <input type="text" name="username" placeholder="Username o email" required>
        <input type="password" name="password" placeholder="Contrasena" required>
        <button type="submit">Entrar</button>
    </form>
    <p class="small">No tienes cuenta? <a href="/auth/register">Registrate</a></p>
</div>
</body>
</html>
"""

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip().lower()
        display_name = request.form.get('display_name', '').strip()
        password = request.form.get('password', '')
        
        if User.query.filter_by(email=email).first():
            flash('Email ya registrado')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(username=username).first():
            flash('Username no disponible')
            return redirect(url_for('auth.register'))
        if len(username) < 3 or not username.replace('-', '').replace('_', '').isalnum():
            flash('Username invalido')
            return redirect(url_for('auth.register'))
        
        user = User(email=email, username=username, display_name=display_name or username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        track_event('user.registered', user_id=user.id, metadata={
            'source': request.args.get('ref', 'direct'),
            'username': username
        })
        
        login_user(user)
        return redirect(url_for('dashboard.index'))
    
    return render_template_string(REGISTER_TEMPLATE)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        
        user = User.query.filter(
            db.or_(User.username == username, User.email == username)
        ).first()
        
        if user and user.check_password(password):
            login_user(user)
            track_event('user.login', user_id=user.id, metadata={'method': 'password'})
            return redirect(url_for('dashboard.index'))
        
        flash('Credenciales invalidas')
        return redirect(url_for('auth.login'))
    
    return render_template_string(LOGIN_TEMPLATE)

@auth_bp.route('/logout')
@login_required
def logout():
    track_event('user.logout', user_id=current_user.id)
    logout_user()
    return redirect(url_for('auth.login'))
