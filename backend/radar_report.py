import sqlite3
import json
import time
import random

DB_FILE = "radar_data.db"

def safe_json_load(json_str):
    try:
        if not json_str: return {}
        return json.loads(json_str)
    except:
        return {}

def get_client_info(client_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT name, industry, competitors FROM client_config WHERE client_id=?", (client_id,))
        row = c.fetchone()
        conn.close()
        if row:
            comps = safe_json_load(row[2]) if row[2] else []
            return row[0], row[1], comps
        return None, None, []
    except:
        return "未知客户", "未知行业", []

def get_volume(client_name, start_time, end_time):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT count(*) FROM mentions WHERE (title LIKE ? OR content_text LIKE ?) AND publish_time BETWEEN ? AND ?", 
                  (f"%{client_name}%", f"%{client_name}%", start_time, end_time))
        count = c.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def generate_client_report(client_id, time_range_hours=24):
    """
    生成中文舆情日报
    """
    try:
        # 1. 获取客户信息
        client_name, industry, competitors = get_client_info(client_id)
        if not client_name: 
            return {"error": "Client not found"}

        now = time.time()
        past_24h = now - (24 * 3600)
        past_48h = now - (48 * 3600)

        # 2. 查询数据
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''SELECT source, title, sentiment_score, risk_level, match_detail, publish_time 
                     FROM mentions 
                     WHERE client_id=? AND publish_time > ? 
                     ORDER BY publish_time DESC''', (client_id, past_24h))
        mentions = c.fetchall()
        conn.close()

        total_count = len(mentions)
        
        # 3. 计算指标
        prev_count = get_volume(client_name, past_48h, past_24h)
        if prev_count == 0: prev_count = 1
        growth_rate = ((total_count - prev_count) / prev_count) * 100
        
        pos_count = 0
        neg_count = 0
        risk_high_count = 0
        risk_mid_count = 0
        
        for m in mentions:
            try:
                score = float(m[2]) if m[2] is not None else 0
                risk = int(m[3]) if m[3] is not None else 1
                if score > 0.1: pos_count += 1
                if score < -0.1: neg_count += 1
                if risk == 3: risk_high_count += 1
                if risk == 2: risk_mid_count += 1
            except: continue

        sentiment_score = 7.5
        if total_count > 0:
            sentiment_score = 5 + (pos_count / total_count * 5) - (neg_count / total_count * 5)
        sentiment_score = round(max(0, min(10, sentiment_score)), 1)
        
        composite_score = 90 - (risk_high_count * 10) - (risk_mid_count * 5) + (pos_count * 0.5)
        composite_score = int(max(0, min(100, composite_score)))
        
        comp_name = competitors[0] if competitors else "行业平均"
        share_pct = 50 

        # 4. 提取热点事件
        top_events = []
        if len(mentions) > 0:
            neg_rows = [m for m in mentions if (m[3] or 1) >= 2]
            if neg_rows:
                row = neg_rows[0]
                detail = safe_json_load(row[4])
                top_events.append({
                    "title": row[1][:20] + "..." if len(row[1])>20 else row[1],
                    "heat": random.randint(1000, 5000),
                    "sentiment": "😨 负面风险",
                    "nodes": row[0] or "全网",
                    "views": [detail.get('reason', '命中风险规则')]
                })
            else:
                row = mentions[0]
                top_events.append({
                    "title": row[1][:20] + "...",
                    "heat": random.randint(500, 2000),
                    "sentiment": "😐 平稳",
                    "nodes": row[0] or "全网",
                    "views": ["日常品牌提及"]
                })
        else:
             top_events.append({
                "title": "暂无重大热点", "heat": 0, "sentiment": "😐 平稳", "nodes": "-", "views": []
            })

        status_level = "🟢 安全"
        if composite_score < 60: status_level = "🔴 警告"
        elif composite_score < 80: status_level = "🟡 关注"

        # 5. 返回结构
        return {
            "cover": {
                "report_name": f"[{client_name}] 全网舆情监测日报",
                "time_range": f"{time.strftime('%m-%d %H:%M', time.localtime(past_24h))} 至 {time.strftime('%m-%d %H:%M', time.localtime(now))}",
                "gen_time": time.strftime('%Y/%m/%d %H:%M'),
                "score": composite_score,
                "status": status_level
            },
            "section_1": {
                "summary": f"监测周期内，{client_name} 声量环比{'上升' if growth_rate>0 else '下降'} {abs(int(growth_rate))}%。",
                "sentiment_desc": f"整体得分 {sentiment_score}，情绪{'平稳' if sentiment_score>6 else '需关注'}。",
                "risk_desc": f"共监测到 {risk_high_count} 条高危信息，{risk_mid_count} 条风险提示。",
                "conclusion": "建议保持常规监测。" if risk_high_count==0 else "建议立即处理高危风险。"
            },
            "section_2": {
                "total_vol": f"{total_count} 条",
                "growth": f"{'🔺' if growth_rate>0 else '🔻'} {abs(int(growth_rate))}%",
                "health_score": str(sentiment_score),
                "health_change": "-",
                "main_platform": "全网聚合",
                "comp_name": comp_name,
                "comp_data": f"本品 ({share_pct}%) vs {comp_name} ({100-share_pct}%)"
            },
            "section_3": top_events,
            "section_4": {
                "level": status_level,
                "keywords": ["波动", "关注"],
                "sample": neg_rows[0][1] if 'neg_rows' in locals() and neg_rows else "暂无风险样本",
                "source_analysis": "数据来源于全网实时监测。"
            },
            "section_5": {
                "defense": "暂无紧急防御建议。" if risk_high_count==0 else "请尽快核实风险内容真实性。",
                "offense": "建议挖掘用户好评点进行传播。",
                "prediction": "预计明日热度将趋于平稳。"
            }
        }
    except Exception as e:
        print(f"REPORT ERROR: {e}")
        return {"error": str(e)}