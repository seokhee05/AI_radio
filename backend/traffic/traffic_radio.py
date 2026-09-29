import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def fetch_its_highway_data() -> str:
    """
    1단계: 전국 고속도로 및 돌발 상황 데이터 수집 (ITS API 단독)
    """
    # TODO: ITS 공식 문서에 기재된 실제 API URL(엔드포인트)로 변경하세요.
    url = "http://openapi.its.go.kr/" 
    params = {
        "apiKey": os.environ.get("ITS_API_KEY"),
        # 필요한 파라미터 추가 (예: type, minX, maxX 등)
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status() # HTTP 에러 발생 시 예외 처리
        data = response.json()
        
        # 💡 데이터가 잘 들어오는지 확인하기 위한 출력 (테스트 후 삭제 또는 주석 처리)
        print("=== ITS API 응답 데이터 ===")
        print(data)
        
        # TODO: data에서 돌발 상황(사고/고장)이나 주요 정체 구간을 파싱하는 로직 추가
        highway_summary = "고속도로 실시간 파싱 데이터 임시 텍스트..." 
        return highway_summary

    except Exception as e:
        print(f"ITS API 연동 오류: {e}")
        return "현재 실시간 교통 정보를 불러올 수 없습니다."


def block_traffic(context=None, language="ko") -> dict:
    """
    2단계: 수집된 ITS 데이터를 바탕으로 GPT를 통한 라디오 대본 생성
    """
    # 현재는 ITS 데이터만 수집
    highway_info = fetch_its_highway_data()
    
    prompt = f"""
    당신은 심야 라디오 프로그램의 다정다감하고 센스 있는 메인 DJ입니다.
    오늘 실시간으로 수집된 교통 및 도로 상황은 다음과 같습니다.
    
    - [고속도로 및 주요 도로 상황]: {highway_info}
    
    위 데이터를 바탕으로, 늦은 밤 귀가하는 청취자들을 위한 **교통 정보 안내와 유용한 운전 상식(또는 안전 당부 멘트)**을 라디오 대본 형식으로 자연스럽게 작성해주세요.
    
    [작성 원칙]
    1. 딱딱한 뉴스 톤이 아니라, 심야 라디오 DJ가 따뜻하게 읽어주듯 친근하고 부드러운 어조를 사용해주세요.
    2. 실시간 교통 상황(특히 정체 구간이나 사고/돌발 상황)을 알기 쉽게 정리하고, 늦은 시간 운전하는 이들에게 건네는 안전 운전 상식이나 위로의 말을 곁들여주세요.
    3. 만약 돌발 상황 데이터가 없다면, 평온한 안부와 함께 일반적인 도로 정보만 가볍게 전달해주세요.
    4. 전체 분량이 너무 길지 않게 핵심 위주로 깔끔하게 구성해주세요.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500,
        )
        content = response.choices[0].message.content.strip()

    except Exception as e:
        print(f"교통 방송 대본 생성 중 오류 발생: {e}")
        content = "오늘의 실시간 교통 정보 및 안전 소식을 전해드렸습니다..."

    return {
        "type": "TRAFFIC",
        "content": content
    }


# 단독 실행 테스트용 블록
if __name__ == "__main__":
    # .env 파일 로드가 필요하다면 상단에 dotenv-python 등을 세팅하세요.
    result = block_traffic()
    print("\n=== 최종 생성된 라디오 대본 ===")
    print(result["content"])