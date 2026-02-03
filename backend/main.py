from fastapi import FastAPI, Body, Depends, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional

# === 引入各功能模块 ===
from radar_weibo import get_weibo_hot_list
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
from ai_engine import generate_analysis, generate_outline, generate_article_from_outline, polish_interview_notes, refine_article_with_chat
# from radar_ai import analyze_topic_deeply, generate_full_outline
import io
from fastapi import UploadFile, File

# ... (omitted)

@app.post("/ai/analyze")
def api_analyze_topic(req: AiAnalyzeReq, user: User = Depends(get_current_active_user)):
    """深度分析话题，返回选题策略（strategies: angle, title, reason, outline）"""
    # 切换回 ai_engine (DeepSeek)
    
    # 尝试获取实时热点上下文
    hot_context = []
    try:
        hot_list = get_weibo_hot_list()
        hot_context = [h['title'] for h in hot_list]
    except:
        pass
        
    # 如果有 instruction，拼接到 topic 中 (ai_engine 暂无独立 instruction 字段)
    topic_query = req.topic
    if req.instruction:
        topic_query += f" (Note: {req.instruction})"

    data = generate_analysis(topic_query, hot_context=hot_context)
    return {"status": "success", "data": data}

@app.post("/ai/outline")
def api_generate_outline_ai(req: AiOutlineReq, user: User = Depends(get_current_active_user)):
    """根据话题+角度生成详细大纲（h1 + text），转为前端 structure 格式"""
    # 切换回 ai_engine (DeepSeek)
    structure = generate_outline(req.topic, req.angle)
    
    # 兼容处理
    if structure and isinstance(structure[0], str):
         structure = [{"title": s, "sub_points": []} for s in structure]
         
    return {"status": "success", "data": {"structure": structure}}

# === 今日热点-极速成稿：备用 ai_engine 选题/大纲/成文 ===
class AnalyzeTopicReq(BaseModel):
    topic: str

class GenerateOutlineReq(BaseModel):
    title: str
    angle: str
    context: Optional[str] = ""

class GenerateArticleReq(BaseModel):
    title: str
    outline: List[dict]  # [{ title, sub_points }] 或 前端传 structure
    context: Optional[str] = ""

@app.post("/analyze")
def analyze_topic(req: AnalyzeTopicReq, user: User = Depends(get_current_active_user)):
    """选题分析：返回情绪、角度、爆款标题建议（财经科技媒体向）"""
    # 尝试混入实时热点上下文
    hot_context = []
    try:
        hot_list = get_weibo_hot_list()
        hot_context = [h['title'] for h in hot_list]
    except:
        pass

    result = generate_analysis(req.topic, hot_context=hot_context)
    return result

@app.post("/generate_outline")
def api_generate_outline(req: GenerateOutlineReq, user: User = Depends(get_current_active_user)):
    """生成文章大纲，返回 structure: [{ title, sub_points }]"""
    sections = generate_outline(req.title, req.angle)
    # 兼容前端：sections 为字符串数组时转为 structure
    if sections and isinstance(sections[0], str):
        structure = [{"title": s, "sub_points": []} for s in sections]
    else:
        structure = sections
    return {"status": "success", "data": {"structure": structure}}

@app.post("/generate_article")
def api_generate_article(req: GenerateArticleReq, user: User = Depends(get_current_active_user)):
    """根据大纲生成全文（财经科技行业媒体风格）"""
    outline = req.outline
    if isinstance(outline, list) and outline and isinstance(outline[0], dict):
        pass  # 已是 structure
    else:
        outline = [{"title": str(s), "sub_points": []} for s in (outline or [])]
    full_text = generate_article_from_outline(req.title, outline, req.context or "")
    return {"status": "success", "data": full_text}

# ==========================================
# === 全网内容库管理接口 ===
# ==========================================

class ContentFilterReq(BaseModel):
    search_text: str = ""
    client_id: Optional[str] = None  # Added for filtering by client
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
            client_id=req.client_id,
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

# [API-8] 数据质检统计
@app.get("/content/quality-stats")
def fetch_quality_stats(user: User = Depends(get_current_active_user)):
    """获取数据质检统计"""
    return get_content_quality_stats()

# ==========================================
# === 智能创作 - 文章管理接口 ===
# ==========================================
from radar_articles import save_article, get_articles, get_article_detail, delete_article

class ArticleSaveReq(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    summary: str = ""
    cover_url: str = ""
    topic: str = ""
    status: str = "draft"  # draft, published

class ArticleListReq(BaseModel):
    page: int = 1
    page_size: int = 10
    status: Optional[str] = None  # draft, published, all
    search: Optional[str] = None

class ArticleDelReq(BaseModel):
    id: int

@app.post("/articles/save")
def article_save(req: ArticleSaveReq, user: User = Depends(get_current_active_user)):
    """保存或发布文章（草稿/已发布）"""
    return save_article(
        user_id=user.username,
        title=req.title,
        content=req.content,
        summary=req.summary,
        cover_url=req.cover_url,
        topic=req.topic,
        status=req.status,
        article_id=req.id
    )

@app.post("/articles/list")
def article_list(req: ArticleListReq, user: User = Depends(get_current_active_user)):
    """获取文章列表（我的作品）"""
    return get_articles(
        user_id=user.username,
        status=req.status,
        search=req.search,
        page=req.page,
        page_size=req.page_size
    )

@app.get("/articles/{article_id}")
def article_detail(article_id: int, user: User = Depends(get_current_active_user)):
    """获取单篇文章详情"""
    art = get_article_detail(article_id)
    if not art:
        raise HTTPException(status_code=404, detail="Article not found")
    if art['user_id'] != user.username and user.role != 'admin':
         # Simple privacy check
         raise HTTPException(status_code=403, detail="Permission denied")
    return {"status": "success", "data": art}

@app.post("/articles/delete")
def article_delete(req: ArticleDelReq, user: User = Depends(get_current_active_user)):
    """删除文章"""
    res = delete_article(req.id, user.username)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


class RefineReq(BaseModel):
    content: str
    instruction: str

@app.post("/ai/refine")
def refine_article_endpoint(req: RefineReq):
    new_content = refine_article_with_chat(req.content, req.instruction)
    return {"content": new_content}

# === AI 润色接口 ===
@app.post("/ai/polish/upload")
async def polish_uploaded_file(file: UploadFile = File(...), instruction: Optional[str] = Form(None)):
    """
    上传 .docx 或 .txt 文件，读取内容并进行 AI 润色
    """
    content = ""
    filename = file.filename.lower()
    
    try:
        contents = await file.read()
        
        if filename.endswith(".docx"):
            import docx
            doc = docx.Document(io.BytesIO(contents))
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            content = "\n".join(full_text)
            
        elif filename.endswith(".txt"):
            content = contents.decode("utf-8")
        elif filename.endswith(".pdf"):
            import pdfplumber
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                full_text = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text.append(text)
                content = "\n".join(full_text)
        else:
            raise HTTPException(status_code=400, detail="Use .docx, .pdf or .txt files")
            
        if len(content.strip()) < 10:
             raise HTTPException(status_code=400, detail="File content is too short")

        # Call AI (Now returns dict {title, summary, content})
        # Note: We need to update polish_interview_notes to accept instruction
        result = polish_interview_notes(content, instruction)
        return {"data": result}
        
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class PolishTextReq(BaseModel):
    content: str
    instruction: Optional[str] = None

@app.post("/ai/polish/text")
def polish_raw_text_endpoint(req: PolishTextReq):
    """直接润色文本"""
    if len(req.content.strip()) < 10:
        raise HTTPException(status_code=400, detail="Content is too short")
    try:
        result = polish_interview_notes(req.content, req.instruction)
        return {"data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from ai_engine import generate_analysis, generate_outline, generate_article_from_outline, polish_interview_notes, refine_article_with_chat, generate_cover_image, smart_parse_topic

# ... existing code ...

class TopicParseReq(BaseModel):
    text: str

@app.post("/ai/topic/smart-parse")
def api_smart_parse_topic(req: TopicParseReq):
    topic = smart_parse_topic(req.text)
    return {"status": "success", "topic": topic}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)