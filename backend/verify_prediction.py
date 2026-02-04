
import sys
import os
sys.path.append(os.getcwd())

from radar_prediction import predict_future_trends
from radar_weibo import get_weibo_hot_list

print("--- Testing Hot List Fetching ---")
hot_list = get_weibo_hot_list("综合")
print(f"Hot List Count: {len(hot_list)}")
if hot_list:
    first_src = list(hot_list.keys())[0]
    print(f"Sample Data from {first_src}: {hot_list[first_src][:1]}")

print("\n--- Testing Prediction Logic ---")
trends = predict_future_trends()
print(f"Trends Count: {len(trends)}")
if trends:
    print(f"First Trend: {trends[0]}")
else:
    print("No trends generated.")
