from fastapi import FastAPI, Body, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional

# === 引入各功能模块 ===
from radar_weibo import get_weibo_hot_list
from radar_ai import generate_smart_outline, generate_full_article
from ai_engine import generate_analysis
from radar_prediction import generate_predictions, predict_future_trends
from radar_monitor import (
    process_monitor_data, 
    get_monitor_stats, 
    save_full_client_config, 
    get_all_clients,
    delete_client_by_id,
    generate_client_report,
    get_global_content_library,
    bulk_discard_content,
    add_source_to_blacklist,
    get_source_blacklist,
    remove_source_from_blacklist,
    associate_content_to_client,
    correct_content_classification,
    get_content_quality_stats
)
from radar_report import generate_client_report
# 引入快报模块
from radar_flash import (
    fetch_all_flashes, 
    get_published_flashes, 
    get_raw_flashes,
    add_flash_config,
    delete_flash_config,
    get_flash_configs
)

# 引入认证模块
from radar_auth import (
    User, Token, get_current_active_user, get_admin_user, 
    create_access_token, verify_password, get_user, create_user,
    list_users, update_user_role, delete_user
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 定义数据模型 ===
class PredictionRequest(BaseModel):
    keywords: List[str]

class AiAnalyzeReq(BaseModel):
    topic: str

class AiOutlineReq(BaseModel):
    title: str
    angle: str
    context: Optional[str] = ""

class AiArticleReq(BaseModel):
    title: str
    outline: List
    context: Optional[str] = ""

class AdvancedRule(BaseModel):
    rule_name: str
    must_contain: List[str]
    nearby_words: List[str]
    distance: int = 50
    risk_level: int = 3

class ClientConfigReq(BaseModel):
    client_id: Optional[str] = None
    name: str
    industry: str = "综合"
    status: int = 1       
    brand_keywords: List[str]
    exclude_keywords: List[str]
    advanced_rules: List[AdvancedRule]

class DeleteReq(BaseModel):
    client_id: str

# 报告请求模型
class ReportReq(BaseModel):
    client_id: str

# 注册请求模型
class RegisterReq(BaseModel):
    username: str
    password: str
    email: str = ""

# 权限修改请求
class RoleReq(BaseModel):
    username: str
    role: str
    status: int

# === 认证接口 ===

@app.post("/auth/register")
def register(req: RegisterReq):
    success, msg = create_user(User(username=req.username, email=req.email), req.password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"msg": "User created successfully"}

@app.post("/auth/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# === 管理员接口 ===

@app.get("/admin/users")
def get_all_users(admin: User = Depends(get_admin_user)):
    return list_users()

@app.post("/admin/user/role")
def change_user_role(req: RoleReq, admin: User = Depends(get_admin_user)):
    update_user_role(req.username, req.role, req.status)
    return {"status": "success"}

@app.post("/admin/user/delete")
def remove_user(req: RoleReq, admin: User = Depends(get_admin_user)):
    if delete_user(req.username):
        return {"status": "success"}
    return {"status": "failed", "msg": "Cannot delete admin"}

# === 业务接口 (部分加权保护) ===

@app.get("/")
def read_root(): return {"msg": "Running"}

@app.get("/hotlist")
def read_hotlist(category: str = "综合", user: User = Depends(get_current_active_user)):
    raw = get_weibo_hot_list(category)
    flat = []
    for k,v in raw.items(): flat.extend(v)
    monitor_res = process_monitor_data(flat)
    return {"data": raw, "alerts": monitor_res['alerts']}

@app.post("/ai/analyze")
def api_analyze_topic(req: AiAnalyzeReq, user: User = Depends(get_current_active_user)):
    raw = generate_analysis(req.topic)
    angles = (raw or {}).get("angles", []) if isinstance(raw, dict) else []
    titles = (raw or {}).get("titles", []) if isinstance(raw, dict) else []
    strategies = []
    for i in range(max(len(angles), len(titles), 3)):
        strategies.append({
            "angle": angles[i] if i < len(angles) else f"角度{i+1}",
            "icon": "✨",
            "title": titles[i] if i < len(titles) else req.topic,
            "reason": (raw or {}).get("emotion", "") if isinstance(raw, dict) else ""
        })
    return {"status": "success", "data": {"topic": req.topic, "analysis": (raw or {}).get("emotion", ""), "strategies": strategies}}

@app.post("/analyze")
def api_analyze_topic_compat(req: AiAnalyzeReq, user: User = Depends(get_current_active_user)):
    raw = generate_analysis(req.topic)
    angles = (raw or {}).get("angles", []) if isinstance(raw, dict) else []
    titles = (raw or {}).get("titles", []) if isinstance(raw, dict) else []
    strategies = []
    for i in range(max(len(angles), len(titles), 3)):
        strategies.append({
            "angle": angles[i] if i < len(angles) else f"角度{i+1}",
            "icon": "✨",
            "title": titles[i] if i < len(titles) else req.topic,
            "reason": (raw or {}).get("emotion", "") if isinstance(raw, dict) else ""
        })
    return {"status": "success", "data": {"topic": req.topic, "analysis": (raw or {}).get("emotion", ""), "strategies": strategies}}

@app.post("/ai/outline")
def api_generate_outline(req: AiOutlineReq, user: User = Depends(get_current_active_user)):
    raw = generate_smart_outline(req.title, req.angle, req.context or "")
    structure = []
    for item in (raw or {}).get("structure", []):
        structure.append({
            "title": item.get("title", ""),
            "sub_points": item.get("sub_points", [])
        })
    return {"status": "success", "data": {"structure": structure}}

@app.post("/generate_outline")
def api_generate_outline_compat(req: AiOutlineReq, user: User = Depends(get_current_active_user)):
    raw = generate_smart_outline(req.title, req.angle, req.context or "")
    structure = []
    for item in (raw or {}).get("structure", []):
        structure.append({
            "title": item.get("title", ""),
            "sub_points": item.get("sub_points", [])
        })
    return {"status": "success", "data": {"structure": structure}}

@app.post("/generate_article")
def api_generate_article(req: AiArticleReq, user: User = Depends(get_current_active_user)):
    text = generate_full_article(req.title, req.outline, context_info=req.context or "")
    return {"status": "success", "data": text}

# NEW: Global Prediction API
@app.get("/prediction/trends")
def get_predicted_trends(user: User = Depends(get_current_active_user)):
    """
    Get global hotspot predictions based on acceleration logic.
    """
    data = predict_future_trends()
    return {"count": len(data), "data": data}

@app.post("/predictions")
def read_predictions(req: PredictionRequest, user: User = Depends(get_current_active_user)):
    data = generate_predictions(req.keywords)
    return {"count": len(data), "data": data}

@app.get("/monitor/dashboard")
def read_dash(client_id: Optional[str] = None, user: User = Depends(get_current_active_user)): 
    return get_monitor_stats(client_id)

@app.get("/monitor/clients")
def read_clients(user: User = Depends(get_current_active_user)):
    return get_all_clients()

@app.post("/monitor/client/save")
def save_client(req: ClientConfigReq, user: User = Depends(get_current_active_user)):
    # 只有 admin 和 editor 可以修改配置
    if user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    logic = {
        "brand_keywords": req.brand_keywords,
        "exclude_keywords": req.exclude_keywords,
        "advanced_rules": [r.dict() for r in req.advanced_rules]
    }
    return save_full_client_config(req.name, req.industry, req.status, logic, req.client_id)

@app.post("/monitor/client/delete")
def delete_client(req: DeleteReq, user: User = Depends(get_admin_user)):
    # 只有 admin 可以删除
    return delete_client_by_id(req.client_id)

@app.post("/monitor/report/generate")
def create_report_endpoint(req: ReportReq, user: User = Depends(get_current_active_user)):
    data = generate_client_report(req.client_id)
    return {"status": "success", "data": data}

# ==========================================
# === 全网内容库管理接口 ===
# ==========================================

class ContentFilterReq(BaseModel):
    search_text: str = ""
    source_filter: Optional[List[str]] = None
    sentiment_filter: Optional[List[str]] = None
    clean_status_filter: Optional[List[str]] = None
    time_range: str = "24h"  # "1h" / "24h" / "7d" / "all"
    page: int = 1
    page_size: int = 20

class BulkDiscardReq(BaseModel):
    mention_ids: List[int]

class BlacklistReq(BaseModel):
    source_name: str
    reason: str = ""

class AssociateReq(BaseModel):
    mention_id: int
    client_id: str

class CorrectionReq(BaseModel):
    mention_id: int
    new_category: Optional[str] = None
    new_sentiment: Optional[str] = None

# [API-1] 全网内容库检索
@app.post("/content/library/search")
def search_content_library(req: ContentFilterReq, user: User = Depends(get_current_active_user)):
    """
    全网内容库检索，支持多维度筛选
    """
    try:
        result = get_global_content_library(
            search_text=req.search_text,
            source_filter=req.source_filter,
            sentiment_filter=req.sentiment_filter,
            clean_status_filter=req.clean_status_filter,
            time_range=req.time_range,
            page=req.page,
            page_size=req.page_size
        )
        return result
    except Exception as e:
        print(f"[ERROR] 搜索内容库失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# [API-2] 批量废弃内容
@app.post("/content/library/bulk-discard")
def discard_content_items(req: BulkDiscardReq, user: User = Depends(get_current_active_user)):
    """批量标记内容为已废弃"""
    if user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    return bulk_discard_content(req.mention_ids)

# [API-3] 添加信源到黑名单
@app.post("/content/blacklist/add")
def add_to_blacklist(req: BlacklistReq, user: User = Depends(get_current_active_user)):
    """添加信源到黑名单"""
    if user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    return add_source_to_blacklist(req.source_name, reason=req.reason, created_by=user.username)

# [API-4] 获取黑名单
@app.get("/content/blacklist")
def fetch_blacklist(user: User = Depends(get_current_active_user)):
    """获取黑名单列表"""
    return get_source_blacklist()

# [API-5] 从黑名单移除信源
@app.post("/content/blacklist/remove")
def remove_from_blacklist(req: BlacklistReq, user: User = Depends(get_admin_user)):
    """从黑名单移除信源"""
    return remove_source_from_blacklist(req.source_name)

# [API-6] 手动关联内容到客户
@app.post("/content/associate")
def associate_to_client(req: AssociateReq, user: User = Depends(get_current_active_user)):
    """手动关联内容到特定客户"""
    if user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    return associate_content_to_client(req.mention_id, req.client_id, assigned_by=user.username)

# [API-7] 人工纠偏：修正 AI 判定
@app.post("/content/correct")
def correct_ai_judgment(req: CorrectionReq, user: User = Depends(get_current_active_user)):
    """编辑手动修正 AI 的自动分类和情感判定"""
    if user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    return correct_content_classification(
        req.mention_id,
        new_category=req.new_category,
        new_sentiment=req.new_sentiment,
        corrected_by=user.username
    )

# ==========================================
# [API-8] 数据质检统计
@app.get("/content/quality-stats")
def fetch_quality_stats(user: User = Depends(get_current_active_user)):
    """获取数据质检统计"""
    return get_content_quality_stats()

# ==========================================
# [API-9] 快报监控相关接口 (Flash News)
# ==========================================

# 引入快报模块 (Updated)
from radar_flash import (
    init_flash_db,
    fetch_all_flashes, 
    backfill_rewrite,
    get_flashes,
    update_flash_status
)

# ...

@app.get("/flash/list")
def read_flash_list(status: str = "all", source: str = "all", limit: int = 50, user: User = Depends(get_current_active_user)):
    """获取快报列表
    status: 'all' | 'draft' | 'published' | 'discarded'
    """
    return get_flashes(status, limit, source)

@app.post("/flash/update")
def update_flash(
    id: int = Body(...), 
    status: str = Body(...), 
    content: Optional[str] = Body(None),
    title: Optional[str] = Body(None),
    user: User = Depends(get_current_active_user)
):
    """更新快报状态或内容"""
    if user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    return update_flash_status(id, status, content, title)

@app.get("/flash/fetch")
def trigger_flash_fetch(source: str = "cls", user: User = Depends(get_current_active_user)):
    """手动触发快报抓取 (Also triggers at interval in background usually)"""
    items = fetch_all_flashes(source)
    return {"status": "success", "count": len(items)}

@app.post("/flash/backfill")
def trigger_flash_backfill(limit: int = Body(10), user: User = Depends(get_current_active_user)):
    """对缺失改写的草稿进行补写"""
    backfill_rewrite(limit=limit)
    return {"status": "success"}

@app.post("/flash/config/add")
def add_flash_cfg(type: str, value: str, user: User = Depends(get_admin_user)):
    return add_flash_config(type, value)

@app.get("/flash/config/list")
def list_flash_cfg(user: User = Depends(get_current_active_user)):
    return get_flash_configs()

@app.post("/flash/config/delete")
def del_flash_cfg(id: int, user: User = Depends(get_admin_user)):
    return delete_flash_config(id)

@app.on_event("startup")
def startup_event():
    # Ensure flash tables and migrations are applied
    try:
        init_flash_db()
    except Exception as e:
        print(f"[flash] init failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)