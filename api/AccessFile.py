import os
import gspread
from google.oauth2.service_account import Credentials

# 設定憑證路徑
credentials_path = 'path/to/credentials.json'

# 從 Google 試算表讀取 user_todo_list
def load_user_todo_list(user_id):
    # 連線到 Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(credentials_path, scopes=scope)
    client = gspread.authorize(credentials)

    # 開啟試算表
    spreadsheet = client.open('Your Spreadsheet Name')  # 替換成你的試算表名稱

    # 選擇工作表
    worksheet = spreadsheet.sheet1  # 選擇你的工作表

    # 讀取 user_todo_list
    data = worksheet.get_all_records()
    todo_list = [record['todo'] for record in data if record['user_id'] == user_id]

    return todo_list