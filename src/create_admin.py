
from src.auth_database import get_connection, initialize_database


def make_admin():

    initialize_database()

    email = input("Enter your registered email: ").strip().lower()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, full_name FROM users WHERE email = ?",
        (email,)
    )

    user = cursor.fetchone()

    if user is None:
        print("Account not found. Please register first.")
        conn.close()
        return

    cursor.execute(
        "UPDATE users SET role = 'admin' WHERE id = ?",
        (user["id"],)
    )

    conn.commit()
    conn.close()

    print(f"Admin access granted to {user['full_name']}.")


if __name__ == "__main__":
    make_admin()
