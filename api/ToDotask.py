import datetime

class ToDotask:

    def __init__(self,text):
        self.__text= text
        self.__created_time=datetime.datetime.now()
        self.__reminder_time = datetime.datetime()
    
    def get_text (self):
        return self.__text
    
    def set_text (self,message):
        self.__text = message