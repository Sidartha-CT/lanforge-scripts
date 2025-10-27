import requests
import time

class RobotClass:
    def __init__(self):
        self.robo_ip = ""

    def move_to_coordinate(self, coordinate=None):
        url = f"http://{self.robo_ip}/cmd/nav_name"
        data = {"coordinate": coordinate}

        print(f"[MOVE] Sending coordinates: {data}")
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("[MOVE] Success  Robot reached the target.")
            return "success"
        else:
            print("[MOVE] Failed ", response.text)
            return "fail"

    def rotate_angle(self, x, y, angle):
        url = f"http://{self.robo_ip}/cmd/nav_angle"
        data = {"x": x, "y": y, "angle": angle}

        print(f"[ROTATE] Rotating: {data}")
        response = requests.post(url, json=data)

        if response.status_code == 200:
            print("[ROTATE] Success Rotation completed.")
            return "success"
        else:
            print("[ROTATE] Failed ", response.text)
            return "fail"

    def wait_for_battery(self):
        url = f"http://{self.robo_ip}/reeman/battery"
        response = requests.get(url)
        data = response.json()
        level = data.get("level", 0)

        if level < 20:
            print(f"[BATTERY] Low ({level}%). Waiting for charge...")
            time.sleep(2)
        else:
            print(f"[BATTERY] OK ({level}%). Continuing.")
        return "ok"

def main():
    robo = RobotClass()
    robo.robo_ip = "127.0.0.1:5000"  # Point to your fake robot API

    robo.wait_for_battery()

    # Example coordinates
    x, y, theta = 1, 2, 3
    for i in range(3):
        move_status = robo.move_to_coordinate(x, y, theta)
        if move_status == "success":
            print("[MAIN] Move successful, now rotating...")
            rotate_status = robo.rotate_angle(x, y, theta)
            if rotate_status == "success":
                print("[MAIN] All operations completed successfully ")
            else:
                print("[MAIN] Rotation failed ")
        else:
            print("[MAIN] Move failed ")

if __name__ == "__main__":
    main()