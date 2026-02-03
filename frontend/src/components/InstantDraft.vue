<template>
  <div class="instant-draft">
    <header class="id-header">
      <button class="back-btn" @click="$emit('back')">← 返回</button>
      <h1 class="id-title">今日热点 · 极速成稿</h1>
      <span class="id-badge">财经科技媒体</span>
    </header>

    <!-- 步骤条 -->
    <div class="steps-bar">
      <div
        v-for="(s, i) in steps"
        :key="i"
        class="step-item"
        :class="{ active: currentStep === i + 1, done: currentStep > i + 1 }"
        @click="currentStep <= i + 1 || currentStep > i + 1 ? goStep(i + 1) : null"
      >
        <span class="step-num">{{ i + 1 }}</span>
        <span class="step-name">{{ s }}</span>
      </div>
    </div>

    <!-- 每一步独立内容区 -->
    <div class="step-content">
      <!-- 步骤 1：选题分析 -->
      <div v-show="currentStep === 1" class="step-panel">
        <h2 class="panel-title">第一步：选题分析</h2>
        <p class="panel-desc">输入或带入今日热点话题，由 AI 分析情绪、推荐角度与爆款标题。</p>
        <div class="form-group">
          <label>话题</label>
          <input v-model="topic" type="text" placeholder="请输入话题，或从「今日热点」页点击「极速成稿」带入" class="full-input">
        </div>
        <button class="btn-primary large" @click="runAnalyze" :disabled="analyzing || !topic.trim()">
          {{ analyzing ? 'AI 分析中...' : '📊 选题分析（调用 AI）' }}
        </button>
        <div v-if="analyzeError" class="error-msg">{{ analyzeError }}</div>
        <div v-if="analysisResult" class="result-card">
          <h4>选题分析结果</h4>
          <p class="meta">情绪：{{ analysisResult.emotion }}</p>
          <div class="angles">
            <span class="label">推荐角度：</span>
            <span v-for="(a, i) in (analysisResult.angles || [])" :key="i" class="angle-tag">{{ a }}</span>
          </div>
          <div class="titles">
            <span class="label">爆款标题（点击选用）：</span>
            <div v-for="(t, i) in (analysisResult.titles || [])" :key="i" class="title-item" @click="selectedTitle = t">{{ t }}</div>
          </div>
          <input v-model="selectedTitle" placeholder="或输入自定义标题" class="full-input">
          <input v-model="selectedAngle" placeholder="切入点/角度" class="full-input">
          <button class="btn-primary" @click="currentStep = 2">下一步：生成大纲</button>
        </div>
      </div>

      <!-- 步骤 2：生成大纲 -->
      <div v-show="currentStep === 2" class="step-panel">
        <h2 class="panel-title">第二步：生成大纲</h2>
        <p class="panel-desc">基于选题分析结果，由 AI 生成文章大纲。</p>
        <div class="form-row">
          <div class="form-group">
            <label>标题</label>
            <input v-model="selectedTitle" type="text" class="full-input">
          </div>
          <div class="form-group">
            <label>切入点/角度</label>
            <input v-model="selectedAngle" type="text" class="full-input">
          </div>
        </div>
        <button class="btn-primary large" @click="generateOutlineAction" :disabled="outlineLoading || !(selectedTitle || topic).trim()">
          {{ outlineLoading ? 'AI 生成大纲中...' : '📝 生成大纲（调用 AI）' }}
        </button>
        <div v-if="outlineError" class="error-msg">{{ outlineError }}</div>
        <div v-if="outlineStructure.length > 0" class="outline-result">
          <h4>文章大纲</h4>
          <div v-for="(section, index) in outlineStructure" :key="index" class="outline-item">
            <span class="outline-num">{{ index + 1 }}</span>
            <span class="outline-title">{{ section.title }}</span>
          </div>
          <button class="btn-secondary" @click="addOutlineSection">添加章节</button>
          <button class="btn-primary" @click="currentStep = 3">下一步：根据大纲成文</button>
        </div>
        <button class="btn-text" @click="currentStep = 1">← 上一步</button>
      </div>

      <!-- 步骤 3：根据大纲成文 -->
      <div v-show="currentStep === 3" class="step-panel">
        <h2 class="panel-title">第三步：根据大纲生成文章</h2>
        <p class="panel-desc">由 AI 根据大纲撰写正文（财经科技媒体风格）。</p>
        <button class="btn-primary large" @click="generateArticleAction" :disabled="articleLoading || outlineStructure.length === 0">
          {{ articleLoading ? 'AI 成文中...' : '✨ 使用此大纲生成文章（调用 AI）' }}
        </button>
        <div v-if="articleError" class="error-msg">{{ articleError }}</div>
        <div v-if="articleBody" class="article-preview">
          <input v-model="articleTitle" class="article-title-input" placeholder="文章标题">
          <textarea v-model="articleBody" class="article-body-preview" readonly rows="16"></textarea>
        </div>
        <button class="btn-text" @click="currentStep = 2">← 上一步</button>
        <button v-if="articleBody" class="btn-text" @click="currentStep = 4">下一步：配图 →</button>
      </div>

      <!-- 步骤 4：配图 -->
      <div v-show="currentStep === 4" class="step-panel">
        <h2 class="panel-title">第四步：配图</h2>
        <p class="panel-desc">成稿后可在此为文章插入配图（功能开发中）。</p>
        <button class="btn-text" @click="currentStep = 3">← 上一步</button>
        <button class="btn-text" @click="currentStep = 5">下一步：审查 →</button>
      </div>

      <!-- 步骤 5：审查 -->
      <div v-show="currentStep === 5" class="step-panel">
        <h2 class="panel-title">第五步：审查</h2>
        <p class="panel-desc">合规与风格审查（功能开发中）。</p>
        <button class="btn-text" @click="currentStep = 4">← 上一步</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { analyzeTopic, generateOutline, generateArticle } from '../services/api'

const steps = ['选题分析', '生成大纲', '成文', '配图', '审查']

export default {
  name: 'InstantDraft',
  props: {
    initialTopic: { type: String, default: '' }
  },
  emits: ['back'],
  setup(props) {
    const currentStep = ref(1)
    const topic = ref(props.initialTopic || '')
    const contentTypes = ref(['科技', '财经'])
    const analyzing = ref(false)
    const outlineLoading = ref(false)
    const articleLoading = ref(false)
    const analysisResult = ref(null)
    const selectedTitle = ref('')
    const selectedAngle = ref('')
    const outlineStructure = ref([])
    const articleTitle = ref('')
    const articleBody = ref('')
    const analyzeError = ref('')
    const outlineError = ref('')
    const articleError = ref('')

    watch(() => props.initialTopic, (v) => { if (v) topic.value = v }, { immediate: true })

    const goStep = (n) => { currentStep.value = n }

    const runAnalyze = async () => {
      if (!topic.value.trim()) return
      analyzing.value = true
      analysisResult.value = null
      analyzeError.value = ''
      try {
        const res = await analyzeTopic(topic.value.trim())
        analysisResult.value = res
        if (res.titles && res.titles[0]) selectedTitle.value = res.titles[0]
        if (res.angles && res.angles[0]) selectedAngle.value = res.angles[0]
      } catch (e) {
        const msg = e.response?.data?.detail || e.message || '选题分析请求失败'
        analyzeError.value = typeof msg === 'object' ? JSON.stringify(msg) : msg
        console.error('选题分析失败', e)
      } finally {
        analyzing.value = false
      }
    }

    const generateOutlineAction = async () => {
      const title = (selectedTitle.value || topic.value || '未命名选题').trim()
      const angle = (selectedAngle.value || '财经科技视角').trim()
      outlineLoading.value = true
      outlineError.value = ''
      try {
        const res = await generateOutline(title, angle, topic.value || '')
        if (res && res.status === 'success' && res.data && res.data.structure) {
          outlineStructure.value = res.data.structure
          if (!articleTitle.value) articleTitle.value = title
        } else {
          outlineError.value = res?.message || '大纲返回格式异常'
        }
      } catch (e) {
        const msg = e.response?.data?.detail || e.message || '生成大纲请求失败'
        outlineError.value = typeof msg === 'object' ? JSON.stringify(msg) : msg
        console.error('生成大纲失败', e)
      } finally {
        outlineLoading.value = false
      }
    }

    const addOutlineSection = () => {
      outlineStructure.value.push({ title: '新章节', sub_points: [] })
    }

    const generateArticleAction = async () => {
      const title = (articleTitle.value || selectedTitle.value || topic.value || '未命名').trim()
      articleLoading.value = true
      articleBody.value = ''
      articleError.value = ''
      try {
        const res = await generateArticle(title, outlineStructure.value, topic.value || '')
        if (res && res.status === 'success') {
          const text = res.data
          articleBody.value = typeof text === 'string' ? text : (text?.content || JSON.stringify(text))
          if (!articleTitle.value) articleTitle.value = title
        } else {
          articleError.value = res?.message || '成文返回格式异常'
        }
      } catch (e) {
        const msg = e.response?.data?.detail || e.message || '生成文章请求失败'
        articleError.value = typeof msg === 'object' ? JSON.stringify(msg) : msg
        console.error('生成文章失败', e)
      } finally {
        articleLoading.value = false
      }
    }

    return {
      steps,
      currentStep,
      topic,
      contentTypes,
      analyzing,
      outlineLoading,
      articleLoading,
      analysisResult,
      selectedTitle,
      selectedAngle,
      outlineStructure,
      articleTitle,
      articleBody,
      analyzeError,
      outlineError,
      articleError,
      goStep,
      runAnalyze,
      generateOutlineAction,
      addOutlineSection,
      generateArticleAction
    }
  }
}
</script>

<style scoped>
.instant-draft { min-height: 100%; display: flex; flex-direction: column; background: #f8fafc; }
.id-header {
  display: flex; align-items: center; gap: 16px; padding: 12px 24px;
  background: white; border-bottom: 1px solid #e2e8f0;
}
.back-btn { border: none; background: none; color: #64748b; cursor: pointer; font-size: 14px; }
.back-btn:hover { color: #2563eb; }
.id-title { margin: 0; font-size: 18px; font-weight: 700; color: #1e293b; }
.id-badge { background: #dbeafe; color: #1d4ed8; padding: 4px 10px; border-radius: 12px; font-size: 12px; }

.steps-bar {
  display: flex; align-items: center; justify-content: center; gap: 8px; padding: 16px 24px;
  background: white; border-bottom: 1px solid #e2e8f0; flex-wrap: wrap;
}
.step-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 8px;
  cursor: pointer; color: #94a3b8; font-size: 13px;
}
.step-item.active { background: #eff6ff; color: #2563eb; font-weight: 600; }
.step-item.done { color: #16a34a; }
.step-num {
  width: 22px; height: 22px; border-radius: 50%; background: #e2e8f0; color: #64748b;
  display: inline-flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600;
}
.step-item.active .step-num { background: #2563eb; color: white; }
.step-item.done .step-num { background: #16a34a; color: white; }

.step-content { flex: 1; padding: 24px 32px; overflow-y: auto; }
.step-panel {
  max-width: 640px; margin: 0 auto; background: white; border-radius: 12px;
  padding: 28px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.panel-title { margin: 0 0 8px 0; font-size: 18px; font-weight: 700; color: #1e293b; }
.panel-desc { margin: 0 0 20px 0; font-size: 13px; color: #64748b; line-height: 1.5; }

.form-group { margin-bottom: 16px; }
.form-group label { display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px; color: #334155; }
.full-input { width: 100%; padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 14px; box-sizing: border-box; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.btn-primary { padding: 10px 20px; border: none; background: #2563eb; color: white; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; }
.btn-primary.large { width: 100%; padding: 12px 24px; font-size: 15px; margin-bottom: 12px; }
.btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary { padding: 8px 16px; border: 1px solid #cbd5e1; background: white; border-radius: 8px; cursor: pointer; font-size: 13px; margin-right: 8px; margin-top: 8px; }
.btn-text { padding: 8px 16px; border: none; background: none; color: #2563eb; cursor: pointer; font-size: 13px; margin-top: 12px; margin-right: 12px; }
.btn-text:hover { text-decoration: underline; }

.error-msg { color: #dc2626; font-size: 13px; margin-top: 8px; padding: 8px 12px; background: #fef2f2; border-radius: 6px; }
.result-card { margin-top: 20px; padding: 20px; background: #f8fafc; border-radius: 10px; }
.result-card h4 { margin: 0 0 12px 0; font-size: 14px; }
.angle-tag { display: inline-block; margin: 2px 4px 2px 0; padding: 2px 8px; background: #e0f2fe; color: #0369a1; border-radius: 4px; font-size: 12px; }
.title-item { margin: 6px 0; cursor: pointer; color: #2563eb; font-size: 13px; }
.title-item:hover { text-decoration: underline; }
.result-card .full-input { margin-top: 8px; }
.result-card .btn-primary { margin-top: 12px; }

.outline-result { margin-top: 20px; padding: 20px; background: #f8fafc; border-radius: 10px; }
.outline-result h4 { margin: 0 0 12px 0; font-size: 14px; }
.outline-item { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #e2e8f0; font-size: 13px; }
.outline-num { width: 24px; height: 24px; border-radius: 50%; background: #1e293b; color: white; display: inline-flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; }
.outline-title { font-weight: 500; color: #334155; }

.article-preview { margin-top: 20px; }
.article-title-input { width: 100%; border: none; border-bottom: 2px solid #e2e8f0; font-size: 20px; font-weight: 700; padding: 8px 0; margin-bottom: 16px; outline: none; }
.article-body-preview { width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 14px; line-height: 1.8; resize: vertical; font-family: inherit; }
</style>
