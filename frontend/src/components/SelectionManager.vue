<template>
  <div class="selection-manager">
    <!-- Header -->
    <header class="page-header">
      <div class="header-left">
        <h2>我的选题</h2>
        <div class="status-tabs">
            <button 
                v-for="st in ['todo', 'completed', 'abandoned']" 
                :key="st" 
                class="tab-btn" 
                :class="{ active: currentStatus === st }"
                @click="currentStatus = st; currentPage = 1; fetchList()"
            >
                {{ getStatusLabel(st) }}
            </button>
        </div>
      </div>
      <div class="header-right">
         <!-- Search box if needed, simplified for now -->
      </div>
    </header>

    <!-- Content List -->
    <div class="content-table-wrapper">
        <table class="data-table">
            <thead>
                <tr>
                    <th width="50%">选题内容</th>
                    <th width="15%">来源</th>
                    <th width="15%">状态</th>
                    <th width="20%">创建时间</th>
                    <th width="100px">操作</th>
                </tr>
            </thead>
            <tbody>
                <tr v-if="loading">
                    <td colspan="5" class="loading-cell">加载中...</td>
                </tr>
                <tr v-else-if="items.length === 0">
                    <td colspan="5" class="empty-cell">
                        <div class="empty-state">
                            <span class="emoji">📌</span>
                            <p>暂无选题</p>
                        </div>
                    </td>
                </tr>
                <tr v-else v-for="item in items" :key="item.id">
                    <td>
                        <div class="topic-cell">
                            <span class="topic-text">{{ item.topic }}</span>
                        </div>
                    </td>
                    <td>
                        <span class="source-tag">{{ item.source }}</span>
                    </td>
                    <td>
                        <span class="status-tag" :class="item.status">
                            {{ getStatusLabel(item.status) }}
                        </span>
                    </td>
                    <td class="time-cell">{{ item.created_at }}</td>
                    <td>
                        <div class="actions">
                            <!-- To Do Actions -->
                            <template v-if="item.status === 'todo'">
                                <button @click="$emit('start-draft', item)" class="act-btn primary" title="极速成稿">⚡</button>
                                <button @click="handleStatusChange(item.id, 'completed')" class="act-btn success" title="标记完成">✅</button>
                                <button @click="handleStatusChange(item.id, 'abandoned')" class="act-btn warn" title="放弃">🚫</button>
                            </template>
                            
                            <!-- Abandoned Actions -->
                            <template v-if="item.status === 'abandoned'">
                                <button @click="handleStatusChange(item.id, 'todo')" class="act-btn" title="恢复为待办">🔄</button>
                            </template>

                            <button @click="handleDelete(item.id)" class="act-btn del" title="删除">🗑️</button>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Pagination -->
    <div class="pagination" v-if="total > pageSize">
        <button :disabled="currentPage === 1" @click="changePage(-1)">上一页</button>
        <span>{{ currentPage }} / {{ totalPages }}</span>
        <button :disabled="currentPage === totalPages" @click="changePage(1)">下一页</button>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { getSelections, updateSelectionStatus, deleteSelection } from '../services/api'

const emit = defineEmits(['start-draft'])

const items = ref([])
const total = ref(0)
const loading = ref(false)
const currentStatus = ref('todo')
const currentPage = ref(1)
const pageSize = 20

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const getStatusLabel = (st) => {
    const map = {todo: '待办', completed: '已完成', abandoned: '放弃'}
    return map[st] || st
}

const fetchList = async () => {
    loading.value = true
    try {
        const res = await getSelections({
            page: currentPage.value,
            page_size: pageSize,
            status: currentStatus.value
        })
        items.value = res.items
        total.value = res.total
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const changePage = (delta) => {
    currentPage.value += delta
    fetchList()
}

const handleStatusChange = async (id, newStatus) => {
    try {
        await updateSelectionStatus(id, newStatus)
        fetchList() 
    } catch (e) {
        alert("操作失败: " + e.message)
    }
}

const handleDelete = async (id) => {
    if (!confirm("确定要删除此选题吗？")) return
    try {
        await deleteSelection(id)
        if (items.value.length === 1 && currentPage.value > 1) {
            currentPage.value -= 1
        }
        fetchList() 
    } catch (e) {
        alert("删除失败: " + e.message)
    }
}

onMounted(() => {
    fetchList()
})
</script>

<style scoped>
.selection-manager { padding: 24px; height: 100%; display: flex; flex-direction: column; background: #f8fafc; }

/* Header */
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-shrink: 0; }
.header-left h2 { font-size: 20px; color: #1e293b; margin: 0 0 16px 0; font-weight: 700; }
.status-tabs { display: flex; gap: 4px; background: #e2e8f0; padding: 4px; border-radius: 8px; width: fit-content; }
.tab-btn { border: none; background: transparent; padding: 6px 16px; font-size: 13px; color: #64748b; cursor: pointer; border-radius: 6px; font-weight: 500; transition: all 0.2s; }
.tab-btn.active { background: white; color: #2563eb; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }

/* Table */
.content-table-wrapper { flex: 1; overflow: hidden; background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; display: flex; flex-direction: column; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th { background: #f8fafc; text-align: left; padding: 12px 20px; font-size: 12px; color: #64748b; font-weight: 600; border-bottom: 1px solid #f1f5f9; position: sticky; top: 0; }
.data-table td { padding: 16px 20px; border-bottom: 1px solid #f1f5f9; font-size: 13px; color: #334155; vertical-align: middle; }
.data-table tr:hover { background: #f8fafc; }

.topic-cell { font-weight: 600; color: #1e293b; font-size: 14px; }
.source-tag { background: #f1f5f9; color: #64748b; padding: 2px 8px; border-radius: 4px; font-size: 12px; }

.status-tag { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.status-tag.todo { background: #eff6ff; color: #3b82f6; }
.status-tag.completed { background: #dcfce7; color: #16a34a; }
.status-tag.abandoned { background: #fef2f2; color: #ef4444; }

.time-cell { color: #64748b; font-family: monospace; }

.actions { display: flex; gap: 8px; }
.act-btn { width: 28px; height: 28px; border: 1px solid #e2e8f0; background: white; border-radius: 6px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; font-size: 14px; }
.act-btn:hover { border-color: #cbd5e1; transform: translateY(-1px); }
.act-btn.primary { color: #2563eb; background: #eff6ff; border-color: #bfdbfe; }
.act-btn.success { color: #16a34a; background: #f0fdf4; border-color: #bbf7d0; }
.act-btn.warn { color: #ef4444; background: #fef2f2; border-color: #fecaca; }
.act-btn.del:hover { border-color: #fecaca; background: #fef2f2; }

.loading-cell, .empty-cell { text-align: center; padding: 60px !important; color: #94a3b8; }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.empty-state .emoji { font-size: 24px; grayscale: 1; opacity: 0.5; }

/* Pagination */
.pagination { display: flex; justify-content: flex-end; align-items: center; padding: 16px 24px; gap: 12px; border-top: 1px solid #f1f5f9; }
.pagination button { border: 1px solid #e2e8f0; background: white; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; color: #475569; }
.pagination button:disabled { opacity: 0.5; cursor: not-allowed; }
.pagination span { font-size: 13px; color: #64748b; }
</style>
