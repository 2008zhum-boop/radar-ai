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