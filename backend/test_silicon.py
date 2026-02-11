import requests
import json
import time
import os

# 1. 您的 Key
API_KEY = "sk-xhlggbibvssprqgoadkdpxdnsbpzdeqfpkcrnhhnuohowrpd"

# 2. 模型列表
MODELS_TO_TEST = [
    "deepseek-ai/DeepSeek-V3",     # 旗舰 (首选)
    "Qwen/Qwen2.5-72B-Instruct",   # 备用
    "deepseek-ai/DeepSeek-R1"      # 推理
]

def test_model(model_name):
    print(f"\n🧪 正在测试模型: {model_name} ...")
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": "你好，请回复'测试成功'四个字。"}],
        "stream": False
    }
    
    try:
        # 🛡️ 关键修改：proxies={"http": None, "https": None}
        # 这行代码强制 requests 忽略系统的代理设置，直接连接
        resp = requests.post(
            url, 
            headers=headers, 
            json=data, 
            timeout=10, 
            proxies={"http": None, "https": None} 
        )
        
        if resp.status_code == 200:
            res_json = resp.json()
            content = res_json['choices'][0]['message']['content']
            print(f"✅ {model_name} 测试通过！回复: {content}")
            return True
        else:
            print(f"❌ {model_name} 失败: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return False

if __name__ == "__main__":
    # 双重保险：在代码里删掉环境变量
    if "HTTP_PROXY" in os.environ: del os.environ["HTTP_PROXY"]
    if "HTTPS_PROXY" in os.environ: del os.environ["HTTPS_PROXY"]
    
    print("🚀 开始诊断 SiliconFlow API (已强制直连)...")
    for model in MODELS_TO_TEST:
        test_model(model)