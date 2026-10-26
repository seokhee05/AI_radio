import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

# 💡 TTS 음성 생성 함수 임포트 (필요 시 파일 단독 테스트용)
from common.tts_utils import generate_tts_url

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def fetch_its_highway_data() -> str:
    """부산권 고속도로 및 시내 주요 간선도로 데이터를 수집하고 파싱합니다."""
    api_key = os.getenv("ITS_API_KEY")

    busan_area_params = {
        "apiKey": api_key,
        "type": "all",
        "minX": "128.4",
        "maxX": "129.3",
        "minY": "35.0",
        "maxY": "35.5",
        "getType": "json",
    }

    traffic_url = "https://openapi.its.go.kr:9443/trafficInfo"

    try:
        res_traffic = requests.get(
            traffic_url, params=busan_area_params, timeout=5
        )
        res_traffic.raise_for_status()
        data = res_traffic.json()

        body = data.get("body", {})
        items = body.get("items", [])

        if not items:
            items = data.get("items", [])

        if not items:
            return "현재 수집된 실시간 도로 소통 정보가 없습니다."

        hw_congestion = []
        hw_smooth = []
        city_congestion = []
        city_smooth = []

        for item in items:
            road_name = item.get("roadName", "도로명 미상")
            speed_val = item.get("speed", 0)

            try:
                speed = float(speed_val)
            except (ValueError, TypeError):
                speed = 50.0

            valid_highways = [
                "경부고속도로", "남해고속도로", "중앙고속도로", "동해고속도로",
                "부산외곽순환고속도로", "함양울산고속도로", "중앙고속도로지선",
                "경부선", "남해선", "중앙선", "동해선"
            ]
            is_highway = any(hw in road_name for hw in valid_highways) or ("고속" in road_name and "대로" not in road_name)

            major_city_keywords = [
                "대로", "번영로", "충렬로", "동서고가", "가야대로",
                "중앙대로", "수영로", "해운대해변로", "광안대교", "거제대로",
                "낙동남로", "구덕로", "터널", "지하차도"
            ]
            is_major_city_road = any(keyword in road_name for keyword in major_city_keywords) and "길" not in road_name

            if not (is_highway or is_major_city_road):
                continue

            if is_highway:
                if speed < 40:
                    hw_congestion.append(f"- {road_name}: 약 {speed:.1f}km/h")
                else:
                    hw_smooth.append(f"- {road_name}: 약 {speed:.1f}km/h")
            elif is_major_city_road:
                if speed < 30:
                    city_congestion.append(f"- {road_name}: 약 {speed:.1f}km/h")
                else:
                    city_smooth.append(f"- {road_name}: 약 {speed:.1f}km/h")

        summary_lines = []

        summary_lines.append("=== [고속도로 교통 상황] ===")
        if hw_congestion:
            summary_lines.append("• 서행 및 정체:")
            summary_lines.extend(list(set(hw_congestion))[:4])
        if hw_smooth:
            summary_lines.append("• 소통 원활:")
            summary_lines.extend(list(set(hw_smooth))[:4])
        if not hw_congestion and not hw_smooth:
            summary_lines.append("특이 고속도로 데이터 없음")

        summary_lines.append("\n=== [부산 시내 주요 간선도로 상황] ===")
        if city_congestion:
            summary_lines.append("• 서행 및 정체:")
            summary_lines.extend(list(set(city_congestion))[:4])
        if city_smooth:
            summary_lines.append("• 소통 원활:")
            summary_lines.extend(list(set(city_smooth))[:4])
        if not city_congestion and not city_smooth:
            summary_lines.append("특이 시내도로 데이터 없음")

        return "\n".join(summary_lines)

    except Exception as e:
        print(f"❌ [traffic_radio] ITS 교통 API 연동 오류: {e}")
        return "현재 실시간 부산 지역 교통 정보를 불러올 수 없어 기본 안전 소식으로 대체합니다."


def run_traffic_radio(block_types, keyword=None, language="ko", prev_type=None, context=None) -> str:
    """
    메인 라디오 시스템에서 호출되는 교통 정보 블록 핸들러 함수입니다.
    ITS 공공데이터 수집 후 LLM으로 방송 대본을 생성하여 문자열(str)을 반환합니다.
    """
    print("🚗 [traffic_radio] 부산 실시간 교통 데이터 수집 시작...")
    highway_info = fetch_its_highway_data()

    context_summary = context[-200:] if context else "전체 방송 진행 중"

    prompt = f"""
    당신은 라디오 프로그램의 다정다감하고 센스 있는 메인 DJ입니다.
    이전 코너의 흐름(직전 유형: {prev_type}, 내용: {context_summary})을 이어받아 자연스럽게 진행해주세요.
    
    오늘 실시간으로 수집된 부산 지역의 교통 상황입니다.
    {highway_info}
    
    위 데이터를 바탕으로, 도로를 달리는 청취자들을 위한 **생생한 교통 정보 안내**와 함께, **운전에 도움이 되는 실용적인 교통 상식이나 안전 운전 꿀팁(방어 운전, 차량 관리, 도로 예절 등)**을 하나의 자연스러운 라디오 대본으로 작성해주세요.
    
    [작성 원칙]
    1. 딱딱한 정보 전달이 아닌, 청취자에게 전하는 따뜻하고 부드러운 구어체를 사용해주세요.
    2. 고속도로 상황을 먼저 다루고, 시내 도로 상황과 안전 운전 팁으로 매끄럽게 연결해주세요.
    3. 특정 시간대(심야, 새벽 등)에 국한되는 인사는 피해주세요.
    4. 분량이 너무 길지 않게 핵심 전달 위주로 깔끔하게 구성해주세요.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1500,
        )
        content = response.choices[0].message.content.strip()
        print("✅ [traffic_radio] 교통 정보 대본 생성 완료")

    except Exception as e:
        print(f"❌ [traffic_radio] 교통 대본 생성 오류: {e}")
        content = "부산 지역 실시간 교통 상황을 전해드립니다. 도로 위 안전 운행을 부탁드리며, 오늘도 편안한 운전 되시기 바랍니다."

    return content