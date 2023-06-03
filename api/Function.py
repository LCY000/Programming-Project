from api import AccessFile
from linebot.models import FlexSendMessage


# 【顯示清單】  回傳顯示清單的訊息
def createTodoListMessage(user_id,user_todo_list):
    if user_todo_list[user_id] == []:
        list_items = [{"type" : "text", "text" : "無待辦事項"}]
    else:
        i = 1
        # 建立待辦事項清單的條列項目
        todoList = user_todo_list[user_id]
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



# 【新增】  新增待辦事項狀態下的訊息
def handle_add_todo_state(user_id, user_message,user_todo_list):
    reply_message = '' # 提供預設值
    
    # if user_message == '結束' or user_message == '1':
    #     reply_message = '已結束新增功能' # 如果使用者輸入1 即代表取消新增功能並回到一般狀態

    # 創建一個新的待辦事項
    new_task = {'text' : user_message}
    user_todo_list[user_id].append(new_task)

    AccessFile.write_user_data(user_id,user_todo_list[user_id])     # 將資料寫入檔案

    reply_message = '已新增待辦事項：\n{}\n\n請輸入下一個要新增的待辦事項'.format(user_message)

    return reply_message, user_todo_list

# 【完成】  完成待辦事項狀態下的訊息
def handle_del_todo_state(user_id, user_message, user_todo_list):
    reply_message = '' # 提供預設值

    # if user_message == '結束' or user_message == '1':
    #     reply_message = '已結束完成功能' # 如果使用者輸入1 即代表取消完成功能並回到一般狀態

    # 遍歷用戶的待辦事項列表
    for task in user_todo_list[user_id]:
        if task['text'] == user_message:
            user_todo_list[user_id].remove(task)  # 刪除匹配的待辦事項內容
            AccessFile.write_user_data(user_id, user_todo_list[user_id]) # 將更新後的待辦清單寫入資料庫
            reply_message = '已完成待辦事項：\n{}'.format(user_message)
            break
    else:
        reply_message = '未找到待辦事項：\n{}'.format(user_message) # 如果沒有找到對應的待辦事項內容，則回傳此訊息

    return reply_message, user_todo_list