import datetime

class ToDo_task:

    def __init__(self,text):
        self.__text= text
        self.__created_time=datetime.datetime.now()
        self.__reminder_time = datetime.datetime()
    
    def get_text (self):
        return self.__text
    
    