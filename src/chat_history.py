
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUTH_DB = ROOT / "data" / "myspace.db"


def get_connection():
    AUTH_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(AUTH_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_chat_tables():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                sender TEXT NOT NULL
                    CHECK(sender IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chat_sessions(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_chat_sessions_user
            ON chat_sessions(user_id);

            CREATE INDEX IF NOT EXISTS idx_chat_messages_chat
            ON chat_messages(chat_id);
        """)


def create_chat(user_id, title="New Chat"):
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO chat_sessions (user_id, title)
            VALUES (?, ?)
        """, (user_id, title))
        return cursor.lastrowid


def get_user_chats(user_id):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, title, created_at, updated_at
            FROM chat_sessions
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
        """, (user_id,)).fetchall()

        return [dict(row) for row in rows]


def get_chat_messages(chat_id, user_id):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT m.id, m.sender, m.content, m.created_at
            FROM chat_messages m
            JOIN chat_sessions s ON s.id = m.chat_id
            WHERE m.chat_id = ? AND s.user_id = ?
            ORDER BY m.id ASC
        """, (chat_id, user_id)).fetchall()

        return [dict(row) for row in rows]


def save_chat_message(chat_id, user_id, sender, content):
    if sender not in ("user", "assistant"):
        raise ValueError("Invalid message sender.")

    with get_connection() as conn:
        chat = conn.execute("""
            SELECT id
            FROM chat_sessions
            WHERE id = ? AND user_id = ?
        """, (chat_id, user_id)).fetchone()

        if not chat:
            raise PermissionError(
                "This conversation does not belong to this user."
            )

        conn.execute("""
            INSERT INTO chat_messages (chat_id, sender, content)
            VALUES (?, ?, ?)
        """, (chat_id, sender, content))

        conn.execute("""
            UPDATE chat_sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, (chat_id, user_id))


def update_chat_title(chat_id, user_id, title):
    with get_connection() as conn:
        conn.execute("""
            UPDATE chat_sessions
            SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, (title, chat_id, user_id))


def delete_chat(chat_id, user_id):
    with get_connection() as conn:
        cursor = conn.execute("""
            DELETE FROM chat_sessions
            WHERE id = ? AND user_id = ?
        """, (chat_id, user_id))

        return cursor.rowcount > 0
