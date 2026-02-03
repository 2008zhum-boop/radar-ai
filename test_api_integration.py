"""
前后端集成测试脚本
用于验证全网内容库 API 的完整流程
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

# 模拟用户 Token（实际应该通过登录获取）
HEADERS = {
    "Authorization": "Bearer fake_token_for_testing",
    "Content-Type": "application/json"
}

def test_content_library_flow():
    """测试完整的内容库工作流"""
    
    print("=" * 70)
    print("全网内容库 - API 集成测试")
    print("=" * 70)
    
    # 1. 测试全文搜索
    print("\n[1] 测试全文搜索...")
    try:
        response = requests.post(
            f"{BASE_URL}/content/library/search",
            json={
                "search_text": "特斯拉",
                "source_filter": None,
                "sentiment_filter": None,
                "clean_status_filter": None,
                "time_range": "24h",
                "page": 1,
                "page_size": 10
            },
            headers=HEADERS
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 搜索成功，找到 {data['total']} 条内容")
            if data['items']:
                print(f"   - 第一条: {data['items'][0]['title'][:50]}")
        else:
            print(f"❌ 搜索失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return
    
    # 2. 测试多维度筛选
    print("\n[2] 测试多维度筛选...")
    try:
        response = requests.post(
            f"{BASE_URL}/content/library/search",
            json={
                "search_text": "",
                "source_filter": ["微博", "36氪"],
                "sentiment_filter": ["negative"],
                "clean_status_filter": ["uncleaned"],
                "time_range": "24h",
                "page": 1,
                "page_size": 20
            },
            headers=HEADERS
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 筛选成功，找到 {data['total']} 条未清洗的负面内容")
        else:
            print(f"❌ 筛选失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
    
    # 3. 测试数据质检统计
    print("\n[3] 测试数据质检统计...")
    try:
        response = requests.get(
            f"{BASE_URL}/content/quality-stats",
            headers=HEADERS
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 质检统计:")
            print(f"   - 今日采集: {data['total_count']} 条")
            print(f"   - 垃圾率: {data['garbage_rate']}%")
            print(f"   - 正面内容: {data['sentiment_distribution']['positive']['percentage']}%")
        else:
            print(f"❌ 统计失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
    
    # 4. 测试黑名单管理
    print("\n[4] 测试黑名单管理...")
    
    # 获取黑名单
    try:
        response = requests.get(
            f"{BASE_URL}/content/blacklist",
            headers=HEADERS
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 当前黑名单有 {len(data['blacklist'])} 个信源")
            for item in data['blacklist'][:3]:
                print(f"   - {item['source_name']}")
        else:
            print(f"❌ 获取黑名单失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
    
    # 5. 测试批量删除
    print("\n[5] 测试批量删除...")
    try:
        response = requests.post(
            f"{BASE_URL}/content/library/search",
            json={
                "search_text": "",
                "source_filter": None,
                "sentiment_filter": None,
                "clean_status_filter": None,
                "time_range": "24h",
                "page": 1,
                "page_size": 5
            },
            headers=HEADERS
        )
        if response.status_code == 200:
            items = response.json()['items']
            if items:
                mention_ids = [item['id'] for item in items[:2]]
                response = requests.post(
                    f"{BASE_URL}/content/library/bulk-discard",
                    json={"mention_ids": mention_ids},
                    headers=HEADERS
                )
                if response.status_code == 200:
                    print(f"✅ 批量删除成功: {response.json()['discarded_count']} 条")
                else:
                    print(f"❌ 批量删除失败: {response.status_code}")
            else:
                print("⚠️ 没有内容可供删除")
        else:
            print(f"❌ 获取内容失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
    
    # 6. 测试手动关联
    print("\n[6] 测试手动关联...")
    try:
        # 先获取一条内容
        response = requests.post(
            f"{BASE_URL}/content/library/search",
            json={
                "search_text": "",
                "source_filter": None,
                "sentiment_filter": None,
                "clean_status_filter": None,
                "time_range": "24h",
                "page": 1,
                "page_size": 1
            },
            headers=HEADERS
        )
        if response.status_code == 200:
            items = response.json()['items']
            if items:
                mention_id = items[0]['id']
                # 获取一个客户 ID（假设存在）
                response = requests.get(
                    f"{BASE_URL}/monitor/clients",
                    headers=HEADERS
                )
                if response.status_code == 200 and response.json():
                    client_id = response.json()[0]['client_id']
                    # 尝试关联
                    response = requests.post(
                        f"{BASE_URL}/content/associate",
                        json={
                            "mention_id": mention_id,
                            "client_id": client_id
                        },
                        headers=HEADERS
                    )
                    if response.status_code == 200:
                        print(f"✅ 手动关联成功")
                    else:
                        print(f"❌ 关联失败: {response.status_code}")
                else:
                    print("⚠️ 没有可用的客户")
            else:
                print("⚠️ 没有内容可供关联")
        else:
            print(f"❌ 获取内容失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
    
    # 7. 测试修正 AI 判定
    print("\n[7] 测试修正 AI 判定...")
    try:
        # 先获取一条内容
        response = requests.post(
            f"{BASE_URL}/content/library/search",
            json={
                "search_text": "",
                "source_filter": None,
                "sentiment_filter": None,
                "clean_status_filter": None,
                "time_range": "24h",
                "page": 1,
                "page_size": 1
            },
            headers=HEADERS
        )
        if response.status_code == 200:
            items = response.json()['items']
            if items:
                mention_id = items[0]['id']
                # 修正
                response = requests.post(
                    f"{BASE_URL}/content/correct",
                    json={
                        "mention_id": mention_id,
                        "new_category": "科技/AI",
                        "new_sentiment": "positive"
                    },
                    headers=HEADERS
                )
                if response.status_code == 200:
                    print(f"✅ 修正 AI 判定成功")
                else:
                    print(f"❌ 修正失败: {response.status_code}")
            else:
                print("⚠️ 没有内容可供修正")
        else:
            print(f"❌ 获取内容失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
    
    print("\n" + "=" * 70)
    print("✅ 集成测试完成！")
    print("=" * 70)
    print("\n提示：")
    print("- 确保后端服务运行在 http://localhost:8000")
    print("- 确保已通过认证（有有效的 Token）")
    print("- 如果某些测试失败，检查后端日志获取更多信息")

if __name__ == "__main__":
    print("\n⏳ 等待 3 秒确保后端已启动...")
    time.sleep(3)
    test_content_library_flow()
