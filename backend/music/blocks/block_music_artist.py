import os
from dotenv import load_dotenv
from openai import OpenAI
from common.prompt_utils import build_block_prompt

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def pick_artist_by_llm(language="ko"):
    if language == "ko":
        prompt = """
당신은 음악 전문 AI입니다.
한국 또는 해외의 대중적으로 잘 알려진 아티스트 중 한 명을 추천해주세요.
답변은 아티스트 이름만 출력하세요.
"""
    else:
        prompt = """
You are a music expert AI.
Recommend one globally well-known artist.
Reply with only the artist's name.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


def block_music_artist(
    keyword=None,
    prev_type=None,
    context=None,
    language="ko"
):
    # 키워드가 있으면 반드시 입력한 아티스트 사용
    if keyword and keyword.strip():
        selected_artist = keyword.strip()
    else:
        selected_artist = pick_artist_by_llm(language=language)

    if language == "ko":
        base_instruction = f"""
당신은 음악 전문 지식을 갖춘 감성적인 라디오 DJ입니다.

이전 코너는 {prev_type}이었고, 이런 분위기였습니다:
{context}

이제 [MUSIC_ARTIST] 코너를 진행해주세요.

오늘 집중 조명할 아티스트는 "{selected_artist}"입니다.

반드시 지켜야 할 조건:
- "{selected_artist}"를 처음부터 끝까지 메인 주제로 유지하세요.
- 다른 아티스트를 메인 아티스트로 변경하지 마세요.
- 다른 아티스트는 비교나 협업 등의 맥락에서 필요한 경우에만 짧게 언급하세요.
- 확인되지 않은 곡명, 앨범명, 발매일, 수상 기록, 활동 이력을 임의로 만들어내지 마세요.
- 확실하지 않은 사실은 구체적인 날짜나 수치로 단정하지 마세요.

스크립트 흐름:

먼저 "{selected_artist}"를 자연스럽게 소개하며 코너를 시작해주세요.

이후 "{selected_artist}"만의 음악적 특징과 개성을 설명해주세요.

보컬, 사운드, 곡의 분위기, 표현 방식 등
이 아티스트만의 음악적 매력이 무엇인지 청취자가 이해하기 쉽게 이야기해주세요.

초기 활동부터 현재까지 음악 스타일이나 이미지가
어떻게 변화해왔는지도 자연스럽게 설명해주세요.

대표적인 앨범이나 주요 활동도 이야기해주세요.

대표곡은 전체적으로 2~3곡 정도 소개해주세요.

각 대표곡은 제목만 단순히 나열하지 말고 다음 내용을 충분히 설명해주세요.

- 곡의 전체적인 분위기
- 사운드와 편곡의 특징
- 보컬 표현이나 창법의 특징
- 리듬, 악기 구성, 프로덕션 등 음악적으로 주목할 요소
- 청취자가 주목해서 들을 만한 감상 포인트
- 해당 곡이 "{selected_artist}"의 음악 세계에서 가지는 의미

대표곡 2~3곡은 서로 비슷한 설명을 반복하지 말고,
각 곡마다 서로 다른 음악적 특징과 매력이 드러나도록 소개해주세요.

실제로 음악을 재생하는 기능이 있는 것처럼 표현하지 마세요.

"이 곡 함께 들어보시죠."
"듣고 오겠습니다."
"잘 듣고 오셨나요?"

등 실제 곡 재생을 전제로 하는 표현은 사용하지 마세요.

대신

"이 곡에서 특히 주목할 부분은..."
"이 곡을 살펴보면 "{selected_artist}"의 변화가 잘 드러나는데요."
"또 다른 대표곡에서는 조금 다른 매력을 발견할 수 있습니다."

등 자연스러운 DJ 연결 멘트를 사용해주세요.

마지막에는 지금까지 소개한 내용을 자연스럽게 정리하면서
"{selected_artist}"가 가진 음악적 매력과 개성을 다시 한번 전달해주세요.

분량:
- MUSIC_ARTIST 본문만 공백 포함 약 3,000자 내외로 작성하세요.
- 최소 2,500자 이상을 목표로 충분히 상세하게 작성하세요.
- 같은 표현이나 내용을 반복해서 분량을 채우지 마세요.
- 아티스트 소개, 음악적 특징, 활동 변화,
  앨범과 대표곡, 감상 포인트를 균형 있게 활용하세요.

문체:
- 실제 라디오 DJ가 청취자에게 이야기하는 듯한 자연스러운 구어체
- 따뜻하고 친근한 분위기
- 지나치게 과장되거나 광고 같은 표현은 피하세요.
- 번호, 소제목, 목록을 출력하지 마세요.
- 하나의 자연스러운 라디오 방송 대본처럼 이어서 작성하세요.

키워드: {keyword}
"""

    else:
        base_instruction = f"""
You are a knowledgeable and warm radio DJ.

The featured artist is "{selected_artist}".

Keep "{selected_artist}" as the main subject throughout the segment.

Introduce the artist naturally and discuss:
- musical characteristics
- career and stylistic development
- notable albums or activities
- 2–3 representative songs
- musical characteristics and listening points of each song
- the meaning of those songs within the artist's musical career

Do not pretend to actually play music.
Do not invent unverified songs, albums, dates, awards, or career records.

Write one continuous radio script without headings or numbered sections.
Aim for a detailed script roughly equivalent to about 3,000 Korean characters.
"""

    prompt = build_block_prompt(
        base_instruction=base_instruction,
        block_name="MUSIC_ARTIST",
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

    # 한국어 결과가 2500자보다 짧으면 한 번 더 확장
    if language == "ko" and len(result) < 2500:
        expand_prompt = f"""
아래 MUSIC_ARTIST 라디오 대본이 현재 너무 짧습니다.

기존 주제와 사실관계, 전체 흐름은 그대로 유지하면서
공백 포함 약 3,000자 내외가 되도록 자연스럽게 확장해주세요.

오늘 집중 조명할 아티스트는 "{selected_artist}"입니다.

특히 다음 내용을 더 풍부하게 설명해주세요.

- "{selected_artist}"의 음악적 특징과 개성
- 초기 활동부터 현재까지의 음악 스타일 변화
- 대표 앨범 또는 주요 활동
- 대표곡 2~3곡
- 각 대표곡의 분위기, 사운드, 보컬, 편곡 등 음악적 특징
- 각 곡에서 주목해서 들을 만한 감상 포인트
- 각 곡이 "{selected_artist}"의 음악 세계에서 가지는 의미
- 실제 곡 재생을 전제로 하지 않는 자연스러운 DJ 연결 멘트
- 마지막에는 "{selected_artist}"의 음악적 매력과 개성을 자연스럽게 정리해주세요.

반드시 "{selected_artist}"를 메인 주제로 유지하세요.
다른 아티스트를 메인 주제로 변경하지 마세요.

같은 표현이나 내용을 반복해서 분량을 늘리지 마세요.
확인되지 않은 곡명, 앨범명, 발매일, 수상 기록 등을
새롭게 만들어내지 마세요.

실제 음악을 재생하는 것처럼 표현하지 마세요.

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