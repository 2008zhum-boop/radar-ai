def generate_news_summary(title, content=""):
    """
    根据用户专用提示词，生成 '事实' + '角度' + '分类' + '标签' json
    """
    if not client: return _get_mock_summary(title)
    
    # 构造内容
    full_text = f"标题：{title}\n内容摘要：{content[:800]}"
    print(f"🗞️ AI 提炼新闻: {title}")


    categories_str = "社会、科技、财经、金融、汽车、大健康、新消费、创投、娱乐、宏观、出海、地方、国际、大公司、大模型"
    
    # 标签库提示 (Simplified for prompt context)
    tag_hint = "标签库参考: AI, 芯片, 股市, 新能源, 医疗, 直播, 创业, 电影, 宏观... (请尽可能使用具体名词)"

    system_prompt = f"""
    你是一名资深新闻主编。请根据提供的新闻内容，输出结构化的 JSON 数据。
    
    【任务要求】
    
    1. 事实 (fact)：
       - **说明**：此字段将由系统自动填充原文首段，你无需生成。请在 JSON 中填入 "AUTO"。
    
    2. 角度 (angle) **【核心任务】**：
       - **目标**：提供 3 个**完全不同维度**的深度选题标题。每个角度必须从独特视角切入，严禁重复相似主题。
       - **必须包含的视角类型**（每个角度选一种）：
         * **商业博弈**：资本动作、并购、估值争议、商业模式颠覆
         * **技术突破/风险**：技术路线之争、核心专利、工艺迭代、安全隐患
         * **监管/政策**：合规风险、政策红利/打压、行业标准争夺
         * **竞争格局**：行业洗牌、对手反击、市占率博弈
         * **人物决策**：创始人战略、高管动荡、关键人物影响力
       
       - **严禁出现的废话模板**：
         ❌ "XXX的真相" ❌ "XXX背后的故事" ❌ "为什么XXX" ❌ "XXX：我们在谈论什么"
         ❌ "深度解析XXX" ❌ "XXX的前世今生"
       
       - **优秀范例**（必须参考此风格）：
         ✅ 《OpenAI董事会政变：非营利组织如何困住千亿估值》
         ✅ 《英伟达H100禁售令下，中国AI大厂的算力豪赌》
         ✅ 《理想汽车放弃增程：李想的战略豪赌还是被迫转型》
         ✅ 《小米造车三年亏400亿：雷军为何仍坚持all in》
       
       - **生成要求**：
         * 每个标题必须包含**具体主体**（公司/人物/产品）+ **明确冲突/矛盾点**
         * 禁止使用"如何"、"什么"等疑问词开头（除非是反问修辞）
         * 必须体现**确定性判断**或**尖锐质疑**，拒绝模棱两可
       
       - **格式**：`1. 《具体标题》\\n2. 《具体标题》\\n3. 《具体标题》`
    
    3. 分类 (category)：
       - 从以下列表中选择最精准的一个：[{categories_str}]。
    
    4. 标签 (tags)：
       - 提取 3-5 个具体的实体标签（人名、公司、产品、专有名词）。
       - 严禁泛词（如"综合"、"热点"）。
    
    请直接以标准 JSON 格式输出，不要包含 Markdown 标记：
    {{
        "fact": "AUTO",
        "angle": "1. 《...》\\n2. 《...》\\n3. 《...》",
        "category": "科技",
        "tags": ["A", "B"]
    }}
    """
    
    try:
        prompt = f"{system_prompt}\n\n{full_text}"
        response = client.generate_content(prompt)
        
        raw = response.text
        clean = extract_json(raw)
        data = json.loads(clean)
        
        # Fallback defaults
        mock = _get_mock_summary(title)
        if "fact" not in data or len(data["fact"]) < 10: data["fact"] = mock["fact"]
        if "angle" not in data: data["angle"] = mock["angle"]
        if "category" not in data: data["category"] = "综合"
        if "tags" not in data: data["tags"] = []
        
        # Post-process tags to remove "综合"
        data["tags"] = [t for t in data["tags"] if t not in ["综合", "全部", "热点", "最新"]]
        
        return data

    except Exception as e:
        print(f"❌ 新闻提炼失败: {e}")
        return _get_mock_summary(title)
