"""

import datetime, json

class ToDotask:

    def __init__(self,text):
        self.text= text
        # self.created_time=datetime.datetime.now()
        # self.reminder_time = datetime.datetime()

    def get_text (self):
        return self.text
    
    def set_text (self,message):
        self.text = message

# Json 編碼器 將物件資料編碼處理後儲存至.json檔中
class ToDotaskEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ToDotask):
            return obj.__dict__
        # if isinstance(obj, datetime):
        #     return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)

"""