import serial
import math


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
        if any(not isinstance(a, (int, float)) for a in angles):
            raise ValueError("All angles must be numbers")
        if any(a < -90 or a > 90 for a in angles):
            raise ValueError("Angles must be between -90 and 90 degrees")
        self.angles = angles.copy()
        for i, val in enumerate(angles):
            mapped_val = int(self.__map(val, -90, 90, 0, 1024))
            self.send_command(f"S{i+1}:{mapped_val:04}\n")

    def close(self):
        self.send_command("stop\n")
        self.tty.close()


# ---------------------------------------------------------------------------
# IK Solver
# ---------------------------------------------------------------------------
# Arm geometry (must match Three.js visualiser):
#   Shoulder pivot at Three.js world (0, SHOULDER_HEIGHT, 0)
#   L1 = 1.05  (shoulder → elbow)
#   L2 = 1.00  (elbow → wrist)
#   Gripper offset from wrist pivot in wrist-local frame: [0.2, 0.9]
#
# User coordinate convention: X = far (+threeZ), Y = wide (+threeX), Z = tall (+threeY)
# Conversion: threeX = userY,  threeY = userZ,  threeZ = userX
#
# With total arm angle theta = pitch1 + pitch2 + pitch3 (FK applies rotZ(-theta)):
#   gripper = wrist + [0.2*cos(theta) + 0.9*sin(theta),
#                      -0.2*sin(theta) + 0.9*cos(theta)]
# Invert to get wrist from gripper:
#   wr = reach  - (0.2*cos(theta) + 0.9*sin(theta))
#   wh = height - (-0.2*sin(theta) + 0.9*cos(theta))
# Then solve 2-link IK for (wr, wh - SHOULDER_HEIGHT) with L1, L2:
#   pitch2 = PI - acos((L1^2+L2^2-d^2)/(2*L1*L2))   [elbow-up]
#   pitch1 = atan2(wrRel, whRel) - alpha              [cosine rule, elbow-up]
#   pitch3 = theta - pitch1 - pitch2

_SHOULDER_HEIGHT = 0.75
_L1 = 1.05
_L2 = 1.00


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def solve_ik(user_x: float, user_y: float, user_z: float, theta_deg: float) -> dict | None:
    """
    Solve IK for the roboruka arm.

    Parameters
    ----------
    user_x    : target X in user coords (far,  = threeZ)
    user_y    : target Y in user coords (wide, = threeX)
    user_z    : target Z in user coords (tall, = threeY)
    theta_deg : desired total arm angle p1+p2+p3 (degrees)

    Returns
    -------
    dict with keys: reachable (bool), yaw, pitch1, pitch2, pitch3 (all degrees),
    or None if the target is singular (too close to solve).
    """
    # Convert user coords → Three.js
    tx3 = user_y  # threeX
    ty3 = user_z  # threeY (height)
    tz3 = user_x  # threeZ

    theta  = math.radians(theta_deg)
    yaw_rad = math.atan2(tz3, tx3)
    reach  = math.sqrt(tx3**2 + tz3**2)

    # Wrist pivot from gripper target
    wr = reach  - (0.2 * math.cos(theta) + 0.9 * math.sin(theta))
    wh = ty3    - (-0.2 * math.sin(theta) + 0.9 * math.cos(theta))

    wr_rel = wr
    wh_rel = wh - _SHOULDER_HEIGHT
    d = math.sqrt(wr_rel**2 + wh_rel**2)

    yaw_deg = math.degrees(yaw_rad)

    if d > _L1 + _L2 + 0.001:
        p1_deg = math.degrees(math.atan2(wr_rel, wh_rel))
        return {
            'reachable': False,
            'yaw':    _clamp(yaw_deg,            -90, 90),
            'pitch1': _clamp(p1_deg,             -90, 90),
            'pitch2': 0.0,
            'pitch3': _clamp(theta_deg - p1_deg, -90, 90),
        }

    if d < abs(_L1 - _L2) - 0.001:
        return None  # singular — target too close

    cos_p2 = max(-1.0, min(1.0, (_L1**2 + _L2**2 - d**2) / (2 * _L1 * _L2)))
    pitch2  = math.pi - math.acos(cos_p2)

    cos_alpha = max(-1.0, min(1.0, (_L1**2 + d**2 - _L2**2) / (2 * _L1 * d)))
    pitch1 = math.atan2(wr_rel, wh_rel) - math.acos(cos_alpha)
    pitch3 = theta - pitch1 - pitch2

    return {
        'reachable': True,
        'yaw':    _clamp(yaw_deg,                -90, 90),
        'pitch1': _clamp(math.degrees(pitch1),   -90, 90),
        'pitch2': _clamp(math.degrees(pitch2),   -90, 90),
        'pitch3': _clamp(math.degrees(pitch3),   -90, 90),
    }