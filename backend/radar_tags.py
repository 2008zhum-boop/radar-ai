import sqlite3
import time
import json
from typing import List, Optional
from pydantic import BaseModel

DB_FILE = "radar_data.db"

# ==========================================
# 1. Pydantic 模型定义 (给 main.py 用的)
# ==========================================

class TagCreateReq(BaseModel):
    name: str
    tag_type: str
    alias: Optional[str] = ""
    parent_id: Optional[int] = None

class TagMergeReq(BaseModel):
    target_id: int
    source_ids: List[int]

class TagUpdateReq(BaseModel):
    id: int
    name: Optional[str] = None
    tag_type: Optional[str] = None
    alias: Optional[str] = None

# ==========================================
# 2. 数据库核心逻辑
# ==========================================

def init_tag_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 标签表
    c.execute('''CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        tag_type TEXT NOT NULL, 
        alias TEXT,
        count INTEGER DEFAULT 0,
        create_time REAL,
        UNIQUE(name, tag_type)
    )''')
    conn.commit()
    conn.close()

def get_tags(tag_type=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    sql = "SELECT * FROM tags"
    params = []
    if tag_type:
        sql += " WHERE tag_type = ?"
        params.append(tag_type)
    sql += " ORDER BY count DESC, id DESC"
    c.execute(sql, tuple(params))
    rows = c.fetchall()
    conn.close()
    return [{"id":r[0], "name":r[1], "type":r[2], "alias":r[3], "count":r[4]} for r in rows]

def create_tag(name, tag_type, alias=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO tags (name, tag_type, alias, create_time) VALUES (?,?,?,?)", 
                  (name, tag_type, alias, time.time()))
        conn.commit()
        return {"status": "success", "id": c.lastrowid}
    except Exception as e:
        return {"status": "error", "msg": str(e)}
    finally:
        conn.close()

def merge_tags(target_id, source_ids):
    """合并标签逻辑"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        # 1. 累加热度
        placeholders = ','.join('?' * len(source_ids))
        c.execute(f"SELECT sum(count) FROM tags WHERE id IN ({placeholders})", tuple(source_ids))
        total = c.fetchone()[0] or 0
        c.execute("UPDATE tags SET count = count + ? WHERE id = ?", (total, target_id))
        # 2. 删除旧标签
        c.execute(f"DELETE FROM tags WHERE id IN ({placeholders})", tuple(source_ids))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}
    finally:
        conn.close()

def get_tag_id_by_name(name, tag_type=None):
    """根据名称获取标签ID"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    sql = "SELECT id FROM tags WHERE name = ?"
    params = [name]
    if tag_type:
        sql += " AND tag_type = ?"
        params.append(tag_type)
    c.execute(sql, tuple(params))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_tag_taxonomy():
    """
    获取完整的标签体系字典 (按类型分组)
    用于 radar_weibo.py 自动匹配关键词
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, tag_type, alias FROM tags")
    rows = c.fetchall()
    conn.close()
    
    taxonomy = {}
    for r in rows:
        tag = {"id": r[0], "name": r[1], "type": r[2], "alias": r[3]}
        if tag["type"] not in taxonomy:
            taxonomy[tag["type"]] = []
        taxonomy[tag["type"]].append(tag)
        
    return taxonomy