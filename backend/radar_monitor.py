import sqlite3
import json
import time
import random
import re
import hashlib
from datetime import datetime, timedelta
from ai_engine import generate_news_summary

DB_FILE = "radar_data.db"

# ==========================================
# 1. 数据库初始化
# ==========================================
def init_monitor_db():
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    c = conn.cursor()
    
    # 客户配置表
    c.execute('''CREATE TABLE IF NOT EXISTS client_config
                 (client_id VARCHAR(64) PRIMARY KEY,
                  name VARCHAR(100),
                  industry VARCHAR(50), 
                  status INTEGER DEFAULT 1,
                  monitor_logic JSON,
                  risk_sensitivity FLOAT DEFAULT 1.0,
                  alert_webhook VARCHAR(255),
                  competitors JSON)''')
                  
    # 自动迁移旧表结构
    try: c.execute("ALTER TABLE client_config ADD COLUMN industry VARCHAR(50)")
    except: pass 
    try: c.execute("ALTER TABLE client_config ADD COLUMN status INTEGER DEFAULT 1")
    except: pass

    # 舆情数据表
    c.execute('''CREATE TABLE IF NOT EXISTS mentions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_id VARCHAR(64),
                  source TEXT,
                  title TEXT,
                  content_text TEXT,
                  url TEXT,
                  publish_time REAL,
                  sentiment_score REAL,
                  risk_level INTEGER,
                  match_detail JSON,
                  clean_status VARCHAR(20) DEFAULT 'uncleaned',
                  manual_category VARCHAR(50),
                  manual_sentiment VARCHAR(20),
                  is_archived INTEGER DEFAULT 0,
                  ai_fact TEXT,
                  ai_angle TEXT,
                  content_hash VARCHAR(64),
                  is_duplicate INTEGER DEFAULT 0,
                  FOREIGN KEY(client_id) REFERENCES client_config(client_id))''')
    
    # 自动迁移新字段
    try: c.execute("ALTER TABLE mentions ADD COLUMN clean_status VARCHAR(20) DEFAULT 'uncleaned'")
    except: pass
    try: c.execute("ALTER TABLE mentions ADD COLUMN manual_category VARCHAR(50)")
    except: pass
    try: c.execute("ALTER TABLE mentions ADD COLUMN manual_sentiment VARCHAR(20)")
    except: pass
    try: c.execute("ALTER TABLE mentions ADD COLUMN is_archived INTEGER DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE mentions ADD COLUMN ai_fact TEXT")
    except: pass
    try: c.execute("ALTER TABLE mentions ADD COLUMN ai_angle TEXT")
    except: pass
    try: c.execute("ALTER TABLE mentions ADD COLUMN manual_tags TEXT")
    except: pass
    try: c.execute("ALTER TABLE mentions ADD COLUMN content_hash VARCHAR(64)")
    except: pass
    try: c.execute("ALTER TABLE mentions ADD COLUMN is_duplicate INTEGER DEFAULT 0")
    except: pass

    # 黑名单表
    c.execute('''CREATE TABLE IF NOT EXISTS source_blacklist
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  source_name TEXT UNIQUE,
                  source_type VARCHAR(20),
                  reason TEXT,
                  created_at REAL,
                  created_by VARCHAR(100))''')
    
    # 内容库表（按客户分类）
    c.execute('''CREATE TABLE IF NOT EXISTS content_library
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  mention_id INTEGER,
                  client_id VARCHAR(64),
                  assigned_category VARCHAR(50),
                  assigned_by VARCHAR(100),
                  assigned_at REAL,
                  FOREIGN KEY(mention_id) REFERENCES mentions(id),
                  FOREIGN KEY(client_id) REFERENCES client_config(client_id))''')

    # 我的选题表 (User Topics)
    c.execute('''CREATE TABLE IF NOT EXISTS user_topics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id VARCHAR(64),
                  topic TEXT,
                  source VARCHAR(50), 
                  created_at REAL,
                  status INTEGER DEFAULT 1,
                  notes TEXT)''')

    # === 3. 新增字段迁移 ===
    try: c.execute("ALTER TABLE mentions ADD COLUMN event_title TEXT")
    except: pass
    try: c.execute("ALTER TABLE mentions ADD COLUMN primary_tag VARCHAR(50)")
    except: pass
    try: c.execute("ALTER TABLE mentions ADD COLUMN secondary_tag VARCHAR(50)")
    except: pass
    try: c.execute("ALTER TABLE mentions ADD COLUMN quality_score INTEGER DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE mentions ADD COLUMN created_at REAL")
    except: pass
        
    conn.commit()
    conn.close()

init_monitor_db()

# ==========================================
# 2. 核心逻辑工具函数
# ==========================================

def get_source_weight(source_name):
    if source_name in ["微博热搜", "央视新闻", "人民日报", "财联社"]: return 100
    if source_name in ["36氪", "虎嗅", "钛媒体", "头条号"]: return 80
    return 50

def calculate_distance(text, word1, word2):
    if word1 not in text or word2 not in text: return float('inf')
    indices1 = [m.start() for m in re.finditer(re.escape(word1), text)]
    indices2 = [m.start() for m in re.finditer(re.escape(word2), text)]
    min_dist = float('inf')
    for i1 in indices1:
        for i2 in indices2:
            dist = abs(i1 - i2)
            if dist < min_dist: min_dist = dist
    return min_dist

def check_advanced_rule(text, rule):
    for word in rule.get('must_contain', []):
        if word not in text: return False, None
    limit_dist = rule.get('distance', 50)
    hit_details = []
    for root_word in rule.get('must_contain', []):
        for near_word in rule.get('nearby_words', []):
            dist = calculate_distance(text, root_word, near_word)
            if dist <= limit_dist:
                hit_details.append(f"{root_word}..({dist}字)..{near_word}")
    if not hit_details: return False, None
    return True, hit_details

def match_client_logic(text, logic_config):
    logic = logic_config if isinstance(logic_config, dict) else json.loads(logic_config)
    for excl in logic.get('exclude_keywords', []):
        if excl and excl in text: return None
    matched_brand = None
    for brand in logic.get('brand_keywords', []):
        if brand and brand in text:
            matched_brand = brand
            break
    advanced_hit_info = None
    for rule in logic.get('advanced_rules', []):
        is_hit, hit_details = check_advanced_rule(text, rule)
        if is_hit:
            advanced_hit_info = {
                "rule_name": rule['rule_name'],
                "risk_level": rule.get('risk_level', 3),
                "details": hit_details
            }
            break
    if matched_brand or advanced_hit_info:
        return {
            "type": "advanced" if advanced_hit_info else "brand",
            "matched_keyword": matched_brand,
            "advanced_detail": advanced_hit_info
        }
    return None

def analyze_risk(text, match_result, source_weight, sentiment_score):
    if match_result.get('advanced_detail'):
        rule_risk = match_result['advanced_detail']['risk_level']
        rule_name = match_result['advanced_detail']['rule_name']
        if rule_risk == 3: return 3, f"命中高危规则: {rule_name}"
        if rule_risk == 0: return 0, f"命中正面利好: {rule_name}"
        if rule_risk == 2: return 2, f"命中风险规则: {rule_name}"
        
    sensitive_words = ["爆炸", "维权", "起诉", "造假", "破产", "去世", "调查", "暴雷"]
    hit_sensitive = [w for w in sensitive_words if w in text]
    
    if sentiment_score < -0.3 and (len(hit_sensitive) > 0 or source_weight >= 80):
        return 3, f"高危负面 (敏感词:{','.join(hit_sensitive)})" if hit_sensitive else "高权重媒体负面"
    if sentiment_score < -0.1: return 2, "疑似负面/争议话题"
    return 1, "常规提及"

# ==========================================
# 3. 核心业务函数 (API 直接调用的 5 个函数)
# ==========================================

# [1] 处理爬虫数据 (main.py 需要这个!)
def process_monitor_data(raw_items):
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    c = conn.cursor()
    c.execute("SELECT client_id, monitor_logic, name FROM client_config WHERE status=1")
    clients = c.fetchall()
    processed_count = 0
    alerts = []
    
    def calculate_sentiment_simple(text):
        score = 0.0 # Default Neutral
        
        # Negative Keywords
        neg_keywords = ["起火", "自燃", "冒烟", "爆炸", "维权", "造假", "破产", "去世", "调查", "暴雷", "事故", "缺陷", "投诉", "致歉", "翻车"]
        for kw in neg_keywords:
            if kw in text:
                # Simple negation check
                if re.search(f"[不没无非].{{0,2}}{kw}", text):
                    continue 
                score -= 0.5
                
        # Positive Keywords
        pos_keywords = ["遥遥领先", "大涨", "突破", "创新", "第一", "首发", "获赞", "好评"]
        for kw in pos_keywords:
             if kw in text:
                 score += 0.3
                 
        return max(-1.0, min(1.0, score))

    for item in raw_items:
        # Handle summary (could be dict from enriched AI, or str)
        summary_val = item.get('summary')
        ai_fact = ""
        ai_angle = ""
        summary_text = ""

        if isinstance(summary_val, dict):
             ai_fact = summary_val.get('fact', '')
             ai_angle = summary_val.get('angle', '')
             summary_text = ai_fact
        elif isinstance(summary_val, str):
             summary_text = summary_val
        
        text = item['title'] + " " + summary_text
        
        # 🟢 获取正文 (如果有)
        full_content = item.get('full_content', '')
        # 如果有抓取到正文，则入库正文，否则入库摘要
        db_content = full_content if len(full_content) > 50 else text

        source = item['source']
        url = item.get('url', '')
        weight = get_source_weight(source)
        sentiment = calculate_sentiment_simple(text)
        
        # If AI summary wasn't pre-generated, generate it now
        if not ai_fact and not ai_angle:
            ai_data = generate_news_summary(item['title'], text)
            ai_fact = ai_data.get('fact', '')
            ai_angle = ai_data.get('angle', '')
        
        # 计算内容指纹 (Title + Summary)
        content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

        # Check Duplicate Logic
        c.execute("SELECT id, is_duplicate FROM mentions WHERE client_id IS NULL AND url=?", (url,))
        existing_url_row = c.fetchone()
        
        is_dup = 0
        if existing_url_row:
             is_dup = existing_url_row[1]
        else:
             c.execute("SELECT id FROM mentions WHERE client_id IS NULL AND content_hash=? AND is_duplicate=0", (content_hash,))
             if c.fetchone():
                 is_dup = 1 
        
        item['is_duplicate'] = is_dup

        if not existing_url_row:
            risk_level_global = 0  # 全局库中的内容不评估风险等级
            c.execute('''INSERT INTO mentions 
                          (client_id, source, title, content_text, url, publish_time, 
                           sentiment_score, risk_level, match_detail, clean_status, ai_fact, ai_angle, content_hash, is_duplicate)
                          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                       (None, source, item['title'], db_content, url, time.time(),
                        sentiment, risk_level_global, json.dumps({"source": source}, ensure_ascii=False), 'uncleaned', ai_fact, ai_angle, content_hash, is_dup))
            processed_count += 1
        
        # 再根据客户监控逻辑保存到特定客户（现有逻辑）
        for client_row in clients:
            c_id, c_logic_str, c_name = client_row
            try: c_logic = json.loads(c_logic_str) if isinstance(c_logic_str, str) else c_logic_str
            except: continue
            
            # 使用 标题+摘要 进行匹配 (效率较高且通常足够)
            match_res = match_client_logic(text, c_logic)
            if match_res:
                c.execute("SELECT id FROM mentions WHERE client_id=? AND url=?", (c_id, url))
                if c.fetchone(): continue 
                
                risk_level, reason = analyze_risk(text, match_res, weight, sentiment)
                
                # FORCE SENTIMENT IF RISK LEVEL (CONFIG DRIVEN)
                final_sentiment = sentiment
                if risk_level >= 2:
                    final_sentiment = -0.6 # Force negative
                elif risk_level == 1:
                    final_sentiment = 0.6 # Force positive
                
                c.execute('''INSERT INTO mentions 
                             (client_id, source, title, content_text, url, publish_time, 
                              sentiment_score, risk_level, match_detail, ai_fact, ai_angle)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                          (c_id, source, item['title'], db_content, url, time.time(),
                           final_sentiment, risk_level, json.dumps({"reason": reason, "match_info": match_res}, ensure_ascii=False), ai_fact, ai_angle))
                if risk_level >= 2:
                    alerts.append({"client": c_name, "level": risk_level, "title": item['title'], "reason": reason})
    conn.commit()
    conn.close()
    return {"processed": processed_count, "alerts": alerts}

# [5] 获取实时监控统计 (Dashboard)
def get_monitor_stats(client_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 基础统计 (Top Cards)
    now = time.time()
    day_seconds = 86400
    
    # Client Filter Condition
    base_filter = ""
    params = []
    if client_id:
        base_filter = " AND client_id = ?"
        params.append(client_id)
        
    c.execute(f"SELECT count(*) FROM mentions WHERE publish_time > ? {base_filter}", [now - day_seconds] + params)
    today_count = c.fetchone()[0]
    
    # Yesterday for Prophet Velocity
    c.execute(f"SELECT count(*) FROM mentions WHERE publish_time BETWEEN ? AND ? {base_filter}", [now - day_seconds * 2, now - day_seconds] + params)
    yesterday_count = c.fetchone()[0]
    
    velocity = today_count - yesterday_count
    velocity_display = f"{'+' if velocity > 0 else ''}{velocity}/d"
    
    c.execute(f"SELECT count(*) FROM mentions WHERE risk_level >= 2 AND publish_time > ? {base_filter}", [now - day_seconds] + params)
    risk_count = c.fetchone()[0]
    
    # Level: 1-5 based on risk count
    level = 1
    if risk_count > 50: level = 5
    elif risk_count > 20: level = 4
    elif risk_count > 10: level = 3
    elif risk_count > 5: level = 2
    
    # 图表数据 (Charts)
    # 模拟 7 天趋势
    trend = {"x": [], "y": []}
    for i in range(6, -1, -1):
        t = now - i * day_seconds
        d_str = time.strftime("%m-%d", time.localtime(t))
        trend["x"].append(d_str)
        
        # 实际查询每一天的数据量
        d_start = t - (t % day_seconds) # 00:00 (rough approx)
        d_end = d_start + day_seconds   # 23:59
        
        c.execute(f"SELECT count(*) FROM mentions WHERE publish_time BETWEEN ? AND ? {base_filter}", 
                  [d_start, d_end] + params)
        cnt = c.fetchone()[0]
        trend["y"].append(cnt)
        
    # 情感分布
    c.execute(f"SELECT count(*) FROM mentions WHERE sentiment_score > 0.3 {base_filter}", params)
    pos = c.fetchone()[0]
    c.execute(f"SELECT count(*) FROM mentions WHERE sentiment_score < -0.1 {base_filter}", params)
    neg = c.fetchone()[0]
    neu = today_count - pos - neg
    if neu < 0: neu = 0
    
    sentiment = {"pos": pos, "neg": neg, "neu": neu}
    
    # Opinion Clusters (Simple Extraction)
    c.execute(f"SELECT title FROM mentions WHERE (risk_level >= 2 OR sentiment_score < -0.3) AND publish_time > ? {base_filter} LIMIT 50", [now - day_seconds] + params)
    neg_titles = [r[0] for r in c.fetchall()]
    cluster_counter = {}
    mock_keywords = ["价格", "电池", "续航", "服务", "质量", "发热", "卡顿", "闪退", "广告", "抄袭"]
    for t in neg_titles:
        for k in mock_keywords:
            if k in t:
                cluster_counter[k] = cluster_counter.get(k, 0) + 1
    
    top_clusters = sorted(cluster_counter.items(), key=lambda x: x[1], reverse=True)[:3]
    clusters_data = []
    total_relevant = sum([x[1] for x in top_clusters]) if top_clusters else 1
    colors = ["red", "orange", "green"]
    for idx, (k, count) in enumerate(top_clusters):
         clusters_data.append({
             "text": f"用户槽点-{k}",
             "percent": f"{int((count / total_relevant) * 100)}%",
             "val": int((count / total_relevant) * 100),
             "color": colors[idx % 3]
         })
    
    # 最新日志 (Logs)
    c.execute(f"SELECT title, source, risk_level, publish_time, sentiment_score FROM mentions WHERE publish_time > ? {base_filter} ORDER BY publish_time DESC LIMIT 10", [now - day_seconds*7] + params)
    logs = []
    for r in c.fetchall():
        logs.append({
            "title": r[0],
            "source": r[1],
            "level": r[2],
            "time": time.strftime("%m-%d %H:%M", time.localtime(r[3])),
            "score": r[4]
        })

    conn.close()
    
    return {
        "today_count": today_count,
        "yesterday_count": yesterday_count,
        "risk_count": risk_count,
        "prophet": {
            "level": level,
            "velocity": velocity_display,
            "peak_time": "今日 14:00", # Mock
            "prediction": "预测 2小时后 传播达峰" # Mock
        },
        "charts": {
            "trend": trend,
            "sentiment": sentiment,
            "clusters": clusters_data
        },
        "logs": logs
    }

# [3] 保存客户配置
def save_full_client_config(name, industry, status, logic_dict, client_id=None):
    conn = sqlite3.connect(DB_FILE, timeout=20)
    c = conn.cursor()
    
    # Try to find existing client
    # If client_id is provided, look up by ID.
    # Otherwise, fallback to looking up by name (legacy support/prevent duplicate names if needed, 
    # though ideally we allow same names if IDs differ? tailored for user request: fixing save bug)
    
    target_id = None
    
    if client_id:
        c.execute("SELECT client_id FROM client_config WHERE client_id=?", (client_id,))
        row = c.fetchone()
        if row:
            target_id = row[0]
            
    # If no ID provided or not found by ID, allow check by name to avoid accidental duplicates 
    # (Optional: depends on if we want unique names. Let's assume unique names for safety)
    if not target_id:
        c.execute("SELECT client_id FROM client_config WHERE name=?", (name,))
        row = c.fetchone()
        if row:
            target_id = row[0]

    logic_json = json.dumps(logic_dict, ensure_ascii=False)
    
    if target_id:
        # Update existing
        c.execute("UPDATE client_config SET name=?, industry=?, status=?, monitor_logic=? WHERE client_id=?", 
                  (name, industry, status, logic_json, target_id))
        cid = target_id
    else:
        # Create new
        cid = f"CLI_{int(time.time())}_{random.randint(100,999)}"
        c.execute("INSERT INTO client_config (client_id, name, industry, status, monitor_logic) VALUES (?,?,?,?,?)", 
                  (cid, name, industry, status, logic_json))
                  
    conn.commit()
    conn.close()
    return {"status": "success", "client_id": cid}

# [4] 删除客户
def delete_client_by_id(client_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM client_config WHERE client_id=?", (client_id,))
    c.execute("DELETE FROM mentions WHERE client_id=?", (client_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

# [5] 获取所有客户列表
def get_all_clients():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT client_id, name, monitor_logic, industry, status FROM client_config")
    res = []
    today_start = time.time() - 86400
    res = []
    
    # Pre-fetch stats for efficiency (or just loop query for simplicity if volume low)
    # Looping is fine for < 50 clients.
    
    for row in c.fetchall():
        cid, cname, logic_str, industry, status = row
        try:
            logic = json.loads(logic_str)
        except:
            logic = {}
            
        # 1. Sentiment Distribution (All time or last 30 days)
        # Pos: >0.3, Neg: <-0.1
        c.execute("SELECT count(*) FROM mentions WHERE client_id=? AND sentiment_score > 0.3", (cid,))
        pos = c.fetchone()[0]
        c.execute("SELECT count(*) FROM mentions WHERE client_id=? AND sentiment_score < -0.1", (cid,))
        neg = c.fetchone()[0]
        c.execute("SELECT count(*) FROM mentions WHERE client_id=? AND sentiment_score BETWEEN -0.1 AND 0.3", (cid,))
        neu = c.fetchone()[0]
        
        total_sent = pos + neg + neu
        if total_sent == 0: total_sent = 1
        
        # 2. 7-Day Trend
        trend_vals = []
        now = time.time()
        for i in range(6, -1, -1):
            t_start = now - (i+1) * 86400
            t_end = now - i * 86400
            c.execute("SELECT count(*) FROM mentions WHERE client_id=? AND publish_time BETWEEN ? AND ?", (cid, t_start, t_end))
            trend_vals.append(c.fetchone()[0])
            
        res.append({
            "client_id": cid,
            "name": cname,
            "industry": industry,
            "status": status,
            "config": logic,
            "stats": {
                "sentiment": [
                    int((neg/total_sent)*100), 
                    int((neu/total_sent)*100), 
                    int((pos/total_sent)*100)
                ], # [Neg%, Neu%, Pos%]
                "trend": trend_vals # [d-6, ..., d-0]
            }
        })
    
    conn.close()
    return res

# [6] 生成客户日报
def generate_client_report(client_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 获取客户信息
    c.execute("SELECT name, industry FROM client_config WHERE client_id=?", (client_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return {"error": "Client not found"}
    
    client_name = row[0]
    industry = row[1]
    
    # 获取过去24小时数据
    start_time = time.time() - 86400
    c.execute("SELECT count(*) FROM mentions WHERE client_id=? AND publish_time > ?", (client_id, start_time))
    total_count = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM mentions WHERE client_id=? AND risk_level >= 2 AND publish_time > ?", (client_id, start_time))
    risk_count = c.fetchone()[0]
    
    # 获取Top 5 负面/高危
    alerts = []
    c.execute("SELECT title, source, risk_level, match_detail FROM mentions WHERE client_id=? AND risk_level>=2 AND publish_time > ? ORDER BY risk_level DESC LIMIT 5", (client_id, start_time))
    for r in c.fetchall():
        try: reason = json.loads(r[3]).get('reason', '')
        except: reason = ''
        alerts.append({"title": r[0], "source": r[1], "level": r[2], "reason": reason})
        
    conn.close()
    
    # 模拟生成报告文本 (Mock LLM)
    summary = f"【{client_name}】过去24小时舆情平稳。全网声量 {total_count} 条，其中高危 {risk_count} 条。"
    if risk_count > 0:
        summary += " 需重点关注负面舆情扩散风险。"
    else:
        summary += " 品牌形象保持良好。"
        
    return {
        "client_name": client_name,
        "industry": industry,
        "time_range": "过去24小时",
        "total_mentions": total_count,
        "high_risk_count": risk_count,
        "summary": summary,
        "top_risks": alerts,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# ==========================================
# 4. 全网内容库管理模块 (Global Content Library)
# ==========================================

# [7] 获取全网内容库列表（支持搜索、筛选）
def get_global_content_library(search_text="", client_id=None, source_filter=None, sentiment_filter=None, 
                                clean_status_filter=None, time_range="24h", page=1, page_size=20):
    """
    获取全网内容库，支持多维度筛选
    client_id: 若指定，则只返回该客户关联的内容
    time_range: "1h" / "24h" / "7d" / "all"
    clean_status_filter: ["uncleaned", "cleaned", "discarded", "archived"]
    sentiment_filter: ["positive", "negative", "neutral"]
    source_filter: ["微博", "微信", "B站", "36氪"] 等
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 构建时间条件
    time_map = {"1h": 3600, "24h": 86400, "7d": 604800}
    time_seconds = time_map.get(time_range, 86400 * 365)
    start_time = time.time() - time_seconds if time_range != "all" else 0
    
    # 基础查询
    # Join with article_tags to get tags
    # We use a subquery or direct join? Direct join with Group By might mess up pagination if not careful.
    # Safe way: Select base items first (with limit), THEN fetch tags for them?
    # OR: Join and Group By ID.
    
    # Let's use GROUP BY id to ensure unique items and agg tags
    # Added new fields: event_title, quality_score, primary_tag, secondary_tag, created_at
    base_cols = "m.id, m.client_id, m.source, m.title, m.content_text, m.url, m.publish_time, m.sentiment_score, m.risk_level, m.clean_status, m.manual_category, m.manual_sentiment, m.event_title, m.quality_score, m.primary_tag, m.secondary_tag, m.ai_fact, m.created_at"
    
    sql = f"""
        SELECT {base_cols}, GROUP_CONCAT(t.name) as tag_names
        FROM mentions m
        LEFT JOIN article_tags at ON cast(m.id as text) = at.article_id
        LEFT JOIN tags t ON at.tag_id = t.id
        WHERE m.publish_time > ?
    """
    params = [start_time]
    
    # Client ID 筛选
    if client_id:
        sql += " AND m.client_id = ?"
        params.append(client_id)

    # 搜索条件（全文检索）
    if search_text:
        sql += " AND (m.title LIKE ? OR m.content_text LIKE ?)"
        search_pattern = f"%{search_text}%"
        params.extend([search_pattern, search_pattern])
    
    # 来源筛选
    if source_filter and len(source_filter) > 0:
        placeholders = ",".join(["?" for _ in source_filter])
        sql += f" AND m.source IN ({placeholders})"
        params.extend(source_filter)
    
    # 情感筛选
    if sentiment_filter and len(sentiment_filter) > 0:
        if "positive" in sentiment_filter and "negative" in sentiment_filter and "neutral" in sentiment_filter:
            pass
        else:
            sentiment_conditions = []
            if "positive" in sentiment_filter:
                sentiment_conditions.append("m.sentiment_score > 0.3")
            if "negative" in sentiment_filter:
                sentiment_conditions.append("m.sentiment_score < -0.1")
            if "neutral" in sentiment_filter:
                sentiment_conditions.append("m.sentiment_score BETWEEN -0.1 AND 0.3")
            if sentiment_conditions:
                sql += " AND (" + " OR ".join(sentiment_conditions) + ")"
    
    # 清洗状态筛选
    if clean_status_filter and len(clean_status_filter) > 0:
        placeholders = ",".join(["?" for _ in clean_status_filter])
        sql += f" AND m.clean_status IN ({placeholders})"
        params.extend(clean_status_filter)
    else:
        # 默认不显示已废弃的
        sql += " AND (m.clean_status != 'discarded' OR m.clean_status IS NULL)"
    
    # 不显示已归档的
    sql += " AND m.is_archived = 0"
    
    # 不显示重复的
    sql += " AND m.is_duplicate = 0"
    
    # Group By ID to combine tags
    sql += " GROUP BY m.id"
    
    # 排序和分页
    sql += " ORDER BY m.publish_time DESC LIMIT ? OFFSET ?"
    offset = (page - 1) * page_size
    params.extend([page_size, offset])
    
    c.execute(sql, params)
    rows = c.fetchall()
    
    items = []
    for row in rows:
        # 计算热度分值（基于情感、风险等级、来源权重）
        weight = get_source_weight(row[2])  # source
        sentiment = row[7] if row[7] is not None else 0  # sentiment_score
        risk = row[8] if row[8] is not None else 0  # risk_level
        hotness_score = (risk * 30) + (weight * 0.3) + max(0, sentiment * 50)
        
        # tags_str is from GROUP_CONCAT(t.name) at row[12]
        tags_val = row[12] if len(row) > 12 else ""
        # If it's a comma separated string, split it for frontend array support if needed, or keep as string
        # Frontend handles string or array: `item.tags`
        # Let's return as string or array? Frontend code: `item.tags.slice(0,2).join(',')` implies array.
        # But `detail.manual_tags` logic suggests it might be string. 
        # GlobalContentLibrary.vue: `Array.isArray(item.tags) ? ...`
        
        if tags_val:
            tags_list = tags_val.split(',')
            # Deduplicate just in case
            tags_list = list(set(tags_list))
            tags_val = tags_list
        else:
            tags_val = []
            
        # Parse new fields
        # row indices have shifted because we added columns to base_cols
        # 0:id, 1:client, 2:source, 3:title (Article Title), 4:content, 5:url, 6:pub_time, 
        # 7:sentiment, 8:risk, 9:clean, 10:man_cat, 11:man_sent, 
        # 12:event_title, 13:quality, 14:p_tag, 15:s_tag, 16:ai_fact, 17:created_at
        # 18: tag_names (GROUP_CONCAT)
        
        event_title = row[12] if row[12] else row[3] # Fallback to article title if no event title
        quality = row[13] if row[13] else 0
        p_tag = row[14]
        s_tag = row[15]
        summary = row[16] # ai_fact
        ingest_time = row[17] if row[17] else row[6] # Fallback to publish_time

        # Logic for tags if p_tag/s_tag are empty but tags_val exists
        if not p_tag and len(tags_val) > 0: p_tag = tags_val[0]
        if not s_tag and len(tags_val) > 1: s_tag = tags_val[1]
        
        items.append({
            "id": row[0],
            "client_id": row[1],
            "source": row[2],
            "article_title": row[3], # rename title -> article_title
            "event_title": event_title,
            "title": row[3], # Keep for compatibility
            "summary": summary,
            "content_text": row[4],
            "content_preview": row[4][:100] if row[4] else "",
            "url": row[5],
            "publish_time": row[6],
            "ingest_time": ingest_time,
            "ingest_time_display": time.strftime("%m-%d %H:%M", time.localtime(ingest_time)),
            "time_display": time.strftime("%m-%d %H:%M", time.localtime(row[6])),
            "sentiment_score": round(sentiment, 2),
            "sentiment_label": "负面" if risk >= 2 else ("正面" if risk == 1 else ("正面" if sentiment > 0.3 else ("负面" if sentiment < -0.1 else "中性"))),
            "risk_level": risk,
            "quality_score": quality,
            "clean_status": row[9] or "uncleaned",
            "manual_category": row[10],
            "manual_sentiment": row[11],
            "category": row[10],
            "primary_tag": p_tag,
            "secondary_tag": s_tag,
            "tags": tags_val,
            "hotness": round(hotness_score, 0),
            "hotness_display": "🔥" * min(5, max(1, int(hotness_score / 1000))),
            # --- New Fields for Rich Dashboard ---
            "author_level": random.randint(3, 5) if "微博" in row[2] or "36氪" in row[2] else random.randint(1, 3), # Mock Lv
            "author_verify": 1 if random.random() > 0.7 else 0, # Mock Verify
            "read_count": f"{random.randint(1, 400)/10.0:.1f}w", # Mock Reads
            "comment_count": random.randint(10, 2000)
        })
    
    # 获取总数
    count_sql = "SELECT COUNT(*) FROM mentions WHERE publish_time > ? AND is_archived = 0"
    count_params = [start_time]
    
    if client_id:
        count_sql += " AND client_id = ?"
        count_params.append(client_id)

    if search_text:
        count_sql += " AND (title LIKE ? OR content_text LIKE ?)"
        count_params.extend([f"%{search_text}%", f"%{search_text}%"])
    if source_filter and len(source_filter) > 0:
        placeholders = ",".join(["?" for _ in source_filter])
        count_sql += f" AND source IN ({placeholders})"
        count_params.extend(source_filter)
    if clean_status_filter and len(clean_status_filter) > 0:
        placeholders = ",".join(["?" for _ in clean_status_filter])
        count_sql += f" AND clean_status IN ({placeholders})"
        count_params.extend(clean_status_filter)
    else:
        count_sql += " AND (clean_status != 'discarded' OR clean_status IS NULL)"
    
    c.execute(count_sql, count_params)
    total = c.fetchone()[0]
    
    conn.close()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

# [8] 批量删除/废弃内容
def bulk_discard_content(mention_ids):
    """将内容标记为已废弃（不是物理删除）"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for mid in mention_ids:
        c.execute("UPDATE mentions SET clean_status='discarded' WHERE id=?", (mid,))
    conn.commit()
    conn.close()
    return {"status": "success", "discarded_count": len(mention_ids)}

# [9] 黑名单管理：添加信源到黑名单
def add_source_to_blacklist(source_name, source_type="general", reason="", created_by="system"):
    """添加信源到黑名单，之后该信源的内容自动丢弃"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO source_blacklist (source_name, source_type, reason, created_at, created_by) VALUES (?,?,?,?,?)",
                  (source_name, source_type, reason, time.time(), created_by))
        
        # 自动标记该源的所有内容为已废弃
        c.execute("UPDATE mentions SET clean_status='discarded' WHERE source=? AND clean_status IS NULL", (source_name,))
        
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"已添加{source_name}到黑名单"}
    except sqlite3.IntegrityError:
        conn.close()
        return {"status": "error", "message": "该信源已在黑名单中"}

# [10] 黑名单管理：获取黑名单列表
def get_source_blacklist():
    """获取所有黑名单源"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, source_name, source_type, reason, created_at, created_by FROM source_blacklist ORDER BY created_at DESC")
    
    items = []
    for row in c.fetchall():
        items.append({
            "id": row[0],
            "source_name": row[1],
            "source_type": row[2],
            "reason": row[3],
            "created_time": time.strftime("%Y-%m-%d %H:%M", time.localtime(row[4])),
            "created_by": row[5]
        })
    
    conn.close()
    return {"blacklist": items}

# [11] 黑名单管理：移除信源
def remove_source_from_blacklist(source_name):
    """从黑名单移除信源"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM source_blacklist WHERE source_name=?", (source_name,))
    conn.commit()
    conn.close()
    return {"status": "success"}

# [12] 手动分发：关联内容到客户
def associate_content_to_client(mention_id, client_id, assigned_by="editor"):
    """
    将内容手动关联到客户
    结果：内容立即出现在该客户的监控中心，并触发风险预警
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 获取mention详情
    c.execute("SELECT title, source, risk_level FROM mentions WHERE id=?", (mention_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return {"status": "error", "message": "内容不存在"}
    
    # 更新关联
    c.execute("UPDATE mentions SET client_id=? WHERE id=?", (client_id, mention_id))
    
    # 添加到内容库记录
    c.execute("INSERT INTO content_library (mention_id, client_id, assigned_category, assigned_by, assigned_at) VALUES (?,?,?,?,?)",
              (mention_id, client_id, "manual_dispatch", assigned_by, time.time()))
    
    # 标记为已清洗
    c.execute("UPDATE mentions SET clean_status='cleaned' WHERE id=?", (mention_id,))
    
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "message": f"已关联到客户",
        "title": row[0],
        "risk_level": row[2]
    }

# [13] 修正 AI 判定：修改内容分类和情感
def correct_content_classification(mention_id, new_category=None, new_sentiment=None, corrected_by="editor"):
    """
    编辑手动修正 AI 的自动分类和情感判定
    场景：AI把"苹果发布会"误分为"水果新闻"，编辑在这里手动改为"科技"
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    updates = []
    params = []
    
    if new_category:
        updates.append("manual_category=?")
        params.append(new_category)
    
    if new_sentiment:
        updates.append("manual_sentiment=?")
        params.append(new_sentiment)
    
    if not updates:
        conn.close()
        return {"status": "error", "message": "未指定修正内容"}
    
    updates.append("clean_status='cleaned'")
    
    params.append(mention_id)
    sql = f"UPDATE mentions SET {', '.join(updates)} WHERE id=?"
    c.execute(sql, params)
    
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "message": "已修正AI判定",
        "new_category": new_category,
        "new_sentiment": new_sentiment
    }

# [13b] 获取单条内容详情（用于编辑时拉取正文、摘要等）
def get_mention_by_id(mention_id):
    """根据 id 返回单条内容的完整信息，供编辑使用"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""SELECT id, client_id, source, title, content_text, url, publish_time,
                        sentiment_score, risk_level, clean_status, manual_category, manual_sentiment,
                        ai_fact, ai_angle FROM mentions WHERE id=?""", (mention_id,))
    row = c.fetchone()
    manual_tags_val = ""
    try:
        c.execute("SELECT manual_tags FROM mentions WHERE id=?", (mention_id,))
        t = c.fetchone()
        if t and t[0]:
            manual_tags_val = t[0]
    except sqlite3.OperationalError:
        pass
    conn.close()
    if not row:
        return None
    # 情感展示：优先 manual_sentiment，否则按 score
    score = row[7]
    label = "正面" if score > 0.3 else ("负面" if score < -0.1 else "中性")
    if row[11]:  # manual_sentiment
        label = "正面" if row[11] == "positive" else ("负面" if row[11] == "negative" else "中性")
    return {
        "id": row[0],
        "client_id": row[1],
        "source": row[2],
        "title": row[3],
        "content_text": row[4] or "",
        "url": row[5],
        "publish_time": row[6],
        "sentiment_score": row[7],
        "risk_level": row[8],
        "clean_status": row[9] or "uncleaned",
        "manual_category": row[10],
        "manual_sentiment": row[11],
        "sentiment_label": label,
        "ai_fact": row[12] or "",
        "ai_angle": row[13] or "",
        "manual_tags": manual_tags_val
    }

# [13c] 全量更新内容（标题、正文、摘要、分类、情感、标签）
# [13c] 全量更新内容（标题、正文、摘要、分类、情感、标签、事件标题、质量）
def update_content_full(mention_id, title=None, content_text=None, manual_category=None,
                        manual_sentiment=None, ai_fact=None, manual_tags=None, 
                        event_title=None, quality_score=None, updated_by="editor"):
    """编辑保存时更新内容的所有可编辑字段"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    updates = []
    params = []
    if title is not None:
        updates.append("title=?")
        params.append(title)
    if content_text is not None:
        updates.append("content_text=?")
        params.append(content_text)
    if manual_category is not None:
        updates.append("manual_category=?")
        params.append(manual_category)
    if manual_sentiment is not None:
        updates.append("manual_sentiment=?")
        params.append(manual_sentiment)
    if ai_fact is not None:
        updates.append("ai_fact=?")
        params.append(ai_fact)
    if event_title is not None:
        try: 
            c.execute("ALTER TABLE mentions ADD COLUMN event_title TEXT")
        except: 
            pass
        updates.append("event_title=?")
        params.append(event_title)
    if quality_score is not None:
        try: 
            c.execute("ALTER TABLE mentions ADD COLUMN quality_score INTEGER DEFAULT 0")
        except: 
            pass
        updates.append("quality_score=?")
        params.append(quality_score)
    if manual_tags is not None:
        try:
            c.execute("ALTER TABLE mentions ADD COLUMN manual_tags TEXT")
        except sqlite3.OperationalError:
            pass
        updates.append("manual_tags=?")
        params.append(manual_tags)
        
        # Also update derived tags
        try:
            tags_list = manual_tags.split(',') if isinstance(manual_tags, str) else manual_tags
            p_tag = tags_list[0] if len(tags_list) > 0 else ""
            s_tag = tags_list[1] if len(tags_list) > 1 else ""
            updates.append("primary_tag=?")
            params.append(p_tag)
            updates.append("secondary_tag=?")
            params.append(s_tag)
        except: pass

    if not updates:
        conn.close()
        return {"status": "error", "message": "未指定要更新的字段"}
    updates.append("clean_status='cleaned'")
    params.append(mention_id)
    sql = f"UPDATE mentions SET {', '.join(updates)} WHERE id=?"
    c.execute(sql, params)
    conn.commit()
    conn.close()
    return {"status": "success", "message": "已保存修改"}

# [14] 数据质检统计：垃圾广告检测
def get_content_quality_stats():
    """
    数据质检统计：检查爬虫抓取的数据质量
    返回：垃圾广告比例、信源质量评分等
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 过去24小时的内容
    start_time = time.time() - 86400
    
    c.execute("SELECT COUNT(*) FROM mentions WHERE publish_time > ?", (start_time,))
    total = c.fetchone()[0]
    
    # 识别可能的垃圾广告（简单启发式）
    # 特征：包含"兼职"、"刷单"、"联系"等关键词，且风险等级低
    c.execute("SELECT COUNT(*) FROM mentions WHERE publish_time > ? AND (content_text LIKE '%兼职%' OR content_text LIKE '%刷单%' OR content_text LIKE '%代理%') AND risk_level < 2",
              (start_time,))
    garbage_count = c.fetchone()[0]
    
    # 各来源的内容数
    c.execute("SELECT source, COUNT(*) as cnt FROM mentions WHERE publish_time > ? GROUP BY source ORDER BY cnt DESC",
              (start_time,))
    sources = []
    for row in c.fetchall():
        sources.append({"source": row[0], "count": row[1], "percentage": round(row[1] * 100 / max(1, total), 2)})
    
    # 情感分布
    c.execute("SELECT COUNT(*) FROM mentions WHERE publish_time > ? AND sentiment_score > 0.3",
              (start_time,))
    positive = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM mentions WHERE publish_time > ? AND sentiment_score < -0.1",
              (start_time,))
    negative = c.fetchone()[0]
    
    neutral = total - positive - negative
    
    conn.close()
    
    return {
        "total_count": total,
        "garbage_count": garbage_count,
        "garbage_rate": round(garbage_count * 100 / max(1, total), 2),
        "source_distribution": sources,
        "sentiment_distribution": {
            "positive": {"count": positive, "percentage": round(positive * 100 / max(1, total), 2)},
            "negative": {"count": negative, "percentage": round(negative * 100 / max(1, total), 2)},
            "neutral": {"count": neutral, "percentage": round(neutral * 100 / max(1, total), 2)}
        }
    }

# ==========================================
# 8. 我的选题管理 (User Topics)
# ==========================================
def add_user_topic(user_id, topic, source="manual", notes=""):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # 简单查重
        c.execute("SELECT id FROM user_topics WHERE user_id=? AND topic=? AND status=1", (user_id, topic))
        if c.fetchone():
            conn.close()
            return {"status": "exists", "msg": "该选题已添加"}
            
        c.execute("INSERT INTO user_topics (user_id, topic, source, created_at, status, notes) VALUES (?, ?, ?, ?, 1, ?)",
                  (user_id, topic, source, time.time(), notes))
        conn.commit()
        tid = c.lastrowid
        conn.close()
        return {"status": "success", "id": tid}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

def list_user_topics(user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, topic, source, created_at, notes FROM user_topics WHERE user_id=? AND status=1 ORDER BY created_at DESC", (user_id,))
        rows = c.fetchall()
        conn.close()
        
        return [{"id": r[0], "topic": r[1], "source": r[2], "time": r[3], "notes": r[4]} for r in rows]
    except Exception as e:
        print(f"List Topics Error: {e}")
        return []

def remove_user_topic(user_id, topic_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE user_topics SET status=0 WHERE id=? AND user_id=?", (topic_id, user_id))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}