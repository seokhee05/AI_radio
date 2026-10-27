import os
import re
import json
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from openai import OpenAI

from app.closing import generate_closing_ment
from app.opening import generate_opening_ment
from music.music_radio import run_music_radio
from music.blocks.block_music_trend import generate_music_trend
from news.news_radio import run_news_radio
from story.story_radio import run_story_radio
from traffic.traffic_radio import run_traffic_radio
from news.blocks.block_additional_news import block_additional_news
from music.jamendo_api import get_bgm, search_bgm_track
from youtube.youtube_api import search_youtube_music
from common.tts_utils import generate_tts_url

load_dotenv()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
os.makedirs("audio_files", exist_ok=True)
app.mount("/static", StaticFiles(directory="audio_files"), name="static")

BLOCK_HANDLERS = {
    "headline": lambda keyword, language, prev_type, context: run_news_radio(
        ["headline"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "deep": lambda keyword, language, prev_type, context: run_news_radio(
        ["deep"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "busan": lambda keyword, language, prev_type, context: block_additional_news(
        current_news=keyword, prev_type=prev_type, context=context, language=language),
    "story_main": lambda keyword, language, prev_type, context: run_story_radio(
        ["story_main"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "story_discussion": lambda keyword, language, prev_type, context: run_story_radio(
        ["story_discussion"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "music_history": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_history"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "music_trend": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_trend"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "music_genre": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_genre"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "music_story": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_story"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "music_artist": lambda keyword, language, prev_type, context: run_music_radio(
        ["music_artist"], keyword=keyword, language=language, prev_type=prev_type, context=context),
    "traffic": lambda keyword, language, prev_type, context: run_traffic_radio(
        ["traffic"], keyword=keyword, language=language, prev_type=prev_type, context=context),
}

BLOCK_SPEAKER_MAP = {
    "headline": "vdaeseong", "deep": "vdaeseong", "busan": "vdaeseong",
    "story_main": "noyj", "music_trend": "vgoeun", "music_story": "vgoeun",
    "music_artist": "vgoeun", "traffic": "vdonghyun",
}
MUSIC_BLOCKS = {"music_history", "music_genre", "music_story", "music_trend", "music_artist"}


def _norm(value):
    return re.sub(r"[^\w가-힣]", "", unicodedata.normalize("NFKC", str(value or "")).casefold())


def _itunes_has_track(artist, title):
    """기존 음악 트렌드 선곡 외 코너에서 곡 실존 여부 최소 확인."""
    for country in ("KR", "US"):
        params = urlencode({"term": f"{artist} {title}", "media": "music",
                            "entity": "song", "country": country, "limit": 50})
        try:
            req = Request("https://itunes.apple.com/search?" + params,
                          headers={"User-Agent": "AI-Radio/1.0"})
            with urlopen(req, timeout=8) as response:
                tracks = json.load(response).get("results", [])
        except Exception as exc:
            print(f"[MUSIC SONG] iTunes {country} error: {exc}", flush=True)
            continue
        for track in tracks:
            if track.get("kind") != "song":
                continue
            match_title = _norm(track.get("trackName")) == _norm(title)
            real_artist = _norm(track.get("artistName"))
            proposed_artist = _norm(artist)
            match_artist = real_artist == proposed_artist or (
                len(proposed_artist) >= 4 and proposed_artist in real_artist)
            if match_title and match_artist:
                return {"artist": track.get("artistName", artist),
                        "song": track.get("trackName", title)}
    return None


def _extract_song_from_script(content):
    """음악 스토리/아티스트: 대본에 나온 곡 하나만 후보로 추출하고 카탈로그에서 확인."""
    response = OpenAI(api_key=os.getenv("OPENAI_API_KEY")).chat.completions.create(
        model="gpt-4o-mini", temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": (
                "라디오 대본에 아티스트와 제목이 명확히 언급된 실제 노래 한 곡만 고르세요. "
                "애매하면 null을 반환하세요. 오직 {\"artist\":string|null,\"song\":string|null} JSON만 출력하세요.")},
            {"role": "user", "content": content},
        ],
    )
    result = json.loads(response.choices[0].message.content or "{}")
    artist, song = result.get("artist"), result.get("song")
    if not isinstance(artist, str) or not isinstance(song, str):
        return None
    if not artist.strip() or not song.strip() or _norm(song) not in _norm(content):
        return None
    return _itunes_has_track(artist.strip(), song.strip())


def _find_youtube_segment(song):
    """가수+곡명 검색. 동명이곡/커버 등 오선곡을 줄이기 위해 보수적으로 검사."""
    artist, title = song["artist"], song["song"]
    videos = search_youtube_music(artist, title)
    safe = []
    for video in videos:
        name = str(video.get("title", ""))
        channel = str(video.get("channel", ""))
        video_id = str(video.get("video_id", ""))
        normalized = _norm(name)
        if not video_id or _norm(title) not in normalized:
            continue
        if not (_norm(artist) in normalized or _norm(artist) in _norm(channel)):
            continue
        if any(bad in name.casefold() for bad in (
            "cover", "reaction", "karaoke", "instrumental", "sped up", "slowed", "직캠", "커버", "노래방")):
            continue
        score = 0
        if "official" in name.casefold():
            score += 3
        if "topic" in channel.casefold() or "vevo" in channel.casefold():
            score += 2
        if "music video" in name.casefold() or "audio" in name.casefold():
            score += 1
        safe.append((score, video))
    if not safe:
        return None
    selected = max(safe, key=lambda pair: pair[0])[1]
    return {"type": "music_song", "content": "", "artist": artist, "song": title,
            "video_id": selected["video_id"], "video_title": selected["title"],
            "video_channel": selected["channel"]}


@app.post("/api/run-radio")
def run_radio(selected: dict = Body(...)):
    print(f"1. [DEBUG] payload: {selected}", flush=True)
    blocks = selected.get("blocks", [])
    keyword = selected.get("keyword", None)
    language = selected.get("language", "ko")

    main_speaker = "vdaeseong"
    for block in blocks:
        if block in BLOCK_SPEAKER_MAP:
            main_speaker = BLOCK_SPEAKER_MAP[block]
            break

    raw_scripts = []
    prev_type, context = None, ""
    verified_music_songs = []
    music_scripts = []

    try:
        opening = generate_opening_ment(keyword, language=language)
        raw_scripts.append({"type": "opening", "content": opening, "speaker": main_speaker})
        prev_type, context = "opening", opening[-400:] if opening else ""
    except Exception as exc:
        print(f"[ERROR] opening: {exc}", flush=True)

    for block in blocks:
        if block not in BLOCK_HANDLERS:
            print(f"[WARNING] unknown block: {block}", flush=True)
            continue
        try:
            if block == "music_trend":
                # 같은 대본을 다시 만들지 않고 검증된 노래 목록을 함께 받아온다.
                output = generate_music_trend(keyword, prev_type, context, language)
                content = output["script"]
                verified_music_songs.extend(output.get("songs", []))
            else:
                content = BLOCK_HANDLERS[block](keyword, language, prev_type, context)
            print(f"[DEBUG] {block} generated: {str(content)[:60]}", flush=True)
            speaker = BLOCK_SPEAKER_MAP.get(block, main_speaker)
            raw_scripts.append({"type": block, "content": content, "speaker": speaker})
            if block in MUSIC_BLOCKS and isinstance(content, str) and content.strip():
                music_scripts.append(content)
            prev_type, context = block, content[-400:] if isinstance(content, str) and content else ""
        except Exception as exc:
            print(f"[ERROR] block {block}: {exc}", flush=True)

    # 음악 코너가 실제로 생성된 경우에만 본문 전체 뒤에 한 곡 삽입.
    if music_scripts:
        song = None
        for candidate in verified_music_songs:
            if candidate.get("artist") and candidate.get("song"):
                song = {"artist": candidate["artist"], "song": candidate["song"]}
                break
        if song is None:
            try:
                song = _extract_song_from_script("\n\n".join(music_scripts))
            except Exception as exc:
                print(f"[MUSIC SONG] extract failed: {exc}", flush=True)
        if song:
            try:
                video = _find_youtube_segment(song)
                if video:
                    raw_scripts.append(video)
                    print(f"[MUSIC SONG] inserted {song['artist']} - {song['song']}", flush=True)
                else:
                    print("[MUSIC SONG] no sufficiently matching video; skipped", flush=True)
            except Exception as exc:
                print(f"[MUSIC SONG] YouTube search failed: {exc}", flush=True)

    try:
        closing = generate_closing_ment(keyword, language=language)
        raw_scripts.append({"type": "closing", "content": closing, "speaker": main_speaker})
    except Exception as exc:
        print(f"[ERROR] closing: {exc}", flush=True)

    final_scripts = []
    for item in raw_scripts:
        script_type = item["type"]
        if script_type == "music_song":
            # YouTube IFrame 재생용 정보. MP3/TTS 생성하지 않음.
            final_scripts.append(item)
            continue
        script_content = item.get("content", "")
        if not script_content:
            print(f"[WARNING] empty content {script_type}; skipped", flush=True)
            continue
        script_speaker = item.get("speaker", main_speaker)
        print(f"[TTS] {script_type} speaker={script_speaker}", flush=True)
        audio_url = generate_tts_url(text=script_content, speaker=script_speaker)
        final_scripts.append({"type": script_type, "content": script_content, "audio_url": audio_url})

    print(f"[DEBUG] final scripts: {[x['type'] for x in final_scripts]}", flush=True)
    return {"scripts": final_scripts}


@app.get("/api/bgm")
def get_radio_bgm(mood: str = "relaxation"):
    return {"bgm": get_bgm(mood)}


@app.get("/api/youtube/search")
def get_youtube_music(artist: str, title: str):
    return {"videos": search_youtube_music(artist, title)}


@app.get("/api/bgm/find")
def find_bgm(title: str, artist: str):
    return {"track": search_bgm_track(title, artist)}
