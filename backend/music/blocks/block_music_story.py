import os
import random
from dotenv import load_dotenv
from openai import OpenAI
from common.prompt_utils import build_block_prompt

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

GENRES_KO = ["재즈", "록", "EDM", "발라드", "힙합", "인디", "R&B", "소울", "펑크", "디스코"]
GENRES_EN = ["Jazz", "Rock", "EDM", "Ballad", "Hip-hop", "Indie", "R&B", "Soul", "Funk", "Disco"]


def _generate(messages, temperature=0.5):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=temperature,
        max_tokens=4200,
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError("MUSIC_STORY 대본이 비어 있습니다.")
    return content.strip()


def block_music_story(keyword=None, prev_type=None, context=None, language="ko"):
    # 키워드가 비어 있으면 무작위 장르를 사용합니다.
    genre_list = GENRES_KO if language == "ko" else GENRES_EN
    selected_genre = keyword.strip() if isinstance(keyword, str) and keyword.strip() else random.choice(genre_list)

    if language == "ko":
        base_instruction = f"""
당신은 음악사에 밝고 이야기를 재미있게 전달하는 한국어 라디오 DJ입니다.
오늘의 MUSIC_STORY 주제는 '{selected_genre}'입니다.
이 코너는 특정 아티스트의 일대기가 아닌, 장르의 탄생과 진화를 소개합니다.

[반드시 지킬 구성]
- 첫 문단: 장르의 소리와 매력을 쉽게 풀어 청취자를 끌어들입니다.
- 태동: 탄생한 시대·지역·사회문화적 맥락과 선행 음악의 영향을 설명합니다.
- 초기: 당시 음악 제작법·연주법·현장 문화 등을 구체적으로 설명합니다.
- 변화: 시대순으로 중요한 변곡점 2~3개를 자연스러운 인과관계로 연결합니다.
- 대표곡: 실제로 존재하고 해당 시기의 장르적 특징을 보여 주는 곡 2~3곡을 이야기 흐름에 녹여 소개합니다.
  각 곡의 아티스트, 제목, 당시의 음악적 특징과 역사적 의미를 정확히 설명하세요.
- 오늘날: 현재의 하위 장르, 다른 장르와의 결합, 음악 산업과 문화에 남긴 영향을 이야기합니다.
- 마지막 문단: 처음의 이미지와 연결되는 따뜻하고 자연스러운 마무리로 끝냅니다.

[사실성]
- 뚜렷한 근거가 없는 정확한 날짜, 최초 기록, 역사적 사건, 곡·가수 이름은 만들지 마세요.
- 특정 행사를 '장르가 탄생한 단 하루'라고 단정하지 마세요. 널리 언급되는 상징적 사건이면 그 맥락을 구분해 설명하세요.
- 음악사적 순서가 꼬이지 않도록 하세요. 예를 들어 2010년대에 부상한 흐름을 2000년대의 대표 현상으로 쓰지 마세요.
- 리듬·보컬·악기·샘플링·제작 방식은 해당 장르의 실제 특징만 골라 설명하세요.
- 대표곡의 발매 연도가 확실치 않으면 연도를 빼고 시대를 설명하세요.
- 실시간 인기 순위나 현재 유행을 확인한 것처럼 꾸미지 마세요.

[문체와 길이]
- 공백 포함 약 2,700~3,200자, 7~9개의 비교적 충실한 문단을 목표로 합니다.
- 라디오 DJ의 편안한 구어체를 사용하고, 문단 사이가 자연스럽게 이어지도록 합니다.
- 문단마다 새로운 정보가 있어야 하며 앞부분을 다시 말하는 방식으로 분량을 채우지 마세요.
- 너무 일반적인 수식어(새로운 가능성, 많은 사랑, 다양한 매력)를 반복하지 마세요.
- 소제목, 숫자 목록, 괄호 속 무대지시, JSON, 인사말·클로징 코너는 출력하지 마세요.
- 실제 음악 재생 기능이 없으므로 '들어보시죠', '듣고 오셨나요'처럼 곡 재생을 암시하지 마세요.
- 이전 코너가 있으면 문장 한두 개로만 자연스럽게 분위기를 잇고, 메인 주제는 끝까지 '{selected_genre}'로 유지하세요.

이전 코너: {prev_type or '없음'}
이전 분위기: {str(context or '없음')[:900]}

대본 본문만 출력하세요.
"""
    else:
        base_instruction = f"""
You are a warm, historically informed radio DJ. MUSIC_STORY topic: {selected_genre}.
Write an engaging chronological radio narrative about the genre, not a single artist's biography.
Cover the sonic identity, social and musical origins, early practices, major changes over time,
2–3 real representative songs embedded naturally with specific musical and historical context,
and the genre's contemporary forms and enduring influence.
Avoid made-up dates, claims of a single definitive founding moment, invented songs, unverified rankings,
or vague repeated praise. If a specific release year is uncertain, omit it.
Write 7–9 substantial, connected paragraphs, roughly 1,500–2,000 English words maximum.
No headings, lists, JSON, opening/closing segments or pretend music playback.
Previous segment: {prev_type or 'none'}. Previous context: {str(context or 'none')[:900]}.
Output only the radio script.
"""

    prompt = build_block_prompt(
        base_instruction=base_instruction,
        block_name="MUSIC_STORY",
        keyword=selected_genre,
        prev_type=prev_type,
        context=context,
    )
    result = _generate([{"role": "user", "content": prompt}])

    # 짧을 때만 한 번 더 보강합니다. 이미 충분하면 추가 API 호출을 하지 않습니다.
    if language == "ko" and len(result) < 2500:
        expand_prompt = f"""
다음 '{selected_genre}' MUSIC_STORY 대본을 공백 포함 2,700~3,200자 정도로 보완하세요.
원문의 장르, 시대순 흐름, 이미 소개한 실제 대표곡은 유지하세요.
부족한 시대적 연결과 그 장르만의 구체적인 사운드·문화적 특징을 추가하세요.
새로운 곡명·날짜·사실을 확인 없이 추가하거나, 같은 내용을 반복하지 마세요.
자연스러운 한국어 DJ 구어체의 본문만 출력하세요. 제목, 목록, 음악 재생 멘트는 금지합니다.

원문:
{result}
"""
        result = _generate([{"role": "user", "content": expand_prompt}], temperature=0.4)

    return result

# MUSIC_GENRE 블록에서도 MUSIC_STORY 대본 생성 기능 사용
def block_music_genre(
    keyword=None,
    prev_type=None,
    context=None,
    language="ko"
):
    return block_music_story(
        keyword=keyword,
        prev_type=prev_type,
        context=context,
        language=language
    )