import os
import sys

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
                result = a+b+c+d+e+f
                return result
    return 0

API_KEY = "sk-1234567890abcdef"
DB_URL = "postgresql://admin:password123@localhost/prod"
