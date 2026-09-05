import os
from dotenv import load_dotenv
from datetime import datetime
from google import genai
from common.prompt_utils import build_block_prompt

load_dotenv()
# Gemini 클라이언트 초기화
client = genai.Client()

def block_music_history(keyword=None, prev_type=None, context=None, language="ko"):
    today = datetime.now().strftime("%m월 %d일")
    if language == "ko":
        base_instruction = f"""
        당신은 감성적인 라디오 DJ입니다.

        이전 코너는 {prev_type}이었고, 이런 분위기였습니다:
        {context}

        이제 [MUSIC_HISTORY] 코너로 이어주세요.
        오늘은 {today}, 과거 오늘의 음악 역사 속 사건들을 함께 살펴보겠습니다.

        과거 오늘의 음악 역사 속에서 실제 있었던 사건 2~3개를 소개해주세요.
        한국 이슈를 최소 1개 포함하고, 해외 사건도 함께 다뤄주세요.
        DJ 멘트 형식으로 감성 있게 작성하고, 각 사건마다 어울리는 곡을 추천하고, 마치 라디오처럼 곡을 직접 이어주세요.
            - (예: “지금 이 곡 함께 들어보시죠” / “잠시 감상하고 오겠습니다”) 
        각각의 사건과 추천곡 소개는 하나의 흐름 있는 덩어리처럼 작성해주세요.
        (예: "강렬한 퍼포먼스가 인상적인 Kill This Love, 그리고 중독적인 뚜두뚜두 함께 들어보시죠.")
        곡을 들은 후에는 “잘 듣고 오셨나요? 그 시절의 감성이 느껴지네요”처럼 후속 멘트를 넣어주세요.
        표현은 매번 다르게 해주세요.
        """
    else:  # English
        base_instruction = f"""
        You are an emotional radio DJ.
        Please answer ONLY in English.
        
        The previous segment was {prev_type}, and it had this vibe:
        {context}

        Now let’s move on to the [MUSIC_HISTORY] corner.
        Today is {today}, so let’s take a look back at music history on this very day.

        Please introduce 2–3 real events from music history that happened on this date.
        Include at least one Korean music-related event and also one from overseas.
        Write in a warm, DJ-style narrative, recommending songs for each event and transitioning as if actually playing them on the radio.
            - (e.g., “Let’s listen to this track together” / “We’ll be right back after this song”) 
        Each event and its recommended track should feel like one natural flowing story.
        (e.g., "The powerful performance of Kill This Love, followed by the addictive Ddu-Du Ddu-Du — let’s listen together.")
        After the song, include a short follow-up comment like “Did you enjoy that? You can really feel the vibe of that era.”
        Vary the expressions each time so it doesn’t sound repetitive.
        """

    prompt = build_block_prompt(
        base_instruction=base_instruction,
        block_name="MUSIC_HISTORY",
        keyword=keyword,
        prev_type=prev_type,
        context=context
    )

    # Gemini 모델로 음악 역사 스크립트 생성
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )
    return response.text.strip()