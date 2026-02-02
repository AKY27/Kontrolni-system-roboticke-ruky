#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"
#include "pico/cyw43_arch.h"

char buffer[256];

uint Pins[] = {16,17,18,19,20,21}; 

int calibration[6][2] = {
    {500, 2500}, // Servo 1 min/max
    {500, 2500}, // Servo 2 min/max
    {500, 2500}, // Servo 3 min/max
    {500, 2500}, // Servo 4 min/max
    {500, 2500}, // Servo 5 min/max
    {500, 2500}  // Servo 6 min/max
};

const float default_angles[6] = {0.0, -90.0, 0.0, 0.0, 0.0, 30.0};

float angles[6] = {0.0, -90.0, 0.0, 0.0, 0.0, 30.0};

uint slice_chans[6][2];

float map(float x, float in_min, float in_max, float out_min, float out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

void servo_init(int servo_index, int angle) {
    gpio_init(Pins[servo_index]);
    gpio_set_function(Pins[servo_index], GPIO_FUNC_PWM);
    slice_chans[servo_index][0] = pwm_gpio_to_slice_num(Pins[servo_index]);
    slice_chans[servo_index][1] = pwm_gpio_to_channel(Pins[servo_index]);
    pwm_set_enabled(slice_chans[servo_index][0], true);
    pwm_set_clkdiv(slice_chans[servo_index][0], 150.0f); // 1 MHz clock for 50Hz PWM
    pwm_set_wrap(slice_chans[servo_index][1], 20000 - 1); // 20 ms period

    int min_pulse = calibration[servo_index][0];
    int max_pulse = calibration[servo_index][1];
    int pulse_width = (int)map(angle, -90.0, 90.0, (float)min_pulse, (float)max_pulse);
    pwm_set_chan_level(slice_chans[servo_index][0], slice_chans[servo_index][1], pulse_width);
}

void move_servo(int servo_index, int angle) {
    int min_pulse = calibration[servo_index][0];
    int max_pulse = calibration[servo_index][1];
    int pulse_width = (int)map(angle, -90.0, 90.0, (float)min_pulse, (float)max_pulse);
    pwm_set_chan_level(slice_chans[servo_index][0], slice_chans[servo_index][1], pulse_width);
}


void process_input(const char* input) {
    printf("Received: %s\n", input);
    // Expected format: "S1:1024\n"
    /*if (input.leng != 8){
        return;
    }*/
    int servo_id = atoi(&input[1]) - 1;
    float angle = map((float)atoi(&input[3]), 0.0, 1024.0, -90.0, 90.0);
    if (servo_id < 0 || servo_id > 5) {
        printf("Invalid servo ID: %d\n", servo_id + 1);
        return; // Invalid servo ID
    }
    if (angle < -90.0 || angle > 90.0) {
        printf("Invalid angle: %f\n", angle);
        return; // Invalid angle    
    }
    angles[servo_id] = angle;
}


int main() {
    bool done = false;
    stdio_init_all();
    if (cyw43_arch_init()) {
        printf("Wi-Fi init failed\n");
        return -1;
    }
    
    for (int i = 0; i < 6; i++)
    {
        servo_init(i, default_angles[i]);
    }
    while (!done) {
        gets(buffer);
        if (strcmp(buffer, "stop\n") == 0){
            for (int i = 0; i < 6; i++)
            {
                move_servo(i, default_angles[i]);
            }     
            done = true;
            continue;
        }
        process_input(buffer);
        for (int i = 0; i < 6; i++) {
            move_servo(i, angles[i]);
        }
    }
}
