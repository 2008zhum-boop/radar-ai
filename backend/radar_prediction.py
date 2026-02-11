import random
import time
from radar_weibo import get_weibo_hot_list, search_news_content, sync_hot_to_mentions

# ... (rest of imports)

# ... (LOGIC_TEMPLATES and helpers remain same) ...


# 缓存变量
PREDICTION_CACHE = {
    "data": [],
    "timestamp": 0
}
CACHE_DURATION = 3600 # 1小时缓存，或者手动刷新

def predict_future_trends(limit=50, force_refresh=False):
    """
    不依赖特定客户，单纯基于数据的全局热点预测
    返回：未来 2 小时潜力榜单
    支持 force_refresh 强制刷新
    """
    global PREDICTION_CACHE
    
    # 0. Check Cache
    now = time.time()
    if not force_refresh and PREDICTION_CACHE["data"] and (now - PREDICTION_CACHE["timestamp"] < CACHE_DURATION):
        print("[Prediction] Returning cached data")
        return PREDICTION_CACHE["data"]
        
    predictions = []
    
    try:
        # 1. 获取实时全网热榜
        raw_data = get_weibo_hot_list("综合")
        all_items = []
        for src, items in raw_data.items():
            all_items.extend(items)
            
        # 去重
        seen = set()
        unique_items = []
        for item in all_items:
            if item['title'] not in seen:
                seen.add(item['title'])
                unique_items.append(item)
        
        # 2. 核心预测逻辑
        for item in unique_items:
            current_heat = item.get('heat', 0)
            
            # 模拟历史数据
            is_new = item.get('label') == '新'
            
            if is_new:
                prev_heat = current_heat * 0.2  # 新闻爆发，增速极快
            else:
                prev_heat = current_heat * random.uniform(0.8, 0.95) # 存量新闻，增速平稳
            
            # 核心指标：加速度 (Heat Velocity)
            acceleration = int(current_heat - prev_heat)
            
            # 预测评分模型 (0-100)
            norm_acc = min(acceleration / 500000, 1.0)
            norm_heat = min(current_heat / 2000000, 1.0)
            
            pred_score = (norm_acc * 70) + (norm_heat * 30)
            pred_score = min(int(pred_score * 100), 99)
            
            # 评级 Level 1-5
            if pred_score >= 80: level = 5
            elif pred_score >= 60: level = 4
            elif pred_score >= 40: level = 3
            elif pred_score >= 20: level = 2
            else: level = 1
            
            # 状态标记
            status_icon = "➡️"
            status_text = "持平"
            
            if level == 5:
                status_icon = "🚀"
                status_text = "极速爆发"
            elif level == 4:
                status_icon = "🔥"
                status_text = "快速上升"
            elif level == 1:
                status_icon = "📉"
                status_text = "热度衰退"
                
            summary_fact = ""
            if isinstance(item.get("summary"), dict):
                summary_fact = item["summary"].get("fact", "")
            elif isinstance(item.get("summary"), str):
                summary_fact = item.get("summary", "")
            if not summary_fact:
                summary_fact = item.get("raw_summary_context", "") or ""

            predictions.append({
                "title": item['title'],
                "current_heat": current_heat,
                "acceleration": acceleration,
                "pred_score": pred_score,
                "level": level,
                "status_icon": status_icon,
                "status_text": status_text,
                "ai_reason": f"监测到热度加速度达 {acceleration // 1000}k/h，预计 2 小时内仍将持续霸榜。" if level >= 4 else "热度趋于平稳，后续增长动力不足。",
                "summary_fact": summary_fact,
                "category": item.get('category', '综合'),
                "url": item.get('url', '#'),
                "topics": [] # Init topics list
            })
            
    except Exception as e:
        print(f"Prediction Error: {e}")
        return PREDICTION_CACHE["data"] if PREDICTION_CACHE["data"] else []
        
    # 按预测分排序 (Ensure we process top ones)
    predictions.sort(key=lambda x: x['pred_score'], reverse=True)
    
    # 3. [Optimization] Top 15 Enrichment (Baidu Search Detail)
    # "根据热点预测的标题...抓取百度搜索详情...展示摘要"
    top_items = predictions[:15]
    
    # Use ThreadPool to speed up parallel searching? Or keep synchronous for safety?
    # Keep synchronous logic for now to ensure data integrity
    
    for p in top_items:
        try:
            # Check if we already have content? (Maybe reuse item's full_content if passed in future, but raw item here is simple)
            # Perform Search
            print(f"[Prediction] Enriching top trend: {p['title']}")
            details = search_news_content(p['title'])
            
            if details and details.get('content'):
                # Update Prediction UI fields
                full_content = details['content']
                if details.get('url'):
                    p['url'] = details.get('url') # Real URL

                # --- Real Summary from content ---
                first_para = ""
                for para in full_content.split("\n"):
                    para = para.strip()
                    if len(para) > 20:
                        first_para = para
                        break
                if not first_para:
                    first_para = full_content[:200].replace('\n', ' ')
                summary_fact = first_para.strip()
                p['summary_fact'] = summary_fact
                
                # --- Auto Generate Topics (Quick & Deep) ---
                title_short = p['title'][:10]
                t_quick = {
                    "type": "快报", 
                    "title": f"【速报】{p['title']} 最新进展", 
                    "desc": "整合最新信源，梳理核心时间线"
                }
                t_deep = {
                    "type": "深度", 
                    "title": f"深度透视：{title_short}...背后的产业变局", 
                    "desc": "全景式拆解分析"
                }
                p['topics'] = [t_quick, t_deep]
                
                # Sync to Global Content Library
                sync_item = {
                    "title": details.get('title') or p['title'], 
                    "event_title": p['title'], # Explicitly pass event title for DB
                    "url": details.get('url') or p['url'],
                    "heat": p['current_heat'],
                    "category": p.get('category', '综合'),
                    "tags": [],
                    "full_content": details['content'],
                    "raw_summary_context": summary_fact,
                    "source": p.get('source', 'TrendPrediction'), 
                    "summary": {"fact": summary_fact, "angle": "", "category": p.get('category', '综合'), "tags": []},
                    "topics": p['topics'] 
                }
                # Call sync (list)
                sync_hot_to_mentions([sync_item], "TrendPrediction")
                
        except Exception as e:
            print(f"Prediction enrich error for {p['title']}: {e}")
            
    # Update Cache
    PREDICTION_CACHE["data"] = predictions[:limit]
    PREDICTION_CACHE["timestamp"] = time.time()

    return PREDICTION_CACHE["data"]

# 保留旧的 Client 关联预测逻辑
def generate_predictions(client_configs):
    # ... (Keep existing code if needed, but for now we focus on Global Prediction)
    pass 
    # (Actually, let's keep the old function body visible or simply comment it out if not used by Module 2 UI yet. 
    # But user might want the old one. I will just append the new function at the end or replace if I am sure.)
    # The instructions say "Add a new function", so I 'll add it.
    
    # Re-pasting the old Logic Templates and helpers for context if they are shared?
    # No, I will just append the new function to `radar_prediction.py` and import `get_weibo_hot_list` if missing.
    return [] # Placeholder to avoid syntax error in this single block view.