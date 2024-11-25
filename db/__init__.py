import sqlite3

DB_PATH = 'logs.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            level TEXT,
            message TEXT,
            source TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_log(timestamp, level, message, source):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs (timestamp, level, message, source)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, level, message, source))
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

