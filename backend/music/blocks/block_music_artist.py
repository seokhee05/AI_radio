import json
import os
import random
from dotenv import load_dotenv
from openai import OpenAI
from common.prompt_utils import build_block_prompt

load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 키워드 기반 아티스트 선택 (LLM)
def pick_artist_by_llm(keyword: str = None, language="ko") -> str:
    if language == "ko":
        if keyword:
            prompt = f"""
            당신은 음악 전문 AI입니다.
            키워드 "{keyword}"와 어울리는 아티스트 1명을 추천해주세요.
            한국/해외 아티스트 모두 가능하며, 전 세계적으로 유명한 뮤지션 위주로 골라주세요.
            답변은 아티스트 이름만 출력하세요.
            """
        else:
            prompt = """
            당신은 음악 전문 AI입니다.
            전 세계적으로 널리 알려지고 사랑받는 아티스트 1명을 무작위로 추천해주세요.
            한국/해외 모두 가능하며, 대중적으로 유명한 뮤지션이면 됩니다.
            답변은 아티스트 이름만 출력하세요.
            """
    else:  # English
        if keyword:
            prompt = f"""
            You are a music expert AI.
            Please answer ONLY in English.
            
            Recommend one artist that best matches the keyword "{keyword}".
            It can be a Korean or international artist, but choose a globally famous musician.
            Reply with only the artist's name.
            """
        else:
            prompt = """
            You are a music expert AI.
            Randomly recommend one artist who is globally popular and well-loved.
            It can be either Korean or international.
            Reply with only the artist's name.
            """

    # OpenAI Chat Completion 호출
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    return res.choices[0].message.content.strip()

# 메인 블록
def block_music_artist(keyword=None, prev_type=None, context=None, language="ko"):
    selected_artist = pick_artist_by_llm(keyword, language=language)

    if language == "ko":
        base_instruction = f"""
        당신은 감성적인 라디오 DJ입니다.
        이전 코너는 {prev_type}이었고, 이런 분위기였습니다:
        {context}

        이제 [MUSIC_ARTIST] 코너를 진행해주세요.
        오늘은 "{selected_artist}" 아티스트를 집중 조명해주세요.

        요구사항:
        1. 아티스트의 특징/음악적 매력을 2~3문장으로 소개해주세요.
        2. 대표곡 소개하고, “이 곡 함께 들어보시죠 / 지금 들어볼까요”처럼 곡을 DJ가 직접 트는 것처럼 이어주세요.
        3. keyword가 있으면 (예: "가을") 그 키워드와 "{selected_artist}"의 곡 중 하나를 연결해서 추천해주세요.
        4. 곡이 끝난 뒤에는 “잘 듣고 오셨나요? 역시 {selected_artist}답네요”처럼 후속 멘트를 넣어주세요.
        5. 전체 톤은 따뜻하고 친근한 라디오 멘트로 작성하고, 표현은 매번 달라지도록 해주세요.

        키워드: {keyword}
        """
    else:  # English
        base_instruction = f"""
        You are a warm and emotional radio DJ.
        Please answer ONLY in English.

        The previous segment was {prev_type}, and the vibe was:
        {context}

        Now let’s move on to the [MUSIC_ARTIST] segment.
        Today, we’re spotlighting the artist "{selected_artist}".

        Requirements:
        1. Introduce the artist’s characteristics and musical charm in 2–3 sentences.
        2. Present a signature song and say it as if you’re playing it on the radio, e.g., “Let’s listen to this track together” or “Shall we hear it now?”
        3. If a keyword is given (e.g., "autumn"), connect that mood to one of "{selected_artist}’s" songs and recommend it.
        4. After the song, add a follow-up comment like: “Did you enjoy that? That’s so typically {selected_artist}.”
        5. The whole script should flow like a natural radio DJ monologue, warm and friendly, with varied expressions.

        Keyword: {keyword}
        """

    prompt = build_block_prompt(
        base_instruction=base_instruction,
        block_name="MUSIC_ARTIST",
        keyword=keyword,
        prev_type=prev_type,
        context=context
    )

    # OpenAI Chat Completion 호출 (단일 user 메시지 전달)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    print(block_music_artist("가을", language="ko"))
    print(block_music_artist("autumn", language="en"))