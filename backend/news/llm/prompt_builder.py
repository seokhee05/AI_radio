def build_summary_prompt(article_text: str, 
                         target_length: str = "700~800자", mode: str = "headline",
                         prev_type: str = None,
                         context: str = None,
                         block_name: str = "NEWS",
                         language: str = "ko") -> str:
    if language == "ko":
        if mode == "deep":
            dj_instruction = (
                "뉴스를 심층적으로 요약하고, "
                "사회적 의미와 제도적 문제를 짚어주세요. "
                "찬성과 반대의 시각을 균형 있게 다루고, "
                "청취자가 생각을 확장할 수 있도록 질문을 2~3개 던져주세요. "
                "예: '여러분은 책임이 개인에게 있다고 보시나요, 아니면 제도의 문제일까요?' "
                "라디오 대본처럼 자연스럽게 이어가되, 인사말은 생략해주세요."
            )
        elif mode == "headline":
            dj_instruction = (
                "뉴스를 간결하게 요약하고, "
                "DJ가 청취자와 대화를 나누듯 편안하게 설명해주세요. "
                "짧은 공감이나 질문을 섞어, 청취자가 쉽게 반응할 수 있도록 해주세요. "
                "라디오 대본처럼 자연스럽게 작성하고, 인사말은 생략해주세요."
            )
        else:  # short/current
            dj_instruction = (
                "뉴스의 핵심만 짧고 간단하게 전해주세요. "
                "한두 문장으로 자연스럽게 마무리되는 라디오 대본처럼 작성하세요."
            )

        transition_part = ""
        if prev_type:
            transition_part = f"""
            직전 코너는 [{prev_type}]이었고, 분위기는 다음과 같았습니다:
            {context}

            이를 자연스럽게 이어서, 이제 [{block_name}] 코너를 진행하는 멘트로 연결해주세요.
            """

        return f"""
        {transition_part}
        
        다음은 KBS 뉴스 기사 본문입니다.  
        이 본문을 바탕으로 **라디오 DJ 스크립트**를 작성해주세요.  

        요구사항:
        1. 기사 내용을 {target_length} 정도 분량으로 요약하세요.
        2. 단순한 사실 나열이 아니라, 청취자가 왜 중요한지 이해할 수 있도록 풀어주세요.
        3. DJ 멘트 형식으로 작성하고, "해설 요약:"이나 "DJ 멘트:" 같은 라벨은 쓰지 마세요.
        4. {dj_instruction}

        [기사 본문]
        {article_text}
        """
    else:  # 영어 버전
        if mode == "deep":
            dj_instruction = (
                "Provide an in-depth summary of the news. "
                "Highlight its social significance and structural issues. "
                "Balance both supporting and opposing perspectives, "
                "and include 2–3 reflective questions to expand the listener’s thoughts. "
                "For example: 'Do you think the responsibility lies with individuals, or is it a systemic issue?' "
                "Write it as a natural radio script, but omit greetings."
            )
        elif mode == "headline":
            dj_instruction = (
                "Summarize the news concisely, "
                "and explain it in a conversational tone as if the DJ is chatting with listeners. "
                "Add short empathetic comments or questions so the audience can easily engage. "
                "Write it as a natural radio script, but omit greetings."
            )
        else:  # short/current
            dj_instruction = (
                "Deliver only the core points briefly. "
                "Wrap it up naturally in one or two sentences as if it’s part of a radio script."
            )

        transition_part = ""
        if prev_type:
            transition_part = f"""
            The previous segment was [{prev_type}], with the following atmosphere/context:
            {context}

            Please transition naturally into the [{block_name}] segment.
            """

        return f"""
        {transition_part}
        
        Below is a KBS news article.  
        Based on this article, please create a **radio DJ script**.  

        Requirements:
        1. Summarize the article in about {target_length}.
        2. Go beyond listing facts—help listeners understand why the news matters.
        3. Write it in the style of a DJ script, without labels like "Summary:" or "DJ Ment:".
        4. {dj_instruction}

        [Article Body]
        {article_text}
        """