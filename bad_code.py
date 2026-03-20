import requests

def process(d, db):
    if d is None:
        return None
    if "id" not in d:
        return None
    res = db.query("SELECT * FROM users WHERE id=" + str(d["id"]))
    if res:
        tmp = res[0]
        payload = {"uid": tmp["id"], "n": tmp["name"]}
        requests.post("https://api.example.com/notify", json=payload)
        return payload
    return None
# test
# retrigger
# retrigger2
# retrigger5
# retrigger6
# retrigger6
# retrigger7
# retrigger8
# retrigger9
# retrigger9
# retrigger10
