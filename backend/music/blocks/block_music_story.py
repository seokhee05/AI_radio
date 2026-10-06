import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from common.prompt_utils import build_block_prompt

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def search_music_story_facts(selected_genre, language="ko"):

    current_date = datetime.now().strftime("%Y-%m-%d")

    if language == "ko":
        search_prompt = f"""
현재 날짜: {current_date}

음악 장르, 스타일 또는 음악 문화 범주 "{selected_genre}"에 대해 웹 검색을 수행하고,
라디오 대본 작성에 사용할 정확한 사실 자료를 정리하세요.

다음 내용을 조사하세요.

1. 장르 소개
- 기본 분위기
- 핵심적인 음악적 특징
- 다른 장르와 구별되는 특징

2. 탄생 배경
- 언제 등장했는지
- 어디에서 시작되었는지
- 어떤 문화적·사회적 배경이 있었는지
- 어떤 기존 음악의 영향을 받았는지

3. 시대별 변화
- 초기 형태
- 대중화 과정
- 중요한 음악적 전환점
- 다른 장르와의 결합
- 현재까지의 변화

4. 음악적 특징
- 리듬
- 사운드
- 주요 악기
- 보컬
- 멜로디
- 편곡
- 프로덕션

5. 시대별 대표 음악
- 서로 다른 시대를 대표하는 실제 곡 2~3곡
- 곡명
- 아티스트
- 발표 연도
- 해당 곡에서 드러나는 장르 특징
- 장르 역사에서 중요한 이유

6. 오늘날의 모습
- 현재 이 장르가 어떤 형태로 이어지고 있는지
- 최근 다른 장르와 어떻게 결합되고 있는지
- 현재 활동 중인 대표 아티스트 또는 최근 실제 사례
- 과거 특징 중 현재까지 남아 있는 요소

중요:
- 실제 웹 자료를 검색해서 작성하세요.
- 장르의 기원, 장소, 연도, 아티스트, 곡명은 정확히 확인하세요.
- 자료마다 설명이 다른 경우 하나의 사실처럼 단정하지 마세요.
- 불확실한 정보는 제외하거나 불확실성을 표시하세요.
- 곡명, 아티스트명, 발표 연도를 임의로 만들지 마세요.
- 시대별 대표곡은 실제 해당 장르의 역사와 관련 있는 곡을 사용하세요.
- 특정 인물을 장르 전체의 창시자로 과도하게 단순화하지 마세요.
- 사회적·문화적 배경도 하나의 원인만으로 설명하지 마세요.
- 객관적 사실과 음악적 해석을 구분하세요.
- 현재 활동과 최근 사례는 현재 날짜 기준으로 확인하세요.
- 신뢰할 수 있는 음악 전문 자료, 공식 자료, 주요 음악 매체를 우선 사용하세요.
- 라디오 대본은 작성하지 말고 사실 자료만 정리하세요.
- K-POP처럼 하나의 고정된 장르로 보기 어려운 음악 문화 범주는
  여러 음악 장르의 결합과 산업·문화적 발전을 함께 조사하세요.
"""
    else:
        search_prompt = f"""
Current date: {current_date}

Search the web for accurate information about the music genre "{selected_genre}".

Research:
- basic characteristics
- origins and cultural background
- historical development
- rhythm, sound, instruments, vocals, arrangement, production
- 2–3 representative songs from different eras
- how the genre exists today

Important:
- verify facts on the web
- do not fabricate artists, songs, dates or historical events
- distinguish factual information from interpretation
- acknowledge uncertainty when sources disagree
- verify current examples as of the current date
- prioritize reliable music publications and official sources
- do not write the radio script yet
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        tools=[
            {"type": "web_search"}
        ],
        input=search_prompt
    )

    return response.output_text

def block_music_story(keyword=None, prev_type=None, context=None, language="ko"):

    if not keyword:
        raise ValueError("장르 키워드를 입력해주세요.")

    selected_genre = keyword

    if selected_genre.upper().replace("-", "") == "KPOP":
        genre_type = "음악 문화 및 산업 범주"
    else:
        genre_type = "음악 장르 또는 스타일"

    story_facts = search_music_story_facts(
        selected_genre=selected_genre,
        language=language
    )

    print("\n===== SELECTED GENRE =====")
    print(selected_genre)

    print("\n===== MUSIC STORY FACTS =====")
    print(story_facts)

    if language == "ko":

        base_instruction = f"""
당신은 음악 전문 라디오 DJ입니다.

이전 코너는 {prev_type}이었고,
이런 분위기였습니다:

{context}

이제 [장르 & 음악 이야기] 코너로 자연스럽게 이어가세요.

오늘 이야기할 음악 주제는:

"{selected_genre}"

이 주제는 "{genre_type}"로 다루세요.

[웹 검색으로 확인된 장르 사실 자료]

{story_facts}

[매우 중요한 사실 사용 규칙]

- 위의 웹 검색 자료만 이 대본의 사실 정보 기준으로 사용하세요.
- 모델이 기존에 알고 있던 기억이나 지식을 이용해 새로운 사실을 추가하지 마세요.
- 장르의 기원, 시대, 장소, 영향 관계, 아티스트, 곡명, 발표 연도는 반드시 위 자료에서 가져오세요.
- 위 자료에 없는 곡, 아티스트, 앨범, 역사적 사건은 절대 추가하지 마세요.
- 대표곡은 반드시 위 자료의 '시대별 대표 음악'에 제시된 곡 중에서 2~3곡을 선택하세요.
- 대표곡을 다른 유명곡으로 교체하지 마세요.
- 시대별 변화도 위 자료에서 확인된 순서와 내용을 따르세요.
- 위 자료와 모델의 기존 지식이 충돌하면 반드시 위 자료를 따르세요.
- 자료에 없는 내용을 채워야 할 경우 추측하지 말고 해당 내용을 생략하세요.

이 코너는 단순히 장르의 특징만 소개하는 것이 아니라,
장르의 탄생과 역사, 음악적 변화, 대표 음악,
그리고 오늘날의 모습까지 하나의 음악 이야기처럼 설명하는 코너입니다.


--------------------------------------------------
1. 장르 소개
--------------------------------------------------

먼저 "{selected_genre}"가 어떤 음악인지 설명하세요.

- 기본적인 분위기
- 사람들이 이 장르에서 느끼는 인상
- 다른 음악과 구별되는 특징

처음부터 어려운 음악 이론을 나열하지 말고,
청취자가 쉽게 이해할 수 있도록 설명하세요.


--------------------------------------------------
2. 탄생 배경과 음악 역사
--------------------------------------------------

"{selected_genre}"가 어떻게 시작되었는지 설명하세요.

다음 내용을 포함하세요.

- 어느 시대에 등장했는지
- 어느 지역 또는 문화에서 시작되었는지
- 어떤 음악이나 문화의 영향을 받았는지
- 당시 사회적·문화적 배경
- 어떻게 하나의 음악 장르로 발전했는지

단순히 연도를 나열하지 말고,
하나의 이야기처럼 자연스럽게 설명하세요.


--------------------------------------------------
3. 시대별 변화
--------------------------------------------------

"{selected_genre}"가 처음 등장한 이후
어떻게 변화했는지 설명하세요.

가능하면 다음 흐름으로 설명하세요.

초기
→ 대중화
→ 새로운 스타일 등장
→ 다른 장르와의 결합
→ 현대적인 형태

모든 시대를 세세하게 설명하기보다,
음악적으로 중요한 변화 중심으로 설명하세요.


--------------------------------------------------
4. 음악적 특징
--------------------------------------------------

"{selected_genre}"의 대표적인 음악적 특징을 설명하세요.

단, K-POP처럼 하나의 고정된 음악 장르가 아닌 음악 문화 범주인 경우에는
하나의 공통된 사운드가 있다고 단정하지 마세요.

대신 여러 시대와 아티스트에서 반복적으로 나타나는
프로덕션 방식, 장르 혼합, 보컬·랩 구성, 퍼포먼스와 음악의 결합 등
대표적인 경향을 설명하고,
모든 K-POP 곡이 이러한 특징을 가지는 것은 아니라는 점을 반영하세요.

실제로 중요한 요소를 골라 설명하세요.

- 리듬
- 사운드
- 악기
- 보컬
- 멜로디
- 편곡
- 프로덕션

전문 용어만 나열하지 말고,
실제로 음악을 들었을 때
어떤 부분에서 이 장르의 특징을 느낄 수 있는지 설명하세요.


--------------------------------------------------
5. 시대별 대표 음악
--------------------------------------------------

"{selected_genre}"의 변화를 잘 보여주는 실제 대표곡을
2~3곡 정도 소개하세요.

가능하면 서로 다른 시대의 곡을 선택하세요.

각 곡마다 다음 내용을 자연스럽게 설명하세요.

- 곡명
- 아티스트
- 발표 시기
- 해당 시대에서의 의미
- 곡에서 드러나는 장르의 특징
- 이전 시대와 달라진 부분
- 사운드, 리듬, 악기 또는 보컬의 특징
- 장르 역사에서 중요한 이유

단순히 유명한 노래를 나열하지 말고,
대표곡을 통해 장르가 어떻게 변화했는지 보여주세요.
대표곡 소개 시 반드시 곡명, 아티스트명, 발표 연도를 자연스럽게 언급하세요.


--------------------------------------------------
6. 오늘날의 모습
--------------------------------------------------

마지막에는 "{selected_genre}"가
현재 어떤 형태로 이어지고 있는지 설명하세요.

- 최근 음악에서는 어떻게 활용되는지
- 다른 장르와 어떻게 결합되고 있는지
- 현재 활동 중인 대표 아티스트나 음악 사례
- 과거의 특징 중 지금도 유지되는 부분
- 새롭게 변화한 부분

"{selected_genre}"가 과거에 끝난 음악처럼 말하지 말고,
현재 음악과 어떻게 연결되고 있는지 설명하세요.


--------------------------------------------------
키워드의 의미
--------------------------------------------------

청취자 키워드는 알고 싶은 음악 장르, 스타일 또는 음악 문화 범주를 의미합니다.

예:
재즈
힙합
R&B
록
시티팝
디스코
소울
펑크
EDM
인디
K-POP

키워드가 있다면 해당 장르 또는 음악 스타일 자체를 이야기의 중심으로 사용하세요.

K-POP처럼 여러 장르가 결합된 음악 문화 범주가 입력된 경우,
하나의 고정된 음악 장르처럼 설명하지 말고
형성 배경, 시대별 변화, 대표적인 음악적 특징,
주요 아티스트와 곡, 현재의 모습까지 폭넓게 설명하세요.

청취자의 감정이나 분위기를 억지로 장르에 연결하지 마세요.


--------------------------------------------------
사실 정확성
--------------------------------------------------

- 실제 존재하는 장르, 아티스트, 곡만 사용하세요.
- 곡명, 아티스트명, 발표 연도를 임의로 만들지 마세요.
- 장르의 정확한 탄생 연도나 장소가 논쟁적인 경우 단정하지 마세요.
- 특정 아티스트 한 명을 장르 전체의 창시자처럼 설명하지 마세요.
- 장르의 변화가 하나의 사건이나 한 사람 때문에 일어난 것처럼 단순화하지 마세요.
- 확실하지 않은 역사적 정보는 구체적인 연도로 단정하지 마세요.
- 현재 활동이나 최근 사례가 확실하지 않으면 추측하지 마세요.
- 검색 자료에 없는 대표곡이나 현대 아티스트를 임의로 예시로 추가하지 마세요.
- 장르의 기원을 설명할 때 특정 연도나 하나의 사건을 "탄생 시점"으로 단정하지 말고,
  "형성되기 시작했다", "발전했다"처럼 역사적 맥락을 반영해 표현하세요.
- 힙합처럼 음악뿐 아니라 DJing, MCing, 브레이킹 등 문화적 요소를 포함하는 장르는
  단순히 하나의 음악 스타일로 축소해서 설명하지 마세요.
- "단순한 파티 음악으로 시작했다"처럼 장르의 초기 역사를 과도하게 단순화하지 마세요.
- 장르 전체를 하나의 분위기나 사운드로 단정하지 마세요. 시대와 하위 스타일에 따라 음악적 특징이 달라지는 경우,
  "초기에는 ~", "1990년대에는 ~", "현대에는 ~"처럼 시대를 구분해서 설명하세요.
- 장르의 사회적 의미를 설명할 때 모든 곡이나 모든 시대가 같은 사회적 역할을 했던 것처럼 일반화하지 마세요.
- K-POP의 시작을 특정 연도나 특정 아티스트 한 팀으로 단정하지 말고,
  "현대적 K-POP의 중요한 전환점"처럼 표현하세요.
- K-POP 전체의 음악적 특징을 하나의 리듬, 보컬 구조, 편곡 방식으로 일반화하지 마세요.
  여러 시대와 하위 스타일에 따라 특징이 달라진다는 점을 반영하세요.
- 최신 K-POP 사례, 최근 발매곡, 현재 활동 정보는
  반드시 위 웹 검색 자료에서 직접 확인된 내용만 사용하세요.

--------------------------------------------------
대본 작성 규칙
--------------------------------------------------

- 한국어 약 3,000~3,500자를 목표로 작성하세요.
- 실제 라디오 DJ가 이야기하는 자연스러운 구어체로 작성하세요.
- 번호, 제목, 소제목, 목록을 최종 결과에 출력하지 마세요.
- 하나의 긴 음악 이야기처럼 자연스럽게 이어지게 작성하세요.
- 같은 내용을 반복하지 마세요.
- 지나치게 학술적인 보고서처럼 작성하지 마세요.
- 실제 음악을 재생하지 않으므로
  "들어보시죠",
  "듣고 왔습니다",
  "잠시 감상하고 오겠습니다"
  같은 표현은 사용하지 마세요.
- 최종 결과에는 완성된 DJ 대본만 출력하세요.
"""

    else:

        base_instruction = f"""
You are a professional music radio DJ.

The previous segment was {prev_type}.

Previous context:
{context}

Now continue naturally into the [MUSIC_STORY] segment.

Today's genre:
"{selected_genre}"

Explain this genre as one continuous music story.

Include:

- what the genre sounds like
- its origins and cultural background
- its historical development
- major musical characteristics
- 2–3 representative songs from different periods
- how the genre exists today

The keyword represents the music genre or style
the listener wants to learn about.

Do not fabricate artists, songs, dates, or historical facts.

Write in natural radio narration.

Do not output headings, numbered sections, or bullet points.
Do not pretend that songs are actually being played.

Output only the finished DJ script.
"""

    prompt = build_block_prompt(
        base_instruction=base_instruction,
        block_name="music_story",
        keyword=keyword,
        prev_type=prev_type,
        context=context
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=4200,
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    print(
        block_music_story(
            keyword="재즈",
            language="ko"
        )
    )