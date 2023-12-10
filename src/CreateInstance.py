from RequestIdentifier import request_identifier

def make_contentinstance(MSRRGN_CD, MSRSTE_NM, measurement, time):
    url = f"http://127.0.0.1:65535/cse-in/{MSRRGN_CD}/{MSRSTE_NM}"
    rqi = request_identifier()
    header = {
        "Content-Type" : "application/json; ty=4",
        "X-M2M-Origin" : "CAdmin",
        "X-M2M-RI" : rqi,
        "X-M2M-RVI" : "3"
    }
    body = {
        "m2m:cin": {
            "cnf": "text/plain:0",
            "con": str(measurement), # str로만 저장가능함. 나중에 정수형혹은 실수형으로 저장할 수 있게끔 필요시 변경
            "rn": time
        }
    }
    return header, body, url