<template>
  <div class="monitor-dashboard">
    <div class="stats-row">
      <div class="stat-card total">
        <div class="stat-label">今日总声量</div>
        <div class="stat-num">{{ stats.today_count }}</div>
        <div class="stat-desc">全网关键词提及次数</div>
      </div>
      <div class="stat-card risk" :class="{ 'has-risk': stats.risk_count > 0 }">
        <div class="stat-label">红色危机预警</div>
        <div class="stat-num">{{ stats.risk_count }}</div>
        <div class="stat-desc">需立即介入处理</div>
      </div>
      <div class="stat-card opportunity">
        <div class="stat-label">高价值情报</div>
        <div class="stat-num">{{ yellowCount }}</div>
        <div class="stat-desc">热点借势/竞品动态</div>
      </div>
    </div>

    <div class="main-content">
      <div class="feed-section">
        <div class="section-header">
          <h3>📡 实时情报流</h3>
          <button class="config-btn" @click="showConfig = true">⚙️ 配置监控词</button>
        </div>
        
        <div class="feed-list">
          <div v-for="log in stats.logs" :key="log.id" class="feed-item" :class="getLevelClass(log.level)">
            <div class="feed-left">
              <span class="level-dot"></span>
              <span class="feed-time">{{ log.time }}</span>
            </div>
            <div class="feed-body">
              <div class="feed-title-row">
                <span class="source-tag">{{ log.source }}</span>
                <span class="category-tag">{{ log.tags }}</span>
                <a :href="log.url" target="_blank" class="feed-title">{{ log.title }}</a>
              </div>
              <p class="feed-summary">{{ log.summary || '暂无摘要，点击标题查看原文...' }}</p>
              <div class="feed-meta">
                <span class="sentiment-score" :style="{ color: getScoreColor(log.score) }">
                  情感值: {{ log.score > 0 ? '+' : '' }}{{ log.score }}
                </span>
                <span v-if="log.level === 3" class="action-required">⚠️ 建议防御：启动公关预警</span>
                <span v-if="log.level === 2" class="action-required">⚡ 建议进攻：借势选题</span>
              </div>
            </div>
          </div>
          
          <div v-if="stats.logs.length === 0" class="empty-state">
            暂无相关情报，请在右上角“配置监控词”添加关键词。
          </div>
        </div>
      </div>

      <div v-if="showConfig" class="config-modal-overlay" @click.self="showConfig = false">
        <div class="config-modal">
          <h3>🔧 监控矩阵配置</h3>
          <div class="input-group">
            <input v-model="newWord" placeholder="输入关键词 (如: 特斯拉)" />
            <select v-model="newType">
              <option :value="1">🔴 核心圈 (自身)</option>
              <option :value="2">🟡 竞品圈 (对手)</option>
              <option :value="3">🔵 行业圈 (宏观)</option>
            </select>
            <input v-model="newSensitive" placeholder="关联敏感词 (逗号隔开)" />
            <button @click="addKeyword">添加</button>
          </div>
          
          <div class="keyword-list">
            <div v-for="kw in keywords" :key="kw.id" class="kw-tag" :class="'type-'+kw.type">
              {{ kw.word }} 
              <span class="kw-cat">({{ kw.category }})</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

// 获取 API 地址
const API_URL = import.meta.env.PROD 
  ? 'https://radar-backend-cvaq.onrender.com' 
  : 'http://localhost:8000'

const stats = ref({ today_count: 0, risk_count: 0, logs: [] })
const keywords = ref([])
const showConfig = ref(false)

const newWord = ref('')
const newType = ref(1)
const newSensitive = ref('')

// 计算黄色预警数量
const yellowCount = computed(() => stats.value.logs.filter(l => l.level === 2).length)

const fetchDashboard = async () => {
  const res = await axios.get(`${API_URL}/monitor/dashboard`)
  stats.value = res.data
}

const fetchConfig = async () => {
  const res = await axios.get(`${API_URL}/monitor/config`)
  keywords.value = res.data
}

onMounted(() => {
  fetchDashboard()
  fetchConfig()
  // 模拟轮询，每30秒刷新一次
  setInterval(fetchDashboard, 30000)
})

const addKeyword = async () => {
  if(!newWord.value) return
  await axios.post(`${API_URL}/monitor/config/add`, {
    word: newWord.value,
    type: newType.value,
    category: newType.value === 1 ? '品牌' : (newType.value === 2 ? '竞品' : '行业'),
    sensitive: newSensitive.value
  })
  newWord.value = ''
  newSensitive.value = ''
  await fetchConfig()
}

const getLevelClass = (level) => {
  if (level === 3) return 'level-red'
  if (level === 2) return 'level-yellow'
  return 'level-green'
}

const getScoreColor = (score) => {
  if (score < -0.2) return '#ef4444'
  if (score > 0.2) return '#10b981'
  return '#94a3b8'
}
</script>

<style scoped>
.monitor-dashboard { padding: 20px; background: #f8fafc; min-height: 100vh; }

/* 顶部统计 */
.stats-row { display: flex; gap: 20px; margin-bottom: 24px; }
.stat-card {
  flex: 1; background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.stat-label { font-size: 14px; color: #64748b; margin-bottom: 8px; }
.stat-num { font-size: 32px; font-weight: 800; color: #1e293b; line-height: 1; margin-bottom: 8px; }
.stat-desc { font-size: 12px; color: #94a3b8; }

.stat-card.risk.has-risk .stat-num { color: #dc2626; }
.stat-card.risk.has-risk { border-color: #fecaca; background: #fef2f2; }
.stat-card.opportunity .stat-num { color: #d97706; }

/* 内容区 */
.feed-section { background: white; border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.config-btn { 
  background: #f1f5f9; border: none; padding: 8px 16px; border-radius: 6px; 
  cursor: pointer; font-size: 13px; font-weight: 600; color: #475569;
}
.config-btn:hover { background: #e2e8f0; }

/* 情报流 Item */
.feed-item { 
  display: flex; gap: 16px; padding: 16px; border-bottom: 1px solid #f1f5f9; 
  transition: all 0.2s; border-radius: 8px;
}
.feed-item:hover { background: #f8fafc; }

/* 颜色分级 */
.level-red { border-left: 4px solid #ef4444; background: #fff5f5; }
.level-yellow { border-left: 4px solid #f59e0b; }
.level-green { border-left: 4px solid #10b981; }

.feed-left { display: flex; flex-direction: column; align-items: center; width: 50px; flex-shrink: 0; }
.level-dot { width: 10px; height: 10px; border-radius: 50%; margin-bottom: 6px; }
.level-red .level-dot { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.4); }
.level-yellow .level-dot { background: #f59e0b; }
.level-green .level-dot { background: #10b981; }
.feed-time { font-size: 12px; color: #94a3b8; }

.feed-body { flex: 1; }
.feed-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.source-tag { background: #0f172a; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
.category-tag { background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
.feed-title { font-weight: 700; color: #1e293b; text-decoration: none; font-size: 15px; }
.feed-title:hover { color: #2563eb; }

.feed-summary { font-size: 13px; color: #64748b; margin-bottom: 8px; line-height: 1.5; }
.feed-meta { display: flex; gap: 12px; font-size: 12px; align-items: center; }
.action-required { font-weight: 700; color: #b91c1c; background: #fee2e2; padding: 2px 8px; border-radius: 4px; }

/* 弹窗 */
.config-modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.config-modal { background: white; padding: 24px; border-radius: 12px; width: 500px; }
.input-group { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.input-group input, .input-group select { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; flex: 1; }
.keyword-list { display: flex; flex-wrap: wrap; gap: 8px; }
.kw-tag { padding: 4px 12px; border-radius: 20px; font-size: 12px; background: #f1f5f9; border: 1px solid #cbd5e1; }
.kw-tag.type-1 { background: #fee2e2; border-color: #fca5a5; color: #991b1b; } /* 核心 */
.kw-tag.type-2 { background: #fef3c7; border-color: #fcd34d; color: #92400e; } /* 竞品 */
</style>