import requests
import time

class RobotClass:
    def __init__(self):
        pass

    def wait_for_battery(self):
        battery_url = f"http://{self.robo_ip}/reeman/base_encode"
        status_url=f"http://{self.robo_ip}/reeman/nav_status"
        move_url=f"http://{self.robo_ip}/cmd/nav_name"
        while True:
            try:
                response = requests.get(battery_url, timeout=5)
                response.raise_for_status()
                data = response.json()
                battery = data.get("battery", 0)
                charge_flag = data.get("chargeFlag", 0)
                retries=0
                if battery <= 27:
                    print(f"Battery low ({battery}%). Pausing test until fully charged...")
                    requests.post(move_url,json={"point":self.charge_point_name})
                    while True:
                        matched = False
                        try:
                            response = requests.get(status_url,timeout=5)
                            response.raise_for_status()
                            nav_status = response.json()
                        except (requests.RequestException, ValueError) as e:
                            print(f"[ERROR] Failed to get robot status: {e}")
                            time.sleep(5)
                            retries+=1
                            if(retries == 15):
                                abort = True
                                break
                            
                            continue
                        goal = nav_status.get("goal","")
                        state=nav_status.get("res","")
                        if goal == self.charge_point_name and state == 3:
                            matched = True
                            break

                    while True:
                        print("enteredwhileee")
                        time.sleep(300) 
                        try:
                            resp = requests.get(battery_url, timeout=5)
                            resp.raise_for_status()
                            charge_data = resp.json()
                            new_battery = charge_data.get("battery", 0)
                            print(f"Current battery: {new_battery}%")
                            if new_battery > 28:
                                print("Battery full. Resuming test...")
                                return
                        except Exception as e:
                            print(f"[ERROR] Checking charge: {e}")
                            time.sleep(300)
                else:
                    print(f"[OK] Battery at {battery}%. Continuing test.")
                    return

            except Exception as e:
                print(f"[ERROR] Failed to check battery: {e}")
                time.sleep(600)

    def move_to_coordinate(self,coord):
        moverobo_url = 'http://'+self.robo_ip+'/cmd/nav_name'
        status_url= 'http://'+self.robo_ip+'/reeman/nav_status'
        requests.post(moverobo_url,json={"point":coord})
        retries=0
        while True:
            matched = False
            try:
                response = requests.get(status_url,timeout=5)
                response.raise_for_status()
                nav_status = response.json()
            except (requests.RequestException, ValueError) as e:
                print(f"[ERROR] Failed to get robot status: {e}")
                time.sleep(5)
                retries+=1
                if(retries == 15):
                    abort = True
                    break
                
                continue
            goal = nav_status.get("goal","")
            state=nav_status.get("res","")
            distance=nav_status.get("dist","")
            if goal == coord and state == 3 and distance < 0.5:
                matched = True
                break
                
        return  matched

    def rotate_angle(self,target_x,target_y,angle):
        nav_pathurl= 'http://'+self.robo_ip+'/cmd/nav'
        pose_url= 'http://'+self.robo_ip+'/reeman/pose'
        requests.post(nav_pathurl,json={"x":target_x,"y":target_y,"theta":angle})
        retries_for_theta=0
        rotated=False
        while True:
            try:
                response = requests.get(pose_url,timeout=5)
                response.raise_for_status()
                data_pose=response.json()
            except (requests.RequestException, ValueError) as e:
                print(f"[ERROR] Failed to get robot status of pose: {e}")
                time.sleep(5)
                retries_for_theta+=1
                if(retries_for_theta == 5):
                    break
                continue

            theta=data_pose['theta']
            theta = round(theta, 2)
            if abs(angle - theta) <= 0.15:
                rotated = True
                break
        
        return rotated
    


def main():
    print("hello")
    
if __name__ == "__main__":
    main()