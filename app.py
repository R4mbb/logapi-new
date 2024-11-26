from flask import Flask
from blueprints.upload_logs import upload_logs_bp
from blueprints.get_logs import get_logs_bp
from blueprints.dashboard import dashboard_bp
from blueprints.collector import start_log_collector
from blueprints.main import main_bp
from blueprints.recent_logs import recent_logs_bp
from db.cleanup import manage_database
from db import init_db
from threading import Timer

import threading


app = Flask(__name__)

# Initialize database
init_db()

# Register blueprints
app.register_blueprint(upload_logs_bp)
app.register_blueprint(get_logs_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(main_bp)
app.register_blueprint(recent_logs_bp)

# Start log collector in a separate thread
collector_thread = threading.Thread(target=start_log_collector, daemon=True)
collector_thread.start()

def schedule_cleanup(interval=3600):
    manage_database()
    Timer(interval, schedule_cleanup, [interval]).start()

schedule_cleanup()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

