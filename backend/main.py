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
            print(
                f"[ITUNES DEBUG] {country} / {artist} - {title} / 결과={len(tracks)}",
                flush=True
            )

            print(
                f"[ITUNES DEBUG] 상위 결과={[(t.get('artistName'), t.get('trackName')) for t in tracks[:5]]}",
                flush=True
            )
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


def _extract_song_from_script(content, allow_unverified=False):
    """대본에 언급된 실제 노래 후보들을 검증하여 리스트로 반환."""
    response = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    ).chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "음악 라디오 대본에서 실제 언급된 아티스트와 곡을 "
                    "최대 8개 추출하세요. "
                    "아티스트 이름은 가능하면 음원 서비스에서 사용하는 "
                    "공식 활동명으로 표기하세요. 예: 방탄소년단은 BTS. "
                    "대본에 없는 곡은 절대 추가하지 마세요. "
                    '반드시 {"songs":[{"artist":"...","song":"..."}]} '
                    "형식의 JSON으로 답하세요."
                )
            },
            {"role": "user", "content": content}
        ]
    )

    data = json.loads(response.choices[0].message.content or "{}")
    candidates = data.get("songs", [])

    if not isinstance(candidates, list):
        return []

    verified_songs = []

    for candidate in candidates[:8]:
        if not isinstance(candidate, dict):
            continue

        artist = str(candidate.get("artist") or "").strip()
        song = str(candidate.get("song") or "").strip()

        if not artist or not song:
            continue

        if _norm(song) not in _norm(content):
            continue

        verified = _itunes_has_track(artist, song)
        print(
            f"[MUSIC SONG DEBUG] iTunes 검증: "
            f"{artist} - {song} -> {verified}",
            flush=True
        )

        if verified:
            if verified not in verified_songs:
                verified_songs.append(verified)

        elif allow_unverified:
            # 트로트 전용 보조 검색 후보
            # 장르명 등을 가수 이름으로 잘못 추출한 경우 제외
            if _norm(artist) in {
                "트로트", "trot", "음악", "music",
                "노래", "가수", "아티스트"
            }:
                continue

            candidate_song = {
                "artist": artist,
                "song": song
            }

            if candidate_song not in verified_songs:
                verified_songs.append(candidate_song)

    print("[MUSIC SONG] candidates:", verified_songs, flush=True)

    return verified_songs


def _find_youtube_segment(song):
    """가수+곡명 검색. 동명이곡/커버 등 오선곡을 줄이기 위해 보수적으로 검사."""
    artist, title = song["artist"], song["song"]
    videos = search_youtube_music(artist, title)
    print(
        f"[MUSIC SONG DEBUG] YouTube 검색: {artist} - {title}",
        flush=True
    )

    print(
        f"[MUSIC SONG DEBUG] 검색 결과 수: {len(videos)}",
        flush=True
    )

    for video in videos:
        print(
            f"[MUSIC SONG DEBUG] title={video.get('title')} "
            f"channel={video.get('channel')} "
            f"id={video.get('video_id')}",
            flush=True
        )
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
    # 음악 본문이 생성된 경우 실제 곡 한 곡 삽입
    if music_scripts:
        candidates = [
            {"artist": item["artist"], "song": item["song"]}
            for item in verified_music_songs
            if item.get("artist") and item.get("song")
        ]

        if not candidates:
            try:
                candidates = _extract_song_from_script(
                    "\n\n".join(music_scripts)
                )
            except Exception as exc:
                print(f"[MUSIC SONG] extract failed: {exc}", flush=True)
                candidates = []

        for song in candidates:
            try:
                video = _find_youtube_segment(song)

                if video:
                    raw_scripts.append(video)
                    print(
                        f"[MUSIC SONG] inserted: "
                        f"{song['artist']} - {song['song']}",
                        flush=True
                    )
                    break

                print(
                    f"[MUSIC SONG] video not found: "
                    f"{song['artist']} - {song['song']}",
                    flush=True
                )

            except Exception as exc:
                print(
                    f"[MUSIC SONG] YouTube error: {exc}",
                    flush=True
                )

        # 트로트 + 장르&음악 이야기 / 최신 음악 트렌드에서만 실행
        # 기존 경로에서 music_song 삽입에 실패했을 때만 추가 검색
        is_trot_target = (
            isinstance(keyword, str)
            and keyword.strip().casefold() in ("트로트", "trot")
            and any(
                b in ("music_story", "music_genre", "music_trend")
                for b in blocks
            )
        )

        already_inserted = any(
            item.get("type") == "music_song"
            for item in raw_scripts
        )

        if is_trot_target and music_scripts and not already_inserted:
            print("[TROT FALLBACK] 트로트 곡 추가 검색 시작", flush=True)

            try:
                trot_candidates = _extract_song_from_script(
                    "\n\n".join(music_scripts),
                    allow_unverified=True
                )

                for song in trot_candidates:
                    try:
                        video = _find_youtube_segment(song)

                        if video:
                            raw_scripts.append(video)
                            print(
                                f"[TROT FALLBACK] inserted: "
                                f"{song['artist']} - {song['song']}",
                                flush=True
                            )
                            break

                    except Exception as exc:
                        print(
                            f"[TROT FALLBACK] YouTube error: {exc}",
                            flush=True
                        )

            except Exception as exc:
                print(
                    f"[TROT FALLBACK] extraction error: {exc}",
                    flush=True
                )

        # 오늘의 아티스트 전용: 기존 곡 삽입 실패 시 보조 검색
        is_artist_target = "music_artist" in blocks

        already_inserted = any(
            item.get("type") == "music_song"
            for item in raw_scripts
        )

        if is_artist_target and music_scripts and not already_inserted:
            print("[ARTIST FALLBACK] 곡 추가 검색 시작", flush=True)

            try:
                import random

                artist_candidates = _extract_song_from_script(
                    "\n\n".join(music_scripts),
                    allow_unverified=True
                )

                # 대본에 소개된 곡 중 무작위로 검색
                random.shuffle(artist_candidates)

                for song in artist_candidates:
                    try:
                        video = _find_youtube_segment(song)

                        if video:
                            raw_scripts.append(video)

                            print(
                                f"[ARTIST FALLBACK] inserted: "
                                f"{song['artist']} - {song['song']}",
                                flush=True
                            )
                            break

                        print(
                            f"[ARTIST FALLBACK] video not found: "
                            f"{song['artist']} - {song['song']}",
                            flush=True
                        )

                    except Exception as exc:
                        print(
                            f"[ARTIST FALLBACK] YouTube error: {exc}",
                            flush=True
                        )

            except Exception as exc:
                print(
                    f"[ARTIST FALLBACK] extraction error: {exc}",
                    flush=True
                )
        
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
