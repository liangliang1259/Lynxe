#!/usr/bin/env python3
"""
小红书数据 Markdown 生成脚本
从 JSON 数据生成格式化的 Markdown 文件
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

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
