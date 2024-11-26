from flask import Blueprint, jsonify, request, render_template
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# SQLAlchemy 설정
DATABASE_URI = "sqlite:///logs.db"  # 데이터베이스 경로
engine = create_engine(DATABASE_URI, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

# Logs 테이블 정의
class Log(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    level = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    method = Column(String, nullable=True)
    source = Column(String, nullable=True)

recent_logs_bp = Blueprint('recent_logs', __name__, url_prefix='/recent_logs')

# GET 요청: 페이지 렌더링
@recent_logs_bp.route('/', methods=['GET'])
def render_logs_page():
    return render_template('recent_logs.html')

# POST 요청: 로그 검색 API
@recent_logs_bp.route('/search', methods=['POST'])
def search_logs():
    filters = request.json
    page = int(filters.get('page', 1))
    per_page = int(filters.get('per_page', 20))

    # 동적 필터 조건
    query = session.query(Log)

    # id 필터
    if 'id' in filters and filters['id']:
        query = query.filter(Log.id == int(filters['id']))
    
    # timestamp 범위 필터
    if 'start_date' in filters and filters['start_date']:
        start_datetime = datetime.strptime(filters['start_date'], "%Y-%m-%d")
        query = query.filter(Log.timestamp >= start_datetime)
    if 'end_date' in filters and filters['end_date']:
        end_datetime = datetime.strptime(filters['end_date'], "%Y-%m-%d")
        query = query.filter(Log.timestamp <= end_datetime)

    # level 필터
    if 'level' in filters and filters['level']:
        query = query.filter(Log.level == filters['level'])

    # message 필터 (부분 일치)
    if 'message' in filters and filters['message']:
        query = query.filter(Log.message.ilike(f"%{filters['message']}%"))

    # method 필터
    if 'method' in filters and filters['method']:
        query = query.filter(Log.method == filters['method'])

    # source 필터
    if 'source' in filters and filters['source']:
        query = query.filter(Log.source == filters['source'])

    # 페이지네이션 적용
    total_logs = query.count()
    logs = query.order_by(Log.timestamp.desc()) \
                .offset((page - 1) * per_page) \
                .limit(per_page) \
                .all()

    # 결과 데이터 변환
    log_data = [{
        "id": log.id,
        "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
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

