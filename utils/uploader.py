import upload_file_main

if __name__ == "__main__":
    # 上传论文笔记
    # title参数现在是可选的，支持以下三种获取方式（按优先级）：
    # 1. 直接提供 title="..." 参数
    # 2. 从arxiv URL自动获取（需要有paper_link且arxiv包已安装）
    # 3. 从markdown内容中的第一个#标题提取
    # 4. 从markdown文件名提取
    
    upload_file_main.upload_paper(
        md_path="D:/Desktop/texts/笔记/算法/T2I_Papers.md",
        # title="SANA-Sprint...",  # 可选：提供标题，会覆盖自动获取
        paper_link="https://arxiv.org/pdf/2503.09641",  # arxiv URL，用于自动提取title和paper_year
        who="ZKY",
        tags=["MultiModal", "Diffusion"],
        # who_count="001",        # 可选：手动指定编号（格式"001"）
        # paper_year="2025",      # 可选：自动从arxiv URL提取，如需覆盖可指定
        # time="2026-01-09",      # 可选：自定义发布日期
    )
    
    # 删除论文笔记（可选）
    #upload_file_main.delete_paper(who="ZKY", who_count="002")