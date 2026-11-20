
import sqlite3
import hashlib
import secrets
from pathlib import Path

# Database location
DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "myspace.db"
)


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# ---------------- INITIALIZE DATABASE ----------------

def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()


# ---------------- PASSWORD HASHING ----------------

def hash_password(password, salt=None):

    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        310000
    ).hex()

    return password_hash, salt


# ---------------- USER REGISTRATION ----------------

def register_user(full_name, email, password):

    initialize_database()

    email = email.strip().lower()
    full_name = full_name.strip()

    if not full_name or not email or not password:
        return False, "All fields are required."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    password_hash, salt = hash_password(password)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (
                full_name,
                email,
                password_hash,
                salt
            )
            VALUES (?, ?, ?, ?)
        """, (
            full_name,
            email,
            password_hash,
            salt
        ))

        conn.commit()
        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."

    finally:
        conn.close()


# ---------------- USER LOGIN ----------------

def login_user(email, password):

    initialize_database()

    email = email.strip().lower()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
        AND is_active = 1
    """, (email,))

    user = cursor.fetchone()

    if not user:
        conn.close()
        return None

    password_hash, _ = hash_password(
        password,
        user["salt"]
    )

    if not secrets.compare_digest(
        password_hash,
        user["password_hash"]
    ):
        conn.close()
        return None

    cursor.execute("""
        UPDATE users
        SET last_login = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (user["id"],))

    conn.commit()

    user_data = dict(user)
    conn.close()

    return {
        "id": user_data["id"],
        "full_name": user_data["full_name"],
        "email": user_data["email"],
        "role": user_data["role"]
    }
