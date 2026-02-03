<template>
  <div class="prediction-page">
    <!-- Top Control Bar -->
    <div class="control-header">
       <div class="ch-title">
          <h2>🔥 热点预测 (Prophet Engine)</h2>
       </div>
       
       <!-- Filter Group -->
       <div class="filter-group">
          <select v-model="filterLevel" class="filter-select">
             <option value="all">全等级预警</option>
             <option value="high">🔴 红色高危</option>
             <option value="mid">🟠 橙色中危</option>
             <option value="low">🟡 黄色低危</option>
          </select>
          <select v-model="filterDomain" class="filter-select">
             <option value="all">全领域</option>
             <option value="tech">科技</option>
             <option value="ent">娱乐</option>
             <option value="society">社会</option>
          </select>
          <div class="sort-toggles">
             <span class="sort-btn" :class="{active: sortBy==='score'}" @click="sortBy='score'">按分值</span>
             <span class="sort-btn" :class="{active: sortBy==='accel'}" @click="sortBy='accel'">按增速</span>
             <span class="sort-btn" :class="{active: sortBy==='window'}" @click="sortBy='window'">按窗口</span>
          </div>
       </div>
       
       <button class="refresh-btn" @click="fetchData(true)" :disabled="loading">
         {{ loading ? '计算中...' : '重新预测' }}
       </button>
    </div>

    <!-- Pulse Wave Chart (Restored) -->
    <div class="pulse-wave-card">
      <div class="pw-header">
        <span class="pw-title">📈 实时脉搏</span>
        <span class="pw-sub">自动滚动</span>
      </div>
      <div class="pw-chart-wrapper">
        <div class="pw-scroll-container">
          <v-chart ref="pulseChartRef" class="pw-chart-inner" :option="pulseOption" autoresize />
        </div>
      </div>
    </div>

    <!-- Content Category Tabs -->
    <div class="category-tabs">
       <div 
         v-for="cat in categories" 
         :key="cat.id" 
         class="cat-tab" 
         :class="{ active: activeCategory === cat.id }"
         @click="activeCategory = cat.id"
       >
         {{ cat.name }}
       </div>
    </div>

    <!-- Batch Operation Tool Bar (Visible when items selected) -->
    <div class="batch-bar" v-if="selectedIds.size > 0">
       <div class="bb-left">
          <span class="bb-count">已选 {{ selectedIds.size }} 项</span>
          <button class="bb-text-btn" @click="clearSelection">取消选择</button>
       </div>
       <div class="bb-actions">
          <button class="bb-btn monitor" @click="handleBatch('monitor')">📡 批量监控</button>
          <button class="bb-btn topic" @click="handleBatch('topic')">📝 批量生成选题</button>
          <button class="bb-btn read" @click="handleBatch('read')">👀 标记已读</button>
       </div>
    </div>

    <!-- Main List Area -->
    <div class="list-container">
      <div v-if="loading" class="loading">先知引擎正在计算潜力评分...</div>
      <div v-else-if="filteredList.length === 0" class="empty-state">暂无符合条件的预测热点</div>
      
      <div v-else class="pred-list">
        <div 
          v-for="(item, index) in filteredList" 
          :key="item.id || index" 
          class="pred-card" 
          :class="[getAlertClass(item.pred_score), { 'is-selected': selectedIds.has(item.id) }]"
        >
          <!-- Checkbox Layer -->
          <div class="card-selection" @click.stop="toggleSelection(item.id)">
             <div class="checkbox" :class="{checked: selectedIds.has(item.id)}"></div>
          </div>

          <!-- Card Content -->
          <div class="card-inner">
              <!-- 1. Header: Alert + Title + Confidence -->
              <div class="card-header">
                 <div class="ch-main">
                    <span class="alert-icon">{{ getAlertIcon(item.pred_score) }}</span>
                    <span class="platform-icon" :class="getPlatform(item).class">{{ getPlatform(item).text }}</span>
                    <a :href="item.url" target="_blank" class="topic-title">{{ item.title }}</a>
                    <span class="read-dot" v-if="!item.isRead"></span>
                 </div>
                 <div class="ch-meta">
                    <div class="confidence-badge" title="模型对该预测的确定性">
                       <span class="cb-label">置信度:</span>
                       <span class="cb-val high">High</span>
                    </div>
                    <div class="prob-text">
                       🔥 {{ item.pred_score }}分 | 爆发概率 <strong>{{ Math.min(99, item.pred_score + 5) }}%</strong>
                    </div>
                 </div>
              </div>

              <!-- 2. Body: Radar + Metrics + Actionable Reasons -->
              <div class="card-body">
                 <!-- Radar Visual -->
                 <div class="radar-section">
                    <svg viewBox="0 0 100 100" class="radar-svg">
                       <polygon points="50,10 90,50 50,90 10,50" class="radar-bg" />
                       <polygon :points="getRadarPoints(item)" class="radar-data" />
                    </svg>
                    <div class="radar-caption">情感驱动型</div>
                 </div>

                 <!-- Metrics & Golden Window -->
                 <div class="metrics-section">
                    <div class="metric-row">
                       <span class="m-label">🚀 增速趋势</span>
                       <div class="sparkline">
                          <!-- Mock Sparkline -->
                          <svg width="60" height="20">
                             <polyline points="0,15 20,10 40,12 60,5" fill="none" class="sl-line" />
                          </svg>
                          <span class="sl-val text-red">↗ {{ formatAccel(item.acceleration) }}k/h</span>
                       </div>
                    </div>
                    <div class="metric-row">
                       <span class="m-label">⏳ 黄金窗口</span>
                       <div class="gw-content">
                          <span class="gw-time">{{ getGoldenWindow(item).time }}</span>
                          <span class="gw-tip">{{ getGoldenWindow(item).tip }}</span>
                       </div>
                    </div>
                 </div>

                 <!-- Insight & Risk Pred (Conditional) -->
                 <div class="insight-section">
                    <div class="is-row ai-insight">
                       <span class="is-icon">💡</span>
                       <span class="is-text">{{ item.ai_reason || getMockInsight(item) }}</span>
                    </div>
                     <!-- Risk Evolution (Only for Red/Orange + Negative) -->
                    <div class="is-row risk-evo" v-if="item.pred_score >= 70">
                       <span class="is-icon">⚠️</span>
                       <span class="is-text">风险演化：预计2h内负面占比 {{35 + (index*3)}}% ➔ {{55 + (index*2)}}%，可能引发次生舆情。</span>
                    </div>
                    <!-- Platform Spread (Mock) -->
                    <div class="is-row spread">
                       <span class="is-icon">🌊</span>
                       <span class="is-text">扩散预测：抖音 (1.5h) ➔ 小红书 (3h)</span>
                    </div>
                 </div>
                 
                 <!-- Accuracy Tag (History) -->
                 <div class="accuracy-tag" v-if="item.pred_score >= 80" title="过去30天同类预警准确率">
                    🎯 历史准确率 89%
                 </div>
              </div>

              <!-- 3. Action Footer -->
              <div class="card-footer">
                 <div class="cf-actions">
                    <button class="act-btn primary" @click="handleAction('draft', item)">
                       ⚡️ 极速成稿
                    </button>
                    <button class="act-btn secondary" @click="handleAction('topic', item)">
                       📝 生成选题
                    </button>
                    <button class="act-btn danger" v-if="item.pred_score >= 80" @click="handleAction('risk', item)">
                       🛡 风险应对
                    </button>
                    <button class="act-btn outline" @click="handleAction('monitor', item)">
                       👀 监控
                    </button>
                 </div>
              </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Modal: Topic Generator -->
    <div v-if="showTopicModal" class="p-modal-overlay" @click.self="showTopicModal = false">
       <div class="p-modal">
          <div class="pm-header">
             <h3>✨ AI 智能选题生成</h3>
             <button class="pm-close" @click="showTopicModal=false">✕</button>
          </div>
          <div class="pm-body">
             <div class="pm-source-title">基于热点：{{ currentItem?.title }}</div>
             <div class="generated-topics">
                <div v-for="(t, i) in generatedTopics" :key="i" class="topic-option">
                   <div class="to-head">
                      <span class="to-tag">{{ t.type }}</span>
                      <span class="to-angle">{{ t.angle }}</span>
                   </div>
                   <div class="to-title">{{ t.title }}</div>
                   <div class="to-desc">{{ t.desc }}</div>
                   <button class="to-add-btn" @click="submitTopic(t)">➕ 提报选题</button>
                </div>
             </div>
          </div>
       </div>
    </div>

    <!-- Modal: Risk Response -->
    <div v-if="showRiskModal" class="p-modal-overlay" @click.self="showRiskModal = false">
       <div class="p-modal risk">
          <div class="pm-header risk">
             <h3>🛡 风险应对建议包</h3>
             <button class="pm-close" @click="showRiskModal=false">✕</button>
          </div>
          <div class="pm-body">
             <div class="risk-section">
                <h4>📜 官方回应话术参考</h4>
                <div class="copy-box">
                   <p>“感谢关注。对于大家关心的问题，我们高度重视，已第一时间成立专项小组...”</p>
                   <button class="copy-btn">复制</button>
                </div>
             </div>
             <div class="risk-section">
                <h4>🚫 敏感词规避清单</h4>
                <div class="tag-cloud">
                   <span>虚假宣传</span><span>诱导消费</span><span>霸王条款</span>
                </div>
             </div>
             <div class="risk-section">
                <h4>🏛 历史同类处置案例</h4>
                <div class="case-link">🔗 2024.11 某同类事件公关复盘报告</div>
             </div>
          </div>
       </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, defineEmits } from 'vue'
import axios from 'axios'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, DataZoomComponent, MarkPointComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { API_URL } from '../services/api'

use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, MarkPointComponent, CanvasRenderer])

const emit = defineEmits(['start-instant-draft'])

// --- State ---
const list = ref([])
const loading = ref(false)
const selectedIds = ref(new Set())
const sortBy = ref('score')
const filterLevel = ref('all')
const filterDomain = ref('all') // Keeping this for backward compatibility if needed, but UI uses tabs now
const activeCategory = ref('all')

const categories = [
    { id: 'all', name: '综合' },
    { id: 'tech', name: '科技' },
    { id: 'finance', name: '财经' },
    { id: 'economy', name: '金融' },
    { id: 'auto', name: '汽车' },
    { id: 'health', name: '大健康' },
    { id: 'consumption', name: '新消费' },
    { id: 'venture', name: '创投' },
    { id: 'macro', name: '宏观' },
    { id: 'crossborder', name: '出海' },
    { id: 'local', name: '地方' },
    { id: 'bigcorp', name: '大公司' },
    { id: 'ai', name: '大模型' }
]

const pulseOption = ref({})
const pulseChartRef = ref(null)

// Modals
const showTopicModal = ref(false)
const showRiskModal = ref(false)
const currentItem = ref(null)
const generatedTopics = ref([])

// --- Data Fetching ---
const fetchData = async () => {
    loading.value = true
    try {
        const token = localStorage.getItem('token')
        const res = await axios.get(`${API_URL}/prediction/trends`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        const raw = res.data.data || []
        
        // Helper to get random category (excluding 'all')
        const getRandomCat = () => {
             const cats = categories.slice(1) // skip 'all'
             return cats[Math.floor(Math.random() * cats.length)].id
        }

        // Enrich Data
        list.value = raw.map((item, idx) => ({
            ...item,
            id: item.title, // use title as id for mock
            // Mock Enhanced Fields
            isRead: idx > 2, // Top 3 unread
            probability: Math.min(99, (item.pred_score || 0) + 5),
            confidence: (item.pred_score > 80) ? 'High' : 'Mid',
            domain: getRandomCat(), // Assign random category
            risk_trend: true
        }))
        buildPulseChart()
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const buildPulseChart = () => {
    const rawData = list.value.slice(0, 30) 
    const loopData = [...rawData, ...rawData, ...rawData] 
    const yValues = loopData.map(item => (item.acceleration || Math.random()*20000) / 10000)
    const xLabels = loopData.map((item, i) => item.title || `Event ${i}`)
    
    const markPoints = loopData
        .map((item, i) => ({ item, i, y: yValues[i] }))
        .map(({ item, i, y }, idx) => ({
            coord: [i, y],
            symbol: 'circle',
            symbolSize: 6,
            label: {
                show: true,
                formatter: item.title.length > 8 ? item.title.slice(0, 8) + '...' : item.title,
                position: idx % 2 === 0 ? 'top' : 'bottom',
                color: '#1e3a5f',
                fontSize: 11,
                fontWeight: 500,
                distance: 6
            },
            itemStyle: { color: '#3b82f6' }
        }))
    
    pulseOption.value = {
        backgroundColor: 'transparent',
        grid: { top: 60, right: 40, bottom: 30, left: 40 },
        tooltip: { trigger: 'axis' }, 
        xAxis: { type: 'category', data: xLabels, show: false },
        yAxis: { type: 'value', show: false, min: 0 },
        dataZoom: [{ type: 'slider', show: false, xAxisIndex: 0, start: 0, end: 33, zoomLock: true }],
        series: [{
            type: 'line', data: yValues, smooth: 0.4, symbol: 'none',
            lineStyle: { width: 2, color: '#6b9bd2' },
            areaStyle: {
                color: {
                    type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                    colorStops: [{ offset: 0, color: 'rgba(107, 155, 210, 0.45)' }, { offset: 1, color: 'rgba(248, 250, 252, 0.02)' }]
                }
            },
            markPoint: { data: markPoints, animation: false }
        }]
    }
}

// --- Filtering & Sorting ---
const filteredList = computed(() => {
    let res = [...list.value]
    
    // Filter Level
    if (filterLevel.value !== 'all') {
        if (filterLevel.value === 'high') res = res.filter(i => i.pred_score >= 80)
        else if (filterLevel.value === 'mid') res = res.filter(i => i.pred_score >= 70 && i.pred_score < 80)
        else if (filterLevel.value === 'low') res = res.filter(i => i.pred_score < 70)
    }
    
    // Filter Category (replaces simple domain select)
    if (activeCategory.value !== 'all') {
        res = res.filter(i => i.domain === activeCategory.value)
    } else if (filterDomain.value !== 'all') {
         // Fallback to old select if needed, but UI hides it
         res = res.filter(i => i.domain === filterDomain.value)
    }
    
    // Sort
    if (sortBy.value === 'score') res.sort((a,b) => b.pred_score - a.pred_score)
    else if (sortBy.value === 'accel') res.sort((a,b) => b.acceleration - a.acceleration)
    else if (sortBy.value === 'window') res.sort((a,b) => b.pred_score - a.pred_score) // proxy
    
    return res
})

// --- Helpers ---
const getAlertClass = (score) => {
    if (score >= 80) return 'alert-red'
    if (score >= 70) return 'alert-orange'
    return 'alert-yellow'
}

const getAlertIcon = (score) => {
    if (score >= 80) return '🔥' // High (Fire)
    if (score >= 70) return '🟠' // Mid (Flame/Orange)
    return '🟡' // Low (Spark)
}

const getPlatform = (item) => {
    const platforms = [
        { text: '微博', class: 'wb' },
        { text: '抖音', class: 'dy' },
        { text: 'B站', class: 'bz' }
    ]
    const idx = (item.title.length) % 3
    return platforms[idx]
}

const formatAccel = (val) => {
    const v = val || (Math.random() * 2000 + 500)
    return (v / 1000).toFixed(1).replace(/\.0$/, '') 
}

const getGoldenWindow = (item) => {
    // Dynamic logic based on score & accel
    const score = item.pred_score || 60
    const accel = item.acceleration || 50000 
    let mins = (105 - score) * 4
    if (accel > 150000) mins *= 0.6
    
    const h = Math.floor(mins / 60)
    const m = Math.floor(mins % 60)
    const timeStr = h > 0 ? `剩 ${h}小时 ${m}分` : `剩 ${m}分钟`
    
    // Tip
    let tip = "建议立即跟进"
    if (mins > 120) tip = "建议提前2h完成创作"
    else if (mins > 60) tip = "爆发在即，优先快讯"
    
    return { time: timeStr, tip }
}

const getRadarPoints = (item) => {
    const hash = item.title.length
    const getS = (off) => 0.5 + ((hash + off) % 5) / 10
    const p1 = `50,${50 - getS(0)*40}`
    const p2 = `${50 + getS(1)*40},50`
    const p3 = `50,${50 + getS(2)*40}`
    const p4 = `${50 - getS(3)*40},50`
    return `${p1} ${p2} ${p3} ${p4}`
}

const getMockInsight = (item) => {
    const insights = [
        "争议点在于回应态度，舆论偏向负面，建议从用户情绪切入。",
        "核心是价值背离，适合做行业对比，风险较低。",
        "事件反差感强，视频传播效率极高，建议抓取Meme。",
        "注意反转风险，信息源单一，建议短快讯处理。"
    ]
    return insights[item.title.length % insights.length]
}

// --- Selection ---
const toggleSelection = (id) => {
    if (selectedIds.value.has(id)) selectedIds.value.delete(id)
    else selectedIds.value.add(id)
}
const clearSelection = () => selectedIds.value.clear()

const handleBatch = (type) => {
    if (type === 'monitor') alert(`已批量监控 ${selectedIds.value.size} 个热点`)
    else if (type === 'topic') alert(`已为 ${selectedIds.value.size} 个热点生成选题池`)
    else if (type === 'read') {
        list.value.forEach(i => { if(selectedIds.value.has(i.id)) i.isRead = true })
        clearSelection()
    }
}

// --- Actions ---
const handleAction = (type, item) => {
    currentItem.value = item
    if (type === 'draft') {
        emit('start-instant-draft', item.title)
    } else if (type === 'topic') {
        // Mock Topics
        generatedTopics.value = [
            { type: '资讯速报', angle: '事实还原', title: `【速报】${item.title} 事件全梳理`, desc: '整合多方信源，梳理时间线' },
            { type: '深度解析', angle: '行业视角', title: `透过 ${item.title} 看行业变局`, desc: '分析背后的资本博弈与影响' },
            { type: '情感共鸣', angle: '用户情绪', title: `为什么说 ${item.title} 刺痛了我们？`, desc: '切入社会情绪，引发共鸣' }
        ]
        showTopicModal.value = true
    } else if (type === 'risk') {
        showRiskModal.value = true
    } else if (type === 'monitor') {
        alert("已添加到舆情监控列表")
    }
}

const submitTopic = (topic) => {
    alert(`选题已提报：${topic.title}`)
    showTopicModal.value = false
}

onMounted(() => fetchData())
</script>

<style scoped>
.prediction-page { padding: 24px; background: #f8fafc; min-height: 100vh; font-family: 'Inter', sans-serif; }

/* Pulse Wave Card (Restored) */
.pulse-wave-card { background: white; border-radius: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); margin-bottom: 24px; overflow: hidden; height: 260px; }
.pw-header { padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }
.pw-title { font-size: 16px; font-weight: 700; color: #1e293b; }
.pw-sub { font-size: 11px; color: #94a3b8; background: #f1f5f9; padding: 2px 8px; border-radius: 10px; }
.pw-chart-wrapper { height: 210px; padding: 0 16px; overflow: hidden; }
.pw-scroll-container { width: 300%; height: 100%; animation: pulse-scroll 35s linear infinite; }
@keyframes pulse-scroll { 0% { transform: translateX(0); } 100% { transform: translateX(-33.33%); } }
.pw-chart-inner { width: 100%; height: 100%; }

/* Content Category Tabs */
.category-tabs { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; margin-bottom: 16px; scrollbar-width: none; }
.category-tabs::-webkit-scrollbar { display: none; }
.cat-tab { 
    white-space: nowrap; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 500; color: #64748b; background: white; border: 1px solid #e2e8f0; cursor: pointer; transition: all 0.2s; 
}
.cat-tab:hover { border-color: #cbd5e1; color: #475569; }
.cat-tab.active { background: #2563eb; color: white; border-color: #2563eb; font-weight: 600; box-shadow: 0 2px 6px rgba(37,99,235,0.3); }

/* Control Header */
.control-header { 
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; 
    background: white; padding: 16px 20px; border-radius: 12px; border: 1px solid #e2e8f0;
}
.ch-title h2 { margin: 0; color: #0f172a; font-size: 18px; font-weight: 800; }
.filter-group { display: flex; gap: 12px; align-items: center; }
.filter-select { padding: 6px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; color: #475569; outline: none; }
.sort-toggles { display: flex; background: #f1f5f9; padding: 2px; border-radius: 6px; margin-left: 12px; }
.sort-btn { font-size: 12px; padding: 4px 12px; cursor: pointer; color: #64748b; border-radius: 4px; }
.sort-btn.active { background: white; color: #2563eb; font-weight: 700; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }

.refresh-btn { 
    background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 13px; margin-left: auto; 
}
.refresh-btn:disabled { opacity: 0.7; }

/* Batch Bar */
.batch-bar {
    position: sticky; top: 0; z-index: 20; margin-bottom: 16px;
    background: #1e293b; color: white; padding: 10px 24px; border-radius: 8px;
    display: flex; justify-content: space-between; align-items: center;
    animation: slideDown 0.2s;
}
@keyframes slideDown { from { transform: translateY(-10px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.bb-left { display: flex; gap: 12px; align-items: center; }
.bb-count { font-weight: 700; font-size: 14px; }
.bb-text-btn { background: none; border: none; color: #cbd5e1; cursor: pointer; font-size: 12px; text-decoration: underline; }
.bb-actions { display: flex; gap: 12px; }
.bb-btn { border: none; padding: 6px 12px; border-radius: 4px; font-size: 12px; cursor: pointer; font-weight: 600; }
.bb-btn.monitor { background: #3b82f6; color: white; }
.bb-btn.topic { background: #10b981; color: white; }
.bb-btn.read { background: rgba(255,255,255,0.2); color: white; }

/* List */
.list-container { min-height: 400px; }
.pred-list { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

/* Card */
.pred-card { 
    background: white; border-radius: 12px; border: 1px solid #e2e8f0; 
    position: relative; display: flex; overflow: hidden;
    transition: all 0.2s;
}
.pred-card:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.06); border-color: #cbd5e1; }
.pred-card.alert-red { border-top: 4px solid #dc2626; }
.pred-card.alert-orange { border-top: 4px solid #ea580c; }
.pred-card.alert-yellow { border-top: 4px solid #facc15; }
.pred-card.is-selected { background: #f8fafc; border-color: #3b82f6; }

/* Selection Area */
.card-selection { 
    width: 40px; border-right: 1px solid #f1f5f9; cursor: pointer; 
    display: flex; justify-content: center; padding-top: 20px;
    background: #fcfcfc;
}
.checkbox { 
    width: 18px; height: 18px; border: 2px solid #cbd5e1; border-radius: 4px; 
    transition: all 0.2s;
}
.checkbox.checked { background: #2563eb; border-color: #2563eb; position: relative; }
.checkbox.checked::after { content: '✔'; color: white; font-size: 12px; position: absolute; top: -1px; left: 2px; }

/* Card Inner */
.card-inner { flex: 1; display: flex; flex-direction: column; }

/* Card Header */
.card-header { padding: 12px 16px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: flex-start; }
.ch-main { display: flex; align-items: center; gap: 8px; flex: 1; overflow: hidden; }
.alert-icon { font-size: 16px; }
.platform-icon { font-size: 11px; padding: 1px 5px; border-radius: 4px; color: white; font-weight: 600; flex-shrink: 0; }
.platform-icon.wb { background: #ef4444; } .platform-icon.dy { background: #000; } .platform-icon.bz { background: #ec4899; }
.topic-title { font-size: 15px; font-weight: 700; color: #1e293b; text-decoration: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.read-dot { width: 8px; height: 8px; background: #ef4444; border-radius: 50%; flex-shrink: 0; }

.ch-meta { text-align: right; display: flex; flex-direction: column; gap: 2px; align-items: flex-end; }
.confidence-badge { font-size: 10px; display: flex; gap: 4px; background: #f0fdf4; color: #166534; padding: 1px 6px; border-radius: 4px; }
.prob-text { font-size: 12px; color: #64748b; }
.prob-text strong { color: #dc2626; font-weight: 800; }

/* Card Body */
.card-body { padding: 16px; display: flex; gap: 16px; position: relative; }
.radar-section { width: 70px; display: flex; flex-direction: column; align-items: center; flex-shrink: 0; gap: 4px; }
.radar-svg { width: 70px; height: 70px; }
.radar-bg { fill: #f8fafc; stroke: #e2e8f0; }
.radar-data { fill: rgba(59,130,246,0.2); stroke: #3b82f6; stroke-width: 2; }
.radar-caption { font-size: 10px; color: #94a3b8; }

.metrics-section { flex: 1; display: flex; flex-direction: column; gap: 12px; }
.metric-row { display: flex; flex-direction: column; gap: 4px; }
.m-label { font-size: 11px; color: #94a3b8; }
.sparkline { display: flex; align-items: center; gap: 6px; }
.sl-line { stroke: #2563eb; stroke-width: 2; }
.sl-val { font-size: 13px; font-weight: 700; font-family: 'DIN Alternate', sans-serif; }
.gw-content { display: flex; flex-direction: column; }
.gw-time { font-size: 14px; font-weight: 800; color: #ea580c; }
.gw-tip { font-size: 11px; color: #64748b; }

.insight-section { width: 180px; display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; background: #f8fafc; padding: 10px; border-radius: 8px; }
.is-row { display: flex; gap: 6px; font-size: 11px; line-height: 1.4; color: #475569; }
.is-icon { font-size: 12px; }
.is-text { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.risk-evo { color: #b91c1c; background: #fef2f2; padding: 4px; border-radius: 4px; }
.accuracy-tag { position: absolute; bottom: 16px; right: 210px; font-size: 10px; color: #2563eb; background: #eff6ff; padding: 2px 6px; border-radius: 4px; }

/* Footer */
.card-footer { padding: 10px 16px; border-top: 1px solid #f1f5f9; background: #fafafa; display: flex; justify-content: flex-end; }
.cf-actions { display: flex; gap: 8px; }
.act-btn { border: none; padding: 6px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.act-btn:hover { transform: translateY(-1px); }
.act-btn.primary { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; box-shadow: 0 2px 6px rgba(37,99,235,0.3); }
.act-btn.secondary { background: #fff7ed; color: #ea580c; border: 1px solid #ffedd5; }
.act-btn.danger { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.act-btn.outline { background: white; border: 1px solid #e2e8f0; color: #64748b; }

/* Modals */
.p-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 1000; display: flex; justify-content: center; align-items: center; backdrop-filter: blur(2px); }
.p-modal { background: white; width: 500px; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.2); animation: fadeIn 0.2s; }
.p-modal.risk { width: 600px; }
@keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }

.pm-header { padding: 16px 20px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; }
.pm-header h3 { margin: 0; font-size: 16px; color: #1e293b; }
.pm-header.risk { background: #fff1f2; }
.pm-header.risk h3 { color: #991b1b; }
.pm-close { border: none; background: none; font-size: 20px; cursor: pointer; color: #64748b; }

.pm-body { padding: 24px; max-height: 70vh; overflow-y: auto; }
.pm-source-title { font-size: 13px; color: #64748b; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px dashed #e2e8f0; }

.topic-option { border: 1px solid #e2e8f0; padding: 16px; border-radius: 8px; margin-bottom: 12px; transition: all 0.2s; }
.topic-option:hover { border-color: #3b82f6; background: #f0f9ff; }
.to-head { display: flex; justify-content: space-between; margin-bottom: 8px; }
.to-tag { font-size: 11px; background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 10px; font-weight: 700; }
.to-angle { font-size: 12px; color: #64748b; }
.to-title { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }
.to-desc { font-size: 12px; color: #64748b; margin-bottom: 12px; }
.to-add-btn { width: 100%; border: 1px dashed #3b82f6; background: white; color: #3b82f6; padding: 8px; border-radius: 6px; cursor: pointer; font-weight: 600; }
.to-add-btn:hover { background: #3b82f6; color: white; }

.risk-section { margin-bottom: 24px; }
.risk-section h4 { font-size: 14px; margin: 0 0 10px 0; color: #1e293b; border-left: 3px solid #dc2626; padding-left: 8px; }
.copy-box { background: #f8fafc; padding: 12px; border-radius: 6px; font-size: 13px; color: #334155; position: relative; border: 1px solid #e2e8f0; }
.copy-btn { position: absolute; right: 8px; bottom: 8px; font-size: 11px; background: #e2e8f0; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; }
.copy-btn:hover { background: #cbd5e1; }
.tag-cloud { display: flex; gap: 8px; flex-wrap: wrap; }
.tag-cloud span { background: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 4px; font-size: 12px; }
.case-link { color: #2563eb; text-decoration: underline; font-size: 13px; cursor: pointer; }

.loading, .empty-state { padding: 40px; text-align: center; color: #94a3b8; }
</style>
