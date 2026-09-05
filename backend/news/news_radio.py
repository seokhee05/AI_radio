from news.crawl_kbs_program_news import crawl_kbs_program_news
from news.blocks.block_news_summary import block_news_summary
from news.blocks.block_deep_news import block_deep_news
from news.blocks.block_additional_news import block_additional_news

def run_news_radio(blocks: list[str], keyword: str = None, prev_type=None, context=None, language: str = "ko") -> str:
    output_lines = []

    # 🗓️ 뉴스 크롤링 (한 번만 실행)
    date_text, deep_news, head_line_news, current_news = crawl_kbs_program_news()

    for b in blocks:
        if b == "headline":
            text = block_news_summary(date_text, head_line_news, prev_type, context, language)
        elif b == "deep":
            text = block_deep_news(date_text, deep_news, prev_type, context, language)
        elif b == "current":
            text = block_additional_news(current_news, prev_type, context, language)
        else:
            text = f"[{b}] 블럭은 아직 구현되지 않았습니다."

        output_lines.append(text)

        prev_type = b
        context = text[-400:]

    return "\n\n".join(output_lines)

