from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.closing import generate_closing_ment
from app.opening import generate_opening_ment
from music.music_radio import run_music_radio
from news.news_radio import run_news_radio
from story.story_radio import run_story_radio
from traffic.traffic_radio import run_traffic_radio  # 💡 교통 모듈 임포트 추가
from news.blocks.block_additional_news import block_additional_news

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 블록 매핑
BLOCK_HANDLERS = {
    # 뉴스
    "headline": lambda keyword, language, prev_type, context: run_news_radio(
        ["headline"],
        keyword=keyword,
        language=language,
        prev_type=prev_type,
        context=context,
    ),
    "deep": lambda keyword, language, prev_type, context: run_news_radio(
        ["deep"],
        keyword=keyword,
        language=language,
        prev_type=prev_type,
        context=context,
    ),
    "busan": lambda keyword, language, prev_type, context: block_additional_news(
        current_news=keyword,
        prev_type=prev_type,
        context=context,
        language=language,
    ),
    # 사연
    "story_main": lambda keyword, language, prev_type, context: run_story_radio(
        ["story_main"],
        keyword=keyword,
        language=language,
        prev_type=prev_type,
        context=context,
    ),
    "story_discussion": lambda keyword, language, prev_type, context: run_story_radio(
        ["story_discussion"],
        keyword=keyword,
        language=language,
        prev_type=prev_type,
        context=context,
    ),
    # 음악
    "music_history": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_history"],
        keyword=keyword,
        language=language,
        prev_type=prev_type,
        context=context,
    ),
    "music_trend": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_trend"],
        keyword=keyword,
        language=language,
        prev_type=prev_type,
        context=context,
    ),
    "music_genre": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_genre"],
        keyword=keyword,
        language=language,
        prev_type=prev_type,
        context=context,
    ),
    "music_artist": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_artist"],
        keyword=keyword,
        language=language,
        prev_type=prev_type,
        context=context,
    ),
    "traffic": lambda keyword, language, prev_type, context: run_traffic_radio(
        ["traffic"],
        keyword=keyword,
        language=language,
        prev_type=prev_type,
        context=context,
    ),
}


@app.post("/api/run-radio")
def run_radio(selected: dict = Body(...)):
    blocks = selected.get("blocks", [])
    keyword = selected.get("keyword", None)
    language = selected.get("language", "ko")
    scripts = []

    prev_type, context = None, ""

    # 오프닝
    opening = generate_opening_ment(keyword, language=language)
    scripts.append({"type": "opening", "content": opening})
    prev_type, context = "opening", opening[-400:]

    # 선택된 블록 순서대로 실행
    for block in blocks:
        if block in BLOCK_HANDLERS:
            content = BLOCK_HANDLERS[block](keyword, language, prev_type, context)
        scripts.append({"type": block, "content": content})
        prev_type, context = block, content[-400:]

    # 클로징
    closing = generate_closing_ment(keyword, language=language)
    scripts.append({"type": "closing", "content": closing})

    return {"scripts": scripts}