"""
新增函数：fetch_tech_news_by_tags
功能：获取"科技"分类下的二级标签，并用这些标签去Google搜索最近6小时的新闻
"""
import sqlite3
import urllib.parse
import requests
from bs4 import BeautifulSoup
import random

DB_FILE = "radar_data.db"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

def fetch_tech_news_by_tags():
    """
    1. 从数据库获取"科技"分类下的所有二级标签
    2. 用标签作为关键词搜索Google News (最近6小时)
    3. 抓取新闻详情并入库
    """
    from radar_weibo import enrich_news_full
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    items = []
    seen_titles = set()
    
    # 1. 获取"科技"分类的 ID
    c.execute("SELECT id FROM tags WHERE name='科技' AND tag_type='CATEGORY'")
    tech_category = c.fetchone()
    
    if not tech_category:
        print("⚠️ Warning: '科技' category not found in database.")
        conn.close()
        return []
    
    tech_id = tech_category[0]
    
    # 2. 获取科技分类下的所有二级标签
    c.execute("""
        SELECT t.name 
        FROM tags t 
        JOIN tag_relations tr ON t.id = tr.child_id 
        WHERE tr.parent_id = ?
    """, (tech_id,))
    
    tech_tags = [row[0] for row in c.fetchall()]
    conn.close()
    
    if not tech_tags:
        print("⚠️ Warning: No secondary tags found under '科技' category.")
        return []
    
    print(f"🔍 Fetching tech news for {len(tech_tags)} tags: {tech_tags[:5]}...")
    
    # 3. 分批查询 (避免URL过长)
    chunk_size = 5
    chunks = [tech_tags[i:i + chunk_size] for i in range(0, len(tech_tags), chunk_size)]
    
    for chunk in chunks:
        try:
            # 构建查询: "(Tag1 OR Tag2 OR ...) when:6h"
            query_str = "(" + " OR ".join(chunk) + ")"
            encoded_q = urllib.parse.quote(query_str)
            
            # Google News RSS (最近6小时)
            rss_url = f"https://news.google.com/rss/search?q={encoded_q}+when:6h&hl=zh-CN&gl=CN&ceid=CN:zh-CN"
            
            resp = requests.get(rss_url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.content, 'xml')
            entries = soup.find_all('item')
            
            for entry in entries[:8]:  # 每批取前8条
                title = entry.title.text if entry.title else ""
                
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)
                
                link = entry.link.text if entry.link else ""
                desc = entry.description.text if entry.description else ""
                pub_date = entry.pubDate.text if entry.pubDate else ""
                
                # 清理描述
                desc_text = BeautifulSoup(desc, "lxml").get_text().strip()
                
                items.append({
                    "rank": 999,
                    "title": title,
                    "heat": random.randint(10000, 500000),
                    "label": "科",
                    "category": "科技",
                    "tags": chunk[:3],
                    "url": link,
                    "raw_summary_context": desc_text[:200],
                    "pub_date": pub_date,
                    "source": "全网监控-科技"
                })
                
        except Exception as e:
            print(f"  Error fetching tech news chunk: {e}")
    
    print(f"✅ Found {len(items)} tech news items. Enriching with full content...")
    
    # 4. 调用增强函数抓取完整内容
    # enrich_news_full 会抓取：标题、摘要、正文、作者、发布时间、URL
    # 如果摘要为空，会调用AI生成
    enriched = enrich_news_full(items)
    
    return enriched


if __name__ == "__main__":
    # 测试
    results = fetch_tech_news_by_tags()
    print(f"\n📰 Successfully fetched {len(results)} tech news articles")
    if results:
        print(f"Sample: {results[0]['title']}")
