import sys, select
from machine import Pin, PWM
from utime import sleep, ticks_ms

class robot_arm:
    def __init__(self, yaw_pin, pitch_1_pin, pitch_2_pin, pitch_3_pin, roll_pin, grip_pin):
        self.yaw =     PWM(Pin(yaw_pin),     freq=50)
        self.pitch_1 = PWM(Pin(pitch_1_pin), freq=50)
        self.pitch_2 = PWM(Pin(pitch_2_pin), freq=50)
        self.pitch_3 = PWM(Pin(pitch_3_pin), freq=50)
        self.roll =    PWM(Pin(roll_pin),    freq=50)
        self.grip =    PWM(Pin(grip_pin),    freq=50)

        self.clam = lambda value, min_value, max_value: max(min(value, max_value), min_value)
        self.map_ = lambda x, in_min, in_max, out_min, out_max: (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

        self.max_duty = 7864
        self.min_duty = 1802
        self.neutral_duty = int(self.map_(0.5, 0, 1, self.min_duty, self.max_duty))
        self.grip_duty = int(self.map_(0.55, 0, 1, self.min_duty, self.max_duty))

        self.yaw.duty_u16(self.neutral_duty),
        self.pitch_1.duty_u16(self.min_duty),
        self.pitch_2.duty_u16(self.neutral_duty),
        self.pitch_3.duty_u16(self.neutral_duty),
        self.roll.duty_u16(self.neutral_duty)

    def apply_rotation(self, rotation):
        yaw, pitch_1, pitch_2, pitch_3, roll, time = rotation
        """
        yaw: -90 to 90; otočení celé ruky vlevo/vpravo
        pitch_1: -90 to 90; naklonění prvního servo motoru náklonu dopředu/dozadu
        pitch_2: -90 to 90; naklonění středního servo motoru náklonu dopředu/dozadu
        pitch_3: -90 to 90; naklonění posledního servo motoru náklonu dopředu/dozadu
        roll: -90 to 90; natočení zápěstí
        time: čas na přesun do pozice v milisekundách
        """

        yaw_duty =     int(self.clam(self.map_(yaw,     -90, 90, self.min_duty, self.max_duty), -90, 90))
        pitch_1_duty = int(self.clam(self.map_(pitch_1, -90, 90, self.min_duty, self.max_duty), -90, 90))
        pitch_2_duty = int(self.clam(self.map_(pitch_2, -90, 90, self.min_duty, self.max_duty), -90, 90))
        pitch_3_duty = int(self.clam(self.map_(pitch_3, -90, 90, self.min_duty, self.max_duty), -90, 90))
        roll_duty =    int(self.clam(self.map_(roll,    -90, 90, self.min_duty, self.max_duty), -90, 90))


        start_time = ticks_ms()
        start_duties = [
            self.yaw.duty_u16(),
            self.pitch_1.duty_u16(),
            self.pitch_2.duty_u16(),
            self.pitch_3.duty_u16(),
            self.roll.duty_u16()
        ]

        done = False
        while not done:
            for i, servo, target_duty in zip(
                range(5),
                [self.yaw, self.pitch_1, self.pitch_2, self.pitch_3, self.roll],
                [yaw_duty, pitch_1_duty, pitch_2_duty, pitch_3_duty, roll_duty]
            ):
                current_time = ticks_ms()
                elapsed_time = current_time - start_time
                if elapsed_time >= time:
                    done = True
                    servo.duty_u16(target_duty)
                else:
                    duty = int(self.map_(elapsed_time, 0, time, start_duties[i], target_duty))
                    servo.duty_u16(duty)
            sleep(0.01)
        
    def close_grip(self):
        self.grip.duty_u16(self.max_duty)
    
    def open_grip(self):
        self.grip.duty_u16(self.grip_duty)
    
    def angle_grip(self, angle):
        pass
    
    def end(self):
        self.apply_rotation((0, -90, 0, 0, 0, 2000))
        self.yaw.deinit()
        self.pitch_1.deinit()
        self.pitch_2.deinit()
        self.pitch_3.deinit()
        self.roll.deinit()
        self.grip.deinit()

def usb_read():
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.readline().strip()
    return None
    
def main():
    arm = robot_arm(
        yaw_pin=16,
        pitch_1_pin=17,
        pitch_2_pin=18,
        pitch_3_pin=19,
        roll_pin=20,
        grip_pin=21,
    )

    while True:
        msg = usb_read()
        if msg:
            try:
                msg_parts = tuple(map(int, msg.split(',')))
            except:
                print("Invalid message:", msg)
                continue
            if len(msg_parts) == 7:
                arm.apply_rotation(msg_parts[0:6])
                if msg_parts[6] == 1:
                    arm.close_grip()
                elif msg_parts[6] == 0:
                    arm.open_grip()
        sleep(0.01)


    arm.end()
main()