from flask import Blueprint, jsonify, render_template

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/')
def hello():
    return jsonify({
        'message': 'Hello from CampusCred!',
        'status': 'running',
        'version': '0.1.0'
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