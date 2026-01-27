import sqlite3
import json
import time
import random
import re

DB_FILE = "radar_data.db"

# === 1. 初始化监控专用表 ===
def init_monitor_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 关键词配置表
    # type: 1=核心圈(品牌/高管), 2=竞品圈, 3=行业圈
    # sensitive_words: 该词关联的敏感词，用逗号分隔
    c.execute('''CREATE TABLE IF NOT EXISTS monitor_keywords
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  word TEXT, 
                  type INTEGER, 
                  category TEXT,
                  sensitive_words TEXT)''')
                  
    # 舆情日志表 (存储清洗后的高价值信号)
    # level: 3=红(危机), 2=黄(风险/热点), 1=绿(机会)
    c.execute('''CREATE TABLE IF NOT EXISTS monitor_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  source TEXT,
                  title TEXT,
                  url TEXT,
                  publish_time REAL,
                  sentiment_score REAL,
                  source_weight INTEGER,
                  level INTEGER,
                  tags TEXT,
                  summary TEXT)''')
                  
    # 预置一些初始关键词 (Demo用)
    c.execute("SELECT count(*) FROM monitor_keywords")
    if c.fetchone()[0] == 0:
        presets = [
            ("星云科技", 1, "品牌", "爆炸,起诉,维权,倒闭,裁员"),
            ("雷军", 1, "高管", "离职,套现,谣言"),
            ("特斯拉", 2, "竞品", "刹车失灵,降价,维权"),
            ("人工智能", 3, "行业", "监管,法案,禁令")
        ]
        c.executemany("INSERT INTO monitor_keywords (word, type, category, sensitive_words) VALUES (?,?,?,?)", presets)
        conn.commit()
        
    conn.commit()
    conn.close()

init_monitor_db()

# === 2. 媒体源分级权重 (Source Weighting) ===
def get_source_weight(source_name):
    # S级 (权重 100)
    if source_name in ["微博热搜", "央视新闻", "人民日报"]:
        return 100
    # A级 (权重 80)
    elif source_name in ["36氪", "虎嗅", "钛媒体", "头条号", "财联社"]:
        return 80
    # B级 (权重 50)
    elif source_name in ["百度风云榜", "微信公众号"]:
        return 50
    # C级
    return 30

# === 3. 情感与敏感词分析 (NLP Analysis) ===
def analyze_content(text, keyword_config):
    """
    分析文本，返回：情感分数(-1到1), 命中的敏感词, 是否命中关键词
    """
    # 1. 检查是否包含监控关键词
    target_word = keyword_config['word']
    if target_word not in text:
        return None # 没命中关键词，直接过滤，视为噪音

    # 2. 检查敏感词 (负面判定)
    sensitive_list = keyword_config['sensitive_words'].split(',') if keyword_config['sensitive_words'] else []
    hit_sensitive = [w for w in sensitive_list if w and w in text]
    
    # 3. 简单的情感打分 (模拟)
    # 实际项目中应调用 NLP 模型
    score = 0.5 # 默认中性
    
    negative_words = ["失望", "垃圾", "维权", "黑屏", "卡顿", "骗子", "爆炸", "暴跌"]
    positive_words = ["惊喜", "遥遥领先", "牛逼", "利好", "大涨", "突破", "首发"]
    
    # 粗糙的词库匹配
    for w in negative_words:
        if w in text: score -= 0.2
    for w in hit_sensitive:
        score -= 0.4 # 命中自定义敏感词扣分更重
        
    for w in positive_words:
        if w in text: score += 0.2
        
    # 限制范围
    score = max(-1, min(1, score))
    
    return {
        "score": score,
        "hit_sensitive": hit_sensitive,
        "matched_keyword": target_word
    }

# === 4. 预警等级判定逻辑 (The Alert System) ===
def determine_alert_level(sentiment_score, source_weight, hit_sensitive):
    # 🔴 红色警报 (危机)：权重高 + 极度负面 或 命中敏感词
    if (sentiment_score < -0.3 and source_weight >= 80) or len(hit_sensitive) > 0:
        return 3 
    
    # 🟡 黄色警报 (风险/热点)：权重高 + 关键词提及 (可能是热点，也可能是轻微负面)
    if source_weight >= 80 or (sentiment_score < 0):
        return 2
        
    # 🟢 绿色信号 (机会)：正面情绪 或 普通提及
    return 1

# === 5. 核心处理管道 (Pipeline) ===
def process_monitor_data(raw_items):
    """
    接收爬虫抓回来的原始数据，进行清洗、匹配、入库
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 获取所有配置的关键词
    c.execute("SELECT * FROM monitor_keywords")
    # 转为字典列表
    keywords = [{"word": row[1], "type": row[2], "category": row[3], "sensitive_words": row[4]} for row in c.fetchall()]
    
    processed_count = 0
    alerts = []

    for item in raw_items:
        text = item['title'] + (item.get('summary') or "")
        source = item['source']
        weight = get_source_weight(source)
        
        # 遍历关键词矩阵进行匹配
        for kw in keywords:
            analysis = analyze_content(text, kw)
            
            if analysis: # 命中了！
                level = determine_alert_level(analysis['score'], weight, analysis['hit_sensitive'])
                
                # 入库
                c.execute('''INSERT INTO monitor_logs 
                             (source, title, url, publish_time, sentiment_score, source_weight, level, tags, summary)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (source, item['title'], item['url'], time.time(), 
                           analysis['score'], weight, level, 
                           f"{kw['category']}-{kw['word']}", 
                           item.get('summary', '')))
                
                processed_count += 1
                
                # 如果是红色或黄色，加入实时告警列表返回
                if level >= 2:
                    alerts.append({
                        "level": level,
                        "title": item['title'],
                        "reason": f"命中[{kw['word']}]" + (f"+敏感词[{','.join(analysis['hit_sensitive'])}]" if analysis['hit_sensitive'] else "")
                    })
                
                # 一条新闻只匹配一次主关键词即可，避免重复入库
                break
    
    conn.commit()
    conn.close()
    return {"processed": processed_count, "alerts": alerts}

# === API 接口支持 ===
def get_monitor_stats():
    """获取看板统计数据"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 今日声量
    c.execute("SELECT count(*) FROM monitor_logs WHERE publish_time > ?", (time.time() - 86400,))
    today_count = c.fetchone()[0]
    
    # 风险指数 (红色警报数量)
    c.execute("SELECT count(*) FROM monitor_logs WHERE level=3 AND publish_time > ?", (time.time() - 86400,))
    risk_count = c.fetchone()[0]
    
    # 最近的监控日志
    logs = []
    c.execute("SELECT * FROM monitor_logs ORDER BY id DESC LIMIT 20")
    for row in c.fetchall():
        logs.append({
            "id": row[0],
            "source": row[1],
            "title": row[2],
            "url": row[3],
            "time": time.strftime("%H:%M", time.localtime(row[4])),
            "score": row[5],
            "weight": row[6],
            "level": row[7], # 3红 2黄 1绿
            "tags": row[8],
            "summary": row[9]
        })
        
    conn.close()
    return {
        "today_count": today_count,
        "risk_count": risk_count,
        "logs": logs
    }

def get_config_keywords():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM monitor_keywords")
    data = [{"id": r[0], "word": r[1], "type": r[2], "category": r[3], "sensitive": r[4]} for r in c.fetchall()]
    conn.close()
    return data

def add_config_keyword(word, type_id, category, sensitive):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO monitor_keywords (word, type, category, sensitive_words) VALUES (?,?,?,?)", 
              (word, type_id, category, sensitive))
    conn.commit()
    conn.close()