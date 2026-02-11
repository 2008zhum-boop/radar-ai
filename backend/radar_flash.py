"""
快报监控模块：抓取、生成、发布钛媒体快讯 (Refactored)
"""
import os
import sqlite3
import time
import json
import hashlib
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import urllib.parse
from urllib.parse import urlparse
from datetime import datetime

# ✅ 修改点：移除 ai_engine，统一使用 radar_ai 的智能接口
from radar_ai import call_openrouter

DB_FILE = "radar_data.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.cls.cn/telegraph"
}

GOOGLE_NEWS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
    "Referer": "https://www.google.com/"
}

GOOGLE_KEYWORDS = [
    # Companies
    "OpenAI", "NVIDIA", "Google", "Alphabet", "Anthropic", "xAI", "Microsoft", "Amazon", "AWS", "Apple", "Meta",
    "Tesla", "DeepMind", "C3.ai", "Scale AI", "Character.AI", "Waymo", "Figure AI", "Neuralink",
    "Thinking Machines Lab", "Safe Superintelligence (SSI)", "Black Forest Labs",
    # Key People
    "Sam Altman", "Jensen Huang", "Elon Musk", "Ilya Sutskever", "Demis Hassabis", "Dario Amodei",
    "Larry Page", "Sergey Brin", "Mira Murati", "John Schulman", "Lisa Su", "Alexander Wang", "Jerry Peng",
    # Products & Models
    "GPT Series", "GPT-4o", "GPT-5", "Claude Series", "Claude 3.5", "Claude 4", "Gemini Series", "Gemini 2.5",
    "Gemini Ultra", "Grok Series", "Grok 4", "Llama Series", "Llama 3", "Llama 4", "Phi Series", "Phi-4",
    "Titan Series", "ChatGPT", "Copilot", "FLUX", "Veo 2", "Apple Intelligence", "Nano Banana",
    "Dojo Supercomputer", "Optimus Robot",
    # Technologies & Brands
    "AI (Artificial Intelligence)", "LLM (Large Language Model)", "Multimodal AI", "Constitutional AI", "CUDA",
    "TPU (Tensor Processing Unit)", "Blackwell Chip", "AI Agent", "Alignment", "Foundation Models",
    "SLM (Small Language Model)", "BCI (Brain-Computer Interface)", "Autonomous Driving",
    "Generative AI", "Enterprise AI"
]

GOOGLE_TIME_WINDOW_SECONDS = 6 * 3600

# ==========================================
# 数据库初始化
# ==========================================

def init_flash_db():
    """初始化快报数据库表 (支持已存在的Schema升级)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='raw_flashes'")
    table_exists = c.fetchone()
    
    if not table_exists:
        # Create new schema
        c.execute('''CREATE TABLE raw_flashes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,  -- 'cls' etc
            source_value TEXT,
            title TEXT,
            content TEXT,
            url TEXT,
            publish_time REAL,
            fetch_time REAL,
            content_hash TEXT UNIQUE,
            status TEXT DEFAULT 'draft',  -- draft, published, discarded
            rewrite_title TEXT,
            rewrite_content TEXT,
            rewrite_error TEXT,
            important INTEGER DEFAULT 0,
            created_at REAL
        )''')
    else:
        # Attempt to add new columns if they don't exist
        try:
            c.execute("ALTER TABLE raw_flashes ADD COLUMN rewrite_title TEXT")
        except: pass
        try:
            c.execute("ALTER TABLE raw_flashes ADD COLUMN rewrite_content TEXT")
        except: pass
        try:
            c.execute("ALTER TABLE raw_flashes ADD COLUMN rewrite_error TEXT")
        except: pass
        try:
            c.execute("ALTER TABLE raw_flashes ADD COLUMN important INTEGER DEFAULT 0")
        except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS flash_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        config_type TEXT NOT NULL,
        config_value TEXT NOT NULL UNIQUE,
        is_active INTEGER DEFAULT 1,
        created_at REAL
    )''')
    
    conn.commit()
    conn.close()

# ==========================================
# 抓取逻辑 (CLS Only)
# ==========================================

def scrape_cls_telegraph(limit=20):
    """Scrape CLS Telegraph using SSR JSON method"""
    url = "https://www.cls.cn/telegraph"
    print(f"[*] Fetching CLS Telegraph from {url}...")
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"[!] CLS Request Failed: {resp.status_code}")
            return []
            
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')
        
        items = []
        raw_list = []

        # 1) 优先从 __NEXT_DATA__ 中读取
        if script_tag and script_tag.string:
            try:
                data = json.loads(script_tag.string)
                raw_list = data.get('props', {}).get('initialState', {}).get('telegraph', {}).get('telegraphList', [])
            except json.JSONDecodeError as e:
                print(f"[!] JSON Decode Error: {e}")
        else:
            print("[!] __NEXT_DATA__ not found on CLS page, trying regex fallback.")

        # 2) 兜底：正则提取 telegraphList
        if not raw_list:
            try:
                m = re.search(r'"telegraphList":(\[.*?\])', html, re.S)
                if m:
                    raw_list = json.loads(m.group(1))
            except Exception as e:
                print(f"[!] Regex fallback failed: {e}")

        for item in raw_list[:limit]:
            title = item.get('title', '')
            content = item.get('content', '')
            if not title and content:
                title = content[:30].replace('\n', ' ') + '...'
            elif not title and not content:
                continue 
            
            ctime = item.get('ctime', time.time())
            important = 1 if (
                item.get('is_important') or item.get('important') or item.get('isImportant') or item.get('important_flag')
            ) else 0
            
            unique_str = f"{title}-{ctime}"
            content_hash = hashlib.md5(unique_str.encode()).hexdigest()
            
            items.append({
                "source_type": "cls",
                "title": title,
                "content": content,
                "url": f"https://www.cls.cn/detail/{item.get('id', '')}",
                "publish_time": ctime,
                "content_hash": content_hash,
                "important": important
            })
        
        print(f"[*] Scraped {len(items)} items from CLS.")
        return items
        
    except Exception as e:
        print(f"[!] Scrape Error: {e}")
        return []

def _parse_relative_time(text: str) -> Optional[float]:
    if not text:
        return None
    text = text.strip().lower()
    now = time.time()
    m = re.search(r"(\d+)\s*(minute|hour|day|week)s?\s*ago", text)
    if m:
        num = int(m.group(1))
        unit = m.group(2)
        if unit == "minute":
            return now - num * 60
        if unit == "hour":
            return now - num * 3600
        if unit == "day":
            return now - num * 86400
        if unit == "week":
            return now - num * 7 * 86400
    m = re.search(r"(\d+)\s*(分钟|小时|天)前", text)
    if m:
        num = int(m.group(1))
        unit = m.group(2)
        if unit == "分钟":
            return now - num * 60
        if unit == "小时":
            return now - num * 3600
        if unit == "天":
            return now - num * 86400
    return None

def _extract_google_news_items(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for card in soup.select("div.dbsr"):
        link_tag = card.find("a", href=True)
        title_tag = card.find("h3")
        snippet_tag = card.select_one(".GI74Re, .Y3v8qd, .aCOpRe")
        meta_tag = card.select_one(".WG9SHc, .CEMjEf")
        if not link_tag or not title_tag:
            continue
        url = link_tag.get("href", "")
        title = title_tag.get_text(strip=True)
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        meta_text = meta_tag.get_text(" ", strip=True) if meta_tag else ""
        # Try to find relative time in meta
        publish_time = _parse_relative_time(meta_text) or time.time()
        if not title and not snippet:
            continue
        items.append({
            "title": title,
            "content": snippet,
            "url": url,
            "publish_time": publish_time
        })
    return items

def _is_english_text(text: str) -> bool:
    if not text:
        return False
    letters = len(re.findall(r"[A-Za-z]", text))
    total = len(re.sub(r"\s+", "", text))
    if total == 0:
        return False
    return (letters / total) >= 0.5

def _translate_to_zh(text: str, provider: str = "deepseek") -> str:
    if not text:
        return ""
    prompt = f"""请将以下英文内容翻译为简体中文，保持信息完整、语气客观专业，不要添加任何额外内容：
{text}
"""
    try:
        # ✅ 修改点：直接调用统一接口
        translated = call_openrouter(prompt) or ""
        return translated.strip()
    except Exception:
        return ""

def scrape_google_news(keywords: List[str], limit=20, per_keyword=3):
    """Search Google News for keywords (last 6 hours)"""
    results = []
    seen = set()
    now = time.time()
    for kw in keywords:
        if len(results) >= limit:
            break
        query = urllib.parse.quote(kw)
        url = f"https://www.google.com/search?q={query}&tbm=nws&hl=en&num=10&tbs=qdr:h6"
        try:
            resp = requests.get(url, headers=GOOGLE_NEWS_HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            items = _extract_google_news_items(resp.text)
            count = 0
            for item in items:
                if len(results) >= limit or count >= per_keyword:
                    break
                title = item.get("title", "")
                content = (item.get("content") or "")[:500]
                url = item.get("url", "")
                pub_time = item.get("publish_time")
                if not pub_time:
                    continue
                if (now - float(pub_time)) > GOOGLE_TIME_WINDOW_SECONDS:
                    continue
                key = f"{title}-{url}"
                if key in seen or not title:
                    continue
                seen.add(key)
                results.append({
                    "source_type": "google",
                    "source_value": kw,
                    "title": title,
                    "content": content,
                    "url": url,
                    "publish_time": float(pub_time),
                    "content_hash": hashlib.md5(key.encode()).hexdigest(),
                    "important": 0
                })
                count += 1
        except Exception as e:
            print(f"[!] Google search failed for {kw}: {e}")
            continue
    return results

def save_raw_flashes(items):
    """Save scraped items to DB and trigger AI if new"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    new_count = 0
    new_ids = []
    for item in items:
        try:
            c.execute("SELECT id FROM raw_flashes WHERE content_hash=?", (item['content_hash'],))
            exist = c.fetchone()
            
            if not exist:
                source_value = item.get("source_value") or ("telegraph" if item['source_type'] == "cls" else "")
                c.execute('''INSERT INTO raw_flashes 
                    (source_type, source_value, title, content, url, publish_time, fetch_time, content_hash, status, important, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)''',
                    (item['source_type'], source_value, item['title'], item['content'], item['url'], 
                     float(item['publish_time']), time.time(), item['content_hash'], int(item.get('important', 0)), time.time()))
                
                new_id = c.lastrowid
                new_count += 1
                new_ids.append((new_id, item['title'], item['content'], float(item['publish_time'])))
        except Exception as e:
            print(f"[!] Insert Error: {e}")
            
    conn.commit()
    conn.close()
    
    # Trigger AI rewrite after DB commit to avoid lock
    for rid, title, content, ptime in new_ids:
        try:
            generate_tmt_flash(rid, title, content, ptime)
        except Exception as e:
            print(f"AI Trigger Failed: {e}")
    return new_count

def fetch_all_flashes(source: str = "cls"):
    items = []
    if source in ("cls", "all"):
        items.extend(scrape_cls_telegraph(limit=20))
    if source in ("google", "all"):
        items.extend(scrape_google_news(GOOGLE_KEYWORDS, limit=20))
    count = save_raw_flashes(items)
    print(f"[*] Processed {len(items)} items, {count} new.")
    # Backfill rewrite for items that are still empty
    backfill_rewrite(limit=10)
    return items

def backfill_rewrite(limit=10):
    """对未生成改写内容的草稿进行补写"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, title, content, publish_time FROM raw_flashes WHERE (rewrite_content IS NULL OR rewrite_content='') AND status='draft' ORDER BY publish_time DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    for r in rows:
        try:
            generate_tmt_flash(r[0], r[1], r[2], r[3] or time.time())
        except Exception as e:
            print(f"Backfill rewrite failed: {e}")

# ==========================================
# AI 改写逻辑
# ==========================================

def generate_tmt_flash(flash_id, title, content, pub_time):
    """Call AI to rewrite content in TMT style"""
    print(f"[*] AI Rewriting Flash ID {flash_id}...")

    # 读取来源 URL 用于尾注
    url = ""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT url FROM raw_flashes WHERE id=?", (flash_id,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            url = row[0]
    except Exception:
        url = ""
    
    time_str = time.strftime("%m月%d日", time.localtime(float(pub_time)))
    
    # provider 参数现在不再需要了，直接由 radar_ai 内部路由
    
    # Translate to Chinese if English content
    if _is_english_text(title) or _is_english_text(content):
        # 简化调用，不再传 provider
        translated_title = _translate_to_zh(title) if title else ""
        translated_content = _translate_to_zh(content) if content else ""
        if translated_title:
            title = translated_title
        if translated_content:
            content = translated_content

    prompt = f"""
请将以下财经快讯改写为钛媒体（TMTPost）风格的快报。
任务要求：
1. 必须以“钛媒体App {time_str}消息，”（注意是中文逗号）作为开头。
2. 语言风格简练、客观、专业。
3. 如果原文中有“财联社”或“电报”字眼，请去除或替换为客观描述。
4. 返回 JSON 格式，包含 title 与 content：
   {{ "title": "改写后的标题", "content": "改写后的正文" }}

原文标题：{title}
原文内容：
{content}
"""
    rewrite_error = ""
    try:
        # ✅ 修改点：直接调用统一接口
        rewritten = call_openrouter(prompt)
        
        rewrite_title = ""
        rewrite_body = ""

        # 尝试解析 JSON
        if rewritten:
            try:
                data = json.loads(rewritten)
                rewrite_title = data.get("title", "")
                rewrite_body = data.get("content", "")
            except Exception:
                rewrite_body = rewritten.strip()

        # 兜底内容：规则改写（不显示“财联社”来源）
        if not rewrite_body:
            rewrite_body = rule_rewrite_flash(content, time_str)
            rewrite_error = "AI改写失败或返回为空"

        if not rewrite_title:
            rewrite_title = title

        # 统一前缀 + 来源尾注
        rewrite_body = normalize_tmt_prefix(rewrite_body, time_str)
        prefix = f"钛媒体App {time_str}消息，"
        if not rewrite_body.startswith("钛媒体App"):
            rewrite_body = prefix + rewrite_body.lstrip("，, ")

        # 写入数据库
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            "UPDATE raw_flashes SET rewrite_title = ?, rewrite_content = ?, rewrite_error = ?, status = 'draft' WHERE id = ?",
            (rewrite_title, rewrite_body, rewrite_error, flash_id)
        )
        conn.commit()
        conn.close()
        print(f"✅ AI Rewrite Success for ID {flash_id}")
        
    except Exception as e:
        # 失败时也写入兜底内容，避免前端一直显示“AI生成中”
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            fallback = rule_rewrite_flash(content, time_str)
            c.execute(
                "UPDATE raw_flashes SET rewrite_content = ?, rewrite_error = ?, status = 'draft' WHERE id = ?",
                (fallback, str(e), flash_id)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        print(f"[!] AI Rewrite Failed: {e}")

def rule_rewrite_flash(text: str, time_str: str) -> str:
    """AI失败时的规则改写：替换报头与财联社字样"""
    if not text:
        return f"钛媒体App {time_str}日消息，"
    result = text.strip()
    # 报头替换：财联社XX月XX日电 -> 钛媒体App XX月XX日消息
    result = re.sub(r"财联社\\s*\\d{1,2}月\\d{1,2}日电", f"钛媒体App {time_str}日消息", result)
    # 替换文中“财联社”为“钛媒体”
    result = result.replace("财联社", "钛媒体")
    # 若未含报头，则补齐
    if not result.startswith("钛媒体App"):
        result = f"钛媒体App {time_str}日消息，" + result.lstrip("，, ")
    return result

def normalize_tmt_prefix(text: str, time_str: str) -> str:
    """去重/清洗快报报头，避免重复或'日日'等异常"""
    if not text:
        return ""
    result = text.strip()
    # 修正“日日消息”
    result = re.sub(r"(\d{1,2}月\d{1,2})日日消息", r"\1日消息", result)
    # 移除重复前缀（允许日出现1-2次）
    result = re.sub(r"^(?:钛媒体App\s*\d{1,2}月\d{1,2}日{0,2}消息[，,]?\s*)+", "", result)
    return result

# ==========================================
# API Helpers
# ==========================================

def get_flashes(status_filter='all', limit=50, source_filter='all'):
    """Get flashes list"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    query = "SELECT id, title, content, rewrite_title, rewrite_content, rewrite_error, publish_time, status, source_type, source_value, url, important FROM raw_flashes"
    params = []
    
    where_parts = []
    if status_filter != 'all':
        where_parts.append("status = ?")
        params.append(status_filter)
    if source_filter != 'all':
        where_parts.append("source_type = ?")
        params.append(source_filter)
    if where_parts:
        query += " WHERE " + " AND ".join(where_parts)
        
    query += " ORDER BY publish_time DESC LIMIT ?"
    params.append(limit)
    
    c.execute(query, tuple(params))
    rows = c.fetchall()
    conn.close()
    
    res = []
    for r in rows:
        rw_title = r[3] or ""
        rw = r[4]
        rw_error = r[5] or ""
        if not rw:
            rw = ""            
        
        try:
            ptime = float(r[6])
        except:
            ptime = time.time() # Fallback

        res.append({
            "id": r[0],
            "title": r[1],
            "raw_content": r[2],
            "rewrite_title": rw_title,
            "rewrite_content": rw,
            "publish_time": ptime,
            "time_display": time.strftime("%H:%M", time.localtime(ptime)),
            "date_display": time.strftime("%Y-%m-%d", time.localtime(ptime)),
            "status": r[7],
            "source": r[8],
            "source_value": r[9],
            "url": r[10],
            "is_important": int(r[11] or 0),
            "rewrite_error": rw_error
        })
    return res

def update_flash_status(flash_id, status, content=None, title=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if content is not None or title is not None:
        if title is None:
            c.execute("UPDATE raw_flashes SET status = ?, rewrite_content = ?, rewrite_error = '' WHERE id = ?", (status, content, flash_id))
        else:
            c.execute(
                "UPDATE raw_flashes SET status = ?, rewrite_title = ?, rewrite_content = ?, rewrite_error = '' WHERE id = ?",
                (status, title, content or "", flash_id)
            )
    else:
        c.execute("UPDATE raw_flashes SET status = ? WHERE id = ?", (status, flash_id))
        
    conn.commit()
    conn.close()
    return {"status": "success"}

# Placeholder for backward compatibility
def get_raw_flashes(limit=50): return get_flashes('all', limit)
def get_published_flashes(limit=50): return get_flashes('published', limit)
def add_flash_config(*args): return {}
def delete_flash_config(*args): return {}
def get_flash_configs(): return []