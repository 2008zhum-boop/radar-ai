from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# 引入我们写的模块
from radar_weibo import get_weibo_hot_list
from radar_prediction import generate_predictions
from radar_ai import generate_smart_outline, generate_full_article

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

# --- 接口定义 ---

@app.get("/")
def read_root():
    return {"message": "Radar AI Backend is Running!"}

@app.get("/hotlist")
def read_hotlist(category: str = "综合"):
    # 获取爬虫数据
    data = get_weibo_hot_list(category)
    
    return {
        "current_keywords": GLOBAL_KEYWORDS,
        "data": data,
        "alerts": [] 
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