<template>
  <div class="customer-module">
    <div class="toolbar">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input 
          v-model="searchText" 
          class="search-input" 
          placeholder="搜索客户名称 / 行业 / 等级..." 
        />
      </div>
      <button class="add-btn" @click="openAddModal">
        <span class="plus">+</span> 新增监控对象
      </button>
    </div>

    <div class="table-container">
      <table class="c-table">
        <thead>
          <tr>
            <th width="25%">客户名称</th>
            <th width="20%">所属行业</th>
            <th width="15%">关注等级</th>
            <th width="25%">当前舆情状态</th>
            <th width="15%" style="text-align: right;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in filteredList" :key="item.name">
            <td>
              <div class="name-cell">
                <span class="name-text">{{ item.name }}</span>
              </div>
            </td>
            <td><span class="industry-badge">{{ item.industry }}</span></td>
            <td>
              <span class="level-badge" :class="getLevelClass(item.level)">
                {{ item.level }}
              </span>
            </td>
            <td>
              <slot name="status" :name="item.name">
                <span class="status-gray">等待扫描...</span>
              </slot>
            </td>
            <td style="text-align: right;">
              <button class="action-icon edit" @click="openEditModal(item)">✎</button>
              <button class="action-icon del" @click="handleDelete(item)">🗑</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredList.length === 0" class="empty-tip">
        {{ searchText ? '未找到匹配的客户' : '暂无客户数据，请点击上方新增' }}
      </div>
    </div>

    <div class="modal-mask" v-if="showModal">
      <div class="modal-box">
        <div class="modal-header">
          <h3>{{ isEditing ? '编辑客户档案' : '新增监控对象' }}</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="form-item">
            <label>客户名称 (关键词)</label>
            <input 
              v-model="form.name" 
              class="f-input" 
              placeholder="输入企业或人物全称" 
              :disabled="isEditing" 
            />
            <p class="f-tip" v-if="!isEditing">系统将以此名称作为全网舆情监控的关键词</p>
          </div>

          <div class="form-item">
            <label>所属行业</label>
            <select v-model="form.industry" class="f-select">
              <option>科技互联网</option>
              <option>汽车出行</option>
              <option>金融财经</option>
              <option>消费零售</option>
              <option>医疗健康</option>
              <option>房地产</option>
              <option>文娱传媒</option>
              <option>其他</option>
            </select>
          </div>

          <div class="form-item">
            <label>关注等级</label>
            <div class="radio-group">
              <label class="radio-label core">
                <input type="radio" v-model="form.level" value="核心"> 核心
              </label>
              <label class="radio-label imp">
                <input type="radio" v-model="form.level" value="重要"> 重要
              </label>
              <label class="radio-label normal">
                <input type="radio" v-model="form.level" value="一般"> 一般
              </label>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="m-btn cancel" @click="closeModal">取消</button>
          <button class="m-btn confirm" @click="handleSave">保存配置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'

const props = defineProps({
  list: Array // 接收父组件传来的客户列表
})

const emit = defineEmits(['save', 'delete'])

const searchText = ref('')
const showModal = ref(false)
const isEditing = ref(false)

// 表单数据
const form = reactive({
  name: '',
  industry: '科技互联网',
  level: '一般'
})

// 搜索过滤逻辑
const filteredList = computed(() => {
  if (!searchText.value) return props.list
  const key = searchText.value.toLowerCase()
  return props.list.filter(item => 
    item.name.toLowerCase().includes(key) || 
    item.industry.includes(key) ||
    item.level.includes(key)
  )
})

// 样式辅助
const getLevelClass = (level) => {
  if (level === '核心') return 'tag-core'
  if (level === '重要') return 'tag-imp'
  return 'tag-normal'
}

// === 交互逻辑 ===

const openAddModal = () => {
  isEditing.value = false
  form.name = ''
  form.industry = '科技互联网'
  form.level = '一般'
  showModal.value = true
}

const openEditModal = (item) => {
  isEditing.value = true
  // 复制数据
  form.name = item.name
  form.industry = item.industry
  form.level = item.level
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const handleSave = () => {
  if (!form.name.trim()) return alert("请输入客户名称")
  
  // 抛出事件给父组件处理
  emit('save', { 
    ...form, 
    isEdit: isEditing.value 
  })
  closeModal()
}

const handleDelete = (item) => {
  if (confirm(`确定删除“${item.name}”吗？\n删除后将停止对该客户的舆情监控。`)) {
    emit('delete', item)
  }
}
</script>

<style scoped>
/* 容器 */
.customer-module { height: 100%; display: flex; flex-direction: column; overflow: hidden; background: white; }

/* 工具栏 */
.toolbar { padding: 16px 24px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; background: #fff; }
.search-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; display: flex; align-items: center; width: 320px; transition: all 0.2s; }
.search-box:focus-within { border-color: #3b82f6; background: #fff; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.search-icon { color: #94a3b8; margin-right: 8px; font-size: 14px; }
.search-input { border: none; background: transparent; outline: none; width: 100%; font-size: 13px; color: #334155; }
.add-btn { background: #2563eb; color: white; border: none; padding: 8px 20px; border-radius: 6px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; font-size: 13px; transition: background 0.2s; }
.add-btn:hover { background: #1d4ed8; }

/* 表格 */
.table-container { flex: 1; overflow-y: auto; padding: 0 24px 24px 24px; }
.c-table { width: 100%; border-collapse: collapse; margin-top: 16px; }
.c-table th { text-align: left; padding: 12px 8px; font-size: 12px; color: #64748b; font-weight: 600; border-bottom: 1px solid #e2e8f0; }
.c-table td { padding: 16px 8px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.c-table tr:hover td { background: #f8fafc; }

/* 单元格样式 */
.name-text { font-weight: 600; color: #1e293b; font-size: 14px; }
.industry-badge { background: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 4px; font-size: 12px; }
.level-badge { padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600; color: white; }
.tag-core { background: #dc2626; }
.tag-imp { background: #ea580c; }
.tag-normal { background: #3b82f6; }

.action-icon { width: 28px; height: 28px; border-radius: 4px; border: none; cursor: pointer; margin-left: 8px; display: inline-flex; align-items: center; justify-content: center; font-size: 14px; transition: all 0.2s; }
.action-icon.edit { background: #eff6ff; color: #2563eb; }
.action-icon.edit:hover { background: #dbeafe; }
.action-icon.del { background: #fef2f2; color: #ef4444; }
.action-icon.del:hover { background: #fee2e2; }

.empty-tip { text-align: center; color: #94a3b8; padding: 60px; font-size: 14px; }

/* 弹窗 */
.modal-mask { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 999; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(2px); }
.modal-box { background: white; width: 420px; border-radius: 12px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); overflow: hidden; animation: slideIn 0.2s ease-out; }
@keyframes slideIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

.modal-header { padding: 16px 24px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
.modal-header h3 { margin: 0; font-size: 16px; color: #1e293b; }
.close-btn { background: none; border: none; font-size: 20px; color: #94a3b8; cursor: pointer; }

.modal-body { padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.form-item label { display: block; font-size: 13px; color: #64748b; margin-bottom: 8px; font-weight: 500; }
.f-input, .f-select { width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; outline: none; }
.f-input:focus, .f-select:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
.f-input:disabled { background: #f1f5f9; color: #94a3b8; cursor: not-allowed; }
.f-tip { font-size: 12px; color: #94a3b8; margin: 6px 0 0 0; }

.radio-group { display: flex; gap: 16px; }
.radio-label { font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.radio-label.core { color: #dc2626; font-weight: 500; }
.radio-label.imp { color: #ea580c; font-weight: 500; }
.radio-label.normal { color: #3b82f6; font-weight: 500; }

.modal-footer { padding: 16px 24px; background: #f8fafc; display: flex; justify-content: flex-end; gap: 12px; border-top: 1px solid #f1f5f9; }
.m-btn { padding: 8px 20px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; border: none; }
.m-btn.cancel { background: white; border: 1px solid #cbd5e1; color: #64748b; }
.m-btn.confirm { background: #2563eb; color: white; }
.m-btn.confirm:hover { background: #1d4ed8; }
</style>