import os
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.closing import generate_closing_ment
from app.opening import generate_opening_ment
from music.music_radio import run_music_radio
from news.news_radio import run_news_radio
from story.story_radio import run_story_radio
from traffic.traffic_radio import run_traffic_radio
from news.blocks.block_additional_news import block_additional_news

# 💡 TTS URL 유틸리티 임포트
from common.tts_utils import generate_tts_url

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# audio_files 디렉토리 생성 및 /static 정적 파일 마운트
os.makedirs("audio_files", exist_ok=True)
app.mount("/static", StaticFiles(directory="audio_files"), name="static")

# 블록 매핑
BLOCK_HANDLERS = {
    # 뉴스
    "headline": lambda keyword, language, prev_type, context: run_news_radio(
        ["headline"], keyword=keyword, language=language, prev_type=prev_type, context=context
    ),
    "deep": lambda keyword, language, prev_type, context: run_news_radio(
        ["deep"], keyword=keyword, language=language, prev_type=prev_type, context=context
    ),
    "busan": lambda keyword, language, prev_type, context: block_additional_news(
        current_news=keyword, prev_type=prev_type, context=context, language=language
    ),
    # 사연
    "story_main": lambda keyword, language, prev_type, context: run_story_radio(
        ["story_main"], keyword=keyword, language=language, prev_type=prev_type, context=context
    ),
    "story_discussion": lambda keyword, language, prev_type, context: run_story_radio(
        ["story_discussion"], keyword=keyword, language=language, prev_type=prev_type, context=context
    ),
    # 음악
    "music_history": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_history"], keyword=keyword, language=language, prev_type=prev_type, context=context
    ),
    "music_trend": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_trend"], keyword=keyword, language=language, prev_type=prev_type, context=context
    ),
    "music_genre": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_genre"], keyword=keyword, language=language, prev_type=prev_type, context=context
    ),
    "music_story": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_story"], keyword=keyword, language=language, prev_type=prev_type, context=context
    ),
    "music_artist": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_artist"], keyword=keyword, language=language, prev_type=prev_type, context=context
    ),
    "traffic": lambda keyword, language, prev_type, context: run_traffic_radio(
        ["traffic"], keyword=keyword, language=language, prev_type=prev_type, context=context
    ),
}

# 코너별 전담 성우 매핑
BLOCK_SPEAKER_MAP = {
    "headline": "vdaeseong",
    "deep": "vdaeseong",
    "busan": "vdaeseong",
    "story_main": "noyj",
    "music_trend": "vgoeun",
    "music_story": "vgoeun",
    "music_artist": "vgoeun",
    "traffic": "vdonghyun",
}


@app.post("/api/run-radio")
def run_radio(selected: dict = Body(...)):
    print(f"1. [DEBUG] 전달받은 전체 JSON payload: {selected}")
    
    blocks = selected.get("blocks", [])
    keyword = selected.get("keyword", None)
    language = selected.get("language", "ko")
    
    print(f"2. [DEBUG] 추출된 blocks 리스트: {blocks}")

    # 💡 메인 코너의 성우 결정 (기본값: vdaeseong)
    # 선택된 블록들 중 첫 번째 블록의 성우를 찾고, 없으면 대성(vdaeseong)으로 설정
    main_speaker = "vdaeseong"
    for block in blocks:
        if block in BLOCK_SPEAKER_MAP:
            main_speaker = BLOCK_SPEAKER_MAP[block]
            break

    print(f"🎙️ [DEBUG] 이번 방송 메인 성우: {main_speaker}")

    raw_scripts = []
    prev_type, context = None, ""

    # 1. 오프닝 멘트 생성 (메인 성우 적용)
    try:
        opening = generate_opening_ment(keyword, language=language)
        print("3. [DEBUG] 오프닝 생성 성공")
        raw_scripts.append({"type": "opening", "content": opening, "speaker": main_speaker})
        prev_type, context = "opening", opening[-400:] if opening else ""
    except Exception as e:
        print(f"❌ [ERROR] 오프닝 생성 오류: {e}")

    # 2. 선택된 블록 실행
    for block in blocks:
        print(f"4. [DEBUG] 현재 실행 시도 중인 블록: {block}")
        
        if block not in BLOCK_HANDLERS:
            print(f"⚠️ [WARNING] BLOCK_HANDLERS에 {block} 없음")
            continue

        try:
            content = BLOCK_HANDLERS[block](keyword, language, prev_type, context)
            print(f"5. [DEBUG] {block} 내용 생성 결과 (앞 50자): {str(content)[:50]}...")
            
            speaker = BLOCK_SPEAKER_MAP.get(block, main_speaker)
            raw_scripts.append({"type": block, "content": content, "speaker": speaker})
            prev_type, context = block, content[-400:] if content else ""
        except Exception as e:
            print(f"❌ [ERROR] {block} 블록 실행 중 에러 터짐: {e}")

    # 3. 클로징 멘트 생성 (메인 성우 적용)
    try:
        closing = generate_closing_ment(keyword, language=language)
        print("6. [DEBUG] 클로징 생성 성공")
        raw_scripts.append({"type": "closing", "content": closing, "speaker": main_speaker})
    except Exception as e:
        print(f"❌ [ERROR] 클로징 생성 오류: {e}")

    # 4. MP3 오디오 파일 생성 및 정적 URL 경로 구성
    final_scripts = []
    for item in raw_scripts:
        script_type = item["type"]
        script_content = item.get("content", "")
        script_speaker = item.get("speaker", main_speaker)

        if not script_content:
            print(f"⚠️ [WARNING] {script_type} 의 content가 비어있어 TTS를 건너뜁니다.")
            continue

        print(f"7. [DEBUG] {script_type} TTS mp3 생성 시작 (성우: {script_speaker})")
        
        # 성우에 맞춰 MP3 파일 생성
        audio_url = generate_tts_url(text=script_content, speaker=script_speaker)

        final_scripts.append({
            "type": script_type,
            "content": script_content,
            "audio_url": audio_url
        })

    print(f"8. [DEBUG] 최종 전달될 scripts 개수: {len(final_scripts)}")
    return {"scripts": final_scripts}