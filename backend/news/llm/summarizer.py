import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from news.llm.prompt_builder import build_summary_prompt
import re

load_dotenv()
# Gemini 클라이언트 초기화
client = genai.Client()

# 기사 본문을 받아 요약과 DJ 멘트를 생성하는 함수
def summarize_article(article_text: str,
                        model: str = "gemini-3.6-flash", # 모델명도 제미나이로 기본값 변경
                        mode: str = "headline", 
                        prev_type: str = None,
                        context: str = None,
                        block_name: str = "NEWS",
                        language: str = "ko"
                        ) -> dict:
    if mode == "deep":
        target_length = "1500~2000자 (10~15분 분량)"
    elif mode == "headline":
        target_length = "700~800자 (5분 분량)"
    else:  # current news or short
        target_length = "300~400자 (2~3분 분량)"

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
        if language == "ko":
            system_content = (
                "당신은 청취자와 공감하며 이야기 나누는 감성적인 AI 뉴스 DJ입니다. "
                "감성적인 위로보다는 해당 뉴스 주제와 연결된 DJ 멘트를 만들어주세요. "
                "멘트는 지나치게 추상적이지 않고, 실제 뉴스 이슈에 대해 DJ가 생각을 나누거나 "
                "청취자와 대화를 나누는 자연스러운 톤이면 좋습니다."
            )
        else:
            system_content = (
                "You are an empathetic AI radio DJ who shares news stories with listeners. "
                "Instead of offering vague comfort, create DJ commentary that connects directly to the news topic. "
                "Your tone should be conversational, thoughtful, and engaging, as if talking naturally with the audience."
            )

        # Gemini SDK 방식의 시스템 프롬프트 및 콘텐츠 호출 설정
        response = client.models.generate_content(
            model=model if model != "gpt-4o" else "gemini-3.6-flash",  # 혹시 모델명이 gpt-4o로 넘어오면 제미나이로 대체
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_content,
                temperature=0.7,
            ),
        )

        script = response.text.strip()

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