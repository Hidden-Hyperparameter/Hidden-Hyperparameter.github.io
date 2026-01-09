# Upload Paper Module

## Overview

`upload_file_main.py` 是一个自动化上传论文笔记到 Jekyll 博客仓库的模块。

主要功能：
- 自动从arxiv URL提取论文年份
- 自动复制markdown中的本地图片到papers目录
- 生成Jekyll兼容的frontmatter

## 核心函数

### `upload_paper()` - 主函数

将本地 Markdown 文件上传为博客 post，自动处理图片和元数据。

**参数：**
- `md_path` (str, 必需): 源 markdown 文件的完整路径
- `who` (str, 必需): 编辑者标识，如 "ZKY", "SQA", "JZC"
- `tags` (list, 必需): 标签列表，用于分类论文
- `paper_link` (str, 可选): 论文的 arxiv/PDF 链接（支持自动提取paper_year）
- `title` (str, 可选): 论文标题（不提供则自动提取）
- `paper_year` (str, 可选): 论文年份（不提供则尝试从arxiv提取）
- `time` (str, 可选): 发布日期，格式"YYYY-MM-DD"，默认当前日期

**返回值：** 生成的 post 文件的完整路径

**处理流程：**
1. 读取源 markdown 文件
2. 复制markdown中的本地图片到 `papers/{post_id}/` 目录
3. 更新markdown中的图片路径
4. 从arxiv URL提取论文年份（严格格式验证）
5. 自动生成编号和文件名
6. 生成Jekyll frontmatter
7. 保存到 `_posts/` 目录

### `extract_arxiv_year()` - arxiv年份提取

从arxiv URL格式 `https://arxiv.org/pdf/YYMM.XXXXX` 提取四位数年份。

**示例：**
```python
extract_arxiv_year("https://arxiv.org/pdf/2503.09641")  # Returns "2025"
extract_arxiv_year("https://arxiv.org/pdf/2410.10733")  # Returns "2024"
```

**错误处理：** URL不符合格式时抛出ValueError异常

### `copy_images()` - 图片处理

复制markdown中的本地图片，更新路径为相对路径。

支持格式：
- Markdown: `![alt](path/to/image.png)`
- HTML: `<img src="path/to/image.png">`

### `get_next_number()` - 编号生成

根据编辑者标识获取下一个递增编号。

### `generate_frontmatter()` - Frontmatter生成

生成符合Jekyll标准的YAML frontmatter。

## 使用示例

### 基础用法

```python
import upload_file_main

upload_file_main.upload_paper(
    md_path="D:/Desktop/texts/笔记/算法/T2I_Papers.md",
    paper_link="https://arxiv.org/pdf/2503.09641",
    who="ZKY",
    tags=["MultiModal", "Diffusion"],
)
```

自动生成：
- Post文件: `_posts/2026-01-09-ZKY002.md`
- 图片目录: `papers/ZKY002/`
- Paper year: `2025` (从arxiv URL提取)

## 输出文件

### Post文件结构

文件: `_posts/2026-01-09-ZKY001.md`

```markdown
---
title: ZKY001
paper: "SANA"
paper_url: "https://arxiv.org/pdf/2503.09641"
paper_year: 2025
tags:
    - "MultiModal"
    - "Diffusion"
layout: post
---

## SANA

sana 是一个工业界模型...

![Image](papers/ZKY001/image.png)
```

### 目录结构

```
Hidden-Hyperparameter.github.io/
├── _posts/
│   ├── 2026-01-09-ZKY001.md
│   ├── 2026-01-10-SQA020.md
│   └── ...
├── papers/
│   ├── ZKY001/
│   │   ├── image1.png
│   │   └── image2.png
│   ├── SQA020/
│   └── ...
└── utils/
    ├── upload_file_main.py
    └── uploader.py
```

## 文件命名规则

**Post文件名:** `YYYY-MM-DD-{who}{003d}.md`
- 示例: `2026-01-09-ZKY001.md`

**图片目录:** `papers/{who}{003d}/`
- 示例: `papers/ZKY001/`

**图片相对路径:** `papers/{who}{003d}/{filename}`
- 示例: `papers/ZKY001/image.png`

## 错误处理

### arxiv URL格式验证

正确格式：
```python
extract_arxiv_year("https://arxiv.org/pdf/2503.09641")  # OK
extract_arxiv_year("https://arxiv.org/abs/2501.17161")  # OK
```

错误格式会抛出ValueError：
```python
try:
    extract_arxiv_year("https://example.com/paper.pdf")
except ValueError as e:
    # Error: Invalid arxiv URL format
```

### 图片处理

- 缺失的本地图片：产生警告，保留原路径
- HTTP图片链接：自动跳过
- markdown格式错误：正确识别并处理

## 技术细节

### arxiv年份转换

arxiv ID格式: `YYMM.XXXXX`
- 前两位是年份后两位: `25` → `2025`, `24` → `2024`
- 支持1900-2099年范围

### 图片路径处理

1. 识别markdown和HTML中的图片
2. 解析相对或绝对路径
3. 复制文件到目标目录
4. 更新markdown中的引用为相对路径
