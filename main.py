import requests


data = {"user": "admin", "password": 123}
response = requests.post(http://advanced.bancocn.com/admin/login.php, data=data)
print(response.text)