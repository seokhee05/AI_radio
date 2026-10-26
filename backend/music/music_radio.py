from music.blocks.block_music_trend import block_music_trend
from music.blocks.block_music_story import block_music_story
from music.blocks.block_music_artist import block_music_artist


def run_music_radio(
    blocks: list[str],
    keyword: str = None,
    language: str = "ko",
    prev_type: str = None,
    context: str = None
) -> str:
    """
    음악 코너 블록 핸들러 함수입니다.
    선택된 음악 세부 블록(트렌드, 사연/장르, 아티스트) 대본을 생성하여 문자열(str)로 반환합니다.
    """
    print(f"🎵 [music_radio] 음악 코너 대본 생성 시작 (블록: {blocks}, 키워드: {keyword})")
    
    output_lines = []
    current_prev_type = prev_type
    current_context = context or ""

    for b in blocks:
        try:
            if b == "music_trend":
                text = block_music_trend(
                    keyword, current_prev_type, current_context, language
                )

            elif b in ["music_story", "music_genre"]:
                text = block_music_story(
                    keyword, current_prev_type, current_context, language
                )

            elif b == "music_artist":
                text = block_music_artist(
                    keyword, current_prev_type, current_context, language
                )

            else:
                print(f"⚠️ [music_radio] 지원하지 않는 음악 블록: {b}")
                continue

            # 대본 텍스트 유효성 확인
            if text and str(text).strip():
                clean_text = str(text).strip()
                output_lines.append(clean_text)

                # 다음 연쇄 블록용 컨텍스트 업데이트
                current_prev_type = b
                current_context = clean_text[-400:]
            else:
                print(f"⚠️ [music_radio] {b} 블록 결과가 비어있습니다.")

        except Exception as e:
            print(f"❌ [music_radio] {b} 블록 실행 오류: {e}")

    final_script = "\n\n".join(output_lines)
    print("✅ [music_radio] 음악 코너 대본 생성 완료")
    
    return final_script