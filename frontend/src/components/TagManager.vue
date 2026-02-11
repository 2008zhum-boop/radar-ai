<template>
  <div class="tag-manager">
    <div class="sidebar">
      <div class="sb-title">标签类型</div>
      <div 
        class="sb-item" 
        :class="{ active: currentType === 'ALL' }" 
        @click="currentType = 'ALL'"
      >
        <span>📚</span> 全部标签
      </div>
      <div 
        class="sb-item" 
        :class="{ active: currentType === t.key }"
        v-for="t in tagTypes" 
        :key="t.key"
        @click="currentType = t.key"
      >
        <span>{{ t.icon }}</span> {{ t.label }}
      </div>
    </div>

    <div class="main-content">
      <div class="top-bar">
        <h2 class="page-title">{{ getTypeName(currentType) }}管理</h2>
        <div class="actions">
          <input v-model="searchText" placeholder="搜索标签..." class="search-input" />
          <button class="btn btn-primary" @click="openCreateModal">+ 新建标签</button>
        </div>
      </div>

       <!-- Merge Action Bar -->
       <div v-if="selectedIds.length > 1" class="merge-bar">
          <span class="mb-text">已选择 {{ selectedIds.length }} 个标签</span>
          <button class="btn btn-warning" @click="prepareMerge">合并选中的标签</button>
       </div>

      <!-- Category Hierarchical View -->
      <div v-if="currentType === 'CATEGORY'" class="category-hierarchy">
        <!-- Level 1 Tags -->
        <div class="level-section">
          <div class="level-header">
            <h3>一级标签 (行业/领域分类)</h3>
            <span class="count-badge">{{ level1Tags.length }} 个</span>
          </div>
          <div class="tag-list">
            <div v-for="tag in level1Tags" :key="tag.id" class="tag-row">
              <div class="tr-checkbox">
                <input type="checkbox" :value="tag.id" v-model="selectedIds" />
              </div>
              <div class="tr-main">
                <span class="tag-name-large">{{ tag.name }}</span>
                <span class="tag-type-badge">一级</span>
              </div>
              <div class="tr-meta">
                <span class="alias-text" v-if="tag.alias">{{ tag.alias }}</span>
                <span class="heat-badge">🔥 {{ tag.count }}</span>
              </div>
              <div class="tr-actions">
                <button class="icon-btn edit-btn" @click.stop="openEditModal(tag)">✎</button>
                <button class="icon-btn del-btn" @click.stop="confirmDelete(tag)">🗑</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Level 2 Tags -->
        <div class="level-section">
          <div class="level-header">
            <h3>二级标签 (细分标签)</h3>
            <span class="count-badge">{{ level2Tags.length }} 个</span>
          </div>
          <div class="tag-list">
            <div v-for="tag in level2Tags" :key="tag.id" class="tag-row level-2">
              <div class="tr-checkbox">
                <input type="checkbox" :value="tag.id" v-model="selectedIds" />
              </div>
              <div class="tr-main">
                <span class="tag-name-large">{{ tag.name }}</span>
                <span class="tag-type-badge secondary">二级</span>
              </div>
              <div class="tr-parent">
                <span class="parent-label">隶属于:</span>
                <span class="parent-names">{{ getParentNames(tag) }}</span>
              </div>
              <div class="tr-meta">
                <span class="alias-text" v-if="tag.alias">{{ tag.alias }}</span>
                <span class="heat-badge">🔥 {{ tag.count }}</span>
              </div>
              <div class="tr-actions">
                <button class="icon-btn edit-btn" @click.stop="openEditModal(tag)">✎</button>
                <button class="icon-btn del-btn" @click.stop="confirmDelete(tag)">🗑</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Grid View for Other Types -->
      <div v-else class="tag-grid">
         <div v-for="tag in filteredTags" :key="tag.id" class="tag-card" :class="{ selected: selectedIds.includes(tag.id) }">
            <div class="tc-header">
               <input type="checkbox" :value="tag.id" v-model="selectedIds" />
               <span class="tag-name">{{ tag.name }}</span>
               <span class="tag-type-badge">{{ getBadge(tag.type) }}</span>
            </div>
            <div class="tc-parents" v-if="tag.parent_ids && tag.parent_ids.length">
               <span style="color:#64748b;font-size:12px;margin-right:4px;">📂</span> {{ getParentNames(tag) }}
            </div>
            <div class="tc-alias" v-if="tag.alias">别名: {{ tag.alias }}</div>
            <div class="tc-meta">
               <span>🔥 {{ tag.count }}次引用</span>
               <div class="card-actions">
                  <button class="icon-btn edit-btn" @click.stop="openEditModal(tag)">✎</button>
                  <button class="icon-btn del-btn" @click.stop="confirmDelete(tag)">🗑</button>
               </div>
            </div>
         </div>
      </div>
    </div>
    
    <!-- Add Modal -->
    <div v-if="showAddModal" class="modal-overlay">
       <div class="modal">
          <h3>{{ newTag.id ? '编辑标签' : '新建标签' }}</h3>
          <div class="form-group">
             <label>名称</label>
             <input v-model="newTag.name" placeholder="请输入标签名" />
          </div>
          <div class="form-group">
            <label>类型</label>
            <select v-model="newTag.tag_type">
               <option v-for="t in tagTypes" :key="t.key" :value="t.key">{{ t.label }}</option>
            </select>
          </div>
          
          <!-- Parent Selection (Multi) -->
          <div class="form-group">
             <label>父级标签 (可选，不选则为一级标签)</label>
             <div class="multi-select-box">
                <div v-for="p in parentOptions" :key="p.id" class="ms-item">
                   <label>
                      <input type="checkbox" :value="p.id" v-model="newTag.parent_ids" />
                      {{ p.name }} <span style="font-size:10px;color:#94a3b8">({{ getBadge(p.type) }})</span>
                   </label>
                </div>
             </div>
          </div>
          <div class="form-group">
             <label>别名 (选填)</label>
             <input v-model="newTag.alias" placeholder="用逗号分隔，如: 雷总,雷布斯" />
          </div>
          <div class="modal-footer">
             <button @click="showAddModal = false">取消</button>
             <button class="primary" @click="submitAdd">确定</button>
          </div>
       </div>
    </div>

    <!-- Merge Modal -->
    <div v-if="showMergeModal" class="modal-overlay">
       <div class="modal">
          <h3>合并标签</h3>
          <p>您选择了 {{ selectedIds.length }} 个标签，请选择一个作为<b>主标签</b>保留：</p>
          <div class="radio-group">
             <div v-for="tag in selectedTagsObj" :key="tag.id" class="radio-item">
                <input type="radio" :value="tag.id" v-model="mergeTargetId" />
                <label>{{ tag.name }} (🔥{{ tag.count }})</label>
             </div>
          </div>
          <p class="warning-text">⚠️ 注意：未被选中的标签将被删除，其关联数据将转移到主标签下。</p>
          <div class="modal-footer">
             <button @click="showMergeModal = false">取消</button>
             <button class="primary" @click="submitMerge">确认合并</button>
          </div>
       </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getTags, createTag, mergeTags, deleteTag, updateTag } from '../services/api'

// Constants
const tagTypes = [
  { key: 'CATEGORY', label: '分类', icon: '📂' },
  { key: 'ENTITY', label: '实体', icon: '🏢' },
  { key: 'SENTIMENT', label: '情绪', icon: '🎭' },
  { key: 'EVENT', label: '事件', icon: '📢' },
  { key: 'QUALITY', label: '质量', icon: '⭐' }
]

// State
const currentType = ref('ALL')
const searchText = ref('')
const tags = ref([])
const parentCandidateTags = ref([]) // 所有可能的父级标签（即一级标签）
const selectedIds = ref([])
const showAddModal = ref(false)
const showMergeModal = ref(false)
const mergeTargetId = ref(null)

const newTag = ref({ name: '', tag_type: 'ENTITY', alias: '', parent_ids: [] })

// Computed
const filteredTags = computed(() => {
  let list = tags.value
  if (searchText.value) {
     list = list.filter(t => t.name.toLowerCase().includes(searchText.value.toLowerCase()) || 
                             (t.alias && t.alias.includes(searchText.value)))
  }
  return list
})

const parentOptions = computed(() => {
    // 只有“分类”类型的标签可以作为父级
    // 这样情绪、事件等标签就不会出现在父级列表中
    return parentCandidateTags.value
})

const selectedTagsObj = computed(() => {
   return tags.value.filter(t => selectedIds.value.includes(t.id))
})

// For CATEGORY type: Split into Level 1 and Level 2
const level1Tags = computed(() => {
   if (currentType.value !== 'CATEGORY') return []
   return filteredTags.value.filter(t => !t.parent_ids || t.parent_ids.length === 0)
})

const level2Tags = computed(() => {
   if (currentType.value !== 'CATEGORY') return []
   return filteredTags.value.filter(t => t.parent_ids && t.parent_ids.length > 0)
})

const getTypeName = (key) => {
   if(key === 'ALL') return '全部标签'
   const t = tagTypes.find(x => x.key === key)
   return t ? t.label : key
}

const getBadge = (type) => {
    const t = tagTypes.find(x => x.key === type)
    return t ? t.label : type
}

const getParentNames = (tag) => {
    if (!tag.parent_ids || tag.parent_ids.length === 0) return ''
    const names = tag.parent_ids.map(pid => {
        // Try to find in candidates first
        let p = parentCandidateTags.value.find(t => t.id === pid)
        if (!p) {
             // If not in candidates (e.g. maybe parent is not CATEGORY?), try current list
             p = tags.value.find(t => t.id === pid)
        }
        return p ? p.name : 'Unknown'
    })
    return names.join(', ')
}

// Methods
const loadTags = async () => {
   selectedIds.value = []
   const res = await getTags(currentType.value)
   tags.value = res.data || []
}

// Load all potential parents (Only CATEGORY)
const loadParentCandidates = async () => {
    const res = await getTags('CATEGORY') 
    parentCandidateTags.value = res.data || []
}

watch(currentType, loadTags)

const openCreateModal = () => {
    newTag.value = { name: '', tag_type: 'ENTITY', alias: '', parent_ids: [] }
    showAddModal.value = true
}

const submitAdd = async () => {
    if(!newTag.value.name) {
        alert("请输入标签名称")
        return
    }

    // Logic simplified: we just take parent_ids as is.
    // If empty -> Level 1. If not empty -> Level 2.
    const payload = { ...newTag.value }

    try {
        let res;
        if (payload.id) {
             res = await updateTag(payload)
        } else {
             res = await createTag(payload)
        }
        
        if(res.status === 'success') {
           showAddModal.value = false
           // Reset form
           newTag.value = { name: '', tag_type: 'ENTITY', alias: '', parent_ids: [] }
           loadTags()
           loadParentCandidates() // Refresh parents too in case a new level 1 was created
        } else {
           alert(res.msg || "保存失败")
        }
    } catch (e) {
        alert("保存异常: " + e.message)
    }
}

const openEditModal = (tag) => {
    const pIds = tag.parent_ids || []
    
    // Ensure parent_ids are integers
    const safePIds = pIds.map(id => parseInt(id))
    
    newTag.value = {
        id: tag.id,
        name: tag.name,
        tag_type: tag.type,
        alias: tag.alias || '',
        parent_ids: safePIds
    }
    showAddModal.value = true
}

const confirmDelete = async (tag) => {
    if(confirm(`确定删除标签"${tag.name}"吗？此操作不可恢复。`)) {
        await deleteTag(tag.id)
        loadTags()
    }
}

const prepareMerge = () => {
    mergeTargetId.value = selectedIds.value[0]
    showMergeModal.value = true
}

const submitMerge = async () => {
    if(!mergeTargetId.value) return
    
    const targetId = mergeTargetId.value
    const sourceIds = selectedIds.value.filter(id => id !== targetId)
    
    const res = await mergeTags(targetId, sourceIds)
    if(res.status === 'success') {
        alert("合并成功")
        showMergeModal.value = false
        loadTags()
    } else {
        alert(res.msg)
    }
}

// Init
onMounted(() => {
    loadTags()
    loadParentCandidates()
})
</script>

<style scoped>
.tag-manager { display: flex; height: 100vh; background: #f8fafc; font-family: 'Inter', sans-serif; }

/* Sidebar */
.sidebar { width: 220px; background: white; border-right: 1px solid #e2e8f0; padding: 20px; display: flex; flex-direction: column; gap: 8px; }
.sb-title { font-size: 12px; color: #64748b; font-weight: 700; margin-bottom: 12px; text-transform: uppercase; }
.sb-item { padding: 10px 14px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; gap: 10px; color: #475569; font-size: 14px; font-weight: 500; }
.sb-item:hover { background: #f1f5f9; }
.sb-item.active { background: #eff6ff; color: #2563eb; font-weight: 600; }

/* Main */
.main-content { flex: 1; padding: 24px; overflow-y: auto; }
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: #0f172a; margin: 0; }
.actions { display: flex; gap: 12px; }
.search-input { padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; width: 200px; font-size: 14px; outline: none; }
.btn { padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: white; }
.btn-primary:hover { background: #1d4ed8; }
.btn-warning { background: #f59e0b; color: white; }

/* Merge Bar */
.merge-bar { background: #fffbeb; border: 1px solid #fcd34d; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
.mb-text { color: #92400e; font-weight: 600; font-size: 14px; }

/* Tag Grid */
.tag-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.tag-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; cursor: pointer; transition: all 0.2s; position: relative; }
.tag-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
.tag-card.selected { border-color: #2563eb; background: #eff6ff; }

.tc-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.tag-name { font-weight: 600; color: #0f172a; font-size: 15px; }
.tag-type-badge { font-size: 10px; background: #f1f5f9; color: #64748b; padding: 2px 6px; border-radius: 4px; margin-left: auto; }
.tc-alias { font-size: 12px; color: #64748b; margin-bottom: 12px; }
.tc-parents { font-size: 12px; color: #475569; margin-bottom: 8px; background: #f8fafc; padding: 4px 8px; border-radius: 4px; display: inline-block; }
.tc-meta { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #94a3b8; }
.card-actions { display: flex; gap: 8px; }
.icon-btn { background: none; border: none; cursor: pointer; font-size: 14px; opacity: 0.5; transition: opacity 0.2s; padding: 2px; }
.icon-btn:hover { opacity: 1; }
.edit-btn:hover { color: #2563eb; }
.del-btn:hover { color: #ef4444; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal { background: white; width: 400px; padding: 24px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
.modal h3 { margin-top: 0; margin-bottom: 20px; font-size: 18px; color: #0f172a; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 6px; }
.form-group input, .form-group select { width: 100%; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; box-sizing: border-box; } /* box-sizing key */
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
.modal-footer button { padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; border: 1px solid #cbd5e1; background: white; color: #475569; }
.modal-footer button.primary { background: #2563eb; color: white; border: none; }

.radio-group { display: flex; flex-direction: column; gap: 10px; max-height: 200px; overflow-y: auto; margin-bottom: 16px; border: 1px solid #f1f5f9; padding: 10px; border-radius: 6px; }
.radio-item { display: flex; align-items: center; gap: 10px; font-size: 14px; }
.radio-inline { display: flex; align-items: center; font-size: 14px; }
.radio-inline input { width: auto; margin-right: 6px; }

.multi-select-box { border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px; max-height: 150px; overflow-y: auto; background: #fafafa; }
.ms-item { margin-bottom: 6px; font-size: 13px; color: #334155; }
.ms-item label { display: flex; align-items: center; cursor: pointer; font-weight: normal; margin: 0; }
.ms-item input { width: auto; margin-right: 8px; }
.warning-text { font-size: 12px; color: #ef4444; margin-top: 10px; }

/* Category Hierarchy Styles */
.category-hierarchy { display: flex; flex-direction: column; gap: 32px; }

.level-section { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }

.level-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid #f1f5f9; }
.level-header h3 { margin: 0; font-size: 18px; font-weight: 700; color: #0f172a; }
.count-badge { background: #eff6ff; color: #2563eb; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: 600; }

.tag-list { display: flex; flex-direction: column; gap: 8px; }

.tag-row { display: flex; align-items: center; gap: 16px; padding: 12px 16px; background: #f8fafc; border-radius: 8px; transition: all 0.2s; border: 1px solid transparent; }
.tag-row:hover { background: #eff6ff; border-color: #bfdbfe; }
.tag-row.level-2 { background: #fefce8; }
.tag-row.level-2:hover { background: #fef3c7; border-color: #fde047; }

.tr-checkbox { display: flex; align-items: center; }
.tr-checkbox input[type="checkbox"] { width: 16px; height: 16px; cursor: pointer; }

.tr-main { flex: 0 0 280px; display: flex; align-items: center; gap: 10px; }
.tag-name-large { font-size: 15px; font-weight: 600; color: #0f172a; }
.tag-type-badge.secondary { background: #fef3c7; color: #92400e; }

.tr-parent { flex: 0 0 220px; display: flex; align-items: center; gap: 8px; font-size: 13px; }
.parent-label { color: #64748b; font-weight: 500; }
.parent-names { color: #2563eb; font-weight: 600; background: #eff6ff; padding: 2px 8px; border-radius: 4px; }

.tr-meta { flex: 1; display: flex; align-items: center; gap: 16px; font-size: 13px; }
.alias-text { color: #64748b; font-style: italic; }
.heat-badge { background: #fff7ed; color: #ea580c; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; }

.tr-actions { display: flex; gap: 8px; }
</style>
