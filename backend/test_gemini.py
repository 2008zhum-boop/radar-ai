import os
import sys
from radar_ai import analyze_topic_deeply, generate_full_outline

# === 1. 配置你的 Key (如果没有在环境变量设置，可以在这里临时填) ===
# os.environ["GOOGLE_API_KEY"] = "AIzaSyCIrIYeRTujYGAina6k67YKqldr1PiOx7Y"  <- 如果环境变量没配，把这就行注释取消并填入Key
os.environ["GOOGLE_API_KEY"] = "AIzaSyCIrIYeRTujYGAina6k67YKqldr1PiOx7Y"
def test_gemini():
    # 检查 Key
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        print("❌ 错误: 未找到 API Key。请设置 GOOGLE_API_KEY 环境变量。")
        return

    print(f"✅ 检测到 Key: {key[:6]}******")
    print("🚀 正在发起 Gemini 请求 (请等待约 5-10 秒)...")

    # 测试话题
    topic = "马斯克收购OpenAI" # 故意用一个假新闻或热门话题测试 AI 的反应

    # 调用核心函数
    try:
        # 1. 测试深度分析
        result = analyze_topic_deeply(topic)
        
        # 2. 验证结果是否为 Mock 数据
        result_str = str(result)
        if "模拟数据" in result_str or "AI服务暂时不可用" in result_str:
            print("\n⚠️  测试失败！接口返回的是【Mock 假数据】。")
            print("可能原因：")
            print("1. 网络不通 (请检查 VPN/代理)")
            print("2. API Key 无效或额度耗尽")
            print("3. requests 没走代理 (请设置 HTTP_PROXY)")
        else:
            print("\n🎉 测试成功！Gemini 返回了真实数据：")
            print("-" * 30)
            print(f"分析结论: {result.get('analysis', '')[:100]}...")
            print(f"切入角度: {result.get('strategies', [])[0]['title']}")
            print("-" * 30)

    except Exception as e:
        print(f"\n❌ 发生异常: {e}")

if __name__ == "__main__":
    test_gemini()