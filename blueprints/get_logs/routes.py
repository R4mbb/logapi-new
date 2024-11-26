from flask import Blueprint, jsonify, request
from db import query_logs

get_logs_bp = Blueprint('get_logs', __name__, url_prefix='/get_logs')

# 허용된 로그 레벨
VALID_LEVELS = {'INFO', 'WARNING', 'ERROR', 'DEBUG'}

@get_logs_bp.route('/', methods=['GET'])
def get_logs():
    # 필터 조건
    level = request.args.get('level')
    limit = request.args.get('limit', 100, type=int)  # 기본 제한 100
    fields = request.args.get('fields', 'id,timestamp,level,message,method,source')  # 기본 필드에 method 추가

    # 필터 유효성 검사
    if level and level not in VALID_LEVELS:
        return jsonify({"error": f"Invalid log level. Valid levels are: {', '.join(VALID_LEVELS)}"}), 400

    # 반환할 필드 처리
    allowed_fields = {'id', 'timestamp', 'level', 'message', 'method', 'source'}  # method 포함
    requested_fields = set(fields.split(','))
    if not requested_fields.issubset(allowed_fields):
        return jsonify({"error": f"Invalid fields requested. Allowed fields are: {', '.join(allowed_fields)}"}), 400

    # SQL 쿼리 생성
    selected_fields = ', '.join(requested_fields)
    query = f"SELECT {selected_fields} FROM logs"
    params = []

    if level:
        query += " WHERE level = ?"
        params.append(level)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    # 데이터베이스 조회
    rows = query_logs(query, params)
    logs = [dict(zip(requested_fields, row)) for row in rows]

    # 결과 반환
    if not logs:
        return jsonify({"error": "No logs found"}), 404

    return jsonify(logs)

