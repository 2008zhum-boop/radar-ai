import requests
from bs4 import BeautifulSoup
import time
import random
import json
import sqlite3
import os

# === 数据库配置 ===
DB_FILE = "radar_data.db"
CACHE_EXPIRE_SECONDS = 3600  # 1 小时缓存

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hot_cache
                 (source text PRIMARY KEY, data text, updated_at real)''')
    conn.commit()
    conn.close()

init_db()

# === 数据库读写 ===
def get_db_cache(source):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT data, updated_at FROM hot_cache WHERE source=?", (source,))
        row = c.fetchone()
        conn.close()

        if row:
            data_json, updated_at = row
            if time.time() - updated_at < CACHE_EXPIRE_SECONDS:
                print(f"[{source}] ⚡️ 命中数据库缓存")
                return json.loads(data_json)
            else:
                print(f"[{source}] ⚠️ 缓存已过期，重新抓取...")
        return None
    except Exception as e:
        print(f"读缓存出错: {e}")
        return None

def set_db_cache(source, data):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("REPLACE INTO hot_cache (source, data, updated_at) VALUES (?, ?, ?)", 
                  (source, json.dumps(data, ensure_ascii=False), time.time()))
        conn.commit()
        conn.close()
        print(f"[{source}] ✅ 数据已存入数据库")
    except Exception as e:
        print(f"写缓存出错: {e}")

# === 伪装头 ===
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# === 1. 微博热搜 ===
def fetch_weibo():
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        data = resp.json()
        items = []
        realtime_list = data.get('data', {}).get('realtime', [])
        for i, item in enumerate(realtime_list[:20]):
            if item.get('is_ad'): continue
            title = item.get('word_scheme', item.get('word'))
            label = item.get('icon_desc', '')
            items.append({
                "rank": i + 1,
                "title": title,
                "heat": item.get('num', 0),
                "label": label[:1],
                "summary": f"微博实时热度：{item.get('num', 0)}",
                "source": "微博热搜"
            })
        return items
    except Exception as e:
        print(f"微博抓取失败: {e}")
        return []

# === 2. 头条号 (原36氪逻辑，仅改名) ===
def fetch_toutiao():
    try:
        # 这里依然去爬 36Kr 的快讯作为数据源，但我们给它贴上“头条号”的标签
        url = "https://36kr.com/newsflashes"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(resp.text, 'lxml')
        items = []
        news_list = soup.find_all('div', class_='newsflash-item')
        for i, news in enumerate(news_list[:15]):
            title_tag = news.find('a', class_='item-title')
            desc_tag = news.find('div', class_='item-desc')
            if title_tag:
                items.append({
                    "rank": i + 1,
                    "title": title_tag.get_text().strip(),
                    "heat": random.randint(50000, 200000),
                    "label": "热", # 改个标签风格
                    "summary": desc_tag.get_text().strip() if desc_tag else "",
                    "source": "头条号"  # <--- 这里改了名字
                })
        return items
    except Exception as e:
        print(f"头条号抓取失败: {e}")
        return []

# === 3. 百度风云榜 ===
def fetch_baidu():
    try:
        url = "https://top.baidu.com/board?tab=realtime"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(resp.text, 'lxml')
        items = []
        rows = soup.find_all('div', class_='category-wrap_iQLoo')
        for i, row in enumerate(rows[:15]):
            title_div = row.find('div', class_='c-single-text-ellipsis')
            heat_div = row.find('div', class_='hot-index_1Bl1a')
            desc_div = row.find('div', class_='hot-desc_1m_jR')
            if title_div:
                try: heat_val = int(heat_div.get_text().strip())
                except: heat_val = 0
                items.append({
                    "rank": i + 1,
                    "title": title_div.get_text().strip(),
                    "heat": heat_val,
                    "label": "热" if i < 3 else "",
                    "summary": desc_div.get_text().strip() if desc_div else "百度实时搜索热点",
                    "source": "百度风云榜"
                })
        return items
    except Exception as e:
        print(f"百度抓取失败: {e}")
        return []

# === 4. 钛媒体 ===
def fetch_tmt():
    try:
        url = "https://www.tmtpost.com/"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(resp.text, 'lxml')
        items = []
        posts = soup.find_all('h3', class_='post_title')
        for i, post in enumerate(posts[:15]):
            link = post.find('a')
            if link:
                items.append({
                    "rank": i + 1,
                    "title": link.get_text().strip(),
                    "heat": random.randint(10000, 80000),
                    "label": "TMT",
                    "summary": "钛媒体前沿科技报道",
                    "source": "钛媒体App"
                })
        return items
    except Exception as e:
        print(f"钛媒体抓取失败: {e}")
        return []

# === 通用获取逻辑 ===
def get_data_with_cache(source_name, fetch_func):
    cached = get_db_cache(source_name)
    if cached: return cached
    
    print(f"[{source_name}] 🌐 正在联网抓取...")
    data = fetch_func()
    
    if data:
        set_db_cache(source_name, data)
        return data
    else:
        return []

# === 主入口 ===
def get_weibo_hot_list(category="综合"):
    result = {}
    tasks = []
    
    # 将 "36氪" 替换为 "头条号"
    if category in ["综合", "新消费", "大健康", "出海"]:
        tasks.append(("微博热搜", fetch_weibo))
    if category in ["综合", "科技", "创投", "财经"]:
        tasks.append(("头条号", fetch_toutiao)) # <--- 这里改了
    if category in ["综合"]:
        tasks.append(("百度风云榜", fetch_baidu))
    
    tasks.append(("钛媒体App", fetch_tmt))

    for source, func in tasks:
        data = get_data_with_cache(source, func)
        if data:
            result[source] = data

    return result