import serial
import subprocess
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

class roboruka:
    def __init__(self, port):
        tty = serial.Serial(port=port, baudrate=115200, timeout=1)
        if not tty.writable():
            raise Exception("Could not open serial port")
        self.tty = tty
        self.angles = [0, -90, 0, 0, 0, 0]

    def __map(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
        
    def send_command(self, command):
        self.tty.write(command.encode('utf-8'))
    
    def get_angles(self):
        return self.angles.copy()

    def set_angles(self, angles):
        if len(angles) != 6:
            raise ValueError("Angles list must have exactly 6 elements")
        elif any(not isinstance(angle, (int, float)) for angle in angles):
            raise ValueError("All angles must be numbers")
        elif any(angle < -90 or angle > 90 for angle in angles):
            raise ValueError("Angles must be between -90 and 90 degrees")
        self.angles = angles.copy()
        for i, val in zip(range(6), angles):
            mapped_val = int(self.__map(val, -90, 90, 0, 1024))
            command = f"S{i+1}:{mapped_val:04}\n"
            self.send_command(command)

    def close(self):
        self.send_command("stop\n")
        self.tty.close()


if __name__ == "__main__":
    # Initialize robot
    try:
        robot = roboruka(port="/dev/ttyACM0")
    except Exception as e:
        print(f"Could not connect to robot: {e}")
        print("Running in simulation mode without hardware.")
        robot = None
    
    # Setup Flask app
    webserver_dir = os.path.join(os.path.dirname(__file__), 'webServer')
    app = Flask(__name__, static_folder=webserver_dir, static_url_path='')
    CORS(app)
    
    @app.route('/')
    def index():
        return send_from_directory(webserver_dir, 'index.html')
    
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
    
    @app.route('/get_angles', methods=['GET'])
    def get_angles():
        if robot is None:
            return jsonify({'angles': [0, -90, 0, 0, 0, 0]})
        return jsonify({'angles': robot.get_angles()})
    
    app.run(port=5000, debug=True)