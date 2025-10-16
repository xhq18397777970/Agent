import requests
import json

url = 'http://127.0.0.1:5001/api/chat'
data = {'message': '你好，这是一个测试消息', 'session_id': 'test_session'}
headers = {'Content-Type': 'application/json'}

try:
    response = requests.post(url, json=data, headers=headers, timeout=10)
    print('Status Code:', response.status_code)
    print('Response:', response.json())
except Exception as e:
    print('Error:', e)