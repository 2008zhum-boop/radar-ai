import requests
from bs4 import BeautifulSoup
import time
import random
import json
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

# 引用 AI
from radar_ai import generate_news_summary

DB_FILE = "radar_data.db"
CACHE_EXPIRE_SECONDS = 600

# ✅ 焊死代理配置 (与 radar_ai 保持一致)
PROXY_URL = "socks5h://127.0.0.1:9091"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def init_db():
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hot_cache (source text PRIMARY KEY, data text, updated_at real)''')
    conn.commit()
    conn.close()

init_db()

# === 核心算法：热度计算 ===
def calculate_heat(source_name, score, rank):
    base = {"Google新闻": 800000, "36氪": 500000, "GitHub": 200000}.get(source_name, 300000)
    rank_drop = max(0.4, 1 - (rank * 0.03))
    score_boost = (score / 60) ** 2 
    return int(base * rank_drop * score_boost * random.uniform(0.9, 1.1))

# === 智能兜底：基础情感 ===
def calculate_fallback_sentiment(title):
    pos_keywords = ["突破", "大涨", "新高", "发布", "成功", "增长", "获批", "首发", "利好"]
    neg_keywords = ["裁员", "暴跌", "亏损", "调查", "罚款", "警示", "下跌", "失败", "漏洞"]
    score = 0
    for k in pos_keywords:
        if k in title: score += 1
    for k in neg_keywords:
        if k in title: score -= 1
        
    if score > 0: return {"positive": 80, "neutral": 15, "negative": 5}
    elif score < 0: return {"positive": 5, "neutral": 15, "negative": 80}
    else: return {"positive": 10, "neutral": 80, "negative": 10}

# === 智能兜底：细粒度情绪 ===
def calculate_fallback_emotions(title):
    emotions = { "anxiety": 5, "anger": 5, "sadness": 5, "excitement": 5, "sarcasm": 5 }
    rules = [
        (["裁员", "制裁", "担忧", "风险", "警告", "延期", "暴雷"], "anxiety", 60),
        (["被查", "罚款", "侵权", "丑闻", "造假", "抗议", "做空"], "anger", 70),
        (["逝世", "暴跌", "亏损", "失败", "腰斩", "惨淡"], "sadness", 60),
        (["首发", "突破", "大涨", "新高", "获批", "重磅", "遥遥领先"], "excitement", 80),
        (["反转", "吃瓜", "打脸", "离谱", "震惊", "辟谣"], "sarcasm", 50)
    ]
    for keywords, emo_key, score in rules:
        for k in keywords:
            if k in title:
                emotions[emo_key] = max(emotions[emo_key], score + random.randint(-10, 10))
    return emotions

# === 抓取工具 ===
def fetch_page_content(url):
    if not url or "github" in url or "google" in url: return ""
    try:
        # 正文抓取根据 URL 决定是否走代理
        use_proxy = "36kr.com" not in url 
        proxies = {"http": PROXY_URL, "https": PROXY_URL} if use_proxy else None
        
        resp = requests.get(url, headers=HEADERS, timeout=5, proxies=proxies)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'lxml')
            return "\n".join([p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 20])
    except: pass
    return ""

def enrich_items(items, source_name):
    print(f"[{source_name}] 抓取成功 {len(items)} 条，正在进行 AI 分析...")
    
    def process(item):
        item['source'] = source_name 
        
        try:
            content = fetch_page_content(item.get('url'))
            ai_data = generate_news_summary(item['title'], content)
        except Exception as e:
            # print(f"AI Error: {e}")
            ai_data = {} 

        fact = ai_data.get('fact') or item['title'] 
        score = ai_data.get('score', 60)
        category = ai_data.get('category', '综合')
        
        sentiment = ai_data.get('sentiment')
        if not isinstance(sentiment, dict):
             sentiment = calculate_fallback_sentiment(item['title'])
             
        emotions = ai_data.get('emotions')
        if not isinstance(emotions, dict):
            emotions = calculate_fallback_emotions(item['title'])

        item.update({
            'heat': calculate_heat(source_name, score, item.get('rank', 10)),
            'score': score,
            'trend': ai_data.get('trend', '平稳'),
            'reason': ai_data.get('reason', ''),
            'category': category,
            'summary': ai_data,
            'fact': fact,
            'tags': ai_data.get('tags', []),
            'sentiment': sentiment,
            'emotions': emotions
        })
        return item

    with ThreadPoolExecutor(max_workers=5) as executor:
        result = list(executor.map(process, items))
    
    return result

def cache_and_save(source_name, items):
    if not items: 
        print(f"⚠️ [{source_name}] 抓取结果为空，跳过缓存。")
        return []
    try:
        conn = sqlite3.connect(DB_FILE, timeout=30.0)
        c = conn.cursor()
        c.execute("REPLACE INTO hot_cache (source, data, updated_at) VALUES (?, ?, ?)", 
                  (source_name, json.dumps(items, ensure_ascii=False), time.time()))
        conn.commit()
        conn.close()
    except Exception as e: print(f"Cache Error: {e}")
    return items

def get_from_cache(source_name):
    try:
        conn = sqlite3.connect(DB_FILE, timeout=30.0)
        c = conn.cursor()
        c.execute("SELECT data, updated_at FROM hot_cache WHERE source=?", (source_name,))
        row = c.fetchone()
        conn.close()
        if row and (time.time() - row[1] < CACHE_EXPIRE_SECONDS):
            return json.loads(row[0])
    except: pass
    return None

# === 信源抓取 ===

def fetch_google():
    # ✅ 强制走代理
    proxies = {"http": PROXY_URL, "https": PROXY_URL}
    
    queries = ["AI大模型 DeepSeek OpenAI", "科技巨头 财报 裁员", "新能源 华为 小米"]
    items = []
    seen = set()
    print("🚀 正在抓取: Google新闻 (使用代理)...")
    
    try:
        for q in queries:
            url = f"https://news.google.com/rss/search?q={quote(q)}+when:24h&hl=zh-CN&gl=CN&ceid=CN:zh-CN"
            resp = requests.get(url, headers=HEADERS, timeout=10, proxies=proxies)
            if resp.status_code != 200:
                print(f"❌ Google 请求失败: {resp.status_code}")
                continue
                
            soup = BeautifulSoup(resp.content, 'xml')
            for entry in soup.find_all('item')[:5]:
                raw_title = entry.title.text
                if raw_title in seen: continue
                seen.add(raw_title)
                clean_title = raw_title
                if " - " in clean_title: clean_title = clean_title.rsplit(" - ", 1)[0].strip()
                items.append({"rank": len(items)+1, "title": clean_title, "url": entry.link.text, "source": "Google新闻"})
    except Exception as e:
        print(f"❌ Google 抓取异常: {e}")
        
    return enrich_items(items, "Google新闻")

def fetch_36kr():
    # ✅ 强制不走代理 (国内站)
    proxies = None 
    
    items = []
    print("🚀 正在抓取: 36氪 (国内直连)...")
    
    try:
        resp = requests.get("https://36kr.com/newsflashes", headers=HEADERS, timeout=5, proxies=proxies)
        if resp.status_code != 200:
            print(f"❌ 36Kr 请求失败: {resp.status_code}")
        else:
            soup = BeautifulSoup(resp.text, 'lxml')
            for i, t in enumerate(soup.find_all('a', class_='item-title')[:15]): 
                items.append({"rank": i+1, "title": t.get_text().strip(), "url": "https://36kr.com"+t.get('href'), "source": "36氪"})
    except Exception as e:
        print(f"❌ 36Kr 抓取异常: {e}")
        
    return enrich_items(items, "36氪")

def fetch_github():
    # ✅ 强制走代理
    proxies = {"http": PROXY_URL, "https": PROXY_URL}
    
    items = []
    print("🚀 正在抓取: GitHub (使用代理)...")
    
    try:
        url = "https://api.github.com/search/repositories?q=topic:ai+created:>2025-01-01&sort=stars&order=desc"
        resp = requests.get(url, headers=HEADERS, timeout=10, proxies=proxies)
        if resp.status_code != 200:
             print(f"❌ GitHub 请求失败: {resp.status_code}")
        else:
            data = resp.json()
            for i, r in enumerate(data.get('items', [])[:8]):
                items.append({"rank": i+1, "title": f"GitHub: {r['name']}", "url": r['html_url'], "source": "GitHub"})
    except Exception as e:
        print(f"❌ GitHub 抓取异常: {e}")
        
    return enrich_items(items, "GitHub")

def get_weibo_hot_list(category="综合"):
    all_data = {}
    # 定义源
    sources = [("Google新闻", fetch_google), ("36氪", fetch_36kr), ("GitHub", fetch_github)]
    
    for name, func in sources:
        # 先读缓存
        data = get_from_cache(name)
        
        # 缓存没数据，进行抓取
        if not data:
            data = cache_and_save(name, func())
        
        # 过滤
        if data:
            if category == "综合": all_data[name] = data
            else:
                filtered = [x for x in data if x.get('category') == category]
                if filtered: all_data[name] = filtered
                
    return all_data

def search_news_content(keyword): return [] 
def sync_hot_to_mentions(items, source): pass