import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def block_story(stories: list[dict], keyword: str, prev_type=None, context=None, language="ko") -> dict:
    stories_text = ""
    for idx, s in enumerate(stories, 1):
        stories_text += f"\n[사연 {idx}]\n{s['content']}\n"

    prompt = f"""
    당신은 심야 라디오 프로그램의 감성적이고 베테랑인 메인 DJ입니다.
    사용자가 입력한 오늘의 핵심 키워드는 "{keyword}"입니다.
    
    다음은 오늘 방송에서 소개할 청취자들의 사연 모음입니다:
    {stories_text}
    
    위 사연들을 바탕으로 아래의 **[방송 순서 1단계부터 4단계까지]**를 빠짐없이 모두 거치며, **반드시 공백 포함 4000자 이상의 매우 길고 풍성한 라디오 대본**을 작성해주세요. 절대 중간에 내용을 생략하거나 짧게 끝내지 마세요.
    
    [방송 순서 및 가이드라인]
    1단계 [오프닝]: 키워드 "{keyword}"와 관련하여, 오늘 밤 청취자들에게 건네는 따뜻하고 감성적인 오프닝 인사를 길고 깊이 있게 열어주세요.
    2단계 [사연 소개 및 공감]: 준비된 사연들을 처음부터 매끄럽게 이어지는 하나의 코스로 소개해주세요. (사연을 넘어갈 때마다 "안녕하세요" 같은 불필요한 첫인사를 반복하지 말고, 하나의 긴 이야기나 편지 모음을 읽어 내려가듯 자연스럽게 연결할 것!) 각 사연의 주인공이 처한 상황과 감정에 진심으로 공감하며 위로의 말을 충분히 길고 가슴 따뜻하게 건네주세요.
    3단계 [DJ의 개인 소견 - 필수!]: 모든 사연 소개가 끝난 뒤, 곧바로 토론으로 넘어가기 전에 반드시 "저도 이 사연들을 하나씩 읽으면서 문득 제 지난날이 스쳤는데요...", "개인적으로 저는 이번 사연들을 보며 이런 생각이 들더라고요"라며 DJ 본인의 솔직한 경험(예: 학창 시절 짝사랑이나 전남친과의 연애 시절 일화 등)을 곁들여 인간적인 생각과 소견을 아주 진솔하게 털어놓아 주세요.
    4단계 [토론 및 클로징]: DJ 자신의 생각이 끝난 뒤에, 방금 나눈 여운을 이어받아 청취자들과 조금 더 깊은 속마음을 나누는 시간으로 넘어가세요. 사연 속 갈등 요소를 바탕으로 **"~입장"과 "~입장"처럼 명확하게 양극단으로 나뉘는 구체적이고 흥미로운 찬반 토론 주제**를 던져주고, "이건 무조건 이해해 줘야지 싶으신가요, 아니면 스스로 노력해야지 생각하시나요?"라며 청취자들에게 깊이 있는 질문을 던지며 방송을 마무리해주세요.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=2500,
        )
        content = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"통합 사연 생성 중 오류 발생: {e}")
        content = "오늘 준비한 사연들을 전해드렸습니다..."

    return {
        "type": "STORY",
        "content": content
    }