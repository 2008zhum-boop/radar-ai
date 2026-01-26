<template>
  <div class="pred-card">
    <div class="card-header">
      <div class="relation-badges">
        <span class="badge keyword-badge">{{ keyword }}</span>
        <span class="link-icon">🔗</span>
        <span class="badge event-badge">{{ event }}</span>
      </div>
      <div class="score-area">
        <span class="score-num">{{ score }}</span>
        <span class="score-label">潜力值</span>
      </div>
    </div>

    <div class="main-content">
      <div class="strategy-tag">{{ type }}</div>
      <h3 class="pred-title">{{ title }}</h3>
      <p class="pred-reason">{{ reason }}</p>
    </div>

    <div class="action-bar">
      <button class="action-btn" @click="$emit('adopt')">
        ✨ 采纳此选题
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  keyword: String,
  event: String,
  type: String,
  title: String,
  reason: String,
  score: Number
})
defineEmits(['adopt'])
</script>

<style scoped>
.pred-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  display: flex; flex-direction: column; gap: 16px;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}
/* 给卡片加一个稍微高级点的顶边 */
.pred-card::before {
  content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px;
  background: linear-gradient(90deg, #8b5cf6, #ec4899); /* 紫色到粉色渐变，区别于热点的蓝色 */
}
.pred-card:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(139, 92, 246, 0.1); }

.card-header { display: flex; justify-content: space-between; align-items: flex-start; }
.relation-badges { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.badge { padding: 4px 8px; border-radius: 4px; font-weight: 600; }
.keyword-badge { background: #f3e8ff; color: #7e22ce; border: 1px solid #d8b4fe; } /* 紫色系 */
.event-badge { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
.link-icon { font-size: 10px; color: #cbd5e1; }

.score-area { text-align: right; line-height: 1; }
.score-num { font-size: 20px; font-weight: 800; color: #db2777; font-family: 'DIN Alternate', sans-serif; }
.score-label { display: block; font-size: 9px; color: #94a3b8; margin-top: 2px; }

.main-content { flex: 1; }
.strategy-tag { display: inline-block; font-size: 10px; color: #db2777; border: 1px solid #fbcfe8; padding: 1px 6px; border-radius: 10px; margin-bottom: 8px; }
.pred-title { font-size: 16px; font-weight: 700; color: #1e293b; margin: 0 0 8px 0; line-height: 1.5; }
.pred-reason { font-size: 12px; color: #64748b; margin: 0; line-height: 1.6; background: #fafafa; padding: 8px; border-radius: 6px; }

.action-btn {
  width: 100%; padding: 8px; border-radius: 6px; border: none; font-size: 13px; font-weight: 600; cursor: pointer;
  background: linear-gradient(90deg, #8b5cf6, #ec4899); color: white;
  opacity: 0.9; transition: opacity 0.2s;
}
.action-btn:hover { opacity: 1; }
</style>