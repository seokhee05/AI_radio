import os
import re
import time
import requests
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

BASE_URL = "https://news.kbs.co.kr"
PROGRAM_URL = f"{BASE_URL}/news/pc/program/program.do?bcd=0001&ref=pGnb"

# 공통: 셀레니움 드라이버 초기화
def init_headless_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    service = Service(log_path=os.devnull)
    return webdriver.Chrome(service=service, options=options)

# 뉴스 날짜 추출
def extract_date_from_html(soup) -> str:
    try:
        date_tag = soup.select_one("div.datepicker-wrapper span.date")
        day_tag = soup.select_one("div.datepicker-wrapper span.day")
        if not date_tag or not day_tag:
            return None
        year, month, day = map(int, date_tag.text.strip().split('.'))
        return f"{year}년 {month}월 {day}일 {day_tag.text.strip()}"
    except:
        return None

# 뉴스 항목 파싱
def parse_news_items(container, selector="a.box-content", exclude_title_keywords=None):
    if exclude_title_keywords is None:
        exclude_title_keywords = []

    items = []
    for a in container.select(selector):
        title_tag = a.select_one("p.title")
        category_tag = a.select_one("span.field")
        writer_tag = a.select_one("span.writer")
        url = urljoin(BASE_URL, a.get("href"))

        if not title_tag:
            continue

        title = title_tag.text.strip()
        if any(keyword in title for keyword in exclude_title_keywords):
            continue

        items.append({
            "title": title_tag.text.strip(),
            "category": category_tag.text.strip() if category_tag else "",
            "writer": writer_tag.text.strip() if writer_tag else "",
            "url": url,
        })
    return items

def search_kbs_news_by_keyword(keyword: str, max_count: int = 8):
    driver = init_headless_driver()
    encoded_kw = quote(keyword)
    search_url = f"https://news.kbs.co.kr/search/search.do?query={encoded_kw}"
    
    items = []
    try:
        driver.get(search_url)
        time.sleep(2.5)  # 검색 결과 로딩 대기
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 1. 사이드바나 헤더의 '많이 본 뉴스'를 제외하고 실제 검색 결과 컨테이너만 지정
        search_container = (
            soup.select_one("div.search-result") or 
            soup.select_one("div#search-result") or 
            soup.select_one("div.contents-wrap") or
            soup.select_one("div#container") or
            soup
        )
        
        # 2. 검색 목록 내부의 뉴스 카드 탐색
        cards = search_container.find_all("a", href=lambda href: href and "view.do" in href)
        
        seen_urls = set()
        for a in cards:
            href = a.get("href")
            full_url = urljoin(BASE_URL, href)
            
            # 중복 링크 제거
            if full_url in seen_urls:
                continue
                
            raw_text = a.get_text(strip=True)
            
            # 너무 짧거나 무관한 헤더 메뉴 텍스트 제외
            if len(raw_text) < 10:
                continue
                
            # '인기뉴스', '추천', '댓글순' 같은 사이드바 위젯 텍스트 방어
            if any(bad_word in raw_text for bad_word in ["로그인", "제보", "라이브", "다시보기", "날씨"]):
                continue

            items.append({
                "title": raw_text,
                "url": full_url,
                "category": keyword,
                "writer": ""
            })
            seen_urls.add(full_url)
            
            if len(items) >= max_count:
                break

    except Exception as e:
        print(f"DEBUG: 뉴스 검색 에러: {e}")
    finally:
        driver.quit()
        
    print(f"DEBUG: '{keyword}' 필터링 완료된 기사 수: {len(items)}건")
    for idx, item in enumerate(items):
        print(f"  [{idx+1}] {item['title'][:30]}... ({item['url']})")

    return items

# [수정된 함수] keyword 인자를 받도록 변경
def crawl_kbs_program_news(keyword: str = None):
    # 1. 키워드가 없는 경우: 기존 9시 뉴스 크롤링
    if not keyword:
        driver = init_headless_driver()
        driver.get(PROGRAM_URL)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        broadcast_date = extract_date_from_html(soup)

        deep_section = soup.select_one("div.main-news-wrapper")
        deep_news = parse_news_items(deep_section, selector="a.main-news") if deep_section else []

        headline_section = soup.select_one("div.box-contents div.box-contents.has-wrap")
        head_line_news = parse_news_items(headline_section, selector="a.box-content") if headline_section else []

        current_section = soup.select_one("div.main-current-event-box div.box-contents.has-wrap")
        exclude_keywords = ["오프닝", "클로징", "헤드라인"] 
        current_news = parse_news_items(current_section, exclude_title_keywords=exclude_keywords) if current_section else []

        all_titles = set(n["title"] for n in (deep_news + head_line_news))
        current_news = [news for news in current_news if news["title"] not in all_titles]

        return broadcast_date, deep_news, head_line_news, current_news

    # 2. 키워드가 있는 경우: 키워드 검색 기반으로 분기
    keyword_news = search_kbs_news_by_keyword(keyword, max_count=10)
    
    deep_news = keyword_news[:2]
    head_line_news = keyword_news[2:7]
    current_news = keyword_news[7:]
    broadcast_date = f"'{keyword}' 관련 최신 이슈"

    return broadcast_date, deep_news, head_line_news, current_news

# 기사 본문 크롤링
def extract_article_body(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        paragraphs = soup.select("div#cont_newstext p.text")
        if not paragraphs:
            paragraphs = soup.select("div#cont_newstext")
            
        full_text = "\n".join(p.text.strip() for p in paragraphs if p.text.strip())
        
        # 🧹 기자 바이라인 및 방송 멘트 제거 정규식
        # 1. "KBS 뉴스 OOO입니다." 형태 제거
        full_text = re.sub(r"KBS\s*뉴스\s+[가-힣]{2,4}\s*입니다\.?", "", full_text)
        # 2. "[리포트]", "[앵커멘트]" 등 괄호 태그 제거
        full_text = re.sub(r"\[[가-힣\s]+\]", "", full_text)
        # 3. 기자 크레딧 ("OOO 기자", "영상편집: OOO" 등) 이후 내용 절삭
        full_text = re.sub(r"[가-힣]{2,4}\s*기자\s*.*", "", full_text, flags=re.DOTALL)
        full_text = re.sub(r"영상취재.*|영상편집.*|그래픽.*", "", full_text, flags=re.DOTALL)

        return full_text.strip()
    except Exception as e:
        print(f"본문 크롤링 실패 ({url}): {e}")
        return ""