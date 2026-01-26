<template>
  <table class="hot-table">
    <thead>
      <tr>
        <th width="80">排名</th>
        <th width="100">热度</th>
        <th>标题 (点击标题进行AI分析)</th>
        <th width="100">标签</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="item in list" :key="item.rank">
        <td class="rank-cell" :class="{'top-3': item.rank <= 3}">{{ item.rank }}</td>
        <td>{{ formatNumber(item.heat) }}</td>
        <td class="title-cell">
          <a href="#" class="title-link" @click.prevent="$emit('analyze', item.title)">
            {{ item.title }} 
            <span class="ai-badge">✨ AI分析</span>
          </a>
        </td>
        <td>
          <span v-if="item.label" class="tag" :class="getTagClass(item.label)">{{ item.label }}</span>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
defineProps({
  list: Array
})

// 定义我们要发出的事件
const emit = defineEmits(['analyze'])

const formatNumber = (num) => {
  if (num > 10000) return (num / 10000).toFixed(1) + '万'
  return num
}

const getTagClass = (label) => {
  if (label === '爆') return 'tag-red'
  if (label === '新') return 'tag-green'
  return 'tag-orange'
}
</script>

<style scoped>
.hot-table { width: 100%; border-collapse: collapse; }
.hot-table th { text-align: left; padding: 12px; color: #64748b; font-weight: 600; border-bottom: 2px solid #e2e8f0; }
.hot-table td { padding: 12px; border-bottom: 1px solid #f1f5f9; }
.rank-cell { font-weight: bold; color: #94a3b8; }
.top-3 { color: #f59e0b; font-size: 1.1em; }
.title-link { text-decoration: none; color: #334155; font-weight: 500; display: inline-flex; align-items: center; }
.title-link:hover { color: #2563eb; }

/* AI 小徽章样式 */
.ai-badge { 
  font-size: 10px; background: #eff6ff; color: #2563eb; 
  padding: 2px 8px; border-radius: 12px; margin-left: 8px; 
  border: 1px solid #dbeafe; opacity: 0.8;
}
.title-link:hover .ai-badge { background: #2563eb; color: white; opacity: 1; }

.tag { padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
.tag-red { background: #fee2e2; color: #dc2626; }
.tag-green { background: #dcfce7; color: #16a34a; }
.tag-orange { background: #ffedd5; color: #c2410c; }
</style>