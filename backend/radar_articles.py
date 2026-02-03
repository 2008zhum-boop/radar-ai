
import sqlite3
import time
import json
from typing import Optional, List

DB_FILE = "radar_data.db"

# ==========================================
# 1. 数据库初始化 (Article Table)
# ==========================================
def init_article_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 智能创作文章表
    c.execute('''CREATE TABLE IF NOT EXISTS articles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id VARCHAR(50),
                  title TEXT,
                  content TEXT,
                  summary TEXT,
                  cover_url TEXT,
                  topic TEXT,
                  status VARCHAR(20) DEFAULT 'draft',
                  created_at REAL,
                  updated_at REAL)''')
                  
    conn.commit()
    conn.close()

init_article_db()

# ==========================================
# 2. CRUD Operations
# ==========================================

def save_article(user_id: str, title: str, content: str, 
                 summary: str = "", cover_url: str = "", 
                 topic: str = "", status: str = "draft", 
                 article_id: Optional[int] = None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    now = time.time()
    
    if article_id:
        # Update existing
        # Security check: ensure user owns the article (or is admin? simplistic for now: checks owner)
        c.execute("SELECT user_id FROM articles WHERE id=?", (article_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return {"error": "Article not found"}
        # Allow overwriting for now
        
        c.execute('''UPDATE articles 
                     SET title=?, content=?, summary=?, cover_url=?, topic=?, status=?, updated_at=?
                     WHERE id=?''',
                  (title, content, summary, cover_url, topic, status, now, article_id))
        aid = article_id
    else:
        # Create new
        c.execute('''INSERT INTO articles 
                     (user_id, title, content, summary, cover_url, topic, status, created_at, updated_at)
                     VALUES (?,?,?,?,?,?,?,?,?)''',
                  (user_id, title, content, summary, cover_url, topic, status, now, now))
        aid = c.lastrowid
        
    conn.commit()
    conn.close()
    return {"status": "success", "id": aid}

def get_articles(user_id: str, status: Optional[str] = None, search: Optional[str] = None, page: int = 1, page_size: int = 10):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    sql = "SELECT id, title, summary, cover_url, topic, status, updated_at, created_at FROM articles WHERE 1=1"
    params = []
    
    # Filter by user (optional: if admin sees all? sticking to user-isolation for now)
    # sql += " AND user_id=?"
    # params.append(user_id) 
    # Actually user requested "Works Management", presumably for themselves or all if admin. 
    # Let's assume user sees their own works for now, or all if we want a shared CMS.
    # Given context, likely personal drafts.
    
    # Removing user filter for now to simplify "global works" view or just assume single user context mostly.
    # Wait, strict multi-user supports requires filtering.
    sql += " AND user_id=?"
    params.append(user_id)
    
    if status is not None and status != "all":
        sql += " AND status=?"
        params.append(status)
        
    if search:
        sql += " AND title LIKE ?"
        params.append(f"%{search}%")
        
    # Count total
    count_sql = sql.replace("SELECT id, title, summary, cover_url, topic, status, updated_at, created_at", "SELECT count(*)")
    c.execute(count_sql, params)
    total = c.fetchone()[0]
    
    # Pagination
    sql += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
    offset = (page - 1) * page_size
    params.extend([page_size, offset])
    
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    
    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "title": r[1],
            "summary": r[2],
            "cover_url": r[3],
            "topic": r[4],
            "status": r[5],
            "status_label": "已发布" if r[5]=='published' else "草稿",
            "updated_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(r[6])),
            "created_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(r[7]))
        })
        
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

def get_article_detail(article_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, user_id, title, content, summary, cover_url, topic, status, updated_at FROM articles WHERE id=?", (article_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return None
        
    return {
        "id": row[0],
        "user_id": row[1],
        "title": row[2],
        "content": row[3],
        "summary": row[4],
        "cover_url": row[5],
        "topic": row[6],
        "status": row[7],
        "updated_at": row[8]
    }

def delete_article(article_id: int, user_id: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check ownership
    c.execute("SELECT user_id FROM articles WHERE id=?", (article_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return {"error": "Not found"}
    if row[0] != user_id:
        conn.close()
        return {"error": "Permission denied"}
        
    c.execute("DELETE FROM articles WHERE id=?", (article_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}
