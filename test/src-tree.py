

""" make source tree ->  http://~/cse-in/Gwangjin-Gu/pm """

import requests
import random
import string

def request_identifier():
    n = 10
    rqi = ""
    for i in range(n):
        rqi += str(random.choice(string.ascii_letters + string.digits))
    return rqi

def make_container():
    url = "http://127.0.0.1:65535/id-in"
    rqi = request_identifier()
    header = {
        "Content-Type" : "application/json; ty=3",
        "X-M2M-Origin" : "CAdmin",
        "X-M2M-RI" : rqi,
        "X-M2M-RVI" : "3"
    }
    body = {
        "m2m:cnt": {
            "mbs": 10000,
            "mni": 10,
            "rn": "Gwangjin-Gu"
        }
    }
    return header, body, url
    
def make_contentinstance():
    url = "http://127.0.0.1:65535/cse-in/Gwangjin-Gu"
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
            "con": "10",
            "rn": "pm"
        }
    }
    return header, body, url

header_cnt, body_cnt, url_cnt = make_container()
header_cin, body_cin, url_cin = make_contentinstance()

http_post_request_cnt = requests.post(url_cnt, headers=header_cnt, json=body_cnt)
http_post_request_cin = requests.post(url_cin, headers=header_cin, json=body_cin)

    