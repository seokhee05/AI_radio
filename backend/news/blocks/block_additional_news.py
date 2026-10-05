import requests
from bs4 import BeautifulSoup
from news.crawl_kbs_program_news import extract_article_body
from news.llm.summarizer import summarize_article

def block_additional_news(current_news, prev_type=None, context=None, language="ko"):
    output_lines = []
    selected = []
    
    # 1. 키워드 검색 없이, KBS 로컬(부산) 뉴스 URL에서 직접 크롤링
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        # KBS 뉴스 '부산' 지역 카테고리 URL (실제 운영되는 KBS 부산 뉴스 페이지 주소로 변경 가능)
        kbs_busan_url = "https://news.kbs.co.kr/news/pc/category/category.do?icd=2021-0004"
        
        response = requests.get(kbs_busan_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # KBS 웹페이지 구조에 맞춰 기사 제목과 링크가 있는 <a> 태그를 찾음
        # (웹페이지 디자인에 따라 '.box-news a' 등 클래스명은 변경될 수 있습니다)
        articles = soup.select('a.news-link') 
        
        for article in articles:
            href = article.get('href', '')
            title = article.text.strip()
            
            # 유효한 기사 링크와 제목이 있는지 확인하고 리스트에 추가
            if href and title:
                # 상대 경로로 되어 있을 경우를 대비해 절대 경로로 변환
                if href.startswith('/'):
                    href = f"https://news.kbs.co.kr{href}"
                    
                selected.append({
                    "title": title,
                    "url": href
                })
                
            # 3개만 추출하면 반복문 종료
            if len(selected) >= 3:
                break
                
    except Exception as e:
        return f"⚠️ 지역 뉴스 크롤링 실패: {e}\n"

    # 뉴스를 하나도 못 가져왔을 경우
    if not selected:
        return "현재 새롭게 들어온 부산 지역 주요 소식이 없습니다.\n"

    # 2. 추출한 뉴스로 기존처럼 본문 추출 및 요약 진행
    for idx, news in enumerate(selected):
        title, url = news["title"], news["url"]
        
        # url이 정상적인 KBS 링크이므로 기존 함수 그대로 사용 가능
        body = extract_article_body(url)
        
        if not body:
            output_lines.append("⚠️ 본문 없음\n")
            continue

        local_context = (
            context or 
            "부산 시민들에게 필요한 생활 밀착형 정보, 교통, 날씨, 지역 이슈 위주로 자연스럽고 친근한 뉴스 톤으로 요약해 줘."
        )

        result = summarize_article(
            body,
            mode="current",
            prev_type=prev_type,
            context=local_context,
            block_name="ADDITIONAL_NEWS",
            language=language
        )
        
        if result["success"]:
            output_lines.append(result["script"])
        else:
            output_lines.append(f"⚠️ 요약 실패: {result['error']}\n")

    return "\n".join(output_lines)