# 小红书热门资讯抓取使用指南

## 功能概述

小红书热门资讯抓取 Func-Agent 可以自动访问小红书发现页，抓取热门笔记的标题、内容、作者信息和互动数据，并输出为格式化的 Markdown 文件。

## 快速开始

### 1. 基本使用

通过 API 调用执行抓取：

```bash
curl -X POST http://localhost:18080/api/executor/executeByToolNameAsync \
  -H "Content-Type: application/json" \
  -d '{
    "toolName": "小红书热门资讯抓取",
    "serviceGroup": "scrapers",
    "replacementParams": {
      "minLikes": 1000,
      "maxPosts": 50,
      "scrollWait": 2000,
      "category": "explore"
    }
  }'
```

### 2. 查询执行状态

```bash
curl http://localhost:18080/api/executor/details/{planId}
```

### 3. 获取结果

执行完成后，在 workspace 目录中查找生成的 Markdown 文件：
```
xhs_trending_YYYY-MM-DD_HH-mm-ss.md
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| minLikes | number | 1000 | 最低点赞数，低于此值停止抓取 |
| maxPosts | number | 50 | 最多抓取帖子数 |
| scrollWait | number | 2000 | 滚动后等待时间（毫秒） |
| category | string | "explore" | 抓取分类 |

## 使用场景

### 场景 1：抓取高热度内容

```json
{
  "minLikes": 10000,
  "maxPosts": 20,
  "scrollWait": 3000
}
```

### 场景 2：快速测试

```json
{
  "minLikes": 0,
  "maxPosts": 5,
  "scrollWait": 1000
}
```

## 输出格式

生成的 Markdown 文件包含以下信息：

- 抓取时间和条件
- 每篇笔记的：
  - 标题
  - 作者信息（带链接）
  - 互动数据（点赞、收藏、评论、分享）
  - 原文链接
  - 内容摘要

## 注意事项

1. 确保网络连接稳定
2. 大量抓取时建议适当增加 scrollWait 参数
3. 某些内容可能需要登录才能查看
4. 请遵守小红书的使用条款
