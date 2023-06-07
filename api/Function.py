from api import AccessFile
from linebot.models import FlexSendMessage,TextSendMessage,QuickReply,QuickReplyButton,MessageAction
from linebot import LineBotApi
import os
from api import index

line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))

# 【顯示清單】  回傳顯示清單的訊息
def createTodoListMessage(user_id,user_todo_list, fixed_reminder_times):
    fixed_reminder_times_text = ''
    if user_todo_list[user_id] == []:
        list_items = [{"type" : "text", "text" : "無待辦事項"}]
    else:
        i = 1
        # 建立待辦事項清單的條列項目
        todoList = user_todo_list[user_id]
        list_items = []

        
        if user_id in fixed_reminder_times:
            fixed_reminder_times_text = str(fixed_reminder_times[user_id].strftime("%H:%M"))
            # fixed_reminder_times_items = {"type" : "text", "text" : fixed_reminder_times_text}
            # list_items.append(fixed_reminder_times_items)
        else:
            fixed_reminder_times_text = '尚未設置'

        for todo in todoList:
            # 印出所有待辦事項內容，如果有設定時間，將會印出預計提醒時間的文字。
            item = {"type": "text", "text": str(str(i) + '. ' + todo['text'] + '\t' + ' 預計提醒時間: ' + todo['remind_time']) if 'remind_time' in todo else str(str(i) + '. ' + todo['text'])}
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
                    {"type": "text", "text": f'\ud83d\udd5b 每日提醒時間: {fixed_reminder_times_text}' , "size": "sm", "color": "#888888"},
                    # {"type": "text", "text": " ", "weight": "bold", "size": "lg"},
                    {"type": "text", "text": "待辦事項清單", "weight": "bold", "size": "lg"},
                    *list_items # 將條列項目展開添加到 "contents" 中
                ]
            }
        }
    )
    return flex_message



# 【新增】  新增待辦事項狀態下的訊息
def handle_add_todo_state(user_id, user_message,user_todo_list):
    reply_message = '' # 提供預設值
    
    # 創建一個新的待辦事項
    new_task = {'text' : user_message}
    user_todo_list[user_id].append(new_task)
    reply_message = '\u2705 已新增待辦事項 \u2705\n{}\n\n已回到主選單'.format(user_message) # \n\n是否為此待辦事項新增提醒功能?
    AccessFile.write_user_data(user_id,user_todo_list[user_id])

    return reply_message, user_todo_list

# 【完成】  完成待辦事項狀態下的訊息
def handle_del_todo_state(user_id, user_message, user_todo_list):
    reply_message = '' # 提供預設值

    # 驗證是否是輸入編號
    if user_message.isdigit():

        number= int(user_message)
        if number > 0 and number <= len(user_todo_list[user_id]):
            reply_message = f"\u2705 已完成: {user_todo_list[user_id][number-1]['text']} \u2705\n\n已回到主選單"
            del user_todo_list[user_id][number-1]  # 刪除匹配的待辦事項內容
            AccessFile.write_user_data(user_id,user_todo_list[user_id]) # 將數據傳入資料庫
        else:
            reply_message = f'\u2757 未找到此待辦事項 \u2757\n\n已回到主選單。' # 如果沒有找到對應的待辦事項內容，則回傳此訊息

    else:
        reply_message = '\u2757 請輸入正確的數字編號 \u2757\n\n已回到主選單。' # 如果沒有找到對應的待辦事項內容，則回傳此訊息

    return reply_message, user_todo_list

# 【設定】  設定功能
def setting_state(user_message, user_id, user_todo_list, user_state):

    if user_message == '設定每天提醒時間':
        
        if len(user_todo_list[user_id]) > 0:
            user_state[user_id] = index.UserState.SETTING_REMIND_TIME
            reply_message = '設定每日提醒時間。\n\n請輸入提醒時間 (hh:mm)'
        else:
            reply_message = '\u2757 目前無待辦事項 \u2757\n\n已回到主選單狀態。'
            user_state[user_id] = index.UserState.NORMAL

    elif user_message == '顯示 說明文件':

        reply_message = '1. 在任何情況下輸入「取消」或「0」\n   即可中斷、跳出當下功能\n\n已回到主選單狀態。'
        user_state[user_id] = index.UserState.NORMAL
    
    elif user_message == '設定特定待辦事項提醒時間':

        reply_message = f'請輸入要新增提醒時間的待辦事項編號'

        i = 1
        for todo in user_todo_list[user_id]:
            reply_message += f"\n{i}. {todo['text']}"
            i+= 1
        
        user_state[user_id] = index.UserState.SETTING_TODO_REMIND_TIME_1
        
    else:
        reply_message = f'\u2757 未找到此設定選項 \u2757\n\n已回到主選單狀態。'
        user_state[user_id] = index.UserState.NORMAL

    return reply_message, user_state[user_id]
