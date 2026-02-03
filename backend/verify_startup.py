
import sys
import os

# Set path to backend
sys.path.append(os.getcwd())

print("Attempting to import radar_weibo...")
try:
    import radar_weibo
    print("SUCCESS: radar_weibo imported.")
except Exception as e:
    print(f"ERROR: Failed to import radar_weibo: {e}")
    sys.exit(1)

print("Attempting to import main...")
try:
    from main import app
    print("SUCCESS: main imported.")
except Exception as e:
    print(f"ERROR: Failed to import main: {e}")
    sys.exit(1)
