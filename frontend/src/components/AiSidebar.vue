<template>
  <div class="sidebar-overlay" v-if="visible" @click="$emit('close')">
    <div class="sidebar" @click.stop>
      <div class="sidebar-header">
        <h2>🤖 AI 智能选题助理</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="sidebar-content">
        <div v-if="loading" class="loading-box">
          <div class="spinner"></div>
          <p>AI 正在阅读全网资料并思考...</p>
          <p class="sub-text">分析对象: {{ topic }}</p>
        </div>

        <div v-else class="result-box">
          <div class="meta-row">
            <span class="meta-tag">分析对象: {{ result.topic }}</span>
            <span class="meta-tag emotion">情绪判定: {{ result.emotion }}</span>
          </div>

          <div class="section">
            <h3>💡 推荐切入角度</h3>
            <div class="card angle-card" v-for="(angle, i) in result.angles" :key="i">
              {{ angle }}
            </div>
          </div>

          <div class="section">
            <h3>🔥 爆款标题预测</h3>
            <div class="title-list">
              <div class="title-item" v-for="(t, i) in result.titles" :key="i">
                <span class="num">{{ i+1 }}</span> {{ t }}
                <button class="btn-sm-copy">复制</button>
              </div>
            </div>
          </div>
          
          <button 
  class="btn-action" 
  @click="$emit('adopt', { 
    title: result.titles[0], // 默认采纳第一个标题
    angle: result.angles[0], // 默认采纳第一个角度
    topic: topic 
  })"
>
  采纳并开始撰稿
</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  visible: Boolean,
  loading: Boolean,
  topic: String,
  result: Object
})

defineEmits(['close'])
</script>

defineEmits(['close', 'adopt']) // 新增 'adopt'

<style scoped>
/* 动画与布局 */
.sidebar-overlay {
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(0,0,0,0.5); z-index: 1000;
  display: flex; justify-content: flex-end;
}
.sidebar {
  width: 450px; height: 100%; background: white;
  box-shadow: -10px 0 30px rgba(0,0,0,0.15);
  display: flex; flex-direction: column;
  animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }

.sidebar-header {
  padding: 20px 24px; border-bottom: 1px solid #e2e8f0;
  display: flex; justify-content: space-between; align-items: center;
}
.sidebar-header h2 { margin: 0; font-size: 1.25rem; color: #1e293b; }
.close-btn { background: none; border: none; font-size: 28px; color: #94a3b8; cursor: pointer; }
.close-btn:hover { color: #334155; }

.sidebar-content { padding: 24px; flex: 1; overflow-y: auto; background: #f8fafc; }

/* 加载动画 */
.loading-box { text-align: center; margin-top: 60px; color: #64748b; }
.spinner {
  width: 40px; height: 40px; border: 4px solid #cbd5e1;
  border-top-color: #2563eb; border-radius: 50%;
  margin: 0 auto 20px; animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.sub-text { font-size: 0.9em; opacity: 0.8; margin-top: 5px; }

/* 结果样式 */
.meta-row { margin-bottom: 24px; }
.meta-tag { display: inline-block; background: #e2e8f0; padding: 4px 10px; border-radius: 6px; font-size: 12px; margin-right: 10px; color: #475569; }
.emotion { background: #fee2e2; color: #991b1b; }

.section { margin-bottom: 32px; }
.section h3 { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; font-weight: 700; }

.angle-card { 
  background: white; padding: 16px; border-radius: 8px; margin-bottom: 10px; 
  border-left: 4px solid #3b82f6; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  line-height: 1.6; color: #334155;
}

.title-list { display: flex; flex-direction: column; gap: 8px; }
.title-item { 
  background: white; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; 
  font-weight: 500; font-size: 15px; display: flex; align-items: center; justify-content: space-between;
}
.title-item:hover { border-color: #3b82f6; color: #2563eb; }
.num { color: #cbd5e1; font-weight: 900; margin-right: 12px; font-style: italic; }
.btn-sm-copy { font-size: 12px; padding: 2px 8px; border: 1px solid #e2e8f0; background: #f8fafc; border-radius: 4px; cursor: pointer; display: none; }
.title-item:hover .btn-sm-copy { display: block; }

.btn-action { 
  width: 100%; padding: 14px; background: #2563eb; color: white; border: none; 
  border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; 
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
}
.btn-action:hover { background: #1d4ed8; }
</style>