import requests
import json

url1 = "http://192.168.242.2:8080/adb"
url2 = "http://192.168.207.78:8080/adb"
response1 = requests.get(url1, verify=False)
response2 = requests.get(url2, verify=False)
data1 = json.loads(response1.text)
data2 = json.loads(response2.text)
print("Response from URL 1:", data1)
print("Response from URL 2:", data2)