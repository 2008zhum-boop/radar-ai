#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全网内容库模块 - 功能测试脚本
用于验证后端 API 是否正确实现
"""

import sys
sys.path.insert(0, '/Users/qianqian/Documents/开发/smart-edit-core/backend')

import sqlite3
import json
import time
from radar_monitor import (
    get_global_content_library,
    bulk_discard_content,
    add_source_to_blacklist,
    get_source_blacklist,
    remove_source_from_blacklist,
    associate_content_to_client,
    correct_content_classification,
    get_content_quality_stats,
    process_monitor_data,
    save_full_client_config
)

def test_1_data_preparation():
    """准备测试数据：创建客户和内容"""
    print("\n[测试 1] 准备测试数据...\n")
    
    # 创建测试客户
    logic = {
        "brand_keywords": ["特斯拉", "电动车"],
        "exclude_keywords": ["玩具"],
        "advanced_rules": []
    }
    result = save_full_client_config("特斯拉", "汽车", 1, logic)
    client_id = result["client_id"]
    print(f"✅ 创建测试客户: {client_id}")
    
    # 创建测试内容
    test_items = [
        {
            "title": "特斯拉新款Model Y售价下调20%",
            "summary": "特斯拉官方宣布2024年Model Y系列产品价格调整",
            "source": "36氪",
            "url": "https://example.com/1"
        },
        {
            "title": "兼职刷单月入万元，联系微信12345678",
            "summary": "广告内容",
            "source": "贴吧",
            "url": "https://example.com/2"
        },
        {
            "title": "比亚迪销量突破500万辆",
            "summary": "比亚迪新能源汽车销售创新高",
            "source": "央视新闻",
            "url": "https://example.com/3"
        },
        {
            "title": "ChatGPT发布GPT-5版本",
            "summary": "OpenAI宣布下一代大语言模型",
            "source": "微博",
            "url": "https://example.com/4"
        }
    ]
    
    result = process_monitor_data(test_items)
    print(f"✅ 插入测试数据: {result['processed']}条内容入库")
    print(f"   - 识别高危内容: {len(result['alerts'])}条")
    
    return client_id

def test_2_search_and_filter():
    """测试 2：搜索和筛选功能"""
    print("\n[测试 2] 搜索和筛选功能...\n")
    
    # 搜索所有未清洗的内容
    result = get_global_content_library(
        search_text="",
        time_range="24h",
        clean_status_filter=["uncleaned"],
        page=1,
        page_size=10
    )
    print(f"✅ 搜索未清洗内容: {len(result['items'])}条")
    
    # 按来源筛选
    result = get_global_content_library(
        search_text="",
        source_filter=["微博"],
        time_range="24h",
        page=1,
        page_size=10
    )
    print(f"✅ 筛选微博内容: {len(result['items'])}条")
    
    # 全文搜索
    result = get_global_content_library(
        search_text="特斯拉",
        time_range="24h",
        page=1,
        page_size=10
    )
    print(f"✅ 搜索关键词'特斯拉': {len(result['items'])}条")
    if result['items']:
        print(f"   - 第一条: {result['items'][0]['title']}")

def test_3_blacklist():
    """测试 3：黑名单管理"""
    print("\n[测试 3] 黑名单管理...\n")
    
    # 添加到黑名单
    result = add_source_to_blacklist("贴吧", "forum", "垃圾广告泛滥", "test_admin")
    print(f"✅ 添加贴吧到黑名单: {result['message']}")
    
    # 获取黑名单
    result = get_source_blacklist()
    print(f"✅ 黑名单中有 {len(result['blacklist'])}个信源")
    for item in result['blacklist']:
        print(f"   - {item['source_name']}: {item['reason']}")
    
    # 从黑名单移除
    result = remove_source_from_blacklist("贴吧")
    print(f"✅ 从黑名单移除贴吧")

def test_4_bulk_operations():
    """测试 4：批量操作"""
    print("\n[测试 4] 批量操作...\n")
    
    # 获取前3条内容的ID
    result = get_global_content_library(page=1, page_size=3)
    mention_ids = [item['id'] for item in result['items']]
    
    if mention_ids:
        result = bulk_discard_content(mention_ids)
        print(f"✅ 批量删除 {result['discarded_count']}条内容")
    else:
        print("⚠️ 没有找到内容进行测试")

def test_5_manual_operations(client_id):
    """测试 5：手动操作（关联、纠偏）"""
    print("\n[测试 5] 手动操作...\n")
    
    # 获取第一条未关联的内容
    result = get_global_content_library(page=1, page_size=10)
    unassociated = [item for item in result['items'] if not item['client_id']]
    
    if unassociated:
        item = unassociated[0]
        print(f"✅ 找到未关联内容: {item['title']}")
        
        # 尝试关联到客户
        try:
            result = associate_content_to_client(item['id'], client_id, "test_editor")
            print(f"✅ 关联到客户成功")
        except Exception as e:
            print(f"⚠️ 关联失败: {e}")
        
        # 尝试修正分类
        try:
            result = correct_content_classification(
                item['id'],
                new_category="科技/汽车",
                new_sentiment="positive",
                corrected_by="test_editor"
            )
            print(f"✅ 修正AI判定成功")
        except Exception as e:
            print(f"⚠️ 修正失败: {e}")
    else:
        print("⚠️ 没有找到未关联的内容")

def test_6_quality_stats():
    """测试 6：数据质检统计"""
    print("\n[测试 6] 数据质检统计...\n")
    
    result = get_content_quality_stats()
    print(f"✅ 今日采集总数: {result['total_count']}")
    print(f"✅ 可疑垃圾广告数: {result['garbage_count']}")
    print(f"✅ 垃圾率: {result['garbage_rate']}%")
    print(f"✅ 来源分布:")
    for source in result['source_distribution'][:3]:
        print(f"   - {source['source']}: {source['count']}条 ({source['percentage']}%)")
    print(f"✅ 情感分布:")
    print(f"   - 正面: {result['sentiment_distribution']['positive']['percentage']}%")
    print(f"   - 负面: {result['sentiment_distribution']['negative']['percentage']}%")
    print(f"   - 中性: {result['sentiment_distribution']['neutral']['percentage']}%")

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("全网内容库模块 - 功能测试")
    print("=" * 60)
    
    try:
        client_id = test_1_data_preparation()
        test_2_search_and_filter()
        test_3_blacklist()
        test_4_bulk_operations()
        test_5_manual_operations(client_id)
        test_6_quality_stats()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
