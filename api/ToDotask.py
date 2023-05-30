import datetime

class ToDotask:

    def __init__(self,text):
        self.text= text
        self.created_time=datetime.datetime.now()
        # self.reminder_time = datetime.datetime()

    def get_text (self):
        return self.text
    
    def set_text (self,message):
        self.text = message