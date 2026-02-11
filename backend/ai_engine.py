import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_BASE_URL")

client = None
if api_key:
    client = OpenAI(api_key=api_key, base_url=base_url)

# === 纯文本生成（DeepSeek）===
def call_deepseek_text(prompt: str) -> str:
    """
    调用 DeepSeek 返回纯文本，用于快报改写等场景。
    """
    if not client:
        return ""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是资深财经科技媒体编辑，输出简洁专业的快讯正文。"},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.3
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        print(f"DeepSeek text error: {e}")
        return ""

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
        "angles": ["请检查后端终端日志", "JSON提取可能失败", "Key可能异常"],
        "titles": [f"测试：{topic}", "系统降级为Mock模式"]
    }

def _get_mock_outline(title):
    return [
        f"【开篇】：强冲突引入 {title}", 
        "【第一部分】：现象深度剖析 (Mock数据)", 
        "【第二部分】：核心原因挖掘", 
        "【第三部分】：未来趋势预判", 
        "【结尾】：总结与升华"
    ]

# === 1. 分析话题 ===
def generate_analysis(topic):
    if not client: return _get_mock_analysis(topic)
    print(f"🧠 AI 分析中: {topic}")
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个资深主编。请以 JSON 格式输出：emotion(情绪), angles(3个角度数组), titles(5个标题数组)。不要输出任何废话。"},
                {"role": "user", "content": f"分析话题：{topic}"}
            ],
            stream=False
        )
        raw = response.choices[0].message.content
        print(f"🔍 [分析-原始返回]: {raw[:100]}...") # 只打印前100字防止刷屏
        
        clean = extract_json(raw) # 使用强力清洗
        return json.loads(clean)
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return _get_mock_analysis(topic)

# === 2. 生成大纲 ===
def generate_outline(title, angle):
    if not client: return _get_mock_outline(title)
    print(f"📝 AI 写大纲: {title}")
    
    system_prompt = """
    你是一个写作助手。请根据标题和切入点，生成一份文章大纲。
    要求：
    1. 返回 JSON 格式。
    2. 根节点 key 必须是 "sections"。
    3. value 是一个包含 5-7 个步骤的字符串数组。
    示例：{ "sections": ["步骤1...", "步骤2..."] }
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"标题：{title}\n切入点：{angle}"}
            ],
            stream=False
        )
        
        raw = response.choices[0].message.content
        print(f"🔍 [大纲-原始返回]: {raw}") # 打印全部内容以便调试
        
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
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"目标主体：{target_entity}\n文本内容：{text}"}
            ],
            stream=False
        )
        
        raw = response.choices[0].message.content
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
def _get_fallback_summary(title, content=""):
    """
    无 AI 时的真实摘要兜底：优先使用正文/摘要首段
    """
    text = (content or "").strip()
    if not text:
        text = (title or "").strip()
    # 取第一句/首段
    if "。" in text:
        first = text.split("。")[0].strip()
        text = first + "。"
    if len(text) > 80:
        text = text[:80].rstrip() + "..."
    return {
        "fact": text,
        "angle": "",
        "category": "综合",
        "tags": []
    }

def generate_news_summary(title, content=""):
    """
    根据用户专用提示词，生成 '事实' + '角度' + '分类' + '标签' json
    """
    if not client:
        return _get_fallback_summary(title, content)
    
    # 构造内容
    full_text = f"标题：{title}\n内容摘要：{content[:800]}"
    print(f"🗞️ AI 提炼新闻: {title}")

    categories_str = "社会、科技、财经、金融、汽车、大健康、新消费、创投、娱乐、宏观、出海、地方、国际、大公司、大模型、体育、军事、三农、农村、音乐、电影、情感、旅游、游戏、家居、综艺、股票、彩票、教育、文化、科学、传媒、生活"

    system_prompt = f"""
    你是一名资深主编，请对新闻进行极简提炼、选题策划及精准分类。
    
    任务：
    1. 【事实 (fact)】：对新闻进行去情绪化处理，用一句话（30字以内）直击核心事件骨架，拒绝任何废话。
    2. 【角度 (angle)】：给出 3 个不同维度的爆款选题标题建议，按 `1. xxx\\n2. xxx\\n3. xxx` 格式输出。
    3. 【分类 (category)】：基于新闻事实语义，从以下列表中选择最精准的一个分类：[{categories_str}]。
    4. 【标签 (tags)】：根据内容提取 3-5 个关键实体或主题标签（数组）。
    
    请以 JSON 格式输出：
    {{
        "fact": "30字以内的核心事件骨架...",
        "angle": "1. ...\\n2. ...",
        "category": "科技",
        "tags": ["标签1", "标签2"]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_text}
            ],
            stream=False
        )
        
        raw = response.choices[0].message.content
        clean = extract_json(raw)
        data = json.loads(clean)
        
        # Fallback defaults
        fallback = _get_fallback_summary(title, content)
        if "fact" not in data: data["fact"] = fallback["fact"]
        if "angle" not in data: data["angle"] = fallback["angle"]
        if "category" not in data: data["category"] = "综合"
        if "tags" not in data: data["tags"] = []
        
        return data

    except Exception as e:
        print(f"❌ 新闻提炼失败: {e}")
        return _get_fallback_summary(title, content)

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
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_text}
            ],
            stream=False
        )
        
        raw = response.choices[0].message.content
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
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是舆情分析专家，擅长从大量文本中提取核心话题和公众观点。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        raw = response.choices[0].message.content
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

# === 7. 通用文本生成 (Generic Text Generation) ===
def call_gemini_text(prompt, context=""):
    """
    通用文本生成函数 (Legacy name, uses current configured client)
    """
    if not client: return "Mock AI Response: Client not configured."
    
    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_prompt}
            ],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ AI Call Failed: {e}")
        return f"AI Generation Failed: {e}"