import sqlite3

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
    """
    Execute a SELECT query and return results.

    Args:
        query (str): SQL query to execute.
        params (tuple): Parameters to pass with the query (default: None).

    Returns:
        list: Query results as a list of tuples.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    results = cursor.fetchall()
    conn.close()
    return results


def execute_query(query, params=None):
    """
    Execute a query that modifies the database (INSERT, UPDATE, DELETE).

    Args:
        query (str): The SQL query to execute.
        params (tuple): The parameters for the query.

    Returns:
        None
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    conn.commit()
    conn.close()


