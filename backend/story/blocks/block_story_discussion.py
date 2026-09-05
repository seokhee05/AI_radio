import os
from dotenv import load_dotenv
from google import genai
from common.prompt_utils import build_block_prompt

load_dotenv()
# Gemini 클라이언트 초기화
client = genai.Client()

def block_story_discussion(story, keyword=None, prev_type=None, context=None, language="ko"):
    author = story.get("author", "익명 청취자" if language == "ko" else "Anonymous Listener")
    content = story["content"]

    if language == "ko":
        base_instruction = f"""
        당신은 라디오 DJ입니다.  
        아래 사연을 바탕으로, 하나의 "토론 주제"를 뽑아내고 청취자와 함께 생각을 나누는 코너를 만듭니다.

        사연 작성자: {author}
        사연 내용:
        \"\"\"
        {content}
        \"\"\"

        요청:
        1. 토론 주제를 뽑아주세요. (예: "연애 중 연락 빈도, 얼마나 자주 해야 할까?")
        2. "{keyword}"와 자연스럽게 연결할 수 있으면 포함해주세요.
        3. 찬성 입장과 반대 입장을 DJ가 혼자 얘기하듯 대화체로 설명해주세요.
        4. 너무 딱딱하지 않게, 대화체/라디오 톤으로 작성하세요.
        5. 마지막에 청취자 참여 유도 멘트를 추가해주세요.  
           (예: "여러분은 어떻게 생각하시나요? 댓글이나 채팅으로 남겨주세요.")
        """
    else:  # English version
        base_instruction = f"""
        You are a warm and engaging radio DJ.  
        Please answer ONLY in English.
        
        Based on the listener's story below, create a "discussion topic" segment to share with the audience.

        Story Author: {author}
        Story Content:
        \"\"\"
        {content}
        \"\"\"

        Requirements:
        1. Suggest one clear discussion topic from the story. (e.g., "How often should couples stay in touch?")
        2. If possible, connect the topic naturally to the keyword "{keyword}".
        3. Explain both the pros and cons of the topic as if you are talking casually to your audience.
        4. Keep the tone conversational and radio-friendly, not too formal.
        5. End with a listener engagement cue, encouraging participation.  
           (e.g., "What do you think? Share your thoughts in the chat or comments!")
        """

    prompt = build_block_prompt(
        base_instruction=base_instruction,
        block_name="STORY_DISCUSSION" if language == "ko" else "STORY_DISCUSSION_EN",
        keyword=keyword,
        prev_type=prev_type,
        context=context
    )

    # Gemini 모델로 사연 토론 스크립트 생성
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    return response.text.strip()