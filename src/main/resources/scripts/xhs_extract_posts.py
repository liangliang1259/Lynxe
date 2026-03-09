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
            if '小红书' in line or (len(line) > 10 and len(line) < 100 and not line.startswith('#')):
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
