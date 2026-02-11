<template>
  <div class="topic-monitor">
    <!-- 列表视图 -->
    <div v-if="!selectedTopic" class="list-view">
      <!-- 顶部操作区 -->
      <div class="tm-header">
        <h2>📊 舆情监控概览</h2>
        <!-- Global Tabs -->
        <div class="tm-tabs">
            <span :class="{active: globalView === 'dashboard'}" @click="globalView='dashboard'">仪表盘</span>
            <span :class="{active: globalView === 'stream'}" @click="globalView='stream'; fetchStream()">实时快报监控</span>
            <span :class="{active: globalView === 'report'}" @click="globalView='report'">报告中心</span>
        </div>
        <div class="tm-actions">
          <button class="btn primary" @click="showCreateModal = true">+ 新建专题</button>
          <button class="btn secondary" @click="batchArchive" :disabled="selectedTopics.length === 0" :title="selectedTopics.length === 0 ? '请先选择专题' : ''">批量归档</button>
          <button class="btn secondary danger-text" @click="batchDelete" :disabled="!canBatchDelete" :title="!canBatchDelete ? '仅可删除已暂停/已归档的专题' : ''">批量删除</button>
        </div>
      </div>

      <!-- GLOBAL DASHBOARD -->
      <template v-if="globalView === 'dashboard'">
          <!-- 筛选栏 (增强版) -->
          <div class="tm-filters">
            <div class="filter-row">
              <input type="text" v-model="filters.search" placeholder="🔍 搜索专题名称、关键词..." class="filter-search" />
              <select v-model="filters.tag" class="filter-select">
                <option value="">全部标签</option>
                <option v-for="tag in allTags" :key="tag">{{ tag }}</option>
              </select>
              <select v-model="filters.status" class="filter-select">
                <option value="">全部状态</option>
                <option value="monitoring">监控中</option>
                <option value="paused">已暂停</option>
                <option value="archived">已归档</option>
                <option value="ended">已结束</option>
              </select>
              <select v-model="filters.platform" class="filter-select">
                <option value="">全平台</option>
                <option value="weibo">微博</option>
                <option value="douyin">抖音</option>
                <option value="xiaohongshu">小红书</option>
                <option value="news">新闻</option>
              </select>
              <select v-model="filters.timeRange" class="filter-select">
                <option value="">全部时间</option>
                <option value="today">今日</option>
                <option value="7d">近7天</option>
                <option value="30d">近30天</option>
              </select>
              <select v-model="filters.sortBy" class="filter-select">
                <option value="created_desc">创建时间 ↓</option>
                <option value="volume_desc">声量 ↓</option>
                <option value="heat_desc">热度 ↓</option>
                <option value="alert_desc">预警数 ↓</option>
              </select>
              <button class="btn secondary" @click="resetFilters" style="margin-left: auto;">重置</button>
            </div>
          </div>
    
          <!-- 专题列表 -->
          <div class="topic-list">
            <!-- 骨架屏加载 -->
            <template v-if="loading">
              <div class="skeleton-card" v-for="i in 3" :key="i">
                <div class="sk-checkbox"></div>
                <div class="sk-content">
                  <div class="sk-line w60"></div>
                  <div class="sk-line w40"></div>
                  <div class="sk-stats">
                    <div class="sk-stat"></div>
                    <div class="sk-stat"></div>
                    <div class="sk-stat"></div>
                  </div>
                </div>
              </div>
            </template>
    
            <!-- 空状态 -->
            <div v-else-if="sortedTopics.length === 0" class="empty-state">
              <div class="empty-icon">📭</div>
              <p>暂无符合条件的专题</p>
              <button class="btn primary" @click="showCreateModal = true">+ 新建专题</button>
            </div>
    
            <!-- 专题卡片列表 -->
            <div 
              v-for="topic in sortedTopics" 
              :key="topic.id"
              class="topic-card"
              :class="{ selected: selectedTopics.includes(topic.id), 'has-alert': topic.unread_alerts > 0 }"
              @click="viewTopic(topic)"
            >
              <!-- 左上角选择框 -->
              <div class="tc-checkbox" @click.stop>
                <input type="checkbox" :value="topic.id" v-model="selectedTopics" />
              </div>
    
              <!-- 预警图标 -->
              <div class="tc-alert" v-if="topic.unread_alerts > 0" @click.stop="goToAlerts(topic)" :title="`该专题有${topic.unread_alerts}条未处理预警`">
                ⚠️
              </div>
    
              <!-- 卡片主体 -->
              <div class="tc-body">
                <!-- 第一行：标题 + 状态 + 元信息 -->
                <div class="tc-row-1">
                  <div class="tc-title-group">
                    <h3 class="tc-title">{{ topic.name }}</h3>
                    <span class="tc-status" :class="topic.status">{{ getStatusLabel(topic.status) }}</span>
                  </div>
                  <div class="tc-meta">
                    <span class="meta-item">
                      <span class="avatar">{{ topic.owner?.charAt(0) || '?' }}</span>
                      {{ topic.owner }}
                    </span>
                    <span class="meta-item">📅 {{ formatDate(topic.created_at) }}</span>
                    <span class="meta-item remaining" :class="{ urgent: topic.remaining_days <= 3 }">⏱️ 剩余{{ topic.remaining_days }}天</span>
                  </div>
                </div>
    
                <!-- 第二行：核心指标 -->
                <div class="tc-row-2">
                  <div class="tc-stat">
                    <span class="stat-label">声量</span>
                    <span class="stat-value">{{ formatNumber(topic.volume) }}</span>
                    <span class="stat-arrow" :class="getVolumeClass(topic.volume_change)">
                      {{ topic.volume_change >= 0 ? '↑' : '↓' }}{{ Math.abs(topic.volume_change) }}%/h
                    </span>
                  </div>
                  <div class="tc-stat">
                    <span class="stat-label">热度</span>
                    <span class="stat-value heat">{{ topic.heat_score }}</span>
                  </div>
                  <div class="tc-stat">
                    <span class="stat-label">负面占比</span>
                    <span class="stat-value" :class="{ negative: topic.negative_ratio >= 30, blink: topic.negative_ratio >= 40 }">{{ topic.negative_ratio }}%</span>
                  </div>
                </div>
    
                <!-- 第三行：标签 + 快捷操作 -->
                <div class="tc-row-3">
                  <div class="tc-tags">
                    <span v-for="tag in topic.tags?.slice(0, 2)" :key="tag" class="tag">{{ tag }}</span>
                    <span v-if="topic.tags?.length > 2" class="tag more">+{{ topic.tags.length - 2 }}</span>
                  </div>
                  <div class="tc-quick-actions" @click.stop>
                    <button class="qa-btn" @click="viewTopic(topic)" title="查看详情">🔍</button>
                    <button class="qa-btn" @click="editTopic(topic)" title="编辑配置">✏️</button>
                    <button class="qa-btn" @click="togglePause(topic)" :title="topic.status === 'paused' ? '恢复监控' : '暂停监控'">
                      {{ topic.status === 'paused' ? '▶️' : '⏸️' }}
                    </button>
                    <button class="qa-btn" @click="exportSingleReport(topic)" title="导出报告">📥</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
    
          <!-- 分页 -->
          <div class="tm-pagination">
            <span>共 {{ sortedTopics.length }} 个专题</span>
            <div class="page-controls">
              <button :disabled="page === 1" @click="page--">上一页</button>
              <span>{{ page }} / {{ totalPages }}</span>
              <button :disabled="page === totalPages" @click="page++">下一页</button>
            </div>
          </div>
      </template>

      <!-- GLOBAL STREAM VIEW -->
      <template v-if="globalView === 'stream'">
          <div class="stream-container">
             <div class="stream-filter-bar">
                 <select class="filter-select">
                    <option>全平台</option>
                    <option>微博</option>
                    <option>抖音</option>
                 </select>
                 <input type="text" placeholder="全网实时搜索..." class="sf-search" />
             </div>
             <div class="stream-list">
                 <!-- Real Flash Items -->
                 <div v-if="loadingStream" class="loading-box">加载中...</div>
                 <div v-else-if="streamItems.length === 0" class="empty-box">暂无快报数据</div>
                 <div v-else v-for="(item, idx) in streamItems" :key="item.id || idx" class="stream-item">
                    <div class="si-left">
                        <span class="si-time">{{ formatTime(item.publish_time || item.created_at) }}</span>
                        <span class="si-platform news">财联社快报</span>
                    </div>
                    <div class="si-main">
                        <div class="si-title">{{ item.tmt_title || item.title }}</div>
                        <div class="si-snippet full-text">{{ item.tmt_content || item.content }}</div>
                        <div class="si-meta">
                           <span class="tag-sm">AI改写</span>
                           <span class="si-source" v-if="item.tmt_source">来源: {{ item.tmt_source }}</span>
                        </div>
                    </div>
                 </div>
             </div>
          </div>
      </template>

      <!-- GLOBAL REPORT VIEW -->
      <template v-if="globalView === 'report'">
          <div class="report-center">
              <div class="report-tools">
                   <h3>📅 全局舆情报告</h3>
                   <div class="rt-options">
                       <div class="rt-card" @click="generateReport('global_daily')">
                           <div class="rt-icon">🌏</div>
                           <h4>全网日报</h4>
                           <p>全平台舆情趋势汇总</p>
                       </div>
                       <div class="rt-card" @click="generateReport('global_weekly')">
                           <div class="rt-icon">📈</div>
                           <h4>全网周报</h4>
                           <p>本周热点事件深度复盘</p>
                       </div>
                   </div>
              </div>
              <div class="report-history">
                  <h3>已生成报告</h3>
                  <table class="rh-table">
                      <thead><tr><th>报告名称</th><th>类型</th><th>生成时间</th><th>操作</th></tr></thead>
                      <tbody>
                          <tr><td>2026-02-01 全网舆情日报</td><td>Daily</td><td>2026-02-02 09:00</td><td><a href="#">下载</a></td></tr>
                      </tbody>
                  </table>
              </div>
          </div>
      </template>
    </div>

    <!-- 详情视图 -->
    <div v-else class="detail-view">
      <!-- 顶部信息栏 -->
      <div class="dv-header">
        <div class="dv-left">
          <button class="back-btn" @click="selectedTopic = null">← 返回列表</button>
          <h2>{{ selectedTopic.name }}</h2>
          <span class="dv-status" :class="selectedTopic.status">{{ getStatusLabel(selectedTopic.status) }}</span>
        </div>
        <!-- View Tabs -->
        <div class="dv-tabs">
            <span :class="{active: currentView === 'dashboard'}" @click="currentView='dashboard'">📊 仪表盘</span>
            <span :class="{active: currentView === 'stream'}" @click="currentView='stream'">⚡️ 实时情报流</span>
            <span :class="{active: currentView === 'report'}" @click="currentView='report'">📄 报告中心</span>
        </div>
        <div class="dv-actions">
          <button class="btn" @click="editTopic(selectedTopic)">✏️ 编辑配置</button>
          <button class="btn" @click="togglePause(selectedTopic)">
            {{ selectedTopic.status === 'paused' ? '▶️ 恢复监控' : '⏸️ 暂停监控' }}
          </button>
          <button class="btn primary" @click="exportReport" v-if="currentView === 'dashboard'">📥 导出报告</button>
          <button class="btn" @click="archiveTopic">📦 复盘归档</button>
        </div>
      </div>

      <!-- DASHBOARD VIEW -->
      <template v-if="currentView === 'dashboard'">
          <!-- 核心指标 -->
          <div class="dv-stats">
            <div class="stat-card">
              <span class="sc-label">当前声量</span>
              <span class="sc-value">{{ formatNumber(selectedTopic.volume) }}</span>
              <span class="sc-change" :class="selectedTopic.volume_change >= 0 ? 'up' : 'down'">
                {{ selectedTopic.volume_change >= 0 ? '+' : '' }}{{ selectedTopic.volume_change }}%/h
              </span>
            </div>
            <div class="stat-card">
              <span class="sc-label">热度评分</span>
              <span class="sc-value">{{ selectedTopic.heat_score }}</span>
            </div>
            <div class="stat-card">
              <span class="sc-label">负面占比</span>
              <span class="sc-value" :class="{ warning: selectedTopic.negative_ratio > 30 }">{{ selectedTopic.negative_ratio }}%</span>
            </div>
            <div class="stat-card">
              <span class="sc-label">跨平台覆盖</span>
              <span class="sc-value">{{ selectedTopic.platforms?.length || 3 }}</span>
            </div>
            <div class="stat-card">
              <span class="sc-label">监控剩余</span>
              <span class="sc-value">{{ selectedTopic.remaining_days }}天</span>
            </div>
          </div>
    
          <!-- 三栏布局 -->
          <div class="dv-body">
            <!-- 左侧配置栏 -->
            <div class="dv-config" :class="{ collapsed: configCollapsed }">
              <div class="config-header" @click="configCollapsed = !configCollapsed">
                <span>专题配置</span>
                <span>{{ configCollapsed ? '展开' : '折叠' }}</span>
              </div>
              <div class="config-content" v-show="!configCollapsed">
                <div class="config-item">
                  <label>🔑 监控关键词</label>
                  <div class="keywords">
                    <span v-for="kw in selectedTopic.keywords" :key="kw" class="kw-tag">{{ kw }}</span>
                  </div>
                  <button class="config-edit">修改</button>
                </div>
                <div class="config-item">
                  <label>📱 监控平台</label>
                  <div class="platforms">
                    <span v-for="p in selectedTopic.platforms" :key="p" class="platform-tag">{{ getPlatformLabel(p) }}</span>
                  </div>
                  <button class="config-edit">修改</button>
                </div>
                <div class="config-item">
                  <label>⚠️ 预警规则</label>
                  <p class="config-desc">爆发预警: 50% | 衰退预警: 30%</p>
                  <button class="config-edit">修改</button>
                </div>
              </div>
            </div>
    
            <!-- 中间图表区 -->
            <div class="dv-charts">
              <div class="chart-section">
                <h4>📈 小时级热度趋势</h4>
                <v-chart class="chart" :option="trendChartOption" autoresize />
              </div>
              <div class="chart-row">
                <div class="chart-half">
                  <h4>🥧 跨平台分布</h4>
                  <v-chart class="chart-sm" :option="platformChartOption" autoresize />
                </div>
                <div class="chart-half">
                  <h4>😊 情感分布</h4>
                  <v-chart class="chart-sm" :option="sentimentChartOption" autoresize />
                </div>
              </div>
            </div>
    
            <!-- 右侧内容区 -->
            <div class="dv-content">
              <div class="content-tabs">
                <span :class="{ active: contentTab === 'content' }" @click="contentTab = 'content'">优质内容</span>
                <span :class="{ active: contentTab === 'kol' }" @click="contentTab = 'kol'">核心KOL</span>
                <span :class="{ active: contentTab === 'derived' }" @click="contentTab = 'derived'">衍生选题</span>
              </div>
              
              <!-- 优质内容 -->
              <div v-if="contentTab === 'content'" class="content-list">
                <div v-for="item in topContents" :key="item.id" class="content-item">
                  <div class="ci-header">
                    <span class="ci-platform">{{ getPlatformLabel(item.platform) }}</span>
                    <span class="ci-time">{{ formatTime(item.time) }}</span>
                  </div>
                  <p class="ci-title">{{ item.title }}</p>
                  <div class="ci-stats">
                    <span>💬 {{ item.comments }}</span>
                    <span>👍 {{ item.likes }}</span>
                    <span>🔄 {{ item.shares }}</span>
                  </div>
                  <button class="ci-action">收藏</button>
                </div>
              </div>
    
              <!-- 核心KOL -->
              <div v-if="contentTab === 'kol'" class="kol-list">
                <div v-for="kol in topKols" :key="kol.id" class="kol-item">
                  <div class="kol-avatar">{{ kol.name.charAt(0) }}</div>
                  <div class="kol-info">
                    <span class="kol-name">{{ kol.name }}</span>
                    <span class="kol-platform">{{ getPlatformLabel(kol.platform) }}</span>
                  </div>
                  <div class="kol-stats">
                    <span>粉丝: {{ formatNumber(kol.followers) }}</span>
                    <span>互动: {{ formatNumber(kol.engagement) }}</span>
                  </div>
                </div>
              </div>
    
              <!-- 衍生选题 -->
              <div v-if="contentTab === 'derived'" class="derived-list">
                <div v-for="topic in derivedTopics" :key="topic.id" class="derived-item">
                  <div class="di-main">
                    <span class="di-title">{{ topic.name }}</span>
                    <span class="di-score">潜力: {{ topic.score }}</span>
                  </div>
                  <button class="di-btn" @click="createDerivedTopic(topic)">创建专题</button>
                </div>
              </div>
            </div>
          </div>
    
          <!-- 底部预警记录 -->
          <div class="dv-alerts">
            <h4>⚠️ 预警记录 ({{ alerts.length }})</h4>
            <div class="alert-list">
              <div v-for="alert in alerts" :key="alert.id" class="alert-item">
                <span class="al-time">{{ formatTime(alert.time) }}</span>
                <span class="al-type" :class="alert.type">{{ alert.type_label }}</span>
                <span class="al-desc">{{ alert.description }}</span>
                <span class="al-status" :class="alert.status">{{ alert.status === 'handled' ? '已处置' : '待处理' }}</span>
              </div>
            </div>
          </div>
      </template>

      <!-- STREAM VIEW -->
      <template v-if="currentView === 'stream'">
          <div class="stream-container">
             <div class="stream-filter-bar">
                 <input type="text" placeholder="搜索情报..." class="sf-search" />
                 <label><input type="checkbox" checked> 只看负面</label>
                 <label><input type="checkbox" checked> 只看高赞</label>
             </div>
             <div class="stream-list">
                 <div v-for="(item, idx) in streamItems" :key="idx" class="stream-item">
                    <div class="si-left">
                        <span class="si-time">{{ formatTime(new Date(Date.now() - idx * 600000)) }}</span>
                        <span class="si-platform" :class="item.platform.toLowerCase()">{{ item.platform }}</span>
                    </div>
                    <div class="si-main">
                        <div class="si-title">{{ item.title }}</div>
                        <div class="si-snippet">{{ item.content }}</div>
                        <div class="si-meta">
                            <span>情感: <b :class="item.sentiment === 'negative' ? 'text-red' : 'text-green'">{{ item.sentiment === 'negative' ? '负面' : '正面' }}</b></span>
                            <span>影响力: {{ item.influence }}</span>
                        </div>
                    </div>
                    <div class="si-right">
                        <button class="btn-sm">查看原文</button>
                        <button class="btn-sm">忽略</button>
                    </div>
                 </div>
             </div>
          </div>
      </template>

      <!-- REPORT VIEW -->
      <template v-if="currentView === 'report'">
          <div class="report-center">
              <div class="report-tools">
                   <h3>📄 智能报告生成</h3>
                   <div class="rt-options">
                       <div class="rt-card" @click="generateReport('daily')">
                           <div class="rt-icon">📅</div>
                           <h4>日报</h4>
                           <p>自动汇总昨日核心数据与舆情</p>
                       </div>
                       <div class="rt-card" @click="generateReport('event')">
                           <div class="rt-icon">🔥</div>
                           <h4>事件专报</h4>
                           <p>针对具体爆发事件的深度复盘</p>
                       </div>
                       <div class="rt-card" @click="generateReport('weekly')">
                           <div class="rt-icon">📊</div>
                           <h4>周/月报</h4>
                           <p>阶段性总结与趋势分析</p>
                       </div>
                   </div>
              </div>
              <div class="report-history">
                  <h3>历史报告记录</h3>
                  <table class="rh-table">
                      <thead>
                          <tr><th>报告名称</th><th>类型</th><th>生成时间</th><th>操作</th></tr>
                      </thead>
                      <tbody>
                          <tr v-for="r in mockReports" :key="r.id">
                              <td>{{ r.name }}</td>
                              <td>{{ r.type }}</td>
                              <td>{{ r.time }}</td>
                              <td>
                                  <a href="#">下载PDF</a> | <a href="#">在线预览</a>
                              </td>
                          </tr>
                      </tbody>
                  </table>
              </div>
          </div>
      </template>
    </div>

    <!-- 创建专题弹窗 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="create-modal">
        <div class="cm-header">
          <h3>➕ 新建专题</h3>
          <button class="close-btn" @click="showCreateModal = false">×</button>
        </div>
        <div class="cm-tabs">
          <span :class="{ active: createMode === 'quick' }" @click="createMode = 'quick'">快速创建</span>
          <span :class="{ active: createMode === 'manual' }" @click="createMode = 'manual'">手动创建</span>
        </div>

        <!-- 快速创建 -->
        <div v-if="createMode === 'quick'" class="cm-body">
          <p class="hint">从热点预测榜单选择高潜力选题，一键导入：</p>
          <div class="hot-topics">
            <div v-for="hot in hotPredictions" :key="hot.id" class="hot-item" @click="selectHotTopic(hot)">
              <span class="hi-title">{{ hot.title }}</span>
              <span class="hi-score">潜力: {{ hot.score }}</span>
            </div>
          </div>
        </div>

        <!-- 手动创建 -->
        <div v-if="createMode === 'manual'" class="cm-body">
          <div class="form-group">
            <label>专题名称 *</label>
            <input v-model="newTopic.name" type="text" placeholder="输入专题名称（最多30字）" maxlength="30" />
          </div>
          <div class="form-group">
            <label>核心关键词 *</label>
            <input v-model="newTopic.keywords" type="text" placeholder="输入关键词，用逗号分隔" />
          </div>
          <div class="form-group">
            <label>监控平台 *</label>
            <div class="checkbox-group">
              <label><input type="checkbox" value="weibo" v-model="newTopic.platforms" /> 微博</label>
              <label><input type="checkbox" value="douyin" v-model="newTopic.platforms" /> 抖音</label>
              <label><input type="checkbox" value="xiaohongshu" v-model="newTopic.platforms" /> 小红书</label>
              <label><input type="checkbox" value="news" v-model="newTopic.platforms" /> 新闻</label>
            </div>
          </div>
          <div class="form-group">
            <label>监控时长</label>
            <select v-model="newTopic.duration">
              <option value="7">短期 7天</option>
              <option value="30">中期 30天</option>
              <option value="90">长期 90天</option>
            </select>
          </div>
          <div class="form-group">
            <label>选题标签</label>
            <input v-model="newTopic.tags" type="text" placeholder="输入标签，用逗号分隔" />
          </div>
        </div>

        <div class="cm-footer">
          <button class="btn" @click="showCreateModal = false">取消</button>
          <button class="btn primary" @click="createTopic">确认创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

// ECharts
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, PieChart, BarChart, GridComponent, TooltipComponent, LegendComponent])

const API_URL = import.meta.env.PROD 
  ? 'https://radar-backend-cvaq.onrender.com' 
  : 'http://localhost:8000'

// State
const loading = ref(false)
const topics = ref([])
const selectedTopic = ref(null)
const selectedTopics = ref([])
const page = ref(1)
const pageSize = ref(10)
const configCollapsed = ref(false)
const contentTab = ref('content')
const showCreateModal = ref(false)
const createMode = ref('quick')
const currentView = ref('dashboard') // Detail View
const props = defineProps({
  initialView: { type: String, default: 'dashboard' } 
})

// ...

const globalView = ref(props.initialView) // Global View

// Filters
const filters = ref({
  tag: '',
  status: '',
  platform: '',
  search: '',
  timeRange: '',
  sortBy: 'created_desc',
  heatMin: 0,
  heatMax: 100
})
const loadingStream = ref(false)

// New Topic Form
const newTopic = ref({
  name: '',
  keywords: '',
  platforms: ['weibo'],
  duration: '7',
  tags: ''
})

// Stream Items (Flash News)
const streamItems = ref([])

const fetchStream = async () => {
    loadingStream.value = true
    try {
        const token = localStorage.getItem('token')
        // Fetch published flashes (AI rewritten)
        const res = await axios.get(`${API_URL}/flash/list?status=published&limit=50`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        streamItems.value = res.data || []
    } catch (e) {
        console.error("Fetch stream error", e)
    } finally {
        loadingStream.value = false
    }
}

const mockReports = ref([
    { id: 1, name: '2026-02-01 日报', type: 'Daily', time: '2026-02-02 08:00' },
    { id: 2, name: '突发事件专报', type: 'Event', time: '2026-02-01 14:30' }
])

const generateReport = (type) => {
    alert(`正在生成 ${type} 报告，请稍候...`)
    setTimeout(() => {
        mockReports.value.unshift({
            id: Date.now(),
            name: `${type === 'daily' ? '日报' : type === 'event' ? '专报' : '周报'} - 新生成`,
            type: type.toUpperCase(),
            time: formatTime(new Date())
        })
        alert('报告生成成功！')
    }, 1000)
}

// Mock Data
const allTags = ref(['娱乐', '财经', '科技', '体育', '政务'])
const hotPredictions = ref([
  { id: 1, title: '2026春节档票房预测', score: 92 },
  { id: 2, title: '新能源汽车价格战', score: 88 },
  { id: 3, title: '科技公司裁员潮', score: 85 },
  { id: 4, title: 'AI大模型应用落地', score: 82 }
])

const topContents = ref([
  { id: 1, platform: 'weibo', title: '春节档票房破80亿，创历史新高', time: '2026-02-01T10:30:00', comments: 2800, likes: 15000, shares: 3200 },
  { id: 2, platform: 'douyin', title: '春节档电影深度解析，这些细节你注意到了吗', time: '2026-02-01T09:15:00', comments: 1500, likes: 28000, shares: 5000 },
  { id: 3, platform: 'xiaohongshu', title: '春节档观影指南，这几部电影值得二刷', time: '2026-02-01T08:45:00', comments: 890, likes: 12000, shares: 1800 }
])

const topKols = ref([
  { id: 1, name: '电影解说XXX', platform: 'weibo', followers: 1200000, engagement: 85000 },
  { id: 2, name: '娱乐八卦王', platform: 'douyin', followers: 850000, engagement: 62000 },
  { id: 3, name: '影评人小红', platform: 'xiaohongshu', followers: 520000, engagement: 38000 }
])

const derivedTopics = ref([
  { id: 1, name: '春节档某电影票房分析', score: 88 },
  { id: 2, name: '春节档导演作品对比', score: 75 },
  { id: 3, name: '春节档演员口碑排名', score: 72 }
])

const alerts = ref([
  { id: 1, time: '2026-02-01T10:30:00', type: 'burst', type_label: '爆发预警', description: '声量1小时内增长58%', status: 'handled' },
  { id: 2, time: '2026-02-01T08:15:00', type: 'negative', type_label: '跑偏预警', description: '负面占比达到42%', status: 'pending' }
])

// Computed
const filteredTopics = computed(() => {
  const now = new Date()
  return topics.value.filter(t => {
    if (filters.value.tag && !t.tags?.includes(filters.value.tag)) return false
    if (filters.value.status && t.status !== filters.value.status) return false
    if (filters.value.platform && !t.platforms?.includes(filters.value.platform)) return false
    if (filters.value.search && !t.name.includes(filters.value.search) && !t.keywords?.some(k => k.includes(filters.value.search))) return false
    // Time range filter
    if (filters.value.timeRange) {
      const created = new Date(t.created_at)
      const days = (now - created) / (1000 * 60 * 60 * 24)
      if (filters.value.timeRange === 'today' && days > 1) return false
      if (filters.value.timeRange === '7d' && days > 7) return false
      if (filters.value.timeRange === '30d' && days > 30) return false
    }
    return true
  })
})

// Sorted topics based on filter
const sortedTopics = computed(() => {
  const list = [...filteredTopics.value]
  const sortBy = filters.value.sortBy
  if (sortBy === 'volume_desc') list.sort((a, b) => b.volume - a.volume)
  else if (sortBy === 'heat_desc') list.sort((a, b) => b.heat_score - a.heat_score)
  else if (sortBy === 'alert_desc') list.sort((a, b) => (b.unread_alerts || 0) - (a.unread_alerts || 0))
  else list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  return list
})

// Can batch delete - only paused/archived topics
const canBatchDelete = computed(() => {
  if (selectedTopics.value.length === 0) return false
  return selectedTopics.value.every(id => {
    const t = topics.value.find(x => x.id === id)
    return t && (t.status === 'paused' || t.status === 'archived')
  })
})

const totalPages = computed(() => Math.ceil(sortedTopics.value.length / pageSize.value) || 1)

// Chart Options
const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { top: 20, right: 20, bottom: 30, left: 50 },
  xAxis: { 
    type: 'category', 
    data: ['00:00', '02:00', '04:00', '06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'],
    axisLabel: { fontSize: 10 }
  },
  yAxis: { type: 'value', axisLabel: { fontSize: 10 } },
  series: [{
    type: 'line',
    smooth: true,
    data: [120, 80, 60, 90, 180, 350, 420, 380, 450, 520, 480, 400],
    areaStyle: { color: 'rgba(59, 130, 246, 0.2)' },
    itemStyle: { color: '#3b82f6' }
  }]
}))

const platformChartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { fontSize: 10 } },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: [
      { value: 45, name: '微博', itemStyle: { color: '#ef4444' } },
      { value: 30, name: '抖音', itemStyle: { color: '#000' } },
      { value: 15, name: '小红书', itemStyle: { color: '#fe2c55' } },
      { value: 10, name: '新闻', itemStyle: { color: '#64748b' } }
    ],
    label: { show: false }
  }]
}))

const sentimentChartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { fontSize: 10 } },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: [
      { value: 55, name: '正面', itemStyle: { color: '#10b981' } },
      { value: 30, name: '中性', itemStyle: { color: '#fcd34d' } },
      { value: 15, name: '负面', itemStyle: { color: '#ef4444' } }
    ],
    label: { show: false }
  }]
}))

// Methods
const fetchTopics = async () => {
  loading.value = true
  // Fetch stream if global view is stream
  if (globalView.value === 'stream') {
      fetchStream()
  }
  
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`${API_URL}/topics`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    topics.value = res.data.topics || []
  } catch (e) {
    console.error('Failed to fetch topics:', e)
    topics.value = [
      { 
        id: 1, name: '2026春节档票房预测', status: 'monitoring', owner: '张三',
        created_at: '2026-01-28', duration: 7, remaining_days: 3,
        volume: 125800, volume_change: 28, heat_score: 92, negative_ratio: 15,
        tags: ['娱乐', '电影'], platforms: ['weibo', 'douyin', 'xiaohongshu'],
        keywords: ['春节档', '票房', '电影'], unread_alerts: 2
      },
      { 
        id: 2, name: '新能源汽车价格战分析', status: 'monitoring', owner: '李四',
        created_at: '2026-01-25', duration: 30, remaining_days: 24,
        volume: 85600, volume_change: -5, heat_score: 78, negative_ratio: 42,
        tags: ['财经', '汽车'], platforms: ['weibo', 'news'],
        keywords: ['新能源', '价格战', '电动车'], unread_alerts: 1
      },
      { 
        id: 3, name: 'AI大模型应用落地', status: 'paused', owner: '王五',
        created_at: '2026-01-20', duration: 30, remaining_days: 19,
        volume: 62000, volume_change: 12, heat_score: 85, negative_ratio: 8,
        tags: ['科技', 'AI'], platforms: ['weibo', 'news', 'douyin'],
        keywords: ['AI大模型', 'ChatGPT', '应用落地'], unread_alerts: 0
      }
    ]
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value = { tag: '', status: '', platform: '', search: '', timeRange: '', sortBy: 'created_desc', heatMin: 0, heatMax: 100 }
}

const viewTopic = (topic) => {
  selectedTopic.value = topic
}

const editTopic = (topic) => {
  alert('编辑功能开发中: ' + topic.name)
}

const togglePause = (topic) => {
  topic.status = topic.status === 'paused' ? 'monitoring' : 'paused'
}

const exportReport = () => {
  alert('报告导出功能开发中')
}

const archiveTopic = () => {
  if (confirm('确认归档该专题？归档后将停止数据采集。')) {
    selectedTopic.value.status = 'archived'
    alert('专题已归档')
  }
}

const batchArchive = () => {
  if (confirm(`确认归档选中的 ${selectedTopics.value.length} 个专题？`)) {
    topics.value.forEach(t => {
      if (selectedTopics.value.includes(t.id)) {
        t.status = 'archived'
      }
    })
    selectedTopics.value = []
  }
}

const batchDelete = () => {
  if (confirm(`确认删除选中的 ${selectedTopics.value.length} 个专题？此操作不可恢复。`)) {
    topics.value = topics.value.filter(t => !selectedTopics.value.includes(t.id))
    selectedTopics.value = []
  }
}

const selectHotTopic = (hot) => {
  newTopic.value.name = hot.title
  newTopic.value.keywords = hot.title.split(/[，,、\s]+/).slice(0, 3).join(',')
  createMode.value = 'manual'
}

const createTopic = async () => {
  if (!newTopic.value.name) {
    alert('请输入专题名称')
    return
  }
  if (!newTopic.value.keywords) {
    alert('请输入核心关键词')
    return
  }
  if (newTopic.value.platforms.length === 0) {
    alert('请选择至少一个监控平台')
    return
  }

  const topic = {
    id: Date.now(),
    name: newTopic.value.name,
    status: 'monitoring',
    owner: '当前用户',
    created_at: new Date().toISOString().split('T')[0],
    duration: parseInt(newTopic.value.duration),
    remaining_days: parseInt(newTopic.value.duration),
    volume: 0,
    volume_change: 0,
    heat_score: 0,
    negative_ratio: 0,
    tags: newTopic.value.tags.split(/[，,、]/).filter(Boolean),
    platforms: newTopic.value.platforms,
    keywords: newTopic.value.keywords.split(/[，,、]/).filter(Boolean)
  }

  topics.value.unshift(topic)
  showCreateModal.value = false
  newTopic.value = { name: '', keywords: '', platforms: ['weibo'], duration: '7', tags: '' }
  alert('专题创建成功！')
}

const createDerivedTopic = (derived) => {
  newTopic.value.name = derived.name
  newTopic.value.keywords = selectedTopic.value?.keywords?.join(',') || ''
  newTopic.value.platforms = selectedTopic.value?.platforms || ['weibo']
  showCreateModal.value = true
  createMode.value = 'manual'
}

// Helpers
const getStatusLabel = (status) => {
  const labels = { monitoring: '监控中', paused: '已暂停', archived: '已归档', ended: '已结束' }
  return labels[status] || status
}

const getPlatformLabel = (platform) => {
  const labels = { weibo: '微博', douyin: '抖音', xiaohongshu: '小红书', news: '新闻', bilibili: 'B站' }
  return labels[platform] || platform
}

const formatNumber = (num) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return num?.toString() || '0'
}

const formatDate = (date) => {
  if (!date) return ''
  return date.split('T')[0]
}

const formatTime = (time) => {
  if (!time) return ''
  const d = new Date(time)
  const now = new Date()
  if (d.toDateString() === now.toDateString()) {
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  }
  return `${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

// Volume change class helper
const getVolumeClass = (change) => {
  if (change >= 20) return 'burst'
  if (change >= 10) return 'high'
  if (change >= 0) return 'up'
  return 'down'
}

// Go to alerts for topic
const goToAlerts = (topic) => {
  selectedTopic.value = topic
  // Scroll to alerts section
}

// Export single topic report
const exportSingleReport = (topic) => {
  alert(`导出「${topic.name}」报告功能开发中`)
}

// Lifecycle
onMounted(() => {
  fetchTopics()
})
</script>

<style scoped>
.topic-monitor {
  height: 100%;
  background: #f1f5f9;
  overflow-y: auto;
}

/* List View */
.list-view { padding: 24px; }

.tm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.tm-header h2 { margin: 0; font-size: 22px; color: #1e293b; }
.tm-actions { display: flex; gap: 8px; }

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  background: #e2e8f0;
  color: #475569;
  font-weight: 500;
  transition: all 0.2s;
}
.btn:hover { background: #cbd5e1; }
.btn.primary { background: #3b82f6; color: white; }
.btn.primary:hover { background: #2563eb; }
.btn.secondary { background: white; border: 1px solid #e2e8f0; color: #64748b; }
.btn.secondary:hover { background: #f8fafc; border-color: #cbd5e1; }
.btn.danger-text { color: #dc2626; }
.btn.danger-text:hover { background: #fef2f2; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn:disabled:hover { background: white; }

/* Filters - Enhanced */
.tm-filters {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.filter-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}
.filter-search {
  flex: 1;
  min-width: 200px;
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  background: #f8fafc;
}
.filter-search:focus {
  outline: none;
  border-color: #3b82f6;
  background: white;
}
.filter-select {
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  background: white;
  cursor: pointer;
}
.filter-select:focus { outline: none; border-color: #3b82f6; }

/* Topic List */
.topic-list { display: flex; flex-direction: column; gap: 10px; }

/* Skeleton Loading */
.skeleton-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background: white;
  border-radius: 12px;
  padding: 16px 20px;
  border: 1px solid #e2e8f0;
}
.sk-checkbox {
  width: 18px;
  height: 18px;
  background: #e2e8f0;
  border-radius: 4px;
  animation: skeleton-pulse 1.5s infinite;
}
.sk-content { flex: 1; }
.sk-line {
  height: 14px;
  background: #e2e8f0;
  border-radius: 4px;
  margin-bottom: 8px;
  animation: skeleton-pulse 1.5s infinite;
}
.sk-line.w60 { width: 60%; }
.sk-line.w40 { width: 40%; }
.sk-stats { display: flex; gap: 16px; }
.sk-stat {
  width: 80px;
  height: 40px;
  background: #e2e8f0;
  border-radius: 8px;
  animation: skeleton-pulse 1.5s infinite;
}
@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  border: 1px dashed #cbd5e1;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-state p { color: #64748b; margin-bottom: 20px; }

/* Topic Card - Enhanced Layout */
.topic-card {
  position: relative;
  display: flex;
  align-items: stretch;
  gap: 12px;
  background: white;
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e2e8f0;
}
.topic-card:hover { 
  box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
  transform: translateY(-1px);
  border-color: #cbd5e1;
}
.topic-card.selected { border-color: #3b82f6; background: #f0f9ff; }
.topic-card.has-alert { border-left: 3px solid #ef4444; }

/* Checkbox */
.tc-checkbox {
  position: absolute;
  top: 12px;
  left: 12px;
}
.tc-checkbox input {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #3b82f6;
}

/* Alert Icon */
.tc-alert {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 16px;
  cursor: pointer;
  animation: alert-pulse 1.5s infinite;
}
@keyframes alert-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* Card Body */
.tc-body {
  flex: 1;
  padding-left: 28px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Row 1: Title + Meta */
.tc-row-1 {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 8px;
}
.tc-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}
.tc-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}
.tc-status {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 600;
  color: white;
}
.tc-status.monitoring { background: #10b981; }
.tc-status.paused { background: #94a3b8; }
.tc-status.archived { background: #3b82f6; }
.tc-status.ended { background: #64748b; }

.tc-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 12px;
  color: #64748b;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.avatar {
  width: 20px;
  height: 20px;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}
.remaining.urgent { color: #ef4444; font-weight: 600; }

/* Row 2: Stats */
.tc-row-2 {
  display: flex;
  gap: 32px;
}
.tc-stat {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.stat-label {
  font-size: 12px;
  color: #94a3b8;
}
.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}
.stat-value.heat { color: #f59e0b; }
.stat-value.negative { color: #ef4444; }
.stat-value.blink { animation: blink-warn 1s infinite; }
@keyframes blink-warn {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.stat-arrow {
  font-size: 12px;
  font-weight: 600;
}
.stat-arrow.burst { color: #ef4444; }
.stat-arrow.high { color: #f59e0b; }
.stat-arrow.up { color: #10b981; }
.stat-arrow.down { color: #ef4444; }

/* Row 3: Tags + Actions */
.tc-row-3 {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tc-tags { display: flex; gap: 6px; }
.tag {
  font-size: 11px;
  padding: 3px 10px;
  background: #f1f5f9;
  color: #475569;
  border-radius: 12px;
}
.tag.more { background: #e2e8f0; }

.tc-quick-actions {
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.2s;
}
.topic-card:hover .tc-quick-actions { opacity: 1; }
.qa-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f1f5f9;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.qa-btn:hover { background: #e2e8f0; transform: scale(1.1); }

/* Pagination */
.tm-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding: 16px 0;
  font-size: 13px;
  color: #64748b;
}
.page-controls { display: flex; align-items: center; gap: 12px; }
.page-controls button {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 6px;
  cursor: pointer;
}
.page-controls button:disabled { opacity: 0.5; cursor: not-allowed; }

/* Detail View */
.detail-view { padding: 24px; }

.dv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.dv-left { display: flex; align-items: center; gap: 16px; }
.back-btn {
  background: none;
  border: none;
  color: #3b82f6;
  cursor: pointer;
  font-size: 14px;
}
.dv-header h2 { margin: 0; font-size: 20px; }
.dv-status {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 6px;
}
.dv-status.monitoring { background: #dcfce7; color: #16a34a; }
.dv-status.paused { background: #f1f5f9; color: #64748b; }
.dv-actions { display: flex; gap: 8px; }



/* Global View Tabs */
.tm-tabs {
    display: flex; gap: 4px; background: #e2e8f0; padding: 4px; border-radius: 8px; margin: 0 16px;
}
.tm-tabs span {
    padding: 6px 12px; font-size: 13px; cursor: pointer; border-radius: 6px; color: #64748b; font-weight: 500;
}
.tm-tabs span.active { background: white; color: #2563eb; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }

/* Detail View Tabs */
.dv-tabs {
    display: flex; gap: 4px; background: #e2e8f0; padding: 4px; border-radius: 8px; margin: 0 16px;
}
.dv-tabs span {
    padding: 6px 12px; font-size: 13px; cursor: pointer; border-radius: 6px; color: #64748b; font-weight: 500;
}
.dv-tabs span.active { background: white; color: #2563eb; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }

/* Stream View */
.stream-container { background: white; border-radius: 12px; padding: 20px; min-height: 500px; }
.stream-filter-bar { display: flex; gap: 12px; margin-bottom: 20px; align-items: center; }
.sf-search { flex: 1; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; }
.stream-list { display: flex; flex-direction: column; gap: 16px; }
.stream-item { display: flex; gap: 16px; padding: 16px; border: 1px solid #f1f5f9; border-radius: 8px; }
.si-left { display: flex; flex-direction: column; gap: 4px; width: 80px; font-size: 12px; color: #94a3b8; }
.si-platform { font-weight: 600; }
.si-platform.weibo { color: #ef4444; } .si-platform.douyin { color: #000; }
.si-main { flex: 1; }
.si-title { font-weight: 700; margin-bottom: 4px; color: #1e293b; }
.si-snippet { font-size: 13px; color: #475569; margin-bottom: 8px; }
.si-meta { font-size: 12px; color: #64748b; display: flex; gap: 12px; }
.text-red { color: #ef4444; } .text-green { color: #10b981; }
.si-right { display: flex; flex-direction: column; gap: 8px; }
.btn-sm { padding: 4px 8px; font-size: 12px; border: 1px solid #e2e8f0; border-radius: 4px; background: white; cursor: pointer; }

/* Report View */
.report-center { display: flex; flex-direction: column; gap: 24px; padding-top: 10px; }
.report-tools { background: white; padding: 24px; border-radius: 12px; }
.report-tools h3 { margin: 0 0 20px 0; font-size: 16px; }
.rt-options { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.rt-card { border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; align-items: center; text-align: center; }
.rt-card:hover { border-color: #3b82f6; background: #eff6ff; }
.rt-icon { font-size: 32px; margin-bottom: 12px; }
.rt-card h4 { margin: 0 0 8px 0; color: #1e293b; }
.rt-card p { margin: 0; font-size: 12px; color: #64748b; }

.report-history { background: white; padding: 24px; border-radius: 12px; }
.rh-table { width: 100%; border-collapse: collapse; margin-top: 16px; }
.rh-table th, .rh-table td { padding: 12px; text-align: left; border-bottom: 1px solid #f1f5f9; font-size: 13px; }
.rh-table th { color: #64748b; font-weight: 500; }
.rh-table a { color: #2563eb; text-decoration: none; margin-right: 8px; }

/* Statistics Cards */
.dv-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  flex: 1;
  background: white;
  padding: 16px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.sc-label { display: block; font-size: 12px; color: #64748b; margin-bottom: 4px; }
.sc-value { display: block; font-size: 24px; font-weight: 700; color: #1e293b; }
.sc-value.warning { color: #ef4444; }
.sc-change { font-size: 12px; }
.sc-change.up { color: #10b981; }
.sc-change.down { color: #ef4444; }

/* Body Layout */
.dv-body {
  display: grid;
  grid-template-columns: 200px 1fr 300px;
  gap: 20px;
  margin-bottom: 24px;
}

/* Config Panel */
.dv-config {
  background: white;
  border-radius: 12px;
  overflow: hidden;
}
.config-header {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f8fafc;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
}
.config-content { padding: 16px; }
.config-item { margin-bottom: 16px; }
.config-item label { display: block; font-size: 12px; color: #64748b; margin-bottom: 6px; }
.keywords, .platforms { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 6px; }
.kw-tag, .platform-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: #eff6ff;
  color: #3b82f6;
  border-radius: 4px;
}
.config-desc { font-size: 12px; color: #64748b; margin: 0 0 6px 0; }
.config-edit {
  font-size: 11px;
  padding: 4px 8px;
  border: none;
  background: #f1f5f9;
  border-radius: 4px;
  cursor: pointer;
}

/* Charts */
.dv-charts {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.chart-section {
  background: white;
  padding: 16px;
  border-radius: 12px;
}
.chart-section h4 { margin: 0 0 12px 0; font-size: 14px; color: #1e293b; }
.chart { width: 100%; height: 200px; }
.chart-row { display: flex; gap: 16px; }
.chart-half {
  flex: 1;
  background: white;
  padding: 16px;
  border-radius: 12px;
}
.chart-half h4 { margin: 0 0 12px 0; font-size: 14px; }
.chart-sm { width: 100%; height: 180px; }

/* Content Panel */
.dv-content {
  background: white;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
}
.content-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.content-tabs span {
  padding: 6px 12px;
  font-size: 12px;
  color: #64748b;
  cursor: pointer;
  border-radius: 6px;
}
.content-tabs span.active { background: #3b82f6; color: white; }

.content-list, .kol-list, .derived-list {
  flex: 1;
  overflow-y: auto;
  max-height: 400px;
}

.content-item {
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
}
.ci-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.ci-platform { font-size: 11px; color: #3b82f6; }
.ci-time { font-size: 11px; color: #94a3b8; }
.ci-title { margin: 0 0 8px 0; font-size: 13px; color: #1e293b; line-height: 1.4; }
.ci-stats { display: flex; gap: 12px; font-size: 11px; color: #64748b; }
.ci-action {
  margin-top: 8px;
  font-size: 11px;
  padding: 4px 8px;
  border: none;
  background: #f1f5f9;
  border-radius: 4px;
  cursor: pointer;
}

.kol-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
}
.kol-avatar {
  width: 36px;
  height: 36px;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}
.kol-info { flex: 1; }
.kol-name { display: block; font-size: 13px; font-weight: 600; color: #1e293b; }
.kol-platform { font-size: 11px; color: #64748b; }
.kol-stats { font-size: 11px; color: #64748b; display: flex; flex-direction: column; gap: 2px; }

.derived-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
}
.di-main { display: flex; flex-direction: column; gap: 4px; }
.di-title { font-size: 13px; color: #1e293b; }
.di-score { font-size: 11px; color: #f59e0b; }
.di-btn {
  font-size: 11px;
  padding: 4px 10px;
  border: none;
  background: #dbeafe;
  color: #2563eb;
  border-radius: 4px;
  cursor: pointer;
}

/* Alerts */
.dv-alerts {
  background: white;
  border-radius: 12px;
  padding: 16px;
}
.dv-alerts h4 { margin: 0 0 12px 0; font-size: 14px; }
.alert-list { max-height: 200px; overflow-y: auto; }
.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 12px;
}
.al-time { color: #64748b; min-width: 100px; }
.al-type {
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}
.al-type.burst { background: #fff7ed; color: #ea580c; }
.al-type.decline { background: #dbeafe; color: #2563eb; }
.al-type.negative { background: #fef2f2; color: #dc2626; }
.al-desc { flex: 1; color: #475569; }
.al-status { font-weight: 500; }
.al-status.handled { color: #10b981; }
.al-status.pending { color: #f59e0b; }

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.create-modal {
  width: 560px;
  background: white;
  border-radius: 16px;
  overflow: hidden;
}
.cm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}
.cm-header h3 { margin: 0; font-size: 18px; }
.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f1f5f9;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
}
.cm-tabs {
  display: flex;
  gap: 8px;
  padding: 16px 24px;
  background: #f8fafc;
}
.cm-tabs span {
  padding: 8px 16px;
  font-size: 13px;
  color: #64748b;
  cursor: pointer;
  border-radius: 6px;
}
.cm-tabs span.active { background: white; color: #3b82f6; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.cm-body { padding: 24px; max-height: 400px; overflow-y: auto; }
.hint { font-size: 13px; color: #64748b; margin-bottom: 16px; }

.hot-topics { display: flex; flex-direction: column; gap: 8px; }
.hot-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid #e2e8f0;
}
.hot-item:hover { border-color: #3b82f6; background: #eff6ff; }
.hi-title { font-size: 13px; color: #1e293b; }
.hi-score { font-size: 12px; color: #f59e0b; font-weight: 600; }

.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px; }
.form-group input, .form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
}
.checkbox-group { display: flex; gap: 16px; flex-wrap: wrap; }
.checkbox-group label { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #475569; }

.cm-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}
</style>
