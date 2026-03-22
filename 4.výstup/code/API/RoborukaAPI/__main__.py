import os, glob
from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
from RoborukaAPI import roboruka, solve_ik


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
# Initialise robot
ports = sorted(glob.glob("/dev/ttyACM*"))
print(f"Found serial ports: {ports or 'none'}")
 
robot = None
if ports:
    try:
        robot = roboruka(port=ports[0])
        print(f"Connected to {ports[0]}")
    except Exception as e:
        print(f"Could not connect to {ports[0]}: {e}")
        print("Running in simulation mode without hardware.")
else:
    print("No /dev/ttyACM* devices found. Running in simulation mode.")

webserver_dir = os.path.join(os.path.dirname(__file__), 'webServer')
app = Flask(__name__, static_folder=webserver_dir, static_url_path='')
CORS(app)

# ---- FK page ----
@app.route('/')
def index():
    return redirect(url_for("fk_page"))

@app.route('/fk')
def fk_page():
    return send_from_directory(webserver_dir, 'fk.html')

# ---- IK page ----
@app.route('/ik')
def ik_page():
    return send_from_directory(webserver_dir, 'ik.html')

# ---- API: set joint angles directly ----
@app.route('/set_angles', methods=['POST'])
def set_angles():
    if robot is None:
        return jsonify({'error': 'Robot not connected'}), 500
    data = request.get_json()
    angles = data.get('angles')
    if not angles or len(angles) != 6:
        return jsonify({'error': 'Invalid angles'}), 400
    try:
        robot.set_angles(angles)
        return jsonify({'status': 'ok'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

# ---- API: read current angles ----
@app.route('/get_angles', methods=['GET'])
def get_angles():
    if robot is None:
        return jsonify({'angles': [0, -90, 0, 0, 0, 0]})
    return jsonify({'angles': robot.get_angles()})

# ---- API: solve IK and (optionally) send to robot ----
@app.route('/solve_ik', methods=['POST'])
def solve_ik_endpoint():
    data = request.get_json()
    try:
        user_x    = float(data['x'])
        user_y    = float(data['y'])
        user_z    = float(data['z'])
        theta_deg = float(data['theta'])
        roll      = float(data.get('roll', 0))
        gripper   = float(data.get('gripper', 0))
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({'error': f'Bad request: {e}'}), 400

    # Y must be non-negative (only forward half-space)
    if user_y < 0:
        return jsonify({'error': 'Y must be >= 0 (forward half-space only)'}), 400

    result = solve_ik(user_x, user_y, user_z, theta_deg)

    if result is None:
        return jsonify({'error': 'Target is singular (too close to solve)'}), 422

    # Compute grip servo angle from gripper percentage
    grip_angle = max(-90.0, min(90.0, 100 - gripper / 100 * 70))

    # Send to robot if connected
    if robot is not None:
        angles = [
            result['yaw'],
            -result['pitch1'],   # sign convention matches FK sender
            result['pitch2'],
            result['pitch3'],
            roll,
            grip_angle,
        ]
        try:
            robot.set_angles(angles)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    return jsonify({
        'reachable': result['reachable'],
        'yaw':    result['yaw'],
        'pitch1': result['pitch1'],
        'pitch2': result['pitch2'],
        'pitch3': result['pitch3'],
        'roll':   roll,
        'gripper': gripper,
    })

app.run(port=5000, debug=True)