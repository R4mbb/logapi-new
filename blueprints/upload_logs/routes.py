from flask import Blueprint, request, render_template
import re
from db import insert_log

upload_logs_bp = Blueprint('upload_logs', __name__, url_prefix='/upload_logs')

# Apache Log Regex Pattern
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

@upload_logs_bp.route('/', methods=['GET', 'POST'])
def upload_logs():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            return render_template('upload_logs.html', message="No file uploaded")
        if not file.filename.endswith(('.log', '.txt')):
            return render_template('upload_logs.html', message="Only .log or .txt files are allowed")

        try:
            logs = file.read().decode('utf-8').splitlines()
            parsed_logs = []

            for line in logs:
                match = re.match(APACHE_LOG_PATTERN, line)
                if match:
                    data = match.groupdict()
                    timestamp = data['timestamp']
                    ip_address = data['ip_address']
                    method = data['method']
                    url = data['url']
                    protocol = data['protocol']
                    status = data['status']
                    size = data['size'] if data['size'] != '-' else 0

                    # Add parsed log to the list
                    parsed_logs.append((timestamp, "INFO", f"{method} {url} {protocol} {status} {size}", ip_address))
            
            # Save parsed logs to database
            for log in parsed_logs:
                insert_log(*log)

            return render_template('upload_logs.html', message=f"Successfully processed {len(parsed_logs)} logs.")
        except Exception as e:
            return render_template('upload_logs.html', message=f"Error: {str(e)}")

    return render_template('upload_logs.html', message=None)

