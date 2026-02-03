<template>
  <div class="article-manager">
    <!-- Header -->
    <header class="page-header">
      <div class="header-left">
        <h2>我的作品</h2>
        <div class="status-tabs">
            <button 
                v-for="st in ['all', 'draft', 'published']" 
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
         <div class="search-box">
             <span class="icon">🔍</span>
             <input v-model="searchText" @keyup.enter="fetchList" placeholder="搜索标题..." />
         </div>
      </div>
    </header>

    <!-- Table -->
    <div class="content-table-wrapper">
        <table class="data-table">
            <thead>
                <tr>
                    <th width="40%">标题/选题</th>
                    <th width="15%">状态</th>
                    <th width="20%">最后更新时间</th>
                    <th width="15%">创建时间</th>
                    <th width="10%">操作</th>
                </tr>
            </thead>
            <tbody>
                <tr v-if="loading">
                    <td colspan="5" class="loading-cell">加载中...</td>
                </tr>
                <tr v-else-if="items.length === 0">
                    <td colspan="5" class="empty-cell">
                        <div class="empty-state">
                            <span class="emoji">📝</span>
                            <p>暂无相关作品</p>
                        </div>
                    </td>
                </tr>
                <tr v-else v-for="item in items" :key="item.id">
                    <td>
                        <div class="title-cell">
                            <div class="cover-thumb" v-if="item.cover_url">
                                <img :src="item.cover_url" />
                            </div>
                            <div class="title-info">
                                <span class="main-title">{{ item.title || '无标题' }}</span>
                                <span class="sub-topic" v-if="item.topic">选题: {{ item.topic }}</span>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="status-tag" :class="item.status">
                            {{ item.status_label }}
                        </span>
                    </td>
                    <td class="time-cell">{{ item.updated_at }}</td>
                    <td class="time-cell">{{ item.created_at }}</td>
                    <td>
                        <div class="actions">
                            <button @click="$emit('edit', item.id)" class="act-btn edit" title="编辑">✏️</button>
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
import { ref, onMounted, computed } from 'vue'
import { getArticles, deleteArticle } from '../services/api'

const emit = defineEmits(['edit'])

const items = ref([])
const total = ref(0)
const loading = ref(false)
const searchText = ref('')
const currentStatus = ref('all')
const currentPage = ref(1)
const pageSize = 10

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const getStatusLabel = (st) => {
    const map = {all: '全部', draft: '草稿箱', published: '已发布'}
    return map[st] || st
}

const fetchList = async () => {
    loading.value = true
    try {
        const res = await getArticles({
            page: currentPage.value,
            page_size: pageSize,
            status: currentStatus.value === 'all' ? null : currentStatus.value,
            search: searchText.value
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

const handleDelete = async (id) => {
    if (!confirm("确定要删除此文章吗？此操作不可恢复。")) return
    try {
        await deleteArticle(id)
        fetchList() // refresh
    } catch (e) {
        alert("删除失败: " + e.message)
    }
}

onMounted(() => {
    fetchList()
})
</script>

<style scoped>
.article-manager { padding: 24px; height: 100%; display: flex; flex-direction: column; background: #f8fafc; }

/* Header */
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-shrink: 0; }
.header-left h2 { font-size: 20px; color: #1e293b; margin: 0 0 16px 0; font-weight: 700; }
.status-tabs { display: flex; gap: 4px; background: #e2e8f0; padding: 4px; border-radius: 8px; width: fit-content; }
.tab-btn { border: none; background: transparent; padding: 6px 16px; font-size: 13px; color: #64748b; cursor: pointer; border-radius: 6px; font-weight: 500; transition: all 0.2s; }
.tab-btn.active { background: white; color: #2563eb; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }

.search-box { display: flex; align-items: center; background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 12px; width: 240px; }
.search-box .icon { font-size: 14px; margin-right: 8px; opacity: 0.5; }
.search-box input { border: none; outline: none; width: 100%; font-size: 13px; color: #334155; }

/* Table */
.content-table-wrapper { flex: 1; overflow: hidden; background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; display: flex; flex-direction: column; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th { background: #f8fafc; text-align: left; padding: 12px 20px; font-size: 12px; color: #64748b; font-weight: 600; border-bottom: 1px solid #f1f5f9; position: sticky; top: 0; }
.data-table td { padding: 16px 20px; border-bottom: 1px solid #f1f5f9; font-size: 13px; color: #334155; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover { background: #f8fafc; }

.title-cell { display: flex; align-items: center; gap: 12px; }
.cover-thumb { width: 48px; height: 32px; border-radius: 4px; overflow: hidden; background: #f1f5f9; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
.cover-thumb img { width: 100%; height: 100%; object-fit: cover; }
.title-info { display: flex; flex-direction: column; gap: 2px; }
.main-title { font-weight: 600; color: #1e293b; font-size: 14px; }
.sub-topic { font-size: 11px; color: #94a3b8; }

.status-tag { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.status-tag.draft { background: #f1f5f9; color: #64748b; }
.status-tag.published { background: #dcfce7; color: #16a34a; }

.time-cell { color: #64748b; font-family: monospace; }

.actions { display: flex; gap: 8px; }
.act-btn { width: 28px; height: 28px; border: 1px solid #e2e8f0; background: white; border-radius: 6px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; font-size: 14px; }
.act-btn:hover { border-color: #cbd5e1; transform: translateY(-1px); }
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
