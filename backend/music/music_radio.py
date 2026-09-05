from music.blocks.block_music_history import block_music_history
from music.blocks.block_music_trend import block_music_trend
from music.blocks.block_music_genre import block_music_genre
from music.blocks.block_music_artist import block_music_artist

def run_music_radio(blocks: list[str], keyword: str = None, language="ko", prev_type=None, context=None) -> str:
    output_lines = []
    prev_type, context = None, ""

    for b in blocks:
        if b == "music_history":
            text = block_music_history(keyword, prev_type, context, language)
        elif b == "music_trend":
            text = block_music_trend(keyword, prev_type, context, language)
        elif b == "music_genre":
            text = block_music_genre(keyword, prev_type, context, language)
        elif b == "music_artist":
            text = block_music_artist(keyword, prev_type, context, language)

        output_lines.append(text)

        # 다음 블럭에 넘겨줄 context 업데이트
        prev_type = b
        context = text[-400:]  # 마지막 400자 정도만 잘라 전달

    return "\n\n".join(output_lines)
