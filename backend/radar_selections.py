
import sqlite3
import time
from typing import Optional, List

DB_FILE = "radar_data.db"

# ==========================================
# 1. Initialize Database (Selections Table)
# ==========================================
def init_selection_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 选题表
    # status: 'todo' (待办), 'completed' (已完成), 'abandoned' (放弃)
    c.execute('''CREATE TABLE IF NOT EXISTS selections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id VARCHAR(50),
                  topic TEXT,
                  source VARCHAR(50),
                  hotspot_id TEXT, 
                  status VARCHAR(20) DEFAULT 'todo',
                  priority INTEGER DEFAULT 1,
                  note TEXT,
                  created_at REAL,
                  updated_at REAL)''')
                  
    conn.commit()
    conn.close()

init_selection_db()

# ==========================================
# 2. CRUD Operations
# ==========================================

def add_selection(user_id: str, topic: str, source: str = "Manual", hotspot_id: Optional[str] = None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = time.time()
    
    # Check duplicates for same user and topic (optional, but good practice)
    c.execute("SELECT id FROM selections WHERE user_id=? AND topic=? AND status!='abandoned'", (user_id, topic))
    if c.fetchone():
        conn.close()
        return {"status": "error", "message": "该选题已存在"}

    c.execute('''INSERT INTO selections 
                 (user_id, topic, source, hotspot_id, status, created_at, updated_at)
                 VALUES (?,?,?,?,?,?,?)''',
              (user_id, topic, source, hotspot_id, 'todo', now, now))
    
    sid = c.lastrowid
    conn.commit()
    conn.close()
    return {"status": "success", "id": sid}

def get_selections(user_id: str, status: Optional[str] = None, page: int = 1, page_size: int = 20):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    sql = "SELECT id, topic, source, status, created_at, updated_at FROM selections WHERE user_id=?"
    params = [user_id]
    
    if status and status != 'all':
        sql += " AND status=?"
        params.append(status)
        
    # Count
    count_sql = sql.replace("SELECT id, topic, source, status, created_at, updated_at", "SELECT count(*)")
    c.execute(count_sql, params)
    total = c.fetchone()[0]
    
    # Pagination
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    offset = (page - 1) * page_size
    params.extend([page_size, offset])
    
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    
    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "topic": r[1],
            "source": r[2],
            "status": r[3],
            "created_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(r[4])),
            "updated_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(r[5]))
        })
        
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

def update_selection_status(selection_id: int, user_id: str, status: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("SELECT user_id FROM selections WHERE id=?", (selection_id,))
    row = c.fetchone()
    if not row or row[0] != user_id:
        conn.close()
        return {"status": "error", "message": "无权限或选题不存在"}
        
    valid_statuses = ['todo', 'completed', 'abandoned']
    if status not in valid_statuses:
        conn.close()
        return {"status": "error", "message": "无效的状态"}
        
    c.execute("UPDATE selections SET status=?, updated_at=? WHERE id=?", (status, time.time(), selection_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

def delete_selection(selection_id: int, user_id: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("DELETE FROM selections WHERE id=? AND user_id=?", (selection_id, user_id))
    if c.rowcount == 0:
        conn.close()
        return {"status": "error", "message": "删除失败"}
        
    conn.commit()
    conn.close()
    return {"status": "success"}
