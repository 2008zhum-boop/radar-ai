import axios from 'axios'

// 自动判断环境：
// 如果是在本地开发 (npm run dev)，就连 localhost
// 如果是发布上线 (npm run build)，就连 Render 的云端地址
export const API_URL = import.meta.env.PROD
  ? 'https://radar-backend-cvaq.onrender.com'  // 你的 Render 真实地址
  : 'http://localhost:8000'                      // 本地开发地址

// === 获取 axios 实例 ===
export const getApi = () => axios

// === Axios 拦截器 (自动附加 Token) ===
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// === Auth & Admin ===
export const login = async (username, password) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  const response = await axios.post(`${API_URL}/auth/login`, formData)
  return response.data
}

export const register = async (username, email, password) => {
  const response = await axios.post(`${API_URL}/auth/register`, { username, email, password })
  return response.data
}

export const getProfile = async () => {
  try {
    const response = await axios.get(`${API_URL}/auth/me`)
    return response.data
  } catch {
    return null
  }
}

export const getUsers = async () => {
  const response = await axios.get(`${API_URL}/admin/users`)
  return response.data
}

export const updateUserRole = async (username, role, status) => {
  const response = await axios.post(`${API_URL}/admin/user/role`, { username, role, status })
  return response.data
}

export const deleteUser = async (username) => {
  const response = await axios.post(`${API_URL}/admin/user/delete`, { username, role: 'dummy', status: 0 })
  return response.data
}

// === Core Logic ===

// 1. 获取热搜列表 (GET)
export const getHotList = async (category) => {
  const response = await axios.get(`${API_URL}/hotlist`, {
    params: { category }
  })
  return response.data
}

// 2. 获取所有关键词 (GET)
export const getKeywords = async () => {
  const response = await axios.get(`${API_URL}/keywords`)
  return response.data
}

// 3. 添加关键词 (POST)
export const addKeyword = async (word) => {
  const response = await axios.post(`${API_URL}/keywords/add`, { word })
  return response.data
}

// 4. 删除关键词 (POST)
export const removeKeyword = async (word) => {
  const response = await axios.post(`${API_URL}/keywords/remove`, { word })
  return response.data
}

// 5. AI 话题分析 (POST)
export const analyzeTopic = async (topic) => {
  const response = await axios.post(`${API_URL}/analyze`, { topic })
  return response.data
}

// 6. 获取热点预测 (POST)
export const getPredictions = async (keywordList = []) => {
  const response = await axios.post(`${API_URL}/predictions`, {
    keywords: keywordList
  })
  return response.data
}

// 7. 生成智能大纲 (POST)
export const generateOutline = async (title, angle, context) => {
  const response = await axios.post(`${API_URL}/generate_outline`, {
    title,
    angle,
    context
  })
  return response.data
}

// 8. 生成全文 (POST)
export const generateArticle = async (title, outline, context) => {
  const response = await axios.post(`${API_URL}/generate_article`, {
    title,
    outline,
    context
  })
  return response.data
}

// 9. 获取所有客户配置
export const getClients = async () => {
  const response = await axios.get(`${API_URL}/monitor/clients`)
  return response.data
}

// 10. 保存客户
export const saveClientConfig = async (clientData) => {
  const response = await axios.post(`${API_URL}/monitor/client/save`, clientData)
  return response.data
}

// 11. 删除客户
export const deleteClient = async (clientId) => {
  const response = await axios.post(`${API_URL}/monitor/client/delete`, { client_id: clientId })
  return response.data
}

// 12. 生成日报 (POST)
export const generateReport = async (clientId) => {
  const response = await axios.post(`${API_URL}/monitor/report/generate`, { client_id: clientId })
  return response.data
}

// === 全网内容库管理 ===

// 13. 搜索内容库
export const searchContentLibrary = async (params) => {
  const response = await axios.post(`${API_URL}/content/library/search`, params)
  return response.data;
}

// 13b. 获取单条内容详情（编辑时拉取正文、摘要等）
export const getContentDetail = async (mentionId) => {
  const response = await axios.get(`${API_URL}/content/library/${mentionId}`)
  return response.data;
}

// 13c. 内容详情编辑保存（全量更新）
export const updateContent = async (payload) => {
  const response = await axios.post(`${API_URL}/content/library/update`, payload)
  return response.data;
}

// 14. 批量废弃
export const bulkDiscard = async (mentionIds) => {
  const response = await axios.post(`${API_URL}/content/library/bulk-discard`, { mention_ids: mentionIds })
  return response.data;
}

// 15. 添加到黑名单
export const addToBlacklist = async (sourceName, reason) => {
  const response = await axios.post(`${API_URL}/content/blacklist/add`, { source_name: sourceName, reason })
  return response.data;
}

// 16. 获取黑名单
export const getBlacklist = async () => {
  const response = await axios.get(`${API_URL}/content/blacklist`)
  return response.data;
}

// 17. 移除黑名单
export const removeFromBlacklist = async (sourceName) => {
  const response = await axios.post(`${API_URL}/content/blacklist/remove`, { source_name: sourceName })
  return response.data;
}

// 18. 关联内容
export const associateContent = async (mentionId, clientId) => {
  const response = await axios.post(`${API_URL}/content/associate`, { mention_id: mentionId, client_id: clientId })
  return response.data;
}

// 19. 纠正内容
export const correctContent = async (mentionId, newCategory, newSentiment) => {
  const response = await axios.post(`${API_URL}/content/correct`, {
    mention_id: mentionId,
    new_category: newCategory,
    new_sentiment: newSentiment
  })
  return response.data;
}

// 20. 获取质检统计
export const getQualityStats = async () => {
  const response = await axios.get(`${API_URL}/content/quality-stats`)
  return response.data;
}

// 21. 获取全球趋势 (HotPrediction.vue dependency)
export const getGlobalTrends = async (force_refresh = false) => {
  // Correctly mapping to the new Global Prediction Endpoint
  const response = await axios.get(`${API_URL}/prediction/trends`, {
    params: { force_refresh }
  })
  return response.data
}


// 22. 上传润色文件 (MonitorDashboard.vue dependency)
export const uploadPolishFile = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await axios.post(`${API_URL}/polish/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

// 23. 解析话题 (MonitorDashboard.vue dependency)
export const parseTopic = async (text) => {
  const response = await axios.post(`${API_URL}/topic/parse`, { text })
  return response.data
}

// 24. Selection Management (Mock or Implement)
export const getSelections = async () => {
  // Placeholder implementation
  return []
}

export const updateSelectionStatus = async (id, status) => {
  return { status: 'success', id, status }
}

export const deleteSelection = async (id) => {
  return { status: 'success', id }
}

// 25. Article Management
export const getArticles = async () => {
  return []
}

export const deleteArticle = async (id) => {
  return { status: 'success' }
}

// 26. Agent Management
export const getAgents = async () => {
  return []
}

export const createAgent = async (data) => {
  return { status: 'success', data }
}

export const updateAgent = async (id, data) => {
  return { status: 'success', id }
}

export const deleteAgent = async (id) => {
  return { status: 'success' }
}

export const runAgent = async (id, input) => {
  return { status: 'success', result: 'Agent run mocked' }
}

// 27. Tag Management
export const getTags = async () => {
  return []
}

export const createTag = async (data) => {
  return { status: 'success', data }
}

export const updateTag = async (id, data) => {
  return { status: 'success' }
}

export const mergeTags = async (ids, newName) => {
  return { status: 'success' }
}

export const deleteTag = async (id) => {
  return { status: 'success' }
}

// 28. Flash News Management (Updated)
export const getFlashList = async (status = 'all', source = 'all') => {
  const response = await axios.get(`${API_URL}/flash/list`, { params: { status, source } })
  return response.data
}

export const updateFlash = async (id, status, content = null, title = null) => {
  const payload = { id, status }
  if (content !== null) payload.content = content
  if (title !== null) payload.title = title
  const response = await axios.post(`${API_URL}/flash/update`, payload)
  return response.data
}

export const triggerFlashFetch = async (source = 'cls') => {
  const response = await axios.get(`${API_URL}/flash/fetch`, { params: { source } })
  return response.data
}

export const backfillFlashRewrite = async (limit = 10) => {
  const response = await axios.post(`${API_URL}/flash/backfill`, { limit })
  return response.data
}
