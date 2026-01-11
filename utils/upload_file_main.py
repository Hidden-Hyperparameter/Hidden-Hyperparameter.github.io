import os
from datetime import datetime
import re
import shutil
from pathlib import Path


# ANSI color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def _print_warning(message: str):
    """Print warning message in red color"""
    print(f"{Colors.RED}Warning: {message}{Colors.RESET}")


def _print_success(message: str):
    """Print success message in green color"""
    print(f"{Colors.GREEN}{message}{Colors.RESET}")


def _print_info(message: str):
    """Print info message in blue color"""
    print(f"{Colors.BLUE}{message}{Colors.RESET}")


# 在定义print函数后再导入arxiv
try:
    import arxiv
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False
    _print_warning("arxiv package not installed. Install with: pip install arxiv")


def get_arxiv_title(url: str) -> str:
    """
    从arxiv URL或ID获取论文标题
    
    Args:
        url: arxiv URL或ID，如 "https://arxiv.org/abs/2501.03215" 或 "2501.03215"
        
    Returns:
        论文标题，如果失败则返回None
    """
    if not ARXIV_AVAILABLE:
        _print_warning("arxiv package not available. Cannot fetch title from arXiv.")
        return None
    
    try:
        # 从URL或ID中提取arxiv ID
        id_pattern = r"(\d{4}\.\d{4,5})"
        match = re.search(id_pattern, url)
        
        if not match:
            _print_warning(f"Could not extract arxiv ID from: {url}")
            return None
        
        paper_id = match.group(1)
        _print_info(f"Fetching title for arxiv ID: {paper_id}")
        
        # 调用arxiv API查询
        search = arxiv.Search(id_list=[paper_id])
        paper = next(search.results(), None)
        
        if paper is None:
            _print_warning(f"Paper not found on arXiv: {paper_id}")
            return None
        
        # 清洗标题（去除换行符）
        title = paper.title.replace('\n', ' ').strip()
        _print_success(f"Fetched title from arXiv: {title}")
        return title
        
    except Exception as e:
        _print_warning(f"Failed to fetch arxiv title: {e}")
        return None


def upload_paper(
    md_path: str,
    who: str,
    tags: list,
    paper_link: str = None,
    title: str = None,
    paper_year: str = None,
    time: str = None,
    who_count: str = None,
):
    """
    上传论文笔记到博客仓库
    
    Args:
        md_path: 源markdown文件的完整路径
        who: 编辑者标识(如 "ZKY", "SQA" 等)
        tags: 标签列表
        paper_link: 论文链接(可选，支持arxiv URL自动提取paper_year)
        title: 论文标题(可选，从md_path文件名或paper标签提取)
        paper_year: 论文年份(可选，如不提供会尝试从arxiv URL提取)
        time: 发布日期(可选，格式为 YYYY-MM-DD，默认为当前日期)
        who_count: 编号(可选，格式为"001"等，不提供则自动递增)
    """
    
    # 获取源markdown文件内容
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"源文件不存在: {md_path}")
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取paper标题（从arxiv、markdown content或文件名）
    paper_title = title
    if not paper_title:
        # 1. 尝试从arxiv URL获取标题（优先级最高）
        if paper_link:
            arxiv_title = get_arxiv_title(paper_link)
            if arxiv_title:
                paper_title = arxiv_title
        
        # 2. 如果arxiv获取失败，尝试从markdown content中提取
        if not paper_title:
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                paper_title = title_match.group(1).strip()
        
        # 3. 最后从文件名提取
        if not paper_title:
            paper_title = os.path.splitext(os.path.basename(md_path))[0]
    
    # 尝试从arxiv URL提取paper_year
    if not paper_year and paper_link:
        try:
            extracted_year = extract_arxiv_year(paper_link)
            if extracted_year:
                paper_year = extracted_year
        except ValueError:
            pass  # 如果提取失败则继续，paper_year可以为None
    
    # 获取发布时间
    if time:
        publish_date = time
    else:
        publish_date = datetime.now().strftime("%Y-%m-%d")
        _print_info(f"No time provided, using current date: {publish_date}")
    
    # 获取下一个编号
    posts_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "_posts"
    )
    
    # 确定编号
    if who_count:
        # 使用手动指定的编号
        number_str = who_count  # 格式: "001"
        number = int(who_count)
    else:
        # 自动生成下一个编号
        number = get_next_number(posts_dir, who)
        number_str = f"{number:03d}"
    
    # 生成两种格式的ID
    post_id_filename = f"{who}{number_str}"  # 用于post文件名：ZKY001
    post_id_display = f"{who}-{number_str}"  # 用于frontmatter和papers目录：ZKY-001
    
    # 生成post文件名
    post_filename = f"{publish_date}-{post_id_filename}.md"
    _print_info(f"Generated post filename: {post_filename}")
    
    post_path = os.path.join(posts_dir, post_filename)
    
    # 处理图片: 提取并复制markdown中的本地图片
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    papers_dir = os.path.join(repo_root, "papers")
    post_images_dir = os.path.join(papers_dir, post_id_display)
    
    # 复制图片并更新内容
    processed_content = copy_images(content, md_path, post_images_dir, post_id_display)
    # Replace pipes inside math blocks and validate overall format
    processed_content, format_errors = check_format(os.path.basename(md_path), processed_content)
    if format_errors:
        for e in format_errors:
            _print_warning(e)
        raise ValueError("Invalid '|' characters found in markdown. See warnings above.")
    
    # 生成frontmatter
    frontmatter = generate_frontmatter(
        title=post_id_display,
        paper=paper_title,
        paper_url=paper_link,
        paper_year=paper_year,
        tags=tags,
    )
    
    # 合并frontmatter和content
    full_content = frontmatter + "\n" + processed_content
    
    # 保存到_posts目录
    os.makedirs(posts_dir, exist_ok=True)
    with open(post_path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    _print_success(f"Successfully uploaded: {post_path}")
    return post_path


def get_next_number(posts_dir: str, who: str) -> int:
    """
    获取该编辑者的下一个编号
    
    Args:
        posts_dir: _posts目录路径
        who: 编辑者标识
        
    Returns:
        下一个编号（整数）
    """
    if not os.path.exists(posts_dir):
        return 1
    
    # 查找所有该编辑者的post文件
    pattern = rf"\d{{4}}-\d{{2}}-\d{{2}}-{who}(\d{{3}})\.md"
    max_number = 0
    
    for filename in os.listdir(posts_dir):
        match = re.match(pattern, filename)
        if match:
            number = int(match.group(1))
            max_number = max(max_number, number)
    
    return max_number + 1


def generate_frontmatter(
    title: str,
    paper: str = None,
    paper_url: str = None,
    paper_year: str = None,
    tags: list = None,
) -> str:
    """
    生成Jekyll post的frontmatter
    
    Args:
        title: post标题
        paper: 论文标题
        paper_url: 论文链接
        paper_year: 论文年份
        tags: 标签列表
        
    Returns:
        格式化的frontmatter字符串
    """
    lines = ["---"]
    lines.append(f"title: {title}")
    
    if paper:
        lines.append(f'paper: "{paper}"')
    
    if paper_url:
        lines.append(f'paper_url: "{paper_url}"')
    
    if paper_year:
        lines.append(f"paper_year: {paper_year}")
    
    if tags:
        lines.append("tags:")
        for tag in tags:
            lines.append(f'    - "{tag}"')
    
    lines.append("layout: post")
    lines.append("---")
    
    return "\n".join(lines)


def extract_arxiv_year(paper_link: str) -> str:
    """
    从arxiv URL提取论文年份
    
    Args:
        paper_link: 论文链接，如 "https://arxiv.org/pdf/2503.09641"
        
    Returns:
        四位数的年份字符串，如 "2025"，如果格式不符合则抛出ValueError
    """
    # 匹配arxiv ID格式: 25 (两位数表示年份，如 25 = 2025)
    match = re.search(r'/(\d{4})\.(\d{5})', paper_link)
    if not match:
        raise ValueError(
            f"Invalid arxiv URL format: {paper_link}\n"
            f"Expected format like: https://arxiv.org/pdf/YYMM.XXXXX"
        )
    
    arxiv_id = match.group(1)
    # arxiv ID的前两位是年份 (20yymm.xxxxx 或 yymm.xxxxx)
    # 从2007年4月开始使用新格式，前两位直接表示年份: 07 -> 2007, 25 -> 2025
    year_short = int(arxiv_id[:2])
    
    # 转换为四位数年份
    if year_short <= int(str(datetime.now().year)[-2:]):
        # 当前年份的后两位或更早
        full_year = 2000 + year_short
    else:
        # 假设是更早的年份 (处理1990年代的文章)
        full_year = 1900 + year_short
    
    return str(full_year)


def copy_images(
    content: str,
    source_md_path: str,
    target_images_dir: str,
    post_id: str,
) -> str:
    """
    复制markdown中引用的本地图片到papers目录，并更新markdown中的图片路径
    
    Args:
        content: markdown内容
        source_md_path: 源markdown文件的完整路径
        target_images_dir: 目标图片目录路径 (如 /papers/ZKY001/)
        post_id: post ID (如 ZKY001)
        
    Returns:
        更新后的markdown内容，图片路径已改为绝对于papers目录
    """
    source_dir = os.path.dirname(source_md_path)
    os.makedirs(target_images_dir, exist_ok=True)
    
    # 匹配markdown和HTML中的图片引用
    # 格式1: ![alt](path/to/image)
    # 格式2: <img src="path/to/image" ...>
    
    updated_content = content
    
    # 处理markdown格式: ![alt](path)
    md_image_pattern = r'!\[([^\]]*)\]\(([^)]+?)(?:\s+"([^"]+)")?\)'
    
    def replace_md_image(match):
        alt_text = match.group(1)
        image_path = match.group(2)
        
        _print_info(f"Processing markdown image: alt='{alt_text}', path='{image_path}'")
        
        # 只处理本地图片（不以http开头）
        if image_path.startswith('http'):
            return match.group(0)
        
        new_path = copy_and_return_relative_path(
            image_path, source_dir, target_images_dir, post_id
        )
        return f"![{alt_text}]({new_path})"
    
    updated_content = re.sub(md_image_pattern, replace_md_image, updated_content)
    
    # 处理HTML格式: <img src="path" ...>
    html_image_pattern = r'<img\s+src="([^"]+)"'
    
    def replace_html_image(match):
        image_path = match.group(1)
        
        _print_info(f"Processing HTML image: path='{image_path}'")
        
        # 只处理本地图片
        if image_path.startswith('http'):
            return match.group(0)
        
        new_path = copy_and_return_relative_path(
            image_path, source_dir, target_images_dir, post_id
        )
        return f'<img src="{new_path}"'
    
    updated_content = re.sub(html_image_pattern, replace_html_image, updated_content)
    
    return updated_content


def copy_and_return_relative_path(
    image_path: str,
    source_dir: str,
    target_dir: str,
    post_id: str,
) -> str:
    """
    复制单个图片文件并返回绝对路径
    
    Args:
        image_path: 源图片路径（可能是相对或绝对路径）
        source_dir: markdown文件所在目录
        target_dir: 目标图片目录
        post_id: post ID
        
    Returns:
        绝对于博客根目录的图片路径
    """
    # 解析源图片的完整路径
    if os.path.isabs(image_path):
        full_source_path = image_path
    else:
        full_source_path = os.path.normpath(
            os.path.join(source_dir, image_path)
        )
    
    _print_info(f"Resolving image path: '{image_path}'")
    _print_info(f"  source_dir: {source_dir}")
    _print_info(f"  resolved to: {full_source_path}")
    
    if not os.path.exists(full_source_path):
        _print_warning(f"Image not found: {full_source_path}")
        return image_path
    
    # 获取文件名
    filename = os.path.basename(full_source_path)
    
    # 复制文件到target_dir
    target_path = os.path.join(target_dir, filename)
    shutil.copy2(full_source_path, target_path)
    _print_success(f"Copied image: {os.path.basename(full_source_path)} -> {target_path}")
    
    # 返回绝对于博客根目录的路径
    # 格式: /papers/ZKY-001/image.png （post_id包含-)
    relative_path = f"/papers/{post_id}/{filename}"
    return relative_path


def check_format(title: str, content: str):
    """
    Ensure no stray '|' remain in markdown. Replace '|' inside $$...$$ with
    '\\mid' except when they are part of '\\left|' or '\\right|' or
    escaped '\\|'. Return (possibly_modified_content, errors_list).
    """
    errors = []

    def _replace_pipes_in_math(m):
        # 现在 m.group(1) 是起始符号 ($ 或 $$)
        # m.group(2) 是括号内部的公式内容
        delim = m.group(1) 
        inner = m.group(2)
        
        # 你的原有保护逻辑不变
        inner = inner.replace(r"\left|", "__LEFTPIPE__")
        inner = inner.replace(r"\right|", "__RIGHTPIPE__")
        inner = inner.replace(r"\|", "__ESCAPEDPIPE__")
        
        inner = inner.replace('|', r"\mid ")
        
        inner = inner.replace("__LEFTPIPE__", r"\left|")
        inner = inner.replace("__RIGHTPIPE__", r"\right|")
        inner = inner.replace("__ESCAPEDPIPE__", r"\|")
        
        # 动态返回：根据匹配到的是什么边界，就还原什么边界
        return f"{delim}{inner}{delim}"

    # 正则修改：(\${1,2}) 匹配 $ 或 $$ 并存入 group(1)
    # \1 确保结尾和开头一致
    content = re.sub(r"(\${1,2})(.*?)\1", _replace_pipes_in_math, content, flags=re.DOTALL)

    # For checking, remove explicit left/right/escaped pipes so they won't
    # be counted as errors
    check_content = content.replace(r"\left|", "").replace(r"\right|", "").replace(r"\\|", "")

    lines = check_content.split('\n')
    for i, line in enumerate(lines):
        if '|' in line and not (line.strip().startswith('|') and not line.strip().endswith('|')):
            # include surrounding context (2 lines before and after)
            start = max(0, i-2)
            end = min(len(lines), i+3)
            context_lines = []
            for ln in range(start, end):
                prefix = '>' if ln == i else ' '
                context_lines.append(f"{prefix} {ln+1}: {lines[ln]}")
            context_text = '\n'.join(context_lines)
            errors.append(
                f"💩💩Fatal💩💩: File {title}, line {i+1} contains invalid `|`. Context:\n{context_text}\nYou should use `|` properly, see README.md for more information"
            )

    return content, errors


def delete_paper(who: str, who_count: str = None, time: str = None):
    """
    删除已上传的论文笔记
    
    Args:
        who: 编辑者标识(如 "ZKY", "SQA" 等)
        who_count: 编号(如 "001", "002"等)，如不提供则删除最新的
        time: 指定日期(格式"YYYY-MM-DD")，用于精确查找post文件
        
    Returns:
        被删除的文件数
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    posts_dir = os.path.join(repo_root, "_posts")
    papers_dir = os.path.join(repo_root, "papers")
    
    # 确定要删除的post ID
    if who_count:
        post_id_filename = f"{who}{who_count}"
        post_id_display = f"{who}-{who_count}"
    else:
        # 查找该编辑者的最新post
        latest_count = get_latest_number(posts_dir, who)
        if latest_count is None:
            _print_warning(f"No posts found for {who}")
            return 0
        post_id_filename = f"{who}{latest_count:03d}"
        post_id_display = f"{who}-{latest_count:03d}"
    
    # 查找对应的post文件（使用filename格式）
    post_file = None
    for filename in os.listdir(posts_dir):
        if post_id_filename in filename and filename.endswith('.md'):
            post_file = os.path.join(posts_dir, filename)
            break
    
    if not post_file:
        if time:
            # 尝试使用时间戳查找
            pattern = f"{time}-{post_id_filename}.md"
            potential_file = os.path.join(posts_dir, pattern)
            if os.path.exists(potential_file):
                post_file = potential_file
        
        if not post_file:
            _print_warning(f"Post file not found for {post_id_filename}")
            return 0
    
    # 删除post文件
    deleted_count = 0
    try:
        os.remove(post_file)
        _print_success(f"Deleted post: {post_file}")
        deleted_count += 1
    except Exception as e:
        _print_warning(f"Failed to delete post: {e}")
        return 0
    
    # 删除对应的图片目录（使用display格式）
    images_dir = os.path.join(papers_dir, post_id_display)
    if os.path.exists(images_dir):
        try:
            shutil.rmtree(images_dir)
            _print_success(f"Deleted images directory: {images_dir}")
            deleted_count += 1
        except Exception as e:
            _print_warning(f"Failed to delete images directory: {e}")
    
    return deleted_count


def get_latest_number(posts_dir: str, who: str) -> int:
    """
    获取该编辑者的最新编号
    
    Args:
        posts_dir: _posts目录路径
        who: 编辑者标识
        
    Returns:
        最新编号（整数），如果没有则返回None
    """
    if not os.path.exists(posts_dir):
        return None
    
    # 查找所有该编辑者的post文件
    pattern = rf"\d{{4}}-\d{{2}}-\d{{2}}-{who}(\d{{3}})\.md"
    max_number = None
    
    for filename in os.listdir(posts_dir):
        match = re.match(pattern, filename)
        if match:
            number = int(match.group(1))
            if max_number is None or number > max_number:
                max_number = number
    
    return max_number