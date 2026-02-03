<template>
  <div class="global-content-library">
    <!-- 顶部：标题和质检统计 -->
    <div class="library-header">
      <div class="header-top">
        <h1>全网内容库</h1>
        <button @click="syncContentLibrary" class="sync-btn" :disabled="syncing">
          {{ syncing ? '同步中...' : '🔄 同步最新内容' }}
        </button>
      </div>
      <div class="quality-stats" v-if="qualityStats">
        <div class="stat-card">
          <span class="stat-label">今日采集</span>
          <span class="stat-value">{{ qualityStats.total_count }}</span>
        </div>
        <div class="stat-card warning" v-if="qualityStats.garbage_rate > 10">
          <span class="stat-label">垃圾率</span>
          <span class="stat-value">{{ qualityStats.garbage_rate }}%</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">正面</span>
          <span class="stat-value">{{ qualityStats.sentiment_distribution.positive.percentage }}%</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">负面</span>
          <span class="stat-value">{{ qualityStats.sentiment_distribution.negative.percentage }}%</span>
        </div>
      </div>
    </div>

    <!-- 超级检索栏 (Super Search) -->
    <div class="search-section">
      <div class="search-bar">
        <input 
          v-model="filters.search_text"
          type="text" 
          placeholder="搜索标题、内容..." 
          class="search-input"
        >
        <button @click="searchContent" class="search-btn">🔍 检索</button>
      </div>

      <!-- 高级筛选器 -->
      <div class="advanced-filters">
        <div class="filter-group">
          <label>时间范围</label>
          <select v-model="filters.time_range" @change="searchContent">
            <option value="1h">近1小时</option>
            <option value="24h">近24小时</option>
            <option value="7d">近7天</option>
            <option value="all">全部</option>
          </select>
        </div>

        <div class="filter-group">
          <label>来源平台</label>
          <select v-model="filters.source_select" @change="searchContent" class="filter-select">
             <option value="">全部</option>
             <option value="微博">微博</option>
             <option value="微信">微信</option>
             <option value="B站">B站</option>
             <option value="头条">头条</option>
             <option value="百度">百度</option>
          </select>
        </div>

        <div class="filter-group">
          <label>情感属性</label>
          <div class="checkbox-group">
            <label><input type="checkbox" value="positive" v-model="filters.sentiment_filter" @change="searchContent"> 正面</label>
            <label><input type="checkbox" value="negative" v-model="filters.sentiment_filter" @change="searchContent"> 负面</label>
            <label><input type="checkbox" value="neutral" v-model="filters.sentiment_filter" @change="searchContent"> 中性</label>
          </div>
        </div>

        <div class="filter-group">
          <label>处理状态</label>
          <div class="checkbox-group">
            <label><input type="checkbox" value="uncleaned" v-model="filters.clean_status_filter" @change="searchContent"> 未清洗</label>
            <label><input type="checkbox" value="cleaned" v-model="filters.clean_status_filter" @change="searchContent"> 已入库</label>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div class="batch-actions" v-if="selectedItems.length > 0">
      <div class="action-info">
        已选择 <strong>{{ selectedItems.length }}</strong> 条内容
      </div>
      <div class="action-buttons">
        <button @click="batchDiscard" class="btn btn-danger">❌ 删除</button>
        <button @click="showBlacklistModal = true" class="btn btn-warning">🚫 屏蔽信源</button>
        <button @click="batchExport" class="btn btn-info">📥 导出</button>
      </div>
    </div>

    <!-- 内容清洗流水线 -->
    <div class="content-pipeline">
      <table class="content-table">
        <thead>
          <tr>
            <th width="40">
              <input type="checkbox" v-model="selectAll" @change="toggleSelectAll">
            </th>
            <th width="200">标题</th>
            <th width="80">来源</th>
            <th width="120">分类 (标签)</th>
            <th width="120">入库时间</th>
            <th width="80">热度</th>
            <th width="100">AI 判定</th>
            <th width="120">关联客户</th>
            <th width="120">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in contentList" :key="item.id" :class="item.clean_status">
            <td>
              <input type="checkbox" :value="item.id" v-model="selectedItems">
            </td>
            <td class="title-cell">
              <div class="title-content">
                <span class="title-text" @click="showPreview(item)">{{ item.title }}</span>
                <span v-if="item.clean_status === 'cleaned'" class="badge badge-success">已入库</span>
              </div>
            </td>
            <td><span class="source-tag">{{ item.source }}</span></td>
            <td>
                <div class="cat-tag-cell">
                    <span class="cat-badge" v-if="item.category">{{ item.category }}</span>
                    <span class="tag-text" v-if="item.tags">{{ Array.isArray(item.tags) ? item.tags.slice(0,2).join(',') : item.tags }}</span>
                </div>
            </td>
            <td class="time-cell">{{ item.time_display }}</td>
            <td class="hotness-cell"><span class="hotness">{{ item.hotness_display || item.hotness }}</span></td>
            <td>
              <div class="ai-judgment">
                <span :class="'sentiment-' + item.sentiment_label">{{ item.sentiment_label }}</span>
              </div>
            </td>
            <td>
               <div v-if="item.matched_clients && item.matched_clients.length" class="client-info">
                   {{ item.matched_clients.join(', ') }}
               </div>
               <div v-else class="unassociated">-</div>
            </td>
            <td class="actions-cell">
              <div class="action-buttons">
                <button @click="showEditModal(item)" class="btn-small btn-default" title="编辑">✏️ 编辑</button>
                <button @click="discardSingle(item.id)" class="btn-small btn-danger" title="删除">🗑️</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div class="pagination" v-if="pagination.total_pages > 1">
        <button @click="filters.page--; searchContent()" :disabled="filters.page <= 1">← 上一页</button>
        <span>第 {{ filters.page }} / {{ pagination.total_pages }} 页 (共 {{ pagination.total }} 条)</span>
        <button @click="filters.page++; searchContent()" :disabled="filters.page >= pagination.total_pages">下一页 →</button>
      </div>
    </div>

    <!-- 二级编辑页 -->
    <div v-if="editItem" class="modal-overlay full-screen-modal" @click="editItem = null">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h3>📝 内容详情编辑</h3>
          <div class="header-actions">
              <span class="status-label">状态: {{ editItem.clean_status === 'cleaned' ? '已入库' : '未清洗' }}</span>
              <button class="close-btn" @click="editItem = null">✕</button>
          </div>
        </div>
        <div class="modal-body edit-mode">
          
          <div class="edit-row">
             <div class="form-group flex-2">
               <label>标题</label>
               <input v-model="editData.title" type="text" class="full-width">
             </div>
             <div class="form-group flex-1">
               <label>来源</label>
               <input v-model="editData.source" type="text" disabled class="full-width disabled-input">
             </div>
          </div>

          <div class="edit-row">
             <div class="form-group">
                <label>分类</label>
                <input v-model="editData.category" type="text" placeholder="例: 科技">
             </div>
             <div class="form-group">
                <label>标签 (逗号分隔)</label>
                <input v-model="editData.tags" type="text" placeholder="例: AI,大模型">
             </div>
             <div class="form-group">
                <label>情感判断</label>
                <select v-model="editData.sentiment">
                    <option value="positive">正面</option>
                    <option value="neutral">中性</option>
                    <option value="negative">负面</option>
                </select>
             </div>
          </div>

          <div class="form-group">
              <label>关联客户 (监控词)</label>
              <input v-model="editData.matched_clients" type="text" placeholder="例: 客户A, 客户B">
          </div>

          <div class="form-group">
             <label>摘要 (Fact)</label>
             <textarea v-model="editData.summary" rows="3" class="full-width"></textarea>
          </div>

          <div class="form-group flex-grow">
             <label>正文内容 (Full Text)</label>
             <textarea v-model="editData.content_text" rows="10" class="full-width"></textarea>
          </div>
          
        </div>
        <div class="modal-footer">
          <button @click="discardSingle(editItem.id); editItem = null" class="btn btn-danger float-left">🗑️ 删除此条</button>
          <button @click="editItem = null" class="btn btn-secondary">取消</button>
          <button @click="saveEdit" class="btn btn-primary">💾 保存修改</button>
        </div>
      </div>
    </div>

    <!-- 黑名单模态框 -->
    <div v-if="showBlacklistModal" class="modal-overlay" @click="showBlacklistModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>屏蔽信源</h3>
          <button class="close-btn" @click="showBlacklistModal = false">✕</button>
        </div>
        <div class="modal-body">
          <p>确定要屏蔽以下信源吗？</p>
          <div class="blacklist-sources">
            <div v-for="itemId in selectedItems" :key="itemId" class="source-item">
              {{ contentList.find(c => c.id === itemId)?.source }}
            </div>
          </div>
          <input 
            v-model="blacklistReason" 
            type="text" 
            placeholder="屏蔽原因（可选）"
            class="full-width"
          >
        </div>
        <div class="modal-footer">
          <button @click="showBlacklistModal = false" class="btn btn-secondary">取消</button>
          <button @click="confirmBlacklist" class="btn btn-danger">确认屏蔽</button>
        </div>
      </div>
    </div>

    <!-- 黑名单管理 -->
    <div class="blacklist-section">
      <h3>📋 信源黑名单</h3>
      <table v-if="blacklist.length > 0" class="blacklist-table">
        <thead>
          <tr>
            <th>信源</th>
            <th>原因</th>
            <th>添加时间</th>
            <th>添加者</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in blacklist" :key="item.id">
            <td>{{ item.source_name }}</td>
            <td>{{ item.reason || '- -' }}</td>
            <td>{{ item.created_time }}</td>
            <td>{{ item.created_by }}</td>
            <td>
              <button @click="removeFromBlacklist(item.source_name)" class="btn-small btn-success">
                ✓ 解除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">暂无黑名单信源</div>
    </div>
  </div>
</template>

<script>
import { 
  getHotList, 
  getClients, 
  searchContentLibrary, 
  getContentDetail,
  updateContent,
  bulkDiscard, 
  addToBlacklist, 
  getBlacklist, 
  removeFromBlacklist, 
  associateContent, 
  getQualityStats 
} from '../services/api.js';

export default {
  name: 'GlobalContentLibrary',
  data() {
    return {
      // 筛选器状态
      filters: {
        search_text: '',
        source_select: '', // Changed from source_filter array to select string
        source_filter: [], // Keep for backward compatibility if needed, else ignore
        sentiment_filter: [],
        clean_status_filter: [],
        time_range: '24h',
        page: 1,
        page_size: 20
      },
      
      // 内容列表
      contentList: [],
      pagination: {
        total: 0,
        page: 1,
        page_size: 20,
        total_pages: 1
      },

      // 选择状态
      selectedItems: [],
      selectAll: false,

      // 模态框状态
      previewItem: null,
      
      // Edit State
      editItem: null,
      editData: {
          title: '',
          source: '',
          category: '',
          tags: '',
          sentiment: '',
          matched_clients: '',
          summary: '',
          content_text: ''
      },

      showBlacklistModal: false,
      blacklistReason: '',

      // 客户列表
      clients: [],

      // 黑名单
      blacklist: [],

      // 质检统计
      qualityStats: null,

      // 加载状态
      loading: false,
      syncing: false
    };
  },

  mounted() {
    this.searchContent();
    this.fetchClients();
    this.fetchBlacklist();
    this.fetchQualityStats();

    // 定期刷新质检统计
    setInterval(() => {
      this.fetchQualityStats();
    }, 60000); // 每分钟刷新一次
  },

  methods: {
    // 同步最新内容
    async syncContentLibrary() {
      this.syncing = true;
      try {
        await getHotList('综合');
        await new Promise(resolve => setTimeout(resolve, 1000));
        this.filters.page = 1;
        await this.searchContent();
        alert('内容库已同步，共获取最新数据！');
      } catch (error) {
        console.error('同步失败', error);
        alert('同步失败，请重试');
      } finally {
        this.syncing = false;
      }
    },

    // 搜索内容
    searchContent() {
      this.loading = true;
      
      // Handle source filter: select takes precedence
      let sources = null;
      if (this.filters.source_select) {
          sources = [this.filters.source_select];
      } else if (this.filters.source_filter.length > 0) {
          sources = this.filters.source_filter;
      }

      const requestBody = {
        search_text: this.filters.search_text,
        source_filter: sources,
        sentiment_filter: this.filters.sentiment_filter.length > 0 ? this.filters.sentiment_filter : null,
        clean_status_filter: this.filters.clean_status_filter.length > 0 ? this.filters.clean_status_filter : null,
        time_range: this.filters.time_range,
        page: this.filters.page,
        page_size: this.filters.page_size
      };

      searchContentLibrary(requestBody)
        .then(data => {
          this.contentList = data.items || [];
          this.pagination = {
            total: data.total,
            page: data.page,
            page_size: data.page_size,
            total_pages: data.total_pages
          };
          this.selectedItems = [];
          this.selectAll = false;
        })
        .catch(error => {
          console.error('搜索失败', error);
        })
        .finally(() => {
          this.loading = false;
        });
    },

    // 获取客户列表
    fetchClients() {
      getClients()
        .then(data => {
          this.clients = data || [];
        })
        .catch(error => {
          console.error('获取客户列表失败', error);
        });
    },

    // 获取黑名单
    fetchBlacklist() {
      getBlacklist()
        .then(data => {
          this.blacklist = data.blacklist || [];
        })
        .catch(error => {
          console.error('获取黑名单失败', error);
        });
    },

    // 获取质检统计
    fetchQualityStats() {
      getQualityStats()
        .then(data => {
          this.qualityStats = data;
        })
        .catch(error => {
          console.error('获取质检统计失败', error);
        });
    },

    // 全选/取消全选
    toggleSelectAll() {
      if (this.selectAll) {
        this.selectedItems = this.contentList.map(item => item.id);
      } else {
        this.selectedItems = [];
      }
    },

    // 预览内容
    showPreview(item) {
      this.previewItem = item;
    },

    // 显示编辑模态框（拉取详情以获取正文、摘要等）
    async showEditModal(item) {
      this.editItem = item;
      this.editData = {
          title: item.title,
          source: item.source,
          category: item.category || item.manual_category || '',
          tags: Array.isArray(item.tags) ? item.tags.join(',') : (item.tags || ''),
          sentiment: item.manual_sentiment || (item.sentiment_label === '正面' ? 'positive' : item.sentiment_label === '负面' ? 'negative' : 'neutral'),
          matched_clients: Array.isArray(item.matched_clients) ? item.matched_clients.join(',') : '',
          summary: '',
          content_text: item.content_text || ''
      };
      try {
        const detail = await getContentDetail(item.id);
        if (detail) {
          this.editData.title = detail.title ?? this.editData.title;
          this.editData.summary = detail.ai_fact ?? '';
          this.editData.content_text = detail.content_text ?? '';
          this.editData.category = detail.manual_category ?? this.editData.category;
          this.editData.tags = detail.manual_tags ?? this.editData.tags;
          this.editData.sentiment = detail.manual_sentiment || (detail.sentiment_label === '正面' ? 'positive' : detail.sentiment_label === '负面' ? 'negative' : 'neutral');
        }
      } catch (e) {
        console.warn('拉取内容详情失败，使用列表数据', e);
      }
    },

    // 保存编辑（全量提交到后端并刷新列表）
    async saveEdit() {
       if (!this.editItem) return;
       try {
           const payload = {
               id: this.editItem.id,
               title: this.editData.title,
               category: this.editData.category || null,
               tags: typeof this.editData.tags === 'string' ? this.editData.tags.trim() : (Array.isArray(this.editData.tags) ? this.editData.tags.join(',') : ''),
               sentiment: this.editData.sentiment || null,
               summary: this.editData.summary || null,
               content_text: this.editData.content_text || null
           };
           await updateContent(payload);
           alert('保存成功');
           this.editItem = null;
           this.searchContent();
       } catch (e) {
           console.error(e);
           alert('保存失败：' + (e.response?.data?.detail || e.message));
       }
    },

    // 删除单条
    discardSingle(itemId) {
      if (confirm('确定删除此内容？')) {
        bulkDiscard([itemId])
          .then(response => {
            this.searchContent();
          })
          .catch(error => {
            console.error('删除失败', error);
            alert('删除失败');
          });
      }
    },

    // 批量删除
    batchDiscard() {
      if (this.selectedItems.length === 0) {
        alert('请先选择要删除的内容');
        return;
      }

      if (confirm(`确定删除 ${this.selectedItems.length} 条内容吗？`)) {
        bulkDiscard(this.selectedItems)
          .then(response => {
            alert(`已删除 ${response.discarded_count} 条内容`);
            this.searchContent();
          })
          .catch(error => {
            console.error('批量删除失败', error);
            alert('批量删除失败');
          });
      }
    },

    // 确认屏蔽
    confirmBlacklist() {
      const sourcesToBlacklist = [...new Set(
        this.selectedItems
          .map(itemId => this.contentList.find(c => c.id === itemId)?.source)
          .filter(s => s)
      )];

      if (sourcesToBlacklist.length === 0) {
        alert('未找到要屏蔽的信源');
        return;
      }

      const promises = sourcesToBlacklist.map(source =>
        addToBlacklist(source, this.blacklistReason)
      );

      Promise.all(promises)
        .then(() => {
          alert(`已屏蔽 ${sourcesToBlacklist.length} 个信源`);
          this.showBlacklistModal = false;
          this.blacklistReason = '';
          this.fetchBlacklist();
          this.searchContent();
        })
        .catch(error => {
          console.error('屏蔽失败', error);
          alert('屏蔽失败');
        });
    },

    // 从黑名单移除
    removeFromBlacklist(sourceName) {
      if (confirm('确定解除屏蔽吗？')) {
        removeFromBlacklist(sourceName)
          .then(response => {
            alert('已解除屏蔽');
            this.fetchBlacklist();
          })
          .catch(error => {
            console.error('解除屏蔽失败', error);
            alert('解除屏蔽失败');
          });
      }
    },

    // 批量导出
    batchExport() {
      const selectedContent = this.contentList.filter(c => this.selectedItems.includes(c.id));
      const csv = [
        ['标题', '来源', '发布时间', '情感', '热度', 'URL'].join(','),
        ...selectedContent.map(item =>
          [
            `"${item.title.replace(/"/g, '""')}"`,
            item.source,
            new Date(item.publish_time * 1000).toLocaleString(),
            item.sentiment_label,
            item.hotness,
            item.url
          ].join(',')
        )
      ].join('\n');

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `content_export_${new Date().getTime()}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }
};
</script>

<style scoped>
.global-content-library {
  padding: 20px;
  background: #f5f5f5;
  min-height: 100vh;
}

.library-header {
  margin-bottom: 30px;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.library-header h1 {
  margin: 0;
  font-size: 28px;
  color: #333;
}

.sync-btn {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.3s;
}

.sync-btn:hover:not(:disabled) {
  background: #45a049;
}

.sync-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
  opacity: 0.7;
}

.quality-stats {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.stat-card {
  background: white;
  padding: 12px 20px;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-card.warning {
  background: #fff3cd;
  border-left: 4px solid #ffc107;
}

.stat-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

/* 搜索栏 */
.search-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.search-btn {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.search-btn:hover {
  background: #0056b3;
}

/* 高级筛选器 */
.advanced-filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  font-weight: bold;
  font-size: 13px;
  color: #333;
}

.filter-group select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: normal;
  cursor: pointer;
}

.checkbox-group input[type="checkbox"] {
  cursor: pointer;
}

/* 批量操作栏 */
.batch-actions {
  background: #e3f2fd;
  padding: 15px 20px;
  border-radius: 6px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-left: 4px solid #2196f3;
}

.action-info {
  font-size: 14px;
  color: #1976d2;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: bold;
}

.btn-primary {
  background: #2196f3;
  color: white;
}

.btn-primary:hover {
  background: #1976d2;
}

.btn-secondary {
  background: #757575;
  color: white;
}

.btn-secondary:hover {
  background: #616161;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.btn-danger:hover {
  background: #d32f2f;
}

.btn-warning {
  background: #ff9800;
  color: white;
}

.btn-warning:hover {
  background: #f57c00;
}

.btn-info {
  background: #00bcd4;
  color: white;
}

.btn-info:hover {
  background: #0097a7;
}

.btn-success {
  background: #4caf50;
  color: white;
}

.btn-success:hover {
  background: #388e3c;
}

/* 内容表格 */
.content-pipeline {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.content-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.content-table thead {
  background: #f5f5f5;
  border-bottom: 2px solid #ddd;
}

.content-table th {
  padding: 12px 15px;
  text-align: left;
  font-weight: bold;
  color: #333;
}

.content-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #eee;
}

.content-table tbody tr:hover {
  background: #f9f9f9;
}

.content-table tbody tr.cleaned {
  background: #f0f8f0;
}

.content-table tbody tr.discarded {
  opacity: 0.6;
  text-decoration: line-through;
}

.title-cell {
  max-width: 300px;
}

.title-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.title-text {
  cursor: pointer;
  color: #2196f3;
  text-decoration: none;
}

.title-text:hover {
  text-decoration: underline;
}

.badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: bold;
  color: white;
}

.badge-success {
  background: #4caf50;
}

.badge-info {
  background: #2196f3;
}

.source-tag {
  display: inline-block;
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 12px;
  color: #666;
}

.time-cell {
  white-space: nowrap;
  color: #999;
}

.hotness-cell {
  text-align: center;
  font-weight: bold;
  color: #ff9800;
}

.hotness {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.ai-judgment {
  text-align: center;
  padding: 4px 8px;
  border-radius: 4px;
}

.sentiment-正面 {
  background: #c8e6c9;
  color: #2e7d32;
  padding: 4px 8px;
  border-radius: 3px;
  font-weight: bold;
}

.sentiment-负面 {
  background: #ffcdd2;
  color: #c62828;
  padding: 4px 8px;
  border-radius: 3px;
  font-weight: bold;
}

.sentiment-中性 {
  background: #e0e0e0;
  color: #616161;
  padding: 4px 8px;
  border-radius: 3px;
}

.client-info {
  color: #2196f3;
  font-weight: bold;
}

.unassociated {
  color: #999;
  font-size: 12px;
}

.actions-cell {
  text-align: center;
}

.action-buttons {
  display: flex;
  gap: 5px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-small {
  padding: 4px 8px;
  font-size: 12px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  background: none;
  border: 1px solid #ddd;
}

.btn-small:hover {
  background: #f5f5f5;
}

.btn-small.btn-primary {
  color: #2196f3;
  border-color: #2196f3;
}

.btn-small.btn-warning {
  color: #ff9800;
  border-color: #ff9800;
}

.btn-small.btn-danger {
  color: #f44336;
  border-color: #f44336;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  padding: 20px;
}

.pagination button {
  padding: 8px 15px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.pagination button:hover:not(:disabled) {
  background: #f5f5f5;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination span {
  color: #666;
  font-size: 13px;
}

/* 模态框 */
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
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

.full-width {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.preview-content {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  line-height: 1.6;
  max-height: 300px;
  overflow-y: auto;
}

.blacklist-sources {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
  max-height: 150px;
  overflow-y: auto;
}

.source-item {
  padding: 5px 0;
  color: #666;
}

/* 黑名单管理 */
.blacklist-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.blacklist-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #333;
}

.blacklist-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-bottom: 15px;
}

.blacklist-table thead {
  background: #f5f5f5;
  border-bottom: 2px solid #ddd;
}

.blacklist-table th {
  padding: 12px 15px;
  text-align: left;
  font-weight: bold;
  color: #333;
}

.blacklist-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #eee;
}

.blacklist-table tbody tr:hover {
  background: #f9f9f9;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 30px;
  font-size: 14px;
}

/* New Styles for Edit Modal and Filters */
.filter-select {
    padding: 10px 15px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; background: white; width: 100%;
}
.cat-badge { background: #e0f2fe; color: #0284c7; padding: 2px 6px; border-radius: 4px; font-size: 12px; margin-right: 4px; }
.tag-text { color: #64748b; font-size: 12px; }
.cat-tag-cell { display: flex; flex-direction: column; align-items: start; gap: 2px; }

/* Edit Modal */
.full-screen-modal { display: flex; align-items: center; justify-content: center; z-index: 1000; }
.large-modal { width: 900px; max-width: 95vw; max-height: 90vh; display: flex; flex-direction: column; }
.large-modal .modal-body { flex: 1; overflow-y: auto; padding: 24px; }
.edit-mode { display: flex; flex-direction: column; gap: 16px; }
.edit-row { display: flex; gap: 16px; }
.flex-1 { flex: 1; }
.flex-2 { flex: 2; }
.flex-grow { flex-grow: 1; display: flex; flex-direction: column; }
.full-width { width: 100%; padding: 8px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; box-sizing: border-box; }
.disabled-input { background: #f1f5f9; color: #64748b; }
.header-actions { display: flex; align-items: center; gap: 12px; }
.status-label { font-size: 12px; background: #dcfce7; color: #16a34a; padding: 2px 8px; border-radius: 12px; }
textarea.full-width { resize: vertical; min-height: 80px; font-family: inherit; }
.form-group label { display: block; margin-bottom: 6px; font-weight: 500; font-size: 13px; color: #334155; }
.float-left { margin-right: auto; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 16px 24px; background: #f8fafc; border-top: 1px solid #e2e8f0; }
</style>
