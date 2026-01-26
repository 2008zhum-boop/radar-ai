import axios from 'axios'

// 自动判断环境：
// 如果是在本地开发 (npm run dev)，就连 localhost
// 如果是发布上线 (npm run build)，就连 Render 的云端地址
const API_URL = import.meta.env.PROD 
  ? 'https://radar-backend-cvaq.onrender.com'  // 你的 Render 真实地址
  : 'http://localhost:8000'                      // 本地开发地址

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