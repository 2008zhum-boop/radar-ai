<template>
  <div class="editor-layout">
    
    <!-- 全屏 Header -->
    <header class="editor-header">
      <div class="header-left">
        <button class="back-btn" @click="$emit('back')">
          <span class="icon">🔙</span> 退出创作
        </button>
        <div class="doc-info" v-if="!isStep1">
           <span class="ai-badge">AI 创作模式</span>
           <span class="doc-title-text">{{ initialData.title || articleTitle || '未命名文档' }}</span>
        </div>
      </div>
      
      <div class="header-right" v-if="!isStep1">
        <button class="action-btn text" @click="showPreview = true">
           <span class="icon">👁️</span> 预览
        </button>
        <button class="action-btn text" @click="showAuditModal = true">
           <span class="icon">🛡️</span> 智能校对
        </button>
        <button class="action-btn text" @click="saveDraft" :disabled="isSaving">
           <span class="icon">💾</span> {{ isSaving ? '保存中...' : '存草稿' }}
        </button>
        <div class="divider"></div>
        <button class="action-btn primary" @click="showPublishModal = true">
           发布设置
        </button>
      </div>
    </header>

    <!-- 主体区域 -->
    <div class="editor-body">
      
      <!-- STEP 1: 选题/角度选择 (居中显示的初始状态) -->
      <div v-if="isStep1" class="step-zero-container">
         <div class="strategy-selector">
            <h2 class="welcome-title">
               <span class="emoji">✨</span> 
               解析话题：{{ initialData.topic || '当前热点' }}
            </h2>
            <p class="welcome-sub" v-if="!loadingStrategies">AI 已分析全网舆情，为您推荐以下创作切入点：</p>

            <div v-if="loadingStrategies" class="loading-state-lg">
               <div class="spinner lg"></div>
               <p>{{ loadingText || '正在深度分析舆论风向...' }}</p>
            </div>

            <div v-else class="cards-grid">
              <div 
                v-for="(strat, idx) in strategies" 
                :key="idx" 
                class="strategy-card"
                @click="selectStrategy(strat)"
              >
                <div class="card-icon">{{ strat.icon || '💡' }}</div>
                <h3 class="card-title">{{ strat.title }}</h3>
                <div class="card-tag">{{ strat.angle }}</div>
                <p class="card-reason">{{ strat.reason }}</p>
              </div>
            </div>

            <!-- 底部对话修改区 -->
            <div class="refine-container" v-if="!loadingStrategies">
                <div class="chat-input-wrapper">
                    <input 
                      v-model="chatInput" 
                      @keyup.enter="refineStrategies" 
                      placeholder="输入您的特定选题方向，回车直接生成大纲（如：'写一篇关于大学生就业的深度文'）..." 
                      class="chat-input"
                    />
                    <button class="chat-send-btn" @click="refineStrategies" :disabled="!chatInput.trim()">
                       ⬆
                    </button>
                </div>
            </div>
         </div>
      </div>

      <!-- STEP 2 & 3: 双栏创作模式 (左大纲，右正文) -->
      <div v-else class="workspace-container">
        
        <!-- Column 1: Chat Interaction (Left) -->
        <aside class="col-chat">
           <div class="chat-header">
              <span class="chat-title">✨ AI 助手</span>
           </div>
           
           <div class="chat-messages" ref="msgContainer">
               <div v-for="(msg, i) in messages" :key="i" class="chat-bubble" :class="msg.role">
                   <div class="cb-avatar">
                        <span v-if="msg.role === 'ai'">🤖</span>
                        <span v-else-if="msg.role === 'file'">📄</span>
                        <span v-else>👤</span>
                   </div>
                   
                   <!-- File Record -->
                   <div v-if="msg.role === 'file'" class="cb-content file-record">
                       <div class="file-icon">DOC</div>
                       <div class="file-info">
                           <span class="fname">{{ msg.content }}</span>
                           <span class="ftag">已解析</span>
                       </div>
                   </div>
                   
                   <!-- Text Message -->
                   <div v-else class="cb-content">{{ msg.content }}</div>
               </div>
               
               <div v-if="chatLoading" class="chat-bubble ai checking">
                   <div class="cb-avatar">🤖</div>
                   <div class="cb-dots"><span>.</span><span>.</span><span>.</span></div>
               </div>
           </div>

           <!-- Quick Actions & Input -->
           <div class="chat-footer">
               <div class="quick-chips-scroll" v-if="!chatLoading">
                   <button class="chip-pill" @click="sendRefineOrder('更专业')">更专业</button>
                   <button class="chip-pill" @click="sendRefineOrder('丰富细节')">丰富细节</button>
                   <button class="chip-pill" @click="sendRefineOrder('精简篇幅')">精简篇幅</button>
                   <button class="chip-pill" @click="sendRefineOrder('调整为口语')">调整为口语</button>
               </div>
               <div class="chat-input-box">
                   <textarea 
                       v-model="chatInput" 
                       @keyup.enter.exact="sendRefineOrder(chatInput)"
                       placeholder="输入修改指令..." 
                       rows="1"
                       class="chat-textarea"
                   ></textarea>
                   <button class="send-btn-icon" @click="sendRefineOrder(chatInput)" :disabled="!chatInput">
                       ➤
                   </button>
               </div>
           </div>
        </aside>

        <!-- Column 2: Outline Navigation (Middle) -->
        <nav class="col-outline">
            <div class="outline-header">
                <h3>大纲导航</h3>
                <button class="icon-refresh" @click="fetchOutline" title="刷新大纲">🔄</button>
            </div>
            
            <div v-if="outlineLoading" class="outline-loading">
                <div class="spinner sm"></div> 解析结构中...
            </div>
            
            <div v-else class="outline-list">
                <div v-for="(section, idx) in outlineData.structure" :key="idx" class="outline-item" @click="scrollToSection(section.id)">
                    <div class="outline-title-row">
                        <span class="idx">{{ idx + 1 }}</span>
                        <span class="txt">{{ section.title }}</span>
                    </div>
                </div>
                <div class="outline-empty" v-if="!outlineData.structure.length">
                    暂无大纲结构
                </div>
            </div>
            
            <div class="outline-bottom-action">
                <button class="regen-btn" @click="generateFullArticle" :disabled="writing">
                    <span v-if="writing">正在生成...</span>
                    <span v-else>✨ 重新生成全文</span>
                </button>
            </div>
        </nav>

        <!-- COL 3: Main Editor -->
        <div class="col-editor-scroll">
            <div class="editor-main-area">
                <div class="editor-meta-inputs">
                    <input 
                        v-model="articleTitle" 
                        class="title-input" 
                        placeholder="请输入文章标题"
                    />
                    <textarea 
                        v-model="articleSummary" 
                        class="summary-input" 
                        placeholder="输入文章摘要..."
                        rows="2"
                    ></textarea>
                </div>

                <div class="immersive-editor">
                    <QuillEditor 
                        ref="quillRef"
                        v-model:content="articleContent" 
                        contentType="html" 
                        theme="snow" 
                        toolbar="full" 
                        class="editor-content"
                        placeholder="在此处开始写作，或利用左侧 AI 大纲自动生成内容..."
                    />
                </div>
            </div>
           <!-- 写作中的遮罩 -->
           <div v-if="writing" class="writing-overlay">
              <div class="writing-status">
                 <span class="cursor-blink">AI 正在疯狂码字中...</span>
              </div>
           </div>
        </div>

      </div>

    </div>

    <!-- 预览模态框 -->
    <div v-if="showPreview" class="modal-fullscreen">
       <div class="preview-container">
          <div class="preview-chrome">
             <div class="chrome-header">
                <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
                <span class="chrome-title">文章预览 (移动端视图)</span>
                <button class="close-preview" @click="showPreview = false">✕</button>
             </div>
             <div class="chrome-body">
                <div class="article-preview-content">
                   <h1 class="p-title">{{ articleTitle }}</h1>
                   <div class="p-meta">
                      <span class="p-author">智能助手</span>
                      <span class="p-time">2026-02-01</span>
                   </div>
                   <div class="p-summary" v-if="articleSummary">
                      <strong>摘要：</strong>{{ articleSummary }}
                   </div>
                   <div class="p-body ql-editor" v-html="articleContent"></div>
                </div>
             </div>
          </div>
       </div>
    </div>

    <!-- 发布设置模态框 (原 Header 右侧内容 + 封面设置) -->
    <div v-if="showPublishModal" class="modal-overlay">
       <div class="modal-dialog">
          <div class="modal-header">
             <h3>发布设置</h3>
             <button class="close-btn" @click="showPublishModal = false">×</button>
          </div>
          <div class="modal-body-scroll">
             <div class="setting-group">
                <label>文章封面</label>
                <div class="cover-uploader-lg">
                   <img v-if="coverUrl" :src="coverUrl" class="cover-preview" />
                   <div v-else class="cover-bg-placeholder" @click="generateCover">
                      <div class="ph-content">
                         <span class="icon">🖼️</span>
                         <span>点击 AI 生成封面</span>
                      </div>
                   </div>
                   <button v-if="coverUrl" class="regen-cover-btn" @click="generateCover">🔄 重新生成</button>
                   <div v-if="generatingCover" class="cover-loading-mask">Generating...</div>
                </div>
             </div>

             <div class="setting-group">
                <label>文章标题</label>
                <input v-model="articleTitle" class="form-input lg" />
             </div>

             <div class="setting-group">
                <label>摘要</label>
                <textarea v-model="articleSummary" class="form-input" rows="4"></textarea>
             </div>
          </div>
          <div class="modal-footer">
             <button class="action-btn outline" @click="showPublishModal = false">取消</button>
             <button class="action-btn primary" @click="handleRealPublish">确认发布</button>
          </div>
       </div>
    </div>

    <!-- 智能审查模态框 (保持不变，或微调样式) -->
    <div v-if="showAuditModal" class="modal-overlay">
       <div class="modal-dialog">
          <div class="modal-header">
             <h3>智能合规审查</h3>
             <button class="close-btn" @click="showAuditModal = false">×</button>
          </div>
          <div class="modal-body-scroll">
             <div v-if="auditing" class="audit-loading">
                <div class="spinner"></div>
                <p>正在扫描...</p>
             </div>
             <div v-else>
                <div class="audit-score-ban">
                    <span class="score-val" :class="getScoreClass(auditResult.score)">{{ auditResult.score }}</span>
                    <span class="score-label">健康分</span>
                </div>
                <!-- 略微简化的结果展示 -->
                <div class="audit-list">
                   <div class="audit-item" v-if="auditResult.sensitiveWords.length">
                      <h4>敏感词</h4>
                      <div class="tags"><span v-for="w in auditResult.sensitiveWords" class="tag red">{{w}}</span></div>
                   </div>
                   <div class="audit-item" v-else>
                      <h4>敏感词</h4>
                      <p class="safe-text">✅ 未发现敏感词</p>
                   </div>
                   
                   <div class="audit-item" v-if="auditResult.typos.length">
                      <h4>建议修改</h4>
                      <ul>
                        <li v-for="t in auditResult.typos">原文“{{t.src}}” → 建议“{{t.dst}}”</li>
                      </ul>
                   </div>
                   <div class="audit-item" v-else>
                      <h4>建议修改</h4>
                       <p class="safe-text">✅ 文案通顺</p>
                   </div>
                </div>
             </div>
          </div>
          <div class="modal-footer">
             <button class="action-btn primary" @click="showAuditModal = false">完成</button>
          </div>
       </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed, watch, nextTick } from 'vue'
import { analyzeTopic, generateOutline, generateArticle, getArticleDetail, saveArticle, refineArticle, generateCover as apiGenerateCover } from '../services/api' 

const props = defineProps({
  initialData: Object, // { topic, polishData: {title, summary, content} }
  articleId: [Number, String],
  mode: { type: String, default: 'create' } // 'create' | 'polish'
})
const emit = defineEmits(['back'])

// --- State ---
const isStep1 = ref(true) // True: 选角度阶段; False: 写作阶段(Outline+Editor)
const loadingStrategies = ref(false)
const loadingText = ref('')
const strategies = ref([])
const selectedStrategy = ref({})
const chatInput = ref('')


// Outline & Chat
const sidebarMode = ref('outline') // 'outline' | 'chat'
const outlineLoading = ref(false)
const outlineData = ref({ structure: [] })
const messages = ref([]) 
const chatLoading = ref(false)

// Editor
const writing = ref(false)
const articleTitle = ref('')
const articleSummary = ref('')
const articleContent = ref('') 
const coverUrl = ref('')
const generatingCover = ref(false)
const isSaving = ref(false)

// Modals
const showPreview = ref(false)
const showPublishModal = ref(false)
const showAuditModal = ref(false)
const auditing = ref(false)
const auditResult = reactive({ score: 100, sensitiveWords: [], typos: [] })

// --- Life Cycle ---
onMounted(async () => {
    // Mode Switch
    if (props.mode === 'polish' && props.initialData?.polishData) {
        // Polish Mode Initialization
        const pd = props.initialData.polishData
        articleTitle.value = pd.title || ''
        articleSummary.value = pd.summary || ''
        articleContent.value = pd.content || ''
        isStep1.value = false
        sidebarMode.value = 'chat'
        
        // Initial Greeting
        // 1. Add File Record
        if (pd.filename) {
            messages.value.push({ role: 'file', content: pd.filename })
        } else {
             messages.value.push({ role: 'file', content: '上传文档.docx' })
        }
        
        // 2. Add AI Greeting
        messages.value.push({ role: 'ai', content: '文档已深度润色完成。您可以直接在右侧编辑，或者在对话框中告诉我修改建议（例如：“增加更多数据支撑”、“调整为通俗口语化”等）。' })

        // 3. Auto-generate Outline from Content (Mock Extraction)
        // In a real scenario, we would parse the markdown headers (#, ##).
        // Here we try to simulate it or call the API if structure is missing.
        generateOutlineFromContent(pd.content)
    } 
    // Create / Edit Mode
    else if (props.articleId) {
        await loadArticle(props.articleId)
    } else {
        // Create Mode
        const topic = props.initialData?.topic || "当前热点话题"
        const instruction = props.initialData?.instruction || null
        await fetchStrategies(topic, instruction)
    }

    // 4. Handle Expand Mode
    if (props.mode === 'expand' && props.initialData?.expandData) {
        const ed = props.initialData.expandData
        isStep1.value = false
        articleTitle.value = ed.topic || '未命名选题'
        
        // Parse raw outline text to structure
        const structure = parseOutlineText(ed.outline)
        outlineData.value = { structure }
        
        // Trigger auto-generation
        // Use nextTick to ensure UI is ready
        nextTick(() => {
            generateFullArticle()
        })
    }
})

// Helper: Parse raw text outline to structure
const parseOutlineText = (text) => {
    if (!text) return []
    const lines = text.split('\n').map(l => l.trim()).filter(l => l)
    const structure = []
    let currentSection = null
    
    // Simple heuristic regexes
    // Matches: "1. Title", "一、Title", "# Title", "Chapter 1", "第一章"
    const titleRegex = /^([一二三四五六七八九十0-9]+[、.]|第[一二三四五六七八九十0-9]+[章节部分]|#+)\s*(.*)/
    
    lines.forEach(line => {
         // If line looks like a main title or explicit header
         if (titleRegex.test(line) || !currentSection) {
             // Create new section
             currentSection = {
                 id: `heading-${structure.length}`,
                 title: line.replace(/^[#\s]+/, ''), // clean markup
                 sub_points: []
             }
             structure.push(currentSection)
         } else {
             // Treat as sub point
             currentSection.sub_points.push(line.replace(/^[-*•]\s*/, ''))
         }
    })
    
    // Fallback if structure is empty but text exists (single block)
    if (structure.length === 0 && lines.length > 0) {
        structure.push({ title: '核心内容', sub_points: lines, id: 'heading-0' })
    }
    
    return structure
}

const loadArticle = async (id) => {
    try {
        const res = await getArticleDetail(id)
        if (res.status === 'success') {
            const data = res.data
            articleTitle.value = data.title
            articleContent.value = data.content
            articleSummary.value = data.summary
            coverUrl.value = data.cover_url
            // Switch to step 2 directly
            isStep1.value = false
        }
    } catch (e) {
        alert("加载文章失败: " + e.message)
        emit('back')
    }
}

// ... (fetchStrategies and friends unchanged) ...

const saveDraft = async () => {
    if (!articleTitle.value) return alert("请填写标题")
    isSaving.value = true
    try {
        await saveArticle({
            id: props.articleId ? parseInt(props.articleId) : undefined,
            title: articleTitle.value,
            content: articleContent.value,
            summary: articleSummary.value,
            cover_url: coverUrl.value,
            topic: props.initialData?.topic || '',
            status: 'draft'
        })
        alert("草稿已保存")
    } catch (e) {
        alert("保存失败: " + e.message)
    } finally {
        isSaving.value = false
    }
}

const handleRealPublish = async () => {
    if (!articleTitle.value) return alert("请填写标题")
    isSaving.value = true
    try {
        await saveArticle({
            id: props.articleId ? parseInt(props.articleId) : undefined,
            title: articleTitle.value,
            content: articleContent.value,
            summary: articleSummary.value,
            cover_url: coverUrl.value,
            topic: props.initialData?.topic || '',
            status: 'published'
        })
        alert("发布成功！文章已存入作品库。")
        showPublishModal.value = false
        emit('back')
    } catch (e) {
        alert("发布失败: " + e.message)
    } finally {
        isSaving.value = false
    }
}

// --- Methods: Step 1 ---
const fetchStrategies = async (topic, instruction = null) => {
    loadingStrategies.value = true
    try {
        const res = await analyzeTopic(topic, instruction)
        if (res.strategies) {
            strategies.value = res.strategies
        } else {
            // Mock fallback
            strategies.value = [
                { title: `深度观察：${topic}`, angle: "深度观察", reason: "全网热议方向", icon: "👁️" },
                { title: `${topic} 背后的商业逻辑`, angle: "商业分析", reason: "适合财经受众", icon: "📊" }
            ]
        }
    } catch (e) {
        console.error(e)
    } finally {
        loadingStrategies.value = false
        loadingText.value = ''
    }
}

const refineStrategies = async () => {
    if (!chatInput.value.trim()) return
    const topic = props.initialData?.topic || "当前热点话题"
    loadingText.value = `正在根据您的指令 "${chatInput.value}" 定制选题并生成大纲...`
    
    // Smooth scroll to top to show loading state (optional, but good for feedback)
    const container = document.querySelector('.step-zero-container')
    if (container) container.scrollTo({ top: 0, behavior: 'smooth' })
    
    try {
        const res = await analyzeTopic(topic, chatInput.value)
        let targetStrategy = null
        
        if (res.strategies && res.strategies.length > 0) {
            // Take the first one as the best match
            targetStrategy = res.strategies[0]
        } else {
            // Fallback if AI fails to return list
            targetStrategy = {
                title: `${topic}：${chatInput.value}`, 
                angle: "定制视角", 
                reason: "基于您的指令生成"
            }
        }
        
        // Auto select and proceed
        selectStrategy(targetStrategy)
        
    } catch (e) {
        console.error(e)
        loadingStrategies.value = false // Stop loading if error
        alert("定制生成失败，请重试")
    } finally {
        chatInput.value = ''
        // Note: loadingStrategies will be set to false inside selectStrategy -> fetchOutline flows or implicitly hidden when v-if="isStep1" becomes false
    }
}

const selectStrategy = (strat) => {
    selectedStrategy.value = strat
    articleTitle.value = strat.title
    isStep1.value = false // Switch to 2-column view
    fetchOutline()
}

// --- Methods: Outline ---
const fetchOutline = async () => {
    outlineLoading.value = true
    try {
        const res = await generateOutline(selectedStrategy.value.title, selectedStrategy.value.angle, props.initialData.topic)
        if (res && res.status === 'success' && res.data) {
           outlineData.value = res.data
        }
    } catch (e) {
        console.error(e)
    } finally {
        outlineLoading.value = false
    }
}

const insertSection = (section) => {
    const points = section.sub_points || []
    let html = `<h2>${section.title || '新章节'}</h2>`
    if (points.length) {
        html += `<ul>${points.map(p => `<li>${p}</li>`).join('')}</ul>`
    }
    html += `<p><br/></p>`
    // Append to content (simple concat for now, better to use Quill API insert)
    articleContent.value += html
}

// --- Methods: Full Gen ---
const generateFullArticle = async () => {
    writing.value = true
    try {
        const res = await generateArticle(
           articleTitle.value,
           outlineData.value.structure,
           props.initialData.topic,
           props.initialData.selectionId
        )
        if (res && res.status === 'success' && res.data) {
            let html = res.data
                .replace(/^# (.*)/gm, '<h1>$1</h1>')
                .replace(/^## (.*)/gm, '<h2>$1</h2>')
                .replace(/^### (.*)/gm, '<h3>$1</h3>')
                .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
                .replace(/\n/g, '<br/>')
            articleContent.value = html
            articleSummary.value = res.data.substring(0, 100).replace(/<[^>]+>/g, '') + '...'
            
            // Auto trigger audit & cover gen (silently)
            if (!coverUrl.value) generateCover()
            runAudit()
        }
    } catch (e) {
        alert("生成失败")
    } finally {
        writing.value = false
    }
}

const generateCover = async () => {
    if (!articleTitle.value) {
        alert("请先设置文章标题")
        return
    }
    generatingCover.value = true
    try {
        // Call Real AI API
        const summaryText = articleSummary.value || articleContent.value.substring(0, 500).replace(/<[^>]+>/g, '')
        const res = await apiGenerateCover(articleTitle.value, summaryText)
        if (res && res.status === 'success' && res.url) {
            coverUrl.value = res.url
        } else {
            // Fallback (Mock) if API returns weirdness
            coverUrl.value = "https://images.unsplash.com/photo-1557683316-973673baf926?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80"
        }
    } catch (e) {
        console.error("Cover Gen Failed", e)
        alert("封面生成失败，请重试")
    } finally {
        generatingCover.value = false
    }
}

const runAudit = () => {
    auditing.value = true
    // Mock
    setTimeout(() => {
        auditResult.score = 95
        auditResult.sensitiveWords = []
        auditResult.typos = [{src:"大岗", dst:"大纲"}]
        auditing.value = false
    }, 1500)
}

const getScoreClass = (s) => s > 80 ? 'text-green-500' : 'text-orange-500'


const sendRefineOrder = async (text) => {
    if (!text || !text.trim()) return
    const order = text.trim()
    chatInput.value = ''
    
    // Add User Message
    messages.value.push({ role: 'user', content: order })
    scrollToBottom()
    
    chatLoading.value = true
    try {
        const res = await refineArticle(articleContent.value, order)
        if (res && res.content) {
            articleContent.value = res.content
            messages.value.push({ role: 'ai', content: '已根据您的要求优化文章内容，请在右侧查看。' })
            
            // Refresh Outline after refinement
            generateOutlineFromContent(res.content)
            
        } else {
             messages.value.push({ role: 'ai', content: '优化未返回有效内容。' })
        }
    } catch (e) {
        messages.value.push({ role: 'ai', content: '优化失败，请稍后重试。' })
    } finally {
        chatLoading.value = false
        scrollToBottom()
    }
}

const msgContainer = ref(null)
const scrollToBottom = () => {
    nextTick(() => {
        if (msgContainer.value) {
            msgContainer.value.scrollTop = msgContainer.value.scrollHeight
        }
    })
}

// Helper: Extract Outline from existing content (Simple Regex for now)
const generateOutlineFromContent = (content) => {
    if (!content) return
    
    // 1. Match H1, H2, H3 (Markdown style # or HTML <h1>)
    // The content from refineArticle/polish usually comes as HTML or Markdown mixed.
    // Let's assume HTML since Quill uses HTML.
    
    const div = document.createElement('div')
    div.innerHTML = content
    
    const headers = div.querySelectorAll('h1, h2, h3')
    const structure = []
    
    headers.forEach((h, index) => {
        const id = `heading-${index}`
        h.id = id // Inject ID into the DOM node
        structure.push({
            id: id,
            title: h.innerText,
            sub_points: [] 
        })
    })
    
    if (structure.length > 0) {
        // Update content with injected IDs
        // Note: This might trigger a re-render of Quill, but necessary for anchors.
        // We only update if structure changed to avoid loops, but here we assume it's called after content generation/refinement.
        if (div.innerHTML !== content) {
             articleContent.value = div.innerHTML
        }
        outlineData.value = { structure }
    } else {
        outlineData.value = { structure: [] }
    }
}

const scrollToSection = (id) => {
    if (!id) return
    // Use standard DOM scan because Quill renders real HTML
    const el = document.getElementById(id)
    if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
}
</script>

<style scoped>
/* Reset & Layout */
.editor-layout { width: 100vw; height: 100vh; background: #f8fafc; display: flex; flex-direction: column; position: fixed; top: 0; left: 0; z-index: 50; }

/* Header */
.editor-header { height: 56px; background: white; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; flex-shrink: 0; box-shadow: 0 1px 2px rgba(0,0,0,0.03); }
.header-left { display: flex; align-items: center; gap: 16px; }
.back-btn { border: none; background: #f1f5f9; padding: 4px 10px; border-radius: 4px; color: #475569; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 4px; transition: all 0.2s; }
.back-btn:hover { background: #e2e8f0; color: #1e293b; }
.doc-info { display: flex; flex-direction: column; justify-content: center; }
.ai-badge { font-size: 10px; color: #2563eb; background: #eff6ff; width: fit-content; padding: 1px 4px; border-radius: 3px; margin-bottom: 2px; }
.doc-title-text { font-size: 14px; font-weight: 700; color: #1e293b; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.header-right { display: flex; align-items: center; gap: 12px; }
.action-btn { border: none; background: none; font-size: 13px; font-weight: 500; cursor: pointer; padding: 6px 12px; border-radius: 6px; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }
.action-btn.text { color: #64748b; }
.action-btn.text:hover { background: #f1f5f9; color: #334155; }
.action-btn.primary { background: #2563eb; color: white; box-shadow: 0 2px 5px rgba(37,99,235, 0.2); }
.action-btn.primary:hover { background: #1d4ed8; transform: translateY(-1px); }
.action-btn.outline { border: 1px solid #cbd5e1; color: #475569; }
.divider { width: 1px; height: 16px; background: #e2e8f0; margin: 0 4px; }

/* Body */
.editor-body { flex: 1; overflow: hidden; display: flex; position: relative; }

/* Step 1: Strategy Selector */
.step-zero-container { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; overflow-y: auto; padding: 100px 40px 160px; background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); }
.strategy-selector { max-width: 1000px; width: 100%; text-align: center; }
.welcome-title { font-size: 24px; color: #1e293b; margin-bottom: 8px; font-weight: 800; display: flex; align-items: center; justify-content: center; gap: 8px; }
.welcome-sub { color: #64748b; margin-bottom: 40px; }
.loading-state-lg { margin-top: 40px; color: #64748b; display: flex; flex-direction: column; items: center; }
.cards-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; text-align: left; }
.strategy-card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; cursor: pointer; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
.strategy-card:hover { border-color: #3b82f6; transform: translateY(-5px); box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.15); }
.card-icon { font-size: 32px; margin-bottom: 16px; background: #f8fafc; width: 56px; height: 56px; display: flex; align-items: center; justify-content: center; border-radius: 50%; }
.card-title { font-size: 16px; font-weight: 700; color: #0f172a; margin: 0 0 8px 0; }
.card-tag { display: inline-block; font-size: 11px; background: #eff6ff; color: #2563eb; padding: 2px 8px; border-radius: 12px; margin-bottom: 12px; font-weight: 600; }
.card-reason { font-size: 13px; color: #64748b; line-height: 1.5; }

/* Chat Input For Strategy Refinement */
.refine-container { position: sticky; bottom: 40px; width: 100%; max-width: 800px; z-index: 10; margin-top: 40px; animation: slideUp 0.3s ease-out; }
.chat-input-wrapper { display: flex; background: white; border-radius: 30px; box-shadow: 0 12px 40px rgba(0,0,0,0.15); border: 1px solid #e2e8f0; padding: 8px; align-items: center; overflow: hidden; transform: scale(1); transition: transform 0.2s; }
.chat-input-wrapper:focus-within { transform: scale(1.02); border-color: #3b82f6; }
.chat-input { flex: 1; border: none; padding: 16px 24px; font-size: 16px; outline: none; border-radius: 20px; color: #334155; }
.chat-input::placeholder { color: #94a3b8; }
.chat-send-btn { width: 44px; height: 44px; background: #0f172a; color: white; border-radius: 50%; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; font-size: 20px; flex-shrink: 0; }
.chat-send-btn:hover { background: #334155; transform: scale(1.05); }
.chat-send-btn:disabled { background: #cbd5e1; cursor: not-allowed; transform: none; }


/* 3-Column Layout */
.workspace-container { width: 100%; height: 100%; display: flex; background: #fdfdfd; }

/* COL 1: Chat (Left) */
.col-chat { width: 340px; display: flex; flex-direction: column; border-right: 1px solid #f1f5f9; background: #fafafa; flex-shrink: 0; }
.chat-header { height: 48px; border-bottom: 1px solid #f1f5f9; display: flex; align-items: center; padding: 0 16px; flex-shrink: 0; }
.chat-title { font-size: 14px; font-weight: 700; color: #334155; }

.chat-messages { flex: 1; overflow-y: auto; padding: 20px 16px; display: flex; flex-direction: column; gap: 16px; }
.chat-bubble { display: flex; gap: 10px; max-width: 100%; }
.chat-bubble.user { flex-direction: row-reverse; }
.cb-avatar { width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; background: white; border: 1px solid #e2e8f0; font-size: 16px; flex-shrink: 0; }
.cb-content { padding: 8px 12px; border-radius: 8px; font-size: 13px; line-height: 1.5; color: #334155; background: white; border: 1px solid #e2e8f0; }
.chat-bubble.user .cb-content { background: #2563eb; color: white; border: none; }
.chat-bubble.file .cb-content.file-record { padding: 8px 12px; background: white; border: 1px solid #e2e8f0; display: flex; align-items: center; gap: 8px; width: fit-content; }

.chat-footer { padding: 16px; border-top: 1px solid #f1f5f9; background: #fafafa; }
.quick-chips-scroll { display: flex; overflow-x: auto; gap: 8px; margin-bottom: 12px; padding-bottom: 4px; }
.quick-chips-scroll::-webkit-scrollbar { height: 0; }
.chip-pill { white-space: nowrap; font-size: 11px; padding: 4px 10px; border-radius: 20px; border: 1px solid #e2e8f0; background: white; color: #64748b; cursor: pointer; transition: all 0.2s; }
.chip-pill:hover { border-color: #2563eb; color: #2563eb; }

.chat-input-box { position: relative; background: white; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.03); display: flex; padding: 4px; transition: border 0.2s; }
.chat-input-box:focus-within { border-color: #2563eb; }
.chat-textarea { flex: 1; border: none; resize: none; padding: 8px; outline: none; font-size: 13px; max-height: 100px; color: #334155; }
.send-btn-icon { width: 28px; height: 28px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; align-self: flex-end; margin-bottom: 2px; }
.send-btn-icon:disabled { background: #e2e8f0; cursor: not-allowed; }

/* COL 2: Outline (Middle) */
.col-outline { width: 260px; display: flex; flex-direction: column; border-right: 1px solid #f1f5f9; background: #fff; flex-shrink: 0; }
.outline-header { height: 48px; border-bottom: 1px solid #f1f5f9; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; flex-shrink: 0; }
.outline-header h3 { font-size: 13px; font-weight: 600; color: #64748b; margin: 0; }
.icon-refresh { background: none; border: none; font-size: 14px; cursor: pointer; color: #94a3b8; }
.icon-refresh:hover { color: #2563eb; }
.outline-loading { padding: 20px; text-align: center; color: #94a3b8; font-size: 12px; display: flex; flex-direction: column; gap: 8px; align-items: center; }
.outline-list { flex: 1; overflow-y: auto; overflow-x: hidden; padding: 16px; }
.outline-item { margin-bottom: 8px; cursor: pointer; padding: 6px 8px; border-radius: 6px; transition: background 0.2s; word-break: break-all; }
.outline-item:hover { background: #f1f5f9; }
.outline-item:hover .idx { color: #2563eb; }
.outline-title-row { display: flex; align-items: baseline; gap: 8px; font-size: 13px; font-weight: 500; color: #334155; line-height: 1.4; }
.outline-title-row .idx { font-family: monospace; color: #94a3b8; }
.outline-empty { text-align: center; color: #cbd5e1; font-size: 12px; margin-top: 40px; }
.outline-bottom-action { padding: 16px; border-top: 1px solid #f1f5f9; }
.regen-btn { width: 100%; border: 1px dashed #cbd5e1; background: transparent; padding: 8px; border-radius: 6px; color: #64748b; font-size: 12px; cursor: pointer; transition: all 0.2s; }
.regen-btn:hover { border-color: #2563eb; color: #2563eb; background: #eff6ff; }


/* Right: Editor */
.editor-main-area { flex: 1; display: flex; flex-direction: column; background: #fff; position: relative; }
.immersive-editor { flex: 1; display: flex; flex-direction: column; border: none !important; }
.writing-overlay { position: absolute; bottom: 20px; right: 20px; pointer-events: none; }
.writing-status { background: rgba(37,99,235,0.9); color: white; padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; box-shadow: 0 4px 12px rgba(37,99,235,0.3); animation: float 2s infinite ease-in-out; }

/* Preview Modal */
.modal-fullscreen { position: fixed; inset: 0; background: rgba(255,255,255,0.95); z-index: 200; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(5px); }
.preview-container { width: 100%; height: 100%; overflow-y: auto; display: flex; justify-content: center; padding: 40px; }
.preview-chrome { width: 375px; height: 812px; background: white; border: 1px solid #e2e8f0; border-radius: 40px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow: hidden; position: relative; }
.chrome-header { height: 44px; background: #f8fafc; border-bottom: 1px solid #f1f5f9; display: flex; align-items: center; padding: 0 16px; gap: 6px; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.red { background: #ef4444; } .dot.yellow { background: #f59e0b; } .dot.green { background: #10b981; }
.chrome-title { font-size: 11px; color: #64748b; font-weight: 500; margin-left: auto; margin-right: auto; }
.close-preview { background: none; border: none; font-size: 16px; color: #bdc3c7; cursor: pointer; }
.chrome-body { flex: 1; overflow-y: auto; background: white; }
.article-preview-content { padding: 20px; }
.p-title { font-size: 22px; font-weight: bold; color: #111; line-height: 1.4; margin-bottom: 10px; }
.p-meta { font-size: 11px; color: #888; margin-bottom: 20px; display: flex; justify-content: space-between; }
.p-summary { background: #f7f9fa; padding: 12px; border-radius: 6px; font-size: 13px; color: #666; line-height: 1.6; margin-bottom: 24px; }
.p-body { font-size: 16px; line-height: 1.8; color: #333; text-align: justify; }
.p-body h2 { font-size: 18px; margin: 24px 0 12px; font-weight: bold; }
.p-body p { margin-bottom: 16px; }

/* Publish/Audit Modal Generic */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 100; display: flex; align-items: center; justify-content: center; }
.modal-dialog { background: white; width: 480px; max-height: 90vh; display: flex; flex-direction: column; border-radius: 12px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }
.modal-header { padding: 16px 20px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }
.close-btn { background: none; border: none; font-size: 20px; color: #94a3b8; cursor: pointer; }
.modal-body-scroll { padding: 20px; overflow-y: auto; }
.modal-footer { padding: 16px 20px; border-top: 1px solid #e2e8f0; display: flex; justify-content: flex-end; gap: 12px; }

/* Publish Settings */
.setting-group { margin-bottom: 20px; }
.setting-group label { display: block; font-size: 13px; font-weight: 500; color: #475569; margin-bottom: 8px; }
.form-input { width: 100%; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 12px; font-size: 13px; outline: none; transition: border 0.2s; }
.form-input:focus { border-color: #2563eb; }
.form-input.lg { font-size: 15px; font-weight: 600; padding: 10px; }
.cover-uploader-lg { width: 100%; aspect-ratio: 16/9; background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 8px; position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.cover-preview { width: 100%; height: 100%; object-fit: cover; }
.cover-bg-placeholder { text-align: center; color: #64748b; }
.ph-content { display: flex; flex-direction: column; align-items: center; gap: 8px; font-size: 12px; }
.regen-cover-btn { position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 10px; border-radius: 4px; border: none; font-size: 11px; cursor: pointer; }

/* Utility */
.spinner { border: 2px solid #e2e8f0; border-top-color: #2563eb; border-radius: 50%; animation: spin 1s infinite linear; }
.spinner.lg { width: 32px; height: 32px; border-width: 3px; }
.spinner.sm { width: 16px; height: 16px; display: inline-block; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes float { 0%,100%{ transform: translateY(0); } 50%{ transform: translateY(-3px); } }

/* Tags */
.tags { display: flex; gap: 6px; flex-wrap: wrap; }
.tag.red { background: #fee2e2; color: #ef4444; padding: 2px 8px; font-size: 11px; border-radius: 4px; }
.safe-text { font-size: 13px; color: #10b981; font-weight: 500; }

/* COL 3: Editor (Right) */
/* COL 3: Editor (Right) override */
.col-editor-scroll { flex: 1; overflow-y: auto; height: 100%; position: relative; background: #fff; }
.editor-main-area { display: flex; flex-direction: column; background: #fff; position: relative; padding: 40px 60px; max-width: 900px; margin: 0 auto; width: 100%; min-height: 100%; }

.editor-meta-inputs { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; width: 100%; border-bottom: 1px solid #f1f5f9; padding-bottom: 20px; }

.title-input { 
    font-size: 32px; 
    font-weight: 800; 
    border: none; 
    outline: none; 
    width: 100%; 
    color: #0f172a; 
    background: transparent; 
    line-height: 1.3;
    display: block;
}
.title-input::placeholder { color: #cbd5e1; }

.summary-input { 
    font-size: 15px; 
    color: #64748b; 
    border: none; 
    outline: none; 
    width: 100%; 
    resize: none; 
    background: transparent; 
    line-height: 1.6;
    display: block;
    font-family: inherit;
}
.summary-input::placeholder { color: #94a3b8; }

.immersive-editor { flex: 1; display: flex; flex-direction: column; border: none !important; }
.writing-overlay { position: absolute; bottom: 20px; right: 20px; pointer-events: none; }

/* Override Quill Border */
::v-deep(.ql-toolbar) { border: none !important; border-bottom: 1px solid #f1f5f9 !important; padding: 12px 0 !important; position: sticky; top: 0; background: white; z-index: 10; margin: 0 -60px; padding-left: 60px !important; padding-right: 60px !important; }
::v-deep(.ql-container) { border: none !important; font-size: 16px; font-family: 'PingFang SC', sans-serif; }
::v-deep(.ql-editor) { padding: 20px 0 !important; color: #334155; line-height: 1.8; min-height: 300px; }
/* Add anchor offset padding if needed */
::v-deep(h1), ::v-deep(h2), ::v-deep(h3) { scroll-margin-top: 80px; }


</style>