import sys
import os
import sqlite3
import json
import time

# Ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radar_tags import get_tag_taxonomy, get_tag_id_by_name, create_tag, TagCreateReq, DB_FILE
from radar_ai import analyze_content_tags

def run_batch_tagging():
    # 1. Load Taxonomy
    print("⏳ Loading Tag Taxonomy...")
    taxonomy = get_tag_taxonomy()
    print(f"✅ Loaded {len(taxonomy)} categories.")

    # 2. Fetch Mentions (Content)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Fetch uncleaned or all mentions? User said "fetched content". Let's do latest 20 for testing.
    # User might want EVERYTHING re-tagged. Let's do a batch of 50.
    c.execute("SELECT id, content_text, title FROM mentions ORDER BY id DESC")
    mentions = c.fetchall()
    
    if not mentions:
        print("⚠️ No mentions found to tag.")
        return

    print(f"🚀 Processing {len(mentions)} items...")

    for m_id, content, title in mentions:
        text = (title or "") + "\n" + (content or "")
        if len(text) < 10:
            print(f"⚠️ Item {m_id}: Content too short, skipping.")
            continue
            
        print(f"\n===== Analyzing Item {m_id}: {title[:20]}... =====")
        
        # 3. Call AI
        result = analyze_content_tags(text, taxonomy)
        if not result:
            print(f"❌ AI analysis failed for {m_id}")
            continue
            
        print(f"🤖 AI Result: {json.dumps(result, ensure_ascii=False)}")
        
        # 4. Save Tags
        # 4a. Level 1 Category
        l1_name = result.get('level1_category')
        l1_id = None
        if l1_name:
            l1_id = get_tag_id_by_name(l1_name, "CATEGORY")
            if l1_id:
                save_article_tag(c, m_id, l1_id, 1.0, "AI")
            else:
                 print(f"  ⚠️ Warning: Category '{l1_name}' not found in DB.")

        # 4b. Level 2 Entities (Create if new)
        l2_names = result.get('level2_entities', [])
        for l2_name in l2_names:
            l2_id = get_tag_id_by_name(l2_name, "ENTITY")
            
            if not l2_id:
                # Create NEW Entity
                print(f"  ✨ Creating NEW Entity: {l2_name} (Parent: {l1_name})")
                parent_ids = [l1_id] if l1_id else []
                req = TagCreateReq(name=l2_name, tag_type="ENTITY", parent_ids=parent_ids)
                res = create_tag(req)
                if res['status'] == 'success':
                    l2_id = res['id']
                else:
                    print(f"  ❌ Failed to create entity: {res}")
            
            if l2_id:
                save_article_tag(c, m_id, l2_id, 0.9, "AI")
                
        # 4c. Other Tags (Event, Quality, Sentiment) - Create as loose tags if needed
        # Event
        for tag_name in result.get('event_tags', []):
            save_loose_tag(c, m_id, tag_name, "EVENT")
            
        # Quality
        for tag_name in result.get('quality_tags', []):
            save_loose_tag(c, m_id, tag_name, "QUALITY")
            
        # Sentiment
        sent_map = {"POSITIVE": "正面", "NEGATIVE": "负面", "NEUTRAL": "中立"}
        sent_val = result.get('sentiment')
        if sent_val:
            sent_name = sent_map.get(sent_val, sent_val)
            save_loose_tag(c, m_id, sent_name, "SENTIMENT")
            
        conn.commit()
        
        # Rate limit protection (Gemini Free Tier)
        print("  ⏳ Waiting 30s to respect rate limits...")
        time.sleep(30)

    conn.close()
    print("\n✅ Batch Tagging Complete.")

def save_loose_tag(cursor, article_id, tag_name, tag_type):
    # Check if tag exists
    tid = get_tag_id_by_name(tag_name, tag_type)
    if not tid:
        # Create it (loose tag, no parent)
        try:
            cursor.execute("INSERT INTO tags (name, tag_type, count, create_time) VALUES (?,?,0,?)",
                           (tag_name, tag_type, time.time()))
            tid = cursor.lastrowid
            print(f"  ✨ Created {tag_type} tag: {tag_name}")
        except sqlite3.IntegrityError:
            print(f"  ⚠️ Tag '{tag_name}' collision.")
            tid = get_tag_id_by_name(tag_name) # Retry get
            
    if tid:
        save_article_tag(cursor, article_id, tid, 0.8, "AI")

def save_article_tag(cursor, article_id, tag_id, confidence, source):
    # Expects article_id to be stored as string in article_tags
    art_id_str = str(article_id)
    # Check duplicate
    cursor.execute("SELECT id FROM article_tags WHERE article_id=? AND tag_id=?", (art_id_str, tag_id))
    if cursor.fetchone():
        return # Already exists
        
    cursor.execute(
        "INSERT INTO article_tags (article_id, tag_id, confidence, source) VALUES (?,?,?,?)",
        (art_id_str, tag_id, confidence, source)
    )
    # Increment count
    cursor.execute("UPDATE tags SET count = count + 1 WHERE id=?", (tag_id,))

if __name__ == "__main__":
    run_batch_tagging()
