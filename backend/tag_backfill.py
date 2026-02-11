import sqlite3
import time
import json
import sys
import os

# Ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from radar_tags import get_tag_id_by_name

DB_FILE = "radar_data.db"

def refresh_tags_from_json():
    """
    Scan 'mentions' table, parse 'manual_tags' JSON or string, 
    and backfill 'article_tags' table.
    """
    print("⏳ Starting Tag Backfill...")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Select all mentions
    c.execute("SELECT id, manual_tags, manual_category, clean_status FROM mentions")
    rows = c.fetchall()
    
    count = 0
    new_links = 0
    
    for row in rows:
        m_id, tags_json, category, status = row
        count += 1
        
        # Parse tags
        tags_list = []
        if tags_json:
            try:
                # Could be JSON array string or simple comma string
                if tags_json.strip().startswith('['):
                    tags_list = json.loads(tags_json)
                else:
                    tags_list = tags_json.split(',')
            except:
                tags_list = [str(tags_json)]

        # Add Category as a tag if valid
        if category and category != '综合':
             cat_id = get_tag_id_by_name(category, "CATEGORY")
             if cat_id:
                  try:
                      c.execute("INSERT OR IGNORE INTO article_tags (article_id, tag_id, confidence, source) VALUES (?, ?, ?, ?)",
                                (str(m_id), cat_id, 1.0, 'Backfill'))
                      new_links += c.rowcount
                  except: pass

        # Add Entity Tags
        for t_name in tags_list:
            t_name = t_name.strip()
            if not t_name: continue
            
            tid = get_tag_id_by_name(t_name)
            if not tid:
                # Create loose tag
                try:
                    c.execute("INSERT INTO tags (name, tag_type, count, create_time) VALUES (?, ?, 0, ?)", 
                             (t_name, 'ENTITY', time.time()))
                    tid = c.lastrowid
                except:
                    # Retry get
                    tid = get_tag_id_by_name(t_name)
            
            if tid:
                try:
                    c.execute("INSERT OR IGNORE INTO article_tags (article_id, tag_id, confidence, source) VALUES (?, ?, ?, ?)",
                              (str(m_id), tid, 1.0, 'Backfill'))
                    if c.rowcount > 0:
                        c.execute("UPDATE tags SET count = count + 1 WHERE id=?", (tid,))
                        new_links += 1
                except: pass
                
        if count % 100 == 0:
            print(f"  Processed {count} items...")
            conn.commit()

    conn.commit()
    conn.close()
    print(f"✅ Backfill Complete. Processed {count} items. Created {new_links} links.")

if __name__ == "__main__":
    refresh_tags_from_json()
