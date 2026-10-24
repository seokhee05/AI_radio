from music.blocks.block_music_trend import block_music_trend
from music.blocks.block_music_story import block_music_story
from music.blocks.block_music_artist import block_music_artist


def run_music_radio(
    blocks: list[str],
    keyword: str = None,
    language="ko",
    prev_type=None,
    context=None
) -> str:

    output_lines = []

    # main.py에서 전달받은 이전 코너 정보 유지
    prev_type = prev_type
    context = context or ""

    for b in blocks:

        if b == "music_trend":
            text = block_music_trend(
                keyword, prev_type, context, language
            )

        elif b == "music_story" or b == "music_genre":
            text = block_music_story(
                keyword, prev_type, context, language
            )

        elif b == "music_artist":
            text = block_music_artist(
                keyword, prev_type, context, language
            )

        else:
            raise ValueError(f"지원하지 않는 음악 블록: {b}")

        output_lines.append(text)

        # 다음 블록에 전달할 정보 업데이트
        prev_type = b
        context = text[-400:]

    return "\n\n".join(output_lines)