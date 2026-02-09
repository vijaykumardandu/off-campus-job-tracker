import sqlite3

def connect_db():
    conn = sqlite3.connect("applications.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            link TEXT,
            score INTEGER,
            status TEXT,
            date_applied TEXT
        )
    """)

    conn.commit()
    return conn
