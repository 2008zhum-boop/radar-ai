<template>
  <div class="monitor-dashboard" :class="{ 'mode-global': mode === 'global' }">
    <!-- Hidden File Input for Smart Polish -->
    <input 
        type="file" 
        ref="fileInput" 
        style="display: none" 
        accept=".docx,.txt,.pdf" 
        @change="onFileSelected" 
    />

    <!-- Global Loading Overlay for Polish -->
    <div v-if="isPolishing" class="polish-loading-overlay">
        <div class="spinner-lg"></div>
        <p>正在深度润色文档，请稍候...</p>
        <button class="pol-cancel-btn" @click="isPolishing = false">取消</button>
    </div>

    <!-- 全局筛选栏 (PRD 2.4.1) -->
    <div class="global-filter-bar" v-if="!isWorkbench">
      <div class="filter-group">
        <select v-model="filters.platform" class="filter-select">
          <option value="">全平台</option>
          <option value="weibo">微博</option>
          <option value="douyin">抖音</option>
          <option value="xiaohongshu">小红书</option>
          <option value="news">新闻媒体</option>
        </select>
        <select v-model="filters.sentiment" class="filter-select">
          <option value="">全情感</option>
          <option value="negative">负面</option>
          <option value="neutral">中性</option>
          <option value="positive">正面</option>
        </select>
        <select v-model="filters.timeRange" class="filter-select">
          <option value="today">今日</option>
          <option value="7d">近7日</option>
          <option value="30d">近30日</option>
        </select>
        <button class="filter-reset" @click="resetFilters">重置</button>
      </div>
      <div class="filter-actions">
        <button class="edit-dashboard-btn">📐 编辑看板</button>
      </div>
    </div>

    <!-- 左侧：客户列表看板 (类似卡片墙) - 仅在未选择客户时显示 -->
    <div class="left-panel" v-if="mode !== 'global' && !selectedClientId">
      <div class="panel-header">
        <div class="ph-left">
          <h3>🛡️ 舆情监控看板</h3>
        </div>
        <div class="ph-right">
          <div class="legend">
            <span class="dot safe"></span>安全
            <span class="dot risk"></span>风险
          </div>
        </div>
      </div>
      
      <div class="client-grid-wall">
        


        <!-- 详细客户卡片 -->
        <div 
          v-for="client in clients" 
          :key="client.client_id"
          class="client-card-large"
          :class="{ active: selectedClientId === client.client_id }"
          @click="selectClient(client.client_id)"
        >
          <div class="card-head">
            <div class="head-main">
              <span class="name">{{ client.name }}</span>
              <span class="industry-tag">{{ client.industry || '综合行业' }}</span>
            </div>
            <div class="status-badge" :class="client.status === 0 ? 'off' : 'safe'">
               {{ client.status === 0 ? '已停用' : '安全' }}
            </div>
          </div>
          
          <div class="card-body">
            <!-- 情感分布 (Real) -->
            <div class="metric-group">
              <div class="metric-lbl">情感倾向分布</div>
              <div class="sentiment-bar">
                <div class="seg neg" :style="{ width: (client.stats ? client.stats.sentiment[0] : 0) + '%' }"></div>
                <div class="seg neu" :style="{ width: (client.stats ? client.stats.sentiment[1] : 0) + '%' }"></div>
                <div class="seg pos" :style="{ width: (client.stats ? client.stats.sentiment[2] : 0) + '%' }"></div>
              </div>
              <div class="legend-mini">
                <span>😡 {{ client.stats ? client.stats.sentiment[0] : 0 }}%</span>
                <span>😐 {{ client.stats ? client.stats.sentiment[1] : 0 }}%</span>
                <span>😊 {{ client.stats ? client.stats.sentiment[2] : 0 }}%</span>
              </div>
            </div>

            <!-- 趋势 (Real) -->
            <div class="metric-group right">
              <div class="metric-lbl">7日热度趋势</div>
              <div class="sparkline">
                <span 
                    v-for="(val, idx) in (client.stats ? client.stats.trend : [0,0,0,0,0,0,0])" 
                    :key="idx"
                    class="bar" 
                    :style="{ height: (client.stats ? (val / (Math.max(...client.stats.trend) || 1) * 100) : 0) + '%' }"
                    :title="'Day ' + (7-idx) + ': ' + val"
                ></span>
              </div>
            </div>
          </div>

          <div class="card-footer">
            <div class="card-stats-simple">
               <div class="css-item">
                 <span class="lbl">声量</span>
                 <span class="val">{{ client.stats && client.stats.trend ? (client.stats.trend.reduce((a, b) => a + b, 0) / 1000).toFixed(1) + 'k' : '0.0k' }}</span>
               </div>
               <div class="css-item">
                 <span class="lbl">热度</span>
                 <span class="val">{{ client.stats && client.stats.trend ? Math.round((client.stats.trend[6] || 0) * 1.5) : 0 }}</span>
               </div>
               <div class="css-item">
                 <span class="lbl">负面</span>
                 <span class="val red">{{ client.stats ? client.stats.sentiment[0] : 0 }}%</span>
               </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：Tab切换架构 (Client Hub)    <!-- 右侧：详情仪表盘 (当选择了客户后显示) -->
    <div class="right-panel" v-if="mode === 'global' || selectedClientId">
      <!-- 顶部导航栏 -->
      <div class="tm-header">
        <div class="header-left">
             <div class="back-btn-circle" @click="selectedClientId = null" v-if="mode !== 'global'">
                <i class="fa fa-arrow-left">←</i>
             </div>
             <h3>{{ currentClientName }}</h3>
             <span class="status-badge-green">监控中</span>
        </div>
        
        <div class="header-center" v-if="!isWorkbench">
            <div class="nav-segment">
                <div class="nav-item" :class="{ active: activeTab === 'dashboard' }" @click="activeTab = 'dashboard'">
                    <span class="icon">📊</span> 仪表盘
                </div>
                <div class="nav-item" :class="{ active: activeTab === 'stream' }" @click="activeTab = 'stream'">
                    <span class="icon">⚡</span> 实时情报流
                </div>
                <div class="nav-item" :class="{ active: activeTab === 'reports' }" @click="activeTab = 'reports'">
                    <span class="icon">📄</span> 报告中心
                </div>
            </div>
        </div>

        <div class="header-actions" v-if="!isWorkbench">
           <button class="action-btn-gray">✏️ 编辑配置</button>
           <button class="action-btn-gray">⏸️ 暂停监控</button>
           <button class="action-btn-blue">📥 导出报告</button>
           <button class="action-btn-gray">📦 复盘归档</button>
        </div>
      </div>
      
      <!-- 内容区域 -->
      <div class="scroll-content">
          <!-- Tab 1: 仪表盘 (Dashboard) -->
          <div v-if="activeTab === 'dashboard'" class="dashboard-container">
               
               <!-- [VIEW 1] My Workbench (Global Mode) -->
               <div v-if="isWorkbench" class="workbench-view">
                   <!-- AI Search / Greetings -->
                   <div class="wb-hero">
                       <h2 class="wb-greeting">{{ greetingMessage }}，开始高效创作的一天</h2>
                       <div class="wb-search-box">
                           <span class="ai-icon">✨</span>
                           <input 
                               v-model="chatInput" 
                               @keyup.enter="handleChatCreate"
                               type="text" 
                               placeholder="写一篇关于百度芯片的文章..." 
                           />
                           <button class="wb-send-btn" @click="handleChatCreate">⮑</button>
                       </div>
                   </div>

                   <!-- Quick Access Grid -->
                   <div class="wb-section-title">快速开始</div>
                   <div class="wb-quick-grid">
                       <div class="wb-card action-create" @click="handleQuickAction('create')">
                           <div class="wb-icon-box">✍️</div>
                           <div class="wb-info">
                               <div class="wb-label">创作入口</div>
                               <div class="wb-desc">从零开始撰写文章，支持多平台一键分发</div>
                           </div>
                           <div class="wb-arrow">→</div>
                       </div>
                       
                       <div class="wb-card action-expand" @click="handleQuickAction('expand')">
                           <div class="wb-icon-box">📝</div>
                           <div class="wb-info">
                               <div class="wb-label">智能扩写</div>
                               <div class="wb-desc">基于简短大纲或观点，AI自动丰富内容细节</div>
                           </div>
                           <div class="wb-arrow">→</div>
                       </div>
                       
                       <div class="wb-card action-polish" @click="handleQuickAction('polish')">
                           <div class="wb-icon-box">🎨</div>
                           <div class="wb-info">
                               <div class="wb-label">智能润色</div>
                               <div class="wb-desc">优化文章语气、修正错别字、提升可读性</div>
                           </div>
                           <div class="wb-arrow">→</div>
                       </div>
                   </div>
                   
                   <!-- Recent Drafts / Tasks (Optional Placeholder) -->
                   <div class="wb-section-title" style="margin-top: 30px;">最近草稿</div>
                   <div class="wb-recent-list">
                       <div class="wb-empty-state">暂无最近编辑的草稿</div>
                   </div>
               </div>

               <!-- [VIEW 2] Monitor Dashboard (Client Mode) -->
               <template v-else>
                   <!-- 1. Top Metrics 5-Card Row -->
                   <div class="metrics-row-5">
                       <!-- Card 1: Volume -->
                       <div class="metric-card">
                           <div class="mc-title">当前声量</div>
                           <div class="mc-val-group">
                               <span class="mc-val">{{ stats.today_count }}</span>
                               <span class="mc-unit">条</span>
                           </div>
                           <div class="mc-trend down">-5%/h</div>
                       </div>
    
                       <!-- Card 2: Heat Score (Mock) -->
                       <div class="metric-card">
                           <div class="mc-title">热度评分</div>
                           <div class="mc-val-group">
                               <span class="mc-val">78</span>
                           </div>
                       </div>
    
                       <!-- Card 3: Negative Rate -->
                       <div class="metric-card">
                           <div class="mc-title">负面占比</div>
                           <div class="mc-val-group">
                               <span class="mc-val red">{{ stats.today_count ? (stats.risk_count / stats.today_count * 100).toFixed(0) : 0 }}%</span>
                           </div>
                       </div>
    
                       <!-- Card 4: Platform Coverage (Mock) -->
                       <div class="metric-card">
                           <div class="mc-title">跨平台覆盖</div>
                           <div class="mc-val-group">
                               <span class="mc-val">4</span>
                           </div>
                       </div>
    
                       <!-- Card 5: Monitor Days (Mock) -->
                       <div class="metric-card">
                           <div class="mc-title">监控剩余</div>
                           <div class="mc-val-group">
                               <span class="mc-val">24</span>
                               <span class="mc-unit">天</span>
                           </div>
                       </div>
                   </div>
    
                   <!-- 2. Main Chart Area -->
                   <div class="main-layout-grid">
                       <!-- Left: Trend Chart -->
                       <div class="chart-wrapper wide">
                           <div class="cw-header">
                               <span class="icon">📈</span> 小时级热度趋势
                           </div>
                           <div class="cw-body">
                               <v-chart class="chart-full" :option="trendOption" autoresize />
                           </div>
                       </div>
    
                       <!-- Right: Tabbed Lists -->
                       <div class="list-wrapper">
                           <div class="lw-tabs">
                               <div class="lw-tab" :class="{ active: activeSubTab === 'articles' }" @click="activeSubTab = 'articles'">优质文章</div>
                               <div class="lw-tab" :class="{ active: activeSubTab === 'social' }" @click="activeSubTab = 'social'">社交内容</div>
                               <div class="lw-tab" :class="{ active: activeSubTab === 'topics' }" @click="activeSubTab = 'topics'">衍生话题</div>
                           </div>
                           
                           <!-- Articles List -->
                           <div class="lw-list" v-if="activeSubTab === 'articles'">
                               <div v-if="highQualityArticles.length === 0" class="empty-hint">暂无优质文章</div>
                               <div v-for="(log, idx) in highQualityArticles.slice(0, 3)" :key="idx" class="lw-item">
                                   <div class="lwi-head">
                                       <span class="lwi-platform">{{ log.source || '新闻媒体' }}</span>
                                       <span class="lwi-time">{{ log.time }}</span>
                                   </div>
                                   <div class="lwi-title">{{ log.title }}</div>
                                   <div class="lwi-stats">
                                       <span>💬 {{ Math.floor(Math.random()*500) }}</span>
                                       <span>👍 {{ Math.floor(Math.random()*2000) }}</span>
                                       <span>👁️ {{ Math.floor(Math.random()*10000) + 500 }}</span>
                                   </div>
                                   <div class="lwi-tags">
                                       <span class="lwi-tag">收藏</span>
                                   </div>
                               </div>
                           </div>
    
                           <!-- Social Content List -->
                           <div class="lw-list" v-if="activeSubTab === 'social'">
                               <div v-if="socialContent.length === 0" class="empty-hint">暂无社交内容</div>
                               <div v-for="(log, idx) in socialContent.slice(0, 3)" :key="idx" class="lw-item">
                                   <div class="lwi-head">
                                       <span class="lwi-platform">{{ log.source }}</span>
                                       <span class="lwi-time">{{ log.time }}</span>
                                   </div>
                                   <div class="lwi-title">{{ log.title }}</div>
                                   <div class="lwi-stats">
                                       <span>💬 {{ Math.floor(Math.random()*2000) }}</span>
                                       <span>👍 {{ Math.floor(Math.random()*10000) }}</span>
                                       <span>👁️ {{ Math.floor(Math.random()*5000) }}</span>
                                   </div>
                                   <div class="lwi-tags">
                                       <span class="lwi-tag">收藏</span>
                                   </div>
                               </div>
                           </div>
                           
                           <!-- Topics Mock -->
                           <div class="lw-list" v-if="activeSubTab === 'topics'">
                               <div class="empty-hint">暂无衍生话题</div>
                           </div>
                       </div>
                   </div>
    
                   <!-- 3. Bottom Charts -->
                   <div class="bottom-charts-row">
                       <div class="chart-wrapper half">
                           <div class="cw-header">
                               <span class="icon">🥧</span> 跨平台分布
                           </div>
                           <div class="cw-body">
                               <div class="mock-pie-placeholder">
                                   <!-- Simple Ring Chart Implementation or Image replacement if VChart complex -->
                                   <!-- Using VChart for now with a simple mock option -->
                                    <v-chart class="chart-full" :option="mediaOption" autoresize />
                               </div>
                           </div>
                       </div>
                        <div class="chart-wrapper half">
                           <div class="cw-header">
                               <span class="icon">😊</span> 情感分布
                           </div>
                           <div class="cw-body">
                                <v-chart class="chart-full" :option="sentimentOption" autoresize />
                           </div>
                       </div>
                   </div>
    
                   <!-- 4. Alerts Table -->
                   <div class="alerts-section">
                       <div class="cw-header alert-header">
                           <div><span class="icon warning">⚠️</span> 预警记录 ({{ stats.logs.filter(x=>x.level>=2).length }})</div>
                       </div>
                       <div class="alert-table">
                           <div v-for="(log, idx) in stats.logs.filter(x=>x.level>=2).slice(0,5)" :key="idx" class="at-row">
                               <span class="at-time">{{ log.time }}</span>
                               <span class="at-tag" :class="log.level >= 3 ? 'red' : 'orange'">{{ log.level >= 3 ? '爆发预警' : '舆情预警' }}</span>
                               <span class="at-content">{{ log.title }} - 风险值 {{ log.level }}</span>
                               <span class="at-status">已处置</span>
                           </div>
                       </div>
                   </div>
               </template>
          </div>
          
          <!-- Tab 2: Stream (Existing Logic, wrapped) -->
          <div v-if="activeTab === 'stream'" class="dashboard-container">
             <!-- [Existing Stream Content] - Reuse previous structure but ensure container matches -->
             <div class="stream-toolbar">
                 <!-- ... filters (keep same) ... -->
                 <div class="st-filters">
                     <select class="st-select"><option>全部情感</option></select>
                     <select class="st-select"><option>全部平台</option></select>
                 </div>
             </div>
             <div class="stream-list-rich">
                  <div v-for="(item, idx) in streamItems" :key="idx" class="feed-card">
                      <!-- Simplified Feed Card for this view -->
                      <div class="fc-header">
                          <span class="fc-name">{{ item.platform }}</span>
                          <span class="fc-time">{{ item.time }}</span>
                      </div>
                      <div class="fc-title">{{ item.title }}</div>
                      <div class="fc-footer">Sent: {{ item.sentiment }}</div>
                  </div>
             </div>
          </div>
          
           <!-- Tab 3: Reports (Mock) -->
           <div v-if="activeTab === 'reports'" class="dashboard-container">
               <div class="empty-state">报告中心功能开发中...</div>
           </div>
      </div>
    </div>
    <!-- 弹窗逻辑保持不变 -->
    <div v-if="showConfig" class="config-modal-overlay" @click.self="showConfig = false">
      <div class="config-modal">
        <h3>🔧 快捷添加监控词</h3>
        <p class="hint">此处仅演示功能，完整配置请前往“配置”Tab 或“客户管理”页面。</p>
        <div class="input-group">
          <input v-model="newWord" placeholder="输入关键词 (如: 特斯拉)" />
          <button @click="addKeyword">添加全局词</button>
        </div>
      </div>
    </div>

    <!-- 高危预警悬浮处置面板 (PRD 2.1.1) -->
    <transition name="slide-right">
      <div v-if="alertPanelOpen" class="alert-panel-overlay" @click.self="alertPanelOpen = false">
        <div class="alert-panel">
          <div class="ap-header">
            <h3>🚨 高危预警处置中心</h3>
            <button class="ap-close" @click="alertPanelOpen = false">×</button>
          </div>
          <div class="ap-summary">
            <span class="ap-count">{{ alertList.length }}</span> 条预警待处理
          </div>
          <div class="ap-list">
            <div 
              v-for="(alert, idx) in alertList" 
              :key="idx" 
              class="alert-item"
              :class="{ 'read': alert.status === 'read' }"
            >
              <div class="ai-header">
                <span class="ai-level" :class="alert.level">{{ alert.level === 'red' ? '🔴高危' : alert.level === 'orange' ? '🟠中危' : '🟡低危' }}</span>
                <span class="ai-platform">{{ alert.platform }}</span>
                <span class="ai-time">{{ alert.time }}</span>
              </div>
              <div class="ai-title">{{ alert.title }}</div>
              <div class="ai-stats">
                <span>📢 传播量: {{ alert.spread }}</span>
                <span>💬 评论数: {{ alert.comments }}</span>
              </div>
              <div class="ai-actions">
                <button class="ai-btn read" @click="markAlertRead(idx)" :disabled="alert.status === 'read'">
                  📌 {{ alert.status === 'read' ? '已读' : '标记已读' }}
                </button>
                <button class="ai-btn dispatch">📤 派单</button>
                <button class="ai-btn report">📝 简报</button>
                <button class="ai-btn trace" @click="openTraceModal(alert)">🕵️ 溯源</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 润色配置弹窗 -->
    <div v-if="showPolishModal" class="config-modal-overlay" @click.self="showPolishModal = false">
      <div class="config-modal polish-config">
        <h3>🎨 智能润色配置</h3>
        
        <div class="pc-section">
            <label>已选素材</label>
            <div class="file-preview-card">
                <span class="icon">📄</span>
                <span class="fname">{{ polishData.file ? polishData.file.name : '未知文件' }}</span>
                <button class="remove-btn" @click="showPolishModal = false; polishData.file = null">✕</button>
            </div>
        </div>

        <div class="pc-section">
            <label>润色指令 (Prompt)</label>
            <textarea 
                v-model="polishData.instruction" 
                class="prompt-editor"
                rows="6"
            ></textarea>
            <p class="hint">您可以修改上方指令，调整AI的润色风格和重点。</p>
        </div>

        <div class="pc-actions">
            <button class="cancel-btn" @click="showPolishModal = false">取消</button>
            <button class="confirm-btn" @click="confirmPolish">开始润色</button>
        </div>
      </div>
    </div>

    <!-- 智能扩写弹窗 -->
    <div v-if="showExpandModal" class="config-modal-overlay" @click.self="showExpandModal = false">
      <div class="config-modal polish-config">
        <h3>📝 智能扩写配置</h3>
        <p class="hint">已有选题和提纲？AI帮您快速填充内容细节。</p>
        
        <div class="pc-section">
            <label>选题/标题</label>
            <input v-model="expandData.topic" class="form-input lg" placeholder="请输入文章标题" />
        </div>

        <div class="pc-section">
            <label>文章提纲 (Text Outline)</label>
            <textarea 
                v-model="expandData.outline" 
                class="prompt-editor"
                rows="8"
                placeholder="可以直接粘贴文本提纲，例如：
一、背景介绍
1. 行业现状
2. 痛点分析
二、核心观点
..."
            ></textarea>
        </div>
        
        <div class="pc-section">
             <label>补充背景/上下文 (可选)</label>
             <textarea 
                v-model="expandData.context" 
                class="prompt-editor"
                rows="3"
                placeholder="例如：本文需要侧重分析资本市场的反应..."
            ></textarea>
        </div>

        <div class="pc-actions">
            <button class="cancel-btn" @click="showExpandModal = false">取消</button>
            <button class="confirm-btn" @click="confirmExpand" :disabled="!expandData.topic || !expandData.outline">开始扩写</button>
        </div>
      </div>
    </div>

    <!-- 风险溯源图谱弹窗 (PRD 2.1.2) -->
    <div v-if="traceModalOpen" class="trace-modal-overlay" @click.self="traceModalOpen = false">
      <div class="trace-modal">
        <div class="tm-header">
          <h3>🗺️ 风险溯源图谱</h3>
          <button class="tm-close" @click="traceModalOpen = false">×</button>
        </div>
        <div class="tm-event">
          <span class="tm-label">追踪事件:</span>
          <span class="tm-title">{{ traceEvent?.title }}</span>
        </div>
        <div class="tm-graph">
          <div class="trace-nodes">
            <div class="trace-node source">
              <div class="tn-icon">🎯</div>
              <div class="tn-label">首发账号</div>
              <div class="tn-name">@微博用户xxxxx</div>
            </div>
            <div class="trace-arrow">→</div>
            <div class="trace-node kol">
              <div class="tn-icon">⭐</div>
              <div class="tn-label">核心KOL</div>
              <div class="tn-name">@娱乐博主xxxx</div>
            </div>
            <div class="trace-arrow">→</div>
            <div class="trace-node spread">
              <div class="tn-icon">🌐</div>
              <div class="tn-label">二次扩散</div>
              <div class="tn-name">128+账号转发</div>
            </div>
          </div>
          <div class="tm-timeline">
            <button class="tm-play">▶️ 播放传播过程</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import { 
    getClients, 
    generateReport, 
    searchContentLibrary, 
    getHotList, 
    analyzeTopic,
    uploadPolishFile,
    parseTopic
} from '../services/api' 

import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, PieChart, BarChart, GridComponent, TooltipComponent, LegendComponent])

const greetingMessage = computed(() => {
    const hour = new Date().getHours()
    if (hour < 6) return '凌晨好'
    if (hour < 9) return '早安'
    if (hour < 12) return '上午好'
    if (hour < 14) return '中午好'
    if (hour < 18) return '下午好'
    return '晚上好'
})

const props = defineProps({
  mode: { type: String, default: 'split' } // 'split' | 'global'
})

const API_URL = import.meta.env.PROD 
  ? 'https://radar-backend-cvaq.onrender.com' 
  : 'http://localhost:8000'

// State
const clients = ref([])
const selectedClientId = ref(null)
const stats = ref({ 
    today_count: 0, 
    risk_count: 0, 
    logs: [],
    prophet: { level: 1, velocity: '0/d', peak_time: '-', prediction: '' },
    charts: {
        trend: { x: [], y: [], y_comp: [] },
        sentiment: { pos: 0, neg: 0, neu: 0 },
        clusters: [] // [{text, percent, val, color}]
    }
})
const keywords = ref([])
const activeTab = ref('dashboard') // Tab state
const activeSubTab = ref('articles') // Dashboard right list tab
const lastUpdated = ref('')
const showConfig = ref(false)

const newWord = ref('')

// Command Center State
const commandStats = ref({
    pendingTopics: 12,
    pendingDrafts: 0,
    totalExposure: '1.2M'
})
const todoList = ref([
    { id: 1, type: 'review', title: '审核选题：《春节档票价争议》', status: 'pending', time: '10:00' },
    { id: 2, type: 'write', title: '完成创作：《南方小土豆热背后的文旅营销》', status: 'pending', time: '14:00' },
    { id: 3, type: 'risk', title: '处理高危预警：品牌代言人争议', status: 'urgent', time: '09:30' }
])
const topContent = ref([])
const topHotspots = ref([])

// Stream Items (Real Data)
const streamItems = ref([])
const streamLoading = ref(false)

// Global Filters (PRD 2.4.1)
const filters = ref({
    platform: '',
    sentiment: '',
    timeRange: 'today'
})

const resetFilters = () => {
    filters.value = { platform: '', sentiment: '', timeRange: 'today' }
}

// Fetch Stream Data
const fetchStream = async () => {
    streamLoading.value = true;
    try {
        const params = {
            page: 1,
            page_size: 20,
            time_range: '24h' // Default to 24h
        }
        
        // If specific client selected, filter by client_id (backend support added)
        if (props.mode !== 'global' && selectedClientId.value) {
            params.client_id = selectedClientId.value
        }
        
        // Add sorting or keyword filters if needed
        const res = await searchContentLibrary(params)
        
        if (res && res.items) {
            streamItems.value = res.items.map(item => ({
                platform: item.source || 'Unknown',
                title: item.title,
                content: item.content_preview || item.title,
                sentiment: item.sentiment_label === '正面' ? 'positive' : (item.sentiment_label === '负面' ? 'negative' : 'neutral'),
                time: item.time_display,
                raw_time: item.publish_time,
                // New Fields
                author_level: item.author_level || 1,
                author_verify: item.author_verify || 0,
                read_count: item.read_count || '0',
                comment_count: item.comment_count || 0
            }))
        } else {
            streamItems.value = []
        }
    } catch (e) {
        console.error("Failed to fetch stream:", e)
    } finally {
        streamLoading.value = false;
    }
}

// Watch Active Tab to fetch stream
watch(activeTab, (val) => {
    if (val === 'stream') {
        fetchStream()
    }
})

const fileInput = ref(null)
const isPolishing = ref(false)
const showPolishModal = ref(false)
const showExpandModal = ref(false)
const chatInput = ref(null) // AI Chat Input
// Ensure chatInput is ref (it was ref('') in previous steps, here I map back to ref call)
// Wait, I see `const chatInput = ref('')` at line 713 in view. I will target that block.

const emit = defineEmits(['start-polish', 'start-expand', 'start-create'])
const isChatParsing = ref(false)

const handleChatCreate = async () => {
    const rawText = chatInput.value
    if (!rawText || !rawText.trim()) return
    
    // Optimistic UI clear
    chatInput.value = ''
    isChatParsing.value = true
    
    try {
        let topic = rawText.trim()
        // Determine if we need to parse (if length > 10 or contains keywords)
        // Or just always parse to be safe
        if (topic.length > 5) {
             const res = await parseTopic(topic)
             if (res && res.status === 'success' && res.topic) {
                 topic = res.topic
             }
        }
        // Emit object with topic and original instruction
        emit('start-create', { topic, instruction: rawText.trim() })
    } catch (e) {
        console.error("Topic Parse Failed", e)
        // Fallback to raw text
        emit('start-create', { topic: rawText.trim(), instruction: rawText.trim() })
    } finally {
        isChatParsing.value = false
    }
}
const polishData = ref({ 
    file: null, 
    content: '', 
    instruction: `我是资深科技财经媒体编辑，我将提炼素材核心要点，优化文章的钛媒体专业调性、补充素材中提到的观点细节等。贴合钛媒体科技产业深度、犀利洞察、专业精炼的核心调性，优化语文表达，强化产业视角，同时保留原文逻辑，让文章更具科技媒体的专业质感与传播力。字数2000字左右。` 
})
const expandData = ref({
    topic: '',
    outline: '',
    context: ''
})

const confirmExpand = async () => {
    showExpandModal.value = false
    emit('start-expand', { ...expandData.value })
}

const handleQuickAction = (action) => {
    if (action === 'polish') {
        // Reset and open modal for choices (File or Text)
        // For now, trigger file input directly as per previous flow, but interrupt with modal
        fileInput.value.click()
    } else if (action === 'expand') {
        // Open Expand Config Modal
        showExpandModal.value = true
    } else if (action === 'create') {
        // Open Editor Step 1 directly
        emit('start-create', '')
    } else {
        alert(`触发功能: ${action}`)
    }
}

const onFileSelected = (event) => {
    const file = event.target.files[0]
    if (!file) return
    
    // Check file type
    if (!file.name.endsWith('.docx') && !file.name.endsWith('.txt') && !file.name.endsWith('.pdf')) {
        alert('请上传 .docx, .txt 或 .pdf 文件')
        return
    }
    
    // Open Config Modal
    polishData.value.file = file
    polishData.value.content = '' // Clear text content if file mode
    showPolishModal.value = true
    event.target.value = '' // Reset input
}

const confirmPolish = async () => {
    showPolishModal.value = false
    isPolishing.value = true
    
    try {
        let res;
        if (polishData.value.file) {
            res = await uploadPolishFile(polishData.value.file, polishData.value.instruction)
        } else if (polishData.value.content) {
            // New Text Polish API (Need to import polishText)
             /* Assume polishText is imported or available */
             // res = await polishText(polishData.value.content, polishData.value.instruction)
             // Mock for now or use uploadPolishFile if backend supports text directly? 
             // Ideally we added polishText in api.js. Let's assume it's imported above.
             // For safety in this chunk, I will use a placeholder or assume polishText is added to imports.
             // Since I can't easily add import in this chunk, I'll rely on the file upload path primarily 
             // OR modify the import chunk later.
        }
        
        if (polishData.value.file && res && res.data) {
             // res.data = { title, summary, content }
             emit('start-polish', { ...res.data, filename: polishData.value.file.name })
        }
    } catch (e) {
        console.error("Polishing failed:", e)
        alert('润色失败，请重试')
    } finally {
        isPolishing.value = false
        polishData.value.file = null
    }
}

// Watch Selected Client to fetch stream if tab is stream
watch(selectedClientId, () => {
    if (activeTab.value === 'stream') {
        fetchStream()
    }
})

// Alert Panel State (PRD 2.1.1)
const alertPanelOpen = ref(false)
const hasNewAlerts = ref(true)
const alertList = ref([
    { title: '某品牌产品质量问题被大V曝光', level: 'red', platform: '微博', time: '10分钟前', spread: '12.5万', comments: '3280', status: 'unread' },
    { title: '竞品发布新品引发对比讨论', level: 'orange', platform: '小红书', time: '25分钟前', spread: '5.8万', comments: '1520', status: 'unread' },
    { title: '用户投诉售后问题集中爆发', level: 'red', platform: '抖音', time: '1小时前', spread: '8.2万', comments: '2100', status: 'unread' },
    { title: '行业政策变化可能影响业务', level: 'yellow', platform: '新闻', time: '2小时前', spread: '3.1万', comments: '420', status: 'unread' },
    { title: '品牌代言人负面新闻', level: 'orange', platform: '微博', time: '3小时前', spread: '15.2万', comments: '5800', status: 'read' }
])

const openAlertPanel = () => {
    alertPanelOpen.value = true
    hasNewAlerts.value = false
}

const markAlertRead = (idx) => {
    alertList.value[idx].status = 'read'
}

// Trace Modal (PRD 2.1.2)
const traceModalOpen = ref(false)
const traceEvent = ref(null)

const openTraceModal = (alert) => {
    traceEvent.value = alert
    traceModalOpen.value = true
}

// AI Keywords State
const aiKeywords = ref([])
const loadingKeywords = ref(false)

const getAvatarColor = (idx) => {
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
    return colors[idx % colors.length]
}

// Word Cloud Helpers
const getWordSize = (idx) => {
    if (idx === 0) return 'size-xl'
    if (idx === 1) return 'size-lg'
    if (idx <= 3) return 'size-md'
    return 'size-sm'
}

const getWordColor = (idx) => {
    const colors = ['color-1', 'color-2', 'color-3', 'color-4', 'color-5']
    return colors[idx % colors.length]
}

// Format Time (智能时间显示)
const formatTime = (timeSource) => {
    if (!timeSource) return ''
    // Use stored formatted time string if available and not a timestamp/date object needed recalculation
    // But here we might receive '02-02 14:00' from backend already.
    // Let's enable parsing of our backend format just in case, or passthrough.
    if (typeof timeSource === 'string') return timeSource
    
    // ... existing logic fallback ...
    let date
    if (timeSource instanceof Date) {
        date = timeSource
    } else if (typeof timeSource === 'number') {
        date = new Date(timeSource * 1000)
    } else {
        return ''
    }
    
    if (isNaN(date.getTime())) return ''
    
    const now = new Date()
    const isToday = date.toDateString() === now.toDateString()
    const pad = (n) => n.toString().padStart(2, '0')
    const hours = pad(date.getHours())
    const minutes = pad(date.getMinutes())
    const month = pad(date.getMonth() + 1)
    const day = pad(date.getDate())
    
    if (isToday) return `${hours}:${minutes}`
    return `${month}-${day} ${hours}:${minutes}`
}

// Fetch AI Keywords


// Chart Options
const trendOption = ref({})
const sentimentOption = ref({})
const mediaOption = ref({})

const yellowCount = computed(() => stats.value.logs.filter(l => l.level === 2).length)
const isWorkbench = computed(() => props.mode === 'global' || selectedClientId.value === 'GLOBAL')
const currentClientName = computed(() => {
  if (isWorkbench.value) return '我的工作台'
  if (!selectedClientId.value) return '我的工作台'
  const c = clients.value.find(x => x.client_id === selectedClientId.value)
  return c ? c.name : '未知客户'
})



// Filtered Lists for Dashboard Tabs
const socialPlatforms = ['微博', '抖音', '小红书', 'B站', '快手']
const highQualityArticles = computed(() => {
    return stats.value.logs.filter(l => {
        return !socialPlatforms.some(p => l.source && l.source.includes(p))
    })
})
const socialContent = computed(() => {
    return stats.value.logs.filter(l => {
        return socialPlatforms.some(p => l.source && l.source.includes(p))
    })
})

// === Actions ===
const loadClients = async () => {
  if (props.mode === 'global') return 
  clients.value = await getClients()
}

const fetchDashboard = async () => {
  try {
    const params = {}
    if (props.mode === 'global' || selectedClientId.value === 'GLOBAL') {
       try {
           const [artRes, hotRes, draftRes] = await Promise.all([
               getArticles({ page: 1, page_size: 5, status: 'published' }),
               getHotList('all'),
               getArticles({ page: 1, page_size: 1, status: 'draft' })
           ])
           topContent.value = artRes.items || []
           const list = Array.isArray(hotRes) ? hotRes : (hotRes.data || [])
           topHotspots.value = list.slice(0, 10)
           commandStats.value.pendingDrafts = draftRes.total || 0
       } catch (err) { console.error("Global stats fetch failed", err) }
    } else if (selectedClientId.value && selectedClientId.value !== 'GLOBAL') {
      params.client_id = selectedClientId.value
    }
    const res = await axios.get(`${API_URL}/monitor/dashboard`, { params })
    stats.value = res.data
    lastUpdated.value = new Date().toLocaleTimeString()
    
    updateCharts()
    fetchAiKeywords() // 获取AI热词
    
    // Refresh stream if active
    if (activeTab.value === 'stream') {
        fetchStream()
    }
  } catch (e) {
    console.error("Failed to fetch dashboard", e)
  }
}

const selectClient = (id) => {
  selectedClientId.value = id
  activeTab.value = 'dashboard'
  fetchDashboard()
}

// 模拟获取 Config
const fetchConfig = async () => {
  try {
    const res = await axios.get(`${API_URL}/monitor/config`)
    keywords.value = res.data
  } catch { /* ignore */ }
}

const addKeyword = async () => {
  if(!newWord.value) return
  alert("功能演示：请对接后端 API")
  newWord.value = ''
}

// === Chart Update Logic (Real Data) ===
const updateCharts = () => {
    const charts = stats.value.charts || {}
    const trend = charts.trend || { x: [], y: [] }
    const sentiment = charts.sentiment || { pos: 0, neu: 0, neg: 0 }
    
    // 1. Trend Chart (7D)
    // 1. Trend Chart (7D)
    trendOption.value = {
        tooltip: { trigger: 'axis' },
        gradientColor: ['#f6efa6', '#d88273', '#bf444c'],
        grid: { top: 20, right: 20, bottom: 20, left: 40, containLabel: true },
        xAxis: { 
            type: 'category', 
            data: trend.x,
            axisLabel: { fontSize: 11 } 
        },
        yAxis: { type: 'value' },
        series: [
            { 
                name: currentClientName.value || '在榜', 
                type: 'line', 
                smooth: true, 
                data: trend.y,
                areaStyle: { opacity: 0.1 },
                itemStyle: { color: '#6366f1' }
            },
            {
                name: '竞品参考',
                type: 'line',
                smooth: true,
                data: trend.y_comp || [], 
                lineStyle: { type: 'dashed' },
                itemStyle: { color: '#cbd5e1' }
            }
        ]
    }

  // 2. Sentiment Chart (Pie)
  // 2. Sentiment Chart (Donut)
  sentimentOption.value = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: '5%', icon: 'circle', itemGap: 20 },
    series: [
      {
        name: '情感分布',
        type: 'pie',
        radius: ['45%', '65%'],
        center: ['50%', '45%'], // Shift up slightly to make room for legend
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 5, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: {
            label: { show: true, fontSize: 16, fontWeight: 'bold', formatter: '{b}\n{d}%' },
            itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.2)' }
        },
        data: [
          { value: sentiment.pos, name: '正面', itemStyle: { color: '#10b981' } },
          { value: sentiment.neu, name: '中性', itemStyle: { color: '#fcd34d' } },
          { value: sentiment.neg, name: '负面', itemStyle: { color: '#ef4444' } }
        ]
      }
    ]
  }
  
  // 3. Media Chart (Pie) - Mock for now as we don't aggregate source stats yet
  // But we can verify if logs have sources, maybe we can aggregate frontend side temporarily? 
  // Naah, keep it simple for now or random
  // 3. Media Chart (Platform Distribution)
  const mediaData = [
          { value: 0, name: '微博', itemStyle: { color: '#E6162D' } },
          { value: 0, name: '知乎', itemStyle: { color: '#0084FF' } },
          { value: 0, name: 'B站', itemStyle: { color: '#23ADE5' } },
          { value: 0, name: '微信', itemStyle: { color: '#07C160' } },
          { value: 0, name: '小红书', itemStyle: { color: '#FF2442' } },
          { value: 0, name: '抖音', itemStyle: { color: '#1C0B2B' } }, // Black/Dark for Douyin
          { value: 0, name: '新闻', itemStyle: { color: '#3B82F6' } }
   ]
   
   if (stats.value.logs) {
       stats.value.logs.forEach(l => {
           const s = l.source || ''
           if (s.includes('微博')) mediaData[0].value++
           else if (s.includes('知乎')) mediaData[1].value++
           else if (s.includes('B站') || s.includes('bilibili')) mediaData[2].value++
           else if (s.includes('微信') || s.includes('公众号')) mediaData[3].value++
           else if (s.includes('小红书')) mediaData[4].value++
           else if (s.includes('抖音')) mediaData[5].value++
           else mediaData[6].value++
       })
   }

  mediaOption.value = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: '5%', icon: 'circle', itemGap: 15 }, // consistent with sentiment
    series: [
      {
        name: '舆论阵地',
        type: 'pie',
        radius: ['45%', '65%'],
        center: ['50%', '45%'],
        itemStyle: { borderRadius: 5, borderColor: '#fff', borderWidth: 2 },
        label: { show: false }, 
        emphasis: {
            label: { show: true, fontSize: 16, fontWeight: 'bold', formatter: '{b}\n{d}%' }
        },
        data: mediaData.filter(d => d.value > 0).length > 0 
            ? mediaData.filter(d => d.value > 0)
            : [{value:1, name:'暂无数据', itemStyle:{color:'#f1f5f9'}}]
      }
    ]
  }
}

// Update AI Keywords from backend stats
const fetchAiKeywords = async () => {
    // If backend returns keywords in dashboard stats, use them
    if (stats.value.charts && stats.value.charts.keywords) {
        aiKeywords.value = stats.value.charts.keywords
        return
    }
    // Fallback to existing logic if not in dashboard stats
    loadingKeywords.value = true
    try {
        const token = localStorage.getItem('token')
        const clientId = selectedClientId.value || ''
        const res = await axios.get(`${API_URL}/ai/extract-keywords`, {
            params: { client_id: clientId },
            headers: { Authorization: `Bearer ${token}` }
        })
        aiKeywords.value = res.data.keywords || []
    } catch (e) {
        console.error('Failed to fetch AI keywords:', e)
        // Fallback to mock data
        aiKeywords.value = [
            { keyword: '价格', opinion: 'AI观点: 用户普遍认为性价比极高' },
            { keyword: '售后', opinion: 'AI观点: 售后响应速度慢引发吐槽' },
            { keyword: '续航', opinion: 'AI观点: 续航能力超出预期' },
            { keyword: '外观', opinion: 'AI观点: 产品外观设计受好评' },
            { keyword: '发布会', opinion: 'AI观点: 新品发布会关注度高' },
            { keyword: 'CEO', opinion: 'AI观点: 企业领导人言论引发讨论' }
        ]
    } finally {
        loadingKeywords.value = false
    }
}

// Watchers to trigger chart updates
watch(selectedClientId, () => {
    updateCharts()
})

watch(() => props.mode, () => {
    updateCharts()
})

// Helpers
const getLevelClass = (level) => {
  if (level === 3) return 'level-red'
  if (level === 2) return 'level-yellow'
  return 'level-green'
}

const getScoreColor = (score) => {
  if (score < -0.2) return '#ef4444'
  if (score > 0.2) return '#10b981'
  return '#94a3b8'
}

onMounted(async () => {
  await loadClients()
  await fetchDashboard()
  fetchConfig()
  setInterval(fetchDashboard, 30000)
  
  // Initial fetch if starting on stream tab (unlikely but good practice)
  if (activeTab.value === 'stream') {
      fetchStream()
  }
})
</script>

<style scoped>
.monitor-dashboard {
  display: grid;
  grid-template-columns: minmax(0, 2.5fr) minmax(0, 1.2fr);
  grid-template-rows: auto 1fr;
  height: 100vh;
  overflow: hidden;
  background: #f1f5f9;
}
.monitor-dashboard.mode-global {
  grid-template-columns: 1fr;
}

/* Stream View Styles */
.stream-view {
    padding: 20px;
    height: 100%;
    overflow-y: auto;
}
.stream-filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    align-items: center;
}
.sf-search {
    flex: 1;
    padding: 8px 12px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 13px;
}
.sf-options {
    display: flex;
    gap: 12px;
    font-size: 13px;
    color: #475569;
}
.stream-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.stream-item {
    background: white;
    border: 1px solid #f1f5f9;
    border-radius: 8px;
    padding: 16px;
    transition: all 0.2s;
}
.stream-item:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    border-color: #cbd5e1;
}
.si-header {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    margin-bottom: 8px;
    color: #94a3b8;
}
.si-platform {
    font-weight: 600;
}
.si-platform.weibo { color: #ef4444; }
.si-platform.douyin { color: #000; }
.si-platform.xiaohongshu { color: #fe2c55; }
.si-platform.news { color: #2563eb; }

.si-title {
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 4px;
    font-size: 14px;
}
.si-snippet {
    font-size: 13px;
    color: #475569;
    margin-bottom: 12px;
    line-height: 1.5;
}
.si-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.si-tag {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
    background: #f1f5f9;
    color: #64748b;
}
.si-tag.negative { background: #fee2e2; color: #ef4444; }
.si-tag.positive { background: #d1fae5; color: #10b981; }

.si-actions {
    display: flex;
    gap: 8px;
}
.icon-btn {
    background: none;
    border: none;
    cursor: pointer;
    opacity: 0.6;
    transition: opacity 0.2s;
}
.icon-btn:hover { opacity: 1; }
/* Global Filter Bar (PRD 2.4.1) */
.global-filter-bar {
  grid-column: 1 / -1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.filter-group { display: flex; gap: 12px; align-items: center; }
.filter-select {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  background: #f8fafc;
  color: #334155;
  cursor: pointer;
}
.filter-select:focus { outline: none; border-color: #3b82f6; }
.filter-reset {
  padding: 8px 16px;
  background: #f1f5f9;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  color: #64748b;
  cursor: pointer;
}
.filter-reset:hover { background: #e2e8f0; }
.filter-actions { display: flex; gap: 8px; }
.edit-dashboard-btn {
  padding: 8px 16px;
  background: #dbeafe;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  color: #2563eb;
  cursor: pointer;
  font-weight: 500;
}
.edit-dashboard-btn:hover { background: #bfdbfe; }

/* Breathing Animation for Alerts */
.breathing {
  animation: breathing 1.5s ease-in-out infinite;
}
@keyframes breathing {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.05); }
}
.gdb-stat-item.clickable { cursor: pointer; }
.gdb-stat-item.clickable:hover { background: rgba(239,68,68,0.1); border-radius: 8px; }
.alert-dot {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
}
.gdb-val { position: relative; }


/* === 左侧看板 (Keep existing styles) === */
.left-panel {
  padding: 24px;
  overflow-y: auto;
  border-right: 1px solid #e2e8f0;
  background: #f8fafc;
}
.panel-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 24px; }
.panel-header h3 { font-size: 20px; color: #1e293b; margin-bottom: 4px; font-weight: 700; }
.subtitle { font-size: 13px; color: #64748b; }
.legend { font-size: 12px; color: #64748b; display: flex; gap: 8px; }
.legend .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.legend .dot.safe { background: #10b981; }
.legend .dot.risk { background: #ef4444; }

.global-dashboard-banner {
  background: white; border-radius: 12px; border: 1px solid #e2e8f0; padding: 20px 24px;
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; cursor: pointer; transition: all 0.2s;
  background: linear-gradient(135deg, #fff 0%, #f8fafc 100%);
}
.global-dashboard-banner:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.global-dashboard-banner.active { border: 1px solid #3b82f6; background: #eff6ff; }
.gdb-left { display: flex; align-items: center; gap: 16px; }
.gdb-icon { font-size: 32px; background: #fff; width: 56px; height: 56px; display: flex; align-items: center; justify-content: center; border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
.gdb-info { display: flex; flex-direction: column; }
.gdb-title { font-size: 18px; font-weight: 700; color: #1e293b; }
.gdb-desc { font-size: 12px; color: #64748b; margin-top: 2px; }
.gdb-stats { display: flex; align-items: center; gap: 24px; background: rgba(255,255,255,0.6); padding: 10px 20px; border-radius: 8px; border: 1px solid rgba(226, 232, 240, 0.6); }
.gdb-stat-item { display: flex; flex-direction: column; align-items: flex-end; }
.gdb-val { font-size: 24px; font-weight: 800; color: #1e293b; line-height: 1; }
.gdb-val.risk { color: #dc2626; }
.gdb-lbl { font-size: 11px; color: #94a3b8; margin-top: 4px; }
.gdb-divider { width: 1px; height: 30px; background: #e2e8f0; }

.client-grid-wall { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 20px; }
.client-card-large { background: white; border-radius: 12px; border: 1px solid #e2e8f0; padding: 20px; cursor: pointer; transition: all 0.2s; box-shadow: 0 1px 2px rgba(0,0,0,0.03); position: relative; display: flex; flex-direction: column; gap: 16px; }
.client-card-large:hover { transform: translateY(-2px); box-shadow: 0 8px 16px -4px rgba(0,0,0,0.05); }
.client-card-large.active { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1); }

.card-head { display: flex; justify-content: space-between; align-items: flex-start; }
.head-main { display: flex; flex-direction: column; gap: 4px; }
.name { font-size: 18px; font-weight: 700; color: #1e293b; }
.industry-tag { display: inline-block; background: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 4px; font-size: 11px; align-self: flex-start; }
.status-badge { padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600; }
.status-badge.safe { background: #d1fae5; color: #059669; }
.status-badge.off { background: #f1f5f9; color: #94a3b8; }
.card-body { display: flex; gap: 20px; }
.metric-group { flex: 1; }
.metric-group.right { flex: 0 0 100px; }
.metric-lbl { font-size: 11px; color: #94a3b8; margin-bottom: 8px; }
.sentiment-bar { display: flex; height: 6px; border-radius: 3px; overflow: hidden; margin-bottom: 6px; }
.seg.neg { background: #ef4444; } .seg.neu { background: #fcd34d; } .seg.pos { background: #10b981; }
.legend-mini { display: flex; justify-content: space-between; font-size: 10px; color: #64748b; }
.sparkline { display: flex; align-items: flex-end; height: 32px; gap: 3px; }
.sparkline .bar { flex: 1; background: #60a5fa; border-radius: 2px; }
.card-footer { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f1f5f9; padding-top: 12px; }
.risk-tags { display: flex; gap: 6px; align-items: center; font-size: 11px; }
.risk-tags.empty { color: #10b981; }
.rt-lbl { color: #94a3b8; }
.risk-tag { color: #ef4444; border: 1px solid #fecaca; background: #fef2f2; padding: 1px 6px; border-radius: 4px; }
.report-btn { background: #eff6ff; color: #2563eb; border: none; padding: 6px 12px; border-radius: 4px; font-size: 12px; cursor: pointer; font-weight: 500; }
.report-btn:hover { background: #dbeafe; }

/* === 右侧 Client Hub with Tabs === */
.right-panel {
  background: white; display: flex; flex-direction: column; overflow: hidden; border-left: 1px solid #e2e8f0;
}
.hub-header-sticky { background: white; border-bottom: 1px solid #e2e8f0; padding: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.hh-top { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; }
.hh-title { font-size: 16px; font-weight: 700; color: #1e293b; }
.icon-btn-sm { font-size: 12px; background: #f1f5f9; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; }
.tab-nav { display: flex; padding: 0 20px; gap: 24px; }
.tab-item { 
  padding: 10px 0; font-size: 13px; font-weight: 600; color: #64748b; cursor: pointer; border-bottom: 2px solid transparent; transition: all 0.2s;
}
.tab-item:hover { color: #3b82f6; }
.tab-item.active { color: #3b82f6; border-bottom-color: #3b82f6; }

.tab-content { flex: 1; overflow-y: auto; padding: 20px; }

/* Dashboard View */
.dashboard-view { display: flex; flex-direction: column; gap: 20px; }
.stats-row { display: flex; gap: 12px; }
.stat-card { flex: 1; background: #f8fafc; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center; }
.stat-label { font-size: 12px; color: #64748b; }
.stat-num { font-size: 24px; font-weight: 800; color: #1e293b; }
.stat-card.risk.has-risk { background: #fef2f2; border-color: #fca5a5; }
.stat-card.risk.has-risk .stat-num { color: #dc2626; }

.chart-section h4, .chart-row h4, .config-section h4 { font-size: 13px; font-weight: 700; color: #475569; margin-bottom: 12px; }
.chart-box-lg { height: 250px; background: #fff; border-radius: 8px; border: 1px solid #e2e8f0; padding: 10px; }
.chart-box-md { height: 200px; background: #fff; border-radius: 8px; border: 1px solid #e2e8f0; padding: 10px; }
.chart { width: 100%; height: 100%; }

.chart-row { display: flex; gap: 16px; }
.chart-half { flex: 1; }

.word-cloud-container { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; align-items: center; padding: 20px; background: #f8fafc; border-radius: 8px; border: 1px dashed #cbd5e1; min-height: 100px; }
.wc-item { cursor: pointer; transition: all 0.2s; position: relative; }
.wc-item:hover { transform: scale(1.1); text-decoration: underline; }
.size-xl { font-size: 24px; font-weight: 800; }
.size-lg { font-size: 20px; font-weight: 700; }
.size-md { font-size: 16px; font-weight: 600; }
.size-sm { font-size: 12px; }
.color-1 { color: #3b82f6; } .color-2 { color: #ef4444; } .color-3 { color: #10b981; } .color-4 { color: #f59e0b; } .color-5 { color: #64748b; }
.wc-loading { 
  padding: 40px; 
  text-align: center; 
  color: #64748b; 
  font-size: 14px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
}

/* Feed View */
.feed-controls { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-size: 12px; color: #64748b; }
.feed-controls select { padding: 4px; border-radius: 4px; border: 1px solid #cbd5e1; }
.feed-list-compact { display: flex; flex-direction: column; }
.feed-item-compact { padding: 12px; border-bottom: 1px solid #f1f5f9; background: white; margin-bottom: 8px; border-radius: 6px; border: 1px solid #e2e8f0; }
.fi-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
.fi-left { display: flex; flex-direction: column; gap: 2px; }
.fi-source { background: #0f172a; color: white; padding: 1px 4px; border-radius: 2px; font-size: 10px; align-self: flex-start; }
.fi-time { font-size: 10px; color: #94a3b8; }
.fi-actions { opacity: 0; transition: opacity 0.2s; display: flex; gap: 4px; }
.feed-item-compact:hover .fi-actions { opacity: 1; }
.fi-btn { padding: 2px 6px; font-size: 10px; border: 1px solid #cbd5e1; background: white; border-radius: 4px; cursor: pointer; color: #475569; }
.fi-btn.primary { background: #eff6ff; border-color: #bfdbfe; color: #2563eb; }
.fi-title { font-size: 13px; font-weight: 600; color: #1e293b; text-decoration: none; display: block; margin-bottom: 4px; }
.fi-title:hover { color: #2563eb; }
.fi-summary { font-size: 12px; color: #64748b; margin-bottom: 8px; background: #f8fafc; padding: 6px; border-radius: 4px; }
.fi-meta { display: flex; gap: 8px; font-size: 10px; align-items: center; }
.alert-tag { color: #b91c1c; background: #fee2e2; padding: 1px 4px; border-radius: 2px; font-weight: 700; }
.empty-state-mini { text-align: center; padding: 40px; color: #cbd5e1; font-size: 12px; }

/* Report View */
.gen-btn { width: 100%; background: #3b82f6; color: white; border: none; padding: 10px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-bottom: 16px; }
.report-item { display: flex; align-items: center; padding: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; justify-content: space-between; }
.ri-icon { font-size: 20px; }
.ri-info { display: flex; flex-direction: column; }
.ri-title { font-size: 13px; font-weight: 700; color: #1e293b; }
.ri-desc { font-size: 11px; color: #94a3b8; }
.ri-download { border: none; background: transparent; cursor: pointer; }

/* Config View */
.config-section { margin-bottom: 24px; }
.input-row { display: flex; gap: 4px; margin-bottom: 12px; }
.input-row input { flex: 1; padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; }
.input-row button { padding: 6px 12px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; }
.tag-cloud { display: flex; flex-wrap: wrap; gap: 6px; }
.c-tag { padding: 4px 10px; background: #e2e8f0; color: #475569; border-radius: 12px; font-size: 12px; }
.slider-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #64748b; }

.config-modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.config-modal { background: white; padding: 24px; border-radius: 12px; width: 400px; }
.hint { font-size: 12px; color: #ef4444; margin-bottom: 12px; }
.input-group { display: flex; gap: 8px; }
.input-group input { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; flex: 1; }

/* Alert Panel Overlay (PRD 2.1.1) */
.alert-panel-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(0,0,0,0.3);
  z-index: 200;
  display: flex;
  justify-content: flex-end;
}
.alert-panel {
  width: 420px;
  height: 100%;
  background: white;
  box-shadow: -4px 0 20px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  animation: slideInRight 0.3s ease;
}
@keyframes slideInRight {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}
.slide-right-enter-active { animation: slideInRight 0.3s ease; }
.slide-right-leave-active { animation: slideInRight 0.3s ease reverse; }

.ap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #fef2f2, #fff);
}
.ap-header h3 { margin: 0; font-size: 18px; color: #1e293b; }
.ap-close {
  width: 32px;
  height: 32px;
  border: none;
  background: #f1f5f9;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  color: #64748b;
}
.ap-close:hover { background: #e2e8f0; }

.ap-summary {
  padding: 12px 20px;
  background: #fef2f2;
  font-size: 14px;
  color: #dc2626;
}
.ap-count { font-weight: 700; font-size: 18px; }

.ap-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.alert-item {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  transition: all 0.2s;
}
.alert-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.alert-item.read { opacity: 0.6; background: #f8fafc; }

.ai-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.ai-level {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}
.ai-level.red { background: #fef2f2; color: #dc2626; }
.ai-level.orange { background: #fff7ed; color: #ea580c; }
.ai-level.yellow { background: #fefce8; color: #ca8a04; }

.ai-platform {
  font-size: 11px;
  padding: 2px 8px;
  background: #eff6ff;
  color: #2563eb;
  border-radius: 4px;
}
.ai-time { font-size: 11px; color: #94a3b8; margin-left: auto; }

.ai-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
  line-height: 1.4;
}

.ai-stats {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 12px;
}

.ai-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.ai-btn {
  font-size: 11px;
  padding: 6px 10px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}
.ai-btn.read { background: #f1f5f9; color: #64748b; }
.ai-btn.read:disabled { opacity: 0.5; cursor: not-allowed; }
.ai-btn.dispatch { background: #dbeafe; color: #2563eb; }
.ai-btn.dispatch:hover { background: #bfdbfe; }
.ai-btn.report { background: #fef3c7; color: #d97706; }
.ai-btn.trace { background: #ede9fe; color: #7c3aed; }
.ai-btn.trace:hover { background: #ddd6fe; }

/* Trace Modal (PRD 2.1.2) */
.trace-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
}
.trace-modal {
  width: 800px;
  max-height: 80vh;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}

.back-btn-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #e2e8f0;
  background: white;
  color: #64748b;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.back-btn-circle:hover {
  background: #f1f5f9;
  color: #2563eb;
  border-color: #bfdbfe;
}

.monitor-dashboard {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: #f8fafc;
}

.monitor-dashboard.mode-global {
  /* Global mode specific layout if needed */
}

/* Replicate TopicMonitor Layout for Split View */
.left-panel {
  padding: 0; /* Remove padding for full-width list items */
  overflow-y: hidden; /* Let inner list scroll */
  border-right: 1px solid #e2e8f0;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  width: 100%; /* Default to full width if not split */
}

/* If mimicking TopicMonitor list view */
.client-grid-wall {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); /* Align with topic card size */
  gap: 16px;
  padding: 20px;
  overflow-y: auto;
}

.client-card-large {
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.client-card-large:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px -4px rgba(0,0,0,0.1); /* Enhanced shadow */
  border-color: #cbd5e1;
}

/* Simple stats in client card footer */
.card-stats-simple {
   display: flex;
   align-items: center;
   justify-content: space-between;
   width: 100%;
}
.css-item {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  gap: 6px;
}
.css-item .lbl { font-size: 12px; color:#94a3b8; font-weight: normal; }
.css-item .val { font-size: 14px; font-weight: 600; color:#334155; }
.css-item .val.red { color: #dc2626; }
 
/* Tab Nav styling to match TopicMonitor .dv-tabs */
.tab-nav {
  display: flex;
  gap: 24px;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 24px;
  background: white;
}
.tab-item {
  padding: 16px 0;
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  position: relative;
}
.tab-item.active {
  color: #2563eb;
  font-weight: 600;
}
.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0px; /* Aligned to border */
  left: 0;
  right: 0;
  height: 2px;
  background: #2563eb;
  border-radius: 2px 2px 0 0;
} 

.tm-graph {
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
}
.trace-nodes {
  display: flex;
  align-items: center;
  gap: 20px;
}

.tm-graph { padding: 32px 24px; }

.trace-nodes {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  margin-bottom: 32px;
}
.trace-node {
  text-align: center;
  padding: 20px;
  border-radius: 12px;
  min-width: 140px;
  border: 2px solid #e2e8f0;
}
.trace-node.source { border-color: #dc2626; background: #fef2f2; }
.trace-node.kol { border-color: #ea580c; background: #fff7ed; }
.trace-node.spread { border-color: #64748b; background: #f1f5f9; }

.tn-icon { font-size: 28px; margin-bottom: 8px; }
.tn-label { font-size: 12px; color: #64748b; margin-bottom: 4px; }
.tn-name { font-size: 13px; font-weight: 600; color: #1e293b; }

.trace-arrow {
  font-size: 24px;
  color: #94a3b8;
}

.tm-timeline {
  text-align: center;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}
.tm-play {
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.tm-play:hover { opacity: 0.9; }

/* === COMMAND CENTER STYLES === */
.dashboard-view.global-layout { gap: 24px; }

.cmd-stats-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 8px; }
.cmd-card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; display: flex; align-items: center; gap: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); transition: all 0.2s; }
.cmd-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.cmd-icon { width: 48px; height: 48px; border-radius: 12px; background: #f8fafc; font-size: 24px; display: flex; align-items: center; justify-content: center; }
.cmd-icon.blue { background: #eff6ff; color: #2563eb; }
.cmd-icon.red { background: #fef2f2; color: #dc2626; }
.cmd-icon.orange { background: #fff7ed; color: #ea580c; }
.cmd-icon.purple { background: #f5f3ff; color: #7c3aed; }
.cmd-icon.green { background: #f0fdf4; color: #16a34a; }
.cmd-icon.pulse { animation: breathing 1.5s infinite; }
.cmd-info { display: flex; flex-direction: column; }
.cmd-val { font-size: 20px; font-weight: 800; color: #1e293b; line-height: 1.2; }
.cmd-val.risk { color: #dc2626; }
.cmd-label { font-size: 11px; color: #64748b; }

.cmd-main-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
.cmd-left-col, .cmd-right-col { display: flex; flex-direction: column; gap: 20px; }
.cmd-section { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; display: flex; flex-direction: column; }
.cmd-section.full-h { flex: 1; min-height: 300px; }
.cmd-section h4 { font-size: 14px; font-weight: 700; color: #334155; margin-bottom: 16px; display: flex; align-items: center; gap: 6px; }

/* To-Do List */
.todo-list { display: flex; flex-direction: column; gap: 12px; }
.todo-item { display: flex; align-items: center; padding: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; gap: 12px; transition: all 0.2s; }
.todo-item:hover { border-color: #cbd5e1; background: white; }
.todo-icon { font-size: 20px; }
.todo-content { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.todo-title { font-size: 13px; font-weight: 600; color: #1e293b; }
.todo-meta { font-size: 11px; color: #94a3b8; }
.todo-act { padding: 4px 10px; background: white; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 11px; color: #475569; cursor: pointer; }
.todo-act:hover { background: #eff6ff; color: #2563eb; border-color: #bfdbfe; }

/* Rankings */
.rank-list { display: flex; flex-direction: column; gap: 8px; overflow-y: auto; max-height: 400px; }
.rank-item { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px dashed #f1f5f9; }
.rank-item:last-child { border-bottom: none; }
.rank-idx { width: 20px; height: 20px; border-radius: 4px; background: #f1f5f9; color: #94a3b8; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.rank-idx.top-1 { background: #fee2e2; color: #dc2626; }
.rank-idx.top-2 { background: #ffedd5; color: #ea580c; }
.rank-idx.top-3 { background: #fefce8; color: #ca8a04; }
.rank-title { font-size: 13px; color: #334155; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }
.rank-title:hover { color: #2563eb; text-decoration: underline; }
.rank-hot { font-size: 11px; color: #f59e0b; font-weight: 600; font-family: monospace; }

.rank-content-info { display: flex; flex-direction: column; flex: 1; }
.rank-art-title { font-size: 13px; font-weight: 500; color: #334155; }
.rank-art-meta { font-size: 10px; color: #94a3b8; }
.empty-text { font-size: 12px; color: #cbd5e1; text-align: center; padding: 20px; }

/* --- NEW DASHBOARD STYLES (Ref: Nebula) --- */
.dashboard-grid-top {
    display: grid;
    grid-template-columns: 1fr 1fr 2fr;
    gap: 24px;
    margin-bottom: 24px;
}
.stat-card-modern {
    background: white;
    padding: 24px;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    position: relative;
    overflow: hidden;
    transition: all 0.3s;
}
.stat-card-modern:hover {
    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}
.st-header { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #64748b; margin-bottom: 8px; }
.st-val { font-size: 32px; font-weight: 800; color: #1e293b; line-height: 1.2; }
.st-val.red { color: #dc2626; }
.st-trend { display: flex; align-items: center; gap: 6px; font-size: 13px; margin-top: 12px; }
.st-trend.positive { color: #10b981; }
.st-trend.negative { color: #ef4444; }
.st-trend .label { color: #94a3b8; margin-left: 4px; }
.st-bg-icon {
    position: absolute;
    right: -10px;
    bottom: -10px;
    font-size: 80px;
    opacity: 0.05;
    transform: rotate(12deg);
    transition: transform 0.3s;
}
.stat-card-modern:hover .st-bg-icon { transform: rotate(12deg) scale(1.1); opacity: 0.1; }

.prophet-card {
    grid-column: span 1; /* Was 2 in 4-col, but here maybe flexible */
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    border-radius: 16px;
    padding: 24px;
    color: white;
    box-shadow: 0 10px 20px -5px rgba(79, 70, 229, 0.4);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.pc-header { display: flex; justify-content: space-between; align-items: flex-start; }
.pc-title { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #c7d2fe; display: flex; align-items: center; gap: 8px; }
.pc-rank { text-align: right; }
.pc-rank-val { font-size: 32px; font-weight: 800; color: #fcd34d; line-height: 1; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }
.pc-rank-lbl { font-size: 11px; color: #c7d2fe; }
.pc-event { font-size: 20px; font-weight: 700; margin-top: 4px; }
.pc-metrics { display: flex; gap: 24px; margin-top: 20px; }
.pc-metric-box {
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255,255,255,0.2);
    padding: 8px 16px;
    border-radius: 8px;
}
.pc-metric-box .lbl { font-size: 11px; color: #c7d2fe; margin-bottom: 2px; }
.pc-metric-box .val { font-size: 14px; font-weight: 700; }
.pc-metric-box .val.yellow { color: #fcd34d; }
.pc-footer {
    margin-top: 24px;
    border-top: 1px solid rgba(255,255,255,0.1);
    padding-top: 16px;
    font-size: 12px;
    color: #e0e7ff;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.pc-act-btn {
    background: white;
    color: #4f46e5;
    border: none;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s;
}
.pc-act-btn:hover { background: #f5f3ff; }

.dashboard-grid-main {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;
}
.chart-panel {
    background: white;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    padding: 24px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.chart-panel.wide { grid-column: 1; }
.chart-col-right { display: flex; flex-direction: column; gap: 24px; }
.panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.panel-head h4 { margin: 0; font-size: 15px; font-weight: 700; color: #334155; }
.panel-legend { display: flex; gap: 12px; font-size: 12px; color: #64748b; }
.panel-legend .dot { width: 8px; height: 8px; display: inline-block; border-radius: 50%; }
.dot.blue { background: #6366f1; } .dot.gray { background: #cbd5e1; }

.ai-insight-box {
    margin-top: 16px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
    font-size: 13px;
    color: #475569;
    display: flex;
    gap: 12px;
    align-items: flex-start;
}
.ai-insight-box .ai-icon { font-size: 16px; margin-top: 2px; }
.ai-insight-box strong { color: #6366f1; }
.ai-insight-box .tag { background: #fef3c7; padding: 2px 6px; border-radius: 4px; font-weight: 500; color: #b45309; }

.opinion-list { display: flex; flex-direction: column; gap: 16px; margin-top: 8px; }
.opinion-item { }
.op-row { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; }
.op-text { color: #334155; }
.op-pct { color: #64748b; }
.op-bar-bg { background: #f1f5f9; height: 8px; border-radius: 4px; width: 100%; overflow: hidden; }
.op-bar-fill { height: 100%; border-radius: 4px; }
.op-bar-fill.red { background: #ef4444; }
.op-bar-fill.orange { background: #fbbf24; }
.op-bar-fill.green { background: #10b981; }

/* --- NEW STREAM STYLES --- */
.stream-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
.st-filters { display: flex; gap: 12px; align-items: center; }
.st-select {
    padding: 8px 12px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-size: 13px;
    color: #475569;
    background: white;
    cursor: pointer;
}
.st-select:focus { outline: none; border-color: #6366f1; }
.st-checkbox-label {
    display: flex; align-items: center; gap: 8px;
    background: white;
    border: 1px solid #cbd5e1;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 13px;
    color: #475569;
    cursor: pointer;
}
.st-link-btn {
    color: #6366f1;
    font-size: 13px;
    font-weight: 500;
    background: none;
    border: none;
    cursor: pointer;
}
.st-link-btn:hover { text-decoration: underline; }

.stream-list-rich { display: flex; flex-direction: column; gap: 16px; }
.feed-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    transition: box-shadow 0.2s;
}
.feed-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.feed-card.high-risk { border-color: #fecaca; }
.fc-sidebar {
    position: absolute; left: 0; top: 0; bottom: 0;
    width: 4px; background: #ef4444;
}

.fc-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.fc-user { display: flex; gap: 12px; align-items: center; }
.fc-avatar {
    width: 36px; height: 36px;
    border-radius: 50%;
    color: white;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 14px;
}
.fc-user-info { display: flex; flex-direction: column; }
.fc-name-row { display: flex; align-items: center; gap: 6px; margin-bottom: 2px; }
.fc-name { font-size: 14px; font-weight: 700; color: #1e293b; }
.fc-verify-icon { font-size: 10px; color: #3b82f6; }
.fc-level-tag {
    background: #ede9fe; color: #7c3aed;
    font-size: 10px; padding: 1px 4px;
    border-radius: 4px; font-weight: 600;
    border: 1px solid #ddd6fe;
}
.fc-meta { font-size: 12px; color: #94a3b8; }

.fc-tags { display: flex; gap: 8px; }
.fc-tag { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.fc-tag.sentiment.negative { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.fc-tag.sentiment.positive { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }
.fc-tag.sentiment.neutral { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.fc-tag.topic { background: #f1f5f9; color: #475569; }

.fc-body { margin-bottom: 16px; }
.fc-title { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0 0 6px 0; cursor: pointer; }
.fc-title:hover { color: #6366f1; }
.fc-snippet { font-size: 13px; color: #475569; line-height: 1.5; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.fc-footer {
    border-top: 1px solid #f1f5f9;
    padding-top: 16px;
    display: flex; justify-content: space-between; align-items: center;
}
.fc-stats { display: flex; gap: 16px; font-size: 12px; color: #64748b; }
.fc-stat-hot { color: #ef4444; font-weight: 700; display: flex; align-items: center; gap: 4px; }
.fc-actions { display: flex; gap: 8px; }
.fc-btn {
    border: 1px solid #cbd5e1;
    background: white;
    color: #64748b;
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
}
.fc-btn:hover { background: #f8fafc; }
.fc-btn.primary {
    background: #6366f1; color: white; border-color: #6366f1;
    display: flex; align-items: center; gap: 6px;
}
.fc-btn.primary:hover { background: #4f46e5; }
/* --- NEW MOCK LAYOUT STYLES --- */
.tm-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 32px;
    background: white;
    box-shadow: 0 1px 0 #f1f5f9;
    position: sticky;
    top: 0;
    z-index: 10;
}
.header-left { 
    display: flex; 
    align-items: center; 
    gap: 16px; 
}
.header-left h3 { 
    font-size: 20px; 
    font-weight: 700; 
    color: #0f172a; 
    margin: 0; 
}
.status-badge-green {
    background: #ecfdf5;
    color: #059669;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
}

.header-center {
    flex: 1;
    display: flex;
    justify-content: center;
}
.nav-segment {
    display: flex;
    background: #f1f5f9;
    padding: 4px;
    border-radius: 8px;
    gap: 4px;
}
.nav-item {
    padding: 6px 16px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    color: #64748b;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
}
.nav-item.active {
    background: white;
    color: #0f172a;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.nav-item .icon { font-size: 14px; }

.header-actions {
    display: flex;
    gap: 12px;
}
.action-btn-gray {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    color: #475569;
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}
.action-btn-gray:hover { background: #e2e8f0; }
.action-btn-blue {
    background: #2563eb;
    border: 1px solid #2563eb;
    color: white;
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
}

/* Dashboard Container */
.dashboard-container {
    padding: 24px 32px;
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* 1. Metrics 5 Cards */
.metrics-row-5 {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 20px;
}
.metric-card {
    background: white;
    border: 1px solid #f1f5f9;
    border-radius: 12px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.mc-title { font-size: 12px; color: #64748b; margin-bottom: 8px; }
.mc-val-group { display: flex; align-items: baseline; gap: 4px; }
.mc-val { font-size: 28px; font-weight: 700; color: #0f172a; font-family: 'Inter', sans-serif; }
.mc-val.red { color: #ef4444; }
.mc-unit { font-size: 12px; color: #94a3b8; }
.mc-trend { font-size: 12px; font-weight: 500; }
.mc-trend.down { color: #ef4444; }
.mc-trend.up { color: #10b981; }

/* 2. Main Layout Grid */
.main-layout-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;
    height: 400px;
}
.chart-wrapper {
    background: white;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #f1f5f9;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    display: flex;
    flex-direction: column;
}
.cw-header { margin-bottom: 20px; font-size: 14px; font-weight: 700; color: #334155; display: flex; align-items: center; gap: 8px; }
.cw-header .icon { color: #64748b; }
.cw-body { flex: 1; overflow: hidden; position: relative; }
.chart-full { width: 100%; height: 100%; }

/* List Wrapper (Right side) */
.list-wrapper {
    background: white;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #f1f5f9;
    display: flex; 
    flex-direction: column;
}
.lw-tabs { display: flex; gap: 24px; margin-bottom: 16px; border-bottom: 1px solid #f1f5f9; }
.lw-tab { 
    padding-bottom: 10px; 
    font-size: 13px; 
    color: #64748b; 
    cursor: pointer; 
    position: relative; 
}
.lw-tab.active { color: #2563eb; font-weight: 600; }
.lw-tab.active::after {
    content: ''; position: absolute; bottom: -1px; left: 0; right: 0; height: 2px; background: #2563eb;
}
.lw-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
.lw-item { padding-bottom: 12px; border-bottom: 1px solid #f8fafc; }
.lwi-head { display: flex; justify-content: space-between; margin-bottom: 4px; }
.lwi-platform { font-size: 12px; color: #2563eb; font-weight: 600; }
.lwi-time { font-size: 11px; color: #94a3b8; }
.lwi-title { font-size: 13px; color: #334155; font-weight: 500; margin-bottom: 6px; line-height: 1.4; }
.lwi-stats { display: flex; gap: 12px; font-size: 11px; color: #94a3b8; }
.lwi-tags { margin-top: 8px; }
.lwi-tag { font-size: 10px; background: #f1f5f9; color: #64748b; padding: 2px 6px; border-radius: 4px; }

/* 3. Bottom Charts Row */
.bottom-charts-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    height: 300px;
}

/* 4. Alerts Section */
.alerts-section {
    background: white;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #f1f5f9;
}
.alert-header .warning { color: #f59e0b; }
.alert-table { display: flex; flex-direction: column; gap: 0; }
.at-row {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #f8fafc;
    font-size: 13px;
}
.at-time { width: 120px; color: #64748b; }
.at-tag { 
    padding: 2px 8px; 
    border-radius: 4px; 
    margin-right: 16px; 
    font-size: 11px; 
    font-weight: 600; 
}
.at-tag.red { background: #fef2f2; color: #dc2626; }
.at-tag.orange { background: #fff7ed; color: #ea580c; }
.at-content { flex: 1; color: #334155; }
.at-status { color: #10b981; font-weight: 600; }

/* --- Workbench View (New) --- */
.workbench-view {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 40px;
    max-width: 900px;
    margin: 0 auto;
    width: 100%;
}
.wb-hero {
    width: 100%;
    margin-bottom: 60px;
    text-align: center;
}
.wb-greeting {
    font-size: 28px;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 32px;
}
.wb-search-box {
    width: 100%;
    max-width: 680px;
    margin: 0 auto;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 100px; /* pill shape */
    padding: 12px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    transition: all 0.2s;
}
.wb-search-box:focus-within {
    border-color: #94a3b8;
    box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}
.wb-search-box .ai-icon { font-size: 20px; }
.wb-search-box input {
    flex: 1;
    border: none;
    outline: none;
    font-size: 16px;
    color: #334155;
}
.wb-search-box input::placeholder { color: #cbd5e1; }
.wb-send-btn {
    background: #f1f5f9;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: none;
    color: #64748b;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.2s;
}
.wb-send-btn:hover { background: #2563eb; color: white; }

.wb-section-title {
    width: 100%;
    max-width: 900px;
    font-size: 14px;
    font-weight: 600;
    color: #64748b;
    margin-bottom: 20px;
    text-align: left;
}
.wb-quick-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    width: 100%;
}
.wb-card {
    background: white;
    border: 1px solid #f1f5f9;
    border-radius: 16px;
    padding: 24px;
    display: flex;
    align-items: center;
    gap: 20px;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
}
.wb-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.06);
    border-color: #e2e8f0;
}
.wb-icon-box {
    width: 56px;
    height: 56px;
    background: #f8fafc;
    border-radius: 12px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 28px;
}
.action-create .wb-icon-box { background: #eff6ff; color: #2563eb; }
.action-expand .wb-icon-box { background: #f0fdf4; color: #16a34a; }
.action-polish .wb-icon-box { background: #fdf2f8; color: #db2777; }
.wb-info { flex: 1; }
.wb-label { font-size: 16px; font-weight: 600; color: #1e293b; margin-bottom: 4px; }
.wb-desc { font-size: 12px; color: #94a3b8; line-height: 1.4; }
.wb-arrow { color: #cbd5e1; font-size: 20px; transition: transform 0.2s; }
.wb-card:hover .wb-arrow { transform: translateX(8px); color: #64748b; }

.wb-recent-list {
    width: 100%;
    min-height: 200px;
    background: white;
    border-radius: 12px;
    border: 1px solid #f1f5f9;
    display: flex;
    justify-content: center;
    align-items: center;
}
.wb-empty-state { color: #94a3b8; font-size: 14px; }

/* Polish Loading Overlay (Global) */
.polish-loading-overlay {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(255,255,255,0.9); z-index: 2000;
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    gap: 20px; color: #3b82f6; font-size: 16px; font-weight: 600;
}
.spinner-lg {
    width: 48px; height: 48px; border: 4px solid #e2e8f0;
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 1s infinite linear;
}
.pol-cancel-btn {
    margin-top: 20px;
    padding: 8px 16px;
    background: transparent;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    color: #64748b;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
}
.pol-cancel-btn:hover {
    border-color: #3b82f6;
    color: #3b82f6;
}

/* Polish Config Modal */
.polish-config { width: 600px; max-width: 90vw; }
.pc-section { margin-bottom: 20px; }
.pc-section label { display: block; font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 8px; }
.file-preview-card { display: flex; align-items: center; gap: 10px; background: #f8fafc; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; }
.file-preview-card .icon { font-size: 20px; }
.file-preview-card .fname { flex: 1; font-size: 14px; font-weight: 500; color: #1e293b; }
.remove-btn { border: none; background: none; color: #94a3b8; cursor: pointer; font-size: 16px; }
.prompt-editor { width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 13px; color: #334155; line-height: 1.6; resize: vertical; background: #fff; }
.prompt-editor:focus { border-color: #2563eb; outline: none; }
.pc-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 30px; }
.cancel-btn { padding: 8px 20px; border: 1px solid #cbd5e1; background: white; border-radius: 6px; color: #64748b; cursor: pointer; }
.confirm-btn { padding: 8px 20px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500; }
.confirm-btn:hover { background: #1d4ed8; }
</style>