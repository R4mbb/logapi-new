from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__, url_prefix='/')

@main_bp.route('/')
def main_page():
    """
    Render the main page with enhanced navigation.
    """
    return render_template(
        'main_page.html',
        navigation=[
            {"name": "Upload Logs", "url": "/upload_logs"},
            {"name": "Recent Logs", "url": "/recent_logs"},
            {"name": "Dashboard", "url": "/dashboard"}
        ]
    )

