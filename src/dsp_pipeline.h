/*
 * Copyright (c) 2021 Arm Limited and Contributors. All rights reserved.
 *
 * SPDX-License-Identifier: Apache-2.0
 * 
 */

#ifndef _DSP_PIPELINE_H_
#define _DSP_PIPELINE_H_

#include "arm_math.h"

class DSPPipeline {
    public:
        DSPPipeline(int fft_size, int hop_size, int n_mfcc, int time_frames);
        virtual ~DSPPipeline();

        bool init();
        void calculate_spectrum(const int16_t* input, int8_t* output, int32_t spectogram_divider, float spectrogram_zero_point);
        void calculate_mfcc(const int16_t* input, int8_t* output, int32_t mfcc_divider, float mfcc_zero_point);
        void shift_spectrogram(int8_t* spectrogram, int shift_amounth);

    private:
        int _fft_size;
        int _hop_size;
        int _n_mfcc;
        int _time_frames;
        int16_t* _hanning_window;
        int16_t* _windowed_input;
        int16_t* _fft_q15; 
        int16_t* _fft_mag_q15;
        arm_rfft_instance_q15 _S_q15;
};

#endif
