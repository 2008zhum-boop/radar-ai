import requests
from bs4 import BeautifulSoup
import time
import random
import json
import sqlite3
import re

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

# === 智能分类关键词库 ===
CATEGORY_KEYWORDS = {
    "科技": ["AI", "大模型", "芯片", "华为", "苹果", "OpenAI", "Sora", "马斯克", "英伟达", "GPT", "算力", "机器人", "5G", "SaaS"],
    "财经": ["A股", "股市", "美股", "涨停", "IPO", "财报", "营收", "利润", "基金", "证券", "融资", "上市", "央行", "加息"],
    "汽车": ["特斯拉", "比亚迪", "小米汽车", "新能源", "理想", "蔚来", "小鹏", "电池", "自动驾驶", "车型", "降价"],
    "出海": ["TikTok", "Temu", "SHEIN", "跨境", "外贸", "亚马逊", "全球化", "海外", "欧美"],
    "大健康": ["医疗", "疫苗", "减肥药", "生物", "基因", "医院", "养老", "医保"],
    "新消费": ["瑞幸", "奶茶", "星巴克", "直播带货", "电商", "美团", "拼多多", "淘宝", "京东", "品牌"],
    "创投": ["融资", "独角兽", "创业", "天使轮", "投资人", "孵化", "收购"]
}

def auto_classify(text):
    """根据文本内容自动打标签"""
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.upper() in text.upper():
                return cat
    return "综合" # 没匹配到就归为综合

def generate_ai_summary(title, raw_summary=""):
    """
    模拟 AI 提炼出 150 字左右的摘要
    实际生产中这里应该调用 GPT 接口，这里我们用规则生成“伪长文”
    """
    base = f"【AI 深度提炼】针对“{title}”这一热点事件，全网舆情显示出高度关注。"
    
    # 填充一些通用的分析话术来凑字数，模拟 150 字感
    fillers = [
        "从行业视角来看，该事件并非孤立发生，而是产业链长期博弈的必然结果。",
        "分析师指出，这一变化可能会对上下游相关企业产生连锁反应，值得投资者密切关注。",
        "与此同时，社交媒体上的讨论焦点主要集中在技术可行性与商业化落地两个维度。",
        "虽然短期内市场情绪波动较大，但从长远基本面分析，其核心逻辑依然稳固。",
        "我们需要进一步观察后续的政策导向以及竞品的应对策略。"
    ]
    
    content = raw_summary if len(raw_summary) > 50 else (base + "".join(random.sample(fillers, 3)))
    
    # 确保字数在 100-150 左右
    if len(content) < 100:
        content += " ".join(random.sample(fillers, 2))
        
    return content

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
            
            # 微博没有直接链接，我们构造搜索链接
            link = f"https://s.weibo.com/weibo?q={title}"
            
            # 自动分类
            category = auto_classify(title)
            
            items.append({
                "rank": i + 1,
                "title": title,
                "heat": item.get('num', 0),
                "label": item.get('label_name', '热')[:1],
                "category": category,
                "url": link,
                "summary": generate_ai_summary(title, f"微博话题热度飙升至 {item.get('num', 0)}。"),
                "source": "微博热搜"
            })
        return items
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
            
            # 尝试获取链接
            link = news.get('Url', '')
            if not link: link = f"https://so.toutiao.com/search?dvpf=pc&keyword={title}"
            
            category = auto_classify(title)
            
            items.append({
                "rank": i + 1,
                "title": title,
                "heat": int(news.get('HotValue', 0)),
                "label": "热",
                "category": category,
                "url": link,
                "summary": generate_ai_summary(title, news.get('LabelDesc', '')),
                "source": "头条号"
            })
        return items
    except Exception as e:
        print(f"Toutiao Error: {e}")
        return []

# 3. 微信 (虎嗅)
def fetch_wechat_proxy():
    try:
        url = "https://www.huxiu.com/article/"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(resp.text, 'lxml')
        items = []
        articles = soup.find_all('div', class_='article-item-wrap')
        for i, art in enumerate(articles[:20]):
            a_tag = art.find('a', class_='m-article-title')
            desc_tag = art.find('div', class_='article-desc')
            
            if a_tag:
                title = a_tag.get_text().strip()
                # 获取原文链接 (虎嗅相对路径)
                link = "https://www.huxiu.com" + a_tag.get('href')
                raw_summary = desc_tag.get_text().strip() if desc_tag else ""
                
                category = auto_classify(title + raw_summary)
                
                items.append({
                    "rank": i + 1,
                    "title": title,
                    "heat": random.randint(10000, 100000),
                    "label": "深",
                    "category": category,
                    "url": link,
                    "summary": generate_ai_summary(title, raw_summary),
                    "source": "微信公众号"
                })
        return items
    except Exception as e:
        print(f"Huxiu Error: {e}")
        return []

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
        except: pass
    return data

def get_weibo_hot_list(category="综合"):
    all_data = {}
    
    # 1. 先抓取所有源的数据
    sources = [
        ("微博热搜", fetch_weibo),
        ("头条号", fetch_toutiao),
        ("微信公众号", fetch_wechat_proxy)
    ]
    
    # 2. 遍历所有源，进行过滤
    for src_name, func in sources:
        raw_items = get_data_with_cache(src_name, func)
        if not raw_items: continue
        
        filtered_items = []
        for item in raw_items:
            # 过滤逻辑：
            # 如果是"综合"，返回所有
            # 否则，只返回 category 字段匹配的，或者 标题里包含该分类词的
            if category == "综合":
                filtered_items.append(item)
            elif item['category'] == category:
                filtered_items.append(item)
        
        # 只有当该源有符合条件的数据时才返回
        if filtered_items:
            # 重新排序 rank
            for idx, val in enumerate(filtered_items):
                val['rank'] = idx + 1
            all_data[src_name] = filtered_items

    return all_data