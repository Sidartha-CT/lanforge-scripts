from flask import Flask, request, jsonify
import time
import threading

app = Flask(__name__)

# Store current robot state
robot_state = {
    "goal": "",
    "res": 0,  # 0 = moving, 3 = reached
    "theta": 0.0
}

# Fake waypoints
waypoints = [
    {"name": "P1", "pose": {"x": 1.0, "y": 1.0, "theta": 0.0}},
    {"name": "P2", "pose": {"x": 2.0, "y": 2.0, "theta": 90.0}},
    {"name": "P3", "pose": {"x": 3.0, "y": 3.0, "theta": 180.0}},
]

@app.route("/reeman/position", methods=["GET"])
def get_position():
    return jsonify({"waypoints": waypoints})

@app.route("/reeman/nav_status", methods=["GET"])
def nav_status():
    return jsonify(robot_state)

@app.route("/cmd/nav_name", methods=["POST"])
def move_to_point():
    data = request.json
    point = data.get("point", "")
    robot_state["goal"] = point
    robot_state["res"] = 0  # moving

    # simulate movement
    def simulate_move():
        time.sleep(3)  # fake 3 seconds travel
        robot_state["res"] = 3  # reached
    threading.Thread(target=simulate_move).start()

    return jsonify({"status": "moving", "point": point})

@app.route("/cmd/nav", methods=["POST"])
def rotate():
    data = request.json
    angle = data.get("theta", 0)
    robot_state["theta"] = angle
    return jsonify({"status": "rotating", "theta": angle})

@app.route("/reeman/pose", methods=["GET"])
def get_pose():
    return jsonify({"theta": robot_state["theta"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
