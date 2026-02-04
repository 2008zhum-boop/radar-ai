
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("DEEPSEEK_API_KEY")
print(f"Key present: {bool(key)}")
if key:
    print(f"Key start: {key[:5]}...")
    print(f"Key length: {len(key)}")
else:
    print("KEY IS WRONG OR MISSING")

from ai_engine import client
print(f"Client initialized: {client is not None}")
