<template>
  <div class="hot-card" @click="openLink">
    <div class="card-header">
      <div class="rank-badge" :class="rankClass">{{ rank }}</div>
      <h3 class="card-title">{{ title }}</h3>
      <span v-if="label" class="hot-label">{{ label }}</span>
    </div>

    <div class="card-meta">
      <span class="heat-value">🔥 {{ formattedHeat }}热度</span>
      <span v-if="category" class="category-tag"># {{ category }}</span>
    </div>

    <div class="ai-summary-box">
      <div class="summary-header">
        <span class="ai-icon">✨ AI 提炼</span>
      </div>
      <p class="summary-text">{{ summary }}</p>
      
      <div class="action-row">
        <button class="action-btn analyze" @click.stop="$emit('analyze')">
          <span class="btn-icon">📊</span> 深度分析
        </button>
        <button class="action-btn write" @click.stop="$emit('analyze')">
          <span class="btn-icon">⚡</span> 极速成稿
        </button>
        <span class="click-hint">点击查看原文 ↗</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  rank: Number,
  title: String,
  heat: [Number, String],
  label: String,
  summary: String,
  category: String, // 新增接收分类
  url: String       // 新增接收链接
})

defineEmits(['analyze'])

const rankClass = computed(() => {
  if (props.rank === 1) return 'rank-1'
  if (props.rank === 2) return 'rank-2'
  if (props.rank === 3) return 'rank-3'
  return 'rank-other'
})

const formattedHeat = computed(() => {
  const num = Number(props.heat)
  if (isNaN(num)) return props.heat
  return num > 10000 ? (num / 10000).toFixed(1) + '万' : num
})

// 跳转原文
const openLink = () => {
  if (props.url) {
    window.open(props.url, '_blank')
  }
}
</script>

<style scoped>
.hot-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
  cursor: pointer; /* 鼠标变手型 */
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
}

.hot-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.06);
  border-color: #cbd5e1;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.rank-badge {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: #f1f5f9;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'DIN Alternate', sans-serif;
}
.rank-1 { background: #fee2e2; color: #dc2626; }
.rank-2 { background: #ffedd5; color: #ea580c; }
.rank-3 { background: #fef9c3; color: #ca8a04; }

.card-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.5;
  flex: 1;
}

.hot-label {
  flex-shrink: 0;
  background: #fff7ed;
  color: #ea580c;
  border: 1px solid #ffedd5;
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 4px;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}

.heat-value { color: #f59e0b; font-weight: 600; }

.category-tag {
  color: #3b82f6;
  background: #eff6ff;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

/* AI 摘要区域 (核心修改) */
.ai-summary-box {
  background: #f8fafc;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #f1f5f9;
}

.summary-header {
  margin-bottom: 6px;
  display: flex;
  align-items: center;
}

.ai-icon {
  font-size: 11px;
  color: #2563eb;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 4px;
}

.summary-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.8; /* 增加行高，更易阅读 */
  color: #475569;
  text-align: justify;
  /* 移除 line-clamp，显示全文 */
}

/* 底部操作栏 */
.action-row {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed #e2e8f0;
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-btn {
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.action-btn.analyze {
  background: #eff6ff;
  color: #2563eb;
}
.action-btn.analyze:hover { background: #dbeafe; }

.action-btn.write {
  background: #f0fdf4;
  color: #16a34a;
}
.action-btn.write:hover { background: #dcfce7; }

.click-hint {
  margin-left: auto;
  font-size: 11px;
  color: #94a3b8;
  opacity: 0;
  transition: opacity 0.2s;
}

.hot-card:hover .click-hint {
  opacity: 1;
}
</style>