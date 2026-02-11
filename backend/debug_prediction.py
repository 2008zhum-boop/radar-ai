from radar_weibo import get_weibo_hot_list
from radar_prediction import predict_future_trends

print("--- Testing Weibo Hot List ---")
try:
    data = get_weibo_hot_list("综合")
    print(f"Sources found: {list(data.keys())}")
    for k, v in data.items():
        print(f"{k}: {len(v)} items")
        if v:
            print(f"First item: {v[0].get('title', 'No Title')}")
except Exception as e:
    print(f"Weibo Error: {e}")

print("\n--- Testing Prediction ---")
try:
    preds = predict_future_trends(force_refresh=True)
    print(f"Predictions count: {len(preds)}")
    if preds:
        print(f"Top 1: {preds[0]['title']} (Score: {preds[0]['pred_score']})")
except Exception as e:
    print(f"Prediction Error: {e}")
