import os
import google.generativeai as genai
import json
import re
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

load_dotenv()

# Use Google Key
api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyCIrIYeRTujYGAina6k67YKqldr1PiOx7Y")

client = None
if api_key:
    genai.configure(api_key=api_key)
    # 2026-02-06: 恢复 Gemini 调用
    client = genai.GenerativeModel('gemini-1.5-flash') 


# === 🛡️ 强力清洗函数 (本次升级重点) ===
def extract_json(text):
    """
    从乱七八糟的 AI 回复中，精准提取出 JSON 部分
    """
    if not text: return "{}"
    
    # 1. 尝试找到第一个 '{' 和最后一个 '}'
    # re.DOTALL 让 . 可以匹配换行符，防 AI 换行输出
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    
    # 2. 如果没找到大括号，尝试清理 markdown 标记后返回
    text = re.sub(r'```json', '', text)
    text = re.sub(r'```', '', text)
    return text.strip()

# === 兜底数据 ===
def _get_mock_analysis(topic):
    return {
        "topic": topic,
        "emotion": "模拟数据",
        "strategies": [
            { "title": f"深度观察：{topic}", "angle": "深度观察", "reason": "全网热议方向", "icon": "👁️" },
            { "title": f"{topic} 背后的商业逻辑", "angle": "商业分析", "reason": "适合财经受众", "icon": "📊" },
            { "title": f"为什么大家都在谈论 {topic}？", "angle": "舆论解构", "reason": "热点归因", "icon": "🔥" }
        ]
    }

def _get_mock_outline(title):
    return [
        {
            "title": f"【开篇】强冲突引入：{title}", 
            "sub_points": ["核心冲突点描述", "当前舆论现状", "文章核心观点抛出"]
        },
        {
            "title": "【第一部分】现象深度剖析",
            "sub_points": ["数据支撑（Mock）", "典型案例分析", "用户/市场反应"]
        },
        {
            "title": "【第二部分】核心原因挖掘",
            "sub_points": ["表面原因vs深层原因", "利益链条分析", "行业背景影响"]
        },
        {
            "title": "【第三部分】未来趋势预判",
            "sub_points": ["短期影响预测", "长期格局演变", "可能的变数"]
        },
        {
            "title": "【结尾】总结与升华",
            "sub_points": ["重申观点", "对读者的建议/呼吁", "金句收尾"]
        }
    ]

# === 1. 分析话题 ===

# === 1. 分析话题 ===
def generate_analysis(topic, hot_context=None):
    if not client: return _get_mock_analysis(topic)
    print(f"🧠 AI 分析中: {topic} (Context: {len(hot_context) if hot_context else 0})")
    
    context_str = ""
    if hot_context and isinstance(hot_context, list):
         context_str = f"\n当前全网舆论热点参考：{', '.join(hot_context[:10])}\n请尝试将话题与上述热点进行关联延伸，寻找具有流量潜力的切入点。"
    
    try:
        import random
        prompt = f"""你是一个资深主编。请分析用户话题，并结合当前舆论环境，生成3个**差异化极大**且极具吸引力的创作切入点（Strategies）。
要求：
1. 返回 JSON 格式，根对象包含：emotion (情绪词), strategies (数组)。
2. strategies 数组中每个对象包含：
   - title: 拟定的爆款标题（必须吸引眼球，拒绝平庸）
   - angle: 切入点名称（如“深度观察”、“反直觉”、“资本博弈”、“行业黑幕”等，**请发挥创意，不要重复**）
   - reason: 推荐理由（结合热点或行业趋势）
   - icon: 一个相关的emoji图标
3. 必须结合提供的热点上下文（如果有）进行发散。
4. **每次生成都必须尝试全新的视角，避免陈词滥调。**

分析话题：{topic}{context_str}\n\n(Random Seed: {random.random()})"""

        response = client.generate_content(prompt)
        raw = response.text
        print(f"🔍 [分析-原始返回]: {raw[:100]}...") 
        
        clean = extract_json(raw) 
        return json.loads(clean)
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return _get_mock_analysis(topic)

# === 2. 生成大纲 ===
def generate_outline(title, angle):
    if not client: return _get_mock_outline(title)
    print(f"📝 AI 写大纲: {title}")
    
    system_prompt = """
    你是一个专业财经科技媒体的主编。请根据标题和特定切入点（Angle），设计一份逻辑严密且富有洞察力的文章大纲。
    
    核心要求：
    1. **拒绝死板的模板**：严禁使用“第一章、第二章”这种教科书式的死板标题。小标题必须具有新闻性和观点性（例如：“泡沫破裂的前夜”、“巨头的隐秘布局”）。
    2. **不仅是列举**：大纲必须体现逻辑递进（现象 -> 原因 -> 利益博弈 -> 终局推演）。
    3. **JSON格式返回**：根节点 "sections"，包含 "title" 和 "sub_points"。
    
    示例格式：
    {
        "sections": [
            { "title": "【切面】....", "sub_points": ["...", "..."] },
            { "title": "【深挖】....", "sub_points": ["...", "..."] }
        ]
    }
    """
    
    try:
        import random
        prompt = f"{system_prompt}\n\n标题：{title}\n切入点：{angle}\n\n(Random Seed: {random.random()})"
        response = client.generate_content(prompt)
        
        raw = response.text
        print(f"🔍 [大纲-原始返回]: {raw[:100]}...") # 打印开头
        
        clean = extract_json(raw) # 使用强力清洗
        data = json.loads(clean)
        
        # 智能提取数据
        if "sections" in data:
            return data["sections"]
        # 找不到 sections 就找第一个列表
        for val in data.values():
            if isinstance(val, list):
                return val
                
        return _get_mock_outline(title)

    except Exception as e:
        print(f"❌ 大纲失败: {e}")
        return _get_mock_outline(title)

# === 2b. 根据大纲生成全文（财经科技行业媒体风格）===
def _get_mock_article(title):
    return f"""# {title}

（此为模拟正文。请配置 GOOGLE_API_KEY 后使用 AI 生成。）

【开篇】强冲突引入，点明热点与争议。
【主体】现象深度剖析、核心原因挖掘、行业影响分析。
【结尾】总结与趋势预判，呼应财经科技视角。
"""

def generate_article_from_outline(title, outline, context=""):
    """
    根据大纲生成完整文章，面向财经科技行业媒体。
    outline: 可以是字符串数组，或 [{ "title": "章节名", "sub_points": [] }] 结构
    """
    if not client:
        return _get_mock_article(title)
    print(f"✍️ AI 成文: {title}")
    # 将 outline 转为可读文本
    if isinstance(outline, list) and outline and isinstance(outline[0], dict):
        outline_text = "\n".join(
            f"{i+1}. {s.get('title', '')} " + (" ".join(s.get("sub_points", [])) or "")
            for i, s in enumerate(outline)
        )
    elif isinstance(outline, list):
        outline_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(outline))
    else:
        outline_text = str(outline)
    system_prompt = """你是一位拥有深厚行业积淀的钛媒体（TMTPost）资深主笔。你擅长观察技术变革背后的商业底层逻辑，风格冷峻、专业，文字具有穿透力，能够平衡商业利益与人文思考。

Role / 角色设定:
- 钛媒体资深财经科技专栏作家。
- 风格：冷峻、专业、数据驱动、具有穿透力。

Tone & Style / 钛媒体调性指南:
1. **专业且犀利**：避免平铺直叙，多探讨“为什么”而非单纯描述“是什么”。
2. **商业语境**：灵活运用商业术语（如：飞轮效应、存量博弈、范式转移、估值重构等），但拒绝堆砌词藻。
3. **批判性思维**：在肯定趋势的同时，必须指出潜在风险、行业壁垒或泡沫。
4. **排版规范**：结构清晰，每节标题要具有“高度概括性”和“冲击力”。

Article Structure / 文章结构要求:
1. **标题优化**：即使给定了标题，也请在文章最开头推荐 1-2 个更具吸引力的备选标题（以 > 引用格式展示）。
2. **核心摘要**：开头需包含 150 字以内的核心摘要，概括核心观点。
3. **强力引言（Lead Paragraph）**：
   - 文章开头必须包含高质量导语（200-300字）。
   - 以行业重大事件或细微的市场异动切入，引出背后的深层矛盾。
4. **正文（深度拆解）**：
   - 严格遵循提供的大纲进行分段论述。
   - 包含对竞品的横向对比分析。
   - 数据描述需精准，观点需有事实依据。
5. **钛度结语**：
   - 给出独家判断。拒绝鸡汤，要给出对行业从业者的警示或策略建议。

Constraints / 约束条件:
- 严禁出现“在当今社会”、“不得不说”、“笔者认为”等学生气词汇。
- 使用 Markdown 格式渲染。
- 字数：1500 - 2500 字。
"""
    user_content = f"标题：{title}\n\n大纲结构：\n{outline_text}\n\n补充背景/上下文：{context[:1000] if context else '无'}"
    try:
        prompt = f"{system_prompt}\n\n{user_content}"
        # For long generation
        response = client.generate_content(prompt)
        raw = response.text
        return (raw or "").strip() or _get_mock_article(title)
    except Exception as e:
        print(f"❌ 成文失败: {e}")
        return _get_mock_article(title)

# === 3. 舆情风险研判 (Risk Assessment) ===
def analyze_risk_assessment(text, target_entity):
    """
    分析文本对自己品牌的风险程度，提取真实的风险关键词
    """
    if not client: 
        return {
            "score": 0,
            "risk_keywords": [],
            "reason": "Mock模式: 未配置AI"
        }
        
    print(f"⚠️ AI 舆情研判: {target_entity} in {text[:20]}...")
    
    system_prompt = """
    你是一个资深舆情分析师。请分析给定文本对目标主体(target)的舆情风险。
    请以 JSON 格式输出：
    - score: 情感倾向分数，范围 -1.0(极度负面/危机) 到 1.0(极度正面/利好)，0为中性。
    - risk_keywords: 字符串数组，提取1-3个核心风险关键词（如"刹车失灵"、"财务造假"），如果是正面或无风险则为空数组。
    - reason: 简短的一句话判断依据。
    """
    
    try:
        prompt = f"{system_prompt}\n\n目标主体：{target_entity}\n文本内容：{text}"
        response = client.generate_content(prompt)
        
        raw = response.text
        clean = extract_json(raw)
        data = json.loads(clean)
        
        # 兜底检查
        if "score" not in data: data["score"] = 0
        if "risk_keywords" not in data: data["risk_keywords"] = []
        
        return data

    except Exception as e:
        print(f"❌ 研判失败: {e}")
        return {
            "score": 0, 
            "risk_keywords": [],
            "reason": f"AI分析异常: {str(e)}"
        }

# === 4. 新闻核心提炼 (List Summary) ===
def _get_mock_summary(title):
    import random
    
    # 随机事实模板
    fact_templates = [
        f"{title} 引发广泛关注，各方观点不一，核心争议点集中在行业影响上。",
        f"关于 {title} 的讨论持续升温，数据表明这可能是一个重要的转折点。",
        f"最新消息显示 {title} 正成为焦点，专家建议保持理性看待。",
        f"{title} 事件背后隐藏着深层次的商业逻辑，值得深挖。",
        f"随着 {title} 的发酵，公众对于相关领域的关注度达到新高。"
    ]
    
    # 随机角度模板 (A/B/C 组)
    angle_groups = [
        [
            f"1. 《深度复盘：{title} 的前世今生》",
            f"2. 《{title}：资本狂欢还是技术革命？》",
            f"3. 《当我们在谈论 {title} 时，我们在谈论什么》"
        ],
        [
            f"1. 《{title} 背后的隐秘利益链条》",
            f"2. 《被误读的 {title}：真相究竟是什么？》",
            f"3. 《独家分析：{title} 对普通人的影响》"
        ],
        [
            f"1. 《{title}：一场注定要发生的变革》",
            f"2. 《风口之下的 {title}：谁是赢家？》",
            f"3. 《{title} 之后，行业将何去何从？》"
        ],
        [
             f"1. 《{title} 爆火背后的底层逻辑》",
             f"2. 《一文看懂 {title} 的核心争议》",
             f"3. 《{title}：或许是今年最大的机会》"
        ]
    ]
    
    selected_angles = random.choice(angle_groups)
    
    return {
        "fact": random.choice(fact_templates),
        "angle": "\n".join(selected_angles),
        "category": "综合",
        "tags": ["热点", "趋势"]
    }

def generate_news_summary(title, content=""):
    """
    根据用户专用提示词，生成 '事实' + '角度' + '分类' + '标签' json
    """
    if not client: return _get_mock_summary(title)
    
    # 构造内容
    full_text = f"标题：{title}\n内容摘要：{content[:800]}"
    print(f"🗞️ AI 提炼新闻: {title}")


    categories_str = "全部、科技、财经、金融、汽车、大健康、新消费、创投、宏观、出海、地方、国际、大公司、大模型"
    
    # 标签库提示 (Simplified for prompt context)
    tag_hint = "标签库参考: AI, 芯片, 股市, 新能源, 医疗, 直播, 创业, 电影, 宏观... (请尽可能使用具体名词)"

    system_prompt = f"""
    你是一名资深新闻主编。请根据提供的新闻内容，输出结构化的 JSON 数据。
    
    【任务要求】
    
    1. 事实 (fact)：
       - **目标**：生成一段约 200 字的纯净新闻摘要。
       - **严格禁止**：不要出现“事件背景”、“值得深挖”、“最新消息”、“据报道”、“小编认为”等任何修饰性前缀或元语言。
       - **内容**：直接陈述核心事实（时间、地点、人物、事件、关键数据、结果）。保持客观、冷静、紧凑。
    
    2. 角度 (angle)：
       - **目标**：提供 3 个不同切入点的选题标题（Title Only）。
       - **风格**：专业、深度、产业视角。**拒绝标题党**（如“震惊”、“吓尿”），**拒绝废话**（如“我们在谈论什么”）。
       - **示例**：
         - 产业/市场视角：《比亚迪降价对合资车企的降维打击》
         - 技术/趋势视角：《Sora 模型背后的世界模拟器路》
         - 人物/商业决策视角：《理想汽车李想的“反共识”产品哲学》
       - **格式**：`1. xxx\\n2. xxx\\n3. xxx`
    
    3. 分类 (category)：
       - 从以下列表中选择最精准的一个：[{categories_str}]。
    
    4. 标签 (tags)：
       - 提取 3-5 个具体的实体标签（人名、公司、产品、专有名词）。
       - 严禁泛词（如“综合”、“热点”）。
    
    请直接以标准 JSON 格式输出，不要包含 Markdown 标记：
    {{
        "fact": "...",
        "angle": "1. ...\\n2. ...\\n3. ...",
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

# === 5. 事件脉络梳理 (Event Pulse) ===
def _get_mock_pulse(title):
    return {
        "facts": f"{title} 的核心事实概要（模拟数据）。",
        "controversy": "1. 争议点一：... \n2. 争议点二：...",
        "timeline": [
            {"time": "6小时前", "event": "事件首次曝光，关注度上升"},
            {"time": "2小时前", "event": "相关方作出回应，引发讨论"},
            {"time": "30分钟前", "event": "热度持续发酵，多方观点博弈"}
        ],
        "suggestion": "建议从争议点切入进行深度分析。"
    }

def generate_event_pulse(title, content=""):
    """
    生成事件脉络、争议点、时间线和建议
    """
    if not client: return _get_mock_pulse(title)
    
    print(f"📈 AI 脉络分析: {title}")
    
    full_text = f"标题：{title}\n内容摘要：{content[:1000]}"
    
    system_prompt = """
    你是一个资深调查记者。请对给定的热点事件梳理出清晰的脉络。
    
    请以 JSON 格式输出：
    {
        "facts": "核心事实简述（50字内）",
        "controversy": "列出1-2个核心争议点或疑问点",
        "timeline": [
            {"time": "推测时间点 (如'2小时前'或具体日期)", "event": "关键节点事件描述"},
            {"time": "...", "event": "..."}
        ],
        "suggestion": "一句话创作切入建议"
    }
    
    要求：
    1. timeline 数组包含 3 个关键节点。
    2. 基于常识推理或内容进行合理的因果推演。
    """
    
    try:
        prompt = f"{system_prompt}\n\n{full_text}"
        response = client.generate_content(prompt)
        
        raw = response.text
        print(f"🔍 [脉络-原始返回]: {raw[:100]}...")
        clean = extract_json(raw)
        data = json.loads(clean)
        
        # Validation
        if "facts" not in data or "timeline" not in data:
            return _get_mock_pulse(title)
            
        return data
        
    except Exception as e:
        print(f"❌ 脉络分析失败: {e}")
        return _get_mock_pulse(title)


# === 6. 热词提取 (Keyword Extraction) ===
def extract_keywords_from_content(content: str, max_keywords: int = 8):
    """
    从舆情内容中提取核心热词及AI观点
    """
    if not client:
        # 无AI时使用jieba分词
        import jieba
        from collections import Counter
        words = [w for w in jieba.cut(content) if len(w) >= 2]
        word_counts = Counter(words).most_common(max_keywords)
        return [
            {"keyword": word, "opinion": f"出现{count}次", "count": count}
            for word, count in word_counts
        ]
    
    try:
        prompt = f"""分析以下舆情内容，提取6-8个核心热词，并为每个热词生成简短的AI观点总结。

内容:
{content[:3000]}

请返回JSON格式:
{{
  "keywords": [
    {{"keyword": "关键词1", "opinion": "AI观点: 一句话总结用户对该词的看法"}},
    {{"keyword": "关键词2", "opinion": "AI观点: 一句话总结"}}
  ]
}}

注意:
1. 关键词应该是内容中讨论最频繁的话题
2. AI观点要简洁，不超过20个字
3. 按重要性排序，最重要的排在前面
"""
        
        response = client.generate_content(prompt)
        
        raw = response.text
        clean = extract_json(raw)
        data = json.loads(clean)
        
        return data.get("keywords", [])[:max_keywords]
        
    except Exception as e:
        print(f"❌ 热词提取失败: {e}")
        # Fallback to jieba
        import jieba
        from collections import Counter
        words = [w for w in jieba.cut(content) if len(w) >= 2]
        word_counts = Counter(words).most_common(max_keywords)
        return [
            {"keyword": word, "opinion": f"出现{count}次", "count": count}
            for word, count in word_counts
        ]
# === 7. 智能润色 (Smart Polish) ===
def _get_mock_polish_result(text_preview):
    return {
        "title": "深度访谈：重塑未来的力量",
        "summary": "本文基于对行业专家的深度访谈，探讨了在快速变化的商业版图中，创新思维与用户至上理念如何成为企业破局的关键。",
        "content": f"""<h2>核心观点一：打破常规</h2>
<p>即使{text_preview[:20]}... 专家指出，唯有创新才能在激烈的市场竞争中立足。</p>
<p>这不仅仅是技术层面的革新，更是思维模式的转变。企业需要跳出舒适区，勇于尝试新的商业模式。</p>
<br>
<h2>核心观点二：用户至上</h2>
<p>我们看到，{text_preview[20:40] if len(text_preview)>40 else "市场反馈"}... 真正理解用户需求，比单纯堆砌功能更为重要。</p>
<p>用户不仅仅是消费者，更是产品的共建者。倾听用户的声音，是产品迭代的最佳指引。</p>
<br>
<h2>结语</h2>
<p>未来的道路充满挑战，但也蕴含机遇。让我们携手共进，创造辉煌。</p>"""
    }

def polish_interview_notes(content: str, instruction: str = None):
    """
    将采访速记润色为长文，返回 { title, summary, content }
    """
    if not client:
        return _get_mock_polish_result(content)
    
    print(f"💅 AI 润色中，长度: {len(content)}")
    
    # Base system prompt with JSON formatting requirements
    base_prompt = """你是一位钛媒体（TMTPost）的资深特稿编辑。我将提供一份采访速记/草稿，请你将其润色改写成一篇深度产业观察文章。
    
请返回 JSON 格式：
{
    "title": "符合钛媒体调性的专业大标题（突出产业洞察和犀利观点）",
    "summary": "200字以内的文章摘要（凝练核心价值与行业影响）",
    "content": "HTML格式的正文，包含 <h2>小标题</h2>、<p>段落</p> 等标签。字数要求 1500-2000 字。"
}"""

    # If instruction is provided, use it as the main guideline. 
    # Otherwise, fallback to the default rigorous logic.
    if instruction:
        writing_logic = f"""
写作要求 (基于用户指令):
{instruction}

通用要求：
1. 必须返回 JSON 格式。
2. 保持 HTML 标签结构。
"""
    else:
        writing_logic = """
写作逻辑与要求：
1. **结构重组**：必须严格遵循【趋势洞察 -> 企业落地 -> 圆桌共识】的逻辑进行重构。
    - **趋势洞察**：从行业宏观视角切入，点出 AI 时代知识治理的紧迫性与核心价值。
    - **企业落地**：结合嘉宾分享的实践经验，详细阐述具体落地路径、挑战与解决方案。
    - **圆桌共识**：升华主题，提炼行业共识，展望未来趋势。
2. **语言风格**：
    - **TMTPost 调性**：科技产业深度、犀利洞察、专业精炼。
    - **去口语化**：彻底剔除“嗯、呃、然后”等口语，将对话转化为逻辑严密的书面表达。
    - **犀利点评**：适当增加“钛媒体注”或主编点评视角的金句，强化文章的观点力度。
3. **内容优化**：
    - **提炼洞察**：不要记流水账，要提炼嘉宾观点背后的行业逻辑。
    - **突出价值**：重点强化“AI时代知识治理”的核心价值。
    - **数据与案例**：保留并突出原文中的关键数据和具体案例。
"""

    system_prompt = f"{base_prompt}\n{writing_logic}"
    
    try:
        prompt = f"{system_prompt}\n\n采访速记内容：\n\n{content[:5000]}"
        response = client.generate_content(prompt)
        raw = response.text
        clean = extract_json(raw)
        return json.loads(clean)
    except Exception as e:
        print(f"❌ 润色失败: {e}")
        return _get_mock_polish_result(content)

def refine_article_with_chat(current_content, instruction):
    """
    根据用户指令优化文章内容
    """
    if not client:
        return f"{current_content}\n<p>（Mock：已根据指令“{instruction}”优化内容）</p>"
        
    print(f"🤖 AI 优化文章: {instruction}")
    
    system_prompt = """你是一位钛媒体（TMTPost）的专业文章优化助手。请根据用户的修改指令，对当前文章内容进行调整或重写。

核心调性要求：
1. **科技产业深度**：保持对行业趋势的敏锐洞察，拒绝肤浅的描述。
2. **犀利洞察**：语言要干练、有力，直击问题本质。
3. **专业质感**：使用准确的行业术语，逻辑严密，行文流畅。

请直接返回修改后的 HTML 正文内容，不要包含 Markdown 标记或 JSON 格式。
保持原有的 HTML 标签结构（h2, p 等）。"""

    try:
        prompt = f"{system_prompt}\n\n用户指令：{instruction}\n\n当前文章内容：\n{current_content[:3000]}"
        response = client.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ 优化失败: {e}")
        return current_content


def generate_cover_image(title, content=""):
    """
    根据文章内容生成封面图
    Note: Google Gemini Python SDK current version (or the standard free tier) 
    might not support text-to-image generation directly. 
    We will mock this or return a visual prompt.
    """
    print(f"🎨 AI 生成封面图 Prompt中: {title}")
    
    # 1. Generate Prompt
    prompt_gen_prompt = f"""你是一个视觉艺术总监。请根据用户的文章标题和摘要，设计一个富有科技感、现代感且抽象的封面图生成提示词(Prompt)。
要求：
1. 英文描述。
2. 包含具体的艺术风格（如：Cyberpunk, Minimalist, 3D Render, Abstract tech lines）。
3. 适合作为 16:9 的文章封面。
4. 直接输出提示词，不要包含其他解释。

文章标题：{title}
内容摘要：{content[:500]}"""
    
    try:
        if client:
            resp = client.generate_content(prompt_gen_prompt)
            visual_prompt = resp.text
            print(f"🎨 [封面Prompt]: {visual_prompt}")
            
            # Since we can't call DALL-E anymore with Google Key, and Gemini Image gen depends on model 'gemini-pro-vision' 
            # (which is image-to-text) or specialized Imagen endpoints not always in `google-generativeai`.
            # We will use Unsplash with a keyword extracted from title.
            pass
    except Exception:
        pass

    # Fallback to Unsplash
    import random
    keyword = "technology" 
    # maybe extract keyword from title? simple logic
    for k in ['AI', 'Chip', 'Finance', 'Auto', 'Space']:
        if k in title: keyword = k; break
        
    return f"https://source.unsplash.com/1600x900/?{keyword},{random.randint(1,100)}"


def smart_parse_topic(user_input: str) -> str:
    """
    从用户的自然语言指令中提取核心选题/话题。
    例如："写一篇关于百度芯片的文章" -> "百度芯片"
    """
    if not client:
        t = user_input.replace("写一篇", "").replace("的文章", "").replace("关于", "").strip()
        return t if t else user_input
    
    try:
        prompt = f"""你是一个智能写作助手。请分析用户的输入，提取出用户真正想写的核心话题或主题（Topic）。
规则：
1. 去除所有指令性词汇，如“帮我写一篇”、“关于”、“你觉得”、“分析一下”、“写个文章”等。
2. 即使包含“你觉得xxx怎么样”，核心话题也是“xxx”。
3. 仅返回提炼后的核心话题词，不要包含标点符号或其他解释。
4. 如果无法提取（例如输入为空或无意义），返回原输入。

示例：
输入：写一篇关于百度芯片的文章
输出：百度芯片

输入：你觉得现在的股市怎么样
输出：当前股市行情

输入：帮我分析下马斯克的最新动态
输出：马斯克最新动态

输入: {user_input}
输出:"""
        
        completion = client.generate_content(prompt)
        return completion.text.strip()
    except Exception as e:
        print(f"Topic parsing error: {e}")
        return user_input

