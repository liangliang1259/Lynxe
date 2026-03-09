# 小红书热门资讯抓取 Func-Agent 设计文档

**设计日期**: 2025-03-09
**状态**: 设计完成，待实现

## 1. 概述

### 1.1 目标
创建一个 Func-Agent 模板，用于自动抓取小红书热门/发现页的笔记内容，提取标题、正文、作者信息和互动数据，并输出为 Markdown 格式文件。

### 1.2 核心功能
- 浏览器自动化访问小红书
- 滚动加载动态内容
- 提取笔记卡片数据
- 根据点赞数阈值终止抓取
- 输出格式化的 Markdown 文件

### 1.3 技术方案
采用 **Playwright 浏览器自动化** 方案，利用 Lynxe 现有的浏览器工具基础设施。

## 2. 架构设计

### 2.1 整体架构

```
用户输入参数 → Func-Agent执行 → 浏览器自动化 → 数据提取 → Markdown输出
```

### 2.2 核心组件

1. **Func-Agent模板** (`xhs_trending_scraper.json`)
   - 定义可配置的输入参数
   - 定义执行步骤序列

2. **浏览器导航步骤**
   - 打开小红书发现页/热门页
   - 处理可能的登录弹窗
   - 等待页面加载

3. **数据抓取循环**
   - 滚动加载更多内容
   - 提取当前页面的笔记卡片信息
   - 检查终止条件（最低点赞数）
   - 保存已抓取数据

4. **数据格式化与保存**
   - 将提取的数据格式化为 Markdown
   - 保存到 workspace 目录

### 2.3 执行流程

```
┌─────────────────┐
│ 接收用户参数     │
│ - minLikes      │
│ - maxPosts      │
│ - scrollWait    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 步骤1: 导航      │
│ 打开小红书发现页 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 步骤2: 循环抓取  │
│ ┌─────────────┐│
│ │ 滚动加载     ││
│ └──────┬──────┘│
│        │       │
│ ▼      │       │
│ ┌─────────────┐│
│ │ 提取笔记卡片 ││
│ └──────┬──────┘│
│        │       │
│ ▼      │       │
│ ┌─────────────┐│
│ │ 检查终止条件 ││
│ └──────┬──────┘│
│        │       │
│   否   │ 是    │
│ ┌─────┴─┐ ┌───┴────┐
│ │继续   │ │退出循环 ││
│ └───────┘ └────────┘│
└─────────────────────┘
         │
         ▼
┌─────────────────┐
│ 步骤3: 格式化    │
│ 生成Markdown     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 步骤4: 保存文件  │
│ 输出.md文件      │
└─────────────────┘
```

## 3. 组件设计

### 3.1 Func-Agent 模板配置

**文件位置**: `src/main/resources/prompts/startup-plans/zh/xhs_trending_scraper.json`

**配置参数**:

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `minLikes` | number | 1000 | 最低点赞数，低于此值停止抓取 |
| `maxPosts` | number | 50 | 最多抓取帖子数（防止无限循环） |
| `scrollWait` | number | 2000 | 滚动后等待时间（毫秒） |
| `category` | string | "explore" | 抓取分类：explore(发现)/fashion(时尚)/food(美食) |

**执行步骤**:

1. **步骤1：浏览器导航**
   - 工具: `navigate_browser`
   - 操作: 打开小红书发现页
   - 代理: `ConfigurableDynaAgent`

2. **步骤2：数据抓取循环**
   - 工具: `think`, `navigate_browser` (滚动), `get_web_content`, `bash` (数据处理)
   - 操作: 循环滚动、提取数据、检查终止条件
   - 代理: `ConfigurableDynaAgent`

3. **步骤3：保存结果**
   - 工具: `save_file_to_workspace`
   - 操作: 保存 Markdown 文件
   - 代理: `ConfigurableDynaAgent`

### 3.2 数据提取策略

**提取字段**:
```javascript
{
  title: "笔记标题",
  content: "笔记内容摘要",
  author: "作者昵称",
  authorUrl: "作者主页链接",
  likes: "点赞数",
  collects: "收藏数",
  comments: "评论数",
  shares: "分享数",
  postUrl: "笔记链接",
  coverImage: "封面图URL"
}
```

**选择器策略** (ARIA 标签 + CSS 选择器):
- 笔记卡片容器: `section` > `div` (包含 note-card 类名)
- 标题: `a[role="link"]` > `span`
- 作者: `[class*="author"]` > `span`
- 互动数据: `[class*="like"]`, `[class*="collect"]` 等

## 4. 数据流设计

### 4.1 数据流图

```
用户请求
  → PlanTemplateService (加载模板、替换参数)
  → 步骤1: 导航到小红书
  → 步骤2: 循环抓取数据
    → 2.1 滚动页面
    → 2.2 等待内容加载
    → 2.3 获取页面内容
    → 2.4 解析笔记卡片
    → 2.5 检查终止条件
    → 2.6 保存到中间数据
    → 2.7 返回 2.1 继续
  → 步骤3: 格式化输出 (Markdown)
  → 返回结果
```

### 4.2 中间数据结构

**临时文件**: `workspace/xhs_raw_data.json`

```json
{
  "posts": [
    {
      "title": "...",
      "content": "...",
      "author": "...",
      "likes": 1500,
      "collects": 200,
      "comments": 50,
      "shares": 10,
      "postUrl": "https://...",
      "coverImage": "https://...",
      "scrapedAt": "2025-03-09T14:30:00"
    }
  ],
  "metadata": {
    "totalPosts": 45,
    "scrapedAt": "2025-03-09T14:30:00",
    "params": {
      "minLikes": 1000,
      "maxPosts": 50
    }
  }
}
```

### 4.3 最终输出格式 (Markdown)

```markdown
# 小红书热门资讯汇总

**抓取时间**: 2025-03-09 14:30:00
**抓取条件**: 最低点赞数 1000
**抓取数量**: 45篇

---

## 1. [标题]

**作者**: [@作者名](链接)
**数据**: 👍 1500 | ⭐ 200 | 💬 50 | 📤 10
**链接**: [查看原文](链接)

内容摘要...

---
```

## 5. 错误处理

### 5.1 错误场景与处理策略

| 错误场景 | 处理策略 |
|----------|----------|
| 页面加载超时 | 重试3次，每次延长等待时间；失败则终止并返回错误 |
| 无法找到笔记卡片 | 检查页面结构是否变化；尝试备用选择器 |
| 滚动无效 | 检查是否到达页面底部；尝试不同的滚动方式 |
| 网络连接失败 | 等待5秒后重试 |
| 登录弹窗遮挡 | 尝试关闭弹窗；继续执行 |

### 5.2 终止条件

- **成功终止**: 达到最低点赞数阈值 OR 达到最大帖子数
- **失败终止**: 连续3次滚动后无新内容 OR 网络错误重试失败

## 6. API 端点

### 6.1 执行端点

```
POST /api/executor/executeByToolNameAsync
```

**请求体**:
```json
{
  "toolName": "小红书热门资讯抓取",
  "serviceGroup": "scrapers",
  "replacementParams": {
    "minLikes": 1000,
    "maxPosts": 50,
    "scrollWait": 2000,
    "category": "explore"
  }
}
```

**响应**:
```json
{
  "planId": "xhs-scraper-20250309-143000",
  "status": "pending",
  "conversationId": "conv-123",
  "toolName": "小红书热门资讯抓取"
}
```

### 6.2 查询执行状态

```
GET /api/executor/details/{planId}
```

## 7. 测试计划

### 7.1 单元测试
- 数据解析函数测试
- Markdown 格式化测试

### 7.2 集成测试
- 完整抓取流程测试（小数据量）
- 不同终止条件测试

### 7.3 手动验证
- 输出文件内容验证
- 边界条件测试（minLikes=0, maxPosts=1等）

## 8. 依赖清单

- 现有组件: `NavigateBrowserTool`, `GetWebContentBrowserTool`
- 现有组件: `Bash` 工具（用于执行 Python 解析脚本）
- 现有组件: 文件系统保存工具
- 无需新增 Java 类（使用现有工具即可）

## 9. 实现文件清单

1. `src/main/resources/prompts/startup-plans/zh/xhs_trending_scraper.json` - Func-Agent 模板
2. `src/main/resources/prompts/startup-plans/en/xhs_trending_scraper.json` - 英文版模板（可选）

## 10. 后续优化方向

1. 支持更多分类（美食、时尚、数码等）
2. 支持定时任务（CronTool）
3. 支持数据去重（避免重复抓取）
4. 支持图片下载
5. 支持导出到数据库
