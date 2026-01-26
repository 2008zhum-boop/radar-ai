<template>
  <div class="nav-container">
    <div class="brand-area">
      <img 
        src="https://images.tmtpost.com/uploads/images/zhaopian/nuxtpic/logo_home.svg" 
        class="logo-img" 
        alt="钛媒体"
      />
      <div class="brand-text">
        <h2>钛媒体·智编</h2>
        <span class="version">AI版</span>
      </div>
    </div>
    
    <nav class="menu-scroll-area">
      <div class="menu-group">
        <div class="group-title">默认项目</div>
        <div 
          class="menu-item" 
          :class="{ 'active-item': currentTab === 'workbench' }"
          @click="$emit('change', 'workbench')"
        >
          <span class="icon">💻</span> 我的工作台
        </div>
        <div 
          class="menu-item"
          :class="{ 'active-item': currentTab === 'write' }"
          @click="$emit('change', 'write')"
        >
          <span class="icon">✍️</span> 写文章
        </div>
        <div 
          class="menu-item"
          :class="{ 'active-item': currentTab === 'video' }"
          @click="$emit('change', 'video')"
        >
          <span class="icon">📹</span> 发视频
        </div>
        <div 
          class="menu-item"
          :class="{ 'active-item': currentTab === 'works' }"
          @click="$emit('change', 'works')"
        >
          <span class="icon">📂</span> 作品管理
        </div>
      </div>

      <div class="menu-group">
        <div class="group-title">选题管理</div>
        
        <div 
          class="menu-item"
          :class="{ 'active-item': currentTab === 'today_hot' }"
          @click="$emit('change', 'today_hot')"
        >
          <span class="icon">🔥</span> 今日热点
        </div>
        
        <div 
          class="menu-item"
          :class="{ 'active-item': currentTab === 'prediction' }"
          @click="$emit('change', 'prediction')"
        >
          <span class="icon">🔮</span> 热点预测
        </div>

        <div 
          class="menu-item highlight"
          :class="{ 'active-item': currentTab === 'monitor' }"
          @click="$emit('change', 'monitor')"
        >
          <span class="icon">📡</span> 舆情监控
        </div>



        <div 
          class="menu-item"
          :class="{ 'active-item': currentTab === 'customer' }"
          @click="$emit('change', 'customer')"
        >
          <span class="icon">👥</span> 客户管理
        </div>

      </div>
    </nav>
  </div>
</template>

<script setup>
defineProps({ currentTab: String })
defineEmits(['change'])
</script>

<style scoped>
/* 样式保持不变 */
.nav-container { height: 100%; display: flex; flex-direction: column; background: #0f172a; color: #fff; border-right: 1px solid #1e293b; }
.brand-area { padding: 24px 24px; display: flex; flex-direction: column; align-items: flex-start; gap: 12px; border-bottom: 1px solid #1e293b; background: #0b1120; }
.logo-img { height: 32px; }
.brand-text { display: flex; align-items: center; }
.brand-text h2 { margin: 0; font-size: 16px; font-weight: 700; color: white; letter-spacing: 0.5px; }
.version { font-size: 10px; background: #dc2626; padding: 1px 5px; border-radius: 3px; color: white; margin-left: 6px; font-weight: bold; }
.menu-scroll-area { flex: 1; padding: 20px 16px; overflow-y: auto; }
.menu-group { margin-bottom: 24px; }
.group-title { font-size: 11px; color: #64748b; font-weight: bold; padding-left: 12px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
.menu-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; margin-bottom: 2px; border-radius: 6px; color: #94a3b8; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; }
.menu-item:hover { background: rgba(255,255,255,0.08); color: white; }
.menu-item.active-item { background: #2563eb; color: white; box-shadow: 0 4px 12px rgba(37,99,235,0.3); }
.menu-item.highlight { color: #cbd5e1; }
</style>