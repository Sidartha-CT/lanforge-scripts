from flask import Flask, request, jsonify
import time
import threading

app = Flask(__name__)

# global state for the "robot"
robot_state = {
    "current_coordinate": None,
    "state": "idle"
}

def simulate_movement(coord, delay=5):
    """Simulate robot moving (takes delay seconds)."""
    global robot_state
    robot_state["state"] = "moving"
    time.sleep(delay)
    robot_state["current_coordinate"] = coord
    robot_state["state"] = "reached"

@app.route("/move", methods=["POST"])
def move():
    data = request.get_json()
    coord = data.get("coordinate")
    # simulate movement in background
    threading.Thread(target=simulate_movement, args=(coord,)).start()
    return jsonify({"message": f"Moving to {coord}"}), 200

@app.route("/status", methods=["GET"])
def status():
    return jsonify(robot_state), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
