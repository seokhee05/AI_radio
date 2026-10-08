import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import re

from news.llm.summarizer import summarize_article

BASE_URL = "https://busan.kbs.co.kr"

def init_headless_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    service = Service(log_path=os.devnull)
    return webdriver.Chrome(service=service, options=options)

def extract_article_body(url: str) -> str:
    driver = init_headless_driver()
    try:
        driver.get(url)
        time.sleep(1.5)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        body_container = soup.select_one("div#cont_newstext") or soup.select_one(
            "div.detail-body"
        )

        if not body_container:
            return ""

        full_text = body_container.get_text(separator="\n", strip=True)

        full_text = re.sub(r"KBS\s*뉴스\s+[가-힣]{2,4}\s*입니다\.?", "", full_text)
        full_text = re.sub(r"\[[가-힣\s]+\]", "", full_text)
        full_text = re.sub(r"[가-힣]{2,4}\s*기자\s*.*", "", full_text, flags=re.DOTALL)
        full_text = re.sub(
            r"영상취재.*|영상편집.*|그래픽.*", "", full_text, flags=re.DOTALL
        )

        return full_text.strip()
    except Exception as e:
        print(f"본문 크롤링 실패 ({url}): {e}")
        return ""
    finally:
        driver.quit()

def block_additional_news(current_news, prev_type=None, context=None, language="ko"):
    output_lines = []
    collected_articles = []
    
    driver = init_headless_driver()
    
    try:
        driver.get(BASE_URL)
        time.sleep(4.0)  # 충분한 로딩 대기
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 기사 링크 수집 패턴
        articles = soup.find_all('a', href=re.compile(r'news|view'))
        
        exclude_words = ["기사더보기", "전체메뉴", "KBS뉴스", "로그인", "제보", "날씨", "스포츠", "영상", "포토", "바로가기", "시청자"]
        seen_urls = set()
        
        for article in articles:
            href = article.get('href', '')
            title = article.get_text(strip=True)
            
            if href and title and len(title) > 8:
                if any(word in title for word in exclude_words):
                    continue
                
                if href.startswith('/'):
                    href = f"https://news.kbs.co.kr{href}"
                elif not href.startswith('http'):
                    href = f"https://news.kbs.co.kr/{href}"
                
                if href in seen_urls:
                    continue
                    
                seen_urls.add(href)
                collected_articles.append({
                    "title": title,
                    "url": href
                })
                
            if len(collected_articles) >= 3:
                break
                
    except Exception as e:
        return f"⚠️ 부산 KBS 크롤링 실패: {e}\n"
    finally:
        driver.quit()

    if not collected_articles:
        return "현재 새롭게 들어온 부산 지역 주요 소식이 없습니다.\n"

    for idx, news in enumerate(collected_articles):
        title, url = news["title"], news["url"]
        body = extract_article_body(url)
        
        if not body:
            output_lines.append("⚠️ 본문 없음\n")
            continue

        local_context = (
            context or 
            "부산 시민들에게 필요한 생활 밀착형 정보, 교통, 날씨, 지역 이슈 위주로 핵심만 자연스럽고 친근한 뉴스 톤으로 요약해 줘."
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

    final_output = "\n".join(output_lines)
    if not final_output.strip():
        return "현재 새롭게 들어온 부산 지역 주요 소식이 없습니다.\n"
        
    return final_output