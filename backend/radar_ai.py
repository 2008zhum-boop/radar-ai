"""
AI 创作：通过 OpenRouter 调用大模型（如 Gemini）分析话题、生成选题策略和大纲。
"""
import os
import json
import re
import requests
from typing import Optional

# ================= 配置区域 =================
# 优先从环境变量读取，便于部署时替换
OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY",
    "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"
)
API_BASE = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-2.0-flash-lite-preview-02-05:free"
# ===========================================


def call_openrouter(prompt: str) -> Optional[str]:
    """
    通用函数：调用 OpenRouter API
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "SmartEdit"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "你是钛媒体的资深主编，擅长商业分析和选题策划。请务必只返回合法的 JSON 格式数据，不要包含 Markdown 代码块标记（如 ```json）。"
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "top_p": 0.9
    }

    try:
        response = requests.post(API_BASE, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            if "choices" in res_json and len(res_json["choices"]) > 0:
                content = res_json["choices"][0]["message"]["content"]
                content = re.sub(r"^```json\s*", "", content)
                content = re.sub(r"^```\s*", "", content)
                content = re.sub(r"\s*```$", "", content)
                return content.strip()
            else:
                print(f"API Response Empty: {res_json}")
                return None
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request Failed: {e}")
        return None


def analyze_topic_deeply(topic: str, instruction: Optional[str] = None) -> dict:
    """
    真 AI：深度分析话题，返回选题策略（角度、标题、理由、大纲要点）。
    支持用户指令 instruction 进行调整。
    """
    print(f"正在 AI 分析话题: {topic}, 指令: {instruction} ...")

    base_prompt = f"请针对话题“{topic}”，生成一份深度选题分析报告。"
    if instruction:
        base_prompt += f"\n用户对选题有特别要求（或基于之前的反馈）：{instruction}。请根据此要求调整你的分析和推荐策略。"

    prompt = f"""
    {base_prompt}
    必须严格按照以下 JSON 格式返回，不要有多余废话：
    {{
        "topic": "{topic}",
        "deep_analysis": {{
            "event": "事件简述：用简练的语言概括核心事件脉络（100字以内）",
            "industry": "行业透视：分析该事件对所在行业的影响、格局变化或潜在机会",
            "thinking": "深度思辨：挖掘事件背后的底层逻辑、人性、资本博弈或社会意义",
            "future": "未来展望：预测该事件或赛道的短期及长期发展趋势",
            "conclusion": "结语：一句话总结核心洞察"
        }},
        "analysis": "（保留字段）简述舆论现状",
        "strategies": [
            {{
                "angle": "切入角度名称(如：深度商业分析)",
                "icon": "emoji图标",
                "title": "拟定的爆款标题",
                "reason": "推荐这个角度的理由(50字以内)",
                "outline": ["一级小标题1", "一级小标题2", "一级小标题3", "一级小标题4"]
            }},
            {{
                "angle": "切入角度名称(如：反直觉思考)",
                "icon": "emoji图标",
                "title": "拟定的爆款标题",
                "reason": "推荐这个角度的理由",
                "outline": ["一级小标题1", "一级小标题2", "一级小标题3", "一级小标题4"]
            }},
            {{
                "angle": "切入角度名称(如：行业盘点)",
                "icon": "emoji图标",
                "title": "拟定的爆款标题",
                "reason": "推荐这个角度的理由",
                "outline": ["一级小标题1", "一级小标题2", "一级小标题3", "一级小标题4"]
            }}
        ]
    }}
    """

    json_str = call_openrouter(prompt)
    if not json_str:
        return _get_mock_data(topic, instruction)

    try:
        return json.loads(json_str)
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        return _get_mock_data(topic, instruction)


def generate_full_outline(topic: str, angle: str) -> list:
    """
    真 AI：根据选定角度生成详细大纲。
    返回列表，每项为 {"h1": "小标题", "text": "写作思路简述"}。
    """
    print(f"正在生成大纲: {topic} - {angle} ...")
    prompt = f"""
    请为话题“{topic}”写一份详细的文章大纲，切入角度是“{angle}”。
    返回 JSON 格式：
    [
        {{"h1": "引言：(小标题内容)", "text": "简述引言部分的写作思路..."}},
        {{"h1": "核心观点：(小标题内容)", "text": "阐述核心论点..."}},
        {{"h1": "深度论证：(小标题内容)", "text": "列举数据或案例进行分析..."}},
        {{"h1": "结论与展望", "text": "总结全文，给出预测..."}}
    ]
    """
    json_str = call_openrouter(prompt)
    if not json_str:
        return [{"h1": "生成失败", "text": "请重试或检查网络"}]

    try:
        return json.loads(json_str)
    except Exception:
        return [{"h1": "格式解析错误", "text": "AI 返回的数据格式不正确"}]


def _get_mock_data(topic: str, instruction: Optional[str] = None) -> dict:
    """
    兜底用的假数据（网络不通时使用）
    """
    suffix = f" (基于指令：{instruction})" if instruction else ""
    return {
        "topic": topic,
        "analysis": f"AI 已检索全网关于“{topic}”的讨论（离线模式）。{suffix}",
        "emotion": "负面偏多",
        "deep_analysis": {
            "event": f"关于“{topic}”的最新进展显示，相关讨论热度持续上升，网络声量在过去24小时内达到峰值。主要聚焦点在于核心利益相关方的回应及后续处理措施。",
            "industry": "该事件暴露了行业在合规性与应急处理机制上的短板，预计将在短期内引发监管部门的关注，倒逼行业进行标准化整改。",
            "thinking": "透过现象看本质，这不仅仅是单一事件，更反映了在流量经济下，公众情绪与事实真相之间的割裂。资本博弈在其中起到了推波助澜的作用。",
            "future": "预计短期内仍将保持高热度，随着更多细节披露，舆论风向可能发生反转。长期来看，将催生新的行业规范。",
            "conclusion": "综上所述，建议密切关注官方通报，避免盲目跟风，保持独立思考。"
        },
        "strategies": [
            {
                "angle": "深度商业分析",
                "icon": "📊",
                "title": f"《{topic}》背后的资本博弈{suffix}",
                "reason": f"从产业链上下游出发，深扒利益分配机制。{suffix}",
                "outline": ["一、现象级爆发的背后", "二、资本图谱全解析", "三、未来终局推演"]
            },
            {
                "angle": "反直觉/逆向思维",
                "icon": "🧠",
                "title": f"为什么舆论此时引爆？{suffix}",
                "reason": "在一片喧嚣中保持冷静，分析时间点背后的深意。",
                "outline": ["一、偶然中的必然", "二、被忽视的关键变量", "三、结局预测"]
            },
            {
                "angle": "定制化视角",
                "icon": "🎯",
                "title": f"从{instruction or '新视角'}看《{topic}》",
                "reason": f"响应您的特殊要求：{instruction or '差异化'}",
                "outline": ["一、核心切入点", "二、具体案例分析", "三、总结与升华"]
            }
        ]
    }
