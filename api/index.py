from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)



app = Flask(__name__)

line_bot_api = LineBotApi('923fb6c9f046e9cfeb9297f2677817ec')
webhook_handler = WebhookHandler('S8n783a5xRnNniTUHE2dmSnDLoDljG+QGJAOphIrQoT8Hz5FtKR3/EChRlVhPfoGhZ7+YPas5wPZOLAqaahnW6EK0teMsjJ0+q5wKWiWDMg1t/HDkNi/f0+/RzjI2tqjvVb58AaxIp5t7QTQB7dvjwdB04t89/1O/w1cDnyilFU=')

@app.route("/")
def home():
    return ""

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        webhook_handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.run()