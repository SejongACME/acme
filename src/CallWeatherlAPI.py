import requests

# API 호출 함수
def call_weather_api(api_url):
    try:
        # GET 요청
        response = requests.get(api_url)

        # HTTP 상태 코드 확인
        if response.status_code == 200:
            # API 응답을 JSON 형식으로 파싱
            data = response.json()
            return data
        else:
            # 에러 출력
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None