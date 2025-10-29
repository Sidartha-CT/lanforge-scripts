import time
import requests
import argparse

def move_robot(ip, coordinates, durations):
    coords = [c.strip() for c in coordinates.split(",")]
    times = [int(t.strip()) for t in durations.split(",")]

    if len(coords) != len(times):
        raise ValueError("Number of coordinates and durations must match!")

    for i, (coord, wait_time) in enumerate(zip(coords, times), start=1):
        move_url = f"http://{ip}/move"
        status_url = f"http://{ip}/status"

        payload = {"coordinate": coord}
        
        try:
            print(f"[Step {i}] Sending move request to {coord}...")
            response = requests.post(move_url, json=payload, timeout=10)
            response.raise_for_status()
            print(f"✅ Move command sent for {coord}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send move request for {coord}: {e}")
            continue

        # Polling until robot reaches the coordinate
        print(f"📡 Waiting for robot to reach {coord}...")
        reached = False
        while not reached:
            try:
                status = requests.get(status_url, timeout=10).json()
                if status.get("current_coordinate") == coord and status.get("state") == "reached":
                    print(f"✅ Robot reached {coord}")
                    reached = True
                else:
                    print("⏳ Still moving...")
                    time.sleep(5)  # wait before next check
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Status check failed: {e}, retrying in 5s...")
                time.sleep(5)

        # Now wait at the coordinate
        print(f"⏳ Waiting at {coord} for {wait_time} minutes...")
        time.sleep(wait_time * 60)
        print(f"✅ Finished waiting at {coord}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Move robot to coordinates and wait")
    parser.add_argument("--ip", required=True, help="Robot IP address")
    parser.add_argument("--coords", required=True, help="Comma-separated coordinates (e.g., 1,2,3)")
    parser.add_argument("--durations", required=True, help="Comma-separated durations in minutes (e.g., 1,2,3)")
    args = parser.parse_args()

    move_robot(args.ip, args.coords, args.durations)
