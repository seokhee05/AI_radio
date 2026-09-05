import datetime
import os
from dotenv import load_dotenv
from google import genai

# .env에서 API 키 불러오기
load_dotenv()

# Gemini 클라이언트 초기화 (환경 변수 GEMINI_API_KEY를 자동으로 인식함)
client = genai.Client()

def generate_opening_ment(keyword: str = None, language="ko"):
    today = datetime.datetime.now().strftime("%Y년 %m월 %d일 %A")
    
    if language == "ko":
        prompt = f"{today}입니다. AI 라디오 DJ로서 오늘 하루를 마무리하는 청취자들에게 감성적이면서도 따뜻한 오프닝 멘트를 너무 길지 않게 만들어주세요. "
        if keyword:
            prompt += f"'{keyword}'와 관련된 계절감이나 분위기를 반영해 주세요."
        else:
            prompt += "청취자에게 친근하게 하루를 마무리할 수 있도록 작성해주세요."
    else:  # English
        prompt = f"Today is {today}. As an AI radio DJ, please create a warm and emotional opening ment for listeners wrapping up their day. Keep it concise and heartfelt. "
        if keyword:
            prompt += f"Make sure to reflect the seasonal mood or atmosphere related to '{keyword}'."
        else:
            prompt += "Make it friendly so listeners can end their day on a comforting note."

    # Gemini 모델 호출 (gemini-3.6-flash 또는 gemini-1.5-flash 사용 가능)
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    return response.text.strip()