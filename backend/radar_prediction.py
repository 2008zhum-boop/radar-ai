import random
import time
from radar_weibo import get_weibo_hot_list

# 定义更丰富的逻辑模板
LOGIC_TEMPLATES = [
    {
        "type": "借势营销",
        "title": "当 {keyword} 遇上“{event}”：教科书级的营销机会",
        "reason": "全网都在讨论该热点，{keyword} 若能快速跟进发布相关海报或观点，预计能获得平时 5 倍的曝光量。"
    },
    {
        "type": "深度对标",
        "title": "{event} 刷屏背后，{keyword} 的护城河在哪里？",
        "reason": "公众注意力被该事件吸引，建议 {keyword} 从差异化角度切入，强调自身在行业内的独特性。"
    },
    {
        "type": "危机/机遇",
        "title": "{event} 持续发酵，会对 {keyword} 产生蝴蝶效应吗？",
        "reason": "虽然看似无关联，但该舆情可能影响上下游产业链，建议 {keyword} 提前做好公关预案或供应链调整。"
    },
    {
        "type": "跨界联想",
        "title": "从 {keyword} 的视角，看 {event} 的底层逻辑",
        "reason": "用 {keyword} 的品牌价值观去解读当前最火的社会议题，能有效建立“行业思想领袖”的形象。"
    },
    {
        "type": "硬核分析",
        "title": "复盘 {event}：{keyword} 能学到什么？",
        "reason": "该事件的爆发路径具有极高参考价值，适合 {keyword} 内部团队进行复盘学习，或输出深度行业观察文章。"
    }
]

def calculate_acceleration(current_heat, prev_heat=None):
    """
    计算热度加速度
    """
    if prev_heat is None:
        # 模拟上一小时热度
        prev_heat = current_heat * random.uniform(0.5, 0.9)
    
    delta_h = current_heat - prev_heat
    # 假设 delta_t = 1 hour
    a = delta_h / 1.0 
    return int(a)

def get_trend_level(score, acceleration):
    """
    根据分数和加速度判定 Level 1-5
    """
    if score > 95 and acceleration > 5000:
        return 5 # P0 爆发
    if score > 90:
        return 4
    if score > 80:
        return 3
    if score > 60:
        return 2
    return 1

def generate_predictions(client_configs):
    """
    输入：client_configs list (dicts with 'brand_keywords')
    输出：结合当下真实热搜的预测选题
    """
    results = []
    
    # 1. 获取真实热搜
    real_news_pool = []
    try:
        raw_data = get_weibo_hot_list("综合") 
        for source, items in raw_data.items():
            for item in items[:8]: 
                # 模拟热度值
                heat = item.get('heat', random.randint(10000, 1000000))
                real_news_pool.append({"title": item['title'], "heat": heat})
    except Exception as e:
        print(f"预测模块获取热搜失败: {e}")
        # Fallback
        real_news_pool = [
            {"title": "OpenAI发布Sora", "heat": 500000},
            {"title": "新能源车降价潮", "heat": 300000}, 
            {"title": "咖啡价格战", "heat": 100000}
        ]

    if not client_configs:
        return []

    # 2. 生成预测
    for client in client_configs:
        # Extract keywords from JSON logic or dict
        if isinstance(client, dict):
             keywords = client.get('brand_keywords', [])
             client_name = client.get('name', 'Unknown')
        else:
             # Handle if it's passed as tuple directly from DB (legacy support)
             keywords = []
             client_name = "Unknown"

        if not keywords:
            continue
            
        # Use first brand keyword as representative
        main_keyword = keywords[0]
        
        # Determine number of predictions
        count = 2 
        
        for _ in range(count):
            # Pick a hot event
            event_obj = random.choice(real_news_pool)
            event_title = event_obj['title']
            clean_event = event_title.split(' ')[0][:20]
            
            # Logic & Score
            logic = random.choice(LOGIC_TEMPLATES)
            base_score = random.randint(70, 95)
            
            # Calculate Acceleration (Simulated)
            acc = calculate_acceleration(event_obj['heat'])
            
            # Boost score if acceleration is high
            if acc > 10000:
                base_score += 4
                
            base_score = min(base_score, 99)
            
            level = get_trend_level(base_score, acc)
            
            # Rocket Flag
            is_rocket = (level >= 4 and acc > 5000)

            results.append({
                "client": client_name,
                "keyword": main_keyword,
                "event": clean_event,
                "type": logic["type"],
                "title": logic["title"].format(keyword=main_keyword, event=clean_event),
                "reason": logic["reason"].format(keyword=main_keyword, event=clean_event),
                "score": base_score,
                "level": level,
                "acceleration": acc,
                "is_rocket": is_rocket
            })
    
    # Sort by Score DESC
    results.sort(key=lambda x: x['score'], reverse=True)
    return results