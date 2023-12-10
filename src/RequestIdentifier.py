import random, string

def request_identifier():
    n = 10
    rqi = ""
    for i in range(n):
        rqi += str(random.choice(string.ascii_letters + string.digits))
    return rqi