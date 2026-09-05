from app.opening import generate_opening_ment # 오프닝
from app.closing import generate_closing_ment # 클로징


# 프로그램별 실행 함수
from backend.news.news_radio import run_news_radio
from story.story_radio import run_story_radio
from music.music_radio import run_music_radio

def main():
    # 🎙️ 오프닝 멘트
    #opening = generate_opening_ment()
    #print("🎙️ 오프닝 멘트\n" + opening + "\n")

    # 콘텐츠 선택
    print("\n🎧 오늘은 어떤 프로그램을 들려드릴까요?")
    print("1. 뉴스 브리핑")
    print("2. 사연 공감")
    print("3. 음악 이슈 탐방")
    choice = input("번호를 선택해주세요 (1~3): ")

    print("\n----------------------------------------\n")

    if choice == "1":
        run_news_radio()
    elif choice == "2":
        run_story_radio()
    elif choice == "3":
        run_music_radio()
    else:
        print("⚠️ 잘못된 입력입니다. 프로그램을 종료합니다.")
        return
    
    # closing = generate_closing_ment()
    # print("🎧 마무리 멘트\n" + closing + "\n")

if __name__ == "__main__":
    main()