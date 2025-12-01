import machine
import utime
import struct
import os

# ButterWorth filter
#  https://www.meme.net.au/butterworth.html
#  https://www.daycounter.com/Filters/LC-Butterworth-Filter/LC-Butterworth-Filter-Calculator.phtml

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
ADC_PIN = 26         # GP26 / A0
GAIN_PIN = 2         # GP2 controls MAX9814 gain if tied to Gain / AR pin
SAMPLE_RATE = 8000   # Hz
RECORD_SECONDS = 2
RECORD_WAIT_SECONDS = 3
NUM_SAMPLES = SAMPLE_RATE * RECORD_SECONDS
WAV_FILE = "record.wav"
FILTER_ALPHA = 0.6

# --------------------------------------------------
# SETUP ADC + GAIN CONTROL
# --------------------------------------------------
adc = machine.ADC(ADC_PIN)

gain = machine.Pin(GAIN_PIN, machine.Pin.OUT)
gain.value(1)        # 1 = LOW gain

# --------------------------------------------------
# HELPER: Write WAV header
# --------------------------------------------------
def write_wav_header(f, sample_rate, num_samples):
    # WAV PCM unsigned 8-bit mono
    byte_rate = sample_rate * 1 * 1
    block_align = 1
    bits_per_sample = 8
    data_size = num_samples * 1

    # RIFF header
    f.write(b"RIFF")
    f.write(struct.pack("<I", 36 + data_size))
    f.write(b"WAVE")

    # fmt chunk
    f.write(b"fmt ")
    f.write(struct.pack("<I", 16))         # chunk size
    f.write(struct.pack("<HHIIHH",
                        1,                 # AudioFormat = PCM
                        1,                 # Channels = 1
                        sample_rate,
                        byte_rate,
                        block_align,
                        bits_per_sample))

    # data chunk header
    f.write(b"data")
    f.write(struct.pack("<I", data_size))

# --------------------------------------------------
# HELPER: filter audio buffer
# --------------------------------------------------
def lowpass_filter_inplace(buf, alpha):
    """
    buf   : bytearray of 8-bit PCM samples (0–255)
    alpha : float (0–1), filter strength
    """
    if not buf:
        return

    # Start from first sample
    y = buf[0]

    for i in range(1, len(buf)):
        x = buf[i]
        y = y * (1.0 - alpha) + x * alpha
        buf[i] = int(y) & 0xFF  # modify in-place


# --------------------------------------------------
# CAPTURE SAMPLES
# --------------------------------------------------
print("Recording {} seconds...".format(RECORD_WAIT_SECONDS))

utime.sleep(1)

for count in range(3):
    print("Ready in {}...".format(count + 1))
    utime.sleep(1)
    
print("Go!")


# Preallocate buffer (faster)
samples = bytearray(NUM_SAMPLES)

# Sample time control
period_us = int(1_000_000 / SAMPLE_RATE)
next_t = utime.ticks_us()

filtered_value = 0
for i in range(NUM_SAMPLES):
    # Wait until it's time for the next sample
    while utime.ticks_diff(utime.ticks_us(), next_t) < 0:
        pass
    next_t = utime.ticks_add(next_t, period_us)

    # Read ADC (0–65535), convert to 8-bit unsigned PCM
    v = adc.read_u16() # 0..65535
    pcm8 = int(v) >> 8
    samples[i] = pcm8

print("Recording done.")

lowpass_filter_inplace(samples, FILTER_ALPHA)

print("Filtering done.")

# --------------------------------------------------
# SAVE WAV FILE
# --------------------------------------------------
with open(WAV_FILE, "wb") as f:
    write_wav_header(f, SAMPLE_RATE, NUM_SAMPLES)
    f.write(samples)

print("Saved:", WAV_FILE)
print("File size:", os.stat(WAV_FILE)[6], "bytes")