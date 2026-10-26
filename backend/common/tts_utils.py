import os
import uuid
import requests
from fastapi import HTTPException
from common.config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET

# 음성 파일 저장 폴더명 정의
AUDIO_DIR = "audio_files"

def split_text_by_limit(text: str, max_chars: int = 1500) -> list[str]:
    """2,000자 제한을 초과하지 않도록 문단/줄바꿈 기준으로 분할"""
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 1 <= max_chars:
            current_chunk += paragraph + "\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def generate_tts_url(text: str, speaker: str = "vdaeseong", speed: str = "0") -> str:
    """
    텍스트를 CLOVA Voice API로 변환하여 MP3 파일로 저장하고,
    프론트엔드에서 접근 가능한 정적 URL 경로(/static/filename.mp3)를 반환합니다.
    """
    if not text or not text.strip():
        return ""

    # audio_files 폴더가 없으면 자동 생성
    os.makedirs(AUDIO_DIR, exist_ok=True)

    chunks = split_text_by_limit(text, max_chars=1500)
    combined_audio = bytearray()

    url = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    for chunk in chunks:
        if not chunk.strip():
            continue

        data = {
            "speaker": speaker,
            "volume": "0",
            "speed": speed,
            "pitch": "0",
            "format": "mp3",
            "text": chunk,
        }

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            combined_audio.extend(response.content)
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"CLOVA TTS Error: {response.text}",
            )

    # 유니크한 파일명 생성 (예: tts_a1b2c3d4e5.mp3)
    filename = f"tts_{uuid.uuid4().hex[:10]}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    # MP3 파일로 저장
    with open(filepath, "wb") as f:
        f.write(combined_audio)

    # FastAPI 정적 파일 경로 반환
    return f"/static/{filename}"