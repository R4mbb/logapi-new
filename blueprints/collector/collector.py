import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from db import insert_log
import re

LOG_PATH = "/var/log/apache2/access.log"

class LogHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == LOG_PATH:
            with open(LOG_PATH, 'r') as f:
                lines = f.readlines()
                for line in lines[-10:]:  # 마지막 10줄만 처리
                    parts = line.split()
                    if len(parts) > 8:
                        timestamp = parts[3][1:]
                        source = parts[0]
                        status = int(parts[8])
                        
                        # Determine log level based on status code
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

                        message = f"{parts[5][1:]} {parts[6]} {parts[7][:-1]} {status} {parts[9]}"
                        insert_log(timestamp, level, message, source)

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

