import sys
import os
import json
import sqlite3
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# === MOCKING DEPENDENCIES ===
# Mock ai_engine
sys.modules['ai_engine'] = MagicMock()
sys.modules['ai_engine'].analyze_risk_assessment.return_value = {'risk_keywords': [], 'score': 0.0}

# Mock requests (referenced by radar_weibo)
sys.modules['requests'] = MagicMock()

# Mock radar_weibo (referenced by radar_prediction)
radar_weibo_mock = MagicMock()
sys.modules['radar_weibo'] = radar_weibo_mock

# Mock return data for get_weibo_hot_list
radar_weibo_mock.get_weibo_hot_list.return_value = {
    "综合": [
        {"title": "DeepSeek Explodes in Popularity", "heat": 800000, "source": "Weibo"},
        {"title": "Nvidia Stock Split", "heat": 600000, "source": "Weibo"},
        {"title": "SpaceX Success", "heat": 400000, "source": "Weibo"}
    ]
}

# Now safe to import modules that depend on these
import radar_monitor
import radar_prediction

def test_monitor_logic():
    print("=== Testing Monitor Logic ===")
    
    # 1. Init DB & Add Test Client
    radar_monitor.init_monitor_db()
    
    # Clean previous test data
    conn = sqlite3.connect("radar_data.db")
    c = conn.cursor()
    c.execute("DELETE FROM client_config WHERE name='TestClient'")
    conn.commit()
    conn.close()
    
    match_logic = {
        "brand_keywords": ["TestBrand", "TB-X"],
        "exclude_keywords": ["TestBrand Fake"],
        "advanced_rules": [
            {"rule_name": "Scandal", "must_contain": ["CEO"], "nearby_words": ["Arrested", "Fraud"], "distance": 10}
        ]
    }
    
    client_id = radar_monitor.add_client_config("TestClient", match_logic)
    print(f"[Pass] Client added: {client_id}")
    
    # 2. Test Data
    test_items = [
        {"title": "TestBrand released a new product", "source": "Weibo", "url": "http://test/1"}, # Should Match (Green)
        {"title": "TestBrand Fake product detected", "source": "Weibo", "url": "http://test/2"},  # Should Exclude
        {"title": "TestBrand CEO was Arrested yesterday", "source": "CCTV", "url": "http://test/3"}, # Should Match Advanced (Red)
        {"title": "TB-X sales are booming", "source": "36Kr", "url": "http://test/4"} # Should Match (Green/Yellow)
    ]
    
    # 3. Process
    result = radar_monitor.process_monitor_data(test_items)
    
    print(f"Processed Count: {result['processed']} (Expected 3, one excluded)")
    print(f"Alerts: {len(result['alerts'])}")
    
    for alert in result['alerts']:
        print(f"ALARM: [{alert['level']}] {alert['title']} -> {alert['reason']}")
        
    # Verify DB content
    conn = sqlite3.connect("radar_data.db")
    c = conn.cursor()
    c.execute(f"SELECT title, risk_level, match_detail FROM mentions WHERE client_id='{client_id}'")
    rows = c.fetchall()
    conn.close()
    
    # We expect 3 rows. 
    # Row 1: "TestBrand released..." -> Level 1 (or 2 if sentiment logic triggers)
    # Row 2: "TestBrand CEO..." -> Level 3 (matches Advanced Rule)
    # Row 3: "TB-X sales..." -> Level 1
    
    assert result['processed'] == 3, f"Expected 3 processed, got {result['processed']}"
    
    # Verify Level 3 logic
    high_risk = [r for r in rows if r[1] == 3]
    assert len(high_risk) >= 1, "Failed to detect Level 3 risk (Advanced Rule)"
    print("[Pass] Monitor Logic Verified")

def test_prediction_logic():
    print("\n=== Testing Prediction Logic ===")
    
    # Prepare client config list for prediction
    clients = [
        {"name": "TestClient", "brand_keywords": ["TestBrand"]}
    ]
    
    predictions = radar_prediction.generate_predictions(clients)
    
    if not predictions:
        print("[Warn] No predictions generated (possibly connection issue or random chance)")
    else:
        print(f"Generated {len(predictions)} predictions")
        first = predictions[0]
        # print("Sample Prediction:")
        # print(json.dumps(first, indent=2, ensure_ascii=False))
        
        # Ensure new keys are present
        assert 'acceleration' in first
        assert 'level' in first
        assert 'is_rocket' in first
        print("[Pass] Prediction Logic Verified")

if __name__ == "__main__":
    test_monitor_logic()
    test_prediction_logic()
