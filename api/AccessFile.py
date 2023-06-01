from pymongo import MongoClient
import json

from api.ToDotask import ToDotaskEncoder

# 建立 MongoDB 連線
def create_mongodb_connection():
    client = MongoClient('mongodb+srv://vercel01:xagqPVm8Ne9dkOQi@userdata.p0fqlpw.mongodb.net/?retryWrites=true&w=majority')
    return client

# 讀取使用者資料
def read_user_data(user_id):
    # 建立 MongoDB 連線
    client = create_mongodb_connection()
    
    # 選擇資料庫和集合
    db = client['your_database_name']
    collection = db['your_collection_name']
    
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
    data_json = json.dumps(data,cls = ToDotaskEncoder)
    
    # 建立 MongoDB 連線
    client = create_mongodb_connection()
    
    # 選擇資料庫和集合
    db = client['your_database_name']
    collection = db['your_collection_name']
    
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