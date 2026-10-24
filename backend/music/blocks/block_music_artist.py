import os
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

    if language == "ko":
        mood_keyword = (
            keyword.strip()
            if keyword and keyword.strip()
            else "편안한 음악"
        )

        prompt = f"""
당신은 음악 전문 AI입니다.

사용자가 오늘 듣고 싶은 분위기, 감정 또는 상황은 다음과 같습니다.

"{mood_keyword}"

이 분위기와 잘 어울리는
실제로 존재하는 유명 아티스트 한 명을 선택해주세요.

예시:

"봄"
→ 밝고 따뜻한 봄 분위기에 잘 어울리는 실제 아티스트

"가을, 드라이브"
→ 가을의 감성과 드라이브 분위기에 잘 어울리는 실제 아티스트

"위로, 새벽"
→ 조용한 새벽과 위로가 필요한 분위기에 어울리는 실제 아티스트

"설렘"
→ 밝고 설레는 감정을 표현하는 음악과 잘 어울리는 실제 아티스트


반드시 지켜야 할 조건:

- 반드시 실제 존재하는 아티스트만 선택하세요.
- 존재하지 않는 아티스트를 만들어내지 마세요.
- "{mood_keyword}" 자체를 아티스트 이름처럼 사용하지 마세요.
- 한국 또는 해외 아티스트 모두 가능합니다.
- 사용자의 분위기, 감정, 상황과 음악적으로 잘 어울리는 아티스트를 선택하세요.
- 곡명이나 앨범명은 출력하지 마세요.
- 선택 이유도 출력하지 마세요.
- 반드시 아티스트 이름 하나만 출력하세요.
"""

    else:
        mood_keyword = (
            keyword.strip()
            if keyword and keyword.strip()
            else "relaxing music"
        )

        prompt = f"""
You are a music expert.

The listener wants music for this mood, emotion, or situation:

"{mood_keyword}"

Choose one real and well-known artist
whose music fits this mood or situation.

Rules:

- The artist must actually exist.
- Never invent an artist.
- Do not use the keyword itself as an artist name.
- Choose only one artist.
- Do not output songs or albums.
- Do not explain your choice.
- Return only the artist's name.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
    )

    return response.choices[0].message.content.strip()


# =========================================================
# MUSIC_ARTIST
# =========================================================
def block_music_artist(
    keyword=None,
    prev_type=None,
    context=None,
    language="ko"
):

    # 사용자가 입력한 분위기 / 감정 / 상황을 기준으로
    # 실제 아티스트 한 명 선택
    selected_artist = pick_artist_by_llm(
        keyword=keyword,
        language=language
    )

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