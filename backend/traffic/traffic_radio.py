import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def fetch_its_highway_data() -> str:
    """부산권 고속도로 및 시내 주요 간선도로 데이터를 수집하고, 고속도로를 우선하여 파싱합니다."""
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
            return "현재 수집된 도로 소통 데이터가 없습니다."

        hw_congestion = []
        hw_smooth = []
        city_congestion = []
        city_smooth = []

        for item in items:
            road_name = item.get("roadName", "도로명 미상")
            speed = item.get("speed", 0)

            try:
                speed = float(speed)
            except:
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
            summary_lines.append("특이 교통량 데이터 없음")

        summary_lines.append("\n=== [부산 시내 주요 간선도로 상황] ===")
        if city_congestion:
            summary_lines.append("• 서행 및 정체:")
            summary_lines.extend(list(set(city_congestion))[:4])
        if city_smooth:
            summary_lines.append("• 소통 원활:")
            summary_lines.extend(list(set(city_smooth))[:4])
        if not city_congestion and not city_smooth:
            summary_lines.append("특이 교통량 데이터 없음")

        return "\n".join(summary_lines)

    except Exception as e:
        print(f"통합 교통 API 연동 오류: {e}")
        return "현재 실시간 교통 정보를 불러올 수 없습니다."


def run_traffic_radio(block_types, keyword=None, language="ko", prev_type=None, context=None):
    """메인 라디오 시스템에서 호출되는 교통 정보 블록 핸들러 함수"""
    highway_info = fetch_its_highway_data()

    prompt = f"""
    당신은 라디오 프로그램의 다정다감하고 센스 있는 메인 DJ입니다.
    이전 코너의 흐름(직전 유형: {prev_type}, 내용 참고: {context[-200:] if context else '옵션'})을 이어받아 자연스럽게 진행해주세요.
    
    오늘 실시간으로 수집된 부산 지역의 교통 상황입니다. (고속도로 소식이 먼저 안내되도록 구성되어 있습니다.)
    
    {highway_info}
    
    위 데이터를 바탕으로, 도로를 달리는 청취자들을 위한 **생생한 교통 정보 안내**와 함께, **운전에 도움이 되는 흥미롭고 유용한 교통 상식이나 안전 운전 꿀팁(시간대나 상황에 얽매이지 않고, 방어 운전 노하우, 차량 관리 팁, 도로 위 매너, 계절별 상식 등 매번 참신하고 실용적인 주제를 자유롭게 선정해주세요)**을 하나의 라디오 대본 형식으로 자연스럽게 작성해주세요.
    
    [작성 원칙]
    1. 딱딱한 뉴스 톤이 아니라, 라디오 DJ가 따뜻하게 읽어주듯 친근하고 부드러운 어조를 사용해주세요.
    2. **대본 시작할 때 "심야의 고요함 속에서 함께하는 DJ [당신의 이름]입니다." 라는 문구는 절대 사용하지 마세요.**
    3. 고속도로 소식을 먼저 비중 있게 다뤄주시고, 시내 간선도로 소식을 이은 뒤, 자연스럽게 '오늘의 운전 꿀팁/상식 코너'로 이어지도록 구성해주세요.
    4. 야간 운전에만 국한하지 말고, **다양하고 신선한 운전 상식 및 도로 위 팁**을 매번 새롭게 고민해서 담아주세요.
    5. 전체 분량이 너무 지루하지 않게 핵심 위주로 깔끔하게 구성해주세요.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1800,
        )
        content = response.choices[0].message.content.strip()

    except Exception as e:
        print(f"교통 방송 대본 생성 중 오류 발생: {e}")
        content = "오늘의 실시간 교통 정보 및 안전 소식을 전해드렸습니다..."

    return content