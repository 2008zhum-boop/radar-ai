<template>
  <div class="user-manager">
    <div class="um-header">
      <h2>👥 用户权限管理 (Admin)</h2>
      <div class="header-actions">
        <button class="add-btn" @click="showAddModal = true">➕ 新增用户</button>
        <button class="refresh-btn" @click="loadUsers">🔄 刷新列表</button>
      </div>
    </div>

    <!-- Add User Modal -->
    <div v-if="showAddModal" class="modal-overlay">
        <div class="modal-card">
            <h3>添加新用户</h3>
            <div class="form-group">
                <label>用户名 <span style="color:red">*</span></label>
                <input v-model="newUser.username" placeholder="输入用户名" />
            </div>
            <div class="form-group">
                <label>邮箱</label>
                <input v-model="newUser.email" placeholder="输入邮箱 (选填)" />
            </div>
            <div class="form-group">
                <label>密码 <span style="color:red">*</span></label>
                <input v-model="newUser.password" type="password" placeholder="设置密码" />
            </div>
             <div class="form-group">
                <label>角色</label>
                <select v-model="newUser.role">
                    <option value="viewer">Viewer</option>
                    <option value="editor">Editor</option>
                    <option value="admin">Admin</option>
                </select>
            </div>
            <div class="modal-actions">
                <button class="cancel-btn" @click="showAddModal = false">取消</button>
                <button class="save-btn" @click="handleAddUser">创建</button>
            </div>
        </div>
    </div>

    <div class="um-table-card">
      <table class="um-table">
        <thead>
          <tr>
            <th>用户名</th>
            <th>邮箱</th>
            <th>角色</th>
            <th>状态</th>
            <th>注册时间</th>
            <th class="text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.username">
            <td class="font-bold">{{ u.username }}</td>
            <td>{{ u.email || '-' }}</td>
            <td>
              <span class="role-badge" :class="u.role">{{ u.role }}</span>
            </td>
            <td>
              <span class="status-dot" :class="u.status===1?'active':'inactive'"></span>
              {{ u.status===1?'正常':'禁用' }}
            </td>
            <td>{{ u.created_at }}</td>
            <td class="text-right">
                <div class="actions" v-if="u.username !== 'admin'">
                    <select @change="changeRole(u, $event)" :value="u.role" class="role-select">
                        <option value="viewer">Viewer</option>
                        <option value="editor">Editor</option>
                        <option value="admin">Admin</option>
                    </select>
                    <button class="btn-toggle" @click="toggleStatus(u)">
                        {{ u.status===1 ? '禁用' : '启用' }}
                    </button>
                    <button class="btn-del" @click="removeUser(u)">🗑️</button>
                </div>
                <div v-else class="locked">
                   🔒 超级管理员
                </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { getUsers, updateUserRole, deleteUser, register } from '../services/api'

const users = ref([])
const showAddModal = ref(false)
const newUser = reactive({ username: '', email: '', password: '', role: 'viewer' })

const handleAddUser = async () => {
    if(!newUser.username || !newUser.password) return alert("请填写用户名和密码")
    try {
        // 1. Create User
        // register takes (username, email, password)
        await register(newUser.username, newUser.email || '', newUser.password)
        
        // 2. Set Role if not viewer
        if (newUser.role !== 'viewer') {
            await updateUserRole(newUser.username, newUser.role, 1)
        }
        
        alert("用户创建成功")
        showAddModal.value = false
        newUser.username = ''
        newUser.email = ''
        newUser.password = ''
        newUser.role = 'viewer'
        loadUsers()
    } catch (e) {
        console.error(e)
        const msg = e.response?.data?.detail || e.message || "未知错误"
        alert("创建失败: " + msg)
    }
}

const loadUsers = async () => {
    try {
        const res = await getUsers()
        users.value = res
    } catch (e) {
        alert("获取用户列表失败：" + e.message)
    }
}

const changeRole = async (user, event) => {
    const newRole = event.target.value
    if(confirm(`确定将 ${user.username} 的角色更改为 ${newRole}?`)) {
        await updateUserRole(user.username, newRole, user.status)
        await loadUsers()
    } else {
        event.target.value = user.role // revert
    }
}

const toggleStatus = async (user) => {
    const newStatus = user.status === 1 ? 0 : 1
    await updateUserRole(user.username, user.role, newStatus)
    await loadUsers()
}

const removeUser = async (user) => {
    if(confirm(`❌ 警告：确定删除用户 ${user.username}? 此操作不可恢复！`)) {
        try {
            await deleteUser(user.username)
            await loadUsers()
        } catch {
            alert("删除失败")
        }
    }
}

onMounted(loadUsers)
</script>

<style scoped>
.user-manager { padding: 30px; background: #f8fafc; min-height: 100vh; }
.um-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.refresh-btn { background: white; border: 1px solid #cbd5e1; padding: 8px 16px; border-radius: 6px; cursor: pointer; }

.um-table-card { background: white; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
.um-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }
.um-table th { background: #f8fafc; padding: 16px 24px; font-weight: 600; color: #64748b; border-bottom: 1px solid #e2e8f0; }
.um-table td { padding: 16px 24px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.um-table tr:hover { background: #fcfcfc; }

.font-bold { font-weight: 600; color: #0f172a; }
.role-badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: capitalize; }
.role-badge.admin { background: #fee2e2; color: #dc2626; }
.role-badge.editor { background: #ffedd5; color: #ea580c; }
.role-badge.viewer { background: #e0f2fe; color: #0284c7; }

.status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
.status-dot.active { background: #16a34a; }
.status-dot.inactive { background: #cbd5e1; }

.text-right { text-align: right; }
.actions { display: flex; justify-content: flex-end; gap: 8px; align-items: center; }

.role-select { padding: 6px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 13px; }
.btn-toggle { padding: 6px 12px; border-radius: 6px; border: 1px solid #cbd5e1; background: white; cursor: pointer; font-size: 12px; }
.btn-toggle:hover { background: #f1f5f9; }
.btn-del { border: none; background: #fef2f2; color: #ef4444; width: 30px; height: 30px; border-radius: 6px; cursor: pointer; }
.locked { color: #94a3b8; font-size: 12px; font-style: italic; }

/* Header & Modal Styles */
.header-actions { display: flex; gap: 12px; }
.add-btn { background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 500; font-size: 13px; }
.add-btn:hover { background: #2563eb; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-card { background: white; width: 400px; padding: 24px; border-radius: 12px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }
.modal-card h3 { margin: 0 0 20px 0; font-size: 18px; color: #1e293b; }

.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; font-weight: 500; color: #64748b; margin-bottom: 6px; }
.form-group input, .form-group select { width: 100%; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; box-sizing: border-box; }
.form-group input:focus, .form-group select:focus { border-color: #3b82f6; outline: none; }

.modal-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
.cancel-btn { background: white; border: 1px solid #cbd5e1; padding: 8px 16px; border-radius: 6px; cursor: pointer; color: #475569; }
.save-btn { background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; }

</style>
