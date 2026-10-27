import os
import random
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

JAMENDO_CLIENT_ID = os.getenv("JAMENDO_CLIENT_ID")

# AI 라디오에서 사용할 고정 BGM 두 곡
BGM_TRACK_IDS = {
    "lofi": "2213549",    # Lofi - LOWTONE MUSIC
    "piano": "1920917",   # lockdown blues - LONELY PIANO
}


def get_bgm(mood="lofi"):
    if not JAMENDO_CLIENT_ID:
        raise RuntimeError("JAMENDO_CLIENT_ID가 없습니다.")

    # 지정한 카테고리에 해당하는 곡 선택
    # 잘못된 mood가 들어오면 기본곡 Lofi 사용
    track_id = BGM_TRACK_IDS.get(mood, BGM_TRACK_IDS["lofi"])

    url = "https://api.jamendo.com/v3.0/tracks/"

    params = {
        "client_id": JAMENDO_CLIENT_ID,
        "format": "json",
        "id": track_id,
        "audioformat": "mp32",
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )
    response.raise_for_status()

    data = response.json()

    if data.get("headers", {}).get("status") != "success":
        raise RuntimeError("Jamendo API 요청 실패")

    tracks = data.get("results", [])

    if not tracks:
        return None

    track = tracks[0]

    return {
        "id": track["id"],
        "title": track["name"],
        "artist": track["artist_name"],
        "audio": track["audio"],
        "license": track.get("license_ccurl"),
    }



def translate_music_keyword(keyword: str) -> str:
    """
    사용자의 한국어 키워드를
    Jamendo 검색에 적합한 영어 키워드로 변환
    """

    keyword = (keyword or "").strip()

    if not keyword:
        return "relaxing"

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                    You are an expert music search query translator.

                    Convert the user's keyword into a short English
                    search query suitable for Jamendo music search.

                    Rules:
                    1. Preserve the original meaning and emotion.
                    2. Prefer common English music-related words.
                    3. Use simple, widely searchable words.
                    4. Do not explain the translation.
                    5. Do not include quotes, punctuation or sentences.
                    6. Return only ONE short English search query.
                    7. Prefer 1-2 English words.

                    Examples:
                    첫사랑 -> love
                    이별 -> heartbreak
                    설렘 -> romantic
                    감성 -> emotional
                    가을 -> autumn
                    드라이브 -> road trip
                    위로 -> comfort
                    밤 -> night
                    봄 -> spring
                    행복 -> happy
                """
            },
            {
                "role": "user",
                "content": keyword
            }
        ],
        temperature=0.2,
        max_tokens=30,
    )

    translated = (response.choices[0].message.content or "").strip()

    return translated or "relaxing"




def search_jamendo_song(keyword: str):
    client_id = os.getenv("JAMENDO_CLIENT_ID")

    if not client_id:
        raise RuntimeError("JAMENDO_CLIENT_ID가 설정되지 않았습니다.")

    # 1. 키워드를 영어 음악 검색어로 변환
    english_keyword = translate_music_keyword(keyword)

    print(f"🎵 원본 키워드: {keyword}")
    print(f"🎵 영어 검색어: {english_keyword}")

    url = "https://api.jamendo.com/v3.0/tracks/"

    # 2. 영어 검색어로 Jamendo 검색
    response = requests.get(
        url,
        params={
            "client_id": client_id,
            "format": "json",
            "limit": 10,
            "search": english_keyword,
        },
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()
    headers = data.get("headers", {})

    if headers.get("status") != "success":
        raise RuntimeError(
            f"Jamendo API 오류: {headers.get('error_message')}"
        )

    tracks = data.get("results", [])

    print(f"🎵 검색된 음악 수: {len(tracks)}")

    if not tracks:
        print("⚠️ 검색 결과가 없습니다.")
        return None

    # 3. 오디오 URL이 존재하는 곡 선택
    track = next(
        (t for t in tracks if t.get("audio")),
        None
    )

    if not track:
        print("⚠️ 재생 가능한 음원이 없습니다.")
        return None

    print(
        f"✅ 음악 검색 성공: "
        f"{track.get('artist_name')} - {track.get('name')}"
    )

    # 4. 실제 노래 정보 반환
    return {
        "artist": track.get("artist_name"),
        "song": track.get("name"),
        "audio_url": track.get("audio"),
        "license_url": track.get("license_ccurl"),
        "provider": "jamendo",
    }

def search_bgm_track(title, artist):
    params = {
        "client_id": JAMENDO_CLIENT_ID,
        "format": "json",
        "search": f"{artist} {title}",
        "limit": 100,
        "type": "single albumtrack",
    }

    response = requests.get(
        "https://api.jamendo.com/v3.0/tracks/",
        params=params,
        timeout=15
    )
    response.raise_for_status()

    tracks = response.json().get("results", [])

    for track in tracks:
        if (
            track["name"].strip().lower() == title.lower()
            and track["artist_name"].strip().lower() == artist.lower()
        ):
            return {
                "id": track["id"],
                "title": track["name"],
                "artist": track["artist_name"],
                "audio": track["audio"],
                "license": track.get("license_ccurl"),
            }

    print("Jamendo 검색 후보:")
    for track in tracks:
        print(
            track["id"],
            track["name"],
            track["artist_name"]
        )

    return None