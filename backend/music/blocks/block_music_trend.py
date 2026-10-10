import os
from dotenv import load_dotenv
from openai import OpenAI
from common.prompt_utils import build_block_prompt

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def block_music_trend(
    keyword=None,
    prev_type=None,
    context=None,
    language="ko"
):
    if language == "ko":
        topic = keyword.strip() if keyword and keyword.strip() else "최근 음악"

        base_instruction = f"""
당신은 최신 음악 흐름을 쉽고 흥미롭게 소개하는 전문 라디오 DJ입니다.

이전 코너는 {prev_type}이었고, 이런 분위기였습니다:
{context}

이제 [MUSIC_TREND] 코너를 진행해주세요.

오늘 다룰 음악 주제는 "{topic}"입니다.

이 코너의 목적은 특정 아티스트 한 명을 집중적으로 소개하거나
한 장르의 역사를 설명하는 것이 아닙니다.

"{topic}"과 관련하여 최근 음악에서 나타나는 여러 흐름을 소개하고,
각 흐름을 대표하는 아티스트와 곡을 함께 이야기하면서
청취자가 최근 음악이 어떻게 변화하고 있는지 이해할 수 있도록
하나의 자연스러운 라디오 이야기로 구성해주세요.

스크립트 흐름:

먼저 "{topic}"과 관련하여 최근 음악에서 어떤 변화와 분위기가
나타나고 있는지 자연스럽게 소개해주세요.

이후 서로 구분되는 3개의 음악 트렌드를 중심으로 이야기해주세요.

각 트렌드에서는 다음 내용을 충분히 포함해주세요.

- 어떤 음악적 흐름이 나타나고 있는지
- 이전 음악과 비교했을 때 어떤 점이 달라지고 있는지
- 왜 이런 스타일이 최근 주목받고 있는지
- 사운드, 보컬, 리듬, 장르 결합, 프로덕션 등의 음악적 특징
- 이 흐름을 잘 보여주는 대표적인 아티스트
- 이 흐름을 잘 보여주는 대표적인 곡
- 해당 아티스트와 곡이 왜 이 트렌드를 보여준다고 볼 수 있는지
- 해당 곡에서 주목할 만한 음악적 특징과 분위기

각 트렌드마다 아티스트와 곡을 단순하게 이름만 나열하지 마세요.

트렌드
→ 대표 아티스트
→ 대표곡
→ 곡의 음악적 특징
→ 해당 트렌드와의 연결

순서가 자연스럽게 느껴지도록 설명해주세요.

중요:
- 실제로 음악을 재생하거나 감상하는 기능이 있는 것처럼 말하지 마세요.
- "이 곡 들어보시죠", "듣고 오겠습니다", "잘 듣고 오셨나요?"
  등의 곡 재생을 전제로 한 표현은 사용하지 마세요.
- 대신 아티스트와 곡에 대한 음악적 이야기와 특징을 충분히 설명해주세요.
- 노래 가사를 길게 인용하거나 그대로 재현하지 마세요.

- 확인되지 않은 실시간 차트 순위나 수치를 사실처럼 만들어내지 마세요.
- 실제 최신 차트 데이터가 제공되지 않은 경우
  "현재 1위", "이번 주 빌보드 3위", "멜론 1위"
  등의 구체적인 순위를 임의로 작성하지 마세요.
- 확실하지 않은 경우
  "최근 주목받고 있는",
  "최근 많은 관심을 받고 있는",
  "최근 음악에서 자주 나타나는"
  등의 표현을 사용하세요.

- 반드시 "{topic}"을 중심 주제로 유지하세요.
- 특정 아티스트 한 명의 활동사나 전기를 지나치게 길게 설명하지 마세요.
  그것은 MUSIC_ARTIST 코너의 역할입니다.
- 특정 장르의 탄생과 역사를 중심으로 길게 설명하지 마세요.
  그것은 MUSIC_STORY 코너의 역할입니다.

마지막에는 지금까지 이야기한 3개의 트렌드를 자연스럽게 연결해서
"{topic}" 음악이 최근 어떤 방향으로 변화하고 있는지 정리해주세요.

분량:
- MUSIC_TREND 본문만 공백 포함 약 3,000자 내외로 작성하세요.
- 최소 2,500자 이상을 목표로 충분히 상세하게 작성하세요.
- 서로 구분되는 3개의 음악 트렌드를 다뤄주세요.
- 각 트렌드마다 관련 아티스트와 대표곡 이야기를 충분히 포함해주세요.
- 동일한 표현이나 내용을 반복해서 분량을 채우지 마세요.

문체:
- 실제 라디오 DJ가 청취자에게 음악 이야기를 들려주는 자연스러운 구어체
- 음악을 잘 모르는 청취자도 이해할 수 있도록 쉽게 설명
- 아티스트와 곡에 대한 이야기는 흥미롭고 구체적으로 설명
- 지나치게 딱딱한 분석문이나 보고서처럼 작성하지 마세요.
- 번호나 소제목을 출력하지 마세요.
- 하나의 자연스러운 라디오 방송 대본처럼 이어서 작성하세요.

키워드: {keyword}
"""

    else:
        topic = keyword.strip() if keyword and keyword.strip() else "recent music"

        base_instruction = f"""
You are a professional radio DJ introducing current music trends.

Today's topic is "{topic}".

Introduce three distinct recent musical trends related to this topic.

For each trend, explain:
- what the trend is
- why it is attracting attention
- its musical characteristics
- representative artists
- representative songs
- why those artists and songs reflect the trend

Do not pretend to actually play music.
Do not quote song lyrics at length.
Do not invent real-time chart rankings when current data has not been supplied.

Do not turn the segment into a biography of one artist.
Do not turn it into a long history of one genre.

End by summarizing how these three trends show
the current direction of "{topic}".

Write one continuous radio script without headings or numbered sections.
Aim for approximately 3,000 Korean-character equivalent length.
"""

    prompt = build_block_prompt(
        base_instruction=base_instruction,
        block_name="MUSIC_TREND",
        keyword=keyword,
        prev_type=prev_type,
        context=context
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4000,
    )

    result = response.choices[0].message.content.strip()

    if language == "ko" and len(result) < 2500:
        expand_prompt = f"""
아래 MUSIC_TREND 라디오 대본이 현재 너무 짧습니다.

기존 주제와 사실관계, 전체적인 방향은 유지하면서
공백 포함 약 3,000자 내외가 되도록 자연스럽게 확장해주세요.

오늘의 주제는 "{topic}"입니다.

특히 다음 내용을 더 풍부하게 작성해주세요.

- 서로 구분되는 3개의 최근 음악적 흐름
- 각 흐름이 주목받는 이유
- 각 흐름의 사운드, 보컬, 리듬, 장르 결합, 프로덕션 특징
- 각 트렌드를 대표하는 아티스트
- 각 트렌드를 보여주는 대표곡
- 해당 아티스트와 곡이 그 트렌드와 연결되는 이유
- 각 곡에서 주목할 만한 음악적 특징
- 3개의 트렌드를 종합한 최근 음악 변화

음악을 실제로 재생하거나 감상하는 것처럼 작성하지 마세요.

"이 곡 들어보시죠",
"듣고 오겠습니다",
"잘 듣고 오셨나요?"

등의 표현은 사용하지 마세요.

같은 표현이나 내용을 반복해서 분량을 늘리지 마세요.
확인되지 않은 차트 순위나 수치를 새롭게 만들어내지 마세요.
특정 아티스트 한 명의 전기처럼 작성하지 마세요.
장르의 역사 설명이 중심이 되지 않도록 해주세요.

번호나 소제목 없이
하나의 자연스러운 라디오 DJ 방송 대본으로 작성해주세요.

기존 대본:
{result}
"""

        retry = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": expand_prompt}
            ],
            temperature=0.7,
            max_tokens=4000,
        )

        result = retry.choices[0].message.content.strip()

    return result