from flask import Flask, request, abort
# from api.ToDotask import ToDotask, ToDotaskEncoder
from api import AccessFile
from api import Function

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


line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
webhook_handler = WebhookHandler(os.environ.get('CHANNEL_SECRET'))

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
    DEL_TODO = 2

# 用戶的待辦事項
user_todo_list = {}

# 追蹤使用者的狀態
user_state = {}


# 處理在主選單下的訊息 (user_state=NORMAL)
def handle_normal_state(user_id, user_message, event):
    global user_state
    reply_message="初始預設2"

    if user_message == '新增 待辦事項':
        user_state[user_id] = UserState.ADD_TODO
        reply_message = f'請輸入待辦事項內容。\n(輸入「結束」或「1」結束新增狀態)'

    elif user_message == '顯示 待辦清單':
        message = Function.createTodoListMessage(user_id,user_todo_list)
        line_bot_api.reply_message(event.reply_token, message)
        reply_message = None
    
    elif user_message == '完成 待辦事項':   # 刪除功能建立於 06-03 12:03 ver1
        user_state[user_id] = UserState.DEL_TODO
        reply_message = f'請輸入要完成的待辦事項編號'
        i = 1
        for todo in user_todo_list[user_id]:
            reply_message += f"\n{i}. {todo['text']}"
            i+= 1

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

    if user_message == '取消' or user_message == '0':
        user_state[user_id] = UserState.NORMAL
        reply_message = '取消已成功\n已重新回到主選單' # 強制取消當下的狀態，回到主選單

    # 檢查使用者的狀態 (處於哪個功能狀態下)
    state = user_state[user_id]
    # 新增功能
    if state == UserState.ADD_TODO:
            reply_message,user_todo_list = Function.handle_add_todo_state(user_id, user_message,user_todo_list)
            user_state[user_id] = UserState.NORMAL
            # if reply_message == '已結束新增功能':
            #     user_state[user_id] = UserState.NORMAL

    # (New) 刪除功能
    elif state == UserState.DEL_TODO:
            reply_message,user_todo_list = Function.handle_del_todo_state(user_id, user_message,user_todo_list)
            user_state[user_id] = UserState.NORMAL

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