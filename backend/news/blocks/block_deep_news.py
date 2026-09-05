from news.crawl_kbs_program_news import extract_article_body
from news.llm.summarizer import summarize_article
from common.prompt_utils import build_block_prompt

def block_deep_news(date_text, deep_news, prev_type=None, context=None, language="ko") -> str:
    output_lines = []

    if language == "ko":
        output_lines.append("오늘의 심층 뉴스입니다.")
    else:
        output_lines.append("Here is today’s deep dive news.")

    for idx, news in enumerate(deep_news):
        title, url = news["title"], news["url"]
        #output_lines.append(f"({idx+1}) {title}")

        body = extract_article_body(url)
        if not body:
            output_lines.append("⚠️ 본문 없음\n")
            continue

        result = summarize_article(
            body, 
            mode="deep",
            prev_type=prev_type,
            context=context,
            block_name="DEEP_NEWS",
            language=language
        )  # 10~15분 분량 (1500~2000자)
        
        if result["success"]:
            output_lines.append(result["script"])
        else:
            output_lines.append(f"⚠️ 요약 실패: {result['error']}\n")

    return "\n".join(output_lines)
