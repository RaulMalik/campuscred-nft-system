from flask import Blueprint, render_template

# was: Blueprint('verifi', __name__, url_prefix='/verify')
bp = Blueprint('verify', __name__, url_prefix='/verify')

@bp.route('/', endpoint='verify_home')
def verify_home():
    return render_template('verify.html', credential=None, error=None, show_private=False)