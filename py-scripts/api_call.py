import requests

response = requests.get("http://192.168.204.75:8080/layer4/wlan0_ftp95_l4,wlan0_ftp95_l43/list?fields=uc-avg,uc-max,uc-min,total-urls,rx%20rate%20(1m),bytes-rd,total-err", params={"key": "value"})
if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"GET failed with status {response.status_code}")
