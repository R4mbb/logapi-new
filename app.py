# app.py
from flask import Flask
from blueprints.upload_logs import upload_logs_bp
from blueprints.get_logs import get_logs_bp
from blueprints.dashboard.routes import dashboard_bp, init_dashboard_dash, init_dashboard_view_dash
from blueprints.main.routes import init_main_page
from blueprints.recent_logs import recent_logs_bp
from blueprints.collector import start_log_collector
from db.cleanup import manage_database
from db import init_db
from apscheduler.schedulers.background import BackgroundScheduler
import sys

sys.path.append('/app/lib/python3.10/site-packages')

# Flask 애플리케이션 초기화
app = Flask(__name__)

# 데이터베이스 초기화
init_db()

# 블루프린트 등록
app.register_blueprint(upload_logs_bp)
app.register_blueprint(get_logs_bp)
app.register_blueprint(dashboard_bp)
#app.register_blueprint(main_bp)
app.register_blueprint(recent_logs_bp)

# APScheduler 초기화
scheduler = BackgroundScheduler()

# 로그 수집기 작업 등록
scheduler.add_job(
    func=start_log_collector,
    trigger="interval",  # 일정 간격으로 실행
    seconds=10,          # 10초 간격으로 실행
    id="log_collector",
    max_instances=1,
    replace_existing=True
)

# 데이터베이스 정리 작업 등록
scheduler.add_job(
    func=manage_database,
    trigger="interval",    # 일정 간격으로 실행
    minutes=5,             # 5분 간격으로 실행
    id="database_cleanup",
    max_instances=1,
    replace_existing=True
)

# 스케줄러 시작
scheduler.start()

# 대시보드 활성화
init_dashboard_view_dash(app)
init_dashboard_dash(app)
init_main_page(app)

# 애플리케이션 실행
if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()  # 안전한 종료

