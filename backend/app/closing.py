import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_closing_ment(keyword: str = None, language="ko"):
    today = datetime.datetime.now().strftime("%Y년 %m월 %d일 %A")

    if language == "ko":
        system_instruction = "당신은 감성적이고 따뜻한 AI 라디오 DJ입니다."
        prompt = f"{today}입니다. 라디오 방송을 마무리하며 청취자들에게 전하는 따뜻하고 편안한 클로징 멘트를 짧게 작성해주세요."
        if keyword:
            prompt += f" '{keyword}'의 여운이 남도록 마무리해 주세요."
    else:
        system_instruction = "You are a warm and emotional AI radio DJ."
        prompt = f"Today is {today}. Create a warm and gentle radio closing ment for the listeners to end the show."
        if keyword:
            prompt += f" Leave an impression related to '{keyword}'."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()