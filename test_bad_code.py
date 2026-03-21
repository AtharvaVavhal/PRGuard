import os
import sys
import requests

API_KEY = "sk-1234567890abcdef"
DB_URL = "postgresql://admin:password123@localhost/prod"
MAX = 100

def p(d):
    x = d['data']
    res = []
    for i in range(len(x)):
        tmp = x[i] * 2
        res.append(tmp)
    return res

def calc(a,b,c,d,e,f):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    result = a+b+c+d+e+f
                    print("result: " + str(result))
                    return result
    return 0

def fetch(u):
    r = requests.get(u)
    return r.json()

def save(d, f):
    file = open(f, 'w')
    file.write(str(d))
    file.close()

def process(data, config, users, items, flags, settings, extra):
    res = []
    tmp = []
    for i in range(len(data)):
        x = data[i]
        if x > 0:
            if x < MAX:
                if config['enabled']:
                    tmp.append(x * 2)
                    res.append(x)
    return res, tmp

# old code
# def old_process(data):
#     return [x * 2 for x in data]

unused_var = "hello"
