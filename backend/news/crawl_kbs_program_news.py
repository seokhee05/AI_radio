from datetime import datetime
import os
import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from urllib.parse import quote, urljoin

BASE_URL = "https://news.kbs.co.kr"
PROGRAM_URL = f"{BASE_URL}/news/pc/program/program.do?bcd=0001&ref=pGnb"


# 공통: 셀레니움 드라이버 초기화
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


# [수정] 메인 페이지용 날짜 생성 (None 방지 및 오늘 날짜 반환)
def extract_date_from_html(soup) -> str:
    # 실시간 메인 페이지는 날짜 컴포넌트가 없으므로 오늘 날짜를 직접 포맷팅해서 반환
    now = datetime.now()
    # 요일 구하기 (월, 화, 수...)
    days = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    day_str = days[now.weekday()]
    return f"{now.year}년 {now.month}월 {now.day}일 {day_str}"


# 뉴스 항목 파싱
def parse_news_items(
    container, selector="a.box-content", exclude_title_keywords=None
):
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


# 심층 뉴스를 위한 키워드 검색 함수
def search_kbs_news_by_keyword(keyword: str, max_count: int = 3):
    driver = init_headless_driver()
    encoded_kw = quote(keyword)
    search_url = f"https://news.kbs.co.kr/search/search.do?query={encoded_kw}"

    items = []
    try:
        driver.get(search_url)
        time.sleep(2.5)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        search_container = (
            soup.select_one("div.search-result")
            or soup.select_one("div#search-result")
            or soup.select_one("div.contents-wrap")
            or soup.select_one("div#container")
            or soup
        )

        cards = search_container.find_all(
            "a", href=lambda href: href and "view.do" in href
        )

        seen_urls = set()
        for a in cards:
            href = a.get("href")
            full_url = urljoin(BASE_URL, href)

            if full_url in seen_urls:
                continue

            raw_text = a.get_text(strip=True)

            if len(raw_text) < 10:
                continue

            if any(
                bad_word in raw_text
                for bad_word in ["로그인", "제보", "라이브", "다시보기", "날씨"]
            ):
                continue

            if "[영상]" in raw_text or "[포토]" in raw_text:
                continue

            keywords = keyword.split()
            if not any(kw in raw_text for kw in keywords):
                continue

            items.append({
                "title": raw_text,
                "url": full_url,
                "category": keyword,
                "writer": "",
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


# 실시간 메인 페이지 크롤링 함수
def crawl_kbs_program_news(keyword: str = None):
    driver = init_headless_driver()
    driver.get(PROGRAM_URL)
    time.sleep(2.5)  # 메인 페이지 로딩 대기 시간 살짝 여유
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    broadcast_date = extract_date_from_html(soup)

    # 메인 페이지 구조에 맞는 셀렉터 지정 (필요에 따라 메인 페이지 HTML 구조에 맞춰 조정)
    # 보통 메인 페이지는 주요 뉴스가 담긴 wrapper가 다를 수 있어 기본 셀렉터 실패 시 대비
    headline_section = soup.select_one(
        "div.box-contents div.box-contents.has-wrap"
    ) or soup.select_one("div.contents-wrap")
    head_line_news = (
        parse_news_items(headline_section, selector="a.box-content")
        if headline_section
        else []
    )

    current_section = soup.select_one(
        "div.main-current-event-box div.box-contents.has-wrap"
    ) or soup.select_one("div.timeline-box")
    exclude_keywords = ["오프닝", "클로징", "헤드라인"]
    current_news = (
        parse_news_items(current_section, exclude_title_keywords=exclude_keywords)
        if current_section
        else []
    )

    # 심층 뉴스 분기 처리
    if keyword and keyword.strip():
        deep_news = search_kbs_news_by_keyword(keyword.strip(), max_count=3)
        if broadcast_date:
            broadcast_date = f"{broadcast_date} ('{keyword}' 집중 분석)"
        else:
            broadcast_date = f"'{keyword}' 집중 분석"
    else:
        deep_section = soup.select_one(
            "div.main-news-wrapper"
        ) or soup.select_one("div.box-list")
        deep_news = (
            parse_news_items(deep_section, selector="a.main-news, a.box-content")
            if deep_section
            else []
        )

    # 만약 메인 페이지 구조상 위 셀렉터로 기사를 못 긁어왔을 때의 안전 장치 (상위 a 태그들 수집)
    if not head_line_news and not deep_news:
        fallback_cards = parse_news_items(soup, selector="a.box-content")
        if fallback_cards:
            head_line_news = fallback_cards[:3]
            current_news = fallback_cards[3:8]

    # 중복 제거 로직
    all_titles = set(n["title"] for n in (deep_news + head_line_news))
    current_news = [
        news for news in current_news if news["title"] not in all_titles
    ]

    return broadcast_date, deep_news, head_line_news, current_news


# 기사 본문 크롤링
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