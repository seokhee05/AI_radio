import json
import os
from dotenv import load_dotenv
from google import genai
from tqdm import tqdm

load_dotenv()
# Gemini 클라이언트 초기화
client = genai.Client()
    
def filter_stories_by_llm(input_path="story/candidate_stories.json", output_path="story/story.json"):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        candidates = data["candidates"]

    formatted_stories = "\n\n".join(
        f"[{i+1}] {item['content'].strip()}" for i, item in enumerate(candidates)
    )

    prompt = f"""
        당신은 감성적인 AI 라디오 DJ입니다.
        다음은 청취자들이 보낸 사연 후보입니다. 이 중에서 청취자들과 함께 나누면 좋을 사연 6개를 골라주세요.

        기준:
        - 감동적이거나 공감할 수 있는 사연
        - 따뜻하거나 생각할 거리를 주는 이야기
        - 단순한 신청곡, 인사, 날씨 얘기, 짧은 코멘트는 제외

        사연 목록:
        \"\"\"
        {formatted_stories}
        \"\"\"

        선택한 사연 번호만 콤마로 구분해서 아래 형식으로 답해주세요.  
        예: 2, 5, 8
        """

    try:
        # Gemini 모델 호출 (텍스트 생성)
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )
        result = response.text.strip()
        print("LLM 응답:", result)

        selected_indices = []
        for part in result.split(","):
            try:
                idx = int(part.strip()) - 1
                if 0 <= idx < len(candidates):
                    selected_indices.append(idx)
            except ValueError:
                continue

        selected_stories = [candidates[i] for i in selected_indices]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"stories": selected_stories}, f, ensure_ascii=False, indent=2)

        print(f"LLM 선정 완료: {len(selected_stories)}개 사연 저장 → {output_path}")

    except Exception as e:
        print("Gemini API 오류:", e)

if __name__ == "__main__":
    filter_stories_by_llm()