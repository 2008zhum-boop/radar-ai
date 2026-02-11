import sqlite3
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from radar_tags import create_tag, TagCreateReq, DB_FILE

def restore_special_tags():
    print("🚀 开始恢复情绪、事件、质量标签...")
    
    # 1. 情绪标签 (SENTIMENT)
    sentiments = ["正面", "负面", "中性", "乐观", "悲观", "焦虑", "兴奋"]
    for name in sentiments:
        # Check existence
        if check_exists(name, "SENTIMENT"):
            print(f"  - 情绪标签 '{name}' 已存在")
            continue
            
        res = create_tag(TagCreateReq(name=name, tag_type="SENTIMENT"))
        if res['status'] == 'success':
            print(f"  ✅ 恢复情绪标签: {name}")
        else:
            print(f"  ⚠️ 恢复失败 {name}: {res.get('msg')}")

    # 2. 事件标签 (EVENT)
    events = ["突发", "政策发布", "财报", "投融资", "上市/IPO", "人事变动", "战略合作", "辟谣", "官宣", "产品发布"]
    for name in events:
        if check_exists(name, "EVENT"):
            print(f"  - 事件标签 '{name}' 已存在")
            continue

        res = create_tag(TagCreateReq(name=name, tag_type="EVENT"))
        if res['status'] == 'success':
            print(f"  ✅ 恢复事件标签: {name}")
        else:
            print(f"  ⚠️ 恢复失败 {name}: {res.get('msg')}")

    # 3. 质量标签 (QUALITY) - 新增类型
    qualities = ["深度", "独家", "爆款", "首发", "优质", "长文", "短讯", "推广", "水文"]
    for name in qualities:
        if check_exists(name, "QUALITY"):
            print(f"  - 质量标签 '{name}' 已存在")
            continue

        res = create_tag(TagCreateReq(name=name, tag_type="QUALITY"))
        if res['status'] == 'success':
            print(f"  ✅ 恢复质量标签: {name}")
        else:
            print(f"  ⚠️ 恢复失败 {name}: {res.get('msg')}")

    print("🎉 所有特殊标签恢复完成!")

def check_exists(name, tag_type):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM tags WHERE name=? AND tag_type=?", (name, tag_type))
    res = c.fetchone()
    conn.close()
    return res is not None

if __name__ == "__main__":
    restore_special_tags()
