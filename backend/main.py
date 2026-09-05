from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware

from app.opening import generate_opening_ment
from app.closing import generate_closing_ment
from news.news_radio import run_news_radio
from story.story_radio import run_story_radio
from music.music_radio import run_music_radio

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
    "headline": lambda keyword, language, prev_type, context: run_news_radio(["headline"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "deep":     lambda keyword, language, prev_type, context: run_news_radio(["deep"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "current":  lambda keyword, language, prev_type, context: run_news_radio(["current"], keyword=keyword, language=language, prev_type=prev_type, context=context),

    # 사연
    "story_main":       lambda keyword, language, prev_type, context: run_story_radio(["story_main"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "story_discussion": lambda keyword, language, prev_type, context: run_story_radio(["story_discussion"], keyword=keyword, language=language, prev_type=prev_type, context=context),

    # 음악
    "music_history": lambda keyword, language, prev_type, context: run_music_radio(["music_history"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "music_trend":   lambda keyword, language, prev_type, context: run_music_radio(["music_trend"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "music_genre":   lambda keyword, language, prev_type, context: run_music_radio(["music_genre"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "music_artist":  lambda keyword, language, prev_type, context: run_music_radio(["music_artist"], keyword=keyword, language=language, prev_type=prev_type, context=context),
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
