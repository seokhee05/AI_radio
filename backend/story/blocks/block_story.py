import os
import re
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def block_story(stories: list[dict], keyword: str, prev_type=None, context=None, language="ko") -> dict:
    # ✨ 사연을 최대 2~3개만 추려서 전달
    selected_stories = stories[:3]
    
    stories_text = ""
    for idx, s in enumerate(selected_stories, 1):
        stories_text += f"\n[청취자 사연 {idx}]\n{s['content']}\n"

    prompt = f"""
    당신은 심야 라디오 프로그램의 감성적이고 다정다감한 메인 DJ입니다.
    사용자가 입력한 오늘의 핵심 키워드는 "{keyword}"입니다.
    
    다음은 오늘 방송에서 소개할 청취자들의 사연 모음입니다 (총 {len(selected_stories)}개):
    {stories_text}
    
    위 사연들을 바탕으로 **공백 포함 4000자 이상의 매우 풍성하고 깊이 있는 라디오 대본**을 작성해주세요.
    
    [가장 중요한 작성 원칙 - 절대 준수!]
    1. 사연은 준비된 2~3개만 집중적으로 다루세요. 사연을 대충 요약하지 말고, DJ가 마이크 앞에서 편지를 읽어 내려가듯 생생한 1인칭(또는 당사자 시점)의 내레이션으로 온전히 낭독해주세요.
    2. **[핵심] 각 사연이 끝난 직후에 DJ가 건네는 공감 멘트와 위로의 말을 평소보다 훨씬 길고 깊이 있게 확장해서 풀어주세요.** 단순한 한 줄 위로가 아니라, 그 사연 속 감정에 완전히 몰입하여 청취자의 마음을 어루만져 주는 따뜻한 독백을 아주 길고 풍성하게 채워주세요.
    3. 사연과 사연 사이, 그리고 토론으로 넘어가는 과정이 어색하지 않게 물 흐듯 자연스럽게 이어져야 합니다.
    
    [방송 흐름 가이드라인]
    1. [오프닝]: 키워드 "{keyword}"와 관련하여, 오늘 밤 청취자들에게 건네는 따뜻하고 감성적인 오프닝 인사를 길고 깊이 있게 열어주세요.
    2. [사연 낭독 및 깊은 공감]: 첫 번째 사연을 생생하게 낭독하고, 이 사연에 얽힌 감정과 상황에 대해 DJ의 진심 어린 공감과 위로를 아주 길고 풍부하게 나누세요. 이어서 두 번째(및 세 번째) 사연도 동일하게 낭독하고 깊은 공감 멘트를 충분히 전해주세요.
    3. [DJ의 개인 소견]: 사연들과의 깊은 교감이 끝난 직후, "이 사연들을 하나씩 읽어 내려가는데 문득 제 지난날이 스치더라고요..."라며 DJ 본인의 솔직한 경험과 생각을 진솔하게 털어놓으세요. 그리고 이 사연 속 고민이 오늘 우리가 함께 생각해 봐야 할 문제라며 자연스럽게 토론 국면으로 판을 깔아주세요.
    4. [심층 찬반 토론 및 클로징]: 방금 나눈 사연의 여운을 이어받아, 청취자들과 치열하게 속마음을 나눌 수 있는 구체적이고 흥미로운 찬반 토론 주제를 던져주세요. "여러분은 과연 어떤 선택을 하시겠습니까?"라는 깊이 있는 질문을 던지며 여운 있게 방송을 마무리해주세요.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=4096,
        )
        content = response.choices[0].message.content.strip()
        
        # 🧹 [안전 장치] 대괄호로 된 모든 목차 타이틀 및 불필요한 레이블을 정규식으로 완벽 제거
        content = re.sub(r"\[.*?\]", "", content)
        content = re.sub(r"\n{3,}", "\n\n", content).strip()

    except Exception as e:
        print(f"통합 사연 생성 중 오류 발생: {e}")
        content = "오늘 준비한 사연들을 전해드렸습니다..."

    return {
        "type": "STORY",
        "content": content
    }