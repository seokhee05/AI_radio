import datetime
import os
from dotenv import load_dotenv
from google import genai

# .env에서 API 키 불러오기
load_dotenv()

# Gemini 클라이언트 초기화
client = genai.Client()

def generate_closing_ment(keyword: str = None, language="ko") -> str:
    today = datetime.datetime.now().strftime("%Y년 %m월 %d일 %A")

    if language == "ko":
        prompt = (
            f"오늘은 {today}입니다. AI 라디오 DJ로서 오늘 방송을 마무리하며, "
            f"오늘과 어울리는 잔잔한 인사로 정리해 주세요. "
            f"청취자에게 감성적이고 따뜻하게 인사하는 클로징 멘트를 만들어주세요. "
            f"진심 어린 인사와 함께, 각자의 일상으로 돌아가는 청취자들에게 따뜻한 작별 인사를 전해주세요. "
            f"너무 길지 않게 간결하게 작성해주세요."
        )
        if keyword:
            prompt += f" '{keyword}'와 관련된 메시지를 포함해 주세요."
        else:
            prompt += " 하루를 잘 마무리할 수 있도록 따뜻한 인사를 해주세요."

    else:  # 영어
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        prompt = (
            f"Today is {today}. As an AI radio DJ, please create a closing ment that gently wraps up today's broadcast. "
            f"Make it warm, heartfelt, and comforting, so listeners can return to their daily lives with a sense of peace. "
            f"Keep it concise and not too long."
        )
        if keyword:
            prompt += f" Please include a message related to '{keyword}'."
        else:
            prompt += " Offer listeners a kind farewell to end their day warmly."

    # Gemini 모델 호출
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    return response.text.strip()