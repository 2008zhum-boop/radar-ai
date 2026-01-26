import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000'

// 1. 获取热搜列表和报警
// 1. 获取热搜列表 (支持分类)
export const getHotList = async (category = '综合') => {
  // 拼接到 URL 参数里
  const response = await axios.get(`${API_URL}/hotlist`, {
    params: { category }
  })
  return response.data
}

// 2. 添加监控词
export const addKeyword = async (keyword) => {
  const response = await axios.post(`${API_URL}/keywords`, { keyword })
  return response.data
}

// 3. 删除监控词
export const removeKeyword = async (keyword) => {
  // Axios delete 传参比较特殊，需要用 data 字段
  const response = await axios.delete(`${API_URL}/keywords`, { data: { keyword } })
  return response.data
}

// 4. 请求 AI 分析话题
export const analyzeTopic = async (title) => {
  const response = await axios.post(`${API_URL}/analyze`, { title })
  return response.data
}

// 5. 请求 AI 生成大纲 (新增)
export const createOutline = async (title, angle) => {
  const response = await axios.post(`${API_URL}/outline`, { title, angle })
  return response.data
}

// ... (其他接口)

// 6. 获取热点预测 (改为 POST，传入关键词列表)
export const getPredictions = async (keywordList = []) => {
  // 发送 POST 请求，body 为 { keywords: [...] }
  const response = await axios.post(`${API_URL}/predictions`, {
    keywords: keywordList
  })
  return response.data
}

// 7. 生成智能大纲
export const generateOutline = async (title, angle, context) => {
  const response = await axios.post(`${API_URL}/generate_outline`, {
    title,
    angle,
    context
  })
  return response.data
}

// 8. 生成全文 (一键写作)
export const generateArticle = async (title, outline, context) => {
  const response = await axios.post(`${API_URL}/generate_article`, {
    title,
    outline,
    context
  })
  return response.data
}