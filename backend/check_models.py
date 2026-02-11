import os
import requests
import json

# === 配置 ===
API_KEY = "AIzaSyCIrIYeRTujYGAina6k67YKqldr1PiOx7Y" # 👈 确保 Key 正确
PROXY_PORT = "9091" # 👈 你的端口

# 设置代理
proxies = {
    "http": f"socks5h://127.0.0.1:{PROXY_PORT}",
    "https": f"socks5h://127.0.0.1:{PROXY_PORT}"
}

def list_models():
    print("🕵️ 正在查询可用模型列表...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    
    try:
        resp = requests.get(url, proxies=proxies, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            print("\n✅ Google 官方返回的可用模型：")
            print("-" * 40)
            valid_models = []
            if "models" in data:
                for m in data["models"]:
                    # 只显示 generateContent 支持的模型
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        name = m["name"].replace("models/", "")
                        print(f"🌟 {name}")
                        valid_models.append(name)
            print("-" * 40)
            
            # 自动推荐
            if "gemini-1.5-flash" in valid_models:
                print("💡 推荐使用: gemini-1.5-flash (速度快，免费额度高)")
            elif "gemini-pro" in valid_models:
                print("💡 推荐使用: gemini-pro (经典稳定)")
            else:
                print(f"💡 推荐使用: {valid_models[0] if valid_models else '无可用模型'}")
                
        else:
            print(f"❌ 查询失败: {resp.status_code}")
            print(resp.text)

    except Exception as e:
        print(f"❌ 网络错误: {e}")

if __name__ == "__main__":
    list_models()