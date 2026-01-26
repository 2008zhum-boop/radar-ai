<template>
  <div class="hot-card">
    <div class="card-header">
      <div class="rank-badge" :class="rankClass">{{ rank }}</div>
      <div class="title-content">
        <div class="title-row">
          <span class="title-text">{{ title }}</span>
          <span v-if="label" class="tag" :class="labelClass">{{ label }}</span>
        </div>
        <div class="heat-info">🔥 {{ (heat / 10000).toFixed(1) }}万热度</div>
      </div>
    </div>

    <div class="ai-summary" v-if="summary">
      <div class="ai-label">✨ AI 提炼</div>
      <p class="summary-text">{{ summary }}</p>
    </div>

    <div class="action-bar">
      <button class="action-btn analyze-btn" @click="$emit('analyze')">
        <span class="icon">🤖</span> 深度分析
      </button>
      <button class="action-btn write-btn">
        <span class="icon">⚡️</span> 极速成稿
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  rank: Number,
  title: String,
  heat: Number,
  label: String,
  summary: String // <--- 接收 summary 参数
})

defineEmits(['analyze'])

const rankClass = computed(() => {
  if (props.rank === 1) return 'rank-1'
  if (props.rank === 2) return 'rank-2'
  if (props.rank === 3) return 'rank-3'
  return 'rank-other'
})

const labelClass = computed(() => {
  if (props.label === '爆') return 'tag-bao'
  if (props.label === '新') return 'tag-xin'
  if (props.label === '热') return 'tag-re'
  return ''
})
</script>

<style scoped>
.hot-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #f1f5f9;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 12px;
  /* 稍微增加高度适应内容 */
  height: auto; 
  min-height: 180px; 
}

.hot-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.08);
  border-color: #e2e8f0;
}

/* 头部布局 */
.card-header {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.rank-badge {
  flex-shrink: 0;
  width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 6px; font-weight: 800; font-size: 14px;
  font-family: 'DIN Alternate', sans-serif;
}
.rank-1 { background: #fee2e2; color: #dc2626; }
.rank-2 { background: #ffedd5; color: #ea580c; }
.rank-3 { background: #fef9c3; color: #ca8a04; }
.rank-other { background: #f1f5f9; color: #64748b; font-weight: 600; }

.title-content { flex: 1; overflow: hidden; }
.title-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; flex-wrap: wrap; }
.title-text { font-size: 15px; font-weight: 600; color: #1e293b; line-height: 1.4; }

.heat-info { font-size: 11px; color: #94a3b8; font-weight: 500; }

.tag { font-size: 10px; padding: 1px 4px; border-radius: 3px; color: white; transform: scale(0.9); font-weight: bold; }
.tag-bao { background: #ef4444; }
.tag-xin { background: #3b82f6; }
.tag-re { background: #f59e0b; }

/* === 新增：AI 摘要样式 === */
.ai-summary {
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px;
  border: 1px solid #e2e8f0;
  position: relative;
}
.ai-label {
  font-size: 10px;
  color: #2563eb;
  font-weight: bold;
  margin-bottom: 4px;
  display: flex; align-items: center;
}
.summary-text {
  font-size: 12px;
  color: #475569;
  line-height: 1.6;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3; /* 最多显示3行 */
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 底部按钮 */
.action-bar {
  margin-top: auto; /* 自动推到底部 */
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  border: none;
  border-radius: 6px;
  padding: 6px;
  font-size: 12px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 4px;
  font-weight: 500;
  transition: all 0.2s;
}

.analyze-btn { background: #eff6ff; color: #2563eb; }
.analyze-btn:hover { background: #dbeafe; }

.write-btn { background: #f0fdf4; color: #16a34a; }
.write-btn:hover { background: #dcfce7; }
</style>