import sqlite3
import sys

DATABASE_PATH = "phoenix.db"

def make_admin(email):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, email, is_admin FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        print(f"User with email '{email}' not found.")
        return

    if user[2] == 1:
        print(f"User '{email}' is already an admin.")
    else:
        cursor.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email,))
        conn.commit()
        print(f"Successfully made '{email}' an admin.")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <email>")
    else:
        make_admin(sys.argv[1])
