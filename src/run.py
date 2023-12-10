import requests
import time
from datetime import timedelta
from CallWeatherlAPI import call_weather_api
from CreateContainer import make_container
from CurrentTime import generate_hourly_time
from CreateInstance import make_contentinstance

# API KEY
API_KEY = "4a59596f57746b6d373464514e7952"
START_TIME = "201306010000"


# 컨테이너 생성
# 컨테이너 이름: NO2, O3, CO, SO2, PM10, PM25 
#            L 강남구, 광진구, 성동구, 송파구, 중구
surveyList = ["NO2", "O3", "CO", "SO2", "PM10", "PM25", "prevPM"]
guList = ["강남구", "광진구", "성동구", "송파구", "중구"]
for survey in surveyList:
    make_container(survey, guList)
    
while True:
    # 시간 설정
    NOW_TIME = generate_hourly_time(START_TIME, 1)
    PREV_TIME = generate_hourly_time(START_TIME, 0)
    
    # 호출하려는 API의 URL을 설정합니다.
    # 방법: 날짜형식(MSRDT)을 201306010100(년도, 월, 일, 시간)을 한시간 단위로 수정해서 api_url의 뒷부분을 수정함
    api_url = f"http://openAPI.seoul.go.kr:8088/{API_KEY}/json/TimeAverageAirQuality/1/25/{NOW_TIME}"
    api_url_prev = f"http://openAPI.seoul.go.kr:8088/{API_KEY}/json/TimeAverageAirQuality/1/25/{PREV_TIME}"
    
    # API 로부터 데이터 받아오기
    data = call_weather_api(api_url)
    data_prev = call_weather_api(api_url_prev)

    # 인스턴스 생성
    # 반복문으로 컨테이너에 데이터 넣기
    # 하루 전 미세먼지
    for element in data_prev["TimeAverageAirQuality"]["row"]:
        if element["MSRSTE_NM"] not in guList:
                continue
        h, b, u = make_contentinstance("prevPM", element["MSRSTE_NM"], element["PM10"], PREV_TIME)
        requests.post(url=u, headers=h, json=b)

    # 나머지 값들
    surveyList = ["NO2", "O3", "CO", "SO2", "PM10", "PM25"]
    for li in surveyList:
        for element in data["TimeAverageAirQuality"]["row"]:
            if element["MSRSTE_NM"] not in guList:
                continue
            h, b, u = make_contentinstance(li, element["MSRSTE_NM"], element[li], NOW_TIME)
            requests.post(url=u, headers=h, json=b)

    START_TIME = NOW_TIME  
    