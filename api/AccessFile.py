from pymongo import MongoClient
import json
import os

from api.ToDotask import ToDotaskEncoder

# 建立 MongoDB 連線
def create_mongodb_connection():
    client = MongoClient(os.environ.get('MONGODB_URI'))
    return client

# 讀取使用者資料
def read_user_data(user_id):
    # 建立 MongoDB 連線
    client = create_mongodb_connection()
    
    # 選擇資料庫和集合
    db = client['Project']
    collection = db['UserData']
    
    # 查找使用者的文件
    user_data = collection.find_one({'user_id': user_id})
    
    if user_data is None:
        # 使用者的文件不存在
        return None
    
    # 將 JSON 字符串轉換回物件列表
    data_json = user_data['data']
    data = json.loads(data_json)
    
    # 關閉 MongoDB 連線
    client.close()
    
    return data

# 寫入使用者資料
def write_user_data(user_id, data):
    # 將物件列表轉換為 JSON 字符串
    data_json = json.dumps(data)
    
    # 建立 MongoDB 連線
    client = create_mongodb_connection()
    
    # 選擇資料庫和集合
    db = client['Project']
    collection = db['UserData']
    
    # 檢查使用者的文件是否已存在
    existing_data = collection.find_one({'user_id': user_id})
    
    if existing_data is None:
        # 使用者的文件不存在，創建一個新文件
        user_data = {'user_id': user_id, 'data': data_json}
        collection.insert_one(user_data)
    else:
        # 使用者的文件已存在，更新資料
        collection.update_one({'user_id': user_id}, {'$set': {'data': data_json}})
    
    # 關閉 MongoDB 連線
    client.close()


# 寫入使用者 時間
def write_user_reminderTime(user_id, reminder_time):
    # 將物件列表轉換為 JSON 字符串
    data_json = json.dumps(reminder_time)
    
    # 建立 MongoDB 連線
    client = create_mongodb_connection()
    
    # 選擇資料庫和集合
    db = client['Project']
    collection = db['UserData']
    
    # 檢查使用者的文件是否已存在
    existing_data = collection.find_one({'user_id': user_id})
    
    if existing_data is None:
        # 使用者的文件不存在，創建一個新文件
        user_data = {'user_id': user_id, 'reminderTime': data_json}
        collection.insert_one(user_data)
    else:
        # 使用者的文件已存在，更新資料
        collection.update_one({'user_id': user_id}, {'$set': {'reminderTime': data_json}})
    
    # 關閉 MongoDB 連線
    client.close()


# 拿出所有用戶的時間

# def read_users_reminderTime(reminder_times):
#     # 建立 MongoDB 連線
#     client = create_mongodb_connection()
    
#     # 選擇資料庫和集合
#     db = client['Project']
#     collection = db['UserData']
    
#     # 尋找所有用戶
#     users = collection.find()

#     for user in users:
#     user_id = user['_id']