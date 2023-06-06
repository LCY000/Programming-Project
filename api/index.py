from flask import Flask, request, abort
# from api.ToDotask import ToDotask, ToDotaskEncoder
from api import AccessFile
from api import Function

from enum import Enum
# from datetime import datetime,timezone,timedelta
import datetime
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

@app.route("/requests_PM")
def check_per_minute():
    try:
        print("Running check_per_minute()")  # 除錯訊息
        check_reminders()
        return '提醒檢查完成'
    except Exception as e:
        print("Error in check_per_minute():", str(e))  # 除錯訊息
        return '檢查失敗'

#----------------------------------------- 分隔線 -----------------------------------------#
 

# 使用者狀態的列舉類型
class UserState(Enum):
    NORMAL = 0
    ADD_TODO = 1
    DEL_TODO = 2
    SETTING = 3
    SETTING_REMIND_TIME = 4
    SETTING_TODO_REMIND_TIME = 5

# 用戶的待辦事項
user_todo_list = {}

# 追蹤使用者的狀態
user_state = {}
fixed_reminder_times = {}
user_reminder_times = {}

# 判斷當前時間是否為提醒時間
def check_reminder_time(reminder_time):
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    taiwan_now_time = now.astimezone(datetime.timezone(datetime.timedelta(hours=8))) # 轉換時區 -> 東八區

    if taiwan_now_time.time().hour == reminder_time.hour and taiwan_now_time.time().minute == reminder_time.minute:
        return True
    else:
        return False

def check_fixed_reminder(user_id, reminder_time):
    # 檢查提醒時間並發送消息
    if check_reminder_time(reminder_time):
        message = '提醒：您有待辦事項需要處理！'
        line_bot_api.push_message(user_id, TextSendMessage(text=message))

def check_reminders():
    for user_id in user_todo_list:
        if user_id in fixed_reminder_times:
            check_fixed_reminder(user_id, fixed_reminder_times[user_id])

# def check_reminder(user_id, remind_time):
#     for todo in user_todo_list[user_id]:
#         if todo.remind_time == remind_time and todo.reminded == False and (user_state[user_id] == UserState.NORMAL or user_state[user_id] == UserState.SETTING_TODO_REMIND_TIME):
#             # 發送提醒訊息
#             send_reminder_message(user_id, todo)
#             todo.reminded = True


#----------------------------------- 處理個別使用者待辦事項 ----------------------------------------#

def set_todo_remind_time(user_id, user_message):
    try:
        hour, minute = map(int, user_message.split(":"))
        user_reminder_times = {'remind_time' : datetime.time(hour, minute)}
        user_todo_list[user_id].append(user_reminder_times)
        reply_message = f"此待辦事項提醒時間已更新為 {user_reminder_times[user_id].strftime('%H:%M')}"
        # check_reminder(user_id, user_reminder_times[user_id])

        AccessFile.write_user_reminderTime(user_id, user_reminder_times)
        
    except:
        reply_message = "輸入的時間格式不正確。\n\n已回到主選單。"

    user_state[user_id] = UserState.NORMAL
    return reply_message



# 處理在主選單下的訊息 (user_state=NORMAL)
def handle_normal_state(user_id, user_message, event):
    global user_state
    reply_message="初始預設2"

    if user_message == '新增 待辦事項':
        user_state[user_id] = UserState.ADD_TODO
        reply_message = f'請輸入待辦事項內容。'

    elif user_message == '顯示 待辦清單':
        message = Function.createTodoListMessage(user_id,user_todo_list)
        line_bot_api.reply_message(event.reply_token, message)
        reply_message = None
    
    elif user_message == '完成 待辦事項':   # 刪除功能建立於 06-03 12:03 ver1
        # 待辦清單是空的情況
        if user_todo_list[user_id] == []:
            reply_message = "目前無待辦事項\n已回到主選單。"
            return reply_message
        
        user_state[user_id] = UserState.DEL_TODO
        reply_message = f'請輸入完成的待辦事項編號'
        i = 1
        for todo in user_todo_list[user_id]:
            reply_message += f"\n{i}. {todo['text']}"
            i+= 1
    
    elif user_message == '設定':
        # 進入設定狀態
        user_state[user_id] = UserState.SETTING
        reply_message = f'\u2699\ufe0f 設定'
        setting_items = ['設定固定提醒時間','說明文件','新增特定待辦事項提醒時間']
        i = 1
        for item in setting_items:
            reply_message += f"\n{i}. {item}"
            i += 1

    else:
        reply_message = f'無此指令\n請輸入正確的指令。'

    return reply_message



# 接收訊息 
@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global user_todo_list, user_state, fixed_reminder_times
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
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
        return

    # 檢查使用者的狀態 (處於哪個功能狀態下)
    state = user_state[user_id]
    # 新增功能
    if state == UserState.ADD_TODO: 
            reply_message, user_todo_list = Function.handle_add_todo_state(user_id, user_message,user_todo_list)
            user_state[user_id] = UserState.NORMAL
        
    # 刪除功能
    elif state == UserState.DEL_TODO:
            reply_message,user_todo_list = Function.handle_del_todo_state(user_id, user_message,user_todo_list)
            user_state[user_id] = UserState.NORMAL

    # 設定功能
    elif state == UserState.SETTING:
            reply_message, user_state[user_id] = Function.setting_state(user_message, user_id, user_todo_list, user_state)
            # user_state[user_id] = UserState.NORMAL

    # 設定提醒時間功能
    elif state == UserState.SETTING_REMIND_TIME:
            try:
                hour, minute = map(int, user_message.split(':'))
                fixed_reminder_times[user_id] = datetime.time(hour, minute)
                reply_message = f'提醒時間已更新。{fixed_reminder_times[user_id].strftime("%H:%M")}'
                # 更新提醒時間
                check_fixed_reminder(user_id, fixed_reminder_times[user_id])
            except:
                reply_message = f'輸入的時間格式不正確。'

            user_state[user_id] = UserState.NORMAL

    elif state == UserState.SETTING_TODO_REMIND_TIME:

            if user_message.isdigit():
                number_remind = int(user_message)
                if number_remind > 0 and number_remind <= len(user_todo_list[user_id]):
                    reply_message = '設定此事項提醒時間。\n\n請輸入提醒時間 (hh:mm)'
                    set_todo_remind_time(user_id, user_message)

                else:
                    reply_message = f'\u2757 未找到此待辦事項 \u2757\n\n已回到主選單。'
                    user_state[user_id] = UserState.NORMAL
            else:
                reply_message = '\u2757 請輸入正確的數字編號 \u2757\n\n已回到主選單。'
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