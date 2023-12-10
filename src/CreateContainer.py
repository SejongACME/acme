import requests
from RequestIdentifier import request_identifier

def make_container(resourceName: str, guList):
    rqi = request_identifier()
    header = {
        "Content-Type" : "application/json; ty=3",
        "X-M2M-Origin" : "CAdmin",
        "X-M2M-RI" : rqi,
        "X-M2M-RVI" : "3"
    }
    url = "http://127.0.0.1:65535/id-in"
    body = {
        "m2m:cnt": {
            "mbs": 10000, # maxByteSize
            "mni": 25, # maxNrOfInstances (컨테이너 안에 넣을 수 있는 최대 데이터 개수인듯)
            "rn": resourceName
        }
    }
    requests.post(url, headers=header, json=body)


    # 컨테이너 안에 컨테이너 생성
    for gu in guList :
        rqi = request_identifier()
        url = f"http://127.0.0.1:65535/cse-in/{resourceName}"
        body = {
        "m2m:cnt": {
            "mbs": 10000, # maxByteSize
            "mni": 10, # maxNrOfInstances (컨테이너 안에 넣을 수 있는 최대 데이터 개수인듯)
            "rn": gu
            }
        }
        requests.post(url, headers=header, json=body)