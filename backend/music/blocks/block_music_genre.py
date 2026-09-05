import os
from dotenv import load_dotenv
import random
from google import genai
from common.prompt_utils import build_block_prompt

load_dotenv()
# Gemini 클라이언트 초기화
client = genai.Client()

def block_music_genre(keyword=None, prev_type=None, context=None, language="ko"):
    genres_ko = ["재즈", "록", "EDM", "발라드", "힙합", "인디"]
    genres_en = ["Jazz", "Rock", "EDM", "Ballad", "Hip-hop", "Indie"]

    if language == "ko":
        selected_genre = random.choice(genres_ko)
        base_instruction = f"""
        당신은 감성적인 라디오 DJ입니다.
        이전 코너는 {prev_type}이었고, 이런 분위기였습니다:
        {context}

        이제 [MUSIC_GENRE] 코너로 자연스럽게 이어주세요.
        오늘은 "{selected_genre}" 장르를 탐험하는 시간입니다.
        
        요구사항:
        1. 이 장르의 특징을 2~3문장으로 소개해주세요.
        2. 대표적인 아티스트나 곡을 1~2개 예시로 들어주세요.
        3. keyword가 있으면 (예: "가을") 그 분위기와 "{selected_genre}" 장르를 연결해서 곡 추천 1개를 추가해주세요.
        4. 추천곡은 단순 나열이 아닌, “이 곡을 들으며 {selected_genre}의 매력을 느껴보시죠”처럼 청취자와 함께 듣는 톤으로 말해주세요.
        5. 곡이 끝난 뒤에는 “방금 들은 곡, 참 인상적이었죠?”처럼 마무리 멘트를 해주세요.
        6. 표현은 매번 달라지도록 해주세요.

        키워드: {keyword}
        """
    else:  # English
        selected_genre = random.choice(genres_en)
        base_instruction = f"""
        You are an emotional radio DJ.
        Please answer ONLY in English.
        
        The previous segment was {prev_type}, and it had this kind of vibe:
        {context}

        Now let’s move on to the [MUSIC_GENRE] segment.
        Today, we’re exploring the "{selected_genre}" genre.
        
        Requirements:
        1. Introduce the characteristics of this genre in 2–3 sentences.
        2. Mention 1–2 representative artists or songs.
        3. If a keyword is given (e.g., "autumn"), connect that mood with the "{selected_genre}" genre and recommend 1 song.
        4. Don’t just list songs—say it in a DJ tone like: “Let’s feel the charm of {selected_genre} with this track.”
        5. After the song, add a short wrap-up comment like: “That was such an impressive piece, wasn’t it?”
        6. Make sure the expressions vary each time so it doesn’t sound repetitive.

        Keyword: {keyword}
        """

    prompt = build_block_prompt(
        base_instruction=base_instruction,
        block_name="MUSIC_GENRE",
        keyword=keyword,
        prev_type=prev_type,
        context=context
    )

    # Gemini 모델로 장르 코너 스크립트 생성
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )
    return response.text.strip()