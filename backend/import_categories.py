import sys
import os
import sqlite3
import re

# Ensure we can import from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radar_tags import DB_FILE

DATA = {
    "科技": ["大模型", "AIGC", "机器学习", "算力", "GPU", "存储芯片", "先进制程", "光刻机", "云计算", "办公协同", "数据库", "信息安全", "手机", "可穿戴设备", "VR/AR", "量子计算", "航天科技", "Web3", "区块", "5G/6G", "卫星通信", "物联网 (IoT)"],
    "财经": ["A股", "港股", "美股", "北交所", "银行", "券商", "保险", "信托", "公募基金", "ETF", "私募基金", "固收", "加密货币", "BTC", "NFT", "数字人民币", "住宅市场", "商业地产", "REITs", "IPO", "上市辅导", "招股书", "破发"],
    "汽车": ["新能源汽车", "纯电", "插混", "增程", "电池/充电桩", "智能驾驶", "自动驾驶", "激光雷达", "智驾芯片", "智能座舱", "车机系统", "HUD", "车载娱乐", "BBA", "燃油车", "汽车后市场", "二手车", "维修保养", "造车新势力", "蔚小理", "小米汽车"],
    "大健康": ["生物医药", "创新药", "疫苗", "CRO/CDMO", "医疗器械", "医学影像", "体外诊断 (IVD)", "手术机器人", "医疗服务", "互联网医疗", "民营医院", "体检", "生命科学", "基因编辑", "脑机接口", "合成生物", "健康管理", "养老产业", "康复", "营养保健"],
    "新消费": ["电商零售", "直播带货", "跨境电商", "即时零售", "食品饮料", "新茶饮", "咖啡", "预制菜", "零食", "美妆个护", "国货美妆", "医美", "护肤", "潮流生活", "运动户外", "宠物经济", "潮玩", "智能家居", "扫地机", "智能家电"],
    "宏观": ["政策解读", "中央文件", "产业政策", "监管动态", "经济数据", "GDP", "CPI/PPI", "PMI", "社融", "货币政策", "美联储加息/降息", "央行降准", "汇率", "全球经济", "地缘政治", "国际贸易", "一带一路"],
    "创投": ["投融资", "天使轮", "A轮", "B轮", "投资机构", "红杉", "高瓴", "VC/PE动态", "创业公司", "独角兽", "创业人物", "商业模式", "硬科技创投", "出海创投"]
}

def parse_name_alias(raw_str):
    # Match "Name (Alias)"
    match = re.match(r"^(.*?)\s*\((.*?)\)$", raw_str.strip())
    if match:
        return match.group(1), match.group(2)
    return raw_str.strip(), ""

def get_or_create_tag(cursor, name, tag_type, alias=""):
    cursor.execute("SELECT id FROM tags WHERE name=? AND tag_type=?", (name, tag_type))
    row = cursor.fetchone()
    if row:
        return row[0]
    
    import time
    cursor.execute(
        "INSERT INTO tags (name, tag_type, parent_id, alias, count, create_time) VALUES (?,?,?,?,0,?)",
        (name, tag_type, None, alias, time.time())
    )
    return cursor.lastrowid

def ensure_relation(cursor, parent_id, child_id):
    cursor.execute("INSERT OR IGNORE INTO tag_relations (parent_id, child_id) VALUES (?, ?)", (parent_id, child_id))

def run_import():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    print("🚀 开始导入分类标签体系...")
    
    try:
        for parent_name, children in DATA.items():
            print(f"🔹 处理一级分类: {parent_name}")
            parent_id = get_or_create_tag(c, parent_name, "CATEGORY")
            
            for child_raw in children:
                name, alias = parse_name_alias(child_raw)
                print(f"  - 添加二级标签: {name} (Alias: {alias})")
                child_id = get_or_create_tag(c, name, "CATEGORY", alias)
                ensure_relation(c, parent_id, child_id)
                
        conn.commit()
        print("✅ 导入完成!")
    except Exception as e:
        conn.rollback()
        print(f"❌ 导入出错: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_import()
