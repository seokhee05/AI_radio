import os
import json
import re
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import date, timedelta

from dotenv import load_dotenv
from openai import OpenAI

from common.prompt_utils import build_block_prompt


# =========================================================
# 환경 설정
# =========================================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


SEARCH_MODEL = "gpt-4.1-mini"
SCRIPT_MODEL = "gpt-4o-mini"


def parse_music_json(raw):
    """Decode JSON, fenced JSON, or a JSON object surrounded by commentary."""
    if not raw or not raw.strip():
        raise ValueError("응답이 비어 있습니다")
    raw = raw.strip().lstrip("\ufeff")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Sometimes the model wraps the response in ```json ... ```.
        fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.I)
        if fenced:
            try:
                result = json.loads(fenced.group(1).strip())
            except json.JSONDecodeError:
                result = None
        else:
            result = None
        if result is None:
            # Support a preamble without silently repairing fabricated or truncated data.
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


# =========================================================
# Apple iTunes Search API를 통한 2차 검증
# - 웹 검색 모델의 release_date / verified 값을 신뢰하지 않음
# - 동일 곡/아티스트를 실제 음원 카탈로그에서 조회
# - 검색 결과에 없는 곡을 보충 생성하지 않음
# =========================================================

def _normalize_name(value):
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    # 기본 표기 및 공백 차이만 무시 (제목 부분 일치는 허용하지 않음)
    return re.sub(r"[^\w가-힣]", "", value, flags=re.UNICODE)


def _itunes_candidates(term, country):
    query = urlencode({
        "term": term,
        "media": "music",
        "entity": "song",
        "country": country,
        "limit": 50,
    })
    url = "https://itunes.apple.com/search?" + query
    req = Request(url, headers={"User-Agent": "AI-Radio/1.0", "Accept": "application/json"})
    with urlopen(req, timeout=12) as response:
        return json.loads(response.read().decode("utf-8")).get("results", [])


def verify_with_itunes(artist, song, earliest, latest):
    """Return matched, in-range catalog metadata, or (None, reason).

    iTunes's releaseDate can represent the *catalog release* of an album/remaster.
    Treat old songs reissued as new as requiring additional original-release review.
    """
    norm_song = _normalize_name(song)
    norm_artist = _normalize_name(artist)
    if not norm_song or not norm_artist:
        return None, "empty_name"

    matched = []
    errors = 0
    for country in ("KR", "US"):
        try:
            results = _itunes_candidates(f"{artist} {song}", country)
        except (OSError, ValueError, HTTPError, URLError) as exc:
            errors += 1
            print(f"[MUSIC_TREND APPLE] {country} search error: {exc}", flush=True)
            continue
        for track in results:
            if track.get("kind") != "song":
                continue
            track_song = _normalize_name(track.get("trackName"))
            track_artist = _normalize_name(track.get("artistName"))
            if track_song != norm_song:
                continue
            if not (track_artist == norm_artist or
                    (len(norm_artist) >= 4 and norm_artist in track_artist)):
                continue
            try:
                published_date = date.fromisoformat(str(track.get("releaseDate", ""))[:10])
            except ValueError:
                continue
            if str(track.get("trackViewUrl", "")).startswith("https://"):
                matched.append((published_date, track))

    if not matched:
        return None, "apple_unavailable" if errors == 2 else "apple_no_exact_match"

    # A currently available reissue must not make a known old catalog track 'new'.
    oldest_date = min(row[0] for row in matched)
    if oldest_date < earliest:
        return None, "older_release_found_in_catalog"

    valid = [(released, row) for released, row in matched
             if earliest <= released <= latest]
    if not valid:
        return None, "apple_release_out_of_range"
    published_date, track = min(valid, key=lambda pair: pair[0])
    return {
        "artist": track["artistName"],
        "song": track["trackName"],
        "release_date": published_date.isoformat(),
        "source_name": "Apple iTunes Search API",
        "source_url": track["trackViewUrl"],
        "track_id": track.get("trackId"),
    }, "ok"



# =========================================================
# Apple Music 공개 차트에서 직접 후보 찾기 (웹검색 실패 시 보충)
# 차트 후보도 iTunes 메타데이터 재검증 후 사용함.
# =========================================================

def _apple_chart_feed(country="kr", limit=100):
    url = (f"https://rss.applemarketingtools.com/api/v2/"
           f"{country}/music/most-played/{limit}/songs.json")
    req = Request(url, headers={
        "User-Agent": "AI-Radio/1.0", "Accept": "application/json"})
    with urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8")).get("feed", {}).get("results", [])


def supplement_from_apple_chart(topic, selected, earliest, latest):
    """Find chart songs without guessing titles/dates. Return selected candidates."""
    selected = list(selected)
    seen_artists = {_normalize_name(x["artist"]) for x in selected}
    is_kpop = "k-pop" in topic.casefold() or "kpop" in topic.casefold() or "케이팝" in topic
    is_general = is_kpop or topic.strip().casefold() in ("음악", "music", "최신곡", "트렌드")
    if not is_general:
        print("[MUSIC_TREND CHART] 특화 주제는 차트 자동 보충을 생략합니다", flush=True)
        return selected
    for country in ("kr", "us"):
        if len(selected) >= 3:
            break
        try:
            chart = _apple_chart_feed(country)
            print(f"[MUSIC_TREND CHART] {country}: {len(chart)} chart entries", flush=True)
        except (OSError, ValueError) as exc:
            print(f"[MUSIC_TREND CHART] {country} failed: {exc}", flush=True)
            continue
        for row in chart:
            if len(selected) >= 3:
                break
            artist, song = str(row.get("artistName", "")).strip(), str(row.get("name", "")).strip()
            if not artist or not song or _normalize_name(artist) in seen_artists:
                continue
            genres = [str(g.get("name", "")).casefold() for g in row.get("genres", []) if isinstance(g, dict)]
            # Don't label general Korean chart entries as K-pop without a K-pop genre.
            if is_kpop and not any("k-pop" in g or "kpop" in g or "케이팝" in g for g in genres):
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
            key = _normalize_name(metadata["artist"])
            if key in seen_artists:
                continue
            seen_artists.add(key)
            selected.append({
                **metadata,
                "verified": True,
                "topic_match": True,
                "is_actual_track": True,
                "is_album_or_event_title": False,
                "trend": "최근 차트에 오른 신곡",
                "features": "출처에서 음향 특징이 확인되지 않음",
                "reason": "Apple Music 공개 차트에서 확인한 곡",
                "verification_note": "Apple chart + iTunes track metadata; original release of reissues may need review",
            })
            print(f"[MUSIC_TREND CHART ACCEPT] {metadata['artist']} - {metadata['song']} "
                  f"({metadata['release_date']})", flush=True)
    return selected


# =========================================================
# 최신 음악 데이터 웹 검색
# =========================================================

def get_latest_music_data(topic, _retry=0, _collected=None):

    today = date.today()
    yesterday = today - timedelta(days=1)
    six_months_ago = today - timedelta(days=365)

    # K-POP은 생성형 웹 검색보다 공개 음원 차트를 먼저 확인.
    # 이미 3곡 확보되면 불필요한 AI 검색을 하지 않음.
    if _retry == 0 and ("k-pop" in topic.casefold() or "kpop" in topic.casefold()
                        or "케이팝" in topic):
        direct = supplement_from_apple_chart(topic, [], six_months_ago, yesterday)
        if len(direct) >= 3:
            direct.sort(key=lambda x: x["release_date"], reverse=True)
            result = {
                "current_date": today.isoformat(),
                "allowed_release_range": {
                    "from": six_months_ago.isoformat(), "to": yesterday.isoformat()
                },
                "trends": direct[:3]
            }
            print("[MUSIC_TREND] Apple chart direct selection:\n" +
                  json.dumps(result, ensure_ascii=False, indent=2), flush=True)
            return result

    known_pairs = [
        f"{x.get('artist', '')} - {x.get('song', '')}"
        for x in (_collected or [])
    ]
    retry_guidance = (
        "1차 검색과 다른 아티스트/곡을 추가 탐색하세요. "
        "음원 플랫폼의 개별 트랙 페이지와 발매일을 우선 확인하세요. "
        "기존 확인 곡은 다시 제출하지 마세요. "
        f"이미 확보한 곡: {known_pairs}"
        if _retry else ""
    )

    search_prompt = f"""
{retry_guidance}

현재 날짜는 {today.isoformat()}입니다.

"{topic}"과 관련된
최근 실제 발매곡을 웹 검색으로 조사하세요.

최종 라디오 대본에서 사용할
최신 음악 대표곡을 찾는 단계입니다.


==================================================
발매일 범위
==================================================

반드시 실제 발매일이

{six_months_ago.isoformat()}
~
{yesterday.isoformat()}

사이인 곡만 후보에 포함하세요.

즉 오늘 기준

어제
~
약 1년 전

사이의 실제 발매곡만 허용합니다.


가능하면 최신곡을 우선하세요.

우선순위:

1. 최근 1개월
2. 최근 1~3개월
3. 최근 3~12개월


==================================================
후보 개수
==================================================

조건을 만족하는 후보를
가능하면 12개 이상 찾아주세요.

최종 3곡을 억지로 맞추기 위해
존재하지 않는 곡이나 정보를
만들어내면 안 됩니다.


==================================================
반드시 확인할 것
==================================================

각 후보마다 웹 검색을 통해
다음 내용을 확인하세요.

1. 아티스트가 실제 존재하는가

2. 곡이 실제 존재하는가

3. 해당 곡을 실제로
   그 아티스트가 발표했는가

4. 해당 제목이 실제 song / track인가

5. 앨범명, EP명, 공연명,
   페스티벌명, 투어명이 아닌가

6. 앨범명과 곡명이 동일한 경우
   실제 트랙리스트에도
   동일 제목의 곡이 존재하는가

7. 정확한 발매일을 확인할 수 있는가

8. 발매일이 허용 범위 안에 있는가

9. "{topic}"과 실제 관련된
   아티스트와 곡인가


==================================================
특히 금지
==================================================

다음과 같은 것을
곡명으로 착각하지 마세요.

- 앨범명
- EP명
- 공연명
- 페스티벌명
- 콘서트명
- 투어명
- 프로젝트명
- 기사 제목


예:

"World Tour"
"Festival 2026"
"XMF 2026"

같은 이름을
실제 곡 제목으로 만들면 안 됩니다.


==================================================
주제가 K-POP일 경우
==================================================

주제가 K-POP이라면

단순히 한국 공연이나
K-POP 행사에 참여했다는 이유만으로

해외 아티스트를
K-POP 대표 아티스트로 선정하지 마세요.

실제로 K-POP 음악 시장과 관련된
아티스트와 곡을 선정하세요.


==================================================
verified 판정
==================================================

다음 조건이 모두 확인될 때만

verified = true

로 설정하세요.

- 실제 아티스트
- 실제 곡
- 아티스트와 곡 매칭 확인
- 실제 track 확인
- 앨범/행사명 아님
- 정확한 발매일 확인
- 날짜 범위 통과
- 주제와 관련 있음


확실하지 않은 정보는 지어내지 말고 verification_note에 불확실한 항목을 기록하세요.

verified는 모든 항목을 확인한 경우에만 true로 설정하되,
일부 검증이 부족하더라도 실제 곡 후보와 확인 가능한 출처를 반환하세요.


==================================================
음악적 특징
==================================================

trend와 features는
웹 검색으로 확인할 수 있는 사실을
중심으로 작성하세요.

근거가 없는 상태에서

R&B
future bass
city pop
EDM
tropical house

등의 장르명을
임의로 붙이지 마세요.

확실하지 않은 경우에는

"강한 신스 중심의 사운드"
"밴드 중심의 편곡"
"리듬을 강조한 팝 사운드"

처럼 확인 가능한 수준으로만
설명하세요.


==================================================
출처
==================================================

가능하면 다음 출처를 우선하세요.

- 공식 아티스트 사이트
- 공식 소속사
- 공식 앨범 / 트랙 페이지
- Apple Music
- Spotify
- Melon
- Bugs
- Genie
- 신뢰할 수 있는 음악 매체

source_url에는
실제로 확인한 주소를 넣으세요.

URL을 만들어내지 마세요.


==================================================
중요
==================================================

아직 라디오 대본은 작성하지 마세요.

최신 음악 후보 데이터만 반환하세요.
"""

    # 재검색 시 이미 확보한 아티스트와 곡을 피하도록 안내
    if _collected:
        excluded = ", ".join(
            f"{item['artist']} - {item['song']}" for item in _collected
        )
        search_prompt += (
            f"\n이미 확인한 곡은 다시 제안하지 마세요: {excluded}\n"
            "다른 아티스트의 실제 발매곡을 추가로 찾으세요. "
            "정확한 출처가 없는 곡은 포함하지 마세요.\n"
        )

    response = client.responses.create(
        model=SEARCH_MODEL,

        tools=[
            {
                "type": "web_search"
            }
        ],

        tool_choice="required",
        max_output_tokens=5000,

        input=search_prompt,

        text={
            "format": {
                "type": "json_schema",
                "name": "latest_music_candidates",
                "strict": True,

                "schema": {
                    "type": "object",

                    "properties": {

                        "candidates": {
                            "type": "array",

                            "items": {
                                "type": "object",

                                "properties": {

                                    "verified": {
                                        "type": "boolean"
                                    },

                                    "topic_match": {
                                        "type": "boolean"
                                    },

                                    "is_actual_track": {
                                        "type": "boolean"
                                    },

                                    "is_album_or_event_title": {
                                        "type": "boolean"
                                    },

                                    "artist": {
                                        "type": "string"
                                    },

                                    "song": {
                                        "type": "string"
                                    },

                                    "release_date": {
                                        "type": "string"
                                    },

                                    "trend": {
                                        "type": "string"
                                    },

                                    "features": {
                                        "type": "string"
                                    },

                                    "reason": {
                                        "type": "string"
                                    },

                                    "source_name": {
                                        "type": "string"
                                    },

                                    "source_url": {
                                        "type": "string"
                                    },

                                    "verification_note": {
                                        "type": "string"
                                    }
                                },

                                "required": [
                                    "verified",
                                    "topic_match",
                                    "is_actual_track",
                                    "is_album_or_event_title",
                                    "artist",
                                    "song",
                                    "release_date",
                                    "trend",
                                    "features",
                                    "reason",
                                    "source_name",
                                    "source_url",
                                    "verification_note"
                                ],

                                "additionalProperties": False
                            }
                        }
                    },

                    "required": [
                        "candidates"
                    ],

                    "additionalProperties": False
                }
            }
        }
    )


    # =====================================================
    # JSON 변환
    # =====================================================

    raw_text = response.output_text or ""
    try:
        data = parse_music_json(raw_text)
    except ValueError as exc:
        print(
            f"[MUSIC_TREND JSON] attempt={_retry + 1}/3 "
            f"status={getattr(response, 'status', 'unknown')} "
            f"error={exc} "
            f"length={len(raw_text)} "
            f"preview={raw_text[:800]!r}",
            flush=True,
        )
        if _retry < 2:
            return get_latest_music_data(
                topic, _retry=_retry + 1, _collected=_collected
            )
        raise RuntimeError(
            "3번 검색했지만 정상적인 최신곡 JSON 결과를 받지 못했습니다. "
            "[MUSIC_TREND JSON] 로그에서 status, length, preview를 확인하세요."
        ) from exc


    # 실제 검색 후보 진단: 필터링 이전 데이터 확인
    raw_candidates = data.get("candidates", [])
    print(f"\n[MUSIC_TREND RAW] attempt={_retry + 1}/3, candidates={len(raw_candidates)}", flush=True)
    for index, item in enumerate(raw_candidates, 1):
        print(json.dumps({
            "index": index,
            "artist": item.get("artist"),
            "song": item.get("song"),
            "release_date": item.get("release_date"),
            "verified": item.get("verified"),
            "topic_match": item.get("topic_match"),
            "is_actual_track": item.get("is_actual_track"),
            "is_album_or_event_title": item.get("is_album_or_event_title"),
            "source_url": item.get("source_url"),
            "verification_note": item.get("verification_note"),
        }, ensure_ascii=False), flush=True)

    # =====================================================
    # 애플 음원 메타데이터 확인 후 후보 선정
    # =====================================================
    valid_candidates = list(_collected or [])
    used_artists = {_normalize_name(x["artist"]) for x in valid_candidates}
    used_songs = {(_normalize_name(x["artist"]), _normalize_name(x["song"]))
                  for x in valid_candidates}
    rejected = {}

    def reject(reason):
        rejected[reason] = rejected.get(reason, 0) + 1

    for item in data.get("candidates", []):
        if item.get("topic_match") is False:
            reject("topic_mismatch")
            continue
        if item.get("is_album_or_event_title") is True:
            reject("album_or_event")
            continue

        artist = str(item.get("artist") or "").strip()
        song = str(item.get("song") or "").strip()
        if not artist or not song:
            reject("empty_artist_or_song")
            continue
        if _normalize_name(artist) in used_artists:
            reject("duplicate_artist")
            continue

        # 주의: 모델이 출력한 release_date 와 verified 는 검증값으로 사용하지 않음.
        # 실제 Apple 카탈로그에서 아티스트/곡 제목을 매칭하고 날짜를 다시 받음.
        metadata, reason = verify_with_itunes(artist, song, six_months_ago, yesterday)
        if not metadata:
            reject(reason)
            print(f"[MUSIC_TREND SKIP] {artist} - {song}: {reason}", flush=True)
            continue

        artist_key = _normalize_name(metadata["artist"])
        song_key = (artist_key, _normalize_name(metadata["song"]))
        if artist_key in used_artists or song_key in used_songs:
            reject("duplicate_confirmed")
            continue

        used_artists.add(artist_key)
        used_songs.add(song_key)
        accepted = dict(item)
        accepted.update(metadata)  # 발매일과 링크는 카탈로그 데이터로 덮어씀
        accepted["verified"] = True
        accepted["is_actual_track"] = True
        accepted["verification_note"] = (
            "Apple iTunes catalog track/artist/date matched; "
            "remaster or re-release original date may need further review"
        )
        valid_candidates.append(accepted)
        print(f"[MUSIC_TREND ACCEPT] {metadata['artist']} - "
              f"{metadata['song']} ({metadata['release_date']})", flush=True)


    # =====================================================
    # 최신순 정렬
    # =====================================================

    valid_candidates.sort(
        key=lambda x: x["release_date"],
        reverse=True
    )


    # =====================================================
    # 최소 3개 확인
    # =====================================================

    print(
        f"[MUSIC_TREND] attempt={_retry + 1}/3, "
        f"returned={len(data.get('candidates', []))}, "
        f"valid_total={len(valid_candidates)}, rejected={rejected}",
        flush=True,
    )

    if len(valid_candidates) < 3:
        valid_candidates = supplement_from_apple_chart(
            topic, valid_candidates, six_months_ago, yesterday
        )
        valid_candidates.sort(key=lambda x: x["release_date"], reverse=True)

    if len(valid_candidates) < 3:
        if _retry < 2:
            return get_latest_music_data(
                topic,
                _retry=_retry + 1,
                _collected=valid_candidates,
            )
        raise RuntimeError(
            "최신곡 검색을 3회 시도했지만 조건에 맞는 서로 다른 "
            f"아티스트의 곡을 {len(valid_candidates)}개만 확보했습니다. "
            "[MUSIC_TREND SKIP] 및 rejected 로그를 확인하세요. "
            "기존 곡을 최신곡으로 바꿔 쓰지 않습니다."
        )


    # =====================================================
    # 최종 3개
    # =====================================================

    final_candidates = (
        valid_candidates[:3]
    )


    result = {

        "current_date": (
            today.isoformat()
        ),

        "allowed_release_range": {

            "from": (
                six_months_ago.isoformat()
            ),

            "to": (
                yesterday.isoformat()
            )
        },

        "trends": final_candidates
    }


    # =====================================================
    # 테스트용 출력
    # 나중에 정상 작동하면 삭제 가능
    # =====================================================

    print(
        "\n"
        "========== MUSIC_TREND 최신곡 검색 결과 =========="
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )

    print(
        "=================================================\n"
    )


    return result


# =========================================================
# MUSIC_TREND
# =========================================================

def block_music_trend(
    keyword=None,
    prev_type=None,
    context=None,
    language="ko"
):

    topic = (
        keyword.strip()
        if keyword
        and keyword.strip()
        else "K-POP"
    )


    # =====================================================
    # 최신 음악 검색
    # 웹 검색은 1번만 실행
    # =====================================================

    latest_music_data = (
        get_latest_music_data(
            topic
        )
    )


    latest_music_text = json.dumps(
        latest_music_data,
        ensure_ascii=False,
        indent=2
    )


    # =====================================================
    # 한국어
    # =====================================================

    if language == "ko":

        base_instruction = f"""
당신은 최신 음악 흐름을
쉽고 흥미롭게 설명하는
전문 라디오 DJ입니다.


이전 코너:

{prev_type}


이전 분위기:

{context}


오늘 MUSIC_TREND의 주제는

"{topic}"

입니다.


==================================================
웹 검색으로 확인한 최신 음악 데이터
==================================================

{latest_music_text}


==================================================
가장 중요한 대표곡 고정 규칙
==================================================

위 데이터의 trends 배열에는

이번 MUSIC_TREND에서 사용할
정확히 3개의 최신 아티스트와
최신곡이 들어 있습니다.


대본에서는 반드시

trends 배열의

artist
song
release_date

값을 그대로 사용하세요.


절대로 수정하거나
다른 이름으로 바꾸지 마세요.


절대 금지:

- 다른 아티스트 추가
- 새로운 대표곡 추가
- 다른 곡으로 교체
- 모델 기억에서 과거곡 가져오기
- 검색 결과에 없는 곡명 만들기
- 검색 결과에 없는 발매일 만들기
- 앨범명을 곡명으로 바꾸기
- 행사명을 곡명으로 바꾸기


대표 아티스트 3명/팀과
대표곡 3곡은 이미 결정되었습니다.


당신의 역할은

새로운 곡을 찾는 것이 아니라

이 3개의 최신곡을 바탕으로
최근 음악 흐름을
자연스럽게 설명하는 것입니다.


==================================================
사실성
==================================================

검색 데이터보다
모델의 기억을 우선하지 마세요.


trend
features
reason

값을 적극 활용하세요.


검색 데이터에서 확인되지 않은
세부 사실은 만들어내지 마세요.


특히

장르
악기
보컬 스타일
랩 스타일
곡 구조
프로덕션

등을 확실하지 않은 상태에서
임의로 만들어내지 마세요.


확인되지 않은 차트 순위도
작성하지 마세요.


"멜론 1위"
"Spotify 1위"
"Billboard 몇 위"

등을 임의로 생성하지 마세요.


==================================================
대본 전체 구성
==================================================

대본은 사진 속 음악 칼럼이나
라디오 원고처럼

정보가 충분하면서도
자연스럽게 이어지는

약 7~8개의 긴 호흡 문단으로
작성하세요.


실제 결과에는

번호
소제목
목차

를 출력하지 마세요.


==================================================
도입 문단
==================================================

첫 번째 문단에서는

최근 "{topic}" 음악 시장에서
어떤 변화가 나타나고 있는지

전체적인 분위기를 먼저 소개하세요.


바로 아티스트 이름을
줄줄이 나열하지 마세요.


최근 음악이

어떤 사운드
어떤 스타일
어떤 제작 방식

쪽으로 변화하고 있는지

2~4문장 정도로
자연스럽게 소개하세요.


==================================================
첫 번째 트렌드
==================================================

다음 문단은 자연스럽게

"첫 번째 트렌드는 ~입니다."

라는 방식으로 시작하세요.


latest_music_data의
첫 번째 trends 데이터를 사용하세요.


한 문단 안에서 자연스럽게

- 이 트렌드가 무엇인지
- 최근 왜 주목받는지
- 대표 아티스트
- 대표곡
- 실제 발매 시점
- 사운드 특징
- 보컬 또는 랩 특징
- 리듬
- 악기 또는 신스
- 편곡
- 프로덕션
- 왜 이 곡이 트렌드를 보여주는지

를 연결해서 설명하세요.


단순 정보 나열이 아니라

하나의 음악 이야기처럼
이어지게 작성하세요.


==================================================
두 번째 트렌드
==================================================

다음 문단에서는

"두 번째 트렌드는 ~입니다."

라고 자연스럽게 이어주세요.


latest_music_data의
두 번째 trends 데이터를 사용하세요.


첫 번째 트렌드와
어떤 점이 다른지를 보여주세요.


대표 아티스트와 대표곡을 소개하고

그 곡의 음악적 특징과
최근 음악 시장에서의 의미를

충분히 한 문단으로 설명하세요.


==================================================
세 번째 트렌드
==================================================

다음 문단에서는

"세 번째 트렌드는 ~입니다."

라고 자연스럽게 이어주세요.


latest_music_data의
세 번째 trends 데이터를 사용하세요.


앞의 두 트렌드와
겹치지 않는 특징을 중심으로 설명하세요.


대표 아티스트
대표곡
발매 시점
사운드
보컬
리듬
편곡
프로덕션

그리고

최근 음악 흐름과의 연결을

한 문단 안에서
자연스럽게 설명하세요.


==================================================
대표곡 심화 설명
==================================================

세 가지 트렌드를 모두 설명한 뒤에는

다음과 같은 문장으로
자연스럽게 연결하세요.


"이제 각 트렌드별 대표곡을
조금 더 깊이 살펴보겠습니다."


그 다음에는

대표곡 3개를
각각 별도의 한 문단으로 설명하세요.


==================================================
대표곡 1
==================================================

첫 번째 곡은

"먼저 [아티스트]의 '[곡명]'을 살펴보면"

처럼 자연스럽게 시작하세요.


앞에서 이야기한 내용을
그대로 반복하지 마세요.


검색 데이터로 확인 가능한 내용 중에서

- 전체적인 분위기
- 주요 사운드
- 악기 또는 신스
- 드럼
- 베이스
- 보컬
- 랩
- 곡 전개
- 편곡
- 프로덕션
- 감상 포인트
- 트렌드와의 연결

을 중심으로
조금 더 깊게 설명하세요.


==================================================
대표곡 2
==================================================

두 번째 대표곡도

별도의 한 문단으로 작성하세요.


첫 번째 곡과 비교했을 때

사운드
보컬
리듬
편곡

측면에서

어떤 차이가 있는지를
자연스럽게 보여주세요.


확인되지 않은 사실을
비교를 위해 새롭게 만들지 마세요.


==================================================
대표곡 3
==================================================

세 번째 대표곡도

별도의 한 문단으로 작성하세요.


앞의 두 곡과 다른
음악적 특징을 중심으로 설명하고

왜 현재 음악 흐름을
잘 보여주는 곡인지

자연스럽게 정리하세요.


==================================================
마지막 종합
==================================================

마지막 문단에서는

"이렇게 세 가지 트렌드를 종합해보면"

과 같은 자연스러운 흐름으로 시작하세요.


세 트렌드의

공통점
차이점

을 연결해서 설명하고


최근 "{topic}" 음악이

전체적으로 어떤 방향으로
변화하고 있는지 정리하세요.


마지막 문단에서

새로운 아티스트
새로운 곡

을 추가하지 마세요.


==================================================
음악 재생 표현 금지
==================================================

현재 실제 음악을
재생하는 기능은 없습니다.


따라서 다음 표현을
사용하지 마세요.


"이 곡 들어보시죠."

"듣고 오겠습니다."

"잘 듣고 오셨나요?"

"방금 들으신 곡은"

"첫 곡으로 만나보겠습니다."


음악을 재생하는 대신

사운드와 음악적 특징을
설명하는 방식으로 작성하세요.


==================================================
다른 코너와 구분
==================================================

MUSIC_TREND는

"지금 음악에서
어떤 변화가 나타나는가"

가 중심입니다.


특정 아티스트 한 명의
활동사를 길게 설명하지 마세요.

그것은 MUSIC_ARTIST입니다.


장르의 탄생과 역사를
길게 설명하지 마세요.

그것은 MUSIC_STORY입니다.


==================================================
문단과 분량
==================================================

전체 대본은

공백 포함 약 2,300~2,700자

정도로 작성하세요.


너무 짧게 작성하지 마세요.

너무 길게 작성하지도 마세요.


각 트렌드 설명은

약 250~350자 정도의
충분한 한 문단으로 작성하세요.


각 대표곡 상세 설명은

약 180~250자 정도의
한 문단으로 작성하세요.


같은 설명을 반복해서
분량을 채우지 마세요.


짧은 문장을
지나치게 많이 끊어 쓰지 마세요.


사진 속 음악 칼럼이나
라디오 음악 원고처럼

정보가 충분하면서도

한 문단씩 자연스럽게
읽히도록 작성하세요.


==================================================
문체
==================================================

- 자연스러운 라디오 DJ 구어체
- 음악 초보자도 쉽게 이해할 수 있게
- 너무 딱딱한 보고서 문체 금지
- 과도한 광고 표현 금지
- 번호 출력 금지
- 소제목 출력 금지
- 하나의 자연스러운 방송 원고


키워드:

"{topic}"
"""


    # =====================================================
    # 영어
    # =====================================================

    else:

        base_instruction = f"""
You are a professional radio DJ
introducing current music trends.

Today's topic is:

"{topic}"


Verified current music data:

{latest_music_text}


Use exactly the three artists and songs
inside the trends array.

Do not replace them.

Do not add another artist.

Do not add another song.

Do not use an album title
or event title as a song title.

Do not invent release dates.

Do not invent chart rankings.

Do not invent musical details
that are not supported by the data.


Structure the script as:

current overview

→ trend 1

→ trend 2

→ trend 3

→ deeper discussion of song 1

→ deeper discussion of song 2

→ deeper discussion of song 3

→ overall summary


Write approximately 7 to 8
natural paragraphs.

Do not output headings or numbers.

Do not pretend that music
is actually being played.

Write one continuous
radio-style script.
"""


    # =====================================================
    # 공통 프롬프트 생성
    # =====================================================

    prompt = build_block_prompt(
        base_instruction=base_instruction,
        block_name="MUSIC_TREND",
        keyword=keyword,
        prev_type=prev_type,
        context=context
    )


    # =====================================================
    # 대본 생성
    # 딱 1번만 호출
    # =====================================================

    response = client.chat.completions.create(
        model=SCRIPT_MODEL,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.2,

        max_tokens=3500
    )


    result = (
        response
        .choices[0]
        .message
        .content
        .strip()
    )


    return result


# =========================================================
# 단독 테스트
# =========================================================

if __name__ == "__main__":

    try:

        script = block_music_trend(
            keyword="K-POP",
            language="ko"
        )

        print(
            "\n"
            "================ MUSIC_TREND ================\n"
        )

        print(
            script
        )

    except Exception as e:

        print(
            "\n[MUSIC_TREND ERROR]"
        )

        print(
            str(e)
        )