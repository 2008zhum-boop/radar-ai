<template>
  <div class="hot-page">
    <div class="sticky-header">
      <!-- Top Header -->
      <div class="page-header">
         <div class="ph-left">
           <h2>全网热点聚合</h2>
           <span class="live-badge">实时聚合</span>
           <button class="refresh-btn" @click="refresh" :disabled="loading">
             <span v-if="loading" class="spin-icon">🔄</span>
             <span v-else>🔄 刷新全网数据</span>
           </button>
         </div>
         <div class="ph-right">
             <!-- Radar Stats (Moved here) -->
             <div class="radar-mini-stats">
                 <div class="rms-item">
                    <span class="rms-label">关键词匹配</span>
                    <span class="rms-val">{{ matchedCount }}</span>
                 </div>
                 <div class="rms-divider"></div>
                 <div class="rms-item">
                    <span class="rms-label">风险指数</span>
                    <span class="rms-val green">低</span>
                 </div>
             </div>

            <!-- Sort Controls -->
             <div class="sort-group">
               <button :class="{active: sortBy === 'heat'}" @click="changeSort('heat')">🔥 按热度</button>
               <button :class="{active: sortBy === 'velocity'}" @click="changeSort('velocity')">🚀 按增速</button>
             </div>
         </div>
      </div>

      <!-- Category Tabs -->
      <div class="category-tabs">
        <div 
          v-for="cat in categories" 
          :key="cat"
          class="tab-item"
          :class="{ active: currentCategory === cat }"
          @click="switchCategory(cat)"
        >
          {{ cat }}
        </div>
      </div>
      
      <!-- Source Filter -->
      <div class="source-filter">
         <span class="sf-label">快速定位:</span>
         <div class="sf-list">
            <div 
              v-for="src in sources" 
              :key="src" 
              class="sf-item"
              :class="{ active: currentSource === src }"
              @click="switchSource(src)"
            >
              {{ src }}
            </div>
         </div>
      </div>
    </div>
    
    <div class="main-layout">
      <div class="content-area full-width">
         <div class="content-sub-header">
            <span class="icon">🚀</span> 
            <span class="src-name">全网热榜</span> 
            <span class="top-tag">Top 30</span>
         </div>

         <div v-if="loading" class="loading-state">
           <div class="spinner"></div> 正在聚合全网数据...
         </div>
         
         <div v-else-if="hotList.length === 0" class="empty-state">
           暂无数据，请稍后刷新
         </div>

         <HotTable 
            v-else 
            :list="hotList" 
            @analyze="handleAnalyze" 
            @click-item="handleClickItem"
            @dismiss="handleDismiss"
            @instant-draft="handleInstantDraft"
         />
      </div>
    </div>

    <!-- Floating Assistant Button -->
    <div class="fab-assistant" @click="showChat = true">
        <span class="fab-icon">🤖</span>
        <span class="fab-text">灵感助手</span>
    </div>

    <!-- Assistant Modal -->
    <div v-if="showChat" class="chat-modal-overlay" @click.self="showChat = false">
        <div class="chat-modal">
           <div class="cm-header">
              <div class="cm-title">✨ 灵感小助手</div>
              <button class="cm-close" @click="showChat = false">✕</button>
           </div>
           
           <!-- Chat Content -->
           <div class="chat-window" ref="chatWindowRef">
             <div v-for="(msg, idx) in chatMessages" :key="idx" class="chat-msg" :class="msg.role">
               <div class="msg-content" style="white-space: pre-wrap;">{{ msg.text }}</div>
             </div>
             <div v-if="isTyping" class="chat-msg ai typing">
               <span class="dot"></span><span class="dot"></span><span class="dot"></span>
             </div>
           </div>

           <!-- Quick Chips -->
           <div class="quick-chips">
              <div class="chip" @click="sendPrompt('生成该热点大纲')">📝 生成大纲</div>
              <div class="chip" @click="sendPrompt('查找相似历史事件')">🔍 相似事件</div>
              <div class="chip" @click="sendPrompt('生成3个爆款标题')">🔥 爆款标题</div>
           </div>

           <!-- Input Area -->
           <div class="chat-input-area">
             <input 
               v-model="inputMessage" 
               @keyup.enter="sendMessage"
               type="text" 
               placeholder="问问 AI (例如：如何蹭这个热点?)..." 
               :disabled="isTyping"
             >
             <button @click="sendMessage" :disabled="!inputMessage.trim() || isTyping">➤</button>
           </div>
        </div>
    </div>



    <!-- Report Loading Overlay -->
    <div v-if="isGeneratingReport" class="loading-overlay">
        <div class="spinner"></div>
        <div class="loading-text">正在生成深度分析报告，请稍候...</div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, inject, computed, watch, nextTick } from 'vue'
import HotTable from './HotTable.vue'
import { getHotList, analyzeTopic, getClients } from '../services/api'

const emit = defineEmits(['start-instant-draft'])

const categories = ["综合", "科技", "财经", "金融", "汽车", "大健康", "新消费", "创投", "宏观", "出海", "地方", "大公司", "大模型"]
const sources = ["全部", "微博", "头条", "微信", "B站", "抖音", "百度", "GoogleAI"]

const currentCategory = ref("综合")
const currentSource = ref("全部")
const sortBy = ref("heat")

const hotList = ref([]) // processed
const rawData = ref({}) // raw
const loading = ref(false)

// Data Maps
const clientMap = ref({}) // keyword -> [ClientNames]
const ignoredIds = ref(new Set()) // dismissed items

// Polling
let pollingTimer = null

// Focus
const focusItem = ref(null)

// Chat State
const chatMessages = ref([
  { role: 'ai', text: '你好！我是你的创作灵感助手。今日热点很多，想写点什么？' }
])
const inputMessage = ref('')
const isTyping = ref(false)
const showChat = ref(false)
const chatWindowRef = ref(null)

// Injects
const openReport = inject('openReport', null)

// Computeds
const matchedCount = computed(() => {
  if (!hotList.value) return 0
  return hotList.value.filter(i => i.matched_clients && i.matched_clients.length > 0).length
})

// Actions
const load = async (silent = false) => {
  if (!silent) loading.value = true
  try {
    const res = await getHotList(currentCategory.value)
    rawData.value = res.data || {}
    processData()
  } catch (e) {
    console.error('获取热搜失败', e)
    if (!silent) hotList.value = []
  } finally {
    if (!silent) loading.value = false
  }
}

const fetchClientMap = async () => {
  try {
    const token = localStorage.getItem('token');
    if(!token) return;

    const clients = await getClients()
    const map = {}
    if (clients && clients.length) {
      clients.forEach(c => {
        if (c.config && c.config.brand_keywords) {
          c.config.brand_keywords.forEach(k => {
             const lowerK = k.toLowerCase()
             if(!map[lowerK]) map[lowerK] = []
             map[lowerK].push(c.name)
          })
        }
      })
    }
    clientMap.value = map
  } catch (e) {
    console.error('获取客户关键词失败', e)
  }
}

const processData = () => {
  try {
    let aggregates = {} // title -> item
    
    // Safety check for rawData
    if (!rawData.value) {
       console.warn("rawData is empty")
       hotList.value = []
       return
    }

    // Determine which sources to include
    const targetSources = currentSource.value === '全部' ? Object.keys(rawData.value) : [currentSource.value]
    
    targetSources.forEach(src => {
        if(rawData.value[src] && Array.isArray(rawData.value[src])) {
           rawData.value[src].forEach(item => {
              if (!item || !item.title) return
              if (ignoredIds.value.has(item.title)) return; // Skip dismissed

              if (!aggregates[item.title]) {
                 aggregates[item.title] = { 
                     ...item, 
                     source_distribution: {}, 
                     sentiment_counts: { pos: 0, neu: 0, neg: 0 },
                     total_mentions: 0 
                 }
              }
              
              const currentAgg = aggregates[item.title]
              
              // Update Max Heat
              if ((item.heat || 0) > (currentAgg.heat || 0)) {
                  currentAgg.heat = item.heat
              }
              
              // Count Source
              if (!currentAgg.source_distribution[src]) {
                  currentAgg.source_distribution[src] = 0
              }
              currentAgg.source_distribution[src] += 1
              
              // Count Sentiment
              // item.sentiment_score is 0.5 default in backend. 
              const score = (typeof item.sentiment_score === 'number') ? item.sentiment_score : (Math.random() * 2 - 1)
              if (score > 0.3) currentAgg.sentiment_counts.pos += 1
              else if (score < -0.1) currentAgg.sentiment_counts.neg += 1
              else currentAgg.sentiment_counts.neu += 1

              currentAgg.total_mentions += 1
           })
        }
    })
    
    // Finalize Items
    let flat = Object.values(aggregates).map(item => {
         // Calculate Source Percentages
         const dist = {}
         const total = item.total_mentions || 1
         Object.keys(item.source_distribution || {}).forEach(src => {
            dist[src] = Math.round((item.source_distribution[src] / total) * 100)
         })
         item.source_distribution = dist
         
         // Calculate Sentiment Dist
         const sDist = {}
         const sTotal = item.sentiment_counts.pos + item.sentiment_counts.neu + item.sentiment_counts.neg
         if (sTotal > 0) {
             sDist.pos = Math.round((item.sentiment_counts.pos / sTotal) * 100)
             sDist.neg = Math.round((item.sentiment_counts.neg / sTotal) * 100)
         } else {
             sDist.pos = 0; sDist.neg = 0;
         }
         sDist.neu = 100 - sDist.pos - sDist.neg // Remainder
         item.sentiment_distribution = sDist
         
         // Match Clients
         item.matched_clients = []
         let summaryStr = ""
         if (item.summary && typeof item.summary === 'string') summaryStr = item.summary
         else if (item.summary && typeof item.summary === 'object') summaryStr = (item.summary.fact || "") + (item.summary.angle || "")
         
         const text = (item.title + summaryStr).toLowerCase()
         if (clientMap.value) {
             Object.keys(clientMap.value).forEach(kw => {
                 if (text.includes(kw)) {
                     item.matched_clients.push(...clientMap.value[kw])
                 }
             })
         }
         item.matched_clients = [...new Set(item.matched_clients)] // dedupe
         
         return item
    })
    
    // Sort
    if (sortBy.value === 'heat') {
        flat.sort((a,b) => (b.heat || 0) - (a.heat || 0))
    } else {
        flat.sort((a,b) => ((b.heat||0) * Math.random()) - ((a.heat||0) * Math.random())) 
    }
    
    // Re-rank
    flat.forEach((item, index) => item.rank = index + 1)
    
    hotList.value = flat
  } catch (err) {
      console.error("Error processing hot list data:", err)
      hotList.value = []
  }
}

// Watch both filters
watch([currentCategory, currentSource, sortBy, clientMap], () => {
   // ClientMap change should re-process to show tags
   processData()
})

const switchCategory = (cat) => {
  if (currentCategory.value !== cat) {
      currentCategory.value = cat
      load()
  }
}

const switchSource = (src) => {
    currentSource.value = src
    processData()
}

const changeSort = (type) => {
    sortBy.value = type
    processData()
}

const refresh = () => load()

// Analysis State
const isGeneratingReport = ref(false)

const handleAnalyze = async (itemOrTitle) => {
  if (isGeneratingReport.value) return // Prevent double click
  isGeneratingReport.value = true
  
  // Resolve title and stats
  let title = ''
  let stats = {}
  
  if (typeof itemOrTitle === 'object') {
      title = itemOrTitle.title
      stats = {
          heat: itemOrTitle.heat,
          source: itemOrTitle.source, 
          total_mentions: itemOrTitle.total_mentions || itemOrTitle.heat,
          sentiment_distribution: itemOrTitle.sentiment_distribution, // Pass raw dist
          emotion: itemOrTitle.sentiment_distribution 
              ? `正面 ${itemOrTitle.sentiment_distribution.pos}% | 负面 ${itemOrTitle.sentiment_distribution.neg}%` 
              : '中性',
          high_risk_count: 0,
          risks: [] 
      }
  } else {
      title = itemOrTitle
  }

  try {
    const result = await analyzeTopic(title)
    
    const combinedData = {
        ...stats,
        ...result, 
        topic: title
    }
    
    console.log("Combined Data for Report:", combinedData) // Debug Log

    if (openReport) {
        openReport(combinedData)
        // Ensure overlay is closed immediately when report opens
        isGeneratingReport.value = false 
    } else {
        console.error("openReport inject is missing!")
        isGeneratingReport.value = false
    }
  } catch (e) {
    console.error("Analysis Failed", e)
    alert("分析失败: " + e.message)
    isGeneratingReport.value = false
  }
  // Remove finally block to avoid double toggle or race conditions if openReport triggers things
  // Or keep it but simple. 
}

const handleDismiss = (title) => {
    ignoredIds.value.add(title)
    processData() // Re-render to remove it
}

const handleInstantDraft = (topic) => {
    emit('start-instant-draft', topic)
}

const handleClickItem = (item) => {
    focusItem.value = item
    showChat.value = true
    
    // Auto-Trigger Pulse Analysis
    chatMessages.value = [
        { role: 'ai', text: '已为您锁定热点：' + item.title + '\n正在为您梳理事件脉络...' }
    ]
    isTyping.value = true
    
    // Simulate Pulse Analysis API Call
    setTimeout(() => {
       const summaryFacts = (typeof item.summary === 'object' ? item.summary.fact : item.summary) || "暂无详情"
       const summaryAngle = (typeof item.summary === 'object' ? item.summary.angle : '') 
       
       let pulseText = `【事件脉络梳理】\n\n📌 **核心事实**\n${summaryFacts}\n\n`
       if (summaryAngle && summaryAngle.length > 5) {
           pulseText += `🔍 **关键争议点**\n${summaryAngle}\n\n`
       }
       
       // Simulate Timeline (Mock)
       const times = ["6小时前", "2小时前", "30分钟前"]
       pulseText += `⏱ **时间线回溯**\n`
       pulseText += `• ${times[0]}: 话题开始发酵，相关讨论量激增。\n`
       pulseText += `• ${times[1]}: 关键大V发布观点，引发第二波转发。\n`
       pulseText += `• ${times[2]}: 当前热度持续上升，情感趋于${item.sentiment_distribution?.pos > 50 ? '正面' : '中性' || '复杂'}。\n\n`
       
       pulseText += `💡 **下一步建议**\n建议从"${summaryAngle ? '争议点切入' : '事实回顾'}"角度进行创作，预计可获得较高流量。`
       
       chatMessages.value.push({ role: 'ai', text: pulseText })
       isTyping.value = false
       scrollToBottom()
    }, 1500)
}

// Chat Methods
const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindowRef.value) {
      chatWindowRef.value.scrollTop = chatWindowRef.value.scrollHeight
    }
  })
}

const sendPrompt = (text) => {
  inputMessage.value = text
  sendMessage()
}

const sendMessage = async () => {
  const text = inputMessage.value.trim()
  if (!text) return

  // User
  chatMessages.value.push({ role: 'user', text })
  inputMessage.value = ''
  scrollToBottom()
  
  // AI
  isTyping.value = true
  setTimeout(async () => {
    let aiText = "收到您的请求！"
    
    if (focusItem.value) {
        aiText += `\n针对正在分析的案例《${focusItem.value.title}》：\n`
    }

    if (text.includes("大纲")) {
        aiText += "已生成大纲：\n1. 事件回顾 (Top 3 观点)\n2. 舆论发酵路径\n3. 行业影响深度剖析"
    } else if (text.includes("标题")) {
        aiText += "爆款标题推荐：\n1. 《震惊！" + (focusItem.value?.title || "...") + " 背后的真相》\n2. 《复盘：从流量到变现的逻辑》\n3. 《也许如果你错过这个热点...》"
    } else if (text.includes("综述")) {
        aiText += "基于您选择的多条热点，我们发现今日市场呈现出明显的“避险”情绪，同时..."
    } else {
        aiText += "正在为您调取全网知识库进行即时分析，请稍候..."
    }
    
    chatMessages.value.push({ role: 'ai', text: aiText })
    isTyping.value = false
    scrollToBottom()
  }, 1200)
}

const formatNumber = (num) => {
  if (num > 10000) return (num / 10000).toFixed(1) + 'w'
  return num
}
const getSentimentClass = (item) => {
   // Mock
   return 'neutral'
}

onMounted(() => {
  load()
  fetchClientMap()
  // Auto Refresh Every 60s
  pollingTimer = setInterval(() => load(true), 60000)
})

onUnmounted(() => {
    if (pollingTimer) {
        clearInterval(pollingTimer)
        pollingTimer = null
    }
})</script>

<style scoped>
.hot-page { 
  padding: 24px; 
  background: #f8fafc; 
  min-height: 100vh;
  font-family: 'Inter', sans-serif;
}

/* Sticky Header */
.sticky-header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: #f8fafc;
  padding: 10px 0 20px 0; /* Adjust padding */
  margin: -24px -24px 24px -24px;
  padding-left: 24px; padding-right: 24px; /* compensate neg margin */
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; margin-top: 10px; }
.ph-left { display: flex; align-items: center; gap: 12px; }
.ph-right { display: flex; align-items: center; gap: 16px; } /* Added gap */

/* Mini Radar Stats */
.radar-mini-stats {
    display: flex; align-items: center; background: white; padding: 4px 12px;
    border-radius: 6px; border: 1px solid #cbd5e1; gap: 12px;
}
.rms-item { display: flex; flex-direction: column; align-items: center; }
.rms-label { font-size: 10px; color: #64748b; }
.rms-val { font-size: 14px; font-weight: 700; color: #0f172a; line-height: 1.2; }
.rms-val.green { color: #16a34a; }
.rms-divider { width: 1px; height: 20px; background: #e2e8f0; }
.ph-left h2 { font-size: 24px; font-weight: 800; color: #0f172a; margin: 0; }
.live-badge { background: #eff6ff; color: #2563eb; font-size: 12px; padding: 4px 8px; border-radius: 4px; border: 1px solid #dbeafe; }

.refresh-btn { 
  background: white; border: 1px solid #cbd5e1; padding: 6px 12px; border-radius: 6px; 
  font-size: 13px; font-weight: 600; color: #475569; cursor: pointer; display: flex; align-items: center; gap: 6px;
}
.spin-icon { display: inline-block; animation: spin 1s linear infinite; }

.sort-group { display: flex; background: #e2e8f0; padding: 2px; border-radius: 6px; }
.sort-group button { 
    border: none; background: none; padding: 4px 12px; font-size: 12px; font-weight: 600; color: #64748b; cursor: pointer; border-radius: 4px; 
}
.sort-group button.active { background: white; color: #0f172a; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }

/* Tabs */
.category-tabs { 
  display: flex; gap: 24px; margin-bottom: 16px; border-bottom: 1px solid #cbd5e1; padding-bottom: 8px; 
  overflow-x: auto; white-space: nowrap; scrollbar-width: none; /* Firefox */
}
.category-tabs::-webkit-scrollbar { display: none; } /* Chrome/Safari */

.tab-item { font-size: 14px; color: #64748b; font-weight: 500; cursor: pointer; position: relative; padding-bottom: 4px; flex-shrink: 0; }
.tab-item:hover { color: #0f172a; }
.tab-item.active { color: #2563eb; font-weight: 700; }
.tab-item.active::after { content: ''; position: absolute; bottom: -9px; left: 0; width: 100%; height: 3px; background: #2563eb; border-radius: 2px 2px 0 0; }

/* Filter */
.source-filter { display: flex; align-items: center; gap: 12px; }
.sf-label { font-size: 13px; font-weight: 600; color: #94a3b8; }
.sf-list { display: flex; gap: 8px; }
.sf-item { font-size: 13px; padding: 4px 12px; border-radius: 4px; cursor: pointer; background: white; border: 1px solid #cbd5e1; color: #64748b; }
.sf-item.active { background: #2563eb; color: white; border-color: #2563eb; }

/* Layout */
.main-layout { display: block; position: relative; } /* Remove flex column/row constraint */
.content-area { width: 100%; } /* Full width */
.content-area.full-width { padding-right: 0; }

/* Floating Assistant */
.fab-assistant {
    position: fixed; bottom: 30px; right: 30px;
    background: #2563eb; color: white;
    padding: 12px 20px; border-radius: 30px;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    cursor: pointer; z-index: 100;
    display: flex; align-items: center; gap: 8px;
    transition: transform 0.2s;
}
.fab-assistant:hover { transform: scale(1.05); background: #1d4ed8; }
.fab-icon { font-size: 20px; }
.fab-text { font-size: 14px; font-weight: 600; }

/* Chat Modal */
.chat-modal-overlay {
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    background: rgba(0,0,0,0.5); z-index: 200;
    display: flex; justify-content: flex-end; align-items: flex-end;
    padding: 30px;
}
.chat-modal {
    width: 380px; height: 600px;
    background: white; border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    display: flex; flex-direction: column;
    overflow: hidden;
    animation: slideUp 0.3s ease-out;
}
@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

.cm-header {
    padding: 16px; border-bottom: 1px solid #e2e8f0;
    display: flex; justify-content: space-between; align-items: center;
    background: #f8fafc;
}
.cm-title { font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 6px; }
.cm-close { border: none; background: none; font-size: 18px; color: #64748b; cursor: pointer; }

/* Reuse existing chat styles... */

/* Sidebar Components */
.side-card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.radar-card { flex-shrink: 0; }
.chat-card { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

.sc-header { display: flex; justify-content: space-between; margin-bottom: 16px; color: #1e293b; font-weight: 700; }
.status-tag { font-size: 12px; background: #dcfce7; color: #16a34a; padding: 2px 6px; border-radius: 4px; }

/* Radar Content */
.rf-title { font-size: 14px; font-weight: 700; margin-bottom: 12px; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.radar-stats { display: flex; margin-bottom: 12px; }
.rs-item { flex: 1; text-align: center; }
.rs-label { font-size: 12px; color: #64748b; }
.rs-val { font-size: 20px; font-weight: 800; color: #0f172a; }
.rs-val.green { color: #16a34a; }
.rs-divider { width: 1px; background: #e2e8f0; margin: 0 10px; }
.radar-footer { text-align: center; background: #f8fafc; padding: 8px; border-radius: 6px; color: #64748b; font-size: 12px; }

/* Chat */
.chat-window { flex: 1; overflow-y: auto; background: #f8fafc; border-radius: 8px; padding: 12px; margin-bottom: 10px; display: flex; flex-direction: column; gap: 10px; }
.chat-msg { max-width: 85%; padding: 8px 12px; border-radius: 8px; font-size: 13px; line-height: 1.4; word-wrap: break-word; }
.chat-msg.ai { align-self: flex-start; background: white; border: 1px solid #e2e8f0; color: #334155; }
.chat-msg.user { align-self: flex-end; background: #2563eb; color: white; }

.quick-chips { display: flex; gap: 6px; margin-bottom: 10px; overflow-x: auto; padding-bottom: 2px; }
.chip { 
    font-size: 11px; background: #eff6ff; color: #2563eb; padding: 4px 8px; border-radius: 12px; cursor: pointer; white-space: nowrap; border: 1px solid #dbeafe;
}
.chip:hover { background: #dbeafe; }

.chat-input-area { display: flex; gap: 8px; }
.chat-input-area input { flex: 1; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; outline: none; }
.chat-input-area button { background: #2563eb; color: white; border: none; width: 32px; height: 32px; border-radius: 6px; cursor: pointer; }

/* Batch Bar */


/* Report Loading */
.loading-overlay {
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    background: rgba(255,255,255,0.8); z-index: 999;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    backdrop-filter: blur(2px);
}
.loading-text { margin-top: 16px; font-weight: 600; color: #475569; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>
