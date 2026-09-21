import os
import re
from dotenv import load_dotenv
from openai import OpenAI
from news.llm.prompt_builder import build_summary_prompt

load_dotenv()

# OpenAI 클라이언트 초기화 (OPENAI_API_KEY 환경변수 자동 인식)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 기사 본문을 받아 요약과 DJ 멘트를 생성하는 함수
def summarize_article(article_text: str,
                    model: str = "gpt-4o-mini",
                    mode: str = "headline", 
                    prev_type: str = None,
                    context: str = None,
                    block_name: str = "NEWS",
                    language: str = "ko"
                    ) -> dict:
    
    # ⏱️ 4,000~5,000자(12~15분) 목표 분량 및 토큰 설정
    if mode == "deep":
        target_length = "공백 포함 4,000~4,500자 (약 12~15분 분량)"
        max_output_tokens = 4096  # 4,000자 이상 길이를 온전히 뽑기 위한 토큰 확보
    elif mode == "headline":
        target_length = "공백 포함 600~700자 (핵심 팩트와 배경 설명 포함)"
        max_output_tokens = 1500
    elif mode == "current":
        target_length = "공백 포함 2,000~2,500자"
        max_output_tokens = 2500
    else:
        target_length = "공백 포함 800~1,000자"
        max_output_tokens = 1500

    prompt = build_summary_prompt(
        article_text,
        target_length=target_length,
        mode=mode,
        prev_type=prev_type,
        context=context,
        block_name=block_name,
        language=language
    )

    try:
        # 모드별 진행자 페르소나 설정 (시스템 블록 이름/전환 멘트 엄금 조건 추가)
        if language == "ko":
            if mode == "headline":
                system_content = (
                    "당신은 신속하고 명확하게 소식을 전달하는 라디오 뉴스 앵커입니다. "
                    "군더더기 없는 두괄식 구어체(~습니다, ~입니다)로 팩트와 전말을 매끄럽게 전달하세요. "
                    "마크다운(#, ** 등)이나 이모지는 일절 쓰지 마세요. "
                    "특히 '이제 [DEEP_NEWS] 코너로...' 같은 시스템 블록 이름이나 코너 전환 안내 멘트는 절대 포함하지 마세요."
                )
            else:
                system_content = (
                    "당신은 청취자와 시사 이슈를 깊이 있게 나누는 AI 라디오 진행자입니다. "
                    "추상적인 위로보다는 사건의 전말과 쟁점, 배경을 알기 쉽게 풀어서 설명해주고, "
                    "청취자가 귀로 들었을 때 몰입할 수 있도록 자연스러운 방송 구어체로 작성하세요. "
                    "마크다운(#, ** 등)이나 이모지는 일절 쓰지 마세요. "
                    "특히 '이제 [DEEP_NEWS] 코너로...' 같은 시스템 블록 이름이나 코너 전환 안내 멘트는 절대 포함하지 마세요."
                )
        else:
            if mode == "headline":
                system_content = (
                    "You are a professional radio news anchor delivering concise, factual headline updates. "
                    "Do not use markdown, emojis, or system block transition phrases like DEEP_NEWS."
                )
            else:
                system_content = (
                    "You are an empathetic and insightful AI radio host exploring news topics in depth. "
                    "Do not use markdown, emojis, or system block transition phrases like DEEP_NEWS."
                )

        use_model = model
        if "gemini" in model.lower():
            use_model = "gpt-4o-mini"

        # OpenAI Chat Completion 호출
        response = client.chat.completions.create(
            model=use_model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=max_output_tokens,  # 토큰 제한 해제
        )

        script = response.choices[0].message.content.strip()

        # 🧹 [안전 장치] 어색한 시스템 코너 전환 멘트 및 블록 이름 정규식 강제 제거
        script = re.sub(r"이제\s*\[?DEEP_NEWS\]?\s*코너로.*?(넘어가겠습니다|시작하겠습니다|살펴보겠습니다)\.?", "", script).strip()
        script = re.sub(r"\[?DEEP_NEWS\]?", "", script).strip()

        return {
            "success": True,
            "script": script,
        }

    except Exception as e:
        return {
            "success": False,
            "script": None,
            "error": str(e),
        }