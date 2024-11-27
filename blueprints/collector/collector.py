import os
import time
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from db import insert_log, query_logs, execute_query
import logging

APACHE_LOG_PATH = "/var/log/apache2/access.log"
NGINX_LOG_PATH = "/var/log/nginx/access.log"
LAST_READ_POSITION_FILE = "/tmp/last_read_position_{}.txt"

# 로깅 설정
logging.basicConfig(
    filename="collector.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_active_webservers():
    """Detect active web servers (Apache2, Nginx)."""
    active_servers = []
    if os.path.exists("/etc/apache2/") and os.path.isfile(APACHE_LOG_PATH):
        active_servers.append("apache2")
    if os.path.exists("/etc/nginx/") and os.path.isfile(NGINX_LOG_PATH):
        active_servers.append("nginx")
    return active_servers

class LogHandler(FileSystemEventHandler):
    def __init__(self, log_type):
        super().__init__()
        self.log_type = log_type
        self.log_path = APACHE_LOG_PATH if log_type == "apache2" else NGINX_LOG_PATH
        self.last_processed_id, self.last_processed_timestamp = self.load_last_processed_log()

    def load_last_processed_log(self):
        """Load the last processed log's ID and timestamp."""
        result = query_logs(f"SELECT last_log_id, last_timestamp FROM {self.log_type}_processed_logs ORDER BY id DESC LIMIT 1")
        if result:
            return result[0][0], result[0][1]
        return None, None

    def save_last_processed_log(self, log_id, timestamp):
        """Save the last processed log's ID and timestamp."""
        execute_query(
            f"INSERT OR REPLACE INTO {self.log_type}_processed_logs (last_log_id, last_timestamp) VALUES (?, ?)",
            (log_id, timestamp)
        )

    def generate_log_id(self, ip, method, url, status, timestamp):
        """Generate a unique ID for a log."""
        unique_string = f"{ip}-{method}-{url}-{status}-{timestamp}"
        return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()

    def get_last_read_position(self):
        """Retrieve the last read position from a file."""
        try:
            with open(LAST_READ_POSITION_FILE.format(self.log_type), 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def save_last_read_position(self, position):
        """Save the last read position to a file."""
        with open(LAST_READ_POSITION_FILE.format(self.log_type), 'w') as f:
            f.write(str(position))

    def determine_log_level(self, status):
        """Determine the log level based on the status code."""
        if 100 <= status < 200:
            return "TRACE"
        elif 200 <= status < 300:
            return "INFO"
        elif 300 <= status < 400:
            return "DEBUG"
        elif 400 <= status < 500:
            return "WARN"
        elif 500 <= status < 600:
            return "ERROR"
        else:
            return "FATAL"

    def on_modified(self, event):
        if event.src_path == self.log_path:
            try:
                with open(self.log_path, 'r') as f:
                    # 마지막 읽은 위치로 이동
                    f.seek(self.get_last_read_position())
                    lines = f.readlines()
                    # 현재 파일 포인터 위치 저장
                    self.save_last_read_position(f.tell())

                    processed_count = 0
                    failed_count = 0

                    for line in lines:
                        try:
                            parts = line.split()
                            if len(parts) > 8:
                                timestamp = parts[3][1:]
                                source = parts[0]
                                method = parts[5][1:]
                                url = parts[6]
                                protocol = parts[7][:-1]
                                status = int(parts[8])

                                # Determine log level
                                level = self.determine_log_level(status)

                                message = f"{method} {url} {protocol} {status} {parts[9]}"
                                log_id = self.generate_log_id(source, method, url, status, timestamp)

                                # Skip already processed logs
                                if self.last_processed_id == log_id and self.last_processed_timestamp == timestamp:
                                    continue

                                # Insert the new log and update last processed
                                insert_log(timestamp, level, message, method, source, self.log_type)
                                self.save_last_processed_log(log_id, timestamp)
                                self.last_processed_id, self.last_processed_timestamp = log_id, timestamp
                                processed_count += 1
                        except Exception as e:
                            logging.error(f"Failed to process log line: {line.strip()} - {e}")
                            failed_count += 1

                    logging.info(f"[{self.log_type}] Logs processed: {processed_count}, Failed: {failed_count}")
            except Exception as e:
                logging.error(f"[{self.log_type}] Failed to read or process log file: {e}")

def start_log_collector():
    active_servers = get_active_webservers()
    handlers = []

    for server in active_servers:
        handler = LogHandler(server)
        observer = Observer()
        observer.schedule(handler, path=os.path.dirname(handler.log_path), recursive=False)
        observer.start()
        handlers.append(observer)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in handlers:
            observer.stop()
        for observer in handlers:
            observer.join()

