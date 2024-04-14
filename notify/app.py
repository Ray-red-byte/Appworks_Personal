import requests
from flask import Flask, request
import os
from dotenv import load_dotenv


dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)

app = Flask(__name__)

LINE_SUBSCRIBE_URL = os.getenv("LINE_SUBSCRIBE_URL")
LINE_CLIENT_ID = os.getenv("LINE_CLIENT_ID")
LINE_CLIENT_SECRET = os.getenv("LINE_CLIENT_SECRET")


def getNotifyToken(AuthorizeCode):
    body = {
        "grant_type": "authorization_code",
        "code": AuthorizeCode,
        "redirect_uri": 'https://b2a2e5fe3748.ngrok.io',
        "client_id": LINE_CLIENT_ID,
        "client_secret": LINE_CLIENT_SECRET
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


@app.route('/', methods=['POST', 'GET'])
def hello_world():
    authorizeCode = request.args.get('code')
    token = getNotifyToken(authorizeCode)
    lineNotifyMessage(token, "恭喜你連動完成")
    return f"恭喜你，連動完成"


if __name__ == '__main__':
    app.run()
