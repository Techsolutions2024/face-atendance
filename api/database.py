import sqlite3

DB_PATH = 'attendance.db'

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def create_database(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        mssv TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        gender TEXT NOT NULL,
        dob TEXT NOT NULL,
        major TEXT NOT NULL,
        class TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS student_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        embedding BLOB,
        image BLOB,
        FOREIGN KEY (student_id) REFERENCES students(mssv)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        timestamp TEXT,
        status TEXT,
        image BLOB,
        FOREIGN KEY (student_id) REFERENCES students(mssv)
    )''')
    conn.commit()
