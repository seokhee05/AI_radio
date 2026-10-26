import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from story.blocks.block_story import block_story
from story.story_filter.story_filter import story_filter
from story.story_filter.llm_story_filter import filter_stories_by_llm

# 💡 TTS 파일 생성 및 URL 반환 함수 임포트
from common.tts_utils import generate_tts_url

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


def run_story_radio(
    blocks: list[str],
    story_path="story/story.json",
    keyword=None,
    prev_type=None,
    context=None,
    language="ko"
) -> str:
    """
    사연 블록 실행 함수
    1. 사연 데이터 필터링 및 LLM 대본 합성
    2. 생성된 사연 대본을 바탕으로 CLOVA Voice TTS(noyj) 음성 파일 생성
    3. main.py 전달용 최종 대본 문자열 반환
    """
    if not keyword:
        raise ValueError("사연 파트 실행을 위해 필수 키워드가 입력되지 않았습니다. keyword 인자를 전달해주세요.")

    # 1. 사연 필터링
    try:
        story_filter()
        filter_stories_by_llm()
    except Exception as e:
        print(f"⚠️ 사연 필터링 단계 건너뜀/오류: {e}")

    # 2. JSON 사연 데이터 로드
    all_stories = []
    if os.path.exists(story_path):
        try:
            with open(story_path, "r", encoding="utf-8") as f:
                all_stories = json.load(f).get("stories", [])
        except Exception as e:
            print(f"⚠️ {story_path} 로드 실패: {e}")

    matched_stories = [s for s in all_stories if keyword in s.get("content", "")]
    processed_stories = []

    if matched_stories:
        print(f"[Info] JSON 데이터에서 '{keyword}' 관련 실제 사연 발견! 각색을 진행합니다.")
        for item in matched_stories[:3]:
            varied_content = paraphrase_story_with_llm(item["content"], keyword)
            processed_stories.append({
                "id": item.get("id", 1),
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

    # 3. 분량 조절 (TTS에 적합한 1,500자 기준)
    total_length = sum(len(s["content"]) for s in processed_stories)
    target_length = 1500

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

    # 4. 통합 사연 대본 생성
    integrated_script = ""
    if "story_main" in blocks or "story_discussion" in blocks:
        integrated_script = block_story(processed_stories, keyword, prev_type, context, language)

    # 문자열로 변환
    if isinstance(integrated_script, dict):
        final_text = integrated_script.get("content", str(integrated_script))
    else:
        final_text = str(integrated_script)

    # 5. 💡 사연 전담 성우('noyj')로 TTS MP3 오디오 파일 생성 및 유효성 검증
    if final_text.strip():
        print("🎙️ [story_radio] 사연 전담 성우(noyj) TTS 오디오 생성 중...")
        audio_url = generate_tts_url(text=final_text, speaker="noyj")
        print(f"✅ [story_radio] 사연 TTS 생성 완료: {audio_url}")

    return final_text