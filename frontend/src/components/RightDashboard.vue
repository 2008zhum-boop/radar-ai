<template>
  <div class="dash-container">
    <div class="dash-card">
      <div class="card-head">
        <h3>📡 舆情雷达</h3>
        <span class="status-badge" :class="alertCount>0 ? 'red' : 'green'">
          {{ alertCount>0 ? '异常' : '正常' }}
        </span>
      </div>
      
      <div class="kpi-row">
        <div class="kpi-box">
          <div class="lbl">今日提及</div>
          <div class="val">{{ alertCount }}</div>
        </div>
        <div class="kpi-box">
          <div class="lbl">风险指数</div>
          <div class="val" :class="alertCount>0 ? 'text-red' : 'text-green'">
            {{ alertCount>0 ? '高' : '低' }}
          </div>
        </div>
      </div>

      <div class="alert-feed" v-if="alerts.length">
        <div class="feed-title">🚨 实时警报</div>
        <div v-for="(a, i) in alerts.slice(0,3)" :key="i" class="feed-item">{{ a }}</div>
      </div>
      <div v-else class="empty-feed">暂无风险</div>
    </div>

    <div class="dash-card ai-style">
      <div class="card-head">
        <h3>💡 灵感助手</h3>
      </div>
      <p class="ai-tip">基于历史数据推荐：</p>
      <div class="idea-item commercial">
        <span class="tag">深度商业</span>
        <p>适合切入 Top3 热点，分析资本博弈。</p>
      </div>
      <div class="idea-item emotion">
        <span class="tag">职场情绪</span>
        <p>今日“焦虑”指数较高，建议撰写破局类文章。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ alerts: Array })
const alertCount = computed(() => props.alerts.length)
</script>

<style scoped>
.dash-container {
  padding: 24px;
  height: 100%;
  display: flex; flex-direction: column; gap: 24px;
  overflow-y: auto; /* 允许右侧内部滚动 */
}

.dash-card {
  background: white; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.card-head h3 { margin: 0; font-size: 14px; color: #1e293b; font-weight: 700; }
.status-badge { font-size: 10px; padding: 2px 6px; border-radius: 4px; }
.status-badge.green { background: #dcfce7; color: #166534; }
.status-badge.red { background: #fee2e2; color: #991b1b; }

.kpi-row { display: flex; gap: 12px; margin-bottom: 16px; }
.kpi-box { flex: 1; background: #f8fafc; padding: 10px; border-radius: 8px; text-align: center; }
.lbl { font-size: 11px; color: #64748b; }
.val { font-size: 18px; font-weight: 800; color: #334155; margin-top: 4px; }
.text-green { color: #22c55e; } .text-red { color: #ef4444; }

.alert-feed .feed-title { font-size: 11px; color: #ef4444; font-weight: bold; margin-bottom: 6px; }
.feed-item { font-size: 11px; background: #fef2f2; padding: 6px; border-radius: 4px; color: #991b1b; margin-bottom: 4px; }
.empty-feed { font-size: 11px; color: #94a3b8; text-align: center; padding: 8px; background: #f8fafc; border-radius: 4px; }

.ai-style { background: linear-gradient(to bottom, #eff6ff, #fff); border-color: #bfdbfe; }
.ai-tip { font-size: 11px; color: #64748b; margin: 0 0 10px 0; }
.idea-item { background: rgba(255,255,255,0.6); padding: 10px; border-radius: 6px; margin-bottom: 8px; border: 1px solid #dbeafe; }
.idea-item .tag { display: inline-block; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; margin-bottom: 4px; }
.idea-item.commercial .tag { background: #dbeafe; color: #1e40af; }
.idea-item.emotion .tag { background: #fee2e2; color: #991b1b; }
.idea-item p { margin: 0; font-size: 11px; color: #334155; line-height: 1.4; }
</style>