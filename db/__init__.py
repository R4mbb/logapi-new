import sqlite3
import logging
import pandas as pd

DB_PATH = 'logs.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Apache2 로그 처리 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS apache2_processed_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        last_log_id TEXT NOT NULL UNIQUE,
        last_timestamp TEXT NOT NULL
    )
    """)

    # Nginx 로그 처리 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nginx_processed_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        last_log_id TEXT NOT NULL UNIQUE,
        last_timestamp TEXT NOT NULL
    )
    """)

    # Apache2 로그 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS apache2_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        level TEXT NOT NULL,
        message TEXT NOT NULL,
        method TEXT NOT NULL,
        source TEXT NOT NULL
    )
    """)

    # Nginx 로그 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nginx_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        level TEXT NOT NULL,
        message TEXT NOT NULL,
        method TEXT NOT NULL,
        source TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def insert_log(timestamp, level, message, method, source, log_type=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if log_type == 'apache2':
        cursor.execute('''
            INSERT INTO apache2_logs (timestamp, level, message, method, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, level, message, method, source))
    elif log_type == 'nginx':
        cursor.execute('''
            INSERT INTO nginx_logs (timestamp, level, message, method, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, level, message, method, source))
    conn.commit()
    conn.close()

def query_logs(query, params=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    results = cursor.fetchall()
    conn.close()
    return results


def execute_query(query, params=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    conn.commit()
    conn.close()

def get_live_logs(log_type, x_axis, y_axis, color):
    try:
        columns = [x_axis] + ([y_axis] if y_axis != 'count' else []) + ([color] if color else [])
        query = f"SELECT {', '.join(columns)} FROM {log_type}"
        rows = query_logs(query)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=columns)

        if y_axis == 'count':
            if color:
                df = df.groupby([x_axis, color]).size().reset_index(name='count')
            else:
                df = df.groupby(x_axis).size().reset_index(name='count')

        return df

    except Exception as e:
        logging.error(f"Error fetching live logs for log_type '{log_type}': {e}")
        return pd.DataFrame()

