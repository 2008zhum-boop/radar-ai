# 全网内容库模块 - 完整文档

## 📋 模块概述

**全网内容库 (Global Content Library)** 是一个针对舆情监控系统的内容管理、清洗与检索中心。它解决了舆情爬虫采集过程中的三大核心问题：

1. **数据质检** - 识别和清除垃圾广告和低质内容
2. **非客户热点发现** - 发现行业大新闻，为编辑提供创作灵感
3. **人工纠偏** - 修正 AI 的分类和情感判定错误

---

## 🎯 核心功能

### 1. 超级检索栏 (Super Search)
支持全文搜索和多维度筛选：
- **全文检索**：在标题和内容中搜索关键词
- **时间范围**：近1小时、近24小时、近7天、全部
- **来源平台**：微博、微信、B站、36氪、头条等
- **情感属性**：正面、负面、中性
- **处理状态**：未清洗、已入库

**API 端点**
```
POST /content/library/search
请求体：
{
  "search_text": "AI",
  "source_filter": ["微博", "36氪"],
  "sentiment_filter": ["negative"],
  "clean_status_filter": ["uncleaned"],
  "time_range": "24h",
  "page": 1,
  "page_size": 20
}
```

### 2. 内容清洗流水线 (The Pipeline)
表格式列表，支持以下操作：

| 操作 | 描述 |
|------|------|
| **🔍 预览** | 点击标题查看完整内容和链接 |
| **🔗 关联客户** | 将内容手动关联到特定客户 |
| **✏️ 修正标签** | 修正 AI 的自动分类和情感判定 |
| **❌ 删除** | 标记为已废弃（软删除，不会硬删除） |

**关键特性**：
- 热度评分：基于风险等级、来源权重、情感分数计算
- 行状态指示：已入库/已清洗/未清洗/已废弃
- 批量选择：支持多选和全选操作

### 3. 批量操作区 (Batch Actions)
当选中内容时出现，支持：

**[1] 批量删除**
```
POST /content/library/bulk-discard
请求体：
{
  "mention_ids": [1, 2, 3, 4, 5]
}
```

**[2] 屏蔽信源**
- 选择要屏蔽的信源
- 填写屏蔽原因
- 之后该信源的所有新内容自动标记为已废弃

```
POST /content/blacklist/add
请求体：
{
  "source_name": "贴吧",
  "reason": "垃圾广告泛滥"
}
```

**[3] 批量导出**
- 导出选中内容为 CSV 格式
- 包含标题、来源、时间、情感、热度、URL

### 4. 人工纠偏 (Manual Correction)
**场景**：AI 把"苹果发布会"误分为"水果新闻"，编辑手动纠正

```
POST /content/correct
请求体：
{
  "mention_id": 123,
  "new_category": "科技/新品发布",
  "new_sentiment": "positive"
}
```

**修正内容**：
- `new_category`：新的分类标签（可选）
- `new_sentiment`：正面/负面/中性（可选）

修正后内容自动标记为"已入库"状态。

### 5. 手动分发 (Manual Distribution)
**场景**：爬虫抓了"特斯拉在华销量新高"，但系统没自动关联到"特斯拉"客户

```
POST /content/associate
请求体：
{
  "mention_id": 456,
  "client_id": "CLI_1234567890_123"
}
```

**结果**：
- 内容立即关联到该客户
- 自动出现在该客户的监控工作台
- 触发风险预警（如果高危）

### 6. 黑名单管理 (Blacklist Management)
**添加到黑名单**
```
POST /content/blacklist/add
请求体：
{
  "source_name": "某营销号",
  "reason": "全是通稿，无新闻价值"
}
```

**效果**：
- 该信源的所有旧内容自动标记为已废弃
- 该信源的所有新内容自动丢弃，不进入系统
- 节省数据库空间

**获取黑名单**
```
GET /content/blacklist
```

**从黑名单移除**
```
POST /content/blacklist/remove
请求体：
{
  "source_name": "某营销号"
}
```

### 7. 数据质检统计 (Quality Stats)
**获取质检指标**
```
GET /content/quality-stats
响应：
{
  "total_count": 1250,           # 今日采集总数
  "garbage_count": 85,           # 可疑垃圾广告数
  "garbage_rate": 6.8,           # 垃圾率百分比
  "source_distribution": [       # 各来源的采集量
    {
      "source": "微博",
      "count": 450,
      "percentage": 36.0
    },
    ...
  ],
  "sentiment_distribution": {    # 情感分布
    "positive": {
      "count": 380,
      "percentage": 30.4
    },
    "negative": {
      "count": 420,
      "percentage": 33.6
    },
    "neutral": {
      "count": 450,
      "percentage": 36.0
    }
  }
}
```

**用途**：
- 监控爬虫数据质量
- 发现问题信源
- 调整爬虫策略

---

## 🗄️ 数据库结构

### 1. mentions 表扩展字段
```sql
-- 原有字段：id, client_id, source, title, content_text, url, publish_time, sentiment_score, risk_level, match_detail

-- 新增字段：
ALTER TABLE mentions ADD COLUMN clean_status VARCHAR(20) DEFAULT 'uncleaned';
ALTER TABLE mentions ADD COLUMN manual_category VARCHAR(50);
ALTER TABLE mentions ADD COLUMN manual_sentiment VARCHAR(20);
ALTER TABLE mentions ADD COLUMN is_archived INTEGER DEFAULT 0;
```

**字段说明**：
- `clean_status`：uncleaned(未清洗) | cleaned(已入库) | discarded(已废弃)
- `manual_category`：编辑手动修正的分类
- `manual_sentiment`：编辑手动修正的情感（positive/negative/neutral）
- `is_archived`：是否归档（0=否, 1=是）

### 2. source_blacklist 表
```sql
CREATE TABLE source_blacklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT UNIQUE,
    source_type VARCHAR(20),
    reason TEXT,
    created_at REAL,
    created_by VARCHAR(100)
);
```

### 3. content_library 表
```sql
CREATE TABLE content_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mention_id INTEGER,
    client_id VARCHAR(64),
    assigned_category VARCHAR(50),
    assigned_by VARCHAR(100),
    assigned_at REAL,
    FOREIGN KEY(mention_id) REFERENCES mentions(id),
    FOREIGN KEY(client_id) REFERENCES client_config(client_id)
);
```

---

## 🔌 API 端点清单

| 方法 | 路由 | 功能 | 权限 |
|-----|------|------|------|
| POST | `/content/library/search` | 全网内容库检索 | user |
| POST | `/content/library/bulk-discard` | 批量删除内容 | editor/admin |
| POST | `/content/blacklist/add` | 添加信源黑名单 | editor/admin |
| GET | `/content/blacklist` | 获取黑名单列表 | user |
| POST | `/content/blacklist/remove` | 从黑名单移除 | admin |
| POST | `/content/associate` | 手动关联到客户 | editor/admin |
| POST | `/content/correct` | 修正AI判定 | editor/admin |
| GET | `/content/quality-stats` | 获取数据质检统计 | user |

---

## 🎨 前端页面设计

### 页面入口
**左侧菜单 → 知识管理 → 全网内容库**

菜单项：
```vue
<div class="nav-item" @click="$emit('change', 'content_library')">
  <span class="icon">🌐</span> 全网内容库
</div>
```

### 页面构成

1. **Header 区域**
   - 页面标题
   - 质检统计卡片（实时更新）

2. **搜索区域**
   - 搜索框（全文检索）
   - 高级筛选器（时间、来源、情感、状态）

3. **批量操作区**
   - 显示已选中的内容数量
   - 批量删除、屏蔽信源、导出按钮

4. **内容表格**
   - 多列展示：标题、来源、时间、热度、AI判定、关联客户、操作
   - 可单选或全选
   - 分页导航

5. **模态框**
   - 内容预览
   - 客户关联选择
   - AI判定修正
   - 黑名单确认

6. **黑名单管理区**
   - 当前黑名单列表
   - 解除屏蔽按钮

---

## 💡 使用示例

### 场景 1：清除垃圾广告

1. 打开"全网内容库"
2. 在"处理状态"勾选"未清洗"
3. 搜索"兼职"、"刷单"等关键词
4. 多选识别出的垃圾内容
5. 点击"❌ 删除"一键清理
6. 系统自动标记为"已废弃"

### 场景 2：发现行业热点

1. 过滤"近1小时"的新采集内容
2. 按热度排序（右侧有火焰图标）
3. 找到"ChatGPT 发布新版本"这样的大新闻
4. 虽然没自动关联客户，但编辑看到了
5. 可点击"🔗 关联客户"关联到"AI科技组"

### 场景 3：纠正 AI 误判

1. 搜索"苹果"相关内容
2. 发现一条被分类为"农业"的"苹果发布会"新闻
3. 点击"✏️ 修正标签"
4. 修改分类为"科技/新品发布"
5. 修改情感为"positive"
6. 确认后自动标记为"已入库"

### 场景 4：屏蔽垃圾信源

1. 发现某个公众号的内容全是营销通稿
2. 选中该信源的多条内容
3. 点击"🚫 屏蔽信源"
4. 填写原因："营销号，通稿泛滥"
5. 系统自动将该源加入黑名单
6. 之后该源的所有内容自动丢弃

---

## 🔐 权限控制

- **viewer**: 只能浏览、搜索、预览内容
- **editor**: 可以删除、修正、关联、屏蔽信源
- **admin**: 拥有所有权限，包括从黑名单移除信源

---

## 📊 监控指标

系统每分钟更新以下指标：

- **今日采集数**：过去24小时新采集的内容总数
- **垃圾率**：可疑广告/采集总数 × 100%
- **情感分布**：正面、负面、中性的百分比
- **来源分布**：各平台的采集量排名

**预警规则**：
- 垃圾率 > 20% 时标记为"⚠️ 警告"
- 单一信源采集量 > 总量的30% 时需要检查

---

## 🚀 快速开始

### 后端启动
```bash
cd backend
python main.py
# FastAPI 将在 http://localhost:8000 启动
```

### 前端启动
```bash
cd frontend
npm run dev
# Vue 应用将在 http://localhost:5173 启动
```

### 数据库初始化
数据库将在首次运行 `init_monitor_db()` 时自动创建所有表和字段。

---

## 📝 常见问题

**Q: 删除的内容能恢复吗？**
A: 不能。删除是软删除（标记为 discarded），物理删除会丢失数据。如果需要恢复，需要直接修改数据库。

**Q: 黑名单中的内容会被删除吗？**
A: 是的。添加到黑名单时，该信源的所有旧内容自动标记为已废弃。新内容则不会进入系统。

**Q: 修正 AI 判定后，关联客户的监控会更新吗？**
A: 是的。修正后内容会立即反映在客户的监控工作台中。

**Q: 支持导出成其他格式吗？**
A: 目前仅支持 CSV 格式。可以在 Excel 中打开或导入其他工具。

---

## 📈 产品路线图

- [x] 全网内容库搜索和筛选
- [x] 批量删除和导出
- [x] 黑名单管理
- [x] 手动关联和纠偏
- [x] 数据质检统计
- [ ] ElasticSearch 集成（百万级亿级数据毫秒检索）
- [ ] 高级规则引擎（自定义质检规则）
- [ ] AI 反馈学习（选中错误数据，自动优化模型）
- [ ] 内容去重（精准识别相同或相似内容）

---

## 📞 技术支持

如有问题，请检查：
1. 后端 API 是否正常运行
2. 数据库表是否已创建
3. 前端是否正确导入了 GlobalContentLibrary 组件
4. 浏览器控制台是否有错误信息
