import sqlite3
import sys
import os

DB_FILE = "radar_data.db"

def debug_query():
    print("Testing Content Library Query...")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Simulate params
    start_time = 0
    params = [start_time]
    
    base_cols = "m.id, m.client_id, m.source, m.title, m.content_text, m.url, m.publish_time, m.sentiment_score, m.risk_level, m.clean_status, m.manual_category, m.manual_sentiment"
    
    sql = f"""
        SELECT {base_cols}, GROUP_CONCAT(t.name) as tag_names
        FROM mentions m
        LEFT JOIN article_tags at ON cast(m.id as text) = at.article_id
        LEFT JOIN tags t ON at.tag_id = t.id
        WHERE m.publish_time > ?
    """
    
    # Add grouping
    sql += " GROUP BY m.id"
    
    # Add Limit
    sql += " ORDER BY m.publish_time DESC LIMIT ? OFFSET ?"
    params.extend([20, 0])
    
    print("SQL:", sql)
    
    try:
        c.execute(sql, params)
        rows = c.fetchall()
        print(f"Success! Retrieved {len(rows)} rows.")
        if rows:
            print("First row sample:", rows[0])
    except Exception as e:
        print("SQL Error:", e)

    # Check if tables exist
    print("\nChecking tables:")
    try:
        c.execute("SELECT count(*) FROM article_tags")
        print("article_tags count:", c.fetchone()[0])
    except Exception as e:
        print("article_tags table error:", e)

    conn.close()

if __name__ == "__main__":
    debug_query()
