import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS comments")
    cursor.execute("DROP TABLE IF EXISTS users")

    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)

    cursor.execute("""
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", "admin123", "admin"))
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("alumno", "alumno123", "user"))
    cursor.execute("INSERT INTO comments (user_id, content) VALUES (?, ?)", (1, "Comentario inicial del administrador."))
    cursor.execute("INSERT INTO comments (user_id, content) VALUES (?, ?)", (2, "Comentario de prueba de un usuario normal."))

    conn.commit()
    conn.close()
    print(f"Base de datos inicializada en {DB_PATH}")


if __name__ == "__main__":
    init_db()
