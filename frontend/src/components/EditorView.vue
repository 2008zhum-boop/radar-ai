<template>
  <div class="editor-layout">
    <header class="editor-header">
      <button class="back-btn" @click="$emit('back')">← 返回工作台</button>
      <div class="header-center">
        <span class="status-badge">AI 辅助创作模式</span>
        <h2 class="doc-title">{{ initialData.title || '无标题文档' }}</h2>
      </div>
      <div class="header-right">
        <button class="save-btn">💾 保存草稿</button>
        <button class="publish-btn">🚀 发布文章</button>
      </div>
    </header>

    <div class="editor-body">
      <aside class="outline-panel">
        <div class="panel-title">
          <span>🧠 AI 智编大纲</span>
          <div class="title-actions">
            <button class="refresh-outline" @click="regenerateOutline" :disabled="loading || writing">
              {{ loading ? '生成中...' : '🔄 优化' }}
            </button>
          </div>
        </div>

        <div class="outline-actions" v-if="outlineData.structure.length > 0">
          <button class="magic-write-btn" @click="startFullWrite" :disabled="writing">
            <span v-if="writing">✍️ AI 正在疯狂码字中...</span>
            <span v-else>✨ 按此大纲一键生成全文 (1000字)</span>
          </button>
        </div>

        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>正在基于“{{ initialData.angle || '通用' }}”策略构建逻辑...</p>
        </div>

        <div v-else class="outline-list">
          <div 
            v-for="(section, index) in outlineData.structure" 
            :key="index"
            class="outline-item"
          >
            <div class="section-head">
              <span class="section-idx">{{ index + 1 }}</span>
              <span class="section-title">{{ section.title }}</span>
            </div>
            <ul class="sub-points">
              <li v-for="(sub, sIdx) in section.sub_points" :key="sIdx">
                • {{ sub }}
              </li>
            </ul>
            <button class="insert-btn" @click="insertToEditor(section)" :disabled="writing">
              写入此段落 ↓
            </button>
          </div>
        </div>
      </aside>

      <main class="writing-area">
        <div class="editor-wrapper">
          <textarea 
            v-model="content" 
            class="main-editor" 
            placeholder="在此处开始写作，或点击左侧大纲自动生成..."
            ref="editorRef"
          ></textarea>
          <div v-if="writing" class="writing-mask">
            <span class="cursor-blink">AI 正在输入...</span>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { generateOutline, generateArticle } from '../services/api' // 引入新API

const props = defineProps({
  initialData: Object // { title, angle, topic ... }
})

const emit = defineEmits(['back'])

const content = ref('')
const loading = ref(false)
const writing = ref(false) // 是否正在写全文
const outlineData = ref({ structure: [] })
const editorRef = ref(null)

// 初始化：自动生成大纲
onMounted(async () => {
  if (!props.initialData.title) {
    props.initialData.title = "未命名选题"
    props.initialData.angle = "通用"
  }
  await regenerateOutline()
})

// 1. 生成大纲
const regenerateOutline = async () => {
  loading.value = true
  try {
    const res = await generateOutline(
      props.initialData.title,
      props.initialData.angle,
      props.initialData.topic
    )
    if (res.status === 'success') {
      outlineData.value = res.data
    }
  } catch (e) {
    console.error("生成大纲失败", e)
  } finally {
    loading.value = false
  }
}

// 2. 插入单段 (旧功能)
const insertToEditor = (section) => {
  const text = `\n## ${section.title}\n${section.sub_points.map(p => `> ${p}`).join('\n')}\n\n[在此处扩展内容...]\n`
  content.value += text
}

// 3. 一键生成全文 (新功能)
const startFullWrite = async () => {
  writing.value = true
  content.value = '' // 清空现有内容
  
  try {
    // 请求后端生成全文
    const res = await generateArticle(
      props.initialData.title,
      outlineData.value.structure,
      props.initialData.topic || "当前热点事件"
    )
    
    if (res.status === 'success') {
      // 获得全文后，模拟打字机效果输出
      const fullText = res.data
      await typeWriterEffect(fullText)
    }
  } catch (e) {
    console.error("生成全文失败", e)
    content.value = "生成失败，请重试..."
  } finally {
    writing.value = false
  }
}

// 打字机效果函数
const typeWriterEffect = async (text) => {
  const chunkSize = 5 // 每次输出5个字，速度快一点
  for (let i = 0; i < text.length; i += chunkSize) {
    content.value += text.slice(i, i + chunkSize)
    // 自动滚动到底部
    if (editorRef.value) {
      editorRef.value.scrollTop = editorRef.value.scrollHeight
    }
    // 暂停一小会儿，模拟打字
    await new Promise(resolve => setTimeout(resolve, 10)) 
  }
}
</script>

<style scoped>
.editor-layout { height: 100%; display: flex; flex-direction: column; background: white; }

/* Header */
.editor-header { 
  height: 60px; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; flex-shrink: 0;
}
.back-btn { border: none; background: none; color: #64748b; cursor: pointer; font-size: 14px; font-weight: 500; }
.back-btn:hover { color: #2563eb; }
.header-center { display: flex; flex-direction: column; align-items: center; }
.doc-title { margin: 0; font-size: 16px; font-weight: 700; color: #1e293b; }
.status-badge { font-size: 10px; color: #2563eb; background: #eff6ff; padding: 1px 6px; border-radius: 4px; margin-bottom: 2px; }
.save-btn, .publish-btn { padding: 6px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; margin-left: 12px; }
.save-btn { background: white; border: 1px solid #cbd5e1; color: #475569; }
.publish-btn { background: #2563eb; border: none; color: white; }

/* Body */
.editor-body { flex: 1; display: flex; overflow: hidden; }

/* Left Outline Panel */
.outline-panel { 
  width: 350px; background: #f8fafc; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; 
}
.panel-title { 
  padding: 16px 20px; font-weight: 700; color: #334155; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; 
}
.refresh-outline { font-size: 12px; color: #2563eb; background: none; border: none; cursor: pointer; }
.refresh-outline:hover { text-decoration: underline; }

.outline-actions { padding: 16px 20px 0; }
.magic-write-btn {
  width: 100%;
  background: linear-gradient(90deg, #6366f1, #ec4899);
  color: white; border: none; padding: 10px; border-radius: 8px;
  font-weight: 600; font-size: 13px; cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}
.magic-write-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4); }
.magic-write-btn:disabled { opacity: 0.7; cursor: wait; }

.outline-list { flex: 1; overflow-y: auto; padding: 20px; }
.outline-item { 
  background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px; 
  transition: all 0.2s; position: relative;
}
.outline-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-color: #cbd5e1; }

.section-head { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 8px; }
.section-idx { 
  background: #0f172a; color: white; width: 20px; height: 20px; border-radius: 50%; 
  display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; flex-shrink: 0;
}
.section-title { font-weight: 700; font-size: 14px; color: #1e293b; line-height: 1.4; }

.sub-points { list-style: none; padding: 0; margin: 0 0 12px 28px; }
.sub-points li { font-size: 12px; color: #64748b; margin-bottom: 4px; line-height: 1.5; }

.insert-btn { 
  width: 100%; background: #f1f5f9; border: 1px dashed #cbd5e1; color: #64748b; 
  padding: 6px; border-radius: 4px; font-size: 11px; cursor: pointer; transition: all 0.2s;
}
.insert-btn:hover { background: #e2e8f0; color: #334155; border-color: #94a3b8; }

.loading-state { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; font-size: 13px; }
.spinner { width: 24px; height: 24px; border: 2px solid #e2e8f0; border-top-color: #2563eb; border-radius: 50%; margin-bottom: 12px; animation: spin 1s linear infinite; }

/* Right Writing Area */
.writing-area { flex: 1; padding: 40px 60px; overflow-y: auto; background: white; position: relative; }
.editor-wrapper { height: 100%; position: relative; }
.main-editor { 
  width: 100%; height: 100%; border: none; resize: none; outline: none; 
  font-size: 16px; line-height: 1.8; color: #334155; font-family: 'PingFang SC', sans-serif; 
}
.writing-mask {
  position: absolute; bottom: 20px; right: 20px;
  background: rgba(37,99,235, 0.9); color: white;
  padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 600;
  box-shadow: 0 4px 12px rgba(37,99,235, 0.2);
  animation: float 2s ease-in-out infinite;
}
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
</style>