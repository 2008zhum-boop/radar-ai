import random
from radar_weibo import get_weibo_hot_list

# 定义更丰富的逻辑模板
# {keyword} = 客户名称 (如: 瑞幸)
# {event} = 真实热点新闻标题 (如: OpenAI发布Sora)
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

def generate_predictions(keywords):
    """
    输入：前端配置的客户关键词列表 (如 ['瑞幸', '特斯拉'])
    输出：结合当下真实热搜的预测选题
    """
    results = []
    
    # 1. 获取当前真实的综合热搜 (取前 20 条)
    # 我们混合 微博、36氪、百度 的数据，让素材更丰富
    real_news_pool = []
    try:
        raw_data = get_weibo_hot_list("综合") # 调用爬虫模块
        for source, items in raw_data.items():
            for item in items[:5]: # 每个来源取前5条，保证不仅是微博
                real_news_pool.append(item['title'])
    except Exception as e:
        print(f"预测模块获取热搜失败: {e}")
        real_news_pool = ["AI技术突飞猛进", "消费市场回暖", "全球股市波动"] # 兜底数据

    # 如果没有关键词，返回空 (前端会提示去添加)
    if not keywords:
        return []

    # 2. 为每个客户生成预测
    for word in keywords:
        # 为每个词生成 1-2 条策略
        count = 1 if len(keywords) > 5 else 2 
        
        for _ in range(count):
            # 随机选一个真实热点
            event_title = random.choice(real_news_pool)
            # 简化标题，去掉"爆"、"新"等后缀，只取前15个字避免标题太长
            clean_event = event_title.split(' ')[0][:20]

            # 随机选逻辑
            logic = random.choice(LOGIC_TEMPLATES)
            
            # 生成
            title = logic["title"].format(keyword=word, event=clean_event)
            reason = logic["reason"].format(keyword=word, event=clean_event)
            score = random.randint(80, 99)

            results.append({
                "keyword": word,
                "event": clean_event,
                "type": logic["type"],
                "title": title,
                "reason": reason,
                "score": score
            })
    
    # 按分数排序
    results.sort(key=lambda x: x['score'], reverse=True)
    return results