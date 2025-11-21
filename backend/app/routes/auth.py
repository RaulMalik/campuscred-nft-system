from flask import Blueprint, jsonify, render_template, request, session
from functools import wraps

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Instructor wallet address
INSTRUCTOR_WALLET = '0xa8cA165C69d2d9f4842428e0ea51EF9881eC59A4'.lower()


def login_required(f):
    # require login for instructor routes

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'wallet_address' not in session:
            return jsonify({'error': 'Authentication required', 'redirect': '/'}), 401
        return f(*args, **kwargs)

    return decorated_function


def instructor_required(f):
    # require instructor wallet

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'wallet_address' not in session:
            return jsonify({'error': 'Authentication required', 'redirect': '/'}), 401

        wallet = session.get('wallet_address', '').lower()
        if wallet != INSTRUCTOR_WALLET:
            return jsonify({'error': 'Instructor access required'}), 403

        return f(*args, **kwargs)

    return decorated_function


@bp.route('/')
def hello():
    return jsonify({
        'message': 'Hello from CampusCred!',
        'status': 'running',
        'version': '0.2.0'
    })


@bp.route('/test')
def test():
    return jsonify({
        'message': 'Auth blueprint is working!',
        'endpoint': '/auth/test'
    })


@bp.route('/test-html')
def test_html():
    """Test route to check templates and static files"""
    return render_template('test.html')


@bp.route('/connect-wallet', methods=['POST'])
def connect_wallet():
    """
    Handle wallet connection from frontend
    Determines if user is instructor or student based on wallet address
    """
    data = request.get_json()
    wallet_address = data.get('address', '').lower()

    if not wallet_address:
        return jsonify({'success': False, 'error': 'No wallet address provided'}), 400

    # store wallet in session
    session['wallet_address'] = wallet_address

    # check if instructor wallet
    is_instructor = (wallet_address == INSTRUCTOR_WALLET)
    session['is_instructor'] = is_instructor

    response_data = {
        'success': True,
        'address': wallet_address,
        'is_instructor': is_instructor,
        'redirect': '/instructor/dashboard' if is_instructor else '/student/portal'
    }

    return jsonify(response_data)


@bp.route('/disconnect', methods=['POST'])
def disconnect_wallet():
    # disconnect wallet and clear session
    session.clear()
    return jsonify({'success': True, 'message': 'Disconnected successfully'})


@bp.route('/check-session')
def check_session():
    # current session status
    return jsonify({
        'connected': 'wallet_address' in session,
        'address': session.get('wallet_address'),
        'is_instructor': session.get('is_instructor', False)
    })