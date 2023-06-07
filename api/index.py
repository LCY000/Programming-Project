import dateutil
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
    MessageEvent, TextMessage, TextSendMessage, RichMenu, QuickReply, QuickReplyButton, MessageAction
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
        #-----#
        check_reminders_todo()
        return '提醒檢查完成'
    except Exception as e:
        print("Error in cpm:", str(e))  # 除錯訊息
        return '檢查失敗'

#----------------------------------------- 分隔線 -----------------------------------------#
 

# 使用者狀態的列舉類型
class UserState(Enum):
    NORMAL = 0
    ADD_TODO = 1
    DEL_TODO = 2
    SETTING = 3
    SETTING_REMIND_TIME = 4
    SETTING_TODO_REMIND_TIME_1 = 5
    SETTING_TODO_REMIND_TIME_2 = 6

# 用戶的待辦事項
user_todo_list = {}

# 追蹤使用者的狀態
user_state = {}
fixed_reminder_times = {}
user_reminder_times = {}
user_options = {}


# 建立快速回覆按鈕
quick_buttons_setting = [
    QuickReplyButton(action=MessageAction(label="設定每日提醒時間", text="設定每天提醒時間")),
    QuickReplyButton(action=MessageAction(label="新增特定待辦事項提醒時間", text="新增特定待辦事項提醒時間")),
    QuickReplyButton(action=MessageAction(label="說明文件", text="顯示 說明文件"))
]
# 建立快速回覆的 QuickReply 物件
quick_reply_buttons_setting = QuickReply(items=quick_buttons_setting)
quick_reply_buttons_remind_time = QuickReply(items=[QuickReplyButton(action=MessageAction(label="關閉提醒", text="關閉提醒"))])
quick_reply_buttons_fixed_remind_time = QuickReply(items=[QuickReplyButton(action=MessageAction(label="關閉每日提醒", text="關閉每日提醒"))])
# 判斷當前時間是否為提醒時間
def check_reminder_time(reminder_time):
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    taiwan_now_time = now.astimezone(datetime.timezone(datetime.timedelta(hours=8))) # 轉換時區 -> 東八區

    if taiwan_now_time.time().hour == reminder_time.hour and taiwan_now_time.time().minute == reminder_time.minute:
        return True
    else:
        # debug
        # print('false' + f'fixed_remind_time {reminder_time} remind_hour = {reminder_time.hour} remind_minute = {reminder_time.minute}  now = {taiwan_now_time.time()} now.hour = {taiwan_now_time.time().hour} now.minute = {taiwan_now_time.time().minute}')
        return False

def check_fixed_reminder(user_id, reminder_time):
    # print('in cfr')
    # 檢查提醒時間並發送消息
    if check_reminder_time(reminder_time):
        message = '提醒：您有待辦事項需要處理！'
        line_bot_api.push_message(user_id, TextSendMessage(text=message))

def check_reminders():
    # print('in crs')
    for user_id in user_todo_list: 
        if user_id in fixed_reminder_times:
            # print('in for loop')
            check_fixed_reminder(user_id, fixed_reminder_times[user_id])
        # 預計提醒個別事項function可以做這裡##

# ----------------------------- 處理特定待辦事項的提醒功能 ----------------------------- #

def check_todo_reminder_time(reminder_time):
    print('in ctrt')
    # 將提醒時間的字符串轉回datetime時間物件。
    format_string = "%Y-%m-%d %H:%M"
    reminder_time_f = datetime.datetime.strptime(reminder_time, format_string)

    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    taiwan_now_time = now.astimezone(datetime.timezone(datetime.timedelta(hours=8))) # 轉換時區 -> 東八區
    if taiwan_now_time.year == reminder_time_f.year and taiwan_now_time.month == reminder_time_f.month and taiwan_now_time.day == reminder_time_f.day and taiwan_now_time.time().hour == reminder_time_f.hour and taiwan_now_time.time().minute == reminder_time_f.minute:
        return True
    else:
        print('False ' + f'now time = {taiwan_now_time} reminder_time = {reminder_time}')
        return False

def check_todo_reminder(user_id, reminder_time, todo):
    # 檢查特定事項的提醒時間並發送消息
    print('in ctr')
    if check_todo_reminder_time(reminder_time):
        message = f'提醒: {todo} 需要完成'
        line_bot_api.push_message(user_id, TextSendMessage(text=message))
        return True
    return False


def check_reminders_todo():
    print('in crt')
    try:
        for user_id in user_todo_list:
            for i in range(len(user_todo_list[user_id])):
                if 'remind_time' in user_todo_list[user_id][i]:
                    print('in for loop')
                    isTodoReminded = check_todo_reminder(user_id, user_todo_list[user_id][i]['remind_time'], user_todo_list[user_id][i]['text'])
        
                    if isTodoReminded :
                        del user_todo_list[user_id][i]['remind_time']
                        AccessFile.write_user_data(user_id, user_todo_list[user_id])
    except Exception as e:
        print("Error in crt: " + str(e))

# 處理個別使用者待辦事項
def set_todo_remind_time(user_id, user_message):
    global user_options , user_todo_list

    if user_message == '關閉提醒':
        if 'remind_time' in user_todo_list[user_id][user_options[user_id]-1]:
            del user_todo_list[user_id][user_options[user_id]-1]['remind_time']
            reply_message = '\u2705此事項提醒已關閉\u2705\n\n已回到主選單。'
            del user_options[user_id]
            # 將更新後的資料寫回資料庫
            AccessFile.write_user_data(user_id, user_todo_list[user_id])

            user_state[user_id] = UserState.NORMAL
            return reply_message
        else:
            reply_message = '\u2757此事項尚未設定提醒\u2757\n\n已回到主選單。'
            del user_options[user_id]
            user_state[user_id] = UserState.NORMAL
            return reply_message

    try:
        year, month, day, hour, minute = map(int, user_message.split("-"))
        
        # 將時間儲存到使用者的清單(陣列)的單個事項字典裡，存為字串
        remind_time = datetime.datetime(year, month, day, hour, minute)
        user_todo_list[user_id][user_options[user_id]-1]['remind_time'] = remind_time.strftime('%Y-%m-%d %H:%M')

        reply_message = f"\u2705此事項提醒時間已更新為{user_todo_list[user_id][user_options[user_id]-1]['remind_time']}\u2705\n\n已回到主選單。"
        
        check_todo_reminder(user_id, user_todo_list[user_id][user_options[user_id]-1]['remind_time'], user_todo_list[user_id][user_options[user_id]-1]['text'])

        # 更新資料庫中的用戶數據
        AccessFile.write_user_data(user_id, user_todo_list[user_id])
        
        # check_reminder(user_id, user_reminder_times[user_id])
    except Exception as e:
        reply_message = "\u2757輸入的時間格式不正確。\u2757\n\n已回到主選單。"
        print(f"錯誤訊息：{str(e)}")  # 輸出錯誤訊息到控制台

    # 清除輸入編號的記憶體
    del user_options[user_id]
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
        message = Function.createTodoListMessage(user_id,user_todo_list, fixed_reminder_times)
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
        setting_items = ['設定每日提醒時間','設定特定待辦事項提醒時間', '說明文件']
        i = 1
        for item in setting_items:
            reply_message += f"\n{i}. {item}"
            i += 1

    else:
        reply_message = f'\u2757無此指令\u2757\n請輸入正確的指令。'

    return reply_message



# 接收訊息 
@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global user_todo_list, user_state, fixed_reminder_times, user_options
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
            # 此程式片段有問題!!
            if user_message == '關閉每日提醒':
                if user_id in fixed_reminder_times:
                    del fixed_reminder_times[user_id]
                    reply_message = '每日提醒已關閉'
                else:
                    reply_message = '尚未設定提醒'
            else:
                try:
                    hour, minute = map(int, user_message.split(':'))
                    fixed_reminder_times[user_id] = datetime.time(hour, minute)
                    reply_message = f'\u2705提醒時間已更新為 {fixed_reminder_times[user_id].strftime("%H:%M")}\u2705\n\n已回到主選單。'
                    # 更新提醒時間
                    check_fixed_reminder(user_id, fixed_reminder_times[user_id])
                except:
                    reply_message = f'輸入的時間格式不正確。'
                    

            user_state[user_id] = UserState.NORMAL

    elif state == UserState.SETTING_TODO_REMIND_TIME_1:

            if user_message.isdigit():
                number_remind = int(user_message)
                if number_remind > 0 and number_remind <= len(user_todo_list[user_id]):
                    reply_message = '設定此事項提醒時間。\n\n請輸入提醒時間，以-分隔 (yyyy-mm-dd-hh-mm)'
                    # 紀錄輸入的編號
                    user_options[user_id] = number_remind
                    user_state[user_id] = UserState.SETTING_TODO_REMIND_TIME_2
                else:
                    reply_message = f'\u2757 未找到此待辦事項 \u2757\n\n已回到主選單。'
                    user_state[user_id] = UserState.NORMAL
            else:
                reply_message = '\u2757 請輸入正確的數字編號 \u2757\n\n已回到主選單。'
                user_state[user_id] = UserState.NORMAL

    elif state == UserState.SETTING_TODO_REMIND_TIME_2:
            reply_message = set_todo_remind_time(user_id, user_message)

    # 主選單
    else:
        reply_message = handle_normal_state(user_id, user_message, event)
        # 要是已輸出待辦清單，則直接結束
        if reply_message is None:
            return
    
    # 輸出回覆訊息 (預防突發意外，保險偵錯)
    if reply_message:
        if user_state[user_id] == UserState.SETTING:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message,quick_reply =quick_reply_buttons_setting))
        elif user_state[user_id] == UserState.SETTING_REMIND_TIME:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message,quick_reply =quick_reply_buttons_fixed_remind_time))
        elif user_state[user_id] == UserState.SETTING_TODO_REMIND_TIME_2:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message,quick_reply =quick_reply_buttons_remind_time))
        else:    
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
    else:
        # 處理空訊息的情況
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="空訊息"))



if __name__ == "__main__":
    app.run()   