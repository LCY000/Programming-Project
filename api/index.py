from flask import Flask, request, abort
# from api.ToDotask import ToDotask, ToDotaskEncoder
from api import AccessFile
from api import Function

import json
from typing import List
from enum import Enum
import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, RichMenu
)

app = Flask(__name__)

line_bot_api = LineBotApi('LlcraQZMrH5dj81FA7Cr61wjDwdIAGvxrAohTctu0ukg69/WZVtMyJXVAgMylX7L7HbY1R22i9CqSqqOQ00iRUaqSs2A1Nblbu4iz4fub3xRhKw8JEj7D0mIBCYT9aN8eV1M2BXD1fJxl8s8ny915wdB04t89/1O/w1cDnyilFU=')
webhook_handler = WebhookHandler('8f948b2d6deda1511f4570128cd231a0')

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

#----------------------------------------- 分隔線 -----------------------------------------#


# 使用者狀態的列舉類型
class UserState(Enum):
    NORMAL = 0
    ADD_TODO = 1

# 用戶的待辦事項
user_todo_list = {}

# 追蹤使用者的狀態
user_state = {}

rich_menu_id = line_bot_api.create_rich_menu()

# 處理在主選單下的訊息 (user_state=NORMAL)
def handle_normal_state(user_id, user_message, event):
    global user_state
    reply_message="初始預設2"

    if user_message == '新增 待辦事項':
        user_state[user_id] = UserState.ADD_TODO
        reply_message = f'請輸入待辦事項內容。'
        # 關閉圖文選單
        line_bot_api.unlink_rich_menu_from_user(user_id,line_bot_api.get_rich_menu_list())
        # 還需製作一個取消新增訊息的功能......

    elif user_message == '顯示 待辦清單':
        message = Function.createTodoListMessage(user_id,user_todo_list)
        line_bot_api.reply_message(event.reply_token, message)
        reply_message = None

    # 等待新增功能中......

    else:
        reply_message = f'無此指令\n請輸入正確的指令。'

    return reply_message



# 接收訊息 
@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global user_todo_list, user_state
    reply_message="初始預設1"

    user_id = event.source.user_id
    user_message = event.message.text

    if user_id not in user_todo_list:
        user_data = AccessFile.read_user_data(user_id)
        if user_data is not None:
            user_todo_list[user_id] = user_data     #讀取的資料寫入字典
        else:
            # 如果是新的使用者，創建一個新的待辦事項清單
            user_todo_list[user_id] = []
        user_state[user_id] = UserState.NORMAL


    # 檢查使用者的狀態 (處於哪個功能狀態下)
    state = user_state[user_id]
    if state == UserState.ADD_TODO:
            reply_message,user_todo_list = Function.handle_add_todo_state(user_id, user_message,user_todo_list)
            user_state[user_id] = UserState.NORMAL
            # 開啟圖文選單
            line_bot_api.link_rich_menu_to_user(user_id,line_bot_api.get_rich_menu_list())
    
    # 等待新增功能中......

    else:
        reply_message = handle_normal_state(user_id, user_message, event)
        # 要是已輸出待辦清單，則直接結束
        if reply_message is None:
            return


    # 輸出回覆訊息 (預防突發意外，保險偵錯)
    if reply_message:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
    else:
        # 處理空訊息的情況
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="空訊息"))




if __name__ == "__main__":
    app.run()