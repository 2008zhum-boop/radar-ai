<template>
  <div class="config-box">
    <h3>🛡️ 客户监控配置</h3>
    <div class="input-group">
      <input 
        v-model="inputValue" 
        @keyup.enter="handleAdd"
        placeholder="输入品牌 (如: 特斯拉)" 
      />
      <button @click="handleAdd" class="btn-primary">添加监控</button>
    </div>
    
    <div class="tags-area">
      <span v-if="keywords.length === 0" class="no-tags">暂无监控词</span>
      <span v-for="word in keywords" :key="word" class="keyword-tag">
        {{ word }}
        <span class="delete-x" @click="$emit('remove', word)">×</span>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  keywords: Array
})

const emit = defineEmits(['add', 'remove'])
const inputValue = ref('')

const handleAdd = () => {
  if (!inputValue.value) return
  emit('add', inputValue.value)
  inputValue.value = ''
}
</script>

<style scoped>
.config-box { background: #f1f5f9; padding: 20px; border-radius: 12px; margin-bottom: 25px; }
.config-box h3 { margin-top: 0; font-size: 1rem; color: #475569; }
.input-group { display: flex; gap: 10px; margin-bottom: 15px; }
input { flex: 1; padding: 10px 15px; border: 1px solid #cbd5e1; border-radius: 8px; }
.btn-primary { background: #2563eb; color: white; border: none; padding: 0 20px; border-radius: 8px; cursor: pointer; }
.tags-area { display: flex; flex-wrap: wrap; gap: 10px; }
.keyword-tag { background: white; padding: 5px 12px; border-radius: 20px; font-size: 13px; border: 1px solid #e2e8f0; display: flex; gap: 6px; }
.delete-x { color: #94a3b8; cursor: pointer; font-weight: bold; }
.delete-x:hover { color: #dc2626; }
.no-tags { font-size: 13px; color: #94a3b8; }
</style>