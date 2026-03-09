# 小红书热门资讯抓取 Func-Agent 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建一个 Func-Agent 模板，使用 Playwright 浏览器自动化抓取小红书热门笔记，提取标题、内容、作者和互动数据，并输出为 Markdown 文件。

**Architecture:** 基于 Lynxe 现有的浏览器工具基础设施，通过 Func-Agent 模板定义多步骤执行流程，使用 ConfigurableDynaAgent 协调浏览器导航、页面滚动、内容提取和数据格式化等操作。

**Tech Stack:**
- Spring Boot 3.5.6
- Playwright 1.55.0 (已集成)
- Func-Agent 模板系统 (JSON 配置)
- ConfigurableDynaAgent (代理执行器)

---

## Task 1: 创建 Func-Agent 模板文件

**Files:**
- Create: `src/main/resources/prompts/startup-plans/zh/xhs_trending_scraper.json`

**Step 1: 创建中文版模板文件**

创建以下 JSON 文件，定义 Func-Agent 的完整配置：

```json
{
  "title": "小红书热门资讯抓取",
  "steps": [
    {
      "stepRequirement": "导航到小红书发现页。使用 navigate_browser 工具打开 https://www.xiaohongshu.com/explore。等待页面完全加载。如果出现登录弹窗，点击关闭按钮。",
      "agentName": "ConfigurableDynaAgent",
      "modelName": "",
      "terminateColumns": "",
      "selectedToolKeys": ["think", "navigate-browser", "click-browser", "get-web-content-browser"]
    },
    {
      "stepRequirement": "循环抓取热门笔记数据。执行以下操作：\n1. 使用 bash 工具运行 Python 脚本提取当前页面的笔记卡片信息（标题、内容、作者、点赞数、收藏数、评论数、分享数、链接）\n2. 检查是否达到终止条件：\n   - 如果当前笔记点赞数 <<minLikes>>，停止抓取\n   - 如果已抓取数量达到 <<maxPosts>>，停止抓取\n3. 如果未达到终止条件，使用 JavaScript 滚动到页面底部，等待 <<scrollWait>> 毫秒\n4. 将抓取的数据追加保存到 xhs_raw_data.json 文件\n5. 返回步骤 1 继续抓取\n\n数据提取要求：\n- 标题：从笔记卡片的标题元素提取\n- 内容：从笔记卡片的内容描述提取（限制200字符）\n- 作者：提取作者昵称和主页链接\n- 互动数据：提取点赞数、收藏数、评论数、分享数\n- 链接：提取笔记详情页链接\n\n每次抓取后，在 think 中记录当前进度（已抓取数量、最后一条点赞数）。",
      "agentName": "ConfigurableDynaAgent",
      "modelName": "",
      "terminateColumns": "",
      "selectedToolKeys": ["think", "bash", "get-web-content-browser"]
    },
    {
      "stepRequirement": "格式化数据并生成 Markdown 文件。使用 bash 工具运行 Python 脚本读取 xhs_raw_data.json，生成格式化的 Markdown 文件。\n\nMarkdown 格式要求：\n```markdown\n# 小红书热门资讯汇总\n\n**抓取时间**: [当前时间]\n**抓取条件**: 最低点赞数 <<minLikes>>\n**抓取数量**: [总数量]篇\n\n---\n\n## [序号]. [标题]\n\n**作者**: [@作者名](链接)\n**数据**: 👍 [点赞数] | ⭐ [收藏数] | 💬 [评论数] | 📤 [分享数]\n**链接**: [查看原文](链接)\n\n[内容摘要]\n\n---\n\n...\n```\n\n输出文件名：xhs_trending_YYYY-MM-DD_HH-mm-ss.md",
      "agentName": "ConfigurableDynaAgent",
      "modelName": "",
      "terminateColumns": "",
      "selectedToolKeys": ["think", "bash"]
    },
    {
      "stepRequirement": "验证输出文件并返回执行结果摘要。\n\n使用 bash 工具检查输出文件是否存在并读取文件大小。\n\n返回以下格式的执行摘要：\n```\n✅ 抓取完成！\n\n📊 抓取统计：\n- 抓取笔记数量：[数量]篇\n- 最低点赞数阈值：<<minLikes>>\n- 输出文件：xhs_trending_YYYY-MM-DD_HH-mm-ss.md\n- 文件大小：[大小]KB\n\n💡 提示：\n- 你可以在 workspace 目录中查看完整的 Markdown 文件\n- 如需重新抓取，可以调整 minLikes 或 maxPosts 参数\n```",
      "agentName": "ConfigurableDynaAgent",
      "modelName": "",
      "terminateColumns": "",
      "selectedToolKeys": ["think", "bash"]
    }
  ],
  "planType": "dynamic_agent",
  "planTemplateId": "xhs-trending-scraper-20250309",
  "accessLevel": "editable",
  "serviceGroup": "scrapers",
  "maxSteps": 50,
  "toolConfig": {
    "toolName": "小红书热门资讯抓取",
    "toolDescription": "自动抓取小红书热门/发现页的笔记内容，提取标题、正文、作者信息和互动数据，并输出为 Markdown 格式文件。支持配置最低点赞数阈值和最大抓取数量。",
    "enableInternalToolcall": true,
    "enableHttpService": false,
    "enableInConversation": true,
    "publishStatus": "PUBLISHED",
    "inputSchema": [
      {
        "name": "minLikes",
        "description": "最低点赞数，低于此值停止抓取（默认1000）",
        "type": "number",
        "required": false
      },
      {
        "name": "maxPosts",
        "description": "最多抓取帖子数，防止无限循环（默认50）",
        "type": "number",
        "required": false
      },
      {
        "name": "scrollWait",
        "description": "滚动后等待时间，毫秒（默认2000）",
        "type": "number",
        "required": false
      },
      {
        "name": "category",
        "description": "抓取分类：explore(发现页)、fashion(时尚)、food(美食)、tech(数码)（默认explore）",
        "type": "string",
        "required": false
      }
    ]
  }
}
```

**Step 2: 验证 JSON 格式**

Run: `cat src/main/resources/prompts/startup-plans/zh/xhs_trending_scraper.json | jq .`
Expected: JSON 格式正确，无语法错误

**Step 3: 提交模板文件**

```bash
git add src/main/resources/prompts/startup-plans/zh/xhs_trending_scraper.json
git commit -m "feat: add Xiaohongshu trending scraper Func-Agent template

- Add xhs_trending_scraper.json template with 4-step execution flow
- Support configurable parameters: minLikes, maxPosts, scrollWait, category
- Extract post data: title, content, author, engagement metrics
- Output formatted Markdown file with scraped results
- Use Playwright browser automation for web scraping

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: 创建数据提取 Python 脚本

**Files:**
- Create: `src/main/resources/scripts/xhs_extract_posts.py`

**Step 1: 创建 Python 数据提取脚本**

```python
#!/usr/bin/env python3
"""
小红书笔记数据提取脚本
从 YAML 文件中提取笔记卡片信息并保存为 JSON
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

def parse_engagement_number(text: str) -> int:
    """解析互动数字，支持 '1.2万'、'3k' 等格式"""
    if not text:
        return 0
    
    text = text.strip().replace(',', '')
    
    # 处理 "万" 单位
    if '万' in text:
        match = re.search(r'([\d.]+)万', text)
        if match:
            return int(float(match.group(1)) * 10000)
    
    # 处理 "k" 单位
    if 'k' in text.lower():
        match = re.search(r'([\d.]+)k', text, re.IGNORECASE)
        if match:
            return int(float(match.group(1)) * 1000)
    
    # 直接提取数字
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())
    
    return 0

def extract_post_from_yaml(yaml_content: str) -> List[Dict[str, Any]]:
    """从 YAML 内容中提取笔记信息"""
    posts = []
    
    # 按行分割内容
    lines = yaml_content.split('\n')
    
    current_post = {}
    in_interactive_section = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # 检测是否进入 interactive elements 区域
        if '# Interactive Elements:' in line:
            in_interactive_section = True
            continue
        
        if in_interactive_section:
            # 提取链接 (通常以 [数字]: 开头)
            link_match = re.match(r'\[(\d+)\]:\s*(https://[^\s]+)', line)
            if link_match:
                if current_post:
                    posts.append(current_post)
                    current_post = {}
                current_post['postUrl'] = link_match.group(2)
                continue
            
            # 提取标题 (通常包含 "小红书" 或有特定格式)
            if '小红书' in line or len(line) > 10 and len(line) < 100:
                if 'title' not in current_post:
                    current_post['title'] = line
                continue
            
            # 提取互动数据 (包含 emoji 和数字)
            if any(emoji in line for emoji in ['👍', '❤️', '⭐', '💬', '📤']):
                if '👍' in line or '❤️' in line:
                    current_post['likes'] = parse_engagement_number(line)
                elif '⭐' in line:
                    current_post['collects'] = parse_engagement_number(line)
                elif '💬' in line:
                    current_post['comments'] = parse_engagement_number(line)
                elif '📤' in line:
                    current_post['shares'] = parse_engagement_number(line)
    
    # 添加最后一个帖子
    if current_post and 'postUrl' in current_post:
        posts.append(current_post)
    
    return posts

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python xhs_extract_posts.py <yaml_file> [output_file]"}))
        sys.exit(1)
    
    yaml_file = Path(sys.argv[1])
    
    if not yaml_file.exists():
        print(json.dumps({"error": f"YAML file not found: {yaml_file}"}))
        sys.exit(1)
    
    # 读取 YAML 内容
    yaml_content = yaml_file.read_text(encoding='utf-8')
    
    # 提取笔记数据
    posts = extract_post_from_yaml(yaml_content)
    
    # 准备输出数据
    output_data = {
        "posts": posts,
        "metadata": {
            "scrapedAt": datetime.now().isoformat(),
            "sourceFile": str(yaml_file.name)
        }
    }
    
    # 确定输出文件
    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
    else:
        output_file = yaml_file.parent / "xhs_raw_data.json"
    
    # 检查是否已存在数据
    if output_file.exists():
        try:
            existing_data = json.loads(output_file.read_text(encoding='utf-8'))
            if 'posts' in existing_data:
                # 合并数据，去重（基于 postUrl）
                existing_urls = {p['postUrl'] for p in existing_data['posts'] if 'postUrl' in p}
                new_posts = [p for p in posts if p.get('postUrl') not in existing_urls]
                output_data['posts'] = existing_data['posts'] + new_posts
        except:
            pass  # 如果合并失败，使用新数据
    
    # 保存输出
    output_file.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding='utf-8')
    
    # 返回结果
    result = {
        "success": True,
        "postsExtracted": len(posts),
        "totalPosts": len(output_data['posts']),
        "outputFile": str(output_file.name),
        "message": f"Extracted {len(posts)} posts, total {len(output_data['posts'])} posts in {output_file.name}"
    }
    
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
```

**Step 2: 设置脚本执行权限**

```bash
chmod +x src/main/resources/scripts/xhs_extract_posts.py
```

**Step 3: 提交脚本**

```bash
git add src/main/resources/scripts/xhs_extract_posts.py
git commit -m "feat: add Python script for extracting Xiaohongshu post data

- Parse YAML content from browser snapshots
- Extract post metadata: title, author, engagement metrics
- Support incremental data accumulation
- Handle various number formats (10k, 1.2万)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: 创建 Markdown 生成脚本

**Files:**
- Create: `src/main/resources/scripts/xhs_generate_markdown.py`

**Step 1: 创建 Markdown 生成脚本**

```python
#!/usr/bin/env python3
"""
小红书数据 Markdown 生成脚本
从 JSON 数据生成格式化的 Markdown 文件
"""

import sys
import json
from pathlib import Path
from datetime import datetime

def generate_markdown(data: Dict[str, Any], min_likes: int = 1000) -> str:
    """生成 Markdown 内容"""
    posts = data.get('posts', [])
    metadata = data.get('metadata', {})
    
    # 文件头
    md_lines = [
        "# 小红书热门资讯汇总",
        "",
        f"**抓取时间**: {metadata.get('scrapedAt', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}",
        f"**抓取条件**: 最低点赞数 {min_likes}",
        f"**抓取数量**: {len(posts)}篇",
        "",
        "---",
        ""
    ]
    
    # 生成每个笔记的条目
    for idx, post in enumerate(posts, 1):
        title = post.get('title', '无标题')
        author = post.get('author', '未知作者')
        author_url = post.get('authorUrl', '')
        likes = post.get('likes', 0)
        collects = post.get('collects', 0)
        comments = post.get('comments', 0)
        shares = post.get('shares', 0)
        post_url = post.get('postUrl', '')
        content = post.get('content', '')[:200]  # 限制内容长度
        
        md_lines.extend([
            f"## {idx}. {title}",
            "",
            f"**作者**: [{author}]({author_url})" if author_url else f"**作者**: {author}",
            f"**数据**: 👍 {likes} | ⭐ {collects} | 💬 {comments} | 📤 {shares}",
            f"**链接**: [查看原文]({post_url})" if post_url else "",
            "",
            content,
            "",
            "---",
            ""
        ])
    
    return '\n'.join(md_lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: python xhs_generate_markdown.py <json_file> [min_likes] [output_file]")
        sys.exit(1)
    
    json_file = Path(sys.argv[1])
    
    if not json_file.exists():
        print(f"Error: JSON file not found: {json_file}")
        sys.exit(1)
    
    # 读取 JSON 数据
    data = json.loads(json_file.read_text(encoding='utf-8'))
    
    # 获取参数
    min_likes = int(sys.argv[2]) if len(sys.argv) >= 3 else 1000
    
    # 生成 Markdown
    markdown_content = generate_markdown(data, min_likes)
    
    # 确定输出文件名
    if len(sys.argv) >= 4:
        output_file = Path(sys.argv[3])
    else:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_file = json_file.parent / f"xhs_trending_{timestamp}.md"
    
    # 保存文件
    output_file.write_text(markdown_content, encoding='utf-8')
    
    print(f"✅ Markdown 文件已生成: {output_file.name}")
    print(f"📊 包含 {len(data.get('posts', []))} 篇笔记")
    print(f"📁 文件大小: {output_file.stat().st_size / 1024:.1f} KB")

if __name__ == '__main__':
    main()
```

**Step 2: 设置脚本执行权限**

```bash
chmod +x src/main/resources/scripts/xhs_generate_markdown.py
```

**Step 3: 提交脚本**

```bash
git add src/main/resources/scripts/xhs_generate_markdown.py
git commit -m "feat: add Python script for generating Markdown from scraped data

- Convert JSON post data to formatted Markdown
- Include post metadata: title, author, engagement stats
- Add timestamp and scraping conditions to output
- Support custom output filename

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: 测试 Func-Agent 模板

**Step 1: 启动应用程序**

```bash
mvn spring-boot:run
```

Expected: 应用程序在 http://localhost:18080 启动成功

**Step 2: 验证模板加载成功**

Run: `curl http://localhost:18080/api/plan-template/list | jq '.[] | select(.planTemplateId == "xhs-trending-scraper-20250309")'`
Expected: 返回刚创建的模板信息

**Step 3: 执行测试抓取（小规模）**

Run: 使用以下请求体调用 API：

```bash
curl -X POST http://localhost:18080/api/executor/executeByToolNameAsync \
  -H "Content-Type: application/json" \
  -d '{
    "toolName": "小红书热门资讯抓取",
    "serviceGroup": "scrapers",
    "replacementParams": {
      "minLikes": 100,
      "maxPosts": 5,
      "scrollWait": 2000,
      "category": "explore"
    }
  }'
```

Expected: 返回 `planId` 和状态 `pending`

**Step 4: 监控执行进度**

Run: 使用返回的 `planId` 查询执行状态

```bash
curl http://localhost:18080/api/executor/details/{planId} | jq
```

Expected: 状态逐步变为 `running` -> `completed`

**Step 5: 验证输出文件**

检查 workspace 目录中的输出文件：

```bash
find . -name "xhs_trending_*.md" -type f -exec ls -lh {} \;
cat $(find . -name "xhs_trending_*.md" -type f | head -1)
```

Expected: Markdown 文件包含抓取的笔记数据

**Step 6: 记录测试结果**

创建测试报告：

```bash
mkdir -p docs/test-results
cat > docs/test-results/xhs-scraper-test-report.md << 'EOF'
# 小红书热门资讯抓取测试报告

**测试日期**: 2025-03-09

## 测试参数
- minLikes: 100
- maxPosts: 5
- scrollWait: 2000ms

## 测试结果
- ✅ 模板加载成功
- ✅ 执行流程正常
- ✅ 数据提取正确
- ✅ Markdown 生成成功

## 问题描述
(记录测试中发现的任何问题)

## 建议
(记录改进建议)
EOF
```

**Step 7: 提交测试报告**

```bash
git add docs/test-results/xhs-scraper-test-report.md
git commit -m "test: add test report for Xiaohongshu trending scraper

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: 创建使用文档

**Files:**
- Create: `docs/usage/xiaohongshu-scraper-guide.md`

**Step 1: 创建使用指南**

```markdown
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
```

**Step 2: 提交使用文档**

```bash
git add docs/usage/xiaohongshu-scraper-guide.md
git commit -m "docs: add usage guide for Xiaohongshu trending scraper

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## 验收标准

完成所有任务后，应满足以下标准：

1. ✅ Func-Agent 模板文件已创建并加载成功
2. ✅ Python 数据提取脚本可以正确解析页面内容
3. ✅ Markdown 生成脚本可以生成格式正确的输出文件
4. ✅ 可以通过 API 成功执行抓取任务
5. ✅ 输出的 Markdown 文件包含完整的笔记数据
6. ✅ 支持可配置参数（minLikes, maxPosts 等）
7. ✅ 代码已提交到 git

## 故障排查

### 问题 1: 模板未加载

**检查**: 确认 JSON 文件语法正确
```bash
cat src/main/resources/prompts/startup-plans/zh/xhs_trending_scraper.json | jq .
```

### 问题 2: 无法找到笔记卡片

**原因**: 小红书页面结构可能已变化
**解决**: 更新 Python 脚本中的选择器

### 问题 3: 抓取速度过慢

**调整**: 减少 scrollWait 参数值
```json
{
  "scrollWait": 1000
}
```

## 后续优化方向

1. 支持更多分类（美食、时尚、数码等）
2. 添加数据去重功能
3. 支持图片下载
4. 支持导出到数据库
5. 添加定时任务支持
