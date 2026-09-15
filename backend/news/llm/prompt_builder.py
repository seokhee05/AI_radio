def build_summary_prompt(article_text: str, 
                        target_length: str = "700~800자", 
                        mode: str = "headline",
                        prev_type: str = None,
                        context: str = None,
                        block_name: str = "NEWS",
                        language: str = "ko") -> str:
    
    # 🎧 CLOVA Voice 및 오디오 낭독 최적화 공통 규칙
    tts_rules_ko = """
    - [음성 낭독 규칙 - 필수 준수]
    1. 마크다운 기호(예: **, ##, -, > 등)와 이모지는 절대로 사용하지 마세요. 오직 소리 내어 읽을 순수 한글 텍스트만 출력하세요.
    2. "해설:", "DJ 멘트:", "오프닝:" 같은 분류 라벨이나 괄호 설명을 절대 적지 마세요.
    3. 날짜, 수치, 단위, 영문 약어는 아나운서가 읽는 한글 발음(예: 3.5% -> 삼 점 오 퍼센트, AI -> 에이아이)을 최대한 활용해 읽기 편하게 작성하세요.
    4. 호흡이 자연스럽도록 긴 문장은 쉼표(,)를 적절히 배치하여 끊어 읽기 좋게 만드세요.
    5. 본문에 포함된 취재 기자 이름이나 "KBS 뉴스 누구입니다" 같은 서명 멘트, 크레딧은 절대로 대본에 넣지 마세요.
    """

    tts_rules_en = """
    - [TTS & Speech Rules - Strict Requirements]
    1. NEVER use markdown symbols (**, ##, -, >) or emojis. Output only plain spoken text.
    2. NEVER include labels like "DJ:", "Segment:", or parenthetical stage directions.
    3. Spell out acronyms and special symbols in easy-to-read spoken forms.
    4. Use natural commas and periods to ensure comfortable pacing for voice synthesis.
    """

    if language == "ko":
        if mode == "deep":
            dj_instruction = (
                "사건의 발단과 전말, 사회적 파급 효과, 제도적 한계를 다각도로 깊이 있게 서술하세요. "
                "단순한 요약에 그치지 말고 역사적 배경과 찬반 양측의 논리를 풍성하게 풀어내어, "
                f"반드시 목표 분량({target_length})을 채울 수 있도록 충실하게 작성하세요. "
                "★ [매우 중요] 제공된 기사 본문 중 사용자가 검색한 메인 키워드(주제)와 직접적인 관련이 없거나, 곁다리로 섞인 엉뚱한 사건(예: 타 분야 경제 뉴스, 부동산, 금리 등)은 대본에 절대로 포함시키지 말고 철저히 배제하세요. "
                "마지막에는 청취자가 스스로 생각해볼 수 있는 질문 2~3개를 던지며 마무리하세요."
            )
        elif mode == "headline":
            dj_instruction = (
                "라디오 뉴스 앵커 톤으로 신속하고 정확하게 핵심 팩트를 두괄식으로 전달하세요. "
                "이어서 청취자가 맥락을 이해할 수 있는 짤막한 배경 설명을 덧붙이세요. "
                "불필요한 감성 표현은 줄이고, 방송 뉴스 특유의 정갈한 구어체(~습니다, ~입니다)를 유지하세요."
            )
        elif mode == "current":
            dj_instruction = (
                "현재 진행 중인 시사 현안의 핵심 쟁점과 양측 입장을 균형 있게 대담하듯 풀어주세요. "
                "청취자가 복잡한 뉴스를 한눈에 파악할 수 있도록 친절하고 몰입감 있는 방송 톤을 사용하세요."
            )
        else:
            dj_instruction = "핵심 팩트만 명확하게 전달하며 자연스러운 구어체로 맺어주세요."

        transition_part = ""
        if prev_type:
            transition_part = f"""
직전 코너: [{prev_type}]
직전 내용 요약: {context}
위 맥락에서 이번 [{block_name}] 코너로 매끄럽게 넘어가는 자연스러운 연결 멘트로 시작하세요.
"""

        return f"""
{transition_part}

다음 기사 본문을 바탕으로 실제 라디오 방송에서 아나운서/DJ가 읽을 **라디오 대본**을 작성해주세요.

[작성 요구사항]
1. 분량 기준: {target_length} 분량을 축소하거나 요약해 버리지 말고 충분한 디테일을 담아 완주하세요.
2. 진행 지침: {dj_instruction}
{tts_rules_ko}

[기사 본문]
{article_text}
""".strip()

    else:  # 영어 버전
        if mode == "deep":
            dj_instruction = (
                "Explore the issue in depth, covering its history, structural challenges, and social implications. "
                f"Do not truncate or over-condense; fulfill the target length ({target_length}) thoroughly. "
                "Conclude with 2-3 thoughtful open questions for listeners."
            )
        elif mode == "headline":
            dj_instruction = (
                "Deliver core facts quickly and accurately in a professional radio anchor tone. "
                "Follow up with concise background context using clean, broadcast-style spoken delivery."
            )
        elif mode == "current":
            dj_instruction = (
                "Break down current debates and multiple perspectives in an accessible, engaging manner."
            )
        else:
            dj_instruction = "Deliver the key takeaway smoothly in spoken English."

        transition_part = ""
        # 첫 번째 기사이거나 이전 블록이 없을 때는 코너 진입 멘트를 강제하지 않음
        if prev_type and prev_type != "headline_item":
            transition_part = f"""
직전 방송 내용 요약: {context}
위 내용에 이어 다음 순서로 매끄럽게 넘어가는 1~2문장의 자연스러운 라디오 전환 멘트를 대본 첫머리에 포함하세요. (단, '{block_name}' 같은 영어 단어나 대괄호 태그는 절대 발음하지 마세요.)
"""

        return f"""
{transition_part}

Please write a broadcast radio script based on the following news article.

[Requirements]
1. Target Length: Fulfill approximately {target_length} without condensing excessively.
2. Direction: {dj_instruction}
{tts_rules_en}

[Article Body]
{article_text}
""".strip()