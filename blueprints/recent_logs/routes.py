from flask import Blueprint, render_template, request, jsonify
import pandas as pd
from db import query_logs
from datetime import datetime

recent_logs_bp = Blueprint('recent_logs', __name__, url_prefix='/recent_logs')

@recent_logs_bp.route('/')
def recent_logs():
    """Render the recent logs page."""
    return render_template('recent_logs.html')
@recent_logs_bp.route('/search', methods=['POST'])
def search_logs():
    """Search logs with filters, including source and destination IP."""
    filters = request.json
    level = filters.get('level')
    start_date = filters.get('start_date')
    end_date = filters.get('end_date')
    keyword = filters.get('keyword')
    source_ip = filters.get('source_ip')
    destination_ip = filters.get('destination_ip')

    query = "SELECT id, timestamp, level, message, source, destination FROM logs"
    conditions = []
    params = []

    # Add filters
    if level:
        conditions.append("level = ?")
        params.append(level)
    if start_date:
        conditions.append("timestamp >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("timestamp <= ?")
        params.append(end_date)
    if keyword:
        conditions.append("message LIKE ?")
        params.append(f"%{keyword}%")
    if source_ip:
        conditions.append("source = ?")
        params.append(source_ip)
    if destination_ip:
        conditions.append("destination = ?")
        params.append(destination_ip)

    # Combine conditions into query
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY timestamp DESC LIMIT 100"

    # Execute query
    rows = query_logs(query, params)
    logs = [
        {"id": r[0], "timestamp": r[1], "level": r[2], "message": r[3], "source": r[4], "destination": r[5]}
        for r in rows
    ]

    if not logs:
        return jsonify({"error": "No logs found"}), 404

    return jsonify(logs)

