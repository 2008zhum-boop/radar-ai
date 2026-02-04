
<template>
  <div class="agent-manager">
    <div class="header">
      <h2>🤖 Agent 管理</h2>
      <button class="create-btn" @click="showCreateModal = true">
        <span class="icon">➕</span> 创建新 Agent
      </button>
    </div>

    <!-- Agent List -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="agents.length === 0" class="empty-state">
      <div class="empty-icon">🤖</div>
      <p>暂无 Agent，创建一个来自动抓取和写作吧！</p>
    </div>
    
    <div v-else class="agent-grid">
      <div v-for="agent in agents" :key="agent.id" class="agent-card">
        <div class="ac-header">
           <div class="ac-icon">🤖</div>
           <div class="ac-info">
             <div class="ac-name">{{ agent.name }}</div>
             <div class="ac-status">
                <span class="status-dot green"></span> 活跃
             </div>
           </div>
           <button class="edit-btn" @click="handleEdit(agent)" title="编辑">✎</button>
           <button class="del-btn" @click="handleDelete(agent.id)" title="删除">✕</button>
        </div>
        
        <div class="ac-body">
           <div class="field-group">
              <label>设定角度</label>
              <div class="val text-blue">{{ agent.angle }}</div>
           </div>
           
           <!-- New Fields Display -->
           <div class="field-row">
               <div class="field-group half">
                  <label>关键词</label>
                  <div class="val">{{ agent.keywords }}</div>
               </div>
               <div class="field-group half">
                  <label>字数</label>
                  <div class="val">{{ agent.word_count || 1500 }}字</div>
               </div>
           </div>
           
           <!-- Removed Source display -->

           <div class="field-group">
              <label>提示词指令</label>
              <div class="val prompt">{{ agent.prompt }}</div>
           </div>
           <div class="ac-meta">
              最后运行: {{ formatTime(agent.last_run_at) }}
           </div>
        </div>
        
        <div class="ac-footer">
           <button class="run-btn" @click="handleRun(agent)" :disabled="runningId === agent.id">
              <span v-if="runningId === agent.id">运行中...</span>
              <span v-else>⚡️ 立即运行</span>
           </button>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
           <h3>{{ form.id ? '编辑 Agent' : '创建 AI 写作 Agent' }}</h3>
           <button class="close-btn" @click="showCreateModal = false">✕</button>
        </div>
        <div class="modal-body">
           <!-- Form Grid -->
           <div class="form-grid">
               <div class="form-group">
                  <label>Agent 名称</label>
                  <input v-model="form.name" placeholder="例如：半导体行业分析师" />
               </div>
               <div class="form-group">
                  <label>抓取/切入角度</label>
                  <input v-model="form.angle" placeholder="例如：关注芯片制造与供应链博弈" />
               </div>
           </div>

           <div class="form-grid">
               <div class="form-group">
                   <label>关键词 (必填，用于 Google 搜索)</label>
                   <input v-model="form.keywords" placeholder="例如：芯片, 台积电 (用于搜索)" />
               </div>
               <div class="form-group">
                  <label>字数要求</label>
                   <input type="number" v-model="form.word_count" placeholder="1500" />
               </div>
           </div>
           
           <div class="form-group">
               <label>内容风格 (Style)</label>
               <input v-model="form.style" placeholder="例如：犀利批判、数据驱动、幽默风趣..." />
           </div>

           <div class="form-group">
              <label>Prompt 提示词</label>
              <textarea v-model="form.prompt" rows="4" placeholder="例如：请以钛媒体资深专家的口吻，深入分析..."></textarea>
              <span class="hint">这些指令将被注入给 AI，用于指导文章的写作风格。</span>
           </div>
        </div>
        <div class="modal-footer">
           <button class="btn-cancel" @click="showCreateModal = false">取消</button>
           <button class="btn-confirm" @click="handleCreate" :disabled="!isFormValid">确认创建</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getAgents, createAgent, deleteAgent, runAgent, updateAgent } from '../services/api'

const agents = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const runningId = ref(null)

const form = ref({
    id: null,
    name: '',
    angle: '',
    // source: '', // Removed per user request
    word_count: 1500,
    keywords: '',
    style: '',
    prompt: ''
})

const isFormValid = computed(() => {
    return form.value.name && form.value.angle && form.value.prompt && form.value.keywords
})

const fetchAgents = async () => {
    loading.value = true
    try {
        const res = await getAgents()
        agents.value = res.data || []
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const handleEdit = (agent) => {
    form.value = { ...agent }
    showCreateModal.value = true
}

const handleCreate = async () => {
    if (!isFormValid.value) return
    try {
        if (form.value.id) {
             await updateAgent(form.value)
        } else {
             await createAgent(form.value)
        }
        showCreateModal.value = false
        // Reset form
        form.value = { 
            id: null,
            name: '', angle: '', prompt: '',
            source: '', word_count: 1500, keywords: '', style: ''
        }
        fetchAgents()
    } catch (e) {
        alert((form.value.id ? "更新" : "创建") + "失败: " + e.message)
    }
    }


const handleDelete = async (id) => {
    if (!confirm("确定要删除这个 Agent 吗？")) return
    try {
        await deleteAgent(id)
        fetchAgents()
    } catch (e) {
        alert("删除失败: " + e.message)
    }
}

const handleRun = async (agent) => {
    runningId.value = agent.id
    try {
        const res = await runAgent(agent.id)
        alert(`任务完成！\n已生成文章：${res.result.topic}\n请前往「作品管理」查看。`)
        fetchAgents() // refresh last run time
    } catch (e) {
        alert("运行失败: " + (e.response?.data?.detail || e.message))
    } finally {
        runningId.value = null
    }
}

const formatTime = (ts) => {
    if (!ts) return '从未运行'
    return new Date(ts * 1000).toLocaleString()
}

onMounted(() => {
    fetchAgents()
})
</script>

<style scoped>
.agent-manager {
    padding: 32px;
    max-width: 1200px;
    margin: 0 auto;
}
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
}
.header h2 { font-size: 24px; color: #1e293b; font-weight: 700; }

.create-btn {
    background: #2563eb;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.2s;
}
.create-btn:hover { background: #1d4ed8; transform: translateY(-1px); }

.agent-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 20px;
}

.agent-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    transition: all 0.2s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.agent-card:hover {
    box-shadow: 0 10px 25px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}

.ac-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    position: relative;
}
.ac-icon {
    width: 48px; height: 48px;
    background: #eff6ff;
    color: #2563eb;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px;
}
.ac-info { flex: 1; }
.ac-name { font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }
.ac-status { font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 6px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #ccc; }
.status-dot.green { background: #10b981; }

.del-btn {
    position: absolute; right: -8px; top: -8px;
    background: transparent; border: none; color: #cbd5e1;
    cursor: pointer; font-size: 18px;
}
.del-btn:hover { color: #ef4444; }

.edit-btn {
    position: absolute; right: 24px; top: -8px;
    background: transparent; border: none; color: #cbd5e1;
    cursor: pointer; font-size: 18px;
}
.edit-btn:hover { color: #3b82f6; }

.ac-body { flex: 1; display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
.field-group label { font-size: 11px; color: #94a3b8; display: block; margin-bottom: 4px; }
.field-group .val { font-size: 13px; color: #334155; font-weight: 500; }
.field-group .val.text-blue { color: #2563eb; }
.field-group .val.prompt { 
    background: #f8fafc; padding: 8px; border-radius: 6px; color: #475569; font-size: 12px; line-height: 1.5;
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}

.ac-meta { font-size: 11px; color: #cbd5e1; margin-top: auto; padding-top: 8px; border-top: 1px dashed #f1f5f9; }

.run-btn {
    width: 100%;
    padding: 10px;
    background: #f0fdf4;
    color: #15803d;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}
.run-btn:hover { background: #dcfce7; }
.run-btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* Modal */
.modal-overlay {
    position: fixed; inset: 0; background: rgba(0,0,0,0.5);
    display: flex; align-items: center; justify-content: center;
    z-index: 100;
    backdrop-filter: blur(2px);
}
.modal {
    background: white; width: 500px; border-radius: 12px; padding: 24px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.2);
    animation: slideUp 0.3s;
}
@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

.modal-header { display: flex; justify-content: space-between; margin-bottom: 20px; }
.modal-header h3 { margin: 0; font-size: 18px; color: #1e293b; }
.close-btn { border: none; background: none; font-size: 20px; cursor: pointer; color: #94a3b8; }

/* Layout utils */
.field-row, .form-grid {
    display: flex; gap: 16px;
}
.field-group.half, .form-group.half, .form-grid .form-group {
    flex: 1;
}

.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 6px; }
.form-group input, .form-group textarea, .form-group select {
    width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; color: #1e293b;
    background: white;
}
.form-group input:focus, .form-group textarea:focus { outline: none; border-color: #3b82f6; }
.hint { font-size: 11px; color: #94a3b8; margin-top: 4px; display: block; }

.modal-footer { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
.btn-cancel { padding: 8px 16px; background: white; border: 1px solid #cbd5e1; border-radius: 6px; color: #64748b; cursor: pointer; }
.btn-confirm { padding: 8px 16px; background: #2563eb; color: white; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; }
.btn-confirm:disabled { opacity: 0.5; }

.loading, .empty-state { text-align: center; padding: 60px; color: #94a3b8; }
.empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; }
</style>
