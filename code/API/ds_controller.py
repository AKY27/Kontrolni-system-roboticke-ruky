#!./venv/bin/python3
from RoborukaAPI import roboruka
import dualsense_controller
import argparse
from time import sleep

argparser = argparse.ArgumentParser(description="Control Roboruka with DualSense controller")
argparser.add_argument("--port", type=str, default="/dev/ttyACM0", help="Serial port for Roboruka (default: /dev/ttyACM0)")
args = argparser.parse_args()
port = args.port or "/dev/ttyACM0"

ruka = roboruka(port=port)
ds = dualsense_controller.DualSenseController()

clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
map_ = lambda x, in_min, in_max, out_min, out_max: (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

yaw = 0
pitch = 0
pitch_1 = -90
pitch_2 = 0
pitch_3 = 0
roll = 0
grip = 0

yaw_speed = - 0.15
pitch_1_speed = -0.15
pitch_speed = 0.3
roll_speed = 0.7
grip_speed = 1

yaw_delta = 0
pitch_delta = 0
roll_delta = 0
pitch_1_delta = 0
grip_delta = 0

def on_left_stick_x_changed(value):
    global yaw_delta
    yaw_delta = value * yaw_speed

def on_left_stick_y_changed(value):
    global pitch_delta
    pitch_delta = value * pitch_speed

def on_right_stick_x_changed(value):
    global roll_delta
    roll_delta = value * roll_speed

def on_right_stick_y_changed(value):
    global pitch_1_delta
    pitch_1_delta = value * pitch_1_speed

def on_r2_changed(value):
    global grip_delta
    grip_delta = value * grip_speed

ds.left_stick_x.on_change(on_left_stick_x_changed)
ds.left_stick_y.on_change(on_left_stick_y_changed)
ds.right_stick_x.on_change(on_right_stick_x_changed)
ds.right_stick_y.on_change(on_right_stick_y_changed)
ds.right_trigger.on_change(on_r2_changed)

is_running = True

ds.activate()

while is_running:
    # apply deltas and clamp positions
    yaw += yaw_delta
    yaw = clamp(yaw, -90, 90)

    pitch += pitch_delta
    pitch = clamp(pitch, -180, 180)
    pitch_2 = pitch / 2
    pitch_3 = pitch / 2

    pitch_1 += pitch_1_delta
    pitch_1 = clamp(pitch_1, -90, 90)

    roll += roll_delta
    roll = clamp(roll, -90, 90)

    grip = grip_delta
    grip = clamp(grip, 0, 1)

    ruka.send_command(f"S1:{int((yaw + 90) / 180 * 1024):04}\n")
    ruka.send_command(f"S2:{int((pitch_1 + 90) / 180 * 1024):04}\n")
    ruka.send_command(f"S3:{int((pitch_2 + 90) / 180 * 1024):04}\n")
    ruka.send_command(f"S4:{int((pitch_3 + 90) / 180 * 1024):04}\n")
    ruka.send_command(f"S5:{int((roll + 90) / 180 * 1024):04}\n")
    ruka.send_command(f"S6:{int(map_(grip, 0,1,1024,600)):04}\n")
    sleep(0.001)


ds.deactivate()
