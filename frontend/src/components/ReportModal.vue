<template>
  <div class="report-overlay" @click.self="$emit('close')">
    <div class="report-paper">
      
      <!-- Toolbar Removed -->
      <button class="close-btn-floating" @click="$emit('close')">✕</button>

      <div class="report-content" id="print-area">
        
        <!-- Header -->
        <header class="report-header">
          <!-- Title -->
          <div class="title-section">
            <h1 class="main-title">{{ safeData.cover.topic_title || '今日热点深度分析' }}</h1>
            <div class="meta-row">
              <span class="meta-item">📅 分析时间: {{ safeData.cover.gen_time }}</span>
            </div>
          </div>

          <!-- New Analysis Metrics Panel -->
          <div class="analysis-metrics-banner">
             <div class="amb-header">📊 舆情分析</div>
             <div class="amb-grid">
               <!-- Heat -->
               <div class="amb-item">
                 <span class="amb-label">🔥 热度指数</span>
                 <span class="amb-val text-red">{{ safeData.metrics.heat }}</span>
               </div>
               <!-- Sentiment -->
               <div class="amb-item">
                 <span class="amb-label">🎭 情感倾向</span>
                 <div class="rpt-sentiment-bar" v-if="safeData.metrics.sentiment_dist">
                    <div class="rsb-track">
                       <div class="rsb-seg" :style="{width: safeData.metrics.sentiment_dist.pos+'%', background:'#22c55e'}"></div>
                       <div class="rsb-seg" :style="{width: safeData.metrics.sentiment_dist.neu+'%', background:'#94a3b8'}"></div>
                       <div class="rsb-seg" :style="{width: safeData.metrics.sentiment_dist.neg+'%', background:'#ef4444'}"></div>
                    </div>
                    <div class="rsb-legend">
                       <span style="color:#22c55e">{{safeData.metrics.sentiment_dist.pos}}%</span> / 
                       <span style="color:#64748b">{{safeData.metrics.sentiment_dist.neu}}%</span> / 
                       <span style="color:#ef4444">{{safeData.metrics.sentiment_dist.neg}}%</span>
                    </div>
                 </div>
                 <span class="amb-val" v-else>{{ safeData.metrics.sentiment }}</span>
               </div>
               <!-- Total Volume -->
               <div class="amb-item">
                 <span class="amb-label">📢 全网声量</span>
                 <span class="amb-val">{{ safeData.metrics.total_vol }}</span>
               </div>
               <!-- High Risk -->
               <div class="amb-item">
                 <span class="amb-label">⚡ 高危负面</span>
                 <span class="amb-val text-red">{{ safeData.metrics.high_risk }}</span>
               </div>
               <!-- Keywords -->
               <div class="amb-item wide">
                 <span class="amb-label">🔑 风险关键词</span>
                 <div class="amb-tags">
                    <span v-for="k in safeData.metrics.keywords" :key="k" class="amb-tag">{{ k }}</span>
                    <span v-if="!safeData.metrics.keywords.length">无</span>
                 </div>
               </div>
             </div>
          </div>
        </header>

        <!-- Section 1: Deep Analysis -->
        <section class="rpt-section">
          <div class="sec-head">
            <span class="sec-num">01</span>
            <h2>深度分析 (Deep Analysis)</h2>
          </div>
          <div class="deep-analysis-box">
            <div class="da-item">
               <div class="da-title">📌 事件简述</div>
               <div class="da-content">{{ safeData.deep_analysis.event }}</div>
            </div>
            <div class="da-item">
               <div class="da-title">🏙️ 行业透视</div>
               <div class="da-content">{{ safeData.deep_analysis.industry }}</div>
            </div>
            <div class="da-item">
               <div class="da-title">🤔 深度思辨</div>
               <div class="da-content">{{ safeData.deep_analysis.thinking }}</div>
            </div>
             <div class="da-item">
               <div class="da-title">🔭 未来展望</div>
               <div class="da-content">{{ safeData.deep_analysis.future }}</div>
            </div>
             <div class="da-item highlight">
               <div class="da-title">📝 结语</div>
               <div class="da-content">{{ safeData.deep_analysis.conclusion }}</div>
            </div>
          </div>
        </section>

        <!-- Section 2 Removed as per request -->

        <footer class="rpt-footer">
          <div class="ft-line"></div>
          <div class="ft-info">
             <span>SmartEdit Core Intelligence System</span>
             <span>CONFIDENTIAL DOCUMENT</span>
          </div>
        </footer>

      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, computed } from 'vue'

const props = defineProps({
  data: Object
})

const formatNumber = (num) => {
    if(!num) return '0'
    if(num > 10000) return (num/10000).toFixed(1) + 'w'
    return num
}

const safeData = computed(() => {
  const d = props.data || {}
  
  // Parse Deep Analysis Data
  // If backend sends structured analysis in d.analysis (object), use it.
  // Otherwise try to split string or use default.
  let da = {
      event: '暂无数据',
      industry: '暂无数据',
      thinking: '暂无数据',
      future: '暂无数据',
      conclusion: '暂无数据'
  }
  
  if (d.deep_analysis && typeof d.deep_analysis === 'object') {
      da = d.deep_analysis
  } else if (typeof d.analysis === 'string' && d.analysis.length > 50) {
      // Fallback: put everything in event if string
      da.event = d.analysis
  }

  return {
    cover: { 
        topic_title: d.topic || d.title || (d.cover && d.cover.report_name) || '今日热点深度分析', 
        gen_time: new Date().toLocaleString()
    },
    metrics: {
        heat: d.heat ? formatNumber(d.heat) : (d.total_mentions ? formatNumber(d.total_mentions * 50) : '计算中...'),
        sentiment: d.emotion || '中性偏正向', 
        sentiment_dist: d.sentiment_distribution, // Raw object
        total_vol: formatNumber(d.total_mentions || d.heat || 0),
        high_risk: d.high_risk_count || 0,
        keywords: (d.risks || []).slice(0, 5) // Assuming d.risks is list of strings
    },
    deep_analysis: da,
    // Legacy mapping for other sections if they exist in template
    section_5: {
        defense: d.strategies ? d.strategies.map(s=>s.text).join('\n') : '',
        offense: ''
    },
    top_risks: d.top_risks || [],
    section_4: { keywords: d.risks || [] }
  }
})

const printReport = () => window.print()

const getScoreClass = (score) => {
  if (score >= 85) return 'sc-green'
  if (score >= 60) return 'sc-yellow'
  return 'sc-red'
}
</script>

<style scoped>
/* 全屏遮罩 */
.report-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 9999;
  display: flex; justify-content: center; overflow-y: auto; padding: 40px 0; backdrop-filter: blur(5px);
}

/* A4 纸张模拟 */
.report-paper {
  background: white; width: 210mm; min-height: 297mm; padding: 0; box-shadow: 0 0 50px rgba(0,0,0,0.5);
  display: flex; flex-direction: column; position: relative;
}

/* 工具栏 */
.report-toolbar {
  position: absolute; top: -50px; left: 0; width: 100%; display: flex; justify-content: space-between; align-items: center;
}
.preview-tag { color: white; font-weight: 600; opacity: 0.8; }
.tool-btn { background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 6px 16px; border-radius: 6px; cursor: pointer; margin-left: 10px; font-size: 13px; }
.tool-btn:hover { background: rgba(255,255,255,0.3); }
.tool-btn.primary { background: #2563eb; border: none; font-weight: 600; }

/* 报告正文 */
.report-content { padding: 50px 60px; font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; }

/* 头部 */
.report-header { text-align: center; margin-bottom: 40px; }
.brand-row { display: flex; justify-content: space-between; border-bottom: 2px solid #0f172a; padding-bottom: 10px; margin-bottom: 20px; }
.brand-logo { font-weight: 900; font-size: 16px; letter-spacing: 1px; color: #0f172a; }
.report-id { font-size: 12px; color: #94a3b8; font-family: monospace; }
.main-title { font-size: 32px; font-weight: 800; margin: 0 0 10px 0; color: #1e293b; }
.meta-row { color: #64748b; font-size: 14px; display: flex; gap: 20px; justify-content: center; }

/* 分数横幅 */
.score-card-banner {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; margin-top: 24px;
  display: flex; overflow: hidden;
}
.score-left { flex: 0 0 140px; background: #0f172a; color: white; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 16px; }
.score-label { font-size: 12px; opacity: 0.8; margin-bottom: 4px; }
.score-val { font-size: 36px; font-weight: 800; line-height: 1; }
.score-right { flex: 1; padding: 16px 24px; display: flex; flex-direction: column; justify-content: center; }
.score-status { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
.score-desc { font-size: 13px; color: #64748b; }
.sc-green .score-left { background: #059669; } .sc-green .score-status { color: #059669; }
.sc-yellow .score-left { background: #d97706; } .sc-yellow .score-status { color: #d97706; }
.sc-red .score-left { background: #dc2626; } .sc-red .score-status { color: #dc2626; }

/* 章节通用 */
.rpt-section { margin-bottom: 40px; }
.sec-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
.sec-num { font-size: 32px; font-weight: 900; color: #e2e8f0; line-height: 1; }
.sec-head h2 { font-size: 18px; font-weight: 700; color: #1e293b; margin: 0; text-transform: uppercase; }

/* AI 综述 */
.ai-box { display: flex; flex-direction: column; gap: 12px; font-size: 14px; line-height: 1.6; }
.ai-row { display: flex; gap: 12px; align-items: flex-start; background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #f1f5f9; }
.ai-row.warning { background: #fff1f2; border-color: #fee2e2; }
.ai-row.highlight { background: #eff6ff; border-color: #dbeafe; }
.ai-icon { font-size: 18px; margin-top: 2px; }
.ai-label { font-weight: 700; color: #475569; margin-right: 4px; }

/* 关键指标 */
.metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.metric-card { border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; text-align: center; }
.m-label { font-size: 13px; color: #64748b; margin-bottom: 8px; }
.m-val { font-size: 28px; font-weight: 800; color: #0f172a; margin-bottom: 4px; }
.m-val.red { color: #dc2626; }
.m-trend { font-size: 12px; color: #10b981; font-weight: 600; }
.m-trend.down { color: #ef4444; }

/* 风险雷达 */
.risk-cloud-box { margin-bottom: 16px; display: flex; align-items: center; gap: 12px; }
.cloud-tit { font-size: 13px; font-weight: 700; color: #64748b; }
.cloud-wrap { display: flex; gap: 8px; flex-wrap: wrap; }
.cloud-badge { font-size: 12px; background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 12px; border: 1px solid #fecaca; }
.no-data { font-size: 12px; color: #94a3b8; font-style: italic; }

.risk-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.risk-table th { background: #f1f5f9; text-align: left; padding: 8px 12px; color: #64748b; font-weight: 600; }
.risk-table td { border-bottom: 1px solid #e2e8f0; padding: 10px 12px; vertical-align: middle; }
.td-title { max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500; }
.source-bdg { background: #e2e8f0; font-size: 11px; padding: 2px 6px; border-radius: 4px; color: #475569; }
.rk-tag { font-size: 11px; padding: 2px 6px; border-radius: 4px; color: white; display: inline-block; }
.rk-tag.high { background: #dc2626; } .rk-tag.mid { background: #ea580c; }
.safe-placeholder { text-align: center; padding: 30px; border: 1px dashed #e2e8f0; color: #10b981; background: #f0fdf4; border-radius: 8px; font-weight: 600; }

/* 策略建议 */
.strategy-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.strat-card { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.strat-head { padding: 10px 15px; font-weight: 700; color: white; font-size: 13px; }
.strat-card.def .strat-head { background: #0f172a; }
.strat-card.off .strat-head { background: #3b82f6; }
.strat-body { padding: 15px; font-size: 13px; line-height: 1.5; color: #334155; height: 80px; }

.rpt-footer { margin-top: auto; padding-top: 40px; text-align: center; }
.ft-line { height: 4px; background: #0f172a; margin-bottom: 14px; width: 40px; margin: 0 auto 14px auto; }
.ft-info { font-size: 12px; color: #94a3b8; display: flex; flex-direction: column; gap: 4px; text-transform: uppercase; letter-spacing: 1px; }

/* New Styles */
.close-btn-floating {
    position: absolute; right: 20px; top: 20px; 
    background: none; border: none; font-size: 24px; color: #cbd5e1; 
    cursor: pointer; z-index: 10;
}
.close-btn-floating:hover { color: #64748b; }

.analysis-metrics-banner {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; margin-top: 24px;
    padding: 20px;
}
.amb-header { font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 16px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
.amb-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; row-gap: 20px; }
.amb-item { display: flex; flex-direction: column; overflow: hidden; } /* Prevent overflow */
.amb-item.wide { grid-column: span 4; }

.amb-label { font-size: 12px; color: #64748b; margin-bottom: 4px; white-space: nowrap; }
.amb-val { 
    font-size: 20px; font-weight: 800; color: #0f172a; 
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    max-width: 100%;
}
.amb-val.text-red { color: #dc2626; }
.amb-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }
.amb-tag { background: #fee2e2; color: #991b1b; padding: 2px 10px; border-radius: 4px; font-size: 13px; font-weight: 500; }

.rpt-sentiment-bar { width: 100%; display: flex; flex-direction: column; gap: 4px; margin-top: 4px; }
.rsb-track { display: flex; height: 8px; border-radius: 4px; overflow: hidden; background: #e2e8f0; width: 100%; }
.rsb-seg { height: 100%; }
.rsb-legend { font-size: 12px; font-weight: 700; display: flex; gap: 4px; }

.deep-analysis-box { display: flex; flex-direction: column; gap: 20px; }
.da-item { background: #fff; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.da-item.highlight { background: #eff6ff; border-color: #dbeafe; }
.da-title { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
.da-content { font-size: 14px; line-height: 1.6; color: #334155; text-align: justify; }

@media print {
  .no-print { display: none !important; }
  .report-overlay { position: static; background: none; padding: 0; display: block; }
  .report-paper { box-shadow: none; width: 100%; min-height: auto; }
  body { background: white; -webkit-print-color-adjust: exact; }
}
</style>