from flask import Flask, request, abort
from api import ToDo_task
import datetime

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

# 待辦事項列表
todoList = []

# 將待辦事項加入列表
def addTodoList(task):
    todoList.append(task)

# 取得待辦事項清單
def getTodoList():
    return todoList

# 處理接收到的訊息事件
@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text

    if user_message == '加新的待辦事項':
        # 創建一個新的待辦事項
        new_task = ToDo_task("新的待辦事項內容")
        
        # 將待辦事項加入列表
        addTodoList(new_task)

        # 取得待辦事項清單
        todoList = getTodoList()

        # 建立訊息窗格，條列顯示待辦事項清單
        message = createTodoListMessage(todoList)

        # 回覆訊息給使用者
        line_bot_api.reply_message(event.reply_token, message)

def createTodoListMessage(todoList):
    # 建立待辦事項清單的條列項目
    list_items = []
    for todo in todoList:
        item = {"type" : "text", "text" : todo.get_text()}
        list_items.append(item)

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
                    # 根據待辦事項清單建立條列項目
                    # 可以使用迴圈遍歷待辦事項清單，建立對應的條列項目
                    *list_items # 將條列項目展開添加到 "contents" 中
                ]
            }
        }
    )

    return flex_message

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

if __name__ == "__main__":
    app.run()