"""
LinkPay - API (pagos MercadoPago, clicks, etc.)
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Link, Payment, ClickEvent
from app import db
from zoo_analytics import track_event
import hashlib
import time

api_bp = Blueprint('api', __name__)

@api_bp.route('/click/<int:link_id>', methods=['POST'])
def track_click(link_id):
    link = Link.query.get_or_404(link_id)
    link.click_count += 1
    ip = request.remote_addr
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16] if ip else None
    click = ClickEvent(link_id=link_id, username=link.owner.username, ip_hash=ip_hash, referer=request.referrer)
    db.session.add(click)
    db.session.commit()
    track_event('action.shared', user_id=link.user_id, metadata={'type': 'link_click', 'link_id': link_id, 'link_title': link.title})
    return jsonify({'ok': True})

@api_bp.route('/payment/create', methods=['POST'])
@login_required
def create_payment():
    """Crea un link de pago. Soporta MP (si hay token) o modo manual."""
    data = request.get_json() or request.form
    amount = data.get('amount')
    description = data.get('description', 'Pago via LinkPay')
    
    if not amount or float(amount) <= 0:
        return jsonify({'error': 'Monto invalido'}), 400
    
    amount = float(amount)
    mp_token = current_app.config.get('MP_ACCESS_TOKEN', '')
    mp_public_key = current_app.config.get('MP_PUBLIC_KEY', '')
    
    payment = Payment(
        user_id=current_user.id,
        amount=amount,
        currency='UYU',
        description=description[:200],
        status='pending'
    )
    
    mp_link = None
    
    # Intentar crear preferencia en MercadoPago
    if mp_token:
        try:
            import urllib.request, json as _json
            payload = _json.dumps({
                'items': [{
                    'title': description[:200],
                    'quantity': 1,
                    'currency_id': 'UYU',
                    'unit_price': amount,
                }],
                'back_urls': {
                    'success': f'https://linkpay.uy/{current_user.username}',
                    'failure': f'https://linkpay.uy/{current_user.username}',
                },
                'auto_return': 'approved',
                'external_reference': f'lp_{current_user.id}_{int(time.time())}',
            }).encode()
            
            req = urllib.request.Request(
                'https://api.mercadopago.com/checkout/preferences',
                data=payload,
                headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {mp_token}'},
                method='POST'
            )
            resp = urllib.request.urlopen(req, timeout=10)
            result = _json.loads(resp.read())
            payment.mp_preference_id = result.get('id')
            mp_link = result.get('init_point')
        except Exception as e:
            current_app.logger.warning(f'MP error: {e}')
    
    # Si no hay MP, generar link de pago manual
    if not mp_link:
        payment_id = f"manual_{current_user.id}_{int(time.time())}"
        mp_link = f"https://linkpay.uy/{current_user.username}?pago={payment_id}&monto={amount}"
    
    db.session.add(payment)
    db.session.commit()
    
    track_event('payment.started', user_id=current_user.id, metadata={
        'amount': str(amount), 'payment_id': payment.id, 'mp': bool(mp_token)
    })
    
    return jsonify({
        'ok': True,
        'payment_id': payment.id,
        'payment_url': mp_link,
        'amount': amount,
        'currency': 'UYU',
    })

@api_bp.route('/payment/webhook', methods=['POST'])
def mp_webhook():
    """Webhook de MercadoPago para confirmar pagos."""
    data = request.get_json() or {}
    payment_id = data.get('data', {}).get('id') or request.args.get('id')
    
    if not payment_id:
        return jsonify({'error': 'No payment ID'}), 400
    
    payment = Payment.query.filter_by(mp_payment_id=str(payment_id)).first()
    if not payment:
        ext_ref = data.get('external_reference', '')
        if ext_ref.startswith('lp_'):
            parts = ext_ref.split('_')
            if len(parts) >= 2:
                payment = Payment.query.filter_by(user_id=int(parts[1]), status='pending').order_by(Payment.created_at.desc()).first()
    
    if payment:
        payment.status = 'completed'
        payment.completed_at = __import__('datetime').datetime.utcnow()
        db.session.commit()
        track_event('payment.completed', user_id=payment.user_id, metadata={'amount': str(payment.amount), 'payment_id': payment.id})
    
    return jsonify({'ok': True})
