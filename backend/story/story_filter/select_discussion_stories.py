import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
# Gemini 클라이언트 초기화
client = genai.Client()

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

    # Gemini 모델 호출
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )
    result = response.text.strip()

    indices = []
    for part in result.split(","):
        try:
            idx = int(part.strip()) - 1
            if 0 <= idx < len(stories):
                indices.append(idx)
        except ValueError:
            continue

    return indices