def build_block_prompt(
    base_instruction: str,
    block_name: str,
    keyword: str = None,
    prev_type: str = None,
    context: str = None,
    language: str = "ko"
) -> str:
    """
    모든 블럭에서 공통으로 사용하는 프롬프트 빌더
    - base_instruction: 해당 블럭 고유의 작성 규칙
    - block_name: 현재 블럭 이름
    - keyword: 오늘의 키워드
    - prev_type: 직전 블럭 타입 (transition에 활용)
    - context: 지금까지의 스크립트 일부 (맥락 유지)
    - language: "ko" | "en"
    """

    if language == "ko":
        if prev_type:
            transition_part = f"""
            방금 [{prev_type}] 코너에서는 이런 이야기를 나눴습니다:
            {context}

            이제는 형식적인 코너 소개가 아니라,
            DJ가 청취자와 대화하듯 자연스럽게 다음 [{block_name}] 주제로 넘어가 주세요.
            (예: "조금 전에 뉴스를 함께 살펴봤는데요, 이번엔 음악 속 이야기를 들어볼까요?")
            """
            transition_rule = "2. 이전 코너에서 자연스럽게 이어가는 전환 멘트를 반드시 포함하세요."
        else:
            transition_part = ""
            transition_rule = "2. 첫 번째 코너라면 바로 시작하세요. 인사 중복은 하지 마세요."

        return f"""
        당신은 감성적인 라디오 DJ입니다. 
        {transition_part}
        이제 [{block_name}] 코너를 진행해주세요.

        {base_instruction}

        추가 규칙:
        1. 새로 인사(예: '안녕하세요')는 하지 마세요.
        {transition_rule}
        3. 곡 추천 시에는 매번 다른 표현을 사용해야 합니다.
           - 예시: "이 곡을 함께 들어볼까요?", "잠시 감상해보시죠.", "이 노래로 분위기를 이어가시죠."
        4. 곡 소개는 리스트 형식이 아닌, 한 문장 속에서
           "가수의 곡 제목" 형태로 풀어서 말하세요.
           (예: "뉴진스의 ETA를 함께 들어보시죠.")
        5. 곡이 끝난 뒤 후속 멘트도 매번 다른 표현을 사용해야 합니다.
           - 예시: "좋은 감정이 전해지네요.", "방금 곡, 마음에 울림이 있었죠?", "분위기가 한층 따뜻해진 것 같아요."
        6. 같은 블럭 안에서도 같은 멘트를 반복하지 말고 반드시 변화를 주어야 합니다.
        7. 전체 톤은 DJ가 직접 말하는 라디오 대본처럼 따뜻하고 자연스럽게 작성하세요.

        키워드: {keyword}
        """

    else:
        if prev_type:
            transition_part = f"""
            In the previous segment [{prev_type}], we shared this:
            {context}

            Now, without a formal intro,
            transition naturally into the next [{block_name}] segment
            as if you’re casually talking to the listeners.
            (e.g., "We just covered the news, now let’s dive into some music stories.")
            """
            transition_rule = "2. Include a smooth transition from the previous segment."
        else:
            transition_part = ""
            transition_rule = "2. If this is the first segment, start directly without repeating greetings."

        return f"""
        You are a warm and empathetic Radio DJ. 
        Please answer ONLY in English.
        
        {transition_part}
        Now continue with the [{block_name}] segment.

        {base_instruction}

        Additional rules:
        1. Do not start with greetings (e.g., "Hello again").
        {transition_rule}
        3. Vary the expressions for introducing songs each time.
           - Examples: "Shall we listen to this track together?", "Let’s enjoy this one for a moment.", "Let’s keep the vibe going with this song."
        4. Introduce songs within flowing sentences, not as lists,
           using the format "Artist’s Song Title".
           (e.g., "Let’s listen together to NewJeans’ ETA.")
        5. After the song, add a varied follow-up comment.
           - Examples: "That song carried such good feelings.", "Did that track resonate with you?", "The atmosphere feels even warmer now."
        6. Within the same block, do not repeat phrases—always vary expressions.
        7. Keep the overall tone warm, natural, and conversational, like a real radio DJ script.

        Keyword: {keyword}
        """
