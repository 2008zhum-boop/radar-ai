
import sqlite3
import sys

DB_FILE = "radar_data.db"

def list_users():
    print(f"\nScanning database: {DB_FILE}...")
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT username, role, status FROM users")
        rows = c.fetchall()
        
        print(f"\n{'USERNAME':<20} | {'ROLE':<10} | {'STATUS':<10}")
        print("-" * 50)
        for r in rows:
            print(f"{r[0]:<20} | {r[1]:<10} | {r[2]:<10}")
        print("-" * 50)
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        print(f"Error reading database: {e}")
        return []

def update_role(username, role):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE users SET role=? WHERE username=?", (role, username))
        conn.commit()
        if c.rowcount > 0:
            print(f"\n✅ Successfully updated '{username}' to role '{role}'.")
        else:
            print(f"\n❌ User '{username}' not found.")
        conn.close()
    except Exception as e:
        print(f"Error updating role: {e}")

if __name__ == "__main__":
    users = list_users()
    
    if len(sys.argv) > 2:
        target_user = sys.argv[1]
        new_role = sys.argv[2]
        if new_role not in ["admin", "editor", "viewer"]:
            print("Invalid role. Use: admin, editor, or viewer")
        else:
            update_role(target_user, new_role)
            list_users() # Show updated list
    else:
        print("\nUsage: python fix_permissions.py [username] [role]")
        print("Example: python fix_permissions.py myuser admin")
