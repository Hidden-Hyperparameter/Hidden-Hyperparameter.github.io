## If you are here because Github Workflow Fails

**You can only use `|` in thw following cases:**
- In a table. In such case, the line must start with `|`.
- `\left|` and `\right|` for abs: $\left|x\right|$
- `\|` for norm: $\|x\|^2$

For other cases, use `\mid` instead.

# Paper sharing website

本仓库主要用于记录大家读过的论文，方便大家共享/查找

包括的内容：你的名字，论文名，链接，（年份），解决的问题和方法，引用的在本仓库中的论文（如果是某篇的改进），可以尽量用中文，但是涉及名词之类的东西就用英文，比如"文字被分割成令牌以后通过词嵌入进入多头注意力机制，前馈神经网络和归一化层，并使用线性整流函数后加上残差连接"就没必要用中文

值得复现的论文可以标注

## 创建一个note

1. 在[_posts](./_posts/)文件夹创造一个文件，文件名必须是`yyyy-mm-dd-title.md`。
2. 在文件中写入以下“头文件”：

```
---
title: 名字-编号
paper: "Paper Title"
paper_url: "Path to the paper" 
paper_year: Year the paper was published
tags: 
    - tag1
    - tag2
layout: post
---
```

（对于`tags`，请尽可能使用已有的标签。）

比如，

```
---
title: JZC-001
paper: "LifeGPT: Topology-Agnostic Generative Pretrained Transformer Model for Cellular Automata"
paper_url: "https://arxiv.org/html/2409.12182v1" 
paper_year: 2024
tags: 
    - Transformer
    - Silly
layout: post
---
```

3. 接下来的内容可以完全正常完成。注意如果你使用图片，请将图片放在`papers/FOLDER`文件夹中，然后使用 **绝对路径** 引用图片（即以`/`开头）。

## 常见的问题

1. 不要使用 `p(z|x)` 这样的记号，而是应该用 `p(z\mid x)`。否则，在渲染的时候会被渲染成表格