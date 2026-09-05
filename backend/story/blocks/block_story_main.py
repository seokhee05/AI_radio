import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from common.prompt_utils import build_block_prompt

load_dotenv()
# Gemini 클라이언트 초기화
client = genai.Client()

def block_story_main(
    story,
    keyword=None,
    prev_type=None,
    context=None,
    language="ko",
    last_song=None,
    is_last=False,
):
    author = story.get("author", "익명 청취자" if language == "ko" else "Anonymous Listener")
    content = story["content"]

    if language == "ko":
        base_instruction = f"""
        당신은 감성적인 AI 라디오 DJ입니다.
        아래 사연을 바탕으로, 청취자에게 따뜻하게 공감하는 멘트를 작성해주세요.

        사연 작성자: {author}
        사연 내용:
        \"\"\"
        {content}
        \"\"\"

        요청:
        1. 먼저 사연을 **청취자에게 간단히 소개**해주세요. (예: "OOO님이 보내주신 사연입니다...")
        2. 그 후, 사연의 감정을 충분히 이해하고, 6~8문장 정도로 길게 공감 멘트를 작성해주세요.
        3. 단순 공감에서 끝내지 말고, 청취자가 생각해볼 만한 이야기를 1~2개 덧붙여주세요.
        4. 마지막에는 해당 분위기에 어울리는 실제 존재하는 노래를 추천해주세요.
        5. 이어서 곡이 끝난 뒤의 후속 멘트를 추가해주세요.  
           - 매번 다르게, 직전 추천곡({last_song})을 언급해서 말해주세요.  
        """
        if is_last:
            base_instruction += """
            6. 이번 사연이 오늘의 마지막 사연이므로,
               "다음 사연"으로 넘어가지 말고 사연 코너 전체를 마무리하는 멘트를 추가해주세요.
            """
        else:
            base_instruction += """
            6. 마지막으로 다음 사연이나 콘텐츠로 자연스럽게 넘어가기 위한 전환 멘트를 1문장 추가해주세요.
            """
        base_instruction += """
        최종 출력은 DJ의 자연스러운 멘트 흐름으로, 중간 구분 없이 하나의 스크립트로 작성해주세요.
        """

        prompt = build_block_prompt(
            base_instruction=base_instruction,
            block_name="STORY_MAIN",
            keyword=keyword,
            prev_type=prev_type,
            context=context,
            language="ko"
        )

        # Gemini 모델 호출 (한국어)
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

    else:  # English version
        base_instruction = f"""
        You are a warm and empathetic AI Radio DJ.
        
        Story Author: {author}
        Story Content:
        \"\"\"
        {content}
        \"\"\"

        Requirements:
        1. Start by briefly introducing the story to the audience. (e.g., "This is a story sent in by OOO...")
        2. Then, deeply empathize with the emotions in the story and write a 6–8 sentence heartfelt response.
        3. Add 1–2 reflections or thoughts that the audience might consider.
        4. Recommend a real existing song that fits the mood of the story.
        5. Add a short follow-up comment as if returning after the song has finished. Mention the previously recommended song ({last_song}).
        """
        if is_last:
            base_instruction += """
            6. Since this is the last story of the day, do not transition to another story.  
               Instead, add a closing remark for the story segment.
            """
        else:
            base_instruction += """
            6. End with a natural transition line leading into the next story or segment.
            """
        base_instruction += """
        The final output should be written as one continuous DJ script,
        with no section labels. Keep it warm, natural, and radio-like.
        """

        prompt = build_block_prompt(
            base_instruction=base_instruction,
            block_name="STORY_MAIN_EN",
            keyword=keyword,
            prev_type=prev_type,
            context=context,
            language="en"
        )

        # 영어 버전은 시스템 인스트럭션과 유저 프롬프트를 나누어 적용
        system_content = "You are an empathetic Radio DJ. ALWAYS respond in English, no matter what the input language is."
        
        user_content = f"""
        The following story is written in Korean.
        You may translate it internally to understand it,
        but your final output MUST be written ONLY in English.
        
        Story:
        \"\"\"
        {content}
        \"\"\"

        Instructions:
        {prompt}
        """

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_content,
                temperature=0.8,
            ),
        )

    return response.text.strip()