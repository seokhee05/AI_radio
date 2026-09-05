from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
import os

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

# 뉴스 크롤링
def crawl_kbs_program_news():
    driver = init_headless_driver()
    driver.get(PROGRAM_URL)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # 날짜
    broadcast_date = extract_date_from_html(soup)

    # 주요뉴스(심층 뉴스용) - main-news-wrapper
    deep_section = soup.select_one("div.main-news-wrapper")
    deep_news = parse_news_items(deep_section, selector="a.main-news") if deep_section else []

    # 헤드라인 뉴스 - box-contents has-wrap
    headline_section = soup.select_one("div.box-contents div.box-contents.has-wrap")
    head_line_news = parse_news_items(headline_section, selector="a.box-content") if headline_section else []

    # current news (기존 나머지 뉴스들)
    current_section = soup.select_one("div.main-current-event-box div.box-contents.has-wrap")
    exclude_keywords = ["오프닝", "클로징", "헤드라인"] 
    current_news = parse_news_items(current_section, exclude_title_keywords=exclude_keywords) if current_section else []

    # 중복 제거
    all_titles = set(n["title"] for n in (deep_news + head_line_news))
    current_news = [news for news in current_news if news["title"] not in all_titles]

    return broadcast_date, deep_news, head_line_news, current_news

# 기사 본문 크롤링
def extract_article_body(url: str) -> str:
    driver = init_headless_driver()
    driver.get(url)
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    paragraphs = soup.select("div#cont_newstext p.text")  # 실제 기사 본문

    if not paragraphs:
        return ""

    full_text = "\n".join(p.text.strip() for p in paragraphs if p.text.strip())
    return full_text

# 실행
if __name__ == "__main__":
    broadcast_date, head_line_news, current_news = crawl_kbs_program_news()
    print(f"\n🗓️ 오늘은 {broadcast_date}\n")

    print("🌟 주요 뉴스 (head-line)")
    for n in head_line_news:
        print(f"📰 {n['title']} [{n['category']}] - {n['writer']}")

    print("\n📺 오늘 방송 뉴스 (current)")
    for n in current_news:
        print(f"📰 {n['title']} [{n['category']}] - {n['writer']}")
