import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from story.blocks.block_story_main import block_story_main
from story.blocks.block_story_discussion import block_story_discussion
from story.story_filter.story_filter import story_filter
from story.story_filter.llm_story_filter import filter_stories_by_llm
from story.story_filter.select_discussion_stories import select_discussion_stories

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def paraphrase_story_with_llm(original_content: str, keyword: str) -> str:
    """
    JSON에서 찾은 진짜 원본 사연을 바탕으로, 디테일을 새롭게 창작하여 중복 없이 각색하는 함수
    """
    prompt = f"""
    다음은 실제 라디오 사연의 원본 코어(핵심 주제/감정)야:
    "{original_content}"
    
    사용자가 입력한 핵심 키워드는 "{keyword}"야.
    이 코어가 가진 감정과 상황을 바탕으로 하되, 실행할 때마다 주인공의 세부 디테일(나이, 장소, 구체적인 행동 등)을 새롭게 창작해서 살을 듬뿍 붙여줘. 
    마치 매번 다른 청취자가 보낸 생생한 실제 사연처럼 1인칭 라디오 사연 스타일로 완전히 재구성해줘.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM 각색 중 오류 발생, 원본 사연으로 대체합니다: {e}")
        return original_content

def generate_story_with_llm(keyword: str) -> str:
    """
    JSON에 일치하는 사연이 없을 때, 키워드 기반으로 완전히 새로운 사연을 실시간 생성하는 함수 (Fallback)
    """
    prompt = f"""
    당신은 라디오 프로그램의 청취자입니다. 
    사용자가 입력한 핵심 키워드 "{keyword}"를 주제로 하여, 실제로 라디오 게시판에 올라올 법한 생생하고 공감 가는 일상 사연 1개를 1인칭 시점으로 새롭게 작성해주세요.
    구체적인 상황과 감정, 소소한 디테일을 살려 공감과 토론을 이끌어내기 좋게 만들어주세요.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM 사연 실시간 생성 중 오류 발생: {e}")
        return f"오늘 '{keyword}'와 관련해서 소소한 일이 있었는데, 참 많은 생각을 하게 되네요."

def run_story_radio(blocks: list[str], story_path="story/story.json", keyword=None, prev_type=None, context=None, language="ko") -> str:
    # 1. 키워드 필수 입력 검증
    if not keyword:
        raise ValueError("사연 파트 실행을 위해 필수 키워드가 입력되지 않았습니다. keyword 인자를 전달해주세요.")

    output_lines = []

    # 사연 필터링 + 선정 (기존 파이프라인 유지)
    story_filter()
    filter_stories_by_llm()

    # 사연 불러오기
    with open(story_path, "r", encoding="utf-8") as f:
        all_stories = json.load(f)["stories"]

    # 2. [하이브리드 전략] 
    # ① JSON 파일에서 키워드와 연관된 진짜 사연이 있는지 탐색
    matched_stories = [s for s in all_stories if keyword in s["content"]]
    
    processed_stories = []

    if matched_stories:
        # 🟢 케이스 A: 진짜 사연이 존재함 -> 원본을 가져와서 LLM으로 신선하게 각색(변주)
        print(f"[Info] JSON 데이터에서 '{keyword}' 관련 실제 사연 발견! 각색을 진행합니다.")
        for item in matched_stories:
            varied_content = paraphrase_story_with_llm(item["content"], keyword)
            processed_stories.append({
                "id": item["id"],
                "content": varied_content
            })
    else:
        # 🟡 케이스 B: 관련 사연이 없음(데이터 부족) -> LLM이 실시간으로 새로운 사연을 창조(생성)하여 메꿈
        print(f"[Info] JSON 데이터에 '{keyword}' 관련 사연이 없어 실시간 생성을 진행합니다.")
        for i in range(2):  # 토론 연계를 위해 2개 생성
            new_content = generate_story_with_llm(keyword)
            processed_stories.append({
                "id": i + 1,
                "content": new_content
            })

    # 토론 주제로 발전할 사연 번호 선택
    discussion_indices = select_discussion_stories(processed_stories)

    # 사연 공감 및 토론 멘트 생성
    for i, item in enumerate(processed_stories):
        if "story_main" in blocks:
            output_lines.append(block_story_main(item, keyword, prev_type, context, language))
        if "story_discussion" in blocks and i in discussion_indices:
            output_lines.append(block_story_discussion(item, keyword, prev_type, context, language))

    return "\n\n".join(output_lines)

if __name__ == "__main__":
    pass