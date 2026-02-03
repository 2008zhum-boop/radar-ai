<template>
  <div class="hot-card-grid">
    <div 
      v-for="item in list" 
      :key="item.title" 
      class="hot-card"
      @click="$emit('click-item', item)"
    >
      <!-- Dismiss Button -->
      <button class="dismiss-btn" @click.stop="$emit('dismiss', item.title)">✕</button>

      <div class="card-header">
        <div class="rank-badge" :class="getRankClass(item.rank)">{{ item.rank }}</div>
        <a :href="item.url" target="_blank" class="card-title" @click.stop>{{ item.title }}</a>
        <!-- Prediction Labels -->
        <span v-if="getPredictionLabel(item)" class="pred-tag" :class="getPredictionLabel(item).class">
           {{ getPredictionLabel(item).text }}
        </span>
        <span v-else-if="item.label" class="hot-tag">{{ item.label }}</span>
      </div>

      <div class="meta-row">
        <div class="heat-wrapper">
           <span class="heat-val">🔥 {{ formatNumber(item.heat) }}万热度</span>
           <!-- Trend Indicator (Mocked for now based on simple logic or random if no data) -->
           <span class="trend-icon" :class="getTrendClass(item)">
             {{ getTrendIcon(item) }}
           </span>
        </div>
        <span class="cat-tag"># {{ item.category || '综合' }}</span>
        <span v-for="tag in (item.tags || []).slice(0,2)" :key="tag" class="content-tag">{{ tag }}</span>
      </div>

      <!-- AI Box -->
      <div class="ai-box">
        <div class="ai-header">
           <span class="ai-title">✨ AI 提炼</span>
           <button class="expand-btn" @click.stop="toggleExpand(item.title)">
             {{ expandedItems.has(item.title) ? '收起 ∧' : '展开 ∨' }}
           </button>
        </div>
        
        <div class="ai-content" :class="{ collapsed: !expandedItems.has(item.title) }">
           <!-- Simulation of Fact vs Angle -->
           <div class="ai-section">
             <span class="ai-label fact">事实:</span>
             <span class="ai-text" v-html="highlightKeywords(getSummaryFact(item.summary))"></span>
           </div>
           <div class="ai-section" v-if="getSummaryAngle(item.summary)">
             <span class="ai-label angle">角度:</span>
             <span class="ai-text highlight" v-html="highlightKeywords(getSummaryAngle(item.summary))"></span>
           </div>
        </div>
      </div>

      <!-- Client Relevance -->
      <div v-if="item.matched_clients && item.matched_clients.length > 0" class="client-relevance">
        <span class="cr-icon">💡</span>
        <span class="cr-label">监控词:</span>
        <span v-for="client in item.matched_clients" :key="client" class="cr-tag">{{ client }}</span>
      </div>

      <!-- Source & Sentiment -->
      <div class="source-bar-container" v-if="item.source_distribution">
         <!-- Source Tags (Simplified) -->
         <div class="source-tags-row">
            <span class="st-label">来源:</span>
            <div class="st-list">
                <span 
                    v-for="(pct, src) in item.source_distribution" 
                    :key="src"
                    class="src-mini-tag"
                    v-show="pct > 0"
                >
                    <span class="src-dot" :style="{background: getSourceColor(src)}"></span>
                    {{ src }}
                </span>
            </div>
         </div>
         
         <!-- Sentiment Bar -->
         <div class="sb-label-row mt-2" v-if="item.sentiment_distribution">
            <span class="sb-title">情感分布</span>
         </div>
         <div class="sb-track" v-if="item.sentiment_distribution">
           <div class="sb-seg" :style="{ width: item.sentiment_distribution.pos + '%', background: '#22c55e' }" title="正面"></div>
           <div class="sb-seg" :style="{ width: item.sentiment_distribution.neu + '%', background: '#94a3b8' }" title="中性"></div>
           <div class="sb-seg" :style="{ width: item.sentiment_distribution.neg + '%', background: '#ef4444' }" title="负面"></div>
         </div>
         <div class="sb-legend-mini" v-if="item.sentiment_distribution">
            <span>😊 {{ item.sentiment_distribution.pos }}%</span>
            <span>😐 {{ item.sentiment_distribution.neu }}%</span>
            <span>😡 {{ item.sentiment_distribution.neg }}%</span>
         </div>
      </div>

      <div class="card-footer">
        <button class="action-btn blue" @click.stop="$emit('analyze', item)">
           <span class="btn-icon">📊</span> 深度分析
        </button>
        <button class="action-btn green" @click.stop="$emit('instant-draft', item.title)">
           <span class="btn-icon">⚡</span> 极速成稿
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  list: Array
})

const emit = defineEmits(['analyze', 'dismiss', 'click-item', 'instant-draft'])

const expandedItems = ref(new Set())

const toggleExpand = (id) => {
  if (expandedItems.value.has(id)) expandedItems.value.delete(id)
  else expandedItems.value.add(id)
}

const formatNumber = (num) => {
  if (num > 10000) return (num / 10000).toFixed(1)
  return num
}

const getRankClass = (rank) => {
  if (rank === 1) return 'rank-1'
  if (rank === 2) return 'rank-2'
  if (rank === 3) return 'rank-3'
  return 'rank-common'
}

// Mock Trend Logic (In real app, backend provides this)
const getTrendClass = (item) => {
    // Randomly assign for demo if no real data
    const isRising = (item.title.length % 2 === 0) 
    return isRising ? 'rising' : 'falling'
}
const getTrendIcon = (item) => {
    const isRising = (item.title.length % 2 === 0) 
    return isRising ? '📈' : '📉'
}

const getPredictionLabel = (item) => {
    if (item.rank <= 3) return { text: '🚀 爆发期', class: 'rocket' }
    if (item.heat > 1000000 && item.rank > 10 && item.rank < 15) return { text: '🔥 潜力股', class: 'potential' }
    return null
}

const getSourceColor = (src) => {
    const map = { '微博': '#ef4444', '微信': '#22c55e', '头条': '#f97316', 'B站': '#ec4899', '百度': '#3b82f6' }
    return map[src] || '#94a3b8'
}

// Summary Parsing
const getSummaryFact = (summary) => {
    if (!summary) return '暂时无法获取详情。'
    if (typeof summary === 'object') return summary.fact || 'AI分析中...'
    
    // Legacy String Handling
    const str = String(summary)
    const parts = str.split('。')
    if (parts.length < 2) return str
    return parts[0] + '。' + parts[1] + '。'
}

const getSummaryAngle = (summary) => {
    if (!summary) return ''
    if (typeof summary === 'object') return summary.angle || ''
    
    // Legacy String
    const parts = summary.split('。')
    if (parts.length > 2) return '建议切入：' + parts.slice(2).join('。')
    return ''
}

const highlightKeywords = (text) => {
    // Simple regex to bold monetary values, companies (mock), etc.
    if (!text) return ''
    return text.replace(/(\d+(?:万|亿)?(?:元|美元|人民币)?)/g, '<b>$1</b>')
               .replace(/(?:“|")([^”"]+)(?:”|")/g, '<b>“$1”</b>')
}
</script>

<style scoped>
.hot-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
  padding: 10px 0;
}

.hot-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: all 0.2s;
  border: 2px solid transparent; 
  position: relative;
  cursor: pointer;
}
.hot-card:hover { transform: translateY(-4px); box-shadow: 0 8px 16px rgba(0,0,0,0.08); z-index: 2; border-color: #cbd5e1; }
/* .selected styles removed */

.chk-icon { font-size: 20px; }

.dismiss-btn {
    position: absolute; top: 12px; right: 12px; border: none; background: none; 
    color: #cbd5e1; font-size: 16px; cursor: pointer; opacity: 0; transition: opacity 0.2s;
}
.hot-card:hover .dismiss-btn { opacity: 1; }
.dismiss-btn:hover { color: #94a3b8; }

/* Header */
.card-header { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px; padding-right: 20px; }
.rank-badge { 
  min-width: 22px; height: 22px; line-height: 22px; 
  text-align: center; border-radius: 6px; 
  font-size: 13px; font-weight: 800; color: white;
  margin-top: 2px;
}
.rank-1 { background: #fee2e2; color: #dc2626; }
.rank-2 { background: #ffedd5; color: #ea580c; }
.rank-3 { background: #fef9c3; color: #ca8a04; }
.rank-common { background: #f1f5f9; color: #64748b; }

.card-title { 
  flex: 1; font-size: 17px; font-weight: 700; color: #1e293b; 
  text-decoration: none; line-height: 1.4; letter-spacing: -0.01em;
}
.card-title:hover { color: #2563eb; }

/* Tags */
.hot-tag { font-size: 10px; padding: 2px 6px; background: #fff1f2; color: #e11d48; border-radius: 4px; white-space: nowrap; }
.pred-tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; white-space: nowrap; font-weight: 700; display: flex; align-items: center; }
.pred-tag.rocket { background: #eff6ff; color: #2563eb; }
.pred-tag.potential { background: #fff7ed; color: #ea580c; }

/* Meta */
.meta-row { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 14px; align-items: center; font-size: 13px; }
.heat-wrapper { display: flex; align-items: center; gap: 6px; }
.heat-val { color: #f59e0b; font-weight: 700; font-family: 'DIN Alternate', sans-serif; font-size: 15px; }
.trend-icon { font-size: 12px; }
.cat-tag { color: #3b82f6; background: #eff6ff; padding: 1px 6px; border-radius: 4px; font-weight: 500; }
.content-tag { color: #64748b; background: #f1f5f9; padding: 1px 6px; border-radius: 4px; font-size: 12px; }

/* AI Box */
.ai-box { background: #f8fafc; border-radius: 8px; padding: 12px; margin-bottom: 12px; border: 1px solid #f1f5f9; }
.ai-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.ai-title { font-size: 12px; font-weight: 700; color: #2563eb; display: flex; align-items: center; gap: 4px; }
.expand-btn { background: none; border: none; color: #94a3b8; font-size: 11px; cursor: pointer; }
.expand-btn:hover { color: #64748b; }

.ai-content.collapsed .ai-text {
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.ai-content.collapsed .ai-section { margin-bottom: 0; } 
.ai-content.collapsed .highlight { background: none; color: inherit; padding: 0; }

.ai-section { margin-bottom: 6px; font-size: 13px; line-height: 1.6; color: #475569; }
.ai-label { font-weight: 700; margin-right: 6px; font-size: 12px; }
.ai-label.fact { color: #0f172a; }
.ai-label.angle { color: #059669; }
.ai-text { white-space: pre-wrap; }
.ai-text.highlight { background: #f0fdf4; padding: 2px 4px; border-radius: 4px; color: #059669; }

/* Client Relevance */
.client-relevance { 
    display: flex; align-items: center; gap: 8px; margin-bottom: 12px; 
    background: #fffbeb; padding: 8px 12px; border-radius: 6px; border: 1px solid #fcd34d;
}
.cr-icon { font-size: 14px; }
.cr-label { font-size: 12px; font-weight: 700; color: #b45309; }
.cr-tag { font-size: 12px; background: white; padding: 2px 8px; border-radius: 10px; color: #d97706; font-weight: 600; border: 1px solid #fcd34d; }

/* Source Bar */
.source-bar-container { margin-bottom: 16px; }
.source-tags-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-size: 11px; }
.st-label { color: #94a3b8; font-weight: 600; white-space: nowrap; }
.st-list { display: flex; flex-wrap: wrap; gap: 6px; }
.src-mini-tag { display: flex; align-items: center; gap: 4px; padding: 2px 6px; background: #f8fafc; border-radius: 4px; border: 1px solid #f1f5f9; color: #64748b; }
.src-dot { width: 6px; height: 6px; border-radius: 50%; }

.sb-label-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
.sb-title { font-size: 10px; color: #94a3b8; font-weight: 600; }
.mt-2 { margin-top: 8px; }

.sb-track { display: flex; height: 6px; border-radius: 3px; overflow: hidden; background: #e2e8f0; } 
.sb-seg { height: 100%; transition: width 0.5s; }
.sb-legend-mini { display: flex; justify-content: space-between; font-size: 10px; color: #64748b; margin-top: 4px; }
/* .dot removed, used src-dot */

/* Footer */
.card-footer { display: flex; gap: 12px; }
.action-btn { 
  flex: 1; border: none; padding: 8px; border-radius: 6px; 
  font-size: 13px; font-weight: 600; cursor: pointer; 
  display: flex; align-items: center; justify-content: center; gap: 6px;
  transition: all 0.2s;
}
.action-btn:hover { transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.action-btn.blue { background: #eff6ff; color: #2563eb; }
.action-btn.green { background: #f0fdf4; color: #16a34a; }
</style>