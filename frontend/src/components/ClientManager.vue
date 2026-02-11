<template>
  <div class="client-manager-container">
    <div class="content-wrapper">
      
      <div class="toolbar-section">
        <div class="toolbar-left">
          <h2 class="page-title">客户配置中心</h2>
          <span class="info-text">已配置 <b>{{ clients.length }}</b> 个监控主体</span>
        </div>
        <button class="add-btn-primary" @click="openEditModal({})">
          <span class="icon">+</span> 新增监控客户
        </button>
      </div>

      <div class="table-card">
        <table class="data-table">
          <thead>
            <tr>
              <th width="20%">客户名称</th>
              <th width="15%">行业分类</th>
              <th width="35%">关键词配置</th>
              <th width="15%">监控状态</th>
              <th width="15%" class="text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="client in clients" :key="client.client_id" :class="{ 'disabled-row': client.status === 0 }">
              
              <td>
                <div class="name-cell">
                  <div class="avatar-placeholder">{{ client.name.charAt(0) }}</div>
                  <div class="name-info">
                    <span class="client-name">{{ client.name }}</span>
                    <span class="rule-badge" v-if="client.config.advanced_rules.length > 0">
                      ⚡ {{ client.config.advanced_rules.length }} 规则
                    </span>
                  </div>
                </div>
              </td>

              <td>
                <span class="industry-tag">{{ client.industry || '综合' }}</span>
              </td>

              <td>
                <div class="keywords-cell">
                   <div class="kw-row" v-if="client.config.brand_keywords.length > 0">
                      <span class="kw-label">包含:</span>
                      <div class="kw-list">
                         <span v-for="w in client.config.brand_keywords.slice(0, 3)" :key="w" class="tag brand">{{ w }}</span>
                         <span v-if="client.config.brand_keywords.length > 3" class="tag more">+{{ client.config.brand_keywords.length - 3 }}</span>
                      </div>
                   </div>
                   <div class="kw-row" v-if="client.config.exclude_keywords.length > 0">
                      <span class="kw-label exclude">排除:</span>
                      <div class="kw-list">
                         <span v-for="w in client.config.exclude_keywords.slice(0, 2)" :key="w" class="tag exclude">{{ w }}</span>
                         <span v-if="client.config.exclude_keywords.length > 2" class="tag more">+{{ client.config.exclude_keywords.length - 2 }}</span>
                      </div>
                   </div>
                   <span v-if="client.config.brand_keywords.length === 0 && client.config.exclude_keywords.length === 0" class="tag none">未配置关键词</span>
                </div>
              </td>

              <td>
                <div class="status-indicator" :class="client.status===1 ? 'active' : 'inactive'">
                  <span class="dot"></span>
                  {{ client.status===1 ? '监控中' : '已暂停' }}
                </div>
              </td>

              <td class="text-right">
                <div class="action-group">
                  <button class="action-btn icon-btn edit" @click="openEditModal(client)" title="编辑">
                    ✏️
                  </button>
                  <button class="action-btn icon-btn del" @click="confirmDelete(client)" title="删除">
                    🗑️
                  </button>
                </div>
              </td>
            </tr>

            <tr v-if="clients.length === 0">
              <td colspan="5" class="empty-cell">
                <div class="empty-state">
                  <div class="empty-icon">📭</div>
                  <p>暂无数据，请点击右上角“新增”按钮开启监控</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>

    <!-- 编辑/新增 弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <div class="header-main">
            <h3>{{ isEditing ? '编辑监控配置' : '新增监控对象' }}</h3>
            <p class="header-sub">配置全网舆情扫描的关键词与预警规则</p>
          </div>
          <button class="close-modal-btn" @click="showModal = false">×</button>
        </div>
        
        <div class="modal-body">
            
            <div class="form-section-block">
                <div class="form-row">
                    <div class="col span-2">
                        <label>监控主体名称 <span class="req">*</span></label>
                        <input v-model="form.name" placeholder="输入企业/品牌全称" class="main-input" />
                    </div>
                    <div class="col span-1">
                         <label>所属行业</label>
                        <select v-model="form.industry" class="main-input">
                            <option>科技互联网</option>
                            <option>消费零售</option>
                            <option>汽车出行</option>
                            <option>金融地产</option>
                            <option>医疗健康</option>
                            <option>文娱传媒</option>
                            <option>其他</option>
                        </select>
                    </div>
                     <div class="col span-1">
                         <label>监控状态</label>
                         <div class="toggle-switch" @click="form.status = form.status===1?0:1" :class="{active: form.status===1}">
                             <div class="toggle-knob"></div>
                             <span>{{ form.status===1 ? '开启' : '暂停' }}</span>
                         </div>
                    </div>
                </div>
            </div>

            <div class="form-section-block">
                <h4 class="block-title">🔍 关键词定义</h4>
                <div class="form-row">
                    <div class="col">
                    <label>包含关键词 (Any) - 回车添加</label>
                    <div class="tag-input-box focus-blue">
                        <span v-for="(tag, i) in form.brand_keywords" :key="i" class="tag brand">
                        {{ tag }} <i @click="removeTag('brand', i)">×</i>
                        </span>
                        <input v-model="tempBrand" @keyup.enter="addTag('brand')" placeholder="输入词语后回车..." />
                    </div>
                    </div>
                    <div class="col">
                    <label>排除关键词 (Not) - 优先级最高</label>
                    <div class="tag-input-box focus-red">
                        <span v-for="(tag, i) in form.exclude_keywords" :key="i" class="tag exclude">
                        {{ tag }} <i @click="removeTag('exclude', i)">×</i>
                        </span>
                        <input v-model="tempExclude" @keyup.enter="addTag('exclude')" placeholder="输入词语后回车..." />
                    </div>
                    </div>
                </div>
            </div>

            <div class="form-section-block bg-gray">
                <div class="section-header-row">
                    <h4 class="block-title">⚡ 高级语义规则 (Context Rules)</h4>
                    <button class="small-add-btn" @click="addRule">+ 添加规则</button>
                </div>
                
                <div class="rules-list-container">
                    <div v-for="(rule, idx) in form.advanced_rules" :key="idx" class="rule-card" :class="getRuleClass(rule.risk_level)">
                        <div class="rule-top">
                            <input v-model="rule.rule_name" placeholder="规则名称" class="rule-name-input"/>
                            <div class="rule-actions">
                                <select v-model="rule.risk_level" class="risk-select" :class="'level-'+rule.risk_level">
                                    <option :value="3">🔴 高危预警</option>
                                    <option :value="2">🟡 中度风险</option>
                                    <option :value="0">🟢 正面利好</option>
                                </select>
                                <button class="del-rule-btn" @click="removeRule(idx)">🗑️</button>
                            </div>
                        </div>
                        <div class="rule-inputs">
                            <div class="input-group">
                                <span>当包含:</span>
                                <input v-model="rule._must_str" placeholder="词A,词B" />
                            </div>
                            <div class="input-group">
                                <span>且附近有:</span>
                                <input v-model="rule._near_str" placeholder="词C,词D" />
                            </div>
                            <div class="input-group short">
                                <span>距离 <</span>
                                <input type="number" v-model="rule.distance" />
                                <span>字</span>
                            </div>
                        </div>
                    </div>
                    <div v-if="form.advanced_rules.length === 0" class="empty-rules">
                        暂无高级规则，点击右上角添加
                    </div>
                </div>
            </div>

        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="showModal = false">取消</button>
          <button class="btn-save" @click="saveConfig">
              {{ isEditing ? '保存修改' : '立即创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { getClients, saveClientConfig, deleteClient } from '../services/api'

const clients = ref([])
const showModal = ref(false)
const isEditing = ref(false)
const form = reactive({ 
    client_id: null,
    name: '', 
    industry: '科技互联网', 
    status: 1, 
    brand_keywords: [], 
    exclude_keywords: [], 
    advanced_rules: [] 
})
const tempBrand = ref('')
const tempExclude = ref('')

const loadData = async () => { 
    try { 
        const res = await getClients(); 
        clients.value = Array.isArray(res) ? res : []; 
    } catch (e) { 
        clients.value = [] 
    } 
}
onMounted(loadData)

const openEditModal = (client) => {
  tempBrand.value = ''
  tempExclude.value = ''
  if (client.client_id) {
    isEditing.value = true
    form.client_id = client.client_id
    form.name = client.name
    form.industry = client.industry || '科技互联网'
    form.status = (client.status !== undefined) ? client.status : 1
    form.brand_keywords = [...(client.config.brand_keywords || [])]
    form.exclude_keywords = [...(client.config.exclude_keywords || [])]
    const rules = client.config.advanced_rules || []
    form.advanced_rules = rules.map(r => ({ ...r, risk_level: r.risk_level ?? 3, _must_str: (r.must_contain || []).join(','), _near_str: (r.nearby_words || []).join(',') }))
  } else {
    isEditing.value = false
    Object.assign(form, { client_id: null, name: '', industry: '科技互联网', status: 1, brand_keywords: [], exclude_keywords: [], advanced_rules: [] })
  }
  showModal.value = true
}

const addTag = (type) => { 
    const val = type==='brand' ? tempBrand.value.trim() : tempExclude.value.trim();
    if (!val) return;
    if (type==='brand') { form.brand_keywords.push(val); tempBrand.value=''; } 
    if (type==='exclude') { form.exclude_keywords.push(val); tempExclude.value=''; } 
}
const removeTag = (type, index) => { if (type==='brand') form.brand_keywords.splice(index, 1); if (type==='exclude') form.exclude_keywords.splice(index, 1); }
const addRule = () => form.advanced_rules.push({ rule_name: '新规则', risk_level: 3, distance: 50, _must_str: '', _near_str: '' })
const removeRule = (idx) => form.advanced_rules.splice(idx, 1)

const saveConfig = async () => {
  if (!form.name.trim()) return alert('请输入客户名称')
  
  // Robust formatting for rules
  const formattedRules = (form.advanced_rules || []).map(r => ({ 
      rule_name: r.rule_name || '新规则', 
      risk_level: Number(r.risk_level ?? 3), 
      must_contain: (r._must_str || '').split(',').filter(s=>s.trim()), 
      nearby_words: (r._near_str || '').split(',').filter(s=>s.trim()), 
      distance: Number(r.distance || 50) 
  }))
  
  // Ensure strict null for new clients (not undefined or empty string)
  const cid = form.client_id || null;

  try { 
      await saveClientConfig({ 
          client_id: cid,
          name: form.name, 
          industry: form.industry, 
          status: Number(form.status), 
          brand_keywords: [...form.brand_keywords], // Copy array
          exclude_keywords: [...form.exclude_keywords], // Copy array
          advanced_rules: formattedRules 
      }); 
      showModal.value = false; 
      await loadData(); 
  } catch (e) { 
      console.error("Save failed:", e)
      alert("保存失败: " + (e.response?.data?.detail || e.message)) 
  }
}
const confirmDelete = async (client) => { if (confirm(`确定要删除客户 [${client.name}] 吗？`)) { await deleteClient(client.client_id); await loadData(); } }
const getRuleClass = (level) => { if (level === 3) return 'rule-danger'; if (level === 2) return 'rule-warning'; return 'rule-success'; }
</script>

<style scoped>
.client-manager-container {
  padding: 32px 48px;
  background: #f8fafc;
  min-height: 100vh;
  margin: 0 auto; 
  font-family: 'Inter', -apple-system, sans-serif;
}

.content-wrapper { max-width: 1400px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }

/* 顶部工具栏 */
.toolbar-section { display: flex; justify-content: space-between; align-items: flex-end; padding-bottom: 10px; }
.page-title { margin: 0 0 4px 0; font-size: 24px; color: #1e293b; font-weight: 800; letter-spacing: -0.5px; }
.info-text { font-size: 14px; color: #64748b; }
.add-btn-primary { background: #0f172a; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 8px; transition: all 0.2s; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
.add-btn-primary:hover { background: #334155; transform: translateY(-1px); }

/* 表格卡片化 */
.table-card { background: white; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th { background: #f8fafc; color: #64748b; font-weight: 600; text-align: left; padding: 16px 24px; border-bottom: 1px solid #e2e8f0; font-size: 13px; }
.data-table td { padding: 20px 24px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover { background-color: #fcfcfc; }

/* 单元格样式 */
.name-cell { display: flex; align-items: center; gap: 12px; }
.avatar-placeholder { width: 40px; height: 40px; background: #eff6ff; color: #3b82f6; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 18px; }
.name-info { display: flex; flex-direction: column; gap: 4px; }
.client-name { font-weight: 700; color: #0f172a; font-size: 15px; }
.rule-badge { font-size: 11px; color: #0284c7; background: #e0f2fe; padding: 2px 6px; border-radius: 4px; display: inline-block; width: fit-content; font-weight: 500;}

.industry-tag { display: inline-block; font-size: 13px; background: #f1f5f9; color: #475569; padding: 4px 12px; border-radius: 20px; font-weight: 500; border: 1px solid #e2e8f0; }

.keywords-cell { display: flex; flex-direction: column; gap: 6px; }
.kw-row { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.kw-label { color: #94a3b8; min-width: 32px; }
.kw-label.exclude { color: #f87171; }
.kw-list { display: flex; gap: 4px; flex-wrap: wrap; }
.tag { font-size: 12px; padding: 2px 8px; border-radius: 4px; border: 1px solid transparent; }
.tag.brand { background: #eff6ff; color: #3b82f6; border-color: #dbeafe; }
.tag.exclude { background: #fef2f2; color: #ef4444; border-color: #fee2e2; }
.tag.more { background: #f1f5f9; color: #64748b; }
.tag.none { color: #cbd5e1; font-style: italic; font-size: 12px;}

.status-indicator { font-size: 13px; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; padding: 4px 10px; border-radius: 20px; }
.status-indicator.active { background: #dcfce7; color: #16a34a; }
.status-indicator.active .dot { background: #16a34a; }
.status-indicator.inactive { background: #f1f5f9; color: #94a3b8; }
.status-indicator.inactive .dot { background: #cbd5e1; }
.dot { width: 8px; height: 8px; border-radius: 50%; }

.action-group { display: flex; justify-content: flex-end; gap: 8px; }
.icon-btn { width: 32px; height: 32px; border-radius: 8px; border: 1px solid #e2e8f0; background: white; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.icon-btn:hover { background: #f8fafc; border-color: #cbd5e1; transform: translateY(-1px); }
.icon-btn.del:hover { background: #fef2f2; border-color: #fca5a5; }

/* 弹窗样式 */
.modal-overlay { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(4px); }
.modal-content { background: white; border-radius: 16px; width: 700px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); animation: modalIn 0.3s cubic-bezier(0.16, 1, 0.3, 1); }

@keyframes modalIn { from { opacity: 0; transform: scale(0.95) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }

.modal-header { padding: 24px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: flex-start; }
.header-main h3 { margin: 0; font-size: 20px; color: #0f172a; font-weight: 700; }
.header-sub { margin: 4px 0 0 0; color: #64748b; font-size: 13px; }
.close-modal-btn { background: none; border: none; font-size: 24px; color: #94a3b8; cursor: pointer; line-height: 1; }

.modal-body { padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; max-height: 60vh; }
.form-section-block { display: flex; flex-direction: column; gap: 16px; }
.block-title { margin: 0 0 12px 0; font-size: 14px; font-weight: 700; color: #334155; text-transform: uppercase; letter-spacing: 0.5px; }

.form-row { display: flex; gap: 20px; }
.col { display: flex; flex-direction: column; gap: 8px; flex: 1; }
.col.span-2 { flex: 2; }
.req { color: #ef4444; }
label { font-size: 13px; font-weight: 600; color: #475569; }

.main-input { padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; outline: none; transition: all 0.2s; }
.main-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }

/* Switch Toggle */
.toggle-switch { display: flex; align-items: center; gap: 8px; cursor: pointer; background: #e2e8f0; padding: 4px; border-radius: 20px; transition: all 0.3s; width: fit-content; padding-right: 12px; }
.toggle-knob { width: 20px; height: 20px; background: white; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: all 0.3s; }
.toggle-switch span { font-size: 12px; font-weight: 600; color: #64748b; }
.toggle-switch.active { background: #16a34a; }
.toggle-switch.active .toggle-knob { transform: translateX(100%); }
.toggle-switch.active span { color: white; margin-left: -20px; margin-right: 8px; } /* Hacky positioning */

.tag-input-box { border: 1px solid #cbd5e1; padding: 8px; border-radius: 8px; display: flex; flex-wrap: wrap; gap: 6px; min-height: 46px; background: white; transition: border 0.2s; }
.focus-blue:focus-within { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.focus-red:focus-within { border-color: #ef4444; box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1); }
.tag-input-box input { border: none; outline: none; flex: 1; min-width: 80px; font-size: 14px; }
.tag i { margin-left: 6px; cursor: pointer; font-style: normal; opacity: 0.6; } .tag i:hover { opacity: 1; }

.bg-gray { background: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; }
.section-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.small-add-btn { font-size: 12px; color: #2563eb; background: white; border: 1px solid #e2e8f0; padding: 4px 10px; border-radius: 6px; cursor: pointer; font-weight: 600; }

.rule-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); transition: all 0.2s; border-left: 4px solid transparent; }
.rule-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.rule-danger { border-left-color: #ef4444; } .rule-warning { border-left-color: #f59e0b; } .rule-success { border-left-color: #22c55e; }

.rule-top { display: flex; justify-content: space-between; margin-bottom: 12px; }
.rule-name-input { font-weight: 700; border: none; border-bottom: 1px dashed #cbd5e1; width: 150px; outline: none; padding-bottom: 2px; }
.rule-actions { display: flex; gap: 8px; }
.risk-select { border: 1px solid #e2e8f0; border-radius: 6px; font-size: 12px; padding: 4px; outline: none; }
.del-rule-btn { border: none; background: #fef2f2; color: #ef4444; width: 24px; height: 24px; border-radius: 4px; cursor: pointer; }

.rule-inputs { display: grid; grid-template-columns: 1fr 1fr auto; gap: 12px; align-items: center; }
.input-group { display: flex; flex-direction: column; gap: 4px; }
.input-group span { font-size: 11px; color: #94a3b8; font-weight: 600; }
.input-group input { padding: 6px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 13px; }
.input-group.short input { width: 60px; text-align: center; }

.empty-rules { text-align: center; color: #94a3b8; font-size: 13px; padding: 20px; border: 1px dashed #cbd5e1; border-radius: 8px; }

.modal-footer { padding: 24px; border-top: 1px solid #f1f5f9; display: flex; justify-content: flex-end; gap: 16px; background: #f8fafc; border-radius: 0 0 16px 16px; }
.btn-cancel { padding: 10px 24px; border: 1px solid #cbd5e1; background: white; border-radius: 8px; font-weight: 600; color: #475569; cursor: pointer; }
.btn-save { padding: 10px 24px; border: none; background: #0f172a; border-radius: 8px; font-weight: 600; color: white; cursor: pointer; box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.2); }
.btn-save:hover { background: #334155; }
</style>