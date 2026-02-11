<template>
  <nav class="sidebar">
    <div class="logo-area">
      <img src="https://images.tmtpost.com/uploads/images/zhaopian/nuxtpic/logo_home.svg" class="logo-img" alt="Logo" />
      <h1 class="logo-text">钛媒体·智编</h1>
    </div>

    <div class="nav-menu">
      
      <!-- 1. 我的看板 -->
      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'my_dashboard' }"
        @click="$emit('change', 'my_dashboard')"
      >
        <span class="icon">💻</span> 我的看板
      </div>

      <!-- 2. 舆情管理 -->
      <div class="nav-group-title" style="margin-top: 24px;">舆情管理</div>
      
      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'hotlist' }"
        @click="$emit('change', 'hotlist')"
      >
        <span class="icon">🔥</span> 今日热榜
      </div>

      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'prediction' }"
        @click="$emit('change', 'prediction')"
      >
        <span class="icon">🚀</span> 热点预测
      </div>

      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'monitor' }"
        @click="$emit('change', 'monitor')"
      >
        <span class="icon">📉</span> 舆情监控
      </div>

      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'topic_monitor' }"
        @click="$emit('change', 'topic_monitor')"
      >
        <span class="icon">📊</span> 专题监控
        <span class="alert-badge" v-if="topicAlertCount > 0">{{ topicAlertCount > 9 ? '9+' : topicAlertCount }}</span>
      </div>

      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'flash_monitor' }"
        @click="$emit('change', 'flash_monitor')"
      >
        <span class="icon">⚡</span> 快报监控
      </div>

      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'reports_center' }"
        @click="$emit('change', 'reports_center')"
      >
        <span class="icon">📑</span> 报告中心
      </div>

      <!-- 3. 我的创作 -->
      <div class="nav-group-title" style="margin-top: 24px;">我的创作</div>

      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'my_selections' }"
        @click="$emit('change', 'my_selections')"
      >
        <span class="icon">✍️</span> 创作(选题)
      </div>

      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'article_manager' }"
        @click="$emit('change', 'article_manager')"
      >
        <span class="icon">📝</span> 文章管理
      </div>

      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'flash_manager' }"
        @click="$emit('change', 'flash_manager')"
      >
        <span class="icon">⚡</span> 快报管理
      </div>

      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'video_manager' }"
        @click="$emit('change', 'video_manager')"
      >
        <span class="icon">🎬</span> 视频管理
      </div>

      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'tag_manager' }"
        @click="$emit('change', 'tag_manager')"
      >
        <span class="icon">🏷️</span> 标签管理
      </div>

      <!-- 3. 知识管理 -->
      <div class="nav-group-title" style="margin-top: 24px;">知识管理</div>

       <div 
        class="nav-item" 
        :class="{ active: currentTab === 'customer' }"
        @click="$emit('change', 'customer')"
      >
        <span class="icon">👥</span> 客户管理
      </div>
      
      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'knowledge' }"
        @click="$emit('change', 'knowledge')"
      >
        <span class="icon">📚</span> 客户知识库
      </div>

      <div 
        class="nav-item" 
        :class="{ active: currentTab === 'content_library' }"
        @click="$emit('change', 'content_library')"
      >
        <span class="icon">🌐</span> 全网内容库
      </div>

      <!-- 4. 系统管理 -->
      <div class="nav-group-title" style="margin-top: 24px;" v-if="userRole === 'admin'">系统管理</div>

      <div 
        class="nav-item admin" 
        v-if="userRole === 'admin'"
        :class="{ active: currentTab === 'users' }"
        @click="$emit('change', 'users')"
      >
        <span class="icon">🔑</span> 权限控制
      </div>

    </div>
    
    <div class="nav-footer">
       <!-- User Info (Moved from Top Header) -->
       <div class="sidebar-user-info" v-if="username">
          <div class="user-avatar">{{ username.charAt(0).toUpperCase() }}</div>
          <div class="user-details">
            <div class="u-name">{{ username }}</div>
            <div class="u-role">{{ userRole }}</div>
          </div>
       </div>

       <div class="nav-item logout" @click="$emit('logout')">
          <span class="icon">🚪</span> 退出登录
       </div>
    </div>
  </nav>
</template>

<script setup>
defineProps(['currentTab', 'userRole', 'username', 'topicAlertCount'])
defineEmits(['change', 'logout'])
</script>

<style scoped>
.sidebar {
  width: 240px;
  background: #0b1121; /* Darker slate */
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  box-shadow: 2px 0 10px rgba(0,0,0,0.2);
  z-index: 10;
}

.logo-area {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  padding: 24px 20px;
  gap: 12px;
  border-bottom: 1px solid #1e293b;
  margin-bottom: 10px;
}

.logo-img { 
  height: 28px; 
  display: block;
}

.logo-text {
  font-size: 18px;
  font-weight: 800;
  color: white;
  margin: 0;
  letter-spacing: 1px;
  line-height: 1.2;
}

.nav-menu {
  padding: 24px 12px;
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow-y: auto;
}

.nav-group-title {
    font-size: 11px;
    color: #64748b;
    padding: 0 12px;
    margin-top: 24px;
    margin-bottom: 6px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.nav-item {
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 2px;
}

.nav-item:hover {
  background: #1e293b;
  color: white;
}

.nav-item.active {
  background: #2563eb;
  color: white;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.nav-item.admin {
    margin-top: 2px;
    color: #fca5a5;
    background: rgba(127, 29, 29, 0.2);
}
.nav-item.admin:hover { background: rgba(127, 29, 29, 0.4); }
.nav-item.admin.active { background: #b91c1c; color: white; }

.nav-footer { 
  padding: 16px; 
  border-top: 1px solid #1e293b; 
  background: #0f172a;
}
.sidebar-user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px 16px 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid #1e293b;
}
.user-avatar {
  width: 32px; height: 32px;
  background: #2563eb; color: white;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: bold; font-size: 14px;
}
.user-details { display: flex; flex-direction: column; }
.u-name { font-size: 13px; font-weight: 600; color: white; }
.u-role { font-size: 11px; color: #94a3b8; text-transform: uppercase; }

.nav-item.logout { 
  color: #ef4444; 
  justify-content: flex-start;
  margin-bottom: 0;
  margin-top: 8px;
} 
.nav-item.logout:hover { background: rgba(239, 68, 68, 0.1); }

/* Scrollbar styling */
.nav-menu::-webkit-scrollbar { width: 4px; }
.nav-menu::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }

/* Alert badge for unread alerts count */
.alert-badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: #ef4444;
  border-radius: 9px;
  margin-left: auto;
  font-size: 11px;
  font-weight: 600;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pulse-badge 2s ease-in-out infinite;
}
@keyframes pulse-badge {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
</style>