from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel  # <--- 这里就是缺少的关键引入
from typing import List
from radar_ai import generate_smart_outline

# 引入我们写的模块
from radar_weibo import get_weibo_hot_list
from radar_prediction import generate_predictions
from radar_ai import generate_smart_outline, generate_full_article # 引入新函数

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
    angle: str = "深度观察" # 默认角度
    context: str = ""

class ArticleRequest(BaseModel):
    title: str
    outline: List[dict] # 接收完整的大纲结构
    context: str = ""

# --- 接口定义 ---

@app.get("/")
def read_root():
    return {"message": "Radar AI Backend is Running!"}

@app.get("/hotlist")
def read_hotlist(category: str = "综合"):
    # 获取爬虫数据
    data = get_weibo_hot_list(category)
    
    # 简单的告警判断 (模拟逻辑：如果标题包含监控词，就加入告警)
    alerts = []
    # 这里为了演示，我们先不通过后端计算告警，而是让前端根据 monitorList 自己算
    # 后端只负责透传数据和关键词
    
    return {
        "current_keywords": GLOBAL_KEYWORDS,
        "data": data,
        "alerts": [] # 告警逻辑已移交前端计算
    }

# 核心：热点预测接口 (POST)
@app.post("/predictions")
def read_predictions(req: PredictionRequest):
    # 1. 接收前端传来的精准名单
    target_keywords = req.keywords
    
    # 2. 如果前端没传 (比如刚初始化)，用全局兜底
    if not target_keywords:
        target_keywords = GLOBAL_KEYWORDS
    
    # 3. 调用算法生成
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

# 2. 新增：生成智能大纲接口
@app.post("/generate_outline")
def create_outline(req: OutlineRequest):
    # 调用 AI 生成逻辑
    result = generate_smart_outline(req.title, req.angle, req.context)
    return {
        "status": "success",
        "data": result
    }

# 新增：一键生成全文接口
@app.post("/generate_article")
def create_article(req: ArticleRequest):
    # 调用 AI 写作逻辑
    content = generate_full_article(req.title, req.outline, req.context)
    return {
        "status": "success",
        "data": content
    }