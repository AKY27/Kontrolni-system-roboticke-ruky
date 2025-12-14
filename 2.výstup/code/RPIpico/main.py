from machine import Pin, PWM
from utime import sleep, ticks_ms

class robot_arm:
    def __init__(self, yaw_pin, pitch_1_pin, pitch_2_pin, pitch_3_pin, roll_pin, grip_pin, pitch_mode="connected"):
        self.yaw =     PWM(Pin(yaw_pin),     freq=50)
        self.pitch_1 = PWM(Pin(pitch_1_pin), freq=50)
        self.pitch_2 = PWM(Pin(pitch_2_pin), freq=50)
        self.pitch_3 = PWM(Pin(pitch_3_pin), freq=50)
        self.roll =    PWM(Pin(roll_pin),    freq=50)
        self.grip =    PWM(Pin(grip_pin),    freq=50)

        self.max_duty = 7864
        self.min_duty = 1802

        self.clam = lambda value, min_value, max_value: max(min(value, max_value), min_value)
        self.floor_lerp = lambda a,b,t:  int((1 - t) * a + t * b)
        self.map_ = lambda x, in_min, in_max, out_min, out_max: (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

        self.pitch_mode = pitch_mode # "connected" or "independent"
        self.connected_pitch = (pitch_mode == "connected")

    def map_pitch(self, pitch, pitch_offset, pitch_distance):
        pitch_offset_ = (90 - abs(pitch / 3)) * pitch_offset
        pitch_distance_ = self.map_(pitch_distance, -1, 1, 90 + pitch / 3, -90 + pitch / 3) 
        #ještě je potřeba vypočítat správné limity

        return pitch_distance_, pitch_offset_


    def apply_rotation(self, rotation):
        if self.connected_pitch: #použít pitch, pitch_offset a pitch_distance 
            yaw, pitch, pitch_offset, pitch_distance, roll, time = rotation 
            
            """
            yaw: -90 to 90; otočení celé ruky vlevo/vpravo
            pitch: 0 to 90; celkové naklonění ruky dopředu/dozadu
            pitch_offset: -1 to 1; úprava naklonění prvního a posledního servo motoru náklonu dopředu/dozadu
            pitch_distance: 0 to 1; úprava naklonění středního servo motoru náklonu dopředu/dozadu
            roll: -90 to 90; natočení zápěstí
            time: čas na přesun do pozice v milisekundách
            """

            pitch_distance_, pitch_offset_ = self.map_pitch(pitch, pitch_offset, pitch_distance)

            pitch_1 = pitch / 3 - pitch_distance_ / 2 + (pitch_offset_)
            pitch_2 = pitch / 3 + pitch_distance_
            pitch_3 = pitch / 3 - pitch_distance_ / 2 - (pitch_offset_)

        else: #použít pitch_1, pitch_2, pitch_3
            yaw, pitch_1, pitch_2, pitch_3, roll, time = rotation
            """
            yaw: -90 to 90; otočení celé ruky vlevo/vpravo
            pitch_1: -90 to 90; naklonění prvního servo motoru náklonu dopředu/dozadu
            pitch_2: -90 to 90; naklonění středního servo motoru náklonu dopředu/dozadu
            pitch_3: -90 to 90; naklonění posledního servo motoru náklonu dopředu/dozadu
            roll: -90 to 90; natočení zápěstí
            time: čas na přesun do pozice v milisekundách
            """

        yaw_duty =     int(self.map_(yaw,     -90, 90, self.min_duty, self.max_duty))
        pitch_1_duty = int(self.map_(pitch_1, -90, 90, self.min_duty, self.max_duty))
        pitch_2_duty = int(self.map_(pitch_2, -90, 90, self.min_duty, self.max_duty))
        pitch_3_duty = int(self.map_(pitch_3, -90, 90, self.min_duty, self.max_duty))
        roll_duty =    int(self.map_(roll,    -90, 90, self.min_duty, self.max_duty))


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
        self.grip.duty_u16(self.min_duty)
    
def main():
    arm = robot_arm(
        yaw_pin=16,
        pitch_1_pin=17,
        pitch_2_pin=18,
        pitch_3_pin=19,
        roll_pin=20,
        grip_pin=21,
        pitch_mode="connected"
    )

    # příklad použití
    arm.apply_rotation((30, 90, 0.5, -1, 15, 2000))
    arm.close_grip()
    sleep(1)
    arm.apply_rotation((-30, 45, -0.5, 0, -15, 2000))
    arm.open_grip()

main()