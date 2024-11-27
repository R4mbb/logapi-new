from flask import Blueprint, jsonify, request, render_template
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, MetaData, Table
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# SQLAlchemy 설정
DATABASE_URI = "sqlite:///logs.db"
engine = create_engine(DATABASE_URI, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

# 동적으로 테이블 모델 생성
metadata = MetaData()
metadata.reflect(bind=engine)

def get_log_model(table_name):
    """동적으로 테이블을 SQLAlchemy 모델로 변환"""
    table = Table(table_name, metadata, autoload_with=engine)
    return type(table_name.capitalize(), (Base,), {"__table__": table})

# Blueprint 정의
recent_logs_bp = Blueprint('recent_logs', __name__, url_prefix='/recent_logs')

@recent_logs_bp.route('/', methods=['GET'])
def render_logs_page():
    return render_template('recent_logs.html')

@recent_logs_bp.route('/search', methods=['POST'])
def search_logs():
    filters = request.json
    log_type = filters.get('log_type', 'apache2')  # 기본값은 apache2
    page = int(filters.get('page', 1))
    per_page = int(filters.get('per_page', 20))

    # 선택된 로그 테이블에 따른 모델 가져오기
    try:
        LogModel = get_log_model(f"{log_type}_logs")
    except Exception as e:
        return jsonify({"error": f"Invalid log type: {log_type}. Error: {str(e)}"}), 400

    # 동적 필터 조건
    query = session.query(LogModel)

    # id 필터
    if 'id' in filters and filters['id']:
        query = query.filter(LogModel.id == int(filters['id']))
    
    # timestamp 범위 필터
    if 'start_date' in filters and filters['start_date']:
        start_datetime = datetime.strptime(filters['start_date'], "%Y-%m-%d")
        query = query.filter(LogModel.timestamp >= start_datetime)
    if 'end_date' in filters and filters['end_date']:
        end_datetime = datetime.strptime(filters['end_date'], "%Y-%m-%d")
        query = query.filter(LogModel.timestamp <= end_datetime)

    # level 필터
    if 'level' in filters and filters['level']:
        query = query.filter(LogModel.level == filters['level'])

    # message 필터 (부분 일치)
    if 'message' in filters and filters['message']:
        query = query.filter(LogModel.message.ilike(f"%{filters['message']}%"))

    # method 필터
    if 'method' in filters and filters['method']:
        query = query.filter(LogModel.method == filters['method'])

    # source 필터
    if 'source' in filters and filters['source']:
        query = query.filter(LogModel.source == filters['source'])

    # 페이지네이션 적용
    total_logs = query.count()
    logs = query.order_by(LogModel.timestamp.desc()) \
                .offset((page - 1) * per_page) \
                .limit(per_page) \
                .all()

    # 결과 데이터 변환
    log_data = [{
        "id": log.id,
        "timestamp": (
            datetime.strptime(log.timestamp, "%d/%b/%Y:%H:%M:%S")
            if isinstance(log.timestamp, str) and '/' in log.timestamp else log.timestamp
        ).strftime("%Y-%m-%d %H:%M:%S"),
        "level": log.level,
        "message": log.message,
        "method": log.method,
        "source": log.source
    } for log in logs]

    return jsonify({
        "logs": log_data,
        "total": total_logs,
        "page": page,
        "per_page": per_page
    })

