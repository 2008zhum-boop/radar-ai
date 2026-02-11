<template>
  <!-- 认证流程 -->
  <div v-if="!isAuthenticated" class="auth-container">
    <Login v-if="authView==='login'" @switch="authView=$event" @success="handleAuthSuccess" />
    <Register v-else @switch="authView=$event" />
  </div>

  <!-- 主应用界面 -->
  <div v-else class="app-container">
    <SidebarNav 
      :currentTab="currentTab" 
      :userRole="userProfile?.role" 
      :username="userProfile?.username"
      :topicAlertCount="topicAlertCount"
      @change="currentTab = $event" 
      @logout="handleLogout"
    />
    
    <main class="main-content">
      <!-- 顶部状态栏 -->
      <header class="top-header" v-if="false">
        <!-- 暂时隐藏 TopHeader，或者保留用于其他功能 -->
      </header>

      <!-- 内容区域 -->
      <!-- 内容区域 -->
      <!-- HotList 使用 v-show 保持存活，避免切换Tab时重载 -->
      <div v-show="currentTab === 'hotlist'" class="page-view">
        <HotList />
      </div>

      <div v-if="currentTab === 'prediction'" class="page-view">
        <HotPrediction />
      </div>

      <div v-else-if="currentTab === 'editor'" class="page-view">
        <SmartEditor />
      </div>

      <div v-else-if="currentTab === 'my_dashboard'" class="page-view">
        <MonitorDashboard :mode="'global'" />
      </div>

      <div v-else-if="currentTab === 'monitor'" class="page-view">
        <MonitorDashboard />
      </div>

      <div v-else-if="currentTab === 'topic_monitor'" class="page-view">
        <TopicMonitor />
      </div>

      <div v-else-if="currentTab === 'flash_monitor'" class="page-view">
        <FlashNewsMonitor />
      </div>

      <div v-else-if="currentTab === 'customer'" class="page-view">
        <ClientManager />
      </div>

      <div v-else-if="currentTab === 'reports_center'" class="page-view">
        <div style="padding: 40px; text-align: center; color: #64748b;">
            <h2>📑 报告中心</h2>
            <p>全站舆情报告均将汇总于此 [开发中]</p>
        </div>
      </div>

      <div v-else-if="currentTab === 'knowledge'" class="page-view">
        <div style="padding: 40px; text-align: center; color: #64748b;">
            <h2>📚 客户知识库</h2>
            <p>RAG 知识库管理 [开发中]</p>
        </div>
      </div>

      <div v-else-if="currentTab === 'content_library'" class="page-view">
        <GlobalContentLibrary />
      </div>

      <!-- My Creations -->
      <div v-else-if="currentTab === 'my_selections'" class="page-view">
        <SelectionManager />
      </div>

      <div v-else-if="currentTab === 'article_manager'" class="page-view">
         <ArticleManager />
      </div>

      <div v-else-if="currentTab === 'flash_manager'" class="page-view">
         <!-- Reuse Monitor UI for Management -->
         <FlashNewsMonitor />
      </div>

      <div v-else-if="currentTab === 'video_manager'" class="page-view">
         <VideoManager />
      </div>

      <div v-else-if="currentTab === 'tag_manager'" class="page-view">
         <TagManager />
      </div>

      <!-- Agent Manager (if needed somewhere else, or keep hidden/dev) -->
      <div v-else-if="currentTab === 'agents'" class="page-view">
         <AgentManager />
      </div>

      <div v-else-if="currentTab === 'reports_center'" class="page-view">
        <div style="padding: 40px; text-align: center; color: #64748b;">
            <h2>📑 报告中心</h2>
            <p>全站舆情报告均将汇总于此 [开发中]</p>
        </div>
      </div>

      <!-- Removed old 'knowledge' block as it seems replaced by content_library/agents/tags 
           or user intends 'customer' to be distinct from 'knowledge'. 
           User's list: 4. Knowledge Management (Customer, Content, Agent, Tag).
           So 'knowledge' tab itself is probably gone/replaced.
      -->
      
      <div v-else-if="currentTab === 'users'" class="page-view">
        <UserManager />
      </div>
    </main>
    
    <!-- 全局报告弹窗 -->
    <ReportModal 
       v-if="showReportModal" 
       :data="reportData" 
       @close="showReportModal = false" 
    />
  </div>
</template>

<script setup>
import { ref, onMounted, provide } from 'vue'
import SidebarNav from './components/SidebarNav.vue'
import HotList from './components/HotList.vue'
import HotPrediction from './components/HotPrediction.vue'
import SmartEditor from './components/SmartEditor.vue'
import MonitorDashboard from './components/MonitorDashboard.vue'
import TopicMonitor from './components/TopicMonitor.vue'
import ClientManager from './components/ClientManager.vue'
import GlobalContentLibrary from './components/GlobalContentLibrary.vue'
import UserManager from './components/UserManager.vue'
import ReportModal from './components/ReportModal.vue'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import SelectionManager from './components/SelectionManager.vue'
import ArticleManager from './components/ArticleManager.vue'
import AgentManager from './components/AgentManager.vue'
import TagManager from './components/TagManager.vue'
import FlashNewsMonitor from './components/FlashNewsMonitor.vue'
import VideoManager from './components/VideoManager.vue'
import { getProfile } from './services/api'

// Auth State
const isAuthenticated = ref(false)
const authView = ref('login')
const userProfile = ref(null)

// App State
const currentTab = ref('hotlist')
const showReportModal = ref(false)
const reportData = ref(null)
const topicAlertCount = ref(2) // 专题监控未读预警数量

// Check Auth on Load
onMounted(async () => {
  const token = localStorage.getItem('token')
  if (token) {
    try {
      const user = await getProfile()
      if (user) {
        userProfile.value = user
        isAuthenticated.value = true
      } else {
        throw new Error("Invalid Token")
      }
    } catch {
      localStorage.removeItem('token')
      isAuthenticated.value = false
    }
  }
})

const handleAuthSuccess = async () => {
    const user = await getProfile()
    userProfile.value = user
    isAuthenticated.value = true
    currentTab.value = 'hotlist'
}

const handleLogout = () => {
    localStorage.removeItem('token')
    isAuthenticated.value = false
    userProfile.value = null
    authView.value = 'login'
}

// Global Event Bus for Report
provide('openReport', (data) => {
    reportData.value = data
    showReportModal.value = true
})
</script>

<style scoped>
.app-container { display: flex; height: 100vh; background-color: #f1f5f9; overflow: hidden; }
.main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; position: relative; }
.page-view { flex: 1; overflow-y: auto; padding: 0; min-height: 0;}
.top-header { background: white; padding: 10px 24px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: flex-end; align-items: center; }
.user-info { font-size: 14px; color: #64748b; display: flex; align-items: center; gap: 8px; }
.role-tag { background: #eff6ff; color: #3b82f6; padding: 2px 6px; border-radius: 4px; font-size: 11px; text-transform: uppercase; font-weight: 700; }
</style>