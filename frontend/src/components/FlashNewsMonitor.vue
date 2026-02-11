<template>
  <div class="flash-monitor">
    <!-- Header / Toolbar -->
    <div class="header-bar">
      <div class="tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.key"
          :class="['tab-btn', { active: currentStatus === tab.key }]"
          @click="changeTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="actions">
        <button class="btn-primary" @click="doFetch" :disabled="loading">
          <span v-if="loading">⏳ 抓取中...</span>
          <span v-else>🔄 立即抓取({{ sourceLabel(currentSource) }})</span>
        </button>
      </div>
    </div>

    <div class="source-bar">
      <div class="source-tabs">
        <button
          v-for="src in sources"
          :key="src.key"
          :class="['source-btn', { active: currentSource === src.key }]"
          @click="changeSource(src.key)"
        >
          {{ src.label }}
        </button>
      </div>
    </div>

    <!-- Main Split View -->
    <div class="main-content" v-loading="loading">
      <div class="panel-title row-head">
        <span>原始快报列表</span>
        <span>钛媒体AI改写列表</span>
      </div>
      <div v-if="items.length === 0" class="empty-state">
        暂无快报数据 (点击抓取试试)
      </div>
      <div v-else class="rows">
        <div v-for="item in items" :key="item.id" class="row">
          <!-- Left -->
          <div class="cell left-card">
            <div class="card-header">
              <span class="time">{{ item.time_display }}</span>
            </div>
            <div class="card-title" :class="{ important: item.is_important }">
              {{ item.title || '无标题' }}
            </div>
            <div class="card-full">{{ item.raw_content || '' }}</div>
            <a v-if="item.url" :href="item.url" target="_blank" class="link">查看源文 ↗</a>
          </div>
          <!-- Right -->
          <div class="cell right-card">
            <div class="card-header">
              <span class="time">{{ item.time_display }}</span>
            </div>
            <input
              v-model="item.rewrite_title"
              class="rewrite-title"
              placeholder="快报标题"
            />
            <textarea
              v-model="item.rewrite_content"
              class="rewrite-editor"
              placeholder="AI生成中..."
              rows="5"
            ></textarea>
            <div class="action-footer">
              <button class="btn-danger" @click="updateStatus(item, 'discarded')">放弃</button>
              <button class="btn-success" @click="updateStatus(item, 'published')">发布快报</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getFlashList, updateFlash, triggerFlashFetch, backfillFlashRewrite } from '../services/api'
// Removed ElMessage import as it is not installed. Using alerts/logs instead.

const tabs = [
  { key: 'draft', label: '草稿 / AI待审' },
  { key: 'published', label: '已发布' },
  { key: 'discarded', label: '已放弃' },
  { key: 'all', label: '全部' }
]

const currentStatus = ref('draft')
const items = ref([])
const loading = ref(false)
const backfilling = ref(false)
const sources = [
  { key: 'cls', label: '财联社' },
  { key: 'google', label: 'Google 快讯' },
  { key: 'all', label: '全部' }
]
const currentSource = ref('cls')

const sourceLabel = (key) => {
  const found = sources.find(s => s.key === key)
  return found ? found.label : key
}

const loadData = async () => {
    loading.value = true
    try {
        const res = await getFlashList(currentStatus.value, currentSource.value)
        items.value = (res || []).map(i => ({
          ...i,
          rewrite_title: i.rewrite_title || i.title || ''
        }))
        // 自动补写改写内容（仅草稿且为空时触发一次）
        if (!backfilling.value && currentStatus.value === 'draft') {
            const need = items.value.some(i => !i.rewrite_content)
            if (need) {
                backfilling.value = true
                await backfillFlashRewrite(10)
                await loadData()
                backfilling.value = false
            }
        }
    } catch (e) {
        console.error("Load failed", e)
    } finally {
        loading.value = false
    }
}

const doFetch = async () => {
    loading.value = true
    try {
        await triggerFlashFetch(currentSource.value)
        // Force refresh
        await loadData()
    } catch (e) {
        alert("Fetch failed")
    } finally {
        loading.value = false
    }
}

const changeTab = (tab) => {
    currentStatus.value = tab
    loadData()
}

const changeSource = (src) => {
    currentSource.value = src
    loadData()
}


const updateStatus = async (item, newStatus) => {
    if (!item) return
    const id = item.id
    try {
        await updateFlash(id, newStatus, item.rewrite_content, item.rewrite_title)
        // Remove from list if status filter is applied and consistent
        // e.g. if we are in 'draft' and move to 'published', it should disappear
        if (currentStatus.value !== 'all' && currentStatus.value !== newStatus) {
            items.value = items.value.filter(i => i.id !== id)
        }
    } catch (e) {
        alert("Update failed")
    }
}

onMounted(() => {
    loadData()
})

//////////////////////////////////////////
// Helper Shim for v-loading if no element-plus
const vLoading = {
  mounted(el, binding) {
    if (binding.value) el.style.opacity = 0.5
    else el.style.opacity = 1
  },
  updated(el, binding) {
    if (binding.value) el.style.opacity = 0.5
    else el.style.opacity = 1
  }
}
</script>

<style scoped>
.flash-monitor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f3f4f6;
}

.header-bar {
  padding: 16px 24px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

.source-bar {
  padding: 8px 24px 0 24px;
  background: #f3f4f6;
}

.source-tabs {
  display: inline-flex;
  gap: 6px;
  background: #ffffff;
  padding: 4px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
}

.source-btn {
  padding: 6px 12px;
  border: none;
  background: transparent;
  border-radius: 999px;
  font-size: 12px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.source-btn.active {
  background: #0f172a;
  color: #ffffff;
  font-weight: 500;
}

.tabs {
  display: flex;
  gap: 6px;
  background: #f1f5f9;
  padding: 4px;
  border-radius: 999px;
}

.tab-btn {
  padding: 6px 14px;
  border: none;
  background: transparent;
  border-radius: 999px;
  font-size: 13px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: white;
  color: #0f172a;
  font-weight: 500;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  overflow: hidden;
}

.rows {
  flex: 1;
  overflow-y: auto;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 6px rgba(15,23,42,0.05);
}

.row-head {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.rows .row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 16px 18px;
  border-bottom: 1px solid #f1f5f9;
}

.cell {
  display: flex;
  flex-direction: column;
}

.rows .row:hover {
  background: #f8fafc;
}


.card-header {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 8px;
  align-items: center;
}

.card-title {
  font-weight: 600;
  font-size: 15px;
  color: #0f172a;
  margin-bottom: 6px;
  line-height: 1.5;
}

.card-title.important {
  color: #dc2626;
}

.card-full {
  font-size: 13px;
  color: #334155;
  line-height: 1.7;
  white-space: pre-wrap;
}

.panel-title {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  color: #0f172a;
  border-bottom: 1px solid #e5e7eb;
  background: #f8fafc;
  border-radius: 12px;
}

.rewrite-title {
  width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 14px;
  font-weight: 600;
  margin-top: 6px;
  color: #0f172a;
  box-sizing: border-box;
}

.rewrite-editor {
  width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  line-height: 1.6;
  color: #111827;
  margin-top: 8px;
  resize: vertical;
  box-sizing: border-box;
  background: #f8fafc;
}

.action-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

.btn-primary, .btn-success, .btn-danger, .btn-save {
  padding: 8px 14px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 13px;
}

.btn-primary { background: #0f172a; color: white; }
.btn-success { background: #10b981; color: white; }
.btn-danger { background: white; color: #ef4444; border: 1px solid #fecaca; }
.btn-save { background: white; color: #0ea5e9; border: 1px solid #bae6fd; }

.btn-primary:hover { background: #1e293b; }
.btn-success:hover { background: #059669; }
.btn-danger:hover { background: #fef2f2; }

.empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: #94a3b8;
    font-size: 14px;
}
</style>
