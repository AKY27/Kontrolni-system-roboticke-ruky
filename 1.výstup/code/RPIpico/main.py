from machine import Pin, PWM
from utime import sleep

servo_pins = [16,17,18,19,20,21]

Servo_Pins = [Pin(pin) for pin in servo_pins]

PWMs = [PWM(pin, freq=50) for pin in Servo_Pins]

floor_lerp = lambda a,b,t:  int((1 - t) * a + t * b)

max_duty = 7864
min_duty = 1802
half_duty = int(floor_lerp(max_duty, min_duty, 0.5))

try:
    while True:
        for servo in PWMs:
            servo.duty_u16(half_duty)
        sleep(0.3)

      
except KeyboardInterrupt:
    print("Keyboard interrupt")
    # Turn off PWM 
    [servo.deinit() for servo in PWMs]