import requests
from flask import Flask, request

app = Flask(__name__)

'''
使用者訂閱網址：
https://notify-bot.line.me/oauth/authorize?response_type=code&client_id=bvtTFwMkqG5LiWFJIq3aXb&redirect_uri=https://b2a2e5fe3748.ngrok.io&scope=notify&state=NO_STATE
'''


def getNotifyToken(AuthorizeCode):
    body = {
        "grant_type": "authorization_code",
        "code": AuthorizeCode,
        "redirect_uri": 'https://b2a2e5fe3748.ngrok.io',
        "client_id": 'KO3a5Ieeg301SDlAa4reD7',
        "client_secret": 'OUpn0VvMjIBdFfdyB4NysPq09PkYIL0vgtWRgvhGQuU'
    }
    r = requests.post("https://notify-bot.line.me/oauth/token", data=body)
    return r.json()["access_token"]


def lineNotifyMessage(token, msg):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {'message': msg}
    r = requests.post("https://notify-api.line.me/api/notify",
                      headers=headers, data=payload)
    return r.status_code


"""
小明的token:MXYXpYMZVvQlGa1qBAK6hjc6IG541I3LRUlW4vaUDau
"""


@app.route('/', methods=['POST', 'GET'])
def hello_world():
    authorizeCode = request.args.get('code')
    token = getNotifyToken(authorizeCode)
    print(token)
    lineNotifyMessage(token, "恭喜你連動完成")
    return f"恭喜你，連動完成"


if __name__ == '__main__':
    lineNotifyMessage("MXYXpYMZVvQlGa1qBAK6hjc6IG541I3LRUlW4vaUDau", "哈哈哈")
    app.run()
