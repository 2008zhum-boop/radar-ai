import sys
import os
import sqlite3

# Ensure we can import from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radar_tags import create_tag, TagCreateReq, init_tag_db

def run_import():
    init_tag_db()

    parent_name = "科技"
    tags_to_add = [
        "人工智能", "大模型", "AIGC", "机器学习", 
        "算力", "芯片半导体", "GPU", "存储芯片", "先进制程", "光刻机",
        "云计算", "办公协同", "数据库", "信息安全",
        "智能硬件", "手机", "PC", "可穿戴设备", "VR/AR",
        "量子计算", "航天科技", "Web3", "区块链",
        "5G/6G", "卫星通信", "物联网" 
    ]
    # Note: "物联网 (IoT)" contains parenthesis, might be cleaner as "物联网" with alias "IoT"
    # User input: "物联网 (IoT)" -> I will keep it as name for now, or split it.
    # Let's handle "物联网 (IoT)" specifically: Name="物联网", Alias="IoT"
    
    special_tags = {
        "物联网 (IoT)": {"name": "物联网", "alias": "IoT"}
    }

    # 1. Get or Create Parent "科技" (CATEGORY)
    conn = sqlite3.connect("radar_data.db")
    c = conn.cursor()
    c.execute("SELECT id FROM tags WHERE name=?", (parent_name,))
    row = c.fetchone()
    parent_id = None

    if row:
        parent_id = row[0]
        print(f"Found parent '{parent_name}' ID: {parent_id}")
    else:
        print(f"Parent '{parent_name}' not found. Creating...")
        req = TagCreateReq(name=parent_name, tag_type="CATEGORY", parent_ids=[])
        res = create_tag(req)
        if res['status'] == 'success':
            parent_id = res['id']
            print(f"Created parent '{parent_name}' ID: {parent_id}")
        else:
            print(f"Failed to create parent: {res}")
            return

    conn.close()

    # 2. Import Children (ENTITY)
    for raw_name in tags_to_add:
        name = raw_name
        alias = ""
        
        # Handle special case if present in list (though my list above has "物联网")
        # Ensure list matches user input exactly or corrected
        if raw_name == "物联网": # In my list above I put "物联网"
             # But user gave "物联网 (IoT)"
             pass

    # Redefine list based strictly on user input text
    user_input_tags = [
        "人工智能", "大模型", "AIGC", "机器学习", "算力", "芯片半导体", "GPU", "存储芯片", "先进制程", "光刻机", "云计算", "办公协同", "数据库", "信息安全", "智能硬件", "手机", "PC", "可穿戴设备", "VR/AR", "量子计算", "航天科技", "Web3", "区块链", "5G/6G", "卫星通信", "物联网 (IoT)"
    ]

    for item in user_input_tags:
        name = item.strip()
        alias = ""
        
        if "物联网 (IoT)" in name:
            name = "物联网"
            alias = "IoT"
            
        print(f"Adding '{name}'...")
        req = TagCreateReq(name=name, tag_type="ENTITY", parent_ids=[parent_id], alias=alias)
        res = create_tag(req)
        if res['status'] == 'success':
            print(f"  ✅ Success: {res['msg']}")
        else:
            print(f"  ⚠️ Skipped/Error: {res['msg']}")

if __name__ == "__main__":
    run_import()
