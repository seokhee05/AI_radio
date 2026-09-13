from news.crawl_kbs_program_news import extract_article_body
from news.llm.summarizer import summarize_article

def block_news_summary(date_text: str, head_line_news: list, prev_type=None, context=None, language="ko") -> str:
    output_lines = []
    
    # 1. 깔끔한 단일 오프닝 멘트
    intro_ment = f"지금 시각 주요 뉴스입니다. {date_text} 헤드라인 브리핑을 전해드립니다."
    output_lines.append(intro_ment)

    # 기사 간 자연스러운 호흡 연결을 위한 컨텍스트
    current_context = intro_ment

    for idx, news in enumerate(head_line_news):
        title, url = news.get("title", ""), news.get("url", "")
        
        body = extract_article_body(url)
        if not body:
            body = title

        # 첫 번째 기사는 이미 인트로가 있으므로 전환 멘트를 붙이지 않음 (prev_type=None)
        item_prev_type = None if idx == 0 else "headline_item"

        result = summarize_article(
            body,
            mode="headline",
            prev_type=item_prev_type,
            context=current_context,
            block_name="HEADLINE_NEWS",
            language=language
        )

        if result.get("success"):
            script_text = result["script"]
            output_lines.append(script_text)
            current_context = script_text[-250:]
        else:
            output_lines.append(f"⚠️ 요약 실패: {result.get('error')}")

    return "\n\n".join(output_lines)