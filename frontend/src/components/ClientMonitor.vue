<template>
  <div class="client-manager">
    <div class="cms-header">
      <div class="header-left">
        <h2>🛡️ 客户监控配置 (CMS)</h2>
        <p>配置品牌词、排除词及高级语义关联规则。</p>
      </div>
      <button class="add-btn" @click="openEditModal({})">+ 新增监控客户</button>
    </div>

    <div class="client-grid">
      <div v-for="client in clients" :key="client.client_id" class="client-card">
        <div class="card-top">
          <h3>{{ client.name }}</h3>
          <span class="id-tag">{{ client.client_id }}</span>
        </div>
        
        <div class="config-summary">
          <div class="tag-group">
            <span class="label">✅ 品牌词:</span>
            <div class="tags">
              <span v-for="w in client.config.brand_keywords" :key="w" class="tag brand">{{ w }}</span>
            </div>
          </div>
          
          <div class="tag-group" v-if="client.config.exclude_keywords.length">
            <span class="label">🚫 排除词:</span>
            <div class="tags">
              <span v-for="w in client.config.exclude_keywords" :key="w" class="tag exclude">{{ w }}</span>
            </div>
          </div>

          <div class="rule-group" v-if="client.config.advanced_rules.length">
            <span class="label">⚡ 高级规则 ({{ client.config.advanced_rules.length }})</span>
          </div>
        </div>

        <button class="edit-btn" @click="openEditModal(client)">⚙️ 编辑配置</button>
      </div>
    </div>

    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-content">
        <h3>{{ isEditing ? '编辑配置' : '新增客户' }}</h3>
        
        <div class="form-section">
          <label>客户名称</label>
          <input v-model="form.name" placeholder="如：星云科技" :disabled="isEditing" class="main-input" />
        </div>

        <div class="form-row">
          <div class="col">
            <label>✅ 品牌关键词 (回车添加)</label>
            <div class="tag-input-box">
              <span v-for="(tag, i) in form.brand_keywords" :key="i" class="tag brand">
                {{ tag }} <i @click="removeTag('brand', i)">×</i>
              </span>
              <input v-model="tempBrand" @keyup.enter="addTag('brand')" placeholder="输入后回车..." />
            </div>
          </div>
          <div class="col">
            <label>🚫 排除关键词 (优先级最高)</label>
            <div class="tag-input-box">
              <span v-for="(tag, i) in form.exclude_keywords" :key="i" class="tag exclude">
                {{ tag }} <i @click="removeTag('exclude', i)">×</i>
              </span>
              <input v-model="tempExclude" @keyup.enter="addTag('exclude')" placeholder="输入后回车..." />
            </div>
          </div>
        </div>

        <div class="advanced-section">
          <div class="section-title">
            <span>⚡ 高级语义规则 (Context Rules)</span>
            <button class="small-btn" @click="addRule">+ 添加规则</button>
          </div>
          
          <div class="rules-list">
            <div v-for="(rule, idx) in form.advanced_rules" :key="idx" class="rule-item">
              <div class="rule-header">
                <input v-model="rule.rule_name" placeholder="规则名 (如:高管负面)" class="rule-name-input"/>
                <button class="del-rule" @click="removeRule(idx)">删除</button>
              </div>
              <div class="rule-body">
                <div class="rule-row">
                  <span>包含:</span>
                  <input v-model="rule._must_str" placeholder="张三,CEO (逗号隔开)" />
                </div>
                <div class="rule-row">
                  <span>附近有:</span>
                  <input v-model="rule._near_str" placeholder="被抓,造假 (逗号隔开)" />
                </div>
                <div class="rule-row">
                  <span>距离 &lt;</span>
                  <input type="number" v-model="rule.distance" class="dist-input" />
                  <span>字</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button class="cancel-btn" @click="showModal = false">取消</button>
          <button class="save-btn" @click="saveConfig">💾 保存配置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { getClients, saveClientConfig } from '../services/api'

const clients = ref([])
const showModal = ref(false)
const isEditing = ref(false)

// 表单数据
const form = reactive({
  name: '',
  brand_keywords: [],
  exclude_keywords: [],
  advanced_rules: []
})

const tempBrand = ref('')
const tempExclude = ref('')

// 加载数据
const loadData = async () => {
  clients.value = await getClients()
}

onMounted(loadData)

// 打开弹窗
const openEditModal = (client) => {
  if (client.client_id) {
    isEditing.value = true
    form.name = client.name
    form.brand_keywords = [...client.config.brand_keywords]
    form.exclude_keywords = [...client.config.exclude_keywords]
    // 处理高级规则，增加临时显示字段
    form.advanced_rules = client.config.advanced_rules.map(r => ({
      ...r,
      _must_str: r.must_contain.join(','),
      _near_str: r.nearby_words.join(',')
    }))
  } else {
    isEditing.value = false
    form.name = ''
    form.brand_keywords = []
    form.exclude_keywords = []
    form.advanced_rules = []
  }
  showModal.value = true
}

// 标签操作
const addTag = (type) => {
  if (type === 'brand' && tempBrand.value) {
    form.brand_keywords.push(tempBrand.value)
    tempBrand.value = ''
  }
  if (type === 'exclude' && tempExclude.value) {
    form.exclude_keywords.push(tempExclude.value)
    tempExclude.value = ''
  }
}
const removeTag = (type, index) => {
  if (type === 'brand') form.brand_keywords.splice(index, 1)
  if (type === 'exclude') form.exclude_keywords.splice(index, 1)
}

// 规则操作
const addRule = () => {
  form.advanced_rules.push({
    rule_name: '新规则',
    _must_str: '',
    _near_str: '',
    distance: 50
  })
}
const removeRule = (idx) => {
  form.advanced_rules.splice(idx, 1)
}

// 保存
const saveConfig = async () => {
  if (!form.name) return alert('请输入客户名称')
  
  // 格式化规则数据
  const formattedRules = form.advanced_rules.map(r => ({
    rule_name: r.rule_name,
    must_contain: r._must_str.split(',').filter(s=>s),
    nearby_words: r._near_str.split(',').filter(s=>s),
    distance: Number(r.distance)
  }))

  await saveClientConfig({
    name: form.name,
    brand_keywords: form.brand_keywords,
    exclude_keywords: form.exclude_keywords,
    advanced_rules: formattedRules
  })
  
  showModal.value = false
  await loadData()
}
</script>

<style scoped>
.client-manager { padding: 20px; background: #f8fafc; min-height: 100vh; }
.cms-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.add-btn { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; }

.client-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.client-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.card-top { display: flex; justify-content: space-between; margin-bottom: 12px; }
.id-tag { font-size: 11px; color: #94a3b8; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }
.tag-group { margin-bottom: 8px; }
.label { font-size: 12px; color: #64748b; display: block; margin-bottom: 4px; }
.tags { display: flex; flex-wrap: wrap; gap: 4px; }
.tag { font-size: 11px; padding: 2px 6px; border-radius: 4px; }
.tag.brand { background: #eff6ff; color: #2563eb; }
.tag.exclude { background: #fef2f2; color: #ef4444; }

.edit-btn { width: 100%; margin-top: 16px; padding: 8px; background: white; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; color: #475569; }
.edit-btn:hover { background: #f8fafc; }

/* 弹窗样式 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-content { background: white; padding: 24px; border-radius: 12px; width: 600px; max-height: 90vh; overflow-y: auto; }
.main-input { width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; margin-top: 6px; }

.form-row { display: flex; gap: 16px; margin-top: 16px; }
.col { flex: 1; }
.tag-input-box { border: 1px solid #cbd5e1; padding: 8px; border-radius: 6px; display: flex; flex-wrap: wrap; gap: 4px; background: white; margin-top: 6px; }
.tag-input-box input { border: none; outline: none; flex: 1; min-width: 60px; }
.tag i { margin-left: 4px; cursor: pointer; opacity: 0.6; }

.advanced-section { margin-top: 24px; background: #f8fafc; padding: 16px; border-radius: 8px; border: 1px dashed #cbd5e1; }
.section-title { display: flex; justify-content: space-between; font-weight: 600; font-size: 13px; color: #475569; margin-bottom: 12px; }
.small-btn { font-size: 12px; padding: 2px 8px; cursor: pointer; }

.rule-item { background: white; padding: 12px; border-radius: 6px; margin-bottom: 8px; border: 1px solid #e2e8f0; }
.rule-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.rule-name-input { border: none; font-weight: 600; color: #1e293b; width: 200px; }
.del-rule { color: #ef4444; background: none; border: none; cursor: pointer; font-size: 12px; }
.rule-body { display: grid; grid-template-columns: 1fr 1fr 80px; gap: 8px; align-items: center; }
.rule-row { display: flex; flex-direction: column; gap: 2px; font-size: 11px; color: #64748b; }
.rule-row input { padding: 4px; border: 1px solid #e2e8f0; border-radius: 4px; }
.dist-input { width: 50px; }

.modal-actions { margin-top: 24px; display: flex; justify-content: flex-end; gap: 12px; }
.save-btn { background: #2563eb; color: white; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; }
.cancel-btn { background: #f1f5f9; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; }
</style>