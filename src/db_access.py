import sqlite3

# SQLite database setup
DB_FILE = 'db/notified_errors.db'


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notified_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_ip TEXT NOT NULL,
            log_filename TEXT NOT NULL,
            error_keyword TEXT NOT NULL,
            notified_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def has_been_notified(server_ip, log_filename, error_keyword):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM notified_errors
        WHERE server_ip = ? AND log_filename = ? AND error_keyword = ?
    ''', (server_ip, log_filename, error_keyword))
    result = cursor.fetchone()[0]
    conn.close()
    return result > 0


def record_notification(server_ip, log_filename, error_keyword):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notified_errors (server_ip, log_filename, error_keyword)
        VALUES (?, ?, ?)
    ''', (server_ip, log_filename, error_keyword))
    conn.commit()
    conn.close()
