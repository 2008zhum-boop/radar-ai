<template>
  <div class="video-manager">
    <div class="header">
      <h2>🎬 视频管理</h2>
      <button class="btn-primary" @click="createVideo">新建视频任务</button>
    </div>
    <div class="content">
      <div class="empty-state">
        <p>暂无视频生成任务</p>
        <p class="sub-text">AI 视频生成功能即将上线</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const createVideo = () => {
    alert("AI视频生成功能开发中...")
}
</script>

<style scoped>
.video-manager {
    padding: 24px;
    background: #f8fafc;
    height: 100%;
}
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
}
.header h2 {
    font-size: 20px;
    color: #1e293b;
    margin: 0;
}
.btn-primary {
    padding: 8px 16px;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
}
.content {
    background: white;
    border-radius: 12px;
    padding: 40px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    min-height: 400px;
    display: flex;
    justify-content: center;
    align-items: center;
}
.empty-state {
    text-align: center;
    color: #94a3b8;
}
.sub-text {
    font-size: 13px;
    margin-top: 8px;
}
</style>
