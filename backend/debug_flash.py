from radar_flash import fetch_all_flashes, init_flash_db, get_flashes
init_flash_db()
print("Fetching...")
items = fetch_all_flashes()
print(f"Fetched {len(items)} items")
print("Verification from DB:")
db_items = get_flashes('all', limit=10)
print(f"DB has {len(db_items)} items")
for item in db_items:
    print(f"- {item['title']} [{item['status']}]")
