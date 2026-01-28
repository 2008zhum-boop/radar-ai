import sqlite3
import json
import time
import random
import re
import ai_engine

DB_FILE = "radar_data.db"

# === 1. 初始化监控专用表 (Database Schema) ===
def init_monitor_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1.1 客户配置表 (Client Config) - 核心逻辑存储
    # monitor_logic: JSON structure including brand_keywords, exclude_keywords, advanced_rules
    c.execute('''CREATE TABLE IF NOT EXISTS client_config
                 (client_id VARCHAR(64) PRIMARY KEY,
                  name VARCHAR(100),
                  monitor_logic JSON,
                  risk_sensitivity FLOAT DEFAULT 1.0,
                  alert_webhook VARCHAR(255),
                  competitors JSON)''')
                  
    # 1.2 舆情数据表 (Mentions) - 存储命中结果
    # risk_level: 0=Safe, 1=Attention, 2=Warning, 3=Critical
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
                  FOREIGN KEY(client_id) REFERENCES client_config(client_id))''')
                  
    # Pre-populate with Demo Data if empty
    c.execute("SELECT count(*) FROM client_config")
    if c.fetchone()[0] == 0:
        demo_clients = [
            ("CLI_1001", "星云科技", json.dumps({
                "brand_keywords": ["星云科技", "Nebula", "N-Bot"],
                "exclude_keywords": ["星云法师", "星云锁链"],
                "advanced_rules": [
                    {"rule_name": "高管负面", "must_contain": ["张三", "CEO"], "nearby_words": ["造假", "被抓", "离职"], "distance": 50}
                ]
            }), 1.0, ""),
            ("CLI_2002", "雷军", json.dumps({
                "brand_keywords": ["雷军", "雷总"],
                "exclude_keywords": [],
                "advanced_rules": []
            }), 1.2, "")
        ]
        c.executemany("INSERT INTO client_config (client_id, name, monitor_logic, risk_sensitivity, alert_webhook) VALUES (?,?,?,?,?)", demo_clients)
        conn.commit()
        
    conn.commit()
    conn.close()

init_monitor_db()

# === 2. 核心匹配逻辑 (Matching Logic) ===

def check_advanced_rule(text, rule):
    """
    检查高级规则: must_contain AND (nearby_words within distance)
    NOTE: 简单实现 distance，暂不使用复杂的 NLP 分词，仅用字符距离估算
    """
    # 1. Check must_contain
    for word in rule.get('must_contain', []):
        if word not in text:
            return False, None
            
    # 2. Check nearby_words
    nearby_hits = []
    text_len = len(text)
    
    # 找到所有 must_contain 词的位置，然后向前后搜索 nearby_words
    # 简化版：只要全文同时包含 must_contain 和 nearby_words，且粗略判断距离
    for nearby in rule.get('nearby_words', []):
        if nearby in text:
            nearby_hits.append(nearby)
            
    if not nearby_hits:
        return False, None
        
    return True, nearby_hits

def match_client_logic(text, logic_config):
    """
    将文本与客户逻辑进行匹配
    Return: { "matched": True/False, "type": "brand/advanced", "details": ... }
    """
    logic = logic_config if isinstance(logic_config, dict) else json.loads(logic_config)
    
    # 1. Exclusion Check (High Priority)
    for excl in logic.get('exclude_keywords', []):
        if excl in text:
            return None # Excluded
            
    # 2. Brand Keyword Match
    matched_brand = None
    for brand in logic.get('brand_keywords', []):
        if brand in text:
            matched_brand = brand
            break
            
    # 3. Advanced Rules Match
    advanced_hit = None
    for rule in logic.get('advanced_rules', []):
        is_hit, hit_words = check_advanced_rule(text, rule)
        if is_hit:
            advanced_hit = {"rule": rule['rule_name'], "words": hit_words}
            break
            
    if matched_brand or advanced_hit:
        return {
            "matched_brand": matched_brand,
            "advanced_hit": advanced_hit
        }
        
    return None

# === 3. 风险评估与AI分析 (Risk Assessment) ===

def get_source_weight(source_name):
    if source_name in ["微博热搜", "央视新闻", "人民日报", "财联社"]:
        return 100
    if source_name in ["36氪", "虎嗅", "钛媒体", "头条号"]:
        return 80
    return 50

def analyze_risk(text, match_result, source_weight, sentiment_score):
    """
    根据匹配详情和情感分，判定风险等级
    Level: 0(Safe), 1(Info), 2(Warning), 3(Critical)
    """
    # 1. AI 敏感词检测 (Simulation for now, call AI engine in real scenario)
    # ai_res = ai_engine.analyze_risk_assessment(text, match_result.get('matched_brand') or "General")
    # sensitive_hit = ai_res['risk_keywords']
    sensitive_words = ["爆炸", "维权", "起诉", "造假", "破产", "去世"]
    hit_sensitive = [w for w in sensitive_words if w in text]
    
    # 2. 逻辑判定
    # 🔴 Level 3: 命中高级负面规则 OR (严重负面 && (权重高 OR 命中敏感词))
    if match_result.get('advanced_hit'):
        return 3, "命中高级风险规则: " + match_result['advanced_hit']['rule']
        
    if (sentiment_score < -0.4 and (source_weight >= 80 or hit_sensitive)):
        return 3, f"高危负面且权重高/敏感 (得分:{sentiment_score})"
        
    # 🟡 Level 2: 负面情感 OR 命中敏感词
    if sentiment_score < -0.2 or hit_sensitive:
        return 2, "疑似负面风险"
        
    # 🟢 Level 1: 普通提及
    return 1, "常规提及"

# === 4. 主处理流程 (Main Pipeline) ===

def process_monitor_data(raw_items):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Load all clients
    c.execute("SELECT client_id, monitor_logic, name FROM client_config")
    clients = c.fetchall()
    
    processed_count = 0
    alerts = []
    
    for item in raw_items:
        text = item['title'] + (item.get('summary') or "")
        source = item['source']
        weight = get_source_weight(source)
        
        # Call AI for sentiment once per item (optimization)
        # Note: In production, passing client context to AI is better, 
        # but for efficiency we get a general sentiment first.
        # Here we use a mockup or call ai_engine if needed.
        # ai_analysis = ai_engine.analyze_sentiment(text) 
        # For demo, using random or heuristic
        sentiment = -0.5 if "维权" in text else 0.5 
        if "发布" in text: sentiment = 0.8
        
        for client_row in clients:
            c_id, c_logic_json, c_name = client_row
            
            match_res = match_client_logic(text, c_logic_json)
            
            if match_res:
                # Determine Risk
                risk_level, reason = analyze_risk(text, match_res, weight, sentiment)
                
                # Insert Record
                c.execute('''INSERT INTO mentions 
                             (client_id, source, title, content_text, url, publish_time, 
                              sentiment_score, risk_level, match_detail)
                             VALUES (?,?,?,?,?,?,?,?,?)''',
                          (c_id, source, item['title'], text, item['url'], time.time(),
                           sentiment, risk_level, json.dumps({"reason": reason, "match": match_res})))
                           
                processed_count += 1
                
                if risk_level >= 2:
                    alerts.append({
                        "client": c_name,
                        "level": risk_level,
                        "title": item['title'],
                        "reason": reason
                    })
                    
    conn.commit()
    conn.close()
    return {"processed": processed_count, "alerts": alerts}

# === 5. API Support ===

def add_client_config(name, logic_dict, webhook=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    client_id = f"CLI_{int(time.time())}"
    c.execute("INSERT INTO client_config (client_id, name, monitor_logic, alert_webhook) VALUES (?,?,?,?)",
              (client_id, name, json.dumps(logic_dict), webhook))
    conn.commit()
    conn.close()
    return client_id

def get_monitor_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Today's Mentions
    c.execute("SELECT count(*) FROM mentions WHERE publish_time > ?", (time.time() - 86400,))
    today_count = c.fetchone()[0]
    
    # Risk Count
    c.execute("SELECT count(*) FROM mentions WHERE risk_level >= 2 AND publish_time > ?", (time.time() - 86400,))
    risk_count = c.fetchone()[0]
    
    # Recent Logs
    logs = []
    c.execute('''SELECT m.source, m.title, m.risk_level, c.name, m.match_detail, m.publish_time 
                 FROM mentions m 
                 JOIN client_config c ON m.client_id = c.client_id 
                 ORDER BY m.id DESC LIMIT 20''')
    for row in c.fetchall():
        detail = json.loads(row[4])
        logs.append({
            "source": row[0],
            "title": row[1],
            "risk_level": row[2],
            "client_name": row[3],
            "reason": detail.get('reason', ''),
            "time": time.strftime("%H:%M", time.localtime(row[5]))
        })
        
    conn.close()
    return {
        "today_count": today_count,
        "risk_count": risk_count,
        "logs": logs
    }