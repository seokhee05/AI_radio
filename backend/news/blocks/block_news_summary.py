from news.crawl_kbs_program_news import extract_article_body
from news.llm.summarizer import summarize_article

def block_news_summary(date_text, head_line_news, prev_type=None, context=None, language="ko") -> str:
    output_lines = []
    output_lines.append(f"🗓️ {date_text}\n")
    output_lines.append("🌟 오늘의 헤드라인 뉴스입니다.")

    for idx, news in enumerate(head_line_news):
        title, url = news["title"], news["url"]
        #output_lines.append(f"📰 ({idx+1}) {title}")

        body = extract_article_body(url)
        if not body:
            output_lines.append("⚠️ 본문 없음\n")
            continue

        result = summarize_article(
            body,
            mode="headline",
            prev_type=prev_type,
            context=context,
            block_name="HEADLINE_NEWS",
            language=language
        )

        if result["success"]:
            # 한 뉴스당 5분 분량 (700~800자) 확보
            output_lines.append(result["script"])
        else:
            output_lines.append(f"⚠️ 요약 실패: {result['error']}\n")
    
    return "\n".join(output_lines)