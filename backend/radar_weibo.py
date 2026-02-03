import requests
from bs4 import BeautifulSoup
import time
import random
import json
import sqlite3
import re
from concurrent.futures import ThreadPoolExecutor
from ai_engine import generate_news_summary

# === 数据库配置 ===
DB_FILE = "radar_data.db"
CACHE_EXPIRE_SECONDS = 1800  # 30 分钟缓存

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hot_cache
                 (source text PRIMARY KEY, data text, updated_at real)''')
    conn.commit()
    conn.close()

init_db()

# === 智能分类关键词库 (AI 分类失败时的兜底) ===
CATEGORY_KEYWORDS = {
    "科技": ["AI", "大模型", "芯片", "华为", "苹果", "OpenAI", "Sora", "马斯克", "英伟达", "GPT", "算力", "5G", "SaaS", "手机", "数码", "科学"],
    "财经": ["A股", "股市", "美股", "IPO", "财报", "营收", "利润", "证券", "融资", "上市", "金融", "股票", "彩票", "宏观"],
    "汽车": ["特斯拉", "比亚迪", "小米汽车", "新能源", "理想", "蔚来", "小鹏", "电池", "自动驾驶", "车型", "车展"],
    "大健康": ["医疗", "疫苗", "减肥药", "生物", "基因", "医院", "养老", "医保", "流感", "病毒", "药企"],
    "新消费": ["瑞幸", "奶茶", "星巴克", "直播带货", "电商", "美团", "拼多多", "淘宝", "京东", "品牌", "餐饮", "旅游", "家居", "生活"],
    "创投": ["独角兽", "创业", "天使轮", "投资人", "孵化", "收购", "VC", "PE", "初创", "大公司", "出海"],
    "娱乐": ["明星", "电影", "电视剧", "综艺", "演唱会", "网红", "八卦", "剧透", "票房", "音乐", "情感", "游戏", "文化", "传媒"],
    "社会": ["教育", "就业", "人口", "三农", "农村", "体育", "军事", "地方", "国际"]
}
# 注意：AI 会覆盖此处的简单分类

def auto_classify(text):
    """
    根据文本内容自动打标签 (Fallback)
    """
    text = text.upper()
    matched_tags = set()
    possible_categories = {}

    for cat, keywords in CATEGORY_KEYWORDS.items():
        if cat in text: possible_categories[cat] = possible_categories.get(cat, 0) + 2 # Category name match has high weight
        for kw in keywords:
            if kw.upper() in text:
                matched_tags.add(kw)
                possible_categories[cat] = possible_categories.get(cat, 0) + 1
    
    if possible_categories:
        primary_category = max(possible_categories, key=possible_categories.get)
    else:
        primary_category = "综合"
        
    return primary_category, list(matched_tags)

def fetch_page_content(url):
    """
    抓取落地页正文内容
    """
    if not url or not url.startswith('http'): return ""
    # 过滤掉一些不需要抓取的域 (如搜索页)
    if "weibo.com" in url and "s.weibo.com" in url: return "" # 微博搜索页没内容
    if "baidu.com/s?" in url: return ""

    try:
        resp = requests.get(url, headers=HEADERS, timeout=3)
        if resp.status_code != 200: return ""
        
        soup = BeautifulSoup(resp.text, 'lxml')
        # 简单提取 P 标签文本
        paragraphs = soup.find_all('p')
        text = "\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 10])
        
        return text if len(text) > 50 else ""
    except Exception as e:
        # print(f"Content fetch error: {e}")
        return ""

def enrich_with_ai(items):
    """
    并发处理: 1. 抓取正文 2. 生成 AI 摘要 + 分类
    """
    def process_one(item):
        # 1. 尝试抓取正文
        full_content = fetch_page_content(item.get('url', ''))
        item['full_content'] = full_content
        
        # 2. 准备 AI 上下文
        context = item.get('title', '')
        if 'raw_summary_context' in item:
            context += " " + item['raw_summary_context']
            del item['raw_summary_context'] 
        
        # 如果有正文，补充正文前 800 字给 AI
        if full_content:
            context += "\n正文摘要: " + full_content[:800]
            
        # 3. 调用 AI
        ai_data = generate_news_summary(item['title'], context)
        item['summary'] = ai_data
        
        # 4. 应用 AI 分类和标签 (覆盖 auto_classify 的结果)
        if ai_data.get('category'):
            item['category'] = ai_data['category']
        if ai_data.get('tags'):
            item['tags'] = ai_data['tags']
            
        return item

    # 使用最多 10 个线程并发处理
    with ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(process_one, items))
    
    return items

def generate_ai_summary(title, raw_summary=""):
    # Deprecated: use enrich_with_ai batch process instead
    return generate_news_summary(title, raw_summary)

# === 爬虫部分 ===

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.toutiao.com/",
}

# 1. 微博热搜
def fetch_weibo():
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        data = resp.json()
        items = []
        for i, item in enumerate(data.get('data', {}).get('realtime', [])[:30]):
            if item.get('is_ad'): continue
            title = item.get('word_scheme', item.get('word'))
            link = f"https://s.weibo.com/weibo?q={title}"
            category, tags = auto_classify(title)
            
            items.append({
                "rank": i + 1,
                "title": title,
                "heat": item.get('num', 0),
                "label": item.get('label_name', '热')[:1],
                "category": category,
                "tags": tags,
                "url": link,
                "raw_summary_context": f"微博话题热度飙升至 {item.get('num', 0)}。",
                "source": "微博热搜"
            })
        return enrich_with_ai(items)
    except Exception as e:
        print(f"Weibo Error: {e}")
        return []

# 2. 头条号
def fetch_toutiao():
    try:
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        data = resp.json()
        items = []
        for i, news in enumerate(data.get('data', [])[:30]):
            title = news.get('Title', '')
            link = news.get('Url', '')
            if not link: link = f"https://so.toutiao.com/search?dvpf=pc&keyword={title}"
            category, tags = auto_classify(title)
            
            items.append({
                "rank": i + 1,
                "title": title,
                "heat": int(news.get('HotValue', 0)),
                "label": "热",
                "category": category,
                "tags": tags,
                "url": link,
                "raw_summary_context": news.get('LabelDesc', ''),
                "source": "头条号"
            })
        return enrich_with_ai(items)
    except Exception as e:
        print(f"Toutiao Error: {e}")
        return []

# 3. 微信 (虎嗅/36Kr Proxy)
def fetch_wechat_proxy():
    try:
        url = "https://www.huxiu.com/article/"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(resp.text, 'lxml')
        items = []
        articles = soup.find_all('div', class_='article-item-wrap')
        for i, art in enumerate(articles[:15]):
            a_tag = art.find('a', class_='m-article-title')
            desc_tag = art.find('div', class_='article-desc')
            
            if a_tag:
                title = a_tag.get_text().strip()
                link = "https://www.huxiu.com" + a_tag.get('href')
                raw_summary = desc_tag.get_text().strip() if desc_tag else ""
                category, tags = auto_classify(title + raw_summary)
                
                items.append({
                    "rank": i + 1,
                    "title": title,
                    "heat": random.randint(10000, 100000),
                    "label": "深",
                    "category": category,
                    "tags": tags,
                    "url": link,
                    "raw_summary_context": raw_summary,
                    "source": "微信"
                })
        if items: return enrich_with_ai(items)
    except Exception as e:
        print(f"Huxiu Error: {e}")

    # Fallback Data (Mock)
    mock_items = [
        {"rank": 1, "title": "微信公开课：视频号GMV增长3倍", "heat": 80000, "label": "热", "category": "科技", "url": "#", "source": "微信", "raw_summary_context": "微信公开课"},
        {"rank": 2, "title": "大模型时代的很多应用其实都是伪需求", "heat": 75000, "label": "深", "category": "科技", "url": "#", "source": "微信", "raw_summary_context": "大模型伪需求"},
        {"rank": 3, "title": "拼多多市值超越阿里给我们的启示", "heat": 70000, "label": "深", "category": "财经", "url": "#", "source": "微信", "raw_summary_context": "拼多多市值"},
    ]
    return enrich_with_ai(mock_items)

# 4. B站热搜
def fetch_bilibili():
    items = []
    try:
        # 尝试使用 B站 Web API
        url = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all"
        # B站防爬严格，添加更多 Header 模拟浏览器
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/v/popular/rank/all",
            "Origin": "https://www.bilibili.com",
            "Accept": "application/json, text/plain, */*"
        }
        resp = requests.get(url, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            for i, video in enumerate(data.get('data', {}).get('list', [])[:20]):
                title = video.get('title', '')
                link = f"https://www.bilibili.com/video/{video.get('bvid')}"
                desc = video.get('desc', '') or title
                heat = video.get('stat', {}).get('view', 0)
                category, tags = auto_classify(title + desc)
                
                items.append({
                    "rank": i + 1,
                    "title": title,
                    "heat": heat,
                    "label": "B站",
                    "category": category,
                    "tags": tags,
                    "url": link,
                    "raw_summary_context": desc[:100],
                    "source": "B站"
                })
    except Exception as e:
        print(f"Bilibili Fetch Error: {e}")

    # 如果抓取失败（为空），使用 Mock 数据兜底，保证前端展示
    if not items:
        print("Using Bilibili Mock Data")
        mock_data = [
            ("【何同学】如果不做UP主，我会做什么？", "科技", 9800000),
            ("2024拜年纪", "娱乐", 8500000),
            ("原神新版本前瞻", "游戏", 7200000),
            ("现在的年轻人为什么不爱走亲戚了", "社会", 6500000),
            ("耗时100天，我做出了核动力手电筒", "科技", 5800000),
            ("猫和老鼠大结局？", "娱乐", 4500000),
            ("小米汽车实测", "汽车", 4200000)
        ]
        for i, (title, cat, heat) in enumerate(mock_data):
            category, tags = auto_classify(title)
            items.append({
                "rank": i + 1,
                "title": title,
                "heat": heat,
                "label": "B站",
                "category": cat or category,
                "tags": tags,
                "url": f"https://search.bilibili.com/all?keyword={title}",
                "raw_summary_context": title,
                "source": "B站"
            })

    return enrich_with_ai(items)

# 5. 抖音热搜 (NEW)
def fetch_douyin():
    items = []
    try:
        # 尝试使用抖音 Web API
        url = "https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/"
        headers = {
             "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
             "Referer": "https://www.douyin.com/"
        }
        resp = requests.get(url, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            # data['word_list'] 包含 { 'word', 'hot_value' }
            word_list = data.get('word_list', [])
            for i, item in enumerate(word_list[:25]):
                title = item.get('word', '')
                heat = item.get('hot_value', 0)
                link = f"https://www.douyin.com/search/{title}"
                category, tags = auto_classify(title)
                
                items.append({
                    "rank": i + 1,
                    "title": title,
                    "heat": heat,
                    "label": "抖",
                    "category": category,
                    "tags": tags,
                    "url": link,
                    "raw_summary_context": f"抖音热榜第{i+1}名",
                    "source": "抖音"
                })
    except Exception as e:
        print(f"Douyin Fetch Error: {e}")

    # Fallback
    if not items:
        print("Using Douyin Mock Data")
        mock_douyin = [
            ("董宇辉新账号粉丝破千万", "新消费", 8800000),
            ("哈尔滨冻梨摆盘", "旅游", 7500000),
            ("科目三火到国外", "娱乐", 6200000),
            ("繁花大结局", "娱乐", 5500000)
        ]
        for i, (title, cat, heat) in enumerate(mock_douyin):
            category, tags = auto_classify(title)
            items.append({
                "rank": i + 1,
                "title": title,
                "heat": heat,
                "label": "抖",
                "category": cat or category,
                "tags": tags,
                "url": f"https://www.douyin.com/search/{title}",
                "raw_summary_context": title,
                "source": "抖音"
            })
            
    return enrich_with_ai(items)

# 5. 百度热搜
def fetch_baidu():
    try:
        url = "https://top.baidu.com/board?tab=realtime"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(resp.text, 'lxml')
        items = []
        
        rows = soup.find_all('div', class_='category-wrap_iQLoo')
        if not rows: rows = soup.find_all('div', class_='content_1YWBm')

        for i, row in enumerate(rows[:20]):
            title_div = row.find('div', class_='c-single-text-ellipsis')
            if not title_div: continue
            
            title = title_div.get_text().strip()
            link = f"https://www.baidu.com/s?wd={title}"
            hot_div = row.find('div', class_='hot-index_1Bl1a')
            heat = int(hot_div.get_text().strip()) if hot_div else 10000
            category, tags = auto_classify(title)
            
            items.append({
                "rank": i + 1,
                "title": title,
                "heat": heat,
                "label": "热",
                "category": category,
                "tags": tags,
                "url": link,
                "raw_summary_context": "百度热搜实时热点",
                "source": "百度"
            })

        if items: return enrich_with_ai(items)
    except Exception as e:
        print(f"Baidu Error: {e}")
        
    # Mock fallback
    mock_items = [
        {"rank": 1, "title": "春节档电影预售开启", "heat": 500000, "label": "热", "category": "综合", "url": "#", "source": "百度", "raw_summary_context": "春节档"},
        {"rank": 2, "title": "南方小土豆勇闯哈尔滨", "heat": 480000, "label": "热", "category": "综合", "url": "#", "source": "百度", "raw_summary_context": "南方小土豆"}
    ]
    return enrich_with_ai(mock_items)

from urllib.parse import quote

# ... (existing imports)

# 6. Google AI News (大模型)
def fetch_google_ai_news():
    items = []
    seen_titles = set()
    
    # KWs
    keywords = [
        "大模型", "AI", "OpenAI", "Gemini", "DeepSeek", "千问", "通义万相", 
        "文心一言", "元宝", "人工智能", "Qwen", "豆包", "Grok", "Clawdbot", 
        "Anthropic", "OpenClaw"
    ]
    # Build Query: (A OR B OR ...) when:12h
    # Note: Google RSS uses 'q=QUERY' and specific params for time, but 'when:12h' inside q usually works better for RSS
    # Or strict param `ceid=CN:zh-CN`
    query_str = " OR ".join(keywords)
    encoded_q = quote(query_str)
    
    rss_url = f"https://news.google.com/rss/search?q={encoded_q}+when:12h&hl=zh-CN&gl=CN&ceid=CN:zh-CN"
    
    try:
        # Use a timeout of 10s as Google might be slow
        resp = requests.get(rss_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'xml') # RSS is XML
            entries = soup.find_all('item')
            
            for i, entry in enumerate(entries[:30]): # Limit to 30
                title = entry.title.text if entry.title else ""
                if not title or title in seen_titles: continue
                seen_titles.add(title)
                
                link = entry.link.text if entry.link else ""
                pub_date = entry.pubDate.text if entry.pubDate else ""
                desc = entry.description.text if entry.description else ""
                
                # HTML strip for desc
                desc_text = BeautifulSoup(desc, "lxml").get_text()
                
                # Assign
                items.append({
                    "rank": i + 1,
                    "title": title,
                    "heat": (35 - i) * 60000, # Mock heat: 2M down to 300k
                    "label": "AI",
                    "category": "大模型", # Forced Category
                    "tags": ["大模型", "AI"],
                    "url": link,
                    "raw_summary_context": desc_text[:200],
                    "source": "GoogleAI"
                })
    except Exception as e:
        print(f"GoogleAI Fetch Error: {e}")
        
    # Fallback if connection fails (e.g. if Google is blocked)
    if not items:
         print("Using GoogleAI Mock Data (Fallback)")
         mock_ai = [
             ("DeepSeek发布新一代开源模型，性能对标GPT-4", "大模型"),
             ("OpenAI Sora公测最新进展：好莱坞导演试用反馈", "大模型"),
             ("文心一言4.0用户数突破1亿，开启商业化", "大模型"),
             ("Anthropic Claude 3.5 Sonnet 能力测评：代码能力逆天", "大模型"),
             ("马斯克xAI宣布Grok-1.5开源，权重下载", "大模型"),
             ("苹果WWDC前瞻：iOS 18将深度集成生成式AI", "大模型")
         ]
         for i, (t, c) in enumerate(mock_ai):
             items.append({
                "rank": i+1,
                "title": t,
                "heat": (20-i) * 300000,
                "label": "AI",
                "category": c,
                "tags": ["AI", "LLM"],
                "url": f"https://www.google.com/search?q={t}",
                "raw_summary_context": t,
                "source": "GoogleAI"
             })

    # AI Process
    # IMPORTANT: enrich_with_ai might change the category using LLM.
    # We must FORCE "大模型" category for this source.
    enriched_items = enrich_with_ai(items)
    for item in enriched_items:
        item['category'] = "大模型"
        # Ensure '大模型' is in tags
        current_tags = item.get('tags', []) or []
        if "大模型" not in current_tags:
            current_tags.insert(0, "大模型")
        item['tags'] = current_tags
        
    return enriched_items


def sync_hot_to_mentions(items, source_name):
    if not items: return
    try:
        import hashlib
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        for item in items:
            title = item.get('title', '')
            url = item.get('url', '')
            # Generate hash
            hash_input = f"{title}_{source_name}" # 简化Hash，主要靠标题去重
            content_hash = hashlib.md5(hash_input.encode()).hexdigest()
            
            # Check existence (Simple Deduplication)
            c.execute("SELECT id FROM mentions WHERE content_hash=?", (content_hash,))
            if c.fetchone(): continue
            
            # Insert
            # item may have 'summary' dict from AI, we take 'raw_summary_context' or summary text
            summary_text = item.get('raw_summary_context', '')
            if isinstance(item.get('summary'), dict):
                summary_text = item['summary'].get('summary', summary_text)
                
            c.execute('''INSERT INTO mentions 
                (client_id, source, title, url, publish_time, content_text, 
                 clean_status, manual_category, manual_tags, content_hash, risk_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                ('system_hotspot', source_name, title, url, time.time(), 
                 summary_text, 
                 'hotspot', item.get('category', '综合'), 
                 json.dumps(item.get('tags', []), ensure_ascii=False),
                 content_hash, 0)
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Sync Hotspot Error: {e}")

# === 核心逻辑：获取并过滤 ===
def get_data_with_cache(source_name, fetch_func):
    # 读缓存
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT data, updated_at FROM hot_cache WHERE source=?", (source_name,))
        row = c.fetchone()
        conn.close()
        
        if row and (time.time() - row[1] < CACHE_EXPIRE_SECONDS):
            return json.loads(row[0])
    except: pass

    # 没缓存，抓取
    print(f"[{source_name}] 抓取中...")
    data = fetch_func()
    if data:
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("REPLACE INTO hot_cache (source, data, updated_at) VALUES (?, ?, ?)", 
                      (source_name, json.dumps(data, ensure_ascii=False), time.time()))
            conn.commit()
            conn.close()
            
            # 同步到全网内容库 (Log Hotspot items)
            sync_hot_to_mentions(data, source_name)
            
        except: pass
    return data

def get_weibo_hot_list(category="综合"):
    all_data = {}
    
    # 1. 先抓取所有源的数据
    sources = [
        ("微博", fetch_weibo),
        ("头条", fetch_toutiao),
        ("微信", fetch_wechat_proxy),   # Using '微信' shorter name
        ("B站", fetch_bilibili),
        ("抖音", fetch_douyin),   # NEW
        ("百度", fetch_baidu),
        ("GoogleAI", fetch_google_ai_news) # NEW: Google AI
    ]
    
    # 2. 遍历所有源，进行过滤
    for src_name, func in sources:
        raw_items = get_data_with_cache(src_name, func)
        if not raw_items: continue
        
        filtered_items = []
        for item in raw_items:
            # 兼容旧逻辑 Source Name Check
            item['source'] = src_name # Ensure consistency
            
            # 强制修正 GoogleAI 的分类 (即使是缓存数据)
            if src_name == "GoogleAI":
                item['category'] = "大模型"
                if "大模型" not in item.get('tags', []):
                    item.setdefault('tags', []).insert(0, "大模型")
            
            # 过滤逻辑：
            # 如果是"综合"，返回所有
            # 否则，只返回 category 字段匹配的
            # EXCEPT: If category is "大模型" and source is "GoogleAI", keep it? 
            # Logic: user selects "大模型" -> filter logic: if item['category'] == '大模型'.
            # GoogleAI items have category='大模型', so they naturally pass.
            
            if category == "综合":
                filtered_items.append(item)
            elif item.get('category') == category:
                filtered_items.append(item)
        
        # 只有当该源有符合条件的数据时才返回
        if filtered_items:
            # 重新排序 rank
            for idx, val in enumerate(filtered_items):
                val['rank'] = idx + 1
            all_data[src_name] = filtered_items

    return all_data