import time
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from db import insert_log, query_logs, execute_query

LOG_PATH = "/var/log/apache2/access.log"

class LogHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_processed_id, self.last_processed_timestamp = self.load_last_processed_log()

    def load_last_processed_log(self):
        """Load the last processed log's ID and timestamp."""
        result = query_logs("SELECT last_log_id, last_timestamp FROM processed_logs ORDER BY id DESC LIMIT 1")
        if result:
            return result[0][0], result[0][1]
        return None, None

    def save_last_processed_log(self, log_id, timestamp):
        """Save the last processed log's ID and timestamp."""
        execute_query("INSERT OR REPLACE INTO processed_logs (last_log_id, last_timestamp) VALUES (?, ?)", (log_id, timestamp))

    def generate_log_id(self, ip, method, url, status, timestamp):
        """Generate a unique ID for a log."""
        unique_string = f"{ip}-{method}-{url}-{status}-{timestamp}"
        return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()

    def on_modified(self, event):
        if event.src_path == LOG_PATH:
            with open(LOG_PATH, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    parts = line.split()
                    if len(parts) > 8:
                        timestamp = parts[3][1:]
                        source = parts[0]
                        method = parts[5][1:]
                        url = parts[6]
                        protocol = parts[7][:-1]
                        status = int(parts[8])
                        
                        # Determine log level
                        if 200 <= status < 300:
                            level = "INFO"
                        elif 300 <= status < 400:
                            level = "REDIRECT"
                        elif 400 <= status < 500:
                            level = "WARNING"
                        elif 500 <= status < 600:
                            level = "ERROR"
                        else:
                            level = "UNKNOWN"

                        message = f"{method} {url} {protocol} {status} {parts[9]}"
                        log_id = self.generate_log_id(source, method, url, status, timestamp)

                        # Skip already processed logs
                        if self.last_processed_id == log_id and self.last_processed_timestamp == timestamp:
                            continue

                        # Insert the new log and update last processed
                        insert_log(timestamp, level, message, source)
                        self.save_last_processed_log(log_id, timestamp)
                        self.last_processed_id, self.last_processed_timestamp = log_id, timestamp

def start_log_collector():
    event_handler = LogHandler()
    observer = Observer()
    observer.schedule(event_handler, path="/var/log/apache2/", recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

