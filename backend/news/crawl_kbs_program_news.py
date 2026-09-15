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
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
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

# 심층 뉴스를 위한 키워드 검색 함수 (살려둠!)
def search_kbs_news_by_keyword(keyword: str, max_count: int = 3):
    driver = init_headless_driver()
    encoded_kw = quote(keyword)
    search_url = f"https://news.kbs.co.kr/search/search.do?query={encoded_kw}"
    
    items = []
    try:
        driver.get(search_url)
        time.sleep(2.5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        search_container = (
            soup.select_one("div.search-result") or 
            soup.select_one("div#search-result") or 
            soup.select_one("div.contents-wrap") or
            soup.select_one("div#container") or
            soup
        )
        
        cards = search_container.find_all("a", href=lambda href: href and "view.do" in href)
        
        seen_urls = set()
        for a in cards:
            href = a.get("href")
            full_url = urljoin(BASE_URL, href)
            
            if full_url in seen_urls:
                continue
                
            raw_text = a.get_text(strip=True)
            
            if len(raw_text) < 10:
                continue
                
            if any(bad_word in raw_text for bad_word in ["로그인", "제보", "라이브", "다시보기", "날씨"]):
                continue
                
            if "[영상]" in raw_text or "[포토]" in raw_text:
                continue

            # ★ [핵심 추가] 제목에 입력한 키워드가 실제로 포함된 기사만 통과시키기
            keywords = keyword.split()
            if not any(kw in raw_text for kw in keywords):
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
        
    print(f"DEBUG: '{keyword}' 키워드로 필터링된 심층 기사 {len(items)}건 수집 완료")
    return items

# [하이브리드 함수] 헤드라인/일반은 고정, 심층만 키워드 적용
def crawl_kbs_program_news(keyword: str = None):
    # 1. 무조건 9시 뉴스 페이지를 열어서 기본 뼈대(헤드라인, 일반 뉴스)를 가져옴
    driver = init_headless_driver()
    driver.get(PROGRAM_URL)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    broadcast_date = extract_date_from_html(soup)

    # 2. 헤드라인 및 일반(추가) 뉴스는 항상 고정으로 파싱
    headline_section = soup.select_one("div.box-contents div.box-contents.has-wrap")
    head_line_news = parse_news_items(headline_section, selector="a.box-content") if headline_section else []

    current_section = soup.select_one("div.main-current-event-box div.box-contents.has-wrap")
    exclude_keywords = ["오프닝", "클로징", "헤드라인"] 
    current_news = parse_news_items(current_section, exclude_title_keywords=exclude_keywords) if current_section else []

    # 3. 심층 뉴스 분기 처리 (키워드가 있으면 키워드 검색 결과로 교체, 없으면 기본 9시 뉴스 심층 기사)
    if keyword and keyword.strip():
        deep_news = search_kbs_news_by_keyword(keyword.strip(), max_count=3)
        if broadcast_date:
            broadcast_date = f"{broadcast_date} ('{keyword}' 집중 분석)"
        else:
            broadcast_date = f"'{keyword}' 집중 분석"
    else:
        deep_section = soup.select_one("div.main-news-wrapper")
        deep_news = parse_news_items(deep_section, selector="a.main-news") if deep_section else []

    # 4. 중복 제거 로직
    all_titles = set(n["title"] for n in (deep_news + head_line_news))
    current_news = [news for news in current_news if news["title"] not in all_titles]

    return broadcast_date, deep_news, head_line_news, current_news

# 기사 본문 크롤링
def extract_article_body(url: str) -> str:
    driver = init_headless_driver()
    try:
        driver.get(url)
        time.sleep(1.5) 
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        body_container = soup.select_one("div#cont_newstext") or soup.select_one("div.detail-body")
        
        if not body_container:
            return ""
            
        full_text = body_container.get_text(separator="\n", strip=True)
        
        # 🧹 기자 바이라인 및 방송 멘트 제거 정규식
        full_text = re.sub(r"KBS\s*뉴스\s+[가-힣]{2,4}\s*입니다\.?", "", full_text)
        full_text = re.sub(r"\[[가-힣\s]+\]", "", full_text)
        full_text = re.sub(r"[가-힣]{2,4}\s*기자\s*.*", "", full_text, flags=re.DOTALL)
        full_text = re.sub(r"영상취재.*|영상편집.*|그래픽.*", "", full_text, flags=re.DOTALL)

        return full_text.strip()
    except Exception as e:
        print(f"본문 크롤링 실패 ({url}): {e}")
        return ""
    finally:
        driver.quit()