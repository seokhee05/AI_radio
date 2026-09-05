from news.crawl_kbs_program_news import extract_article_body
from news.llm.summarizer import summarize_article

def block_additional_news(current_news, prev_type=None, context=None, language="ko"):
    # 국제/경제/문화 기사만 필터링
    filtered = [n for n in current_news if n["category"] in ["국제", "경제", "문화"]]
    selected = filtered[:3]  # 최대 3개만 사용

    output_lines = []
    #output_lines.append("🌍 추가 뉴스 (국제/경제/문화)")

    for idx, news in enumerate(selected):
        title, url = news["title"], news["url"]
        #output_lines.append(f"📰 ({idx+1}) {title}")

        body = extract_article_body(url)
        if not body:
            output_lines.append("⚠️ 본문 없음\n")
            continue

        # 짧은 뉴스니까 current 모드 (300~400자)
        result = summarize_article(
            body,
            mode="current",  # 짧은 뉴스니까 current 모드
            prev_type=prev_type,
            context=context,
            block_name="ADDITIONAL_NEWS",
            language=language
        )
        if result["success"]:
            output_lines.append(result["script"])
        else:
            output_lines.append(f"⚠️ 요약 실패: {result['error']}\n")

    return "\n".join(output_lines)
