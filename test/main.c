#include <stdio.h>

#include "pico/stdlib.h"
#include "hardware/pwm.h"  
#include "hardware/timer.h"
#include "pico/analog_microphone.h"

// constants
#define MIC_SAMPLE_RATE             8000
#define MIC_BLOCK_SAMPLES           512
#define MIC_BIAS_VOLTAGE            1.25
#define MIC_ADC_PIN                 26
#define MIC_GAIN_PIN                2

#define PLAYBACK_PIN                8
#define PLAYBACK_PWM_CARRIER        20000 
#define PLAYBACK_SAMPLE_RATE        8000

const struct analog_microphone_config mic_analog_config = {
    .gpio =               MIC_ADC_PIN,
    .bias_voltage =       MIC_BIAS_VOLTAGE,
    .sample_rate =        MIC_SAMPLE_RATE,
    .sample_buffer_size = MIC_BLOCK_SAMPLES
};

volatile int mic_samples_captured = 0;
int16_t      mic_buffer[MIC_BLOCK_SAMPLES];

void on_mic_samples_ready() {
    mic_samples_captured = analog_microphone_read(mic_buffer, MIC_BLOCK_SAMPLES);
}

int main(void) {
    // Initialize stdio
    stdio_init_all();

    // Wait someone to connect
    while (!stdio_usb_connected()) {
        sleep_ms(10);
    }

    printf("record_play_test starting\n");

    // initialize the PDM microphone
    printf("Analog microphone initialization\n");
    if (analog_microphone_init(&mic_analog_config) < 0) {
        printf("Analog microphone initialization failed!\n"); 
        while (1) { tight_loop_contents(); }
    }

    // Set mic gain
    gpio_init(MIC_GAIN_PIN);
    gpio_set_dir(MIC_GAIN_PIN, GPIO_OUT); // GPIO_OUT: 60/50dB, GPIO_IN: 40dB
    gpio_put(MIC_GAIN_PIN, 0); //0: 60dB, 1: 50dB

    // Set callback that is called when all the samples in the library
    // Internal sample buffer are ready for reading
    analog_microphone_set_samples_ready_handler(on_mic_samples_ready);
    
    // Start capturing data from the Analog microphone
    printf("Analog microphone starting\n");
    if (analog_microphone_start() < 0) {
        printf("Analog microphone start failed!\n");
        while (1) { tight_loop_contents(); }
    }

    int report_cnt = 0;
    while (1) {
        if (mic_samples_captured > 0) {
            int16_t peak = 0;
            int64_t acc = 0;

            for (int i = 0; i < mic_samples_captured; i++) {
                int16_t v = mic_buffer[i];

                // DC accumulator
                acc += v;

                // Peak (absolute)
                int16_t a = v < 0 ? -v : v;
                if (a > peak) peak = a;
            }
            int16_t dc_offset = (int16_t)(acc / mic_samples_captured);

            mic_samples_captured = 0;
            if (++report_cnt >= 15) {
                printf("peak: %d, offset: %d\n", peak, dc_offset);
            }
        }
    }

    return 0;
}