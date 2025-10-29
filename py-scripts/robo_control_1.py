import argparse
import requests
import time
import math
import os
import json
from datetime import datetime

def angles_to_radians(angles):
    result = []
    for angle in angles:
        angle = float(angle)
        if angle > 180:
            angle -= 360
        elif angle <= -180:
            angle += 360
        result.append(round(math.radians(angle), 2))
    return result

def update_navdata(nav_data, status, coord, angle=""):
    try:
        with open(nav_data, "r") as f:
            navdata = json.load(f)
    except Exception:
        navdata = {}

    # Update current state
    navdata["status"] = status
    navdata["Canbee_location"] = coord
    navdata["angle"] = angle

    # Maintain history
    # if "history" not in navdata:
    #     navdata["history"] = []
    # navdata["history"].append({
    #     "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #     "status": status,
    #     "coord": coord,
    #     "angle": angle
    # })

    with open(nav_data, "w") as f:
        json.dump(navdata, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        prog="lf_interop_throughput.py",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Robot throughput test runner",
    )
    required = parser.add_argument_group("Required")
    optional = parser.add_argument_group("Optional")

    required.add_argument("--robot_ip", default="localhost", help="Robot server IP")
    optional.add_argument("--robot_port", default=5000, help="Robot server port")
    required.add_argument("--coordinate", help="Comma-separated list of waypoints")
    optional.add_argument("--rotation", help="Angles to rotate at each point")
    parser.add_argument("--duration", required=True, help="Comma-separated durations in minutes")
    optional.add_argument('--result_dir', help='Specify the result dir to store the runtime logs', default='')

    args = parser.parse_args()

    robo_ip = args.robot_ip
    robo_port = args.robot_port
    rotation_enabled = False
    coord_list = args.coordinate.split(",")
    duration_list = args.duration.split(",")
    base_dir = os.path.dirname(os.path.dirname(args.result_dir))
    nav_data = os.path.join(base_dir, 'nav_data.json') 
    with open(nav_data, "w") as file:
        json.dump({}, file)

    if args.rotation:
        angle_list = args.rotation.split(",")
        list_of_rotation = angles_to_radians(angle_list)
        rotation_enabled = True
    else:
        angle_list = []
        list_of_rotation = [0]

    if len(coord_list) != len(duration_list):
        raise ValueError("Number of coordinates and durations must match!")

    # ✅ FIX: Include port everywhere
    position_url = f"http://{robo_ip}:{robo_port}/reeman/position"
    status_url   = f"http://{robo_ip}:{robo_port}/reeman/nav_status"
    nav_pathurl  = f"http://{robo_ip}:{robo_port}/cmd/nav" if rotation_enabled else None
    pose_url     = f"http://{robo_ip}:{robo_port}/reeman/pose" if rotation_enabled else None
    moverobo_url = f"http://{robo_ip}:{robo_port}/cmd/nav_name"

    # --- Fetch waypoints
    try:
        print(f"[DEBUG] Fetching waypoints from {position_url}")
        data = requests.get(position_url).json()
        waypoint_list = [
            {wp["name"]: {"x": wp["pose"]["x"], "y": wp["pose"]["y"], "theta": wp["pose"]["theta"]}}
            for wp in data["waypoints"]
        ]
    except Exception as e:
        print(f"[ERROR] Failed to fetch waypoints: {e}")
        return

    while True:
        for i in range(len(coord_list)):
            coord = coord_list[i]
            print(f"Moving to {coord} via {moverobo_url}")
            try:
                requests.post(moverobo_url, json={"point": coord})
                update_navdata(nav_data, "Moving", coord, "")
            except Exception as e:
                print(f"[ERROR] Failed to send nav command: {e}")
                continue

            # Get target x,y
            target_x, target_y = None, None
            for wp in waypoint_list:
                if coord in wp:
                    target_x = wp[coord]["x"]
                    target_y = wp[coord]["y"]

            retries = 0
            while True:
                try:
                    nav_status = requests.get(status_url, timeout=5).json()
                except Exception as e:
                    print(f"[ERROR] Status fetch failed: {e}")
                    time.sleep(5)
                    retries += 1
                    if retries >= 15:
                        print("Skipping this coordinate due to too many retries...")
                        break
                    continue

                goal = nav_status.get("goal", "")
                state = nav_status.get("res", "")

                reached = False
                if goal == coord and state == 3:
                    reached = True
                elif "," in goal:
                    gx, gy, *_ = map(float, goal.split(","))
                    if gx == target_x and gy == target_y and state == 3:
                        reached = True

                if reached:
                    print(f"Reached {coord}")
                    update_navdata(nav_data, "Reached", coord, "")

                    # --- Handle rotations
                    for j, angle in enumerate(list_of_rotation):
                        if rotation_enabled:
                            try:
                                print(f"Rotating to {angle_list[j]}° (rad={angle})")
                                requests.post(nav_pathurl, json={"x": target_x, "y": target_y, "theta": angle})
                                update_navdata(nav_data, "Rotating", coord, str(angle_list[j]))
                            except Exception as e:
                                print(f"[ERROR] Rotation command failed: {e}")
                                continue

                            retries_theta = 0
                            while True:
                                try:
                                    data_pose = requests.get(pose_url, timeout=5).json()
                                except Exception as e:
                                    print(f"[ERROR] Pose fetch failed: {e}")
                                    time.sleep(5)
                                    retries_theta += 1
                                    if retries_theta >= 5:
                                        print("Skipping this rotation...")
                                        break
                                    continue

                                theta = round(data_pose.get("theta", 0), 2)
                                if abs(angle - theta) <= 0.15:
                                    print(f"Completed rotation to {angle_list[j]}°")
                                    # ✅ FIX: Don't reset angle to empty string
                                    update_navdata(nav_data, "Reached", coord, str(angle_list[j]))
                                    break

                        # --- Wait at the point
                        wait_time = float(duration_list[i]) * 60
                        print(f"Waiting {wait_time}s at {coord}")
                        time.sleep(wait_time)

                    break  

        print("Iteration completed. Restarting...")

if __name__ == "__main__":
    main()
