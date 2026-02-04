
import sqlite3
import time
import json
import random
from radar_weibo import get_weibo_hot_list
from radar_articles import save_article
from ai_engine import generate_news_summary, generate_outline, generate_article_from_outline

DB_FILE = "radar_data.db"

def init_agent_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS agents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  angle TEXT,
                  prompt TEXT,
                  status INTEGER DEFAULT 1,
                  created_at REAL,
                  last_run_at REAL,
                  style TEXT,
                  word_count INTEGER DEFAULT 1500,
                  source TEXT,
                  keywords TEXT)''')
    
    # Auto-migration
    try: c.execute("ALTER TABLE agents ADD COLUMN style TEXT")
    except: pass
    try: c.execute("ALTER TABLE agents ADD COLUMN word_count INTEGER DEFAULT 1500")
    except: pass
    try: c.execute("ALTER TABLE agents ADD COLUMN source TEXT")
    except: pass
    try: c.execute("ALTER TABLE agents ADD COLUMN keywords TEXT")
    except: pass

    conn.commit()
    conn.close()

init_agent_db()

def create_agent(name, angle, prompt, style, word_count, source, keywords):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = time.time()
    c.execute("INSERT INTO agents (name, angle, prompt, style, word_count, source, keywords, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
              (name, angle, prompt, style, word_count, source, keywords, now))
    aid = c.lastrowid
    conn.commit()
    conn.close()
    return aid

def get_agents():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, angle, prompt, status, last_run_at, style, word_count, source, keywords FROM agents ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "name": r[1],
            "angle": r[2],
            "prompt": r[3],
            "status": r[4],
            "last_run_at": r[5],
            "style": r[6],
            "word_count": r[7],
            "source": r[8],
            "keywords": r[9]
        }
        for r in rows
    ]

def delete_agent(agent_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM agents WHERE id=?", (agent_id,))
    conn.commit()
    conn.close()

def run_agent_task(agent_id, user_id):
    """
    Executes the agent task:
    1. Fetches hot news (filtered by source).
    2. Filters items by keywords.
    3. Selects a candidate.
    4. Rewrites using AI with Agent's prompt/angle/style/word_count.
    5. Saves to articles.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, angle, prompt, style, word_count, source, keywords FROM agents WHERE id=?", (agent_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {"error": "Agent not found"}
    
    name, angle, prompt, style, word_count, source, keywords_str = row
    
def update_agent(agent_id, name, angle, prompt, style, word_count, source, keywords):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''UPDATE agents 
                 SET name=?, angle=?, prompt=?, style=?, word_count=?, source=?, keywords=?
                 WHERE id=?''',
              (name, angle, prompt, style, word_count, source, keywords, agent_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_google(keywords, time_range='d'):
    """
    Search Google for keywords within time range (default 'd' = 24h).
    Returns list of dicts: [{'title': ..., 'summary': ..., 'href': ...}]
    Note: Scraping Google SERP is fragile.
    """
    try:
        print(f"Searching Google for: {keywords}")
        query = urllib.parse.quote(keywords)
        # qdr:d = past 24 hours
        url = f"https://www.google.com/search?q={query}&tbs=qdr:{time_range}&hl=zh-CN"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"Google search failed with status: {resp.status_code}")
            return []
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = []
        
        # Google HTML structure changes often. Common pattern for results: div.g
        # We try a few selectors
        
        # Pattern 1: Standard div.g
        results = soup.select('div.g')
        
        if not results:
             # Fallback: try finding h3 and going up
             # This is a bit loose but works for simple pages
             results = [h3.find_parent('div') for h3 in soup.select('h3')]

        seen_hrefs = set()
        
        for res in results:
            if not res: continue
            
            # Title
            h3 = res.select_one('h3')
            if not h3: continue
            title = h3.get_text()
            
            # Link
            a = res.select_one('a')
            if not a: 
                a = h3.find_parent('a')
            if not a: continue
            
            href = a.get('href')
            if not href or href.startswith('/search'): continue
            
            if href in seen_hrefs: continue
            seen_hrefs.add(href)
            
            # Snippet
            # Usually in a div or span with checking for text
            # We take all text in the result div as summary if we can't find specific class
            summary = res.get_text()
            # Clean up title from summary
            summary = summary.replace(title, '').strip()
            if len(summary) > 300: summary = summary[:300] + "..."
            
            items.append({
                "title": title,
                "summary": summary,
                "href": href
            })
            
            if len(items) >= 10: break
            
        return items
    except Exception as e:
        print(f"Error searching Google: {e}")
        return []

def run_agent_task(agent_id, user_id):
    """
    Executes the agent task:
    1. Search Google via Keywords (Past 24h).
    2. Selects a candidate (first one or random).
    3. Rewrites using AI with Agent's prompt/angle/style/word_count.
    4. Saves to articles.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, angle, prompt, style, word_count, source, keywords FROM agents WHERE id=?", (agent_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {"error": "Agent not found"}
    
    name, angle, prompt, style, word_count, source, keywords_str = row
    
    # 1. Fetch News
    hot_data = []
    
    # Use Keywords for Search
    if keywords_str and keywords_str.strip():
        # Google Search
        hot_data = search_google(keywords_str, time_range='d')
    
    # Fallback to general hotlist if search failed or no keywords
    if not hot_data:
        print("Google search returned no results or no keywords, checking general hotlist...")
        # Fallback to Comprehensive
        fallback_data = get_weibo_hot_list("综合") or {}
        for k, v in fallback_data.items():
            hot_data.extend(v)

    if not hot_data:
        return {"error": "No news data fetched (Search & Fallback failed)"}
        
    # 2. Pick a fresh topic
    # Prefer top result from Search
    target_item = hot_data[0] if hot_data else None
    
    # Randomize slightly if using fallback to avoid same item
    if not keywords_str and hot_data:
        target_item = random.choice(hot_data[:5])
        
    if not target_item:
         return {"error": "No target item found"}

    topic_title = target_item.get('title')
    topic_summary = target_item.get('summary', topic_title)
    topic_href = target_item.get('href', '')
    
    print(f"Agent {name} processing: {topic_title} (Source: {topic_href})")
    
    # Step A: Generate Outline
    structure = generate_outline(topic_title, angle)
    
    # Step B: Generate Full Article
    # Inject Agent's Config into Context
    style_instruction = f"文章风格要求：{style}" if style else ""
    wc_instruction = f"字数要求：{word_count}字左右" if word_count else ""
    src_instruction = f"原文链接：{topic_href}" if topic_href else ""
    
    context_payload = f"""
    【Agent指令】: {prompt}
    {style_instruction}
    {wc_instruction}
    {src_instruction}
    【原始资讯及其摘要】: {topic_summary}
    """
    
    full_text = generate_article_from_outline(topic_title, structure, context=context_payload)
    
    # 3. Save
    res = save_article(
        user_id=user_id,
        title=f"【Agent】{topic_title}",
        content=full_text,
        summary=f"由Agent[{name}]抓取全网最新资讯生成。\n搜索词：{keywords_str}\n信源：{topic_href}\n切入点：{angle}",
        topic=topic_title,
        status="draft"
    )
    
    # Update last run
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE agents SET last_run_at=? WHERE id=?", (time.time(), agent_id))
    conn.commit()
    conn.close()
    
    return {"status": "success", "article": res, "topic": topic_title}
