import os
import json
import re
import time
import requests
from typing import Optional

# ================= 🚀 核心配置 =================

# 1. SiliconFlow Key
#SILICON_KEY = "sk-xhlggbibvssprqgoadkdpxdnsbpzdeqfpkcrnhhnuohowrpd"

# 2. 模型选择
SILICON_MODEL_MAIN = "Qwen/Qwen2.5-72B-Instruct" 
SILICON_MODEL_BACKUP = "deepseek-ai/DeepSeek-V3"

# 3. Google 配置
GEMINI_API_KEY = "AIzaSyCIrIYeRTujYGAina6k67YKqldr1PiOx7Y"
GEMINI_MODEL = "gemini-2.0-flash"

# 4. 代理地址
PROXY_URL = "socks5h://127.0.0.1:9091"

# =============================================

def get_proxies(force_proxy=False):
    if force_proxy:
        return { "http": PROXY_URL, "https": PROXY_URL }
    else:
        return { "http": None, "https": None }

def call_silicon_raw(prompt, model_name):
    if not SILICON_KEY: return None
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = { "Authorization": f"Bearer {SILICON_KEY}", "Content-Type": "application/json" }
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=20, proxies=get_proxies(False))
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content']
        elif resp.status_code == 402:
            print(f"⚠️ {model_name} 余额不足 (402)，跳过...")
        else:
            print(f"⚠️ SiliconFlow ({model_name}) Error: {resp.text[:100]}")
    except Exception as e: 
        print(f"⚠️ SF Network Error: {e}")
    return None

def call_gemini(prompt):
    if not GEMINI_API_KEY: return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = { "contents": [{ "parts": [{"text": prompt}] }] }
    try:
        for i in range(2):
            if i > 0: time.sleep(1)
            resp = requests.post(url, headers=headers, json=data, timeout=30, proxies=get_proxies(True))
            if resp.status_code == 200:
                res = resp.json()
                if "candidates" in res: return res["candidates"][0]["content"]["parts"][0]["text"].strip()
    except: pass
    return None

def call_ai(prompt):
    res = call_silicon_raw(prompt, SILICON_MODEL_MAIN)
    if res: return res
    print(f"⚠️ 主模型失败，尝试备用...")
    res = call_silicon_raw(prompt, SILICON_MODEL_BACKUP)
    if res: return res
    print("⚠️ SiliconFlow 全线失败，切换 Google Gemini...")
    return call_gemini(prompt)

def _safe_json(text: Optional[str]):
    if not text: return None
    try:
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if match: text = match.group(0)
        return json.loads(text)
    except: return None

# ================= 业务逻辑 =================

def generate_news_summary(title, content=""):
    full_text = f"标题：{title}\n内容简述：{content[:1000]}"
    
    # 🔥 核心升级：增加 emotions 字段，要求返回 5 种具体情绪
    prompt = f"""
    你是一名资深舆情分析师。请分析这条新闻的选题价值，并精准判断其蕴含的情绪成分。
    
    请返回严格的 JSON 格式：
    {{
        "fact": "100字以内的深度摘要",
        "score": 0-100 (选题价值),
        "trend": "上升/平稳/下降",
        "reason": "推荐理由",
        "category": "从以下选择: [综合, 大模型, 科技, 财经, 金融, 汽车, 大健康, 新消费, 创投, 出海, 大公司, 国际]",
        "tags": ["标签1"],
        "sentiment": {{ "positive": 20, "neutral": 60, "negative": 20 }},
        "emotions": {{
            "anxiety": 10,   // 焦虑 (如裁员、制裁、亏损)
            "anger": 5,      // 愤怒 (如丑闻、侵权、不公)
            "sadness": 5,    // 悲伤 (如逝世、失败、灾难)
            "excitement": 10,// 兴奋 (如突破、新高、发布)
            "sarcasm": 0     // 嘲讽 (如吃瓜、反转、打脸)
        }}
    }}
    
    注意：
    1. sentiment 三项之和必须为 100。
    2. emotions 的五项数值代表强度(0-100)，不需要加起来等于100，但要符合逻辑。若新闻很平淡，所有情绪值都应较低。
    
    新闻：
    {full_text}
    """
    
    res = call_ai(prompt)
    data = _safe_json(res)
    
    if data: return data
    
    return {}

# 兼容接口
def call_openrouter(prompt): return call_ai(prompt)
def analyze_topic_deeply(topic): return _safe_json(call_ai(f"分析话题：{topic}，返回json")) or {}
def generate_full_outline(topic, angle): return _safe_json(call_ai(f"写大纲：{topic}，角度{angle}，返回json")) or []
def generate_smart_outline(title, angle, context=""): return _safe_json(call_ai(f"详细大纲：{title}，返回json")) or {}
def generate_full_article(title, outline, context=""): return call_ai(f"写文章：{title}，大纲{outline}") or ""
