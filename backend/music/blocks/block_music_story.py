import os
import random
from dotenv import load_dotenv
from openai import OpenAI
from common.prompt_utils import build_block_prompt

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def block_music_story(
    keyword=None,
    prev_type=None,
    context=None,
    language="ko"
):
    genres_ko = [
        "재즈",
        "록",
        "EDM",
        "발라드",
        "힙합",
        "인디",
        "R&B",
        "소울",
        "펑크",
        "디스코"
    ]

    genres_en = [
        "Jazz",
        "Rock",
        "EDM",
        "Ballad",
        "Hip-hop",
        "Indie",
        "R&B",
        "Soul",
        "Funk",
        "Disco"
    ]

    if language == "ko":
        selected_genre = (
            keyword.strip()
            if keyword and keyword.strip()
            else random.choice(genres_ko)
        )

        base_instruction = f"""
당신은 음악 전문 지식을 갖춘 감성적인 라디오 DJ입니다.

이전 코너는 {prev_type}이었고, 이런 분위기였습니다:
{context}

이제 [MUSIC_STORY] 코너를 진행해주세요.

오늘 이야기할 음악 장르는 "{selected_genre}"입니다.

이 코너는 "{selected_genre}" 장르의 탄생부터 현재까지의 변화를
시간의 흐름에 따라 들려주는 음악 이야기 코너입니다.

단순히 장르의 특징만 설명하는 것이 아니라,

탄생 배경
→ 초기의 모습
→ 시대에 따른 변화
→ 다른 음악과의 결합 및 확장
→ 오늘날의 모습

순서가 자연스럽게 느껴지도록 하나의 이야기처럼 구성해주세요.

청취자가 방송을 들으면서

"이 장르가 처음에는 이런 음악이었는데,
시간이 지나면서 이런 모습으로 변화했구나"

라고 이해할 수 있도록 작성해주세요.

스크립트 흐름:

먼저 "{selected_genre}"가 어떤 음악인지
청취자가 쉽게 이해할 수 있도록 자연스럽게 소개해주세요.

이후 "{selected_genre}"가 어떤 시대적·문화적·음악적 배경에서
등장했는지 설명해주세요.

장르가 처음 등장했을 당시에는 어떤 모습이었는지,
어떤 문화적 환경에서 발전했는지도 자연스럽게 이야기해주세요.

그다음 "{selected_genre}"의 변화를
시간의 흐름에 따라 설명해주세요.

최소한 다음과 같은 흐름이 느껴져야 합니다.

- 장르가 처음 등장했을 당시의 모습
- 대중화되거나 크게 변화하기 시작한 시기
- 음악 기술이나 다른 장르와 결합하면서 변화한 모습
- 오늘날 "{selected_genre}"가 어떤 형태로 이어지고 있는지

연도와 사건을 단순 나열하지 말고,

"처음에는 이러했지만 이후 이런 변화가 나타났고,
오늘날에는 이런 모습으로 이어지고 있다"

는 식으로 하나의 음악 이야기처럼 자연스럽게 연결해주세요.

이어서 "{selected_genre}"만의 음악적인 특징을 설명해주세요.

리듬, 악기 구성, 보컬 스타일, 연주 방식,
사운드, 곡의 분위기, 즉흥성, 프로덕션 특징 등
해당 장르에 실제로 중요한 요소를 골라 설명해주세요.

특정 아티스트 한 명의 활동이나 음악 세계를
길게 설명하지 마세요.

아티스트는 장르의 역사적 변화나 음악적 특징을 설명하기 위해
필요한 경우에만 대표 사례로 짧게 언급해주세요.

대표곡은 2~3곡 정도 소개해주세요.

각 곡에 대해서는

- 해당 시대의 "{selected_genre}"가 어떤 모습이었는지
- 곡에서 드러나는 장르의 음악적 특징
- 사운드, 리듬, 악기, 보컬 등의 특징
- 해당 곡이 장르의 변화 과정에서 어떤 의미를 가지는지
- 청취자가 주목해서 들을 만한 감상 포인트

를 자연스럽게 설명해주세요.

실제로 음악을 재생하는 것처럼 표현하지 마세요.

"이 곡 들어보시죠."
"듣고 오겠습니다."
"잘 듣고 오셨나요?"

등의 표현은 사용하지 마세요.

마지막에는 "{selected_genre}"가 오늘날 어떤 모습으로 이어지고 있는지,
현대 음악에 어떤 영향을 남겼는지,
그리고 지금도 이 장르가 가진 매력이 무엇인지 이야기하며
코너를 자연스럽게 마무리해주세요.

중요:
- 반드시 "{selected_genre}"를 메인 주제로 끝까지 유지하세요.
- 특정 아티스트가 메인 주제가 되지 않도록 하세요.
- 다른 장르는 "{selected_genre}"의 변화나 영향을 설명하기 위한
  비교 대상으로만 필요한 만큼 언급하세요.
- 확인되지 않은 음악사적 사건, 발매일, 인물, 곡명을 임의로 만들어내지 마세요.
- 특정 날짜에 일어난 사건을 억지로 연결하지 마세요.
- 역사적 사실이 확실하지 않은 경우 구체적인 날짜를 단정하지 마세요.

분량:
- MUSIC_STORY 본문만 공백 포함 약 3,000자 내외로 작성하세요.
- 최소 2,500자 이상을 목표로 충분히 상세하게 작성하세요.
- 같은 설명을 반복해서 분량을 채우지 마세요.
- 탄생 배경, 시대적 변화, 음악적 특징,
  대표곡, 현재 모습을 균형 있게 활용하세요.

문체:
- 실제 라디오 DJ가 음악 이야기를 들려주는 자연스러운 구어체
- 음악 교과서나 백과사전처럼 딱딱하게 작성하지 마세요.
- 전문적인 내용도 일반 청취자가 이해할 수 있도록 쉽게 설명하세요.
- 소제목, 번호, 목록을 출력하지 마세요.
- 하나의 자연스러운 라디오 방송 대본처럼 이어서 작성하세요.

키워드: {keyword}
"""

    else:
        selected_genre = (
            keyword.strip()
            if keyword and keyword.strip()
            else random.choice(genres_en)
        )

        base_instruction = f"""
You are a knowledgeable and warm radio DJ.

Today's genre is "{selected_genre}".

Tell the story of this genre from its origins to the present.

Focus on:
- its origins
- its early form
- how it changed over time
- interaction with other genres and technology
- defining musical characteristics
- 2–3 representative songs
- what the genre looks like today
- its influence on modern music

Artists may be mentioned briefly as examples,
but do not turn the segment into a biography of one artist.

Do not pretend to actually play music.

Keep "{selected_genre}" as the central subject throughout the segment.

Do not invent unverified historical events, dates, artists, or songs.

Write one continuous radio script without headings or numbered sections.
Aim for approximately 3,000 Korean-character equivalent length.
"""

    prompt = build_block_prompt(
        base_instruction=base_instruction,
        block_name="MUSIC_STORY",
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
아래 MUSIC_STORY 라디오 대본이 현재 너무 짧습니다.

기존 내용의 주제와 사실관계, 전체 흐름은 유지하면서
공백 포함 약 3,000자 내외가 되도록 자연스럽게 확장해주세요.

특히 다음 내용을 더 풍부하게 설명해주세요.

- "{selected_genre}"의 탄생 배경
- 초기의 음악적 모습
- 시대에 따른 변화
- 다른 장르 및 음악 기술과의 결합
- "{selected_genre}"만의 음악적 특징
- 시대별 대표곡 2~3곡과 각 곡의 특징
- 오늘날의 모습
- 현대 음악에 남긴 영향과 매력

핵심 흐름은 반드시

탄생
→ 초기 모습
→ 시대별 변화
→ 확장
→ 현재

순서가 느껴지도록 유지해주세요.

특정 아티스트 한 명의 활동이나 음악 세계를
길게 설명하지 마세요.

아티스트는 장르의 변화나 특징을 설명하기 위한
대표 사례로만 짧게 언급해주세요.

음악을 실제로 재생하는 것처럼 표현하지 마세요.

같은 말을 반복해서 분량을 늘리지 마세요.
확인되지 않은 새로운 사실을 임의로 만들어내지 마세요.

번호나 소제목 없이
하나의 자연스러운 라디오 DJ 대본으로 작성해주세요.

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