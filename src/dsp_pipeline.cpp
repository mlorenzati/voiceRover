/*
 * Copyright (c) 2021 Arm Limited and Contributors. All rights reserved.
 *
 * SPDX-License-Identifier: Apache-2.0
 * 
 */

#include "dsp_pipeline.h"

DSPPipeline::DSPPipeline(int fft_size, int hop_size, int n_mfcc, int time_frames) :
    _fft_size(fft_size), _hop_size(hop_size), _n_mfcc(n_mfcc), _time_frames(time_frames),
    _hanning_window(NULL), _windowed_input(NULL), _fft_q15(NULL), _fft_mag_q15(NULL) {
}

DSPPipeline::~DSPPipeline()  {
    if (_hanning_window) { delete [] _hanning_window; _hanning_window = NULL; }
    if (_windowed_input) { delete [] _windowed_input; _windowed_input = NULL; }
    if (_fft_q15) { delete [] _fft_q15; _fft_q15 = NULL; }
    if (_fft_mag_q15) { delete [] _fft_mag_q15; _fft_mag_q15 = NULL; }
}

bool DSPPipeline::init()
{
    // sanity checks
    const int fft_bins = (_fft_size / 2) + 1;
    if (_fft_size <= 0 || _hop_size <= 0 || _n_mfcc <= 0 || _time_frames <= 0) {
        return false;
    }
    if (_n_mfcc > fft_bins) {
        // can't output more MFCCs than FFT bins (temporary check)
        return false;
    }

    // allocate buffers
    _hanning_window = new int16_t[_fft_size];
    _windowed_input = new int16_t[_fft_size];
    _fft_q15 = new int16_t[_fft_size * 2];
    _fft_mag_q15 = new int16_t[fft_bins];

    if (!_hanning_window || !_windowed_input || !_fft_q15 || !_fft_mag_q15) {
        return false;
    }

    // build hanning window in q15
    for (int i = 0; i < _fft_size; ++i) {
        float32_t f = 0.5f * (1.0f - arm_cos_f32(2.0f * PI * i / _fft_size));
        arm_float_to_q15(&f, &_hanning_window[i], 1);
    }

    // init RFFT (forward, bit reversal enabled)
    if (arm_rfft_init_q15(&_S_q15, _fft_size, 0, 1) != ARM_MATH_SUCCESS) {
        return false;
    }

    return true;
}

void DSPPipeline::calculate_spectrum(const int16_t* input, int8_t* output, int32_t spectogram_divider, float spectrogram_zero_point) {
    const int fft_bins = (_fft_size / 2) + 1;

    // Apply window: element-wise multiply (q15)
    arm_mult_q15(_hanning_window, input, _windowed_input, _fft_size);

    // Perform RFFT (q15)
    arm_rfft_q15(&_S_q15, _windowed_input, _fft_q15);

    // Compute magnitude (q15)
    arm_cmplx_mag_q15(_fft_q15, _fft_mag_q15, fft_bins);

    // SAFETY: write only up to _n_mfcc values into output buffer to avoid overflow
    // This preserves previous behavior (raw FFT) but prevents tensor corruption.
    const int write_bins = (_n_mfcc < fft_bins) ? _n_mfcc : fft_bins;

    // Use 32-bit intermediate to divide and add zero_point safely
    for (int j = 0; j < write_bins; ++j) {
        // fft_mag_q15[j] is q15 (signed 16-bit)
        int32_t mag_q15 = (int32_t)_fft_mag_q15[j];

        // integer divide (preserve sign) - use spectogram_divider > 0
        int32_t scaled = (spectogram_divider != 0) ? (mag_q15 / spectogram_divider) : mag_q15;

        // add zero point (float -> round to nearest int)
        int32_t with_zero = scaled + (int32_t)roundf(spectrogram_zero_point);

        // saturate to int8 range
        int32_t sat = __SSAT(with_zero, 8); // clamps to [-128,127]
        output[j] = (int8_t)sat;
    }

    // If output buffer expects more bins than we wrote, zero the remainder to avoid stale data
    for (int j = write_bins; j < _n_mfcc; ++j) {
        output[j] = 0;
    }
}

void DSPPipeline::calculate_mfcc(const int16_t* input, int8_t* output, int32_t mfcc_divider, float mfcc_zero_point) {
    //TODO
}

void DSPPipeline::shift_spectrogram(int8_t* spectrogram, int shift_amount) {
       if (shift_amount <= 0) return;
    if (shift_amount >= _time_frames) {
        // clear all frames
        memset(spectrogram, 0, _n_mfcc * _time_frames * sizeof(int8_t));
        return;
    }

    const int frames_to_keep = _time_frames - shift_amount;
    memmove(
        spectrogram,
        spectrogram + (_n_mfcc * shift_amount),
        _n_mfcc * frames_to_keep * sizeof(int8_t)
    );

    // clear the newly freed tail frames (optional but safer)
    memset(
        spectrogram + (_n_mfcc * frames_to_keep),
        0,
        _n_mfcc * shift_amount * sizeof(int8_t)
    );
}
