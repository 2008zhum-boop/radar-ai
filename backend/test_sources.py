import os
import sys

# ================= 配置区域 =================
# 1. 设置 Google API Key
os.environ["GOOGLE_API_KEY"] = "AIzaSyCIrIYeRTujYGAina6k67YKqldr1PiOx7Y" 

# 2. 强制指定使用 Gemini
os.environ["AI_PROVIDER"] = "gemini" 
os.environ["GEMINI_MODEL"] = "gemini-1.5-flash"

# 3. 设置代理 (端口 9091)
PROXY_PORT = "9091"
PROXY_URL = f"socks5h://127.0.0.1:{PROXY_PORT}"

os.environ["HTTP_PROXY"] = PROXY_URL
os.environ["HTTPS_PROXY"] = PROXY_URL
# ===========================================

print("🚀 正在初始化...")

# 直接导入，不拦截错误，以便看清具体的 Traceback
from radar_weibo import fetch_google_custom_search, fetch_github_trending, fetch_36kr

def print_result(name, data):
    print(f"\n{'='*20} 测试源：{name} {'='*20}")
    if not data:
        print("❌ 未获取到数据 (可能是网络超时或解析失败)")
        return
    
    print(f"✅ 成功获取 {len(data)} 条数据")
    if len(data) > 0:
        first = data[0]
        print(f"📌 [标题]: {first.get('title')}")
        print(f"🔗 [链接]: {first.get('url')}")
        print(f"🏷️ [标签]: {first.get('tags')}")
        
        fact = first.get('fact')
        if fact:
            print(f"🧠 [AI事实]: {fact[:60]}...")
        else:
            print("⚠️ AI 未生成摘要 (可能被限流或出错)")

def main():
    print(f"🚀 开始测试... (代理: {PROXY_URL})")
    print(f"🤖 AI 模型: {os.environ.get('GEMINI_MODEL')}")

    # 1. 测试 36氪
    try:
        print("\n🔵 [1/3] 正在抓取 36氪 (测试 AI 功能)...")
        kr_data = fetch_36kr()
        print_result("36Kr", kr_data)
    except Exception as e:
        print(f"❌ 36Kr 测试出错: {e}")

    # 2. 测试 GitHub
    try:
        print("\n🐱 [2/3] 正在抓取 GitHub...")
        github_data = fetch_github_trending()
        print_result("GitHub", github_data)
    except Exception as e:
        print(f"❌ GitHub 测试出错: {e}")

    # 3. 测试 Google
    try:
        print("\n🔍 [3/3] 正在抓取 Google News...")
        google_data = fetch_google_custom_search()
        print_result("Google AI News", google_data)
    except Exception as e:
        print(f"❌ Google 测试出错: {e}")

if __name__ == "__main__":
    main()