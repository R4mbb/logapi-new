from flask import Blueprint, request, render_template
from werkzeug.utils import secure_filename
import re
import json
from db import insert_log
from datetime import datetime

upload_logs_bp = Blueprint('upload_logs', __name__, url_prefix='/upload_logs')

# 로그 정규식 패턴
APACHE_LOG_PATTERN = (
    r'(?P<ip_address>\S+) '
    r'(?P<identity>\S+) '
    r'(?P<userid>\S+) '
    r'\[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) '
    r'(?P<url>[^\s]+) '
    r'(?P<protocol>[^\s]+)" '
    r'(?P<status>\d{3}) '
    r'(?P<size>\S+)'
)

NGINX_LOG_PATTERN = (
    r'(?P<ip_address>\S+) - - \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<url>[^\s]+) HTTP/\d.\d" '
    r'(?P<status>\d{3}) (?P<size>\d+)'
)

# 로그 레벨 결정 함수
def determine_level(method, status):
    method = method.upper() if method else "UNKNOWN"
    if method in {"GET", "HEAD"}:
        return "TRACE"
    elif method in {"POST", "PUT", "DELETE", "PATCH"}:
        return "DEBUG"
    elif method == "OPTIONS":
        return "INFO"

    try:
        status_code = int(status)
        if 200 <= status_code < 300:
            return "INFO"
        elif 300 <= status_code < 400:
            return "WARN"
        elif 400 <= status_code < 500:
            return "ERROR"
        elif 500 <= status_code:
            return "FATAL"
    except ValueError:
        pass

    return "INFO"

# Apache/Nginx 타임스탬프 파싱
def parse_timestamp(raw_timestamp):
    try:
        if "+" in raw_timestamp:
            dt = raw_timestamp.split()
            return dt[0]
    except ValueError:
        return None

# JSON 로그 처리
def process_json_logs(file_stream, log_type):
    logs = json.load(file_stream)
    for log in logs:
        raw_timestamp = log.get("timestamp")
        parsed_timestamp = parse_timestamp(raw_timestamp)
        if not parsed_timestamp:
            continue

        method = log.get("method", "")
        status = log.get("status", "200")
        level = determine_level(method, status)
        message = log.get("message", "")
        source_ip = log.get("source_ip", "")
        insert_log(parsed_timestamp, level, message, method, source_ip, log_type)

# 텍스트 로그 처리
def process_text_logs(file_stream, log_type):
    for line in file_stream:
        line = line.decode('utf-8').strip()
        for pattern in [APACHE_LOG_PATTERN, NGINX_LOG_PATTERN]:
            match = re.match(pattern, line)
            if match:
                data = match.groupdict()
                raw_timestamp = data['timestamp']
                parsed_timestamp = parse_timestamp(raw_timestamp)
                if not parsed_timestamp:
                    continue
                method = data.get('method', "")
                level = determine_level(method, data.get('status', "200"))
                ip_address = data['ip_address']
                url = data.get('url', "")
                status = data.get('status', "")
                size = data.get('size', "0")
                message = f"{url} {status} {size}"
                insert_log(parsed_timestamp, level, message, method, ip_address, log_type)
                break

@upload_logs_bp.route('/', methods=['GET', 'POST'])
def upload_logs():
    if request.method == 'GET':
        return render_template('upload_logs.html')

    file = request.files.get('file')
    log_type = request.form.get('log_type')
    if not file or log_type not in {"apache2", "nginx"}:
        return render_template('upload_logs.html', message="File and log type are required")

    if not file.filename.endswith(('.log', '.txt', '.json')):
        return render_template('upload_logs.html', message="Supported formats: .log, .txt, .json")

    try:
        filename = secure_filename(file.filename)
        file_stream = file.stream

        if filename.endswith('.json'):
            process_json_logs(file_stream, log_type)
        elif filename.endswith(('.log', '.txt')):
            process_text_logs(file_stream, log_type)

        return render_template('upload_logs.html', message="Logs successfully uploaded and processed")
    except Exception as e:
        return render_template('upload_logs.html', message=f"Error processing file: {e}")

