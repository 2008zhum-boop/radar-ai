
import sqlite3
from passlib.context import CryptContext

DB_FILE = "radar_data.db"
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def check_users():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT username, email, hashed_password, role, status FROM users")
        rows = c.fetchall()
        
        print(f"Total Users: {len(rows)}")
        for r in rows:
            username = r[0]
            hashed = r[2]
            print(f"User: {username}, Role: {r[3]}, Status: {r[4]}")
            
            # Verify default password 'admin123'
            if username == 'admin':
                is_valid = pwd_context.verify("admin123", hashed)
                print(f"  -> Password 'admin123' matches: {is_valid}")
        
        conn.close()
    except Exception as e:
        print(f"Error reading DB: {e}")

if __name__ == "__main__":
    check_users()
