<template>
  <div class="auth-wrapper">
    <div class="auth-card">
      <div class="logo-area">
        <h1>SmartEdit Core</h1>
        <p>创建您的账号</p>
      </div>

      <div class="form-body">
        <h2 class="form-title">注册账号</h2>
        <div class="input-group">
          <label>用户名</label>
          <input v-model="username" placeholder="设置用户名" />
        </div>
        <div class="input-group">
          <label>邮箱</label>
          <input v-model="email" placeholder="example@mail.com" />
        </div>
        <div class="input-group">
          <label>密码</label>
          <input type="password" v-model="password" placeholder="设置密码" />
        </div>
        
        <button class="auth-btn" @click="handleRegister" :disabled="loading">
            {{ loading ? '注册中...' : '立即注册' }}
        </button>

        <div class="footer-links">
           <span>已有账号？</span>
           <span class="link" @click="$emit('switch', 'login')">返回登录</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { register } from '../services/api'

const emit = defineEmits(['switch'])

const username = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)

const handleRegister = async () => {
    if(!username.value || !password.value) return alert("请填写完整信息")
    loading.value = true
    try {
        await register(username.value, email.value, password.value)
        alert("注册成功，请登录")
        emit('switch', 'login')
    } catch (e) {
        alert("注册失败：" + (e.response?.data?.detail || e.message))
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
.auth-wrapper {
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #0f172a;
    font-family: 'Inter', sans-serif;
}
.auth-card {
    background: white;
    width: 400px;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 20px 50px rgba(0,0,0,0.3);
    display: flex;
    flex-direction: column;
}
.logo-area {
    background: #1e293b;
    padding: 30px;
    text-align: center;
    color: white;
}
.logo-area h1 { margin: 0; font-size: 24px; font-weight: 800; }
.logo-area p { margin: 5px 0 0 0; font-size: 13px; color: #94a3b8; }

.form-body { padding: 40px 30px; display: flex; flex-direction: column; gap: 20px; }
.form-title { margin: 0 0 10px 0; font-size: 20px; color: #334155; text-align: center; }

.input-group label { display: block; font-size: 13px; font-weight: 600; color: #64748b; margin-bottom: 6px; }
.input-group input { width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 15px; outline: none; transition: all 0.2s; box-sizing: border-box; }
.input-group input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }

.auth-btn { background: #2563eb; color: white; border: none; padding: 14px; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
.auth-btn:hover { background: #1d4ed8; }
.auth-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.footer-links { text-align: center; font-size: 13px; color: #64748b; }
.link { color: #2563eb; font-weight: 600; cursor: pointer; margin-left: 5px; }
.link:hover { text-decoration: underline; }
</style>
