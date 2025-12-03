import sqlite3
import os

DATABASE_PATH = "phoenix.db"

def fix_db():
    if not os.path.exists(DATABASE_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    
    print("Checking for is_admin column...")
    try:
        cur.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0;")
        print("Added is_admin column.")
    except Exception as e:
        print(f"Column might already exist or error: {e}")
        
    conn.commit()
    conn.close()
    print("Database fix completed.")

if __name__ == "__main__":
    fix_db()
