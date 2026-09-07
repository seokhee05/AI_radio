import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def select_discussion_stories(stories):
    """LLM으로 토론 주제로 발전할 사연을 골라줌"""
    formatted_stories = "\n\n".join(
        f"[{i+1}] {s['content']}" for i, s in enumerate(stories)
    )

    prompt = f"""
    당신은 라디오 방송 작가입니다. 아래 사연 목록 중에서
    청취자와 함께 토론하면 재미있을 만한 사연을 골라주세요.

    기준:
    - 사회적 이슈, 가치관 차이, 생활 속에서 의견이 갈릴만한 주제
    - 단순 감정 공유, 개인적인 사소한 경험은 제외
    - 최소 1개, 최대 2개 추천

    사연 목록:
    \"\"\" 
    {formatted_stories}
    \"\"\"

    선택한 사연 번호만 콤마로 구분해서 출력해주세요.  
    예: 2, 5
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )
    result = response.choices[0].message.content.strip()

    indices = []
    for part in result.split(","):
        try:
            idx = int(part.strip()) - 1
            if 0 <= idx < len(stories):
                indices.append(idx)
        except ValueError:
            continue

    return indices