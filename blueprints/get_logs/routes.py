from flask import Blueprint, jsonify, request
from db import query_logs

get_logs_bp = Blueprint('get_logs', __name__, url_prefix='/get_logs')

@get_logs_bp.route('/', methods=['GET'])
def get_logs():
    level = request.args.get('level')
    query = "SELECT * FROM logs WHERE level = ?" if level else "SELECT * FROM logs"
    params = (level,) if level else None

    rows = query_logs(query, params)
    logs = [{"id": r[0], "timestamp": r[1], "level": r[2], "message": r[3], "source": r[4]} for r in rows]
    return jsonify(logs)

