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

line_bot_api = LineBotApi('LlcraQZMrH5dj81FA7Cr61wjDwdIAGvxrAohTctu0ukg69/WZVtMyJXVAgMylX7L7HbY1R22i9CqSqqOQ00iRUaqSs2A1Nblbu4iz4fub3xRhKw8JEj7D0mIBCYT9aN8eV1M2BXD1fJxl8s8ny915wdB04t89/1O/w1cDnyilFU=')
webhook_handler = WebhookHandler('aa515afa1bf748a3805ee3c599a71c95')

@app.route("/")
def home():
    return "LINE BOT API Server is running."

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