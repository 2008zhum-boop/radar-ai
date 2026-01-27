from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# 引入我们写的模块
from radar_weibo import get_weibo_hot_list
from radar_prediction import generate_predictions
from radar_ai import generate_smart_outline, generate_full_article
from radar_monitor import process_monitor_data, get_monitor_stats, get_config_keywords, add_config_keyword

app = FastAPI()

# 允许跨域 (让前端能访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局监控词 (简单的内存存储，默认值)
GLOBAL_KEYWORDS = ["华为", "小米", "特斯拉", "OpenAI"]

# --- 数据模型定义 ---
class PredictionRequest(BaseModel):
    keywords: List[str]

class OutlineRequest(BaseModel):
    title: str
    angle: str = "深度观察"
    context: str = ""

class ArticleRequest(BaseModel):
    title: str
    outline: List[dict]
    context: str = ""

# 定义关键词添加的请求体
class MonitorKeywordRequest(BaseModel):
    word: str
    type: int # 1核心, 2竞品, 3行业
    category: str # 品牌/产品/高管...
    sensitive: str = "" # 逗号分隔的敏感词

# --- 接口定义 ---

@app.get("/")
def read_root():
    return {"message": "Radar AI Backend is Running!"}

@app.get("/hotlist")
def read_hotlist(category: str = "综合"):
    # 1. 获取原始爬虫数据
    raw_data_dict = get_weibo_hot_list(category)
    
    # 2. 将字典转为列表，用于监控分析
    all_items = []
    for source, items in raw_data_dict.items():
        all_items.extend(items)
    
    # 3. 【核心步骤】送入监控漏斗进行清洗和分析
    monitor_result = process_monitor_data(all_items)
    
    return {
        "current_keywords": GLOBAL_KEYWORDS,
        "data": raw_data_dict,
        "alerts": monitor_result['alerts'] # 返回新生成的实时告警
    }

# 核心：热点预测接口 (POST)
@app.post("/predictions")
def read_predictions(req: PredictionRequest):
    target_keywords = req.keywords
    if not target_keywords:
        target_keywords = GLOBAL_KEYWORDS
    data = generate_predictions(target_keywords)
    return {
        "count": len(data),
        "data": data
    }

# --- 关键词管理接口 ---

@app.get("/keywords")
def get_keywords():
    return {"keywords": GLOBAL_KEYWORDS}

@app.post("/keywords/add")
def add_keyword(word: str = Body(..., embed=True)):
    if word and word not in GLOBAL_KEYWORDS:
        GLOBAL_KEYWORDS.insert(0, word)
    return {"keywords": GLOBAL_KEYWORDS}

@app.post("/keywords/remove")
def remove_keyword(word: str = Body(..., embed=True)):
    if word in GLOBAL_KEYWORDS:
        GLOBAL_KEYWORDS.remove(word)
    return {"keywords": GLOBAL_KEYWORDS}

# --- AI 生成接口 ---

@app.post("/generate_outline")
def create_outline(req: OutlineRequest):
    result = generate_smart_outline(req.title, req.angle, req.context)
    return {
        "status": "success",
        "data": result
    }

@app.post("/generate_article")
def create_article(req: ArticleRequest):
    content = generate_full_article(req.title, req.outline, req.context)
    return {
        "status": "success",
        "data": content
    }

# --- 新增：舆情看板接口 ---
@app.get("/monitor/dashboard")
def read_monitor_dashboard():
    return get_monitor_stats()

@app.get("/monitor/config")
def read_monitor_config():
    return get_config_keywords()

@app.post("/monitor/config/add")
def create_monitor_keyword(req: MonitorKeywordRequest):
    add_config_keyword(req.word, req.type, req.category, req.sensitive)
    return {"status": "success"}