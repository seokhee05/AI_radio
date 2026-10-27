import os
import requests
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def search_youtube_music(artist, title):
    if not YOUTUBE_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY가 없습니다.")

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": f"{artist} {title} official audio",
        "type": "video",
        "videoEmbeddable": "true",
        "maxResults": 5,
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    response.raise_for_status()
    data = response.json()

    videos = data.get("items", [])

    return [
        {
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
            "url": (
                "https://www.youtube.com/watch?v="
                + item["id"]["videoId"]
            ),
        }
        for item in videos
        if item.get("id", {}).get("videoId")
    ]