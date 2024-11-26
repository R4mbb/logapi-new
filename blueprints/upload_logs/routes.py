from flask import Blueprint, request, render_template
from werkzeug.utils import secure_filename
import re
import json
from db import insert_log
from datetime import datetime

upload_logs_bp = Blueprint('upload_logs', __name__, url_prefix='/upload_logs')

# 로그 정규식 패턴
APACHE_LOG_PATTERN = (
    r'(?P<ip_address>\S+) '          # IP Address
    r'(?P<identity>\S+) '            # Identity (ignored)
    r'(?P<userid>\S+) '              # UserID (ignored)
    r'\[(?P<timestamp>[^\]]+)\] '    # Timestamp
    r'"(?P<method>\S+) '             # HTTP Method
    r'(?P<url>[^\s]+) '              # URL
    r'(?P<protocol>[^\s]+)" '        # Protocol
    r'(?P<status>\d{3}) '            # Status Code
    r'(?P<size>\S+)'                 # Response Size
)

NGINX_LOG_PATTERN = (
    r'(?P<ip_address>\S+) - - \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<url>[^\s]+) HTTP/\d.\d" '
    r'(?P<status>\d{3}) (?P<size>\d+)'
)

def determine_level(method, status):
    """
    Method와 Status Code에 따라 Log Level을 결정합니다.
    """
    # Method 기준 TRACE, DEBUG 설정
    method = method.upper() if method else "UNKNOWN"
    if method in {"GET", "HEAD"}:
        return "TRACE"
    elif method in {"POST", "PUT", "DELETE", "PATCH"}:
        return "DEBUG"
    elif method == "OPTIONS":
        return "INFO"

    # Status Code 기준 INFO, WARN, ERROR, FATAL 설정
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

    # 기본값
    return "INFO"

@upload_logs_bp.route('/', methods=['GET', 'POST'])
def upload_logs():
    if request.method == 'GET':
        return render_template('upload_logs.html')

    # POST 요청 처리
    file = request.files.get('file')
    if not file:
        return render_template('upload_logs.html', message="No file uploaded")
    if not file.filename.endswith(('.log', '.txt', '.json')):
        return render_template('upload_logs.html', message="Supported formats: .log, .txt, .json")

    try:
        filename = secure_filename(file.filename)
        file_stream = file.stream

        # JSON 형식 로그 처리
        if filename.endswith('.json'):
            process_json_logs(file_stream)

        # 텍스트 형식 로그 처리
        elif filename.endswith(('.log', '.txt')):
            process_text_logs(file_stream)

        return render_template('upload_logs.html', message="Logs successfully uploaded and processed")

    except Exception as e:
        return render_template('upload_logs.html', message=f"Error processing file: {e}")

# Apache/Nginx 타임스탬프 형식을 파싱하기 위한 함수
def parse_timestamp(raw_timestamp):
    try:
        # Apache/Nginx 로그 형식 변환: '17/May/2015:23:05:58 +0000'
        return datetime.strptime(raw_timestamp, "%d/%b/%Y:%H:%M:%S %z")
    except ValueError:
        # 기본 ISO 형식 처리
        try:
            return datetime.fromisoformat(raw_timestamp)
        except ValueError:
            return None  # 변환 실패 시 None 반환

# JSON 로그 처리 함수
def process_json_logs(file_stream):
    logs = json.load(file_stream)
    for log in logs:
        raw_timestamp = log.get("timestamp")
        parsed_timestamp = parse_timestamp(raw_timestamp)  # 타임스탬프 변환
        if not parsed_timestamp:
            continue  # 변환 실패 시 무시

        method = log.get("method", "")
        status = log.get("status", "200")  # 상태 코드 기본값
        level = determine_level(method, status)
        message = log.get("message", "")
        source_ip = log.get("source_ip", "")  # `source`로 매핑
        insert_log(parsed_timestamp, level, message, method, source_ip)

# 텍스트 로그 처리 함수
def process_text_logs(file_stream):
    for line in file_stream:
        line = line.decode('utf-8').strip()
        for pattern in [APACHE_LOG_PATTERN, NGINX_LOG_PATTERN]:
            match = re.match(pattern, line)
            if match:
                data = match.groupdict()
                raw_timestamp = data['timestamp']
                parsed_timestamp = parse_timestamp(raw_timestamp)  # 타임스탬프 변환
                if not parsed_timestamp:
                    continue  # 변환 실패 시 무시
                method = data.get('method', "")
                level = determine_level(method, data.get('status', "200"))
                ip_address = data['ip_address']
                url = data.get('url', "")
                status = data.get('status', "")
                size = data.get('size', "0")
                message = f"{url} {status} {size}"
                insert_log(parsed_timestamp, level, message, method, ip_address)
                break

