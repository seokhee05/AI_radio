from typing import List
import json
from tqdm import tqdm

# 광고 필터링 키워드
AD_KEYWORDS = ["구매", "할인", "이벤트", "홍보", "광고", "www", "http", "카카오톡"]

# 스코어링 기준 키워드
FIRST_PERSON_KEYWORDS = ["저는", "제", "제가", "저도", "저희", "우리"]
TIME_KEYWORDS = ["오늘", "어제", "작년", "며칠 전", "몇 년 전", "방금", "요즘"]
EMOTION_KEYWORDS = ["힘들", "기쁘", "슬프", "행복", "짜증", "뿌듯", "지치"]
QUESTION_KEYWORDS = ["어떡하죠", "어떻게", "왜 그랬을까요", "괜찮을까요", "도와주세요", "알려주세요", "해주세요"]

# 점수 기준
SCORE_THRESH = 2
MIN_LENGTH = 40

RAW_PATH = "story/raw_messages.json"
CANDIDATE_PATH = "story/candidate_stories.json"

def contains_ad(text: str) -> bool:
    return any(word in text.lower() for word in AD_KEYWORDS)


def score_message(text: str) -> int:
    score = 0
    if any(word in text for word in FIRST_PERSON_KEYWORDS):
        score += 1
    if any(word in text for word in TIME_KEYWORDS):
        score += 1
    if any(word in text for word in EMOTION_KEYWORDS):
        score += 1
    if any(word in text for word in QUESTION_KEYWORDS):
        score += 1
    if len(text.strip()) >= MIN_LENGTH:
        score += 1
    return score


def filter_story_candidates(messages: List[str]) -> List[str]:
    candidates = []
    for msg in tqdm(messages, desc="1차 규칙기반 filtering"):
        try:
            if contains_ad(msg):
                continue
            if score_message(msg) >= SCORE_THRESH:
                candidates.append(msg.strip())
        except Exception as e:
            print(f"처리 중 오류 발생: {e}")
            continue
    return candidates


def story_filter():
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        messages = json.load(f)["messages"]

    candidates = filter_story_candidates(messages)
    print("1차 필터링 완료")

    with open(CANDIDATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"candidates": [{"id": i+1, "content": msg} for i, msg in enumerate(candidates)]}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    story_filter()
    print("1차 필터링 완료")