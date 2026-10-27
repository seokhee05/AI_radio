import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from common.prompt_utils import build_block_prompt

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =========================================================
# 분위기 / 감정 / 상황 키워드에 맞는 실제 아티스트 선택
#
# 예)
# "가을, 드라이브" → 노라 존스 / 이소라 / 잔나비 등
# "새벽, 위로" → 아이유 / 정승환 등
# =========================================================


def pick_artist_by_llm(keyword=None, language="ko"):

    mood_keyword = (
        keyword.strip()
        if keyword and keyword.strip()
        else ("편안한 음악" if language == "ko" else "relaxing music")
    )

    if language == "ko":
        prompt = f"""
당신은 국내외 음악의 가사, 주제, 아티스트,
장르에 정통한 전문 음악 큐레이터입니다.

사용자가 입력한 키워드는 다음과 같습니다.

"{mood_keyword}"

당신의 목표는 키워드와 가장 직접적으로
관련된 실제 노래를 가진 아티스트 한 명을
정확하게 선정하는 것입니다.

==================================================
1. 가장 중요한 원칙
==================================================

아티스트의 유명세나 전체적인 음악 분위기가 아니라,
실제 발표한 노래와 키워드의 관련성을 기준으로
아티스트를 선택하세요.

예를 들어 키워드가 "첫사랑"이라면,

단순히 사랑 노래를 많이 부르거나
감성적인 발라드를 부르는 가수를 선택하지 마세요.

실제로 첫사랑의 설렘, 풋풋한 감정,
처음 좋아했던 사람에 대한 기억 등을
직접적으로 표현한 곡이 있는 아티스트를
우선적으로 선택해야 합니다.

"감성적인 가수이므로 첫사랑과 어울린다"는
선정 근거로 인정하지 않습니다.

==================================================
2. 노래를 먼저 선택하세요
==================================================

아티스트를 먼저 떠올리지 마세요.

반드시 아래 순서로 판단하세요.

STEP 1.
키워드 "{mood_keyword}"가 의미하는
핵심 주제와 감정, 상황을 분석합니다.

STEP 2.
키워드와 직접 관련된 실제 발표곡을
최소 5곡 이상 후보로 고려합니다.

STEP 3.
각 노래의 실제 주제와 가사 내용을 기준으로
키워드와의 관련성을 비교합니다.

STEP 4.
가장 관련성이 높은 노래를 선정합니다.

STEP 5.
그 노래의 실제 아티스트를 선택합니다.

단순히 제목에 키워드가 들어간다는 이유만으로
관련성이 높다고 판단해서는 안 됩니다.

실제 곡의 주제와 내용이 키워드와
연결되는지를 우선적으로 판단하세요.

==================================================
3. 관련성 평가 기준
==================================================

후보 곡과 아티스트를 아래 기준으로 평가하세요.

A. 주제 직접성: 40점
- 곡이 키워드 자체를 중심 주제로 다루는가?
- 키워드와 직접 연결되는 이야기가 있는가?

B. 가사 및 메시지: 30점
- 실제 가사와 메시지가 키워드와 일치하는가?
- 키워드와 관련된 감정이나 상황이 구체적인가?

C. 음악적 분위기: 20점
- 곡의 멜로디와 분위기가 키워드에 어울리는가?
- 청취자가 키워드의 감정을 느낄 수 있는가?

D. 아티스트 적합성: 10점
- 아티스트를 해당 키워드와 연결해
  자연스럽고 구체적인 이야기를 할 수 있는가?

주제와 가사 관련성을 가장 중요하게 평가하세요.

유명세와 대중적 인지도는 점수에 포함하지 마세요.

==================================================
4. 반드시 피해야 할 선정 방식
==================================================

다음과 같은 방식으로 아티스트를 선택하지 마세요.

- 첫사랑 → 단순히 감성적인 발라드 가수
- 바람 → 단순히 목소리가 부드러운 가수
- 여름 → 단순히 밝고 경쾌한 음악을 하는 가수
- 이별 → 단순히 슬픈 노래를 많이 부르는 가수
- 여행 → 단순히 편안한 분위기의 음악을 하는 가수

반드시 관련된 실제 노래가 있어야 합니다.

특정 키워드와 직접 관련된 곡이 있다면,
분위기만 유사한 유명 아티스트보다
그 곡을 발표한 아티스트를 우선하세요.

==================================================
5. 아티스트 다양성
==================================================

항상 대중적으로 유명한 아티스트만
선택하는 편향을 피하세요.

아이유, 이소라, 김동률, 이승철,
노라 존스 등의 아티스트가
자동적으로 우선 선택되지 않도록 주의하세요.

이 아티스트들도 후보로 고려할 수 있지만,
키워드와의 실제 음악적 관련성이
다른 후보보다 높을 때만 선택하세요.

국내외 인디, 포크, 발라드, 록, 팝,
R&B, 힙합 등 다양한 장르를 고려하세요.

신인, 인디, 중견 아티스트를 포함해
폭넓은 후보를 비교하세요.

단, 다양성을 위해 관련성이 떨어지는
아티스트를 억지로 선택하지 마세요.

==================================================
6. 최종 자체 검토
==================================================

최종 아티스트를 결정하기 전에
다음 질문을 스스로 확인하세요.

1. 이 아티스트에게 키워드와 직접 관련된
   실제 발표곡이 존재하는가?

2. 그 노래가 키워드와 관련된 이유를
   구체적으로 설명할 수 있는가?

3. 단순히 음악 분위기가 비슷하다는 이유로
   선택한 것은 아닌가?

4. 더 직접적으로 관련된 실제 곡을 가진
   다른 아티스트가 있지는 않은가?

5. 곡과 아티스트의 관계를 확실하게 알고 있는가?

확신이 낮은 후보는 제외하고
더 신뢰할 수 있는 후보를 선택하세요.

==================================================
7. 사실 정확성
==================================================

- 실존 아티스트만 선정하세요.
- 실제 발표된 곡만 기준으로 삼으세요.
- 곡명과 아티스트를 혼동하지 마세요.
- 다른 가수의 곡을 잘못 연결하지 마세요.
- 존재하지 않는 음악을 만들어내지 마세요.
- 음악적 관련성이 불분명한 후보는 제외하세요.

==================================================
8. 최종 출력
==================================================

내부적으로 여러 곡과 아티스트를 비교한 뒤
키워드에 가장 적합한 아티스트 한 명을 선택하세요.

최종 출력에는 아티스트 이름만 작성하세요.

노래 제목, 점수, 선정 이유, 설명, 번호는
절대 출력하지 마세요.

반드시 아티스트 이름 하나만 반환하세요.
"""

    else:
        prompt = f"""
You are an expert international music curator.

User keyword: "{mood_keyword}"

Choose ONE real artist whose actual released music
has the strongest thematic connection to the keyword.

IMPORTANT:
Do not select an artist merely because their music
has a similar emotional atmosphere.

Selection process:

1. Analyze the literal and emotional meaning
   of the keyword.

2. Consider at least five real released songs
   related to the keyword.

3. Compare candidates using these criteria:

   - Direct thematic relevance: 40%
   - Lyrical and message relevance: 30%
   - Musical atmosphere: 20%
   - Artist suitability: 10%

4. Prioritize songs that directly address
   the keyword's theme or situation.

5. Identify the actual performer of the
   strongest matching song.

6. Consider artists across genres, generations
   and popularity levels.

7. Do not automatically prefer famous artists.

8. Reject candidates based only on vague
   similarity, sentiment, or vocal style.

9. Never invent artists, songs, or relationships.

10. If uncertain, prefer well-established
    information over speculation.

Return ONLY the artist's name.
Do not include songs, scores, or explanations.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict keyword-based music curator. "
                    "Choose artists based on actual songs with direct "
                    "thematic relevance, not generic emotional similarity. "
                    "Popularity does not determine suitability. "
                    "Never fabricate music information."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=100,
    )
    

    return response.choices[0].message.content.strip()



def classify_music_keyword(keyword, language="ko"):
    """
    artist: 실제 아티스트 이름
    theme: 계절, 감정, 상황, 일반 주제
    """

    keyword = (keyword or "").strip()

    if not keyword:
        return "theme"

    # 자주 사용하는 아티스트는 바로 처리
    known_artists = {
        "아이유", "IU", "방탄소년단", "BTS",
        "잔나비", "정준일", "태연", "뉴진스",
        "BLACKPINK", "블랙핑크", "데이식스",
    }

    if keyword in known_artists:
        return "artist"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
당신은 음악 라디오의 키워드 분류기입니다.

사용자 입력을 정확히 두 가지로 분류하세요.

artist:
실제 가수, 밴드, 음악 그룹, 아티스트 이름

theme:
계절, 감정, 상황, 분위기, 음악 주제

예시:
아이유 -> artist
방탄소년단 -> artist
정준일 -> artist
가을 -> theme
여름 -> theme
첫사랑 -> theme
이별 -> theme
드라이브 -> theme
위로 -> theme
가을밤 -> theme

아티스트임이 확실하지 않으면 theme로 분류하세요.

반드시 JSON으로만 출력하세요.
{"type": "artist"} 또는 {"type": "theme"}
"""
            },
            {
                "role": "user",
                "content": keyword
            }
        ],
        temperature=0,
        response_format={"type": "json_object"},
        max_tokens=50,
    )

    try:
        result = json.loads(
            response.choices[0].message.content
        )

        return (
            "artist"
            if result.get("type") == "artist"
            else "theme"
        )

    except (ValueError, TypeError):
        return "theme"


def generate_theme_music_script(
    keyword,
    prev_type=None,
    context=None,
    language="ko"
):
    if language == "ko":
        instruction = f"""
당신은 자연스럽고 매력적인 한국어 음악 라디오 DJ입니다.

오늘의 음악 라디오 주제는 "{keyword}"입니다.

이것은 특정 가수의 일대기를 소개하는 코너가 아닙니다.
사용자의 키워드에 맞는 노래와 이야기를 들려주는 코너입니다.

[핵심 규칙]

1. "{keyword}"를 대본 전체의 중심 주제로 유지하세요.

2. 키워드가 계절이라면 그 계절의 분위기,
   날씨, 풍경, 추억, 어울리는 음악을 다룹니다.

3. 키워드가 감정이라면 그 감정이 느껴지는
   상황과 경험, 관련된 음악 이야기를 다룹니다.

4. 키워드가 첫사랑이라면 첫사랑의 설렘,
   기억, 그리움 등을 음악과 연결합니다.

5. 키워드가 드라이브라면 이동하는 풍경,
   시간대와 분위기에 어울리는 음악을 소개합니다.

[노래 추천]

- 키워드에 적합한 실제 노래 2~3곡을 소개하세요.
- 각 곡의 정확한 아티스트와 제목을 사용하세요.
- 단순히 분위기가 비슷하다는 설명을 반복하지 마세요.
- 각 곡이 키워드와 연결되는 구체적인 이유를 설명하세요.
- 존재 여부가 불확실한 곡은 소개하지 마세요.
- 곡을 소개하더라도 한 아티스트의 일대기로
  주제가 바뀌지 않도록 하세요.

[대본 구성]

첫 부분:
오늘의 주제를 자연스럽고 흥미롭게 소개합니다.

중간 부분:
키워드와 관련된 감정, 상황, 경험을 이야기하고
실제 음악 2~3곡을 자연스럽게 소개합니다.

후반 부분:
앞서 소개한 곡들을 통해 느낄 수 있는
공통된 감정과 음악적 의미를 연결합니다.

마지막 부분:
오늘의 키워드를 중심으로 따뜻하게 마무리합니다.

[문체]

- 자연스럽고 편안한 라디오 DJ 말투
- 공백 포함 약 2,700~3,200자
- 7~9개 문단
- 같은 표현 반복 금지
- 번호와 소제목 출력 금지
- 과장하거나 확인되지 않은 음악 정보 생성 금지
- 실제 곡 재생을 암시하는 멘트 금지
- 별도의 오프닝이나 클로징 코너를 만들지 마세요.

이전 코너: {prev_type or "없음"}
이전 분위기: {str(context or "없음")[:400]}

대본 본문만 출력하세요.
"""
    else:
        instruction = f"""
You are a professional music radio DJ.

The theme is "{keyword}".

Write a natural radio narrative centered on this theme.
Introduce 2-3 real, relevant songs and explain their
connection to the theme.

Do not change the main topic into an artist biography.
Do not invent songs or facts.
Do not pretend music has been played.

Write 7-9 connected paragraphs.
Output only the radio script.

Previous segment: {prev_type or "none"}
Previous context: {str(context or "none")[:400]}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": instruction}
        ],
        temperature=0.6,
        max_tokens=4000,
    )

    result = response.choices[0].message.content.strip()

    if language == "ko" and len(result) < 2500:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"""
다음 음악 라디오 대본을 공백 포함
2,700~3,200자 분량으로 자연스럽게 보완하세요.

중심 주제는 "{keyword}"입니다.

원문의 실제 노래와 아티스트를 유지하고,
주제에 대한 구체적인 이야기와 음악적 설명을
추가하세요.

불확실한 곡명이나 사실을 만들지 마세요.
같은 표현을 반복하지 마세요.
본문만 출력하세요.

원문:
{result}
"""
                }
            ],
            temperature=0.4,
            max_tokens=4000,
        )

        result = response.choices[0].message.content.strip()

    return result



# =========================================================
# MUSIC_ARTIST
# =========================================================
def block_music_artist(
    keyword=None,
    prev_type=None,
    context=None,
    language="ko"
):

    keyword = (keyword or "").strip()

    # 1. 키워드 종류 구분
    keyword_type = classify_music_keyword(
        keyword,
        language
    )

    print(f"🎵 입력 키워드: {keyword}")
    print(f"🎵 키워드 종류: {keyword_type}")

    # 2. 계절·감정·상황 키워드
    if keyword_type == "theme":
        return generate_theme_music_script(
            keyword=keyword,
            prev_type=prev_type,
            context=context,
            language=language
        )

    # 3. 아티스트 이름이면 입력한 이름 그대로 사용
    selected_artist = keyword

    print(f"🎤 선택된 아티스트: {selected_artist}")

    # =====================================================
    # 한국어
    # =====================================================
    if language == "ko":

        base_instruction = f"""
당신은 음악 전문 지식을 갖춘
따뜻하고 감성적인 라디오 DJ입니다.

이전 코너는 {prev_type}이었고,
이런 분위기였습니다:

{context}

이제 [MUSIC_ARTIST] 코너를 진행해주세요.

오늘 집중 조명할 아티스트는
"{selected_artist}"입니다.


반드시 지켜야 할 조건:

- "{selected_artist}"를 처음부터 끝까지 메인 주제로 유지하세요.
- 다른 아티스트를 메인 아티스트로 변경하지 마세요.
- 다른 아티스트는 비교나 협업 등의 맥락에서
  필요한 경우에만 짧게 언급하세요.

- 확인되지 않은 곡명, 앨범명, 발매일,
  수상 기록, 활동 이력을 임의로 만들어내지 마세요.

- 확실하지 않은 사실은
  구체적인 날짜나 수치로 단정하지 마세요.

- 사용자 키워드 "{keyword}"는 아티스트 선택의 기준으로 활용하되,
  코너 첫 1~2문장에서는 오늘의 분위기와 아티스트를
  자연스럽게 연결하여 소개해주세요.

- 예를 들어 키워드가 "가을, 드라이브"이고
  선택된 아티스트가 "이소라"라면,

  "오늘의 아티스트 코너에서는 특별한 가을의 정취와
  드라이브에 잘 어울리는 이소라를 소개해드리려고 합니다."

  처럼 자연스럽게 시작할 수 있습니다.

- 첫 소개 이후에는 "{keyword}"를 반복해서 언급하지 말고,
  "{selected_artist}"의 음악적 특징과 활동 이야기에 집중해주세요.

- 앨범과 대표곡의 관계를 정확하게 작성하세요.

- 특정 곡이 특정 앨범의 수록곡이라고
  확실하지 않은 경우
  앨범과 곡을 임의로 연결하지 마세요.

- 발매 연도, 앨범명, 수록곡 관계가 확실하지 않은 경우에는
  불확실한 세부 정보는 생략하고
  음악적 특징 중심으로 설명하세요.

- 실제 음악을 재생하는 기능이 있는 것처럼
  표현하지 마세요.

- 노래 가사를 길게 인용하거나
  그대로 재현하지 마세요.


==================================================
1. 아티스트 소개
==================================================

코너의 첫 문장에서는
사용자가 입력한 분위기 "{keyword}"와
"{selected_artist}"를 자연스럽게 연결하여 소개해주세요.

예를 들어

"오늘의 아티스트 코너에서는
특별한 가을의 정취와 드라이브에 잘 어울리는
이소라를 소개해드리려고 합니다."

처럼 실제 라디오 DJ가 오늘의 분위기에 맞는
아티스트를 추천하는 느낌으로 시작해주세요.

그다음 "{selected_artist}"가 어떤 아티스트인지
기본적인 특징과 음악적 개성을 자연스럽게 설명해주세요.

초기 활동이나 대표적인 음악적 배경도
필요한 경우 간단하게 포함할 수 있습니다.

너무 긴 출생 정보, 학력, 사생활 등은 나열하지 말고
음악과 관련된 내용에 집중해주세요.


==================================================
2. 음악적 특징
==================================================

"{selected_artist}"만의 음악적 특징을
충분히 이야기해주세요.

다음 요소 가운데
실제로 해당 아티스트에게 중요한 내용을 골라 설명해주세요.

- 보컬
- 음색
- 사운드
- 곡의 분위기
- 감정 표현 방식
- 리듬
- 악기 구성
- 편곡
- 프로덕션
- 음악을 전달하는 방식

단순히

"목소리가 좋다"
"감성적이다"

처럼 추상적으로 끝내지 말고,

왜 그런 분위기가 느껴지는지
음악적인 요소를 함께 설명해주세요.


==================================================
3. 활동 / 스타일 변화
==================================================

"{selected_artist}"의 초기 활동부터 이후까지
음악 스타일과 이미지가 어떻게 변화해왔는지
자연스럽게 이야기해주세요.

초기 음악에서는 어떤 특징이 있었고,
시간이 지나면서

- 사운드
- 장르
- 보컬 표현
- 이미지
- 음악적 방향

등이 어떻게 달라졌는지 설명해주세요.

연도와 활동을 단순하게 나열하지 말고,

"초기에는 이런 음악적 특징을 보여주었지만,
이후에는 이런 방향으로 변화했다"

라는 흐름이 느껴지도록 작성해주세요.


==================================================
4. 앨범 · 대표곡
==================================================

"{selected_artist}"의
대표적인 앨범과 대표곡을 소개해주세요.

앨범명과 수록곡의 관계는
정확하게 구분해주세요.

특정 곡이 어떤 앨범에 수록되었다고
확실하게 알고 있는 경우에만
앨범과 곡을 연결해서 설명해주세요.

확실하지 않은 경우에는
앨범과 대표곡을 각각 별도로 소개하고,
잘못된 수록 관계를 만들어내지 마세요.

대표곡은 실제 존재하며 널리 알려진 곡 중
전체적으로 2~3곡 정도 선정해주세요.

각 곡이 어떤 분위기와 특징을 가지고 있는지,
청취자가 어떤 부분을 집중해서 들으면 좋은지
감상 포인트도 설명해주세요.


==================================================
5. 대표곡 이야기
==================================================

대표곡 2~3곡 각각에 대해
음악적 특징과 감상 포인트를 충분히 설명해주세요.

각 곡에서는 다음 내용을 자연스럽게 포함해주세요.

- 곡의 전체적인 분위기
- 사운드
- 보컬 표현
- 리듬
- 악기 구성
- 편곡
- 프로덕션 특징
- 청취자가 주목해서 들을 만한 부분
- 이 곡이 "{selected_artist}"의 음악 세계에서 가지는 의미


대표곡마다 같은 설명을 반복하지 마세요.

한 곡에서는 보컬이 돋보인다면,
다른 곡에서는 사운드나 편곡,
또 다른 곡에서는 음악 스타일의 변화가
드러날 수 있도록 구성해주세요.


곡을 실제로 재생하는 기능이 있는 것처럼
표현하지 마세요.

다음과 같은 표현은 사용하지 마세요.

"이 곡 함께 들어보시죠."

"듣고 오겠습니다."

"잠시 감상해볼까요?"

"잘 듣고 오셨나요?"

"방금 들으신 곡은..."


대신 다음과 같이
자연스러운 DJ 연결 멘트를 사용해주세요.

"이 곡에서 특히 주목할 부분은..."

"이 곡을 살펴보면
{selected_artist}의 음악적 특징이 잘 드러나는데요."

"또 다른 대표곡에서는
조금 다른 매력을 발견할 수 있습니다."

"앞선 곡과 비교하면
이 곡에서는 조금 다른 음악적 방향이 느껴집니다."


==================================================
6. 아티스트의 음악적 매력
==================================================

마지막에는 지금까지 이야기한 내용을 바탕으로

"{selected_artist}"만의 음악적 매력과
음악적 의미를 자연스럽게 정리해주세요.

다음 내용을 종합해주세요.

- 아티스트만의 음악적 개성
- 보컬과 사운드의 특징
- 활동 과정에서 나타난 변화
- 대표곡에서 드러나는 음악적 특징
- 사람들이 이 아티스트의 음악에서 느낄 수 있는 매력

새로운 내용을 갑자기 추가하기보다
앞에서 이야기한 내용을 자연스럽게 정리하며
코너를 마무리해주세요.


==================================================
코너 구성 관련 중요 조건
==================================================

MUSIC_ARTIST는 반드시 다음 6단계 내용을
자연스럽게 포함해야 합니다.

아티스트 소개
→ 음악적 특징
→ 활동 / 스타일 변화
→ 앨범 · 대표곡
→ 대표곡 이야기
→ 아티스트의 음악적 매력


하지만 실제 출력에서는

"아티스트 소개"
"음악적 특징"
"대표곡 이야기"

같은 제목을 출력하지 마세요.

번호나 소제목 없이
하나의 자연스러운 라디오 방송 대본처럼
이어지도록 작성해주세요.

오프닝이나 클로징 역할을 대신하지 마세요.

다음 코너를 임의로 예고하지 마세요.

예를 들어

"다음 코너에서는..."
"다음 아티스트를 만나보겠습니다."

같은 표현은 사용하지 마세요.


==================================================
분량
==================================================

- MUSIC_ARTIST 본문만 공백 포함 약 3,000자 내외로 작성하세요.
- 최소 2,500자 이상을 목표로 작성하세요.
- 같은 내용을 반복해서 분량을 채우지 마세요.

다음 내용을 균형 있게 활용해주세요.

아티스트 소개
+ 음악적 특징
+ 활동 / 스타일 변화
+ 앨범 · 대표곡
+ 대표곡 2~3곡의 음악적 특징과 감상 포인트
+ 아티스트의 음악적 매력


==================================================
문체
==================================================

- 실제 라디오 DJ가 이야기하는 자연스러운 구어체
- 따뜻하고 친근한 분위기
- 음악을 잘 모르는 청취자도 이해할 수 있는 설명
- 지나치게 딱딱한 분석문이나 백과사전식 문체 금지
- 지나치게 과장된 광고성 표현 금지
- 번호, 목록, 소제목 출력 금지
- 하나의 자연스러운 라디오 대본처럼 작성


선택된 아티스트: {selected_artist}
"""

    # =====================================================
    # 영어
    # =====================================================
    else:

        base_instruction = f"""
You are a knowledgeable and warm radio DJ.

The selected artist is:

"{selected_artist}"

Present the MUSIC_ARTIST segment
with "{selected_artist}" as the central subject.

The listener originally requested this mood or situation:

"{keyword}"

Use that keyword only as the basis for selecting the artist.
Do not repeatedly discuss the keyword in the radio script.

The segment must naturally cover these six areas:

1. Artist introduction
2. Musical characteristics
3. Career and stylistic development
4. Albums and representative songs
5. Detailed discussion of 2–3 representative songs
6. Summary of the artist's musical appeal

Introduce the artist by focusing on their musical identity.

Explain their vocal style, sound, mood,
emotional expression, instrumentation,
arrangement, and production where relevant.

Describe how the artist's musical style
or image developed from earlier work to later work.

Discuss notable albums and representative songs.

Choose approximately 2–3 real,
well-established representative songs.

For each song, explain:

- overall mood
- sound
- vocal characteristics
- rhythm
- instrumentation
- arrangement
- production
- listening points
- its meaning within the artist's musical career

Only connect a song to a specific album
when you are confident that the relationship is correct.

If uncertain, discuss the album and song separately.

Do not pretend that songs are actually being played.

Do not say:

"Let's listen to this song."
"We'll listen and come back."
"Did you enjoy the song?"

Do not invent songs, albums,
release dates, collaborations,
awards, or career information.

Do not present uncertain recent information as fact.

Do not turn another artist into the main subject.

Do not announce the next radio segment.

End by naturally summarizing
"{selected_artist}"'s musical identity and appeal.

Do not output headings or numbered sections.

Write one continuous radio script.

Aim for approximately 3,000 Korean-character
equivalent length.
"""


    # =====================================================
    # 공통 프롬프트 생성
    # =====================================================
    prompt = build_block_prompt(
        base_instruction=base_instruction,
        block_name="MUSIC_ARTIST",
        keyword=keyword,
        prev_type=prev_type,
        context=context
    )


    # =====================================================
    # 1차 생성
    # =====================================================
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.6,
        max_tokens=4000,
    )

    result = response.choices[0].message.content.strip()


    # =====================================================
    # 한국어 결과가 2500자 미만이면 한 번 확장
    # =====================================================
    if language == "ko" and len(result) < 2500:

        expand_prompt = f"""
아래 MUSIC_ARTIST 라디오 대본이 너무 짧습니다.

선택된 아티스트는

"{selected_artist}"

입니다.

기존 사실관계와 아티스트,
전체 흐름을 그대로 유지하면서

공백 포함 약 3,000자 내외가 되도록
자연스럽게 확장해주세요.


반드시 다음 6가지 내용이
균형 있게 포함되도록 해주세요.

1. 아티스트 소개
- 아티스트의 기본적인 특징과 음악적 개성

2. 음악적 특징
- 보컬
- 사운드
- 분위기
- 음악 표현 방식

3. 활동 / 스타일 변화
- 초기 활동부터 이후까지
  음악 스타일과 이미지의 변화

4. 앨범 · 대표곡
- 주요 앨범과 대표곡 소개
- 앨범과 곡의 수록 관계가 확실한 경우에만 연결

5. 대표곡 이야기
- 실제 존재하는 대표곡 2~3곡
- 각 곡의 분위기
- 사운드
- 보컬
- 리듬
- 편곡
- 프로덕션
- 감상 포인트
- 해당 곡이 아티스트에게 가지는 의미

6. 아티스트의 음악적 매력
- 지금까지의 내용을 종합한
  "{selected_artist}"만의 음악적 매력과 의미


사용자 키워드 "{keyword}"는
아티스트를 선택하기 위한 기준으로만 사용하세요.

대본 안에서는 해당 키워드나 상황 설명을
반복하지 마세요.


실제로 음악을 재생하는 것처럼
표현하지 마세요.

다음 표현은 사용하지 마세요.

"이 곡 들어보시죠."
"듣고 오겠습니다."
"잘 듣고 오셨나요?"
"방금 들으신 곡은..."


존재하지 않는 곡이나 앨범,
활동, 협업, 수상 기록을
새롭게 만들어내지 마세요.

확실하지 않은 최신 활동이나 신곡을
임의로 추가하지 마세요.

특정 곡이 특정 앨범의 수록곡이라고
확실하지 않다면 임의로 연결하지 마세요.

같은 내용을 반복해서
분량을 늘리지 마세요.

다음 코너를 임의로 예고하지 마세요.

실제 결과에서는 번호나 소제목을 출력하지 말고,
하나의 자연스러운 라디오 DJ 대본으로 작성해주세요.


기존 대본:

{result}
"""

        retry = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": expand_prompt
                }
            ],
            temperature=0.6,
            max_tokens=4000,
        )

        result = retry.choices[0].message.content.strip()


    return result


# =========================================================
# 단독 실행 테스트
# =========================================================
if __name__ == "__main__":

    script = block_music_artist(
        keyword="가을, 드라이브",
        language="ko"
    )

    print(script)