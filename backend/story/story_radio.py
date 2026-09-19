import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from story.blocks.block_story import block_story  # ✨ block_story 임포트
from story.story_filter.story_filter import story_filter
from story.story_filter.llm_story_filter import filter_stories_by_llm

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def paraphrase_story_with_llm(original_content: str, keyword: str) -> str:
    prompt = f"""
    다음은 실제 라디오 사연의 원본 코어(핵심 주제/감정)야:
    "{original_content}"
    
    사용자가 입력한 핵심 키워드는 "{keyword}"야.
    이 코어가 가진 감정과 상황을 바탕으로 하되, 주인공의 세부 디테일을 새롭게 창작해서 살을 듬뿍 붙여줘. 
    마치 생생한 실제 사연처럼 1인칭 라디오 사연 스타일로 완전히 재구성해줘.
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
    prompt = f"""
    당신은 라디오 프로그램의 청취자입니다. 
    사용자가 입력한 핵심 키워드 "{keyword}"를 주제로 하여, 실제로 라디오 게시판에 올라올 법한 생생하고 공감 가는 일상 사연 1개를 1인칭 시점으로 새롭게 작성해주세요.
    구체적인 상황과 감정을 살려 공감과 토론을 이끌어내기 좋게 만들어주세요.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
        )
        content = response.choices[0].message.content
        return content.strip() if content else f"오늘 '{keyword}'와 관련해서 소소한 일이 있었는데..."
    except Exception as e:
        print(f"LLM 사연 실시간 생성 중 오류 발생: {e}")
        return f"오늘 '{keyword}'와 관련해서 소소한 일이 있었는데, 참 많은 생각을 하게 되네요."

def run_story_radio(blocks: list[str], story_path="story/story.json", keyword=None, prev_type=None, context=None, language="ko") -> list[dict]:
    if not keyword:
        raise ValueError("사연 파트 실행을 위해 필수 키워드가 입력되지 않았습니다. keyword 인자를 전달해주세요.")

    # 사연 필터링
    story_filter()
    filter_stories_by_llm()

    with open(story_path, "r", encoding="utf-8") as f:
        all_stories = json.load(f)["stories"]

    matched_stories = [s for s in all_stories if keyword in s["content"]]
    processed_stories = []

    if matched_stories:
        print(f"[Info] JSON 데이터에서 '{keyword}' 관련 실제 사연 발견! 각색을 진행합니다.")
        for item in matched_stories[:3]:
            varied_content = paraphrase_story_with_llm(item["content"], keyword)
            processed_stories.append({
                "id": item["id"],
                "content": varied_content
            })
    else:
        print(f"[Info] JSON 데이터에 '{keyword}' 관련 사연이 없어 실시간 생성을 진행합니다.")
        for i in range(3):
            new_content = generate_story_with_llm(keyword)
            processed_stories.append({
                "id": i + 1,
                "content": new_content
            })

    # ✨ 핵심: 사연이 있든 없든 총 글자 수가 4000자보다 부족하면 4000자가 넘을 때까지 추가 생성!
    total_length = sum(len(s["content"]) for s in processed_stories)
    target_length = 4000  # 기준 글자 수

    additional_id = len(processed_stories) + 1
    while total_length < target_length:
        print(f"[Info] 현재 사연 총 글자 수가 {total_length}자로 부족하여, 추가 사연을 생성합니다.")
        new_content = generate_story_with_llm(keyword)
        processed_stories.append({
            "id": additional_id,
            "content": new_content
        })
        total_length += len(new_content)
        additional_id += 1

    # ✨ blocks에 사연 관련 블록이 포함되어 있다면 block_story 호출
    script_results = []
    if "story_main" in blocks or "story_discussion" in blocks:
        integrated_script = block_story(processed_stories, keyword, prev_type, context, language)
        script_results.append(integrated_script)

    return script_results