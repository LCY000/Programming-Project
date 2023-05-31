from flask import Flask, request, abort
from api.ToDotask import ToDotask, ToDotaskEncoder
import json
from typing import List
from enum import Enum

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
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

# 將待辦事項加入列表
def addTodoList(user_id,task):

    if user_id not in user_todo_list:
        user_todo_list[user_id] = []

    user_todo_list[user_id].append(task) 

# 取得待辦事項清單
def getTodoList(user_id):
    return user_todo_list[user_id]

# 寫檔進.json檔
def save_to_json(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, cls = ToDotaskEncoder)

# 讀取 .json檔
def load_from_json(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

# 處理正常狀態下的訊息
def handle_normal_state(user_id, user_message, event):
    global user_state

    if user_message == '新增/完成 待辦事項':
        user_state[user_id] = UserState.ADD_TODO
        reply_message = f'請輸入待辦事項內容。\nin normal_state state = {user_state[user_id].value}'
    elif user_message == '顯示待辦清單':

        if user_id not in user_todo_list:
            reply_message = "無待辦事項。"
        else:
            user_todo_list[user_id] = load_from_json(f'user_data/{user_id}.json') # 從.json檔讀取資料
            message = createTodoListMessage(user_id,user_todo_list[user_id])
            line_bot_api.reply_message(event.reply_token, message)
    else:
        reply_message = f'請輸入正確的指令。in normal_state state= {user_state[user_id].value}'

    return reply_message


# 新增待辦事項狀態下的訊息
def handle_add_todo_state(user_id, user_message):
    reply_message = '' # 提供預設值

    # 創建一個新的待辦事項
    new_task = ToDotask(user_message)
    addTodoList(user_id,new_task)
    user_state[user_id] = UserState.NORMAL
    reply_message = '已新增待辦事項：\n{}'.format(user_message)
    
    
    save_to_json(user_todo_list, f'user_data/{user_id}.json')  # 將資料寫入檔案    

    return reply_message


def createTodoListMessage(user_id,user_todo_list):
    i = 1
    # 建立待辦事項清單的條列項目
    todoList = user_todo_list
    list_items = []
    for todo in todoList:
        item = {"type" : "text", "text" : str(str(i) + '. ' + todo['text'])} 
        list_items.append(item)
        i += 1

    # 建立Flex Message物件，用於顯示待辦事項清單
    flex_message = FlexSendMessage(
        alt_text = "待辦事項清單",
        contents = {
            "type" : "bubble",
            "body" : {
                "type" : "box",
                "layout" : "vertical",
                "contents" : [
                    {"type" : "text", "text" : "待辦事項清單", "weight" : "bold", "size" : "lg"},
                    *list_items # 將條列項目展開添加到 "contents" 中
                ]
            }
        }
    )
    return flex_message

# 處理接收到的訊息事件
@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global user_todo_list, user_state

    user_id = event.source.user_id
    user_message = event.message.text

    if user_id not in user_todo_list:
        # 如果是新的使用者，創建一個新的待辦事項清單
        user_todo_list[user_id] = []

    # 單純在偵錯
    if user_message=='印':
        if len(user_todo_list[user_id]) >= 1:
            test = user_todo_list[user_id][0].get_text()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=test))
        else:
            message = "使用者待辦事項清單：\n"
            for user_id, todo_list in user_todo_list.items():
                message += f"\n使用者ID: {user_id}\n"
                for todo in todo_list:
                    message += f"- {todo.get_text()}\n"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


    # 檢查使用者的狀態
    if user_id in user_state:
        state = user_state[user_id]
        if state == UserState.ADD_TODO:
              reply_message = handle_add_todo_state(user_id, user_message)
        else:
            reply_message = handle_normal_state(user_id, user_message, event)

    else:
        user_state[user_id] = UserState.NORMAL
        reply_message = handle_normal_state(user_id, user_message, event)
        

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))


if __name__ == "__main__":
    app.run()