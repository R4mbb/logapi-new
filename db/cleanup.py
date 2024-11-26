import os
import sqlite3
import pandas as pd
import gzip
import shutil
from datetime import datetime, timedelta

DB_PATH = "logs.db"
EXPORT_DIR = "exports/"
MAX_DB_SIZE_MB = 50  # Maximum DB size in MB
MAX_LOG_COUNT = 10000  # Maximum number of logs
RETENTION_DAYS = 30  # 로그 유지 기간 (30일)

def get_db_size():
    """Get the size of the database file in MB."""
    return os.path.getsize(DB_PATH) / (1024 * 1024)

def get_log_count():
    """Get the number of logs in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM logs")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def export_logs():
    """Export logs to a CSV file and compress it."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM logs", conn)
    conn.close()

    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

    # Save logs to a CSV file
    export_file = os.path.join(EXPORT_DIR, "logs_export.csv")
    df.to_csv(export_file, index=False)

    # Compress the CSV file
    compressed_file = export_file + ".gz"
    with open(export_file, "rb") as f_in:
        with gzip.open(compressed_file, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Remove the original CSV file after compression
    os.remove(export_file)
    return compressed_file

def cleanup_database():
    """Clean up old logs from the database."""
    cutoff_date = (datetime.now() - timedelta(days=RETENTION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)

    try:
        # 트랜잭션 시작 (동시성 문제 방지)
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()

        # 오래된 로그 삭제
        cursor.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff_date,))
        deleted_count = cursor.rowcount
        conn.commit()
        print(f"{deleted_count} old logs deleted.")
    except sqlite3.Error as e:
        print(f"Database cleanup failed: {e}")
        conn.rollback()
    finally:
        conn.close()

def manage_database():
    """Check database status and perform cleanup if necessary."""
    db_size = get_db_size()
    log_count = get_log_count()

    if db_size > MAX_DB_SIZE_MB or log_count > MAX_LOG_COUNT:
        print(f"Database size: {db_size:.2f} MB, Log count: {log_count}. Exporting logs...")
        compressed_file = export_logs()
        print(f"Logs exported and compressed to: {compressed_file}")

    # Cleanup old logs
    cleanup_database()

