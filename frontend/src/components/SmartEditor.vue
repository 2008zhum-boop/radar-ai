<template>
  <div class="smart-editor">
    <div class="editor-header">
      <h2>智能写作（占位）</h2>
    </div>

    <textarea v-model="text" placeholder="在此输入标题或内容..." />

    <div class="editor-actions">
      <button @click="clear">清空</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const text = ref('')

const clear = () => { text.value = '' }
</script>

<style scoped>
.smart-editor { padding: 16px }
.editor-header h2 { margin: 0 0 12px 0 }
textarea { width:100%; min-height:320px; padding:12px; border-radius:8px; border:1px solid #e2e8f0; resize:vertical }
.editor-actions { margin-top:12px }
button { background:#2563eb; color:#fff; border:none; padding:8px 12px; border-radius:6px }
</style>
