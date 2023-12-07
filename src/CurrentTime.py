from datetime import datetime, timedelta

def generate_hourly_time(time, sign):
    datetime_format = "%Y%m%d%H%M"
    start_time = datetime.strptime(time, datetime_format)

    # 1시간 경과된 타임 반환
    time_interval = timedelta(hours=1)
    start_time += time_interval
    # sign = 0 일 때, 하루 전 타임 반환
    if sign == 0:
        time_interval = timedelta(days=1)
        start_time -= time_interval
    
    # 년도, 월, 일, 시간을 나타내는 문자열을 생성합니다.
    formatted_time = start_time.strftime("%Y%m%d%H%M")

    return formatted_time
