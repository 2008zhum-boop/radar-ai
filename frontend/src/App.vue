<template>
  <div class="app-container">
    
    <EditorView 
      v-if="editorVisible" 
      :initialData="editorData"
      @back="editorVisible = false"
    />

    <template v-else>
      <aside class="sidebar-left">
        <SidebarNav 
          :currentTab="currentTab"
          @change="switchTab"
        />
      </aside>

      <main class="main-center">
        
        <header class="top-bar">
          <div class="bar-left">
            <h1>{{ pageTitle }}</h1>
            <span class="update-pill" v-if="currentTab === 'today_hot'">实时聚合</span>
          </div>
          <div class="bar-right">
            <button v-if="currentTab === 'today_hot'" @click="loadData" :disabled="loading" class="action-btn">
              {{ loading ? '⏳ 正在抓取全网...' : '🔄 刷新全网数据' }}
            </button>
            <button v-if="currentTab === 'monitor'" @click="loadData" :disabled="loading" class="action-btn">
              {{ loading ? '⏳ 深度扫描中...' : '📡 实时扫描' }}
            </button>
            <button v-if="currentTab === 'prediction'" @click="loadData" :disabled="loading" class="action-btn">
              {{ loading ? '⏳ 计算中...' : '🔮 重新预测' }}
            </button>
          </div>
        </header>

        <div v-if="currentTab === 'monitor'" class="hot-container">
          <div class="monitor-dashboard-header">
            <div class="dash-card">
              <div class="dash-label">监控主体</div>
              <div class="dash-value">{{ monitorList.length }} <span class="unit">个</span></div>
            </div>
            <div class="dash-card warning">
              <div class="dash-label">高风险预警</div>
              <div class="dash-value red">{{ getHighRiskCount() }} <span class="unit">个</span></div>
            </div>
            <div class="dash-card">
              <div class="dash-label">今日舆情总量</div>
              <div class="dash-value">{{ getAllAlertsCount() }} <span class="unit">条</span></div>
            </div>
            <div class="dash-desc-box">
              <div class="desc-title">🤖 AI 舆情研判中</div>
              <div class="desc-text">已连接 36氪、微博、百度实时数据源，每 5 分钟自动更新。</div>
            </div>
          </div>

          <div class="content-scroll-area">
            <div class="monitor-grid">
              <div v-for="item in monitorList" :key="item.name" class="monitor-pro-card">
                <div class="mp-header">
                  <div class="mp-info">
                    <h3 class="mp-name">{{ item.name }}</h3>
                    <span class="industry-badge">{{ item.industry }}</span>
                  </div>
                  <div class="risk-badge" :class="getRiskLevel(item.name).class">
                    {{ getRiskLevel(item.name).text }}
                  </div>
                </div>

                <div class="mp-viz-row">
                  <div class="viz-col">
                    <div class="viz-label">情感倾向分布</div>
                    <div class="sentiment-bar-track">
                      <div class="s-bar negative" :style="{ width: getSentimentData(item.name).neg + '%' }"></div>
                      <div class="s-bar neutral" :style="{ width: getSentimentData(item.name).neu + '%' }"></div>
                      <div class="s-bar positive" :style="{ width: getSentimentData(item.name).pos + '%' }"></div>
                    </div>
                    <div class="viz-legend">
                      <span>😡 {{ getSentimentData(item.name).neg }}%</span>
                      <span>😐 {{ getSentimentData(item.name).neu }}%</span>
                      <span>😄 {{ getSentimentData(item.name).pos }}%</span>
                    </div>
                  </div>
                  <div class="viz-col">
                    <div class="viz-label">7日热度趋势</div>
                    <div class="trend-chart">
                      <div class="trend-bar" v-for="h in getTrendData(item.name)" :key="h" :style="{ height: h + '%' }"></div>
                    </div>
                  </div>
                </div>

                <div class="mp-tags-row" v-if="getRelatedNews(item.name).length > 0">
                  <span class="viz-label">风险关键词：</span>
                  <div class="tags-wrapper">
                    <span v-for="tag in getRiskTags(item.name)" :key="tag" class="risk-tag">{{ tag }}</span>
                  </div>
                </div>

                <div class="mp-footer">
                  <div v-if="getRelatedNews(item.name).length > 0" class="latest-alert">
                    <span class="alert-icon">🔥</span>
                    <span class="alert-text">{{ getRelatedNews(item.name)[0].title }}</span>
                  </div>
                  <div v-else class="latest-alert safe">
                    <span class="alert-icon">✅</span>
                    <span class="alert-text">暂无重大负面舆情</span>
                  </div>
                  <button class="mp-btn" @click="jumpToPrediction">生成报告</button>
                </div>
              </div>
            </div>
            
             <div v-if="monitorList.length === 0" class="empty-placeholder">
              <div class="empty-icon">📂</div>
              <h3>暂无监控数据</h3>
              <p>请前往“客户管理”添加需要监控的对象</p>
            </div>
          </div>
        </div>

        <div v-else-if="currentTab === 'customer'" class="full-height-container">
          <CustomerManager 
            :list="monitorList" 
            @save="handleCustomerSave"
            @delete="handleCustomerDelete"
          >
            <template #status="{ name }">
              <span v-if="getRelatedNews(name).length > 0" class="status-badge warning">
                ⚠️ {{ getRelatedNews(name).length }} 条动态
              </span>
              <span v-else class="status-badge safe">✅ 平稳</span>
            </template>
          </CustomerManager>
        </div>

        <div v-else-if="currentTab === 'today_hot'" class="hot-container">
          <div class="category-tabs">
            <div v-for="cat in categories" :key="cat" class="cat-pill" :class="{ active: currentCategory === cat }" @click="switchCategory(cat)">{{ cat }}</div>
          </div>
          
          <div class="source-anchors" v-if="!loading && Object.keys(hotMap).length > 0">
            <span class="anchor-label">快速定位：</span>
            <div v-for="(items, source) in hotMap" :key="source" class="anchor-item" @click="scrollToSource(source)">{{ source }}</div>
          </div>

          <div class="content-scroll-area">
            <div v-for="(items, sourceName) in hotMap" :key="sourceName" class="source-section">
              <div class="section-header" :id="'source-' + sourceName">
                <span class="source-icon">📌</span><h3>{{ sourceName }}</h3><span class="top-count">Top {{ items.length }}</span>
              </div>
              <div class="cards-wrapper">
                <HotCard 
                  v-for="item in items" 
                  :key="item.rank" 
                  :rank="item.rank" 
                  :title="item.title" 
                  :heat="item.heat" 
                  :label="item.label" 
                  :summary="item.summary" 
                  @analyze="openAiSidebar(item.title)"
                />
              </div>
            </div>
            
            <div v-if="loading" class="loading-mask">
              <div class="spinner"></div>
              <p>正在连接全网数据源 (Weibo/36Kr/Baidu)...</p>
            </div>
             <div v-if="!loading && Object.keys(hotMap).length === 0" class="empty-placeholder">
              <div class="empty-icon">📡</div>
              <h3>暂无数据</h3>
              <p>请点击右上角刷新，确保后端服务正常</p>
            </div>
          </div>
        </div>

        <div v-else-if="currentTab === 'prediction'" class="hot-container">
           <div class="prediction-header">
            <div class="pred-intro">
              <h2>🔥 智能选题预测</h2>
              <p>AI 已结合 {{ monitorList.length }} 个客户标签进行交叉分析</p>
            </div>
          </div>
          <div class="content-scroll-area">
            <div class="cards-wrapper">
              <PredictionCard v-for="(item, index) in predictionList" :key="index" :keyword="item.keyword" :event="item.event" :type="item.type" :title="item.title" :reason="item.reason" :score="item.score" @adopt="onAdoptStrategy({title: item.title, angle: item.reason, topic: item.event})"/>
            </div>
             <div v-if="loading" class="loading-mask">正在进行智能计算...</div>
          </div>
        </div>

        <div v-else class="empty-placeholder">
          <div class="empty-icon">🚧</div><h3>“{{ pageTitle }}”模块开发中</h3>
        </div>

      </main>

      <aside class="sidebar-right">
        <RightDashboard :alerts="alerts" />
      </aside>

      <AiSidebar 
        :visible="sidebarVisible" :loading="aiLoading" :topic="currentTopic" :result="aiResult"
        @close="sidebarVisible = false" @adopt="onAdoptStrategy" 
      />
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import SidebarNav from './components/SidebarNav.vue'
import HotCard from './components/HotCard.vue'
import RightDashboard from './components/RightDashboard.vue'
import AiSidebar from './components/AiSidebar.vue'
import EditorView from './components/EditorView.vue'
import PredictionCard from './components/PredictionCard.vue'
import CustomerManager from './components/CustomerManager.vue'
import { getHotList, addKeyword, removeKeyword, analyzeTopic, getPredictions } from './services/api'

// === 状态 ===
const currentTab = ref('today_hot')
const categories = ['综合', '科技', '财经', '汽车', '出海', '大健康', '新消费', '创投']
const currentCategory = ref('综合')
const hotMap = ref({}) 
const predictionList = ref([]) 
const alerts = ref([])
const loading = ref(false)
const sidebarVisible = ref(false)
const aiLoading = ref(false)
const currentTopic = ref('')
const aiResult = ref({})
const editorVisible = ref(false)
const editorData = ref({})

// 客户数据
const monitorList = ref([
  { name: '瑞幸咖啡', industry: '消费零售', level: '核心' },
  { name: '特斯拉', industry: '汽车出行', level: '重要' },
  { name: 'OpenAI', industry: '科技互联网', level: '核心' }
])

const pageTitle = computed(() => {
  const map = { 
    'today_hot': '全网热点聚焦', 
    'prediction': '智能选题预测',
    'monitor': '舆情监控雷达',
    'customer': '客户档案管理',
    'workbench': '我的工作台'
  }
  return map[currentTab.value] || '智编系统'
})

// === 业务逻辑 (含缓存优化) ===
const switchTab = (tab) => {
  currentTab.value = tab
  // 缓存策略: 有数据就不刷
  if (tab === 'prediction' && predictionList.value.length > 0) return
  if (tab === 'today_hot' && Object.keys(hotMap.value).length > 0) return
  if (tab === 'monitor' && Object.keys(hotMap.value).length > 0) return
  if (tab === 'customer') return
  loadData()
}

const switchCategory = (cat) => { currentCategory.value = cat; loadData(); }
const scrollToSource = (sourceName) => {
  const element = document.getElementById(`source-${sourceName}`)
  if (element) element.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// 4. 加载数据 (终极优化版：数据库 + 静默刷新)
const loadData = async () => {
  // 策略：如果当前页面已经有数据展示了，就不显示全屏 Loading，改为“静默更新”
  const hasData = (currentTab.value === 'today_hot' && Object.keys(hotMap.value).length > 0) ||
                  (currentTab.value === 'prediction' && predictionList.value.length > 0) ||
                  (currentTab.value === 'monitor' && monitorList.value.length > 0)
  
  if (!hasData) {
    loading.value = true // 只有第一次空的时候才转圈
  }
  
  try {
    if (currentTab.value === 'prediction') {
      const currentKeywords = monitorList.value.map(item => item.name)
      const res = await getPredictions(currentKeywords)
      predictionList.value = res.data
    } else if (currentTab.value === 'today_hot') {
      const data = await getHotList(currentCategory.value)
      hotMap.value = data.data
      alerts.value = data.alerts
    } else {
      // 监控页面 & 客户管理
      const data = await getHotList('综合') 
      hotMap.value = data.data
      alerts.value = data.alerts
    }
  } catch (e) { 
    console.error(e) 
  } finally { 
    loading.value = false 
  }
}

const handleCustomerSave = async (customer) => {
  if (customer.isEdit) {
    const index = monitorList.value.findIndex(i => i.name === customer.name)
    if (index !== -1) monitorList.value[index] = { ...customer, isEdit: undefined }
  } else {
    if (monitorList.value.find(i => i.name === customer.name)) return alert('该客户已存在')
    monitorList.value.unshift({ ...customer, isEdit: undefined })
    await addKeyword(customer.name)
  }
  loadData()
}

const handleCustomerDelete = async (customer) => {
  const index = monitorList.value.findIndex(i => i.name === customer.name)
  if (index !== -1) {
    monitorList.value.splice(index, 1)
    await removeKeyword(customer.name)
    loadData()
  }
}

// === 模拟AI分析逻辑 ===
const getRelatedNews = (keyword) => {
  let matches = []
  if (!hotMap.value) return []
  for (const source in hotMap.value) {
    hotMap.value[source].forEach(item => {
      if (item.title && item.title.includes(keyword)) matches.push(item)
    })
  }
  return matches
}

const getRiskLevel = (name) => {
  const count = getRelatedNews(name).length
  if (count >= 3) return { text: '高风险', class: 'risk-high' }
  if (count > 0) return { text: '中风险', class: 'risk-mid' }
  return { text: '安全', class: 'risk-low' }
}

const getSentimentData = (name) => {
  const news = getRelatedNews(name)
  if (news.length === 0) return { neg: 0, neu: 10, pos: 90 }
  const neg = Math.min(80, news.length * 20)
  const neu = 20
  const pos = 100 - neg - neu
  return { neg, neu, pos }
}

const getTrendData = (name) => {
  const newsCount = getRelatedNews(name).length
  const base = newsCount > 0 ? 40 : 10
  return Array.from({length: 7}, () => Math.floor(Math.random() * 40) + base)
}

const getRiskTags = (name) => {
  const news = getRelatedNews(name)
  if (news.length === 0) return []
  return ['股价波动', '高管言论', '产品争议']
}

const getHighRiskCount = () => {
  return monitorList.value.filter(item => getRelatedNews(item.name).length >= 3).length
}

const getAllAlertsCount = () => {
  let count = 0
  monitorList.value.forEach(m => count += getRelatedNews(m.name).length)
  return count
}

const jumpToPrediction = () => { currentTab.value = 'prediction'; loadData(); }
const openAiSidebar = async (t) => {
  currentTopic.value = t; sidebarVisible.value = true; aiLoading.value = true; aiResult.value = {};
  try { aiResult.value = await analyzeTopic(t); } catch (e) { sidebarVisible.value = false; } finally { aiLoading.value = false; }
}
const onAdoptStrategy = (data) => { editorData.value = data; sidebarVisible.value = false; editorVisible.value = true; }

onMounted(() => { loadData() })
</script>

<style>
/* === 核心布局修复 (CSS Fix) === */

:root, html, body { 
  margin: 0; padding: 0; width: 100vw; height: 100vh; 
  overflow: hidden; /* 锁死 Body */
  background-color: #0f172a; 
}
#app { width: 100%; height: 100%; display: block; }
.app-container { display: flex; width: 100%; height: 100%; font-family: -apple-system, sans-serif; color: #334155; background-color: #f1f5f9; }
.sidebar-left { width: 240px; flex-shrink: 0; background: #0f172a; height: 100%; border-right: 1px solid #1e293b; }
.sidebar-right { width: 320px; flex-shrink: 0; background: #fff; border-left: 1px solid #e2e8f0; height: 100%; }

/* 中间区域：关键点 */
.main-center { 
  flex: 1; 
  min-width: 0; 
  height: 100%; /* 占满高度 */
  display: flex; 
  flex-direction: column; /* 纵向排列 */
  background: #f8fafc; 
  position: relative; 
  overflow: hidden; /* 防止内容撑大容器 */
}

/* 顶部标题栏：强力锁死 */
.top-bar { 
  flex: 0 0 60px; /* 【核心修复】禁止 Flex 压缩 */
  height: 60px;
  background: white; border-bottom: 1px solid #e2e8f0; 
  display: flex; justify-content: space-between; align-items: center; 
  padding: 0 24px; z-index: 20; 
}

/* 内容容器：自适应剩余空间 */
.hot-container, .full-height-container { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  overflow: hidden; /* 内部溢出隐藏 */
  min-height: 0; /* Flex 嵌套滚动的关键 */
}

/* 其他样式保持不变 */
.bar-left h1 { margin: 0; font-size: 18px; color: #1e293b; font-weight: 700; }
.update-pill { display: inline-block; margin-left: 12px; font-size: 11px; color: #64748b; background: #f1f5f9; padding: 2px 8px; border-radius: 4px; border: 1px solid #e2e8f0; }
.action-btn { background: #fff; border: 1px solid #cbd5e1; padding: 6px 12px; border-radius: 6px; font-size: 13px; color: #475569; cursor: pointer; transition: all 0.2s; font-weight: 600; }
.action-btn:hover { border-color: #3b82f6; color: #2563eb; background: #eff6ff; }
.action-btn:disabled { opacity: 0.6; cursor: wait; }

.category-tabs { height: 48px; min-height: 48px; flex-shrink: 0; display: flex; align-items: center; gap: 8px; padding: 0 24px; background: #fff; overflow-x: auto; }
.cat-pill { padding: 6px 16px; font-size: 13px; border-radius: 20px; color: #64748b; cursor: pointer; transition: all 0.2s; font-weight: 500; white-space: nowrap; }
.cat-pill:hover { background: #f1f5f9; color: #334155; }
.cat-pill.active { background: #2563eb; color: white; font-weight: 600; box-shadow: 0 2px 6px rgba(37,99,235,0.2); }
.source-anchors { height: 40px; min-height: 40px; flex-shrink: 0; display: flex; align-items: center; gap: 16px; padding: 0 24px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; border-top: 1px solid #f1f5f9; }
.anchor-label { font-size: 12px; color: #94a3b8; font-weight: bold; }
.anchor-item { font-size: 13px; color: #64748b; cursor: pointer; padding: 2px 0; position: relative; font-weight: 500; transition: all 0.2s; }
.anchor-item:hover { color: #dc2626; }
.anchor-item::before { content: ''; position: absolute; left: -8px; top: 50%; transform: translateY(-50%); width: 4px; height: 4px; background: #cbd5e1; border-radius: 50%; }
.anchor-item:first-of-type::before { display: none; }
.anchor-item:hover::before { background: #dc2626; }

.prediction-header, .monitor-dashboard-header { padding: 20px 24px; background: white; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; }
.pred-intro h2 { margin: 0 0 4px 0; font-size: 18px; color: #1e293b; }
.pred-intro p { margin: 0; font-size: 13px; color: #64748b; }

.monitor-dashboard-header { display: flex; gap: 20px; }
.dash-card { background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 20px; border-radius: 8px; min-width: 120px; }
.dash-card.warning { background: #fef2f2; border-color: #fee2e2; }
.dash-label { font-size: 12px; color: #64748b; margin-bottom: 4px; }
.dash-value { font-size: 24px; font-weight: 800; color: #1e293b; font-family: 'DIN Alternate'; }
.dash-value.red { color: #dc2626; }
.unit { font-size: 12px; color: #94a3b8; font-weight: normal; margin-left: 2px; }
.dash-desc-box { margin-left: auto; background: #eff6ff; border: 1px solid #dbeafe; padding: 10px 16px; border-radius: 8px; max-width: 300px; }
.desc-title { color: #2563eb; font-weight: 700; font-size: 12px; margin-bottom: 2px; }
.desc-text { color: #3b82f6; font-size: 11px; line-height: 1.4; }

.content-scroll-area { flex: 1; overflow-y: auto; padding: 24px; scroll-behavior: smooth; }
.source-section { margin-bottom: 40px; scroll-margin-top: 20px; }
.section-header { display: flex; align-items: center; margin-bottom: 16px; gap: 8px; }
.source-icon { font-size: 18px; }
.section-header h3 { margin: 0; font-size: 16px; font-weight: 700; color: #1e293b; }
.top-count { font-size: 11px; color: #94a3b8; background: #e2e8f0; padding: 2px 6px; border-radius: 4px; }
.cards-wrapper { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 24px; align-items: start; padding-bottom: 40px; }
.monitor-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; }

.loading-mask { text-align: center; padding: 60px 20px; color: #94a3b8; font-size: 14px; }
.spinner { width: 30px; height: 30px; border: 3px solid #e2e8f0; border-top-color: #2563eb; border-radius: 50%; margin: 0 auto 16px; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.empty-placeholder { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; }
.empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; }

.monitor-pro-card { background: white; border-radius: 12px; border: 1px solid #e2e8f0; padding: 20px; display: flex; flex-direction: column; gap: 16px; transition: all 0.2s; }
.monitor-pro-card:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.05); }
.mp-header { display: flex; justify-content: space-between; align-items: flex-start; }
.mp-name { margin: 0 0 4px 0; font-size: 16px; color: #1e293b; font-weight: 700; }
.industry-badge { font-size: 11px; background: #f1f5f9; color: #64748b; padding: 2px 6px; border-radius: 4px; }
.risk-badge { font-size: 11px; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
.risk-high { background: #fee2e2; color: #dc2626; }
.risk-mid { background: #ffedd5; color: #ea580c; }
.risk-low { background: #dcfce7; color: #16a34a; }
.mp-viz-row { display: flex; gap: 20px; }
.viz-col { flex: 1; }
.viz-label { font-size: 11px; color: #94a3b8; margin-bottom: 6px; display: block; }
.sentiment-bar-track { height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden; display: flex; width: 100%; margin-bottom: 6px; }
.s-bar { height: 100%; }
.s-bar.negative { background: #ef4444; }
.s-bar.neutral { background: #cbd5e1; }
.s-bar.positive { background: #22c55e; }
.viz-legend { display: flex; justify-content: space-between; font-size: 10px; color: #64748b; }
.trend-chart { height: 30px; display: flex; align-items: flex-end; gap: 4px; }
.trend-bar { flex: 1; background: #3b82f6; border-radius: 2px 2px 0 0; opacity: 0.8; }
.mp-tags-row { display: flex; align-items: center; gap: 8px; background: #fff1f2; padding: 8px; border-radius: 6px; }
.tags-wrapper { display: flex; gap: 6px; flex-wrap: wrap; }
.risk-tag { font-size: 10px; color: #be123c; background: white; padding: 1px 6px; border-radius: 4px; border: 1px solid #fda4af; }
.mp-footer { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f1f5f9; padding-top: 12px; margin-top: auto; }
.latest-alert { font-size: 12px; color: #334155; display: flex; align-items: center; gap: 6px; max-width: 200px; }
.alert-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.latest-alert.safe { color: #16a34a; }
.mp-btn { background: #eff6ff; color: #2563eb; border: none; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; font-weight: 500; }
.mp-btn:hover { background: #dbeafe; }
</style>