import os
import json
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from datetime import date, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from common.prompt_utils import build_block_prompt

# =========================================================
# 환경 설정
# =========================================================
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SEARCH_MODEL = "gpt-4.1-mini"
SCRIPT_MODEL = "gpt-4o-mini"

LOOKBACK_DAYS = 365      # 기본 검색 범위. 트로트만 18개월로 확대
HTTP_TIMEOUT = 8         # Apple API 타임아웃 (초)
HTTP_RETRIES = 1         # 실패 시 재시도 횟수

# 차트 보충에서만 쓰는 '자동 채택' 밴드 목록 (웹 검색 경로에서는 사용하지 않음)
KNOWN_BAND_NAMES = {
    "day6", "데이식스", "qwer", "엔플라잉", "nflying", "n.flying", "잔나비",
    "jannabi", "실리카겔", "silicagel", "루시", "lucy", "엑스디너리히어로즈",
    "xdinaryheroes", "터치드", "touched", "넬", "nell", "the rose", "더로즈",
    "cnblue", "씨엔블루", "ftisland", "ft아일랜드", "새소년", "너드커넥션",
}

# 웹 검색 힌트 (화이트리스트 아님, 검색을 돕는 예시일 뿐)
TOPIC_HINTS = {
    "밴드": "예: DAY6, QWER, 잔나비, 실리카겔, 루시, N.Flying, 넬, 새소년, 너드커넥션 같은 한국 밴드 "
            "(이 목록에 한정하지 말고 다른 밴드도 찾으세요)",
    "트로트": "예: 임영웅, 송가인, 영탁, 이찬원, 장민호 등 트로트 가수 (이 목록에 한정하지 않음)",
    "힙합": "한국 힙합 래퍼/프로듀서의 힙합 곡만. 아이돌 그룹의 팝/댄스곡과 K-POP 곡은 제외. 음원 장르가 Hip-Hop/Rap인 곡을 우선 (특정 목록에 한정하지 않음)",
}

# 시도 횟수별로 검색 관점을 바꿔서 같은 결과만 반복되는 것을 막음
ATTEMPT_ANGLES = [
    "최근 1년 안에 발표해 화제가 되었거나 대표곡으로 꼽히는 곡",
    "최근 3개월 안에 발매된 신곡 (음악 매체 리뷰, 음원 사이트 기준)",
    "멜론/지니/벅스/스포티파이 등 음원 차트에 진입한 최근 1년 이내 곡",
]


# =========================================================
# 공통 유틸
# =========================================================
def _http_get_json(url, timeout=HTTP_TIMEOUT, retries=HTTP_RETRIES):
    last_exc = None
    for i in range(retries + 1):
        try:
            req = Request(url, headers={"User-Agent": "AI-Radio/1.0", "Accept": "application/json"})
            with urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:          # 타임아웃/네트워크/JSON 오류 모두 재시도
            last_exc = exc
            time.sleep(0.5)
    raise last_exc


def parse_music_json(raw):
    """Decode JSON, fenced JSON, or a JSON object surrounded by commentary."""
    if not raw or not raw.strip():
        raise ValueError("응답이 비어 있습니다")
    raw = raw.strip().lstrip("\ufeff")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.I)
        result = None
        if fenced:
            try:
                result = json.loads(fenced.group(1).strip())
            except json.JSONDecodeError:
                result = None
        if result is None:
            decoder = json.JSONDecoder()
            for match in re.finditer(r"\{", raw):
                try:
                    value, _ = decoder.raw_decode(raw[match.start():])
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict) and isinstance(value.get("candidates"), list):
                    result = value
                    break
        if result is None:
            raise ValueError("올바른 JSON 객체를 찾을 수 없습니다")
    if not isinstance(result, dict) or not isinstance(result.get("candidates"), list):
        raise ValueError("candidates 배열이 없습니다")
    result["candidates"] = [x for x in result["candidates"] if isinstance(x, dict)]
    return result


def _normalize_name(value):
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    value = re.sub(r"[\(\[].*?[\)\]]", "", value)     # (Korean Ver.) [feat. X] 제거
    return re.sub(r"[^\w가-힣]", "", value, flags=re.UNICODE)


# =========================================================
# Apple iTunes Search API 검증 (실존 + 발매일 확인용)
# =========================================================
def _itunes_candidates(term, country):
    query = urlencode({
        "term": term, "media": "music", "entity": "song",
        "country": country, "limit": 50,
    })
    return _http_get_json("https://itunes.apple.com/search?" + query).get("results", [])


def verify_with_itunes(artist, song, earliest, latest, artist_alt=""):
    """Return (metadata, 'ok') or (None, reason)."""
    norm_song = _normalize_name(song)
    norm_artists = {n for n in (_normalize_name(artist), _normalize_name(artist_alt)) if n}
    if not norm_song or not norm_artists:
        return None, "empty_name"

    matched, errors = [], 0
    for country in ("KR", "US"):
        try:
            results = _itunes_candidates(f"{artist} {song}", country)
        except Exception as exc:
            errors += 1
            print(f"[MUSIC_TREND APPLE] {country} search error: {exc}", flush=True)
            continue
        for track in results:
            if track.get("kind") != "song":
                continue
            if _normalize_name(track.get("trackName")) != norm_song:
                continue
            track_artist = _normalize_name(track.get("artistName"))
            if not any(track_artist == a or (len(a) >= 4 and a in track_artist)
                       for a in norm_artists):
                continue
            try:
                published = date.fromisoformat(str(track.get("releaseDate", ""))[:10])
            except ValueError:
                continue
            if str(track.get("trackViewUrl", "")).startswith("https://"):
                matched.append((published, track))
        if matched:
            break  # KR에서 찾았으면 US 조회 생략

    if not matched:
        return None, "apple_unavailable" if errors == 2 else "apple_no_exact_match"
    if min(r[0] for r in matched) < earliest:
        return None, "older_release_found_in_catalog"
    valid = [(d, t) for d, t in matched if earliest <= d <= latest]
    if not valid:
        return None, "apple_release_out_of_range"
    published, track = min(valid, key=lambda p: p[0])
    return {
        "artist": track["artistName"],
        "song": track["trackName"],
        "release_date": published.isoformat(),
        "source_name": "Apple iTunes Search API",
        "source_url": track["trackViewUrl"],
        "track_id": track.get("trackId"),
        "primary_genre": track.get("primaryGenreName", ""),
    }, "ok"


# =========================================================
# 장르 매칭 / 보충 (Apple 차트, iTunes 장르 검색)
# =========================================================
GENRE_ALIASES = {
    "트로트": ("trot", "트로트", "성인가요"),
    "힙합": ("hip-hop", "hip hop", "rap", "힙합"),
    "랩": ("hip-hop", "hip hop", "rap", "힙합"),
    "발라드": ("ballad", "발라드"),
    "인디": ("indie", "인디", "alternative"),
    "록": ("rock", "록"),
    "락": ("rock", "록"),
    "밴드": ("rock", "alternative", "indie", "록"),
    "재즈": ("jazz", "재즈"),
    "알앤비": ("r&b", "soul", "알앤비"),
    "r&b": ("r&b", "soul"),
    "edm": ("dance", "electronic", "edm"),
    "팝": ("pop", "팝"),
    "pop": ("pop",),
}


def _is_kpop(topic):
    value = str(topic or "").casefold()
    return any(x in value for x in ("k-pop", "kpop", "케이팝", "케이 팝"))


def _genre_key(topic):
    if _is_kpop(topic):
        return None   # K-POP 은 'pop' 장르 검색으로 보충하지 않음 (서양 팝 혼입 방지)
    value = str(topic or "").strip().casefold()
    for key in sorted(GENRE_ALIASES, key=len, reverse=True):
        if key in value:
            return key
    return None


def _matches_genre(topic, genres):
    key = _genre_key(topic)
    if key is None:
        return False
    genre_text = " ".join(str(g).casefold() for g in genres)
    return any(alias in genre_text for alias in GENRE_ALIASES[key])


def supplement_from_itunes_genre(topic, selected, earliest, latest):
    selected = list(selected)
    genre = _genre_key(topic)
    # '밴드'는 iTunes 장르(rock 등)로 솔로 가수와 구분할 수 없으므로 보충하지 않음
    if genre is None or genre == "밴드":
        return selected

    search_terms = {
        "트로트": ["트로트", "trot"], "힙합": ["힙합", "korean hip hop"], "랩": ["rap", "힙합"],
        "발라드": ["발라드", "ballad"], "인디": ["indie", "인디"], "록": ["rock", "록"],
        "락": ["rock", "락"], "재즈": ["jazz"], "알앤비": ["r&b", "soul"], "r&b": ["r&b", "soul"],
        "edm": ["edm", "electronic"], "팝": ["pop"], "pop": ["pop"],
    }.get(genre, [genre])

    known = {_normalize_name(x["artist"]) for x in selected}
    possible = []
    for term in search_terms:
        for country in ("KR", "US"):
            try:
                rows = _itunes_candidates(term, country)
            except Exception as exc:
                print(f"[MUSIC_TREND GENRE] query={term} country={country}: {exc}", flush=True)
                continue
            for row in rows:
                if row.get("kind") != "song":
                    continue
                if not _matches_genre(topic, [row.get("primaryGenreName", "")]):
                    continue
                artist, song = row.get("artistName", ""), row.get("trackName", "")
                if not artist or not song or _normalize_name(artist) in known:
                    continue
                try:
                    released = date.fromisoformat(str(row.get("releaseDate", ""))[:10])
                except ValueError:
                    continue
                if earliest <= released <= latest:
                    possible.append((released, artist, song))

    possible.sort(reverse=True)
    attempted = set()
    for _, artist, song in possible:
        if len(selected) >= 3:
            break
        key = (_normalize_name(artist), _normalize_name(song))
        if key in attempted or key[0] in known:
            continue
        attempted.add(key)
        metadata, reason = verify_with_itunes(artist, song, earliest, latest)
        if not metadata:
            print(f"[MUSIC_TREND GENRE SKIP] {artist} - {song}: {reason}", flush=True)
            continue
        if not _topic_candidate_ok(topic, metadata):
            continue
        known.add(_normalize_name(metadata["artist"]))
        selected.append({**metadata, "verified": True, "is_actual_track": True,
                         "trend": "", "features": ""})
        print(f"[MUSIC_TREND GENRE ACCEPT] {artist} - {song}", flush=True)
    return selected


def _apple_chart_feed(country="kr", limit=100):
    url = (f"https://rss.applemarketingtools.com/api/v2/"
           f"{country}/music/most-played/{limit}/songs.json")
    return _http_get_json(url, timeout=HTTP_TIMEOUT).get("feed", {}).get("results", [])


def supplement_from_apple_chart(topic, selected, earliest, latest):
    selected = list(selected)
    seen_artists = {_normalize_name(x["artist"]) for x in selected}
    is_kpop = _is_kpop(topic)
    is_general = is_kpop or topic.strip().casefold() in ("음악", "music", "최신곡", "트렌드")
    genre_key = _genre_key(topic)
    known_bands = {_normalize_name(x) for x in KNOWN_BAND_NAMES}

    for country in ("kr",):
        if len(selected) >= 3:
            break
        try:
            chart = _apple_chart_feed(country)
            print(f"[MUSIC_TREND CHART] {country}: {len(chart)} chart entries", flush=True)
        except Exception as exc:
            print(f"[MUSIC_TREND CHART] {country} failed: {exc}", flush=True)
            continue

        for row in chart:
            if len(selected) >= 3:
                break
            artist, song = str(row.get("artistName", "")).strip(), str(row.get("name", "")).strip()
            if not artist or not song or _normalize_name(artist) in seen_artists:
                continue
            genres = [str(g.get("name", "")).casefold()
                      for g in row.get("genres", []) if isinstance(g, dict)]
            if is_kpop and not any("k-pop" in g or "kpop" in g or "케이팝" in g for g in genres):
                continue
            if not is_general:
                if genre_key == "밴드":
                    if _normalize_name(artist) not in known_bands:
                        continue
                elif not _matches_genre(topic, genres):
                    continue
            try:
                rss_date = date.fromisoformat(str(row.get("releaseDate", ""))[:10])
            except ValueError:
                continue
            if not earliest <= rss_date <= latest:
                continue
            metadata, reason = verify_with_itunes(artist, song, earliest, latest)
            if not metadata:
                print(f"[MUSIC_TREND CHART SKIP] {artist} - {song}: {reason}", flush=True)
                continue
            if not _topic_candidate_ok(topic, metadata):
                continue
            key = _normalize_name(metadata["artist"])
            if key in seen_artists:
                continue
            seen_artists.add(key)
            selected.append({**metadata, "verified": True, "is_actual_track": True,
                             "trend": "", "features": ""})
            print(f"[MUSIC_TREND CHART ACCEPT] {metadata['artist']} - {metadata['song']}", flush=True)
    return selected


# =========================================================
# 웹 검색: 후보 수집
# =========================================================
def _search_candidates(topic, today, earliest, latest, known_pairs, attempt):
    angle = ATTEMPT_ANGLES[min(attempt, len(ATTEMPT_ANGLES) - 1)]
    hint = TOPIC_HINTS.get(_genre_key(topic) or "", "")
    exclude = f"\n이미 확보한 곡(다시 제출 금지): {known_pairs}\n" if known_pairs else ""

    prompt = f"""
현재 날짜는 {today.isoformat()}입니다.
"{topic}" 장르/주제와 관련된 실제 발매곡 후보를 웹 검색으로 찾으세요.
이번 검색 관점: {angle}
{hint}

검색어는 한국어와 영어를 함께 사용하세요.
(예: 한국 {topic} 신곡 {today.year}, Korean {topic} new release {today.year})

[중요 조건]
- 발매일이 {earliest.isoformat()} ~ {latest.isoformat()} 사이인, 이미 발매 완료된 곡만 포함하세요.
  가장 최신일 필요는 없습니다. 이 기간 안이면 충분합니다.
- 컴백 일정, 카운트다운, 발매 예정 정보 사이트는 사용하지 마세요.
  (발매 예정곡, 미래 날짜의 곡은 절대 포함 금지)
- 후보는 서로 다른 아티스트로 8개를 찾으세요. 존재하지 않는 곡을 지어내지 마세요.
- release_date: 출처(음원 사이트, 공식 채널, 음악 매체)에서 확인한 정확한 발매일(YYYY-MM-DD).
  발매일을 확인하지 못한 곡은 후보에서 제외하세요.
- trend: 이 곡이 보여주는 "{topic}" 음악의 최근 트렌드 한 문장 (후보마다 서로 다른 관점).
- features: 사운드·보컬·리듬·편곡 특징 1~2문장. 출처에서 확인된 내용만, 모르면 빈 문자열.
- 앨범명/EP명/공연명/투어명을 곡명으로 쓰지 마세요.
- artist_type: solo / band / group / duo 중 하나. 실제 출처로 확인하세요.
  '밴드' 주제는 악기를 직접 연주하는 밴드만 band 입니다.
  아이돌 보컬/댄스 그룹(BTS, SHINee, Stray Kids, ILLIT, IVE 등)은 band 가 아니라 group 이고,
  록 장르 솔로 가수는 solo 입니다.
- artist_alt: 아티스트의 다른 언어 표기 (예: DAY6 ↔ 데이식스). 없으면 빈 문자열.
- topic_match: "{topic}" 과 실제로 관련되면 true.
- source_url: 실제로 확인한 URL만 넣으세요.
{exclude}
라디오 대본은 쓰지 말고 후보 데이터만 반환하세요.
"""
    schema = {
        "type": "object",
        "properties": {"candidates": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "artist": {"type": "string"},
                "artist_alt": {"type": "string"},
                "song": {"type": "string"},
                "artist_type": {"type": "string", "enum": ["solo", "band", "group", "duo"]},
                "topic_match": {"type": "boolean"},
                "is_album_or_event_title": {"type": "boolean"},
                "source_url": {"type": "string"},
                "release_date": {"type": "string"},
                "trend": {"type": "string"},
                "features": {"type": "string"},
            },
            "required": ["artist", "artist_alt", "song", "artist_type",
                         "topic_match", "is_album_or_event_title", "source_url",
                         "release_date", "trend", "features"],
            "additionalProperties": False,
        }}},
        "required": ["candidates"],
        "additionalProperties": False,
    }
    response = client.responses.create(
        model=SEARCH_MODEL,
        tools=[{"type": "web_search", "search_context_size": "low"}],
        tool_choice="required",
        max_output_tokens=6000,
        input=prompt,
        text={"format": {"type": "json_schema", "name": "music_candidates",
                         "strict": True, "schema": schema}},
    )
    return parse_music_json(response.output_text or "")["candidates"]


# =========================================================
# 웹 검색: 최종 곡의 트렌드/음악적 특징 보강
# =========================================================
def describe_tracks(topic, tracks):
    pairs = [{"artist": t["artist"], "song": t["song"],
              "release_date": t["release_date"]} for t in tracks]
    prompt = f"""
아래 곡들은 이미 실존이 확인된 "{topic}" 관련 곡입니다. 곡을 바꾸거나 추가하지 마세요.
{json.dumps(pairs, ensure_ascii=False)}

각 곡을 웹 검색(음악 매체 리뷰, 소속사 보도자료, 인터뷰 등)으로 조사해서 반환하세요.
- trend: 이 곡이 보여주는 "{topic}" 음악의 최근 트렌드를 한 문장으로.
         세 곡은 서로 다른 관점이어야 합니다 (예: 사운드 실험 / 장르 혼합 / 라이브·밴드 사운드 / 세대교체 등).
- features: 사운드, 보컬, 리듬, 편곡, 프로덕션 특징을 2~3문장으로.
            출처에서 확인되는 내용만 쓰고, 근거 없는 장르명은 붙이지 마세요.
- source_url: 실제로 참고한 URL.
"""
    schema = {
        "type": "object",
        "properties": {"tracks": {"type": "array", "items": {
            "type": "object",
            "properties": {"artist": {"type": "string"}, "song": {"type": "string"},
                           "trend": {"type": "string"}, "features": {"type": "string"},
                           "source_url": {"type": "string"}},
            "required": ["artist", "song", "trend", "features", "source_url"],
            "additionalProperties": False}}},
        "required": ["tracks"], "additionalProperties": False,
    }
    try:
        response = client.responses.create(
            model=SEARCH_MODEL,
            tools=[{"type": "web_search", "search_context_size": "low"}],
            tool_choice="required",
            max_output_tokens=3000,
            input=prompt,
            text={"format": {"type": "json_schema", "name": "track_details",
                             "strict": True, "schema": schema}},
        )
        rows = json.loads(response.output_text).get("tracks", [])
    except Exception as exc:
        print(f"[MUSIC_TREND DESCRIBE] failed: {exc}", flush=True)
        return tracks

    by_song = {_normalize_name(r.get("song")): r for r in rows}
    for t in tracks:
        r = by_song.get(_normalize_name(t["song"]))
        if r and r.get("features"):
            t["trend"] = r.get("trend", "")
            t["features"] = r["features"]
    return tracks


# iTunes에서 확인되지 않은 웹 검색 후보는 절대로 선곡하지 않습니다.
# 웹 검색 결과의 곡명/발매일/URL은 AI가 잘못 생성할 수 있습니다.


# =========================================================
# 밴드 판별 (악기 연주 밴드인지)
# =========================================================
def _band_check(artists):
    """아티스트 이름 목록 -> {정규화된 이름: 밴드 여부}. 실패 시 None."""
    prompt = (
        "다음 아티스트가 '밴드'인지 각각 판정하세요.\n"
        "밴드 = 멤버들이 기타/베이스/드럼/키보드 등 악기를 직접 연주하는 것이 팀의 정체성인 그룹.\n"
        "예) DAY6, CNBLUE, FT아일랜드, N.Flying, 잔나비, QWER, 넬, 실리카겔 -> true\n"
        "아이돌 보컬/댄스/힙합 그룹은 false.\n"
        "예) BTS, SHINee, Stray Kids, IVE, ILLIT, NCT, aespa -> false\n"
        "솔로 가수는 false. 잘 모르는 아티스트는 false.\n\n"
        f"아티스트: {json.dumps(artists, ensure_ascii=False)}"
    )
    schema = {
        "type": "object",
        "properties": {"artists": {"type": "array", "items": {
            "type": "object",
            "properties": {"artist": {"type": "string"}, "is_band": {"type": "boolean"}},
            "required": ["artist", "is_band"], "additionalProperties": False}}},
        "required": ["artists"], "additionalProperties": False,
    }
    try:
        resp = client.chat.completions.create(
            model=SEARCH_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_schema",
                             "json_schema": {"name": "band_check", "strict": True, "schema": schema}},
        )
        rows = json.loads(resp.choices[0].message.content).get("artists", [])
        return {_normalize_name(r.get("artist")): bool(r.get("is_band")) for r in rows}
    except Exception as exc:
        print(f"[MUSIC_TREND BAND_CHECK] failed: {exc}", flush=True)
        return None


# =========================================================
# 트로트: 웹 검색에서 나온 아티스트의 실제 iTunes 곡을 역검색
# 힙합: 음원 카탈로그에 표기된 장르가 힙합인지 확인
# =========================================================
def _months_before(d, months):
    year, month = d.year, d.month - months
    while month <= 0:
        year -= 1
        month += 12
    import calendar
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def _is_hiphop_topic(topic):
    return _genre_key(topic) in ("힙합", "랩")


def _hiphop_genre_ok(genre):
    name = str(genre or "").casefold()
    return any(word in name for word in ("hip-hop", "hip hop", "hiphop", "rap", "힙합"))


def _topic_candidate_ok(topic, metadata):
    if _is_hiphop_topic(topic):
        return _hiphop_genre_ok(metadata.get("primary_genre"))
    return True


def supplement_trot_from_artists(selected, artist_names, earliest, latest):
    """AI가 지어낸 제목은 사용하지 않고, Apple 등록곡을 아티스트별로 역검색한다.

    Apple releaseDate는 재발매 날짜일 수 있으므로, 같은 곡의 오래된 등록판본이
    검색되면 최신곡으로 채택하지 않는다. 장르가 애매한 곡은 최소한
    트로트 아티스트의 실제 카탈로그라는 점까지만 확인할 수 있다.
    """
    selected = list(selected)
    known = {_normalize_name(x["artist"]) for x in selected}
    # 고정 선정 목록이 아닌 검색 출발점. 웹 검색이 발견한 아티스트도 추가한다.
    seeds = ["김용빈", "영탁", "이찬원", "장민호", "송가인", "금잔디", "박서진", "진해성", "홍지윤", "정동원", "김희재", "나태주"]
    names = list(dict.fromkeys([*artist_names, *seeds]))
    print(f"[MUSIC_TREND TROT] 실제 음원 역검색 아티스트={len(names)}", flush=True)
    for name in names[:20]:
        if len(selected) >= 3:
            break
        if _normalize_name(name) in known:
            continue
        possible = []
        for country in ("KR", "US"):
            try:
                url = "https://itunes.apple.com/search?" + urlencode({
                    "term": name, "attribute": "artistTerm", "media": "music",
                    "entity": "song", "country": country, "limit": 200,
                })
                rows = _http_get_json(url).get("results", [])
            except Exception as exc:
                print(f"[MUSIC_TREND TROT ERROR] {name}/{country}: {exc}", flush=True)
                continue
            for row in rows:
                if row.get("kind") != "song":
                    continue
                # 동명이인을 막기 위해 Apple의 아티스트 표시명 정확히 검사
                if _normalize_name(row.get("artistName")) != _normalize_name(name):
                    continue
                try:
                    released = date.fromisoformat(str(row.get("releaseDate", ""))[:10])
                except ValueError:
                    continue
                if earliest <= released <= latest and str(row.get("trackViewUrl", "")).startswith("https://"):
                    possible.append((released, row))
        # 실제 조회된 제목에 대해 다시 검증해 오래된 동일 곡 판본을 거른다
        for _, row in sorted(possible, key=lambda item: item[0], reverse=True)[:8]:
            metadata, reason = verify_with_itunes(row["artistName"], row["trackName"], earliest, latest)
            if not metadata:
                continue
            if _normalize_name(metadata["artist"]) in known:
                break
            known.add(_normalize_name(metadata["artist"]))
            selected.append({**metadata, "verified": True, "is_actual_track": True,
                "trend": "최근 트로트 음반에서 확인된 곡", "features": "",
                "verification_note": "Apple 등록곡 확인. 최초 발매일과 트로트 스타일은 별도 확인 필요"})
            print(f"[MUSIC_TREND TROT ACCEPT] {metadata['artist']} - {metadata['song']} ({metadata['release_date']})", flush=True)
            break
    return selected


# =========================================================
# 최신 음악 데이터 수집
# 웹 검색 -> iTunes 검증 -> 장르 보충 -> 차트 보충 -> 특징 보강
# =========================================================
def get_latest_music_data(topic):
    today = date.today()
    yesterday = today - timedelta(days=1)
    earliest = _months_before(today, 18) if _genre_key(topic) == "트로트" else today - timedelta(days=LOOKBACK_DAYS)

    selected, used_artists, rejected = [], set(), {}
    discovered_artists = []

    def reject(reason):
        rejected[reason] = rejected.get(reason, 0) + 1

    for attempt in range(2):
        known = [f"{x['artist']} - {x['song']}" for x in selected]
        try:
            candidates = _search_candidates(topic, today, earliest, yesterday, known, attempt)
        except Exception as exc:
            print(f"[MUSIC_TREND SEARCH] attempt={attempt + 1} error: {exc}", flush=True)
            continue

        print(f"[MUSIC_TREND RAW] attempt={attempt + 1}/2 candidates={len(candidates)}", flush=True)

        # 1) 사전 필터 (네트워크 호출 없음)
        pending, seen_now = [], set()
        for item in candidates:
            artist = str(item.get("artist", "")).strip()
            song = str(item.get("song", "")).strip()
            if not artist or not song:
                reject("empty"); continue
            if item.get("is_album_or_event_title"):
                reject("album_or_event"); continue
            if item.get("topic_match") is False:
                reject("topic_mismatch"); continue
            if _genre_key(topic) == "밴드" and item.get("artist_type") == "solo":
                reject("not_band"); continue
            key = _normalize_name(artist)
            if key in used_artists or key in seen_now:
                reject("duplicate_artist"); continue
            seen_now.add(key)
            pending.append(item)
            if _genre_key(topic) == "트로트":
                discovered_artists.append(artist)

        # 1.5) 밴드 주제: 악기 연주 밴드인지 별도 판정 (아이돌 그룹 제외)
        if _genre_key(topic) == "밴드" and pending:
            verdict = _band_check([str(i.get("artist", "")).strip() for i in pending])
            kept = []
            for it in pending:
                if verdict is None:
                    ok = it.get("artist_type") == "band"      # 판정 실패 시 라벨로 대체
                else:
                    ok = verdict.get(_normalize_name(it.get("artist")), False)
                if ok:
                    kept.append(it)
                else:
                    reject("not_band")
                    print(f"[MUSIC_TREND NOT_BAND] {it.get('artist')}", flush=True)
            pending = kept

        # 2) iTunes 검증을 병렬로 실행
        def _check(it):
            return verify_with_itunes(
                str(it.get("artist", "")).strip(), str(it.get("song", "")).strip(),
                earliest, yesterday, artist_alt=str(it.get("artist_alt", "")).strip())

        with ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(_check, pending))

        for item, (metadata, reason) in zip(pending, results):
            if not metadata:
                reject(reason)
                print(f"[MUSIC_TREND SKIP] {item.get('artist')} - {item.get('song')}: {reason}",
                      flush=True)
                # 검증 실패곡은 절대 웹 검색 결과만으로 다시 채택하지 않음
                continue
            if len(selected) >= 3:
                continue
            if not _topic_candidate_ok(topic, metadata):
                reject("wrong_music_genre")
                print(f"[MUSIC_TREND HIPHOP SKIP] {metadata['artist']} - {metadata['song']}: {metadata.get('primary_genre')}", flush=True)
                continue
            key = _normalize_name(metadata["artist"])
            if key in used_artists:
                reject("duplicate_confirmed"); continue
            used_artists.add(key)
            used_artists.add(_normalize_name(item.get("artist")))
            selected.append({**item, **metadata, "verified": True, "is_actual_track": True})
            print(f"[MUSIC_TREND ACCEPT] {metadata['artist']} - {metadata['song']} "
                  f"({metadata['release_date']})", flush=True)

        print(f"[MUSIC_TREND] attempt={attempt + 1}/2 verified={len(selected)} "
              f"rejected={rejected}", flush=True)
        if len(selected) >= 3:
            break

    if _genre_key(topic) == "트로트" and len(selected) < 3:
        selected = supplement_trot_from_artists(selected, discovered_artists, earliest, yesterday)
    if len(selected) < 3:
        selected = supplement_from_itunes_genre(topic, selected, earliest, yesterday)
    if len(selected) < 3:
        selected = supplement_from_apple_chart(topic, selected, earliest, yesterday)

    if not selected:
        raise RuntimeError(
            f"'{topic}'에서 실제 곡을 1곡도 확인하지 못했습니다. "
            f"허위 곡을 생성하지 않습니다. rejected={rejected}"
        )

    print(f"[MUSIC_TREND VERIFIED] topic={topic}, count={len(selected)}", flush=True)

    selected.sort(key=lambda x: x["release_date"], reverse=True)
    selected = selected[:3]

    # iTunes 확인 곡만 특징을 보강 (곡명/아티스트/날짜는 바꾸지 않음)
    missing = [t for t in selected if not str(t.get("features") or "").strip()]
    if missing:
        describe_tracks(topic, missing)

    return {
        "current_date": today.isoformat(),
        "allowed_release_range": {"from": earliest.isoformat(), "to": yesterday.isoformat()},
        "trends": selected,
    }


# =========================================================
# 프롬프트
# =========================================================
SLIM_FIELDS = ("artist", "song", "release_date", "trend", "features")

STRUCTURE_GUIDE = """
[대본 구성 - 번호/소제목 없이 자연스러운 문단으로]
① 현재 음악 흐름 소개 (200~300자)
   "{topic}" 중심으로 최근 음악 분위기와 변화를 소개.
② 트렌드 1~{n} (트렌드당 250~350자, 곡마다 별도 문단)
   '첫 번째 트렌드는', '두 번째 트렌드는', '세 번째 트렌드는'으로 문단을 시작하세요.
   트렌드 + 대표 아티스트 + 곡명 + 발매일 + 음악적 특징.
③ 트렌드별 대표곡 해설 (곡당 별도 문단, 180~250자)
   '먼저 ...를 살펴보면', '두 번째 곡인 ...', '마지막으로 ...'처럼 곡 순서대로 시작하세요.
   각 곡이 해당 트렌드를 보여주는 이유와 사운드·보컬·리듬·편곡·프로덕션 특징.
   두 번째 곡부터는 앞의 곡과의 차이를 언급.
④ 전체 흐름 정리 (200~300자)
   {n}가지 트렌드를 종합해 "{topic}" 음악이 어떤 방향으로 변화하는지 정리.
   새 아티스트/곡 추가 금지.

[문체]
- 문단은 정확히 {p}개: 흐름 소개 1 + 트렌드 소개 {n} + 곡 해설 {n} + 전체 정리 1. 문단 사이는 빈 줄로 구분.
- 전체 약 2,300~2,700자, 친근한 라디오 DJ 구어체.
- 이 대본은 방송 중간 코너입니다. 오프닝/클로징은 따로 있으므로
  '안녕하세요', '청취자 여러분' 같은 인사로 시작하지 말고, 곧바로 음악 흐름 소개로 시작하세요.
  이전 코너와의 연결은 인사 없이 첫 문장에서 자연스럽게 한 번만 하세요.
- '감사합니다', '좋은 밤 되세요', '다음에 또 만나요' 같은 작별/마무리 인사도 쓰지 마세요.
- 실제로 음악을 재생하는 듯한 표현 금지.
- '(곡 재생)', '(음악)' 같은 괄호 표시나 지문을 절대 넣지 마세요.
- '함께 들어볼까요', '잠시 감상해보시죠'처럼 지금 곡을 틀겠다는 표현 금지.
  (곡은 대본이 모두 끝난 뒤 소개한 곡 중 한 곡만 별도로 재생됩니다.)
- 대본은 '전체 흐름 정리' 문단에서 그대로 끝내세요. 그 뒤에 문장이나 문단을 더 붙이지 마세요.
- '이제 ~로 마무리해볼까요?', '~를 이어서 들려드릴게요', '다음 곡은', '다음 곡을 기대해 주세요'처럼
  곡을 틀겠다거나 다음으로 넘기는 문장은 절대 쓰지 마세요.
- 마지막 문장은 음악 흐름에 대한 소감이나 따뜻한 한마디로 끝내세요.
"""


def build_ko_instruction(topic, prev_type, context, music_data):
    songs = [{k: t.get(k, "") for k in SLIM_FIELDS} for t in music_data["trends"]]
    n = len(songs)
    data_text = json.dumps(songs, ensure_ascii=False, indent=2)
    return f"""
당신은 최신 음악 트렌드를 소개하는 전문 라디오 DJ입니다.

이전 코너: {prev_type}
이전 내용: {context}
오늘의 음악 키워드: {topic}

[확인된 곡 {n}곡]
{data_text}

[규칙]
1. 위 {n}곡만 소개하세요. 곡/아티스트/발매일을 바꾸거나 추가하지 마세요.
2. 각 곡의 trend 필드를 해당 트렌드의 주제로, features 필드를 곡 해설의 근거로 사용하세요.
   features 에 없는 사운드 묘사, 차트 순위, 인기 수준은 단정하지 마세요.
3. 곡마다 서로 다른 관점의 트렌드로 소개하고, 같은 표현을 반복하지 마세요.
{STRUCTURE_GUIDE.format(topic=topic, n=n, p=2 * n + 2)}
""".strip()


# 대본 앞뒤에 모델이 멋대로 붙인 인사/마무리/재생 유도 문장을 지우는 안전장치
START_CUE = re.compile(r"(안녕하세요|청취자 여러분|반갑습니다|환영합니다)")
END_CUE = re.compile(
    r"(들려드릴게요|들려드리겠습니다|들어볼까요|들어보시죠|감상해보시죠|틀어|마무리해볼까요|"
    r"다음 곡|기대해 ?주세요|좋은 밤|안녕히|또 만나|다음 시간|감사합니다)"
)


def _split_sentences(paragraph):
    return [x for x in re.split(r"(?<=[.?!])\s+", paragraph.strip()) if x]


def _clean_script(text):
    text = re.sub(r"[\(\[（]\s*(?:[^\)\]）]{0,10}재생[^\)\]）]{0,10}|음악|music|playing)\s*[\)\]）]",
                  "", text, flags=re.I)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]

    # 앞쪽 인사 문장 제거
    while paras:
        sents = _split_sentences(paras[0])
        while sents and START_CUE.search(sents[0]) and len(sents[0]) <= 60:
            sents.pop(0)
        if sents:
            paras[0] = " ".join(sents)
            break
        paras.pop(0)

    # 끝쪽 마무리/재생 유도 문장 제거
    while paras:
        sents = _split_sentences(paras[-1])
        while sents and END_CUE.search(sents[-1]):
            sents.pop()
        if sents:
            paras[-1] = " ".join(sents)
            break
        paras.pop()

    return "\n\n".join(paras).strip()


# =========================================================
# MUSIC_TREND
# =========================================================
def generate_music_trend(keyword=None, prev_type=None, context=None, language="ko"):
    """Return {"script": str, "songs": [{artist, song, release_date}, ...]}"""
    topic = keyword.strip() if keyword and keyword.strip() else "K-POP"

    try:
        latest_music_data = get_latest_music_data(topic)
    except Exception as e:
        print(f"[MUSIC_TREND] 최신곡 검색 실패: {e}", flush=True)

        fallback_prompt = f"""
당신은 음악 라디오 DJ입니다. 방송 중간 코너의 대본을 작성합니다.

이전 코너: {prev_type}
이전 내용: {context}
오늘의 음악 주제: {topic}

검증된 곡을 확보하지 못했습니다. 특정 곡명, 아티스트의 신곡, 발매일, 차트 순위는 절대 만들어내지 마세요.

"{topic}" 음악의 특징과 최근 경향을 아래 흐름으로 설명하세요. (총 8문단, 문단 사이 빈 줄)
① 현재 음악 흐름 소개 1문단
② 최근 눈에 띄는 스타일/사운드 트렌드 3가지를 '첫 번째 트렌드는', '두 번째 트렌드는', '세 번째 트렌드는'으로 시작하는 3문단
③ 각 트렌드의 사운드·보컬·리듬·편곡·프로덕션 특징 해설 3문단
④ 전체 흐름 정리 1문단
약 1,800~2,200자, 친근한 라디오 DJ 구어체.
'안녕하세요' 같은 인사로 시작하지 말고, 작별 인사나 '다음 곡' 같은 마무리 문장도 쓰지 마세요.
실제로 음악을 재생하는 듯한 표현은 쓰지 마세요.
"""
        response = client.chat.completions.create(
            model=SCRIPT_MODEL,
            messages=[{"role": "user", "content": fallback_prompt}],
            temperature=0.5,
            max_tokens=3000,
        )
        return {"script": _clean_script(response.choices[0].message.content), "songs": []}

    song_count = len(latest_music_data["trends"])

    if language == "ko":
        base_instruction = build_ko_instruction(topic, prev_type, context, latest_music_data)
    else:
        songs = [{k: t.get(k, "") for k in SLIM_FIELDS} for t in latest_music_data["trends"]]
        base_instruction = f"""
You are a professional radio DJ introducing music trends.
Today's topic is: "{topic}"
Verified songs:
{json.dumps(songs, ensure_ascii=False, indent=2)}

Use exactly the {song_count} artists and songs above. Do not replace or add any.
Use each song's "trend" as its trend theme and "features" as the basis for discussion.
Do not invent release dates, chart rankings, or musical details not in the data.
Structure (exactly {2 * song_count + 2} paragraphs): current overview -> trend 1..{song_count}
-> deeper discussion of each song -> overall summary. No headings or numbers.
This is a middle segment of a broadcast: do not greet the listeners and do not sign off.
Do not pretend that music is actually being played.
Never write playback cues such as (playing) and never say you are about to play a song.
End with the overall summary and nothing after it.
"""

    prompt = build_block_prompt(
        base_instruction=base_instruction,
        block_name="MUSIC_TREND",
        keyword=keyword,
        prev_type=prev_type,
        context=context,
    )

    response = client.chat.completions.create(
        model=SCRIPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=3500,
    )
    songs = [{"artist": t["artist"], "song": t["song"], "release_date": t["release_date"]}
             for t in latest_music_data["trends"]]
    return {"script": _clean_script(response.choices[0].message.content), "songs": songs}


def block_music_trend(keyword=None, prev_type=None, context=None, language="ko"):
    """기존 호출부 호환용: 대본 문자열만 반환."""
    return generate_music_trend(keyword, prev_type, context, language)["script"]


# =========================================================
# 단독 테스트
# =========================================================
if __name__ == "__main__":
    try:
        result = generate_music_trend(
            keyword=os.getenv("MUSIC_TEST_KEYWORD", "K-POP"),
            language="ko",
        )
        print("\n================ MUSIC_TREND ================\n")
        print(result["script"])
        print("\n---------------- songs ----------------")
        print(json.dumps(result["songs"], ensure_ascii=False, indent=2))
    except Exception as e:
        print("\n[MUSIC_TREND ERROR]")
        print(str(e))