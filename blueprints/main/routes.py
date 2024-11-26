from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__, url_prefix='/')

@main_bp.route('/')
def main_page():
    """Render the main page with navigation."""
    return render_template('main_page.html')

