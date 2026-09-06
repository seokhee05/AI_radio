import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI

# .env에서 API 키 불러오기
load_dotenv()

# OpenAI 클라이언트 초기화 (기본적으로 환경 변수 OPENAI_API_KEY를 인식합니다)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_opening_ment(keyword: str = None, language="ko"):
    today = datetime.datetime.now().strftime("%Y년 %m월 %d일 %A")
    
    if language == "ko":
        system_instruction = "당신은 감성적이고 따뜻한 AI 라디오 DJ입니다."
        prompt = f"{today}입니다. AI 라디오 DJ로서 오늘 하루를 마무리하는 청취자들에게 감성적이면서도 따뜻한 오프닝 멘트를 너무 길지 않게 만들어주세요. "
        if keyword:
            prompt += f"'{keyword}'와 관련된 계절감이나 분위기를 반영해 주세요."
        else:
            prompt += "청취자에게 친근하게 하루를 마무리할 수 있도록 작성해주세요."
    else:  # English
        system_instruction = "You are a warm and emotional AI radio DJ."
        prompt = f"Today is {today}. As an AI radio DJ, please create a warm and emotional opening ment for listeners wrapping up their day. Keep it concise and heartfelt. "
        if keyword:
            prompt += f"Make sure to reflect the seasonal mood or atmosphere related to '{keyword}'."
        else:
            prompt += "Make it friendly so listeners can end their day on a comforting note."

    # OpenAI GPT 모델 호출 (gpt-4o-mini 또는 gpt-4o 사용 권장)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()