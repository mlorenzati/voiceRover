#include <stdio.h>

#include "pico/stdlib.h"
#include "hardware/pwm.h"

#define MIC_SETUP_PDM     1
#define MIC_SETUP_ANALOG  2

extern "C" {
#if MIC_SETUP == MIC_SETUP_PDM
    #include "pico/pdm_microphone.h"
#elif MIC_SETUP == MIC_SETUP_ANALOG 
    #include "pico/analog_microphone.h"
#endif
}

#include "tflite_model.h"
#include "dsp_pipeline.h"
#include "ml_model.h"

// constants
#define SAMPLE_RATE                 8000
#define FFT_SIZE                    256
#define HOP_SIZE                    80
#define N_MFCC                      32
#define SPECTROGRAM_TIME_FRAMES     80

#define SPECTRUM_SHIFT              ((FFT_SIZE + HOP_SIZE - 1) / HOP_SIZE)
// How many new samples capture per callback
#define MIC_BLOCK_SAMPLES           (HOP_SIZE * SPECTRUM_SHIFT)
// How many samples needed to compute SPECTRUM_SHIFT MFCC frames
#define FFT_FRAME_BUFFER_SAMPLES    (FFT_SIZE + (SPECTRUM_SHIFT - 1) * HOP_SIZE)
#define N_BINS                      ((FFT_SIZE / 2) + 1)

#define INPUT_SHIFT       0
#define BIAS_VOLTAGE      1.65
#define TENSOR_ARENA_SIZE 128 * 1024

// microphone configuration
#if MIC_SETUP == MIC_SETUP_PDM
const struct pdm_microphone_config pdm_config = {
    // GPIO pin for the PDM DAT signal
    .gpio_data = 2,

    // GPIO pin for the PDM CLK signal
    .gpio_clk = 3,

    // PIO instance to use
    .pio = pio0,

    // PIO State Machine instance to use
    .pio_sm = 0,

    // sample rate in Hz
    .sample_rate = SAMPLE_RATE,

    // number of samples to buffer
    .sample_buffer_size = MIC_BLOCK_SAMPLES,
};
#elif MIC_SETUP == MIC_SETUP_ANALOG
#define MIC_GPIO_ADC 26
#define MIC_GPIO_GAIN 2
const struct analog_microphone_config analog_config {
    .gpio = MIC_GPIO_ADC,
    .bias_voltage = BIAS_VOLTAGE,
    .sample_rate = SAMPLE_RATE,
    .sample_buffer_size = MIC_BLOCK_SAMPLES
};
#else 
#error "MIC_SETUP not defined!"
#endif

q15_t capture_buffer_q15[MIC_BLOCK_SAMPLES];
q15_t input_q15[FFT_FRAME_BUFFER_SAMPLES];
DSPPipeline dsp_pipeline(FFT_SIZE, HOP_SIZE, N_MFCC, SPECTROGRAM_TIME_FRAMES);

//static uint8_t tensor_arena[TENSOR_ARENA_SIZE] __attribute__((aligned(16)));
MLModel ml_model(tflite_model, TENSOR_ARENA_SIZE);
volatile int new_samples_captured = 0;
int8_t* scaled_spectrum = nullptr;
const size_t tail_samples = FFT_SIZE - HOP_SIZE;

int32_t spectogram_divider;
float spectrogram_zero_point;

void on_mic_samples_ready();

int main( void )
{
    // initialize stdio
    stdio_init_all();

    printf("hello pico Voice Rover!\n");

    if (!ml_model.init()) {
        printf("Failed to initialize ML model!\n");
        while (1) { tight_loop_contents(); }
    }

    if (!dsp_pipeline.init()) {
        printf("Failed to initialize DSP Pipeline!\n");
        while (1) { tight_loop_contents(); }
    }

    scaled_spectrum = (int8_t*)ml_model.input_data();
    spectogram_divider = 64 * ml_model.input_scale(); 
    spectrogram_zero_point = ml_model.input_zero_point();

#if MIC_SETUP == MIC_SETUP_PDM
    // initialize the PDM microphone
    if (pdm_microphone_init(&pdm_config) < 0) {
        printf("PDM microphone initialization failed!\n");
        while (1) { tight_loop_contents(); }
    }

    // set callback that is called when all the samples in the library
    // internal sample buffer are ready for reading
    pdm_microphone_set_samples_ready_handler(on_mic_samples_ready);
    
    // start capturing data from the PDM microphone
    if (pdm_microphone_start() < 0) {
        printf("PDM microphone start failed!\n");
        while (1) { tight_loop_contents(); }
    }
#elif MIC_SETUP == MIC_SETUP_ANALOG
    // initialize the PDM microphone
    if (analog_microphone_init(&analog_config) < 0) {
        printf("Analog microphone initialization failed!\n");
        while (1) { tight_loop_contents(); }
    }
    // Set mic gain
    gpio_init(MIC_GPIO_GAIN);
    gpio_set_dir(MIC_GPIO_GAIN, GPIO_OUT);
    gpio_put(MIC_GPIO_GAIN, 1);

    // set callback that is called when all the samples in the library
    // internal sample buffer are ready for reading
    analog_microphone_set_samples_ready_handler(on_mic_samples_ready);
    
    // start capturing data from the PDM microphone
    if (analog_microphone_start() < 0) {
        printf("PDM microphone start failed!\n");
        while (1) { tight_loop_contents(); }
    }
#endif

    while (1) {
        // wait for new samples
        while (new_samples_captured == 0) {
            tight_loop_contents();
        }
        new_samples_captured = 0;

        dsp_pipeline.shift_spectrogram(scaled_spectrum, SPECTRUM_SHIFT);

        // move input buffer values over by MIC_BLOCK_SAMPLES samples
        memmove(input_q15, &input_q15[FFT_FRAME_BUFFER_SAMPLES - tail_samples], tail_samples * sizeof(q15_t));

        // copy new samples to end of the input buffer with a bit shift of INPUT_SHIFT
        arm_shift_q15(capture_buffer_q15, INPUT_SHIFT, input_q15 + tail_samples, MIC_BLOCK_SAMPLES);
    
        for (int i = 0; i < SPECTRUM_SHIFT; i++) {
            const int spect_frame_index = SPECTROGRAM_TIME_FRAMES - SPECTRUM_SHIFT + i;
            int8_t* spect_ptr = scaled_spectrum + (N_MFCC * spect_frame_index);
            const int start_sample = i * HOP_SIZE;
            
            dsp_pipeline.calculate_mfcc(input_q15 + start_sample, spect_ptr, spectogram_divider, spectrogram_zero_point);
        }

        float prediction = ml_model.predict();

        if (prediction >= 0.5) {
          printf("\t🔥 🔔\tdetected!\t(prediction = %f)\n\n", prediction);
        } else {
          printf("\t🔕\tNOT detected\t(prediction = %f)\n\n", prediction);
        }
    }

    return 0;
}

// callback from library when all the samples in the library
// internal sample buffer are ready for reading 
// read in the new samples
#if MIC_SETUP == MIC_SETUP_PDM
void on_mic_samples_ready() {
    new_samples_captured = pdm_microphone_read(capture_buffer_q15, MIC_BLOCK_SAMPLES);
}
#elif MIC_SETUP == MIC_SETUP_ANALOG
void on_mic_samples_ready() {
    new_samples_captured = analog_microphone_read(capture_buffer_q15, MIC_BLOCK_SAMPLES);
}
#endif