import machine
import utime
import struct

AUDIO_PIN = 8
PWM_CARRIER = 20000
BOOT_DELAY_MS = 3000     # time to interrupt after reset
LOOP_PLAYBACK = False     # True = loop sound
RANGE = int(256)

# ========== WAV LOADER (reads all audio to memory) ==========
def wav_open_read_all(filename):
    f = open(filename, "rb")

    if f.read(4) != b'RIFF': raise Exception("Not RIFF")
    f.read(4)
    if f.read(4) != b'WAVE': raise Exception("Not WAVE")

    if f.read(4) != b'fmt ': raise Exception("fmt missing")
    fmt_size = struct.unpack("<I", f.read(4))[0]
    fmt = f.read(fmt_size)
    audio_format, ch, sr, br, ba, bits = struct.unpack("<HHIIHH", fmt[:16])

    if audio_format != 1: raise Exception("Not PCM")
    if ch != 1: raise Exception("Mono only")
    if bits != 8: raise Exception("Must be 8-bit PCM")

    while True:
        hdr = f.read(4)
        if hdr == b'data':
            break
        if not hdr:
            raise Exception("data chunk missing")
        skip = struct.unpack("<I", f.read(4))[0]
        f.seek(skip, 1)

    size = struct.unpack("<I", f.read(4))[0]
    pcm = f.read(size)
    f.close()
    return pcm, sr


# ========== PWM ==========
def setup_pwm(pin):
    p = machine.Pin(pin)
    pwm = machine.PWM(p)
    pwm.freq(PWM_CARRIER)
    pwm.duty_u16(32768)
    return pwm


# ========== ISR FACTORY ==========
def make_play_callback(pcm, pwm, timer, loop):
    ln = len(pcm)
    idx = 0
    stopped = False

    def cb(t):
        nonlocal idx, stopped
        try:
            if stopped:
                return

            if idx >= ln:
                if loop:
                    idx = 0
                else:
                    timer.deinit()
                    pwm.duty_u16(127 * RANGE)
                    stopped = True
                    return

            s = pcm[idx]
            pwm.duty_u16((s * RANGE))
            idx += 1

        except Exception:
            # Hard stop if ISR misbehaves
            try: timer.deinit()
            except: pass
            try: pwm.duty_u16(32768)
            except: pass
            stopped = True

    return cb


# ========== MAIN ==========
def main():
    utime.sleep_ms(BOOT_DELAY_MS)

    pcm, sr = wav_open_read_all("audio.wav")
    print("Loaded WAV:", sr, "Hz,", len(pcm), "bytes")

    pwm = setup_pwm(AUDIO_PIN)
    timer = machine.Timer()

    cb = make_play_callback(pcm, pwm, timer, LOOP_PLAYBACK)
    timer.init(freq=sr, mode=machine.Timer.PERIODIC, callback=cb)

    print("Playing. Press STOP in Thonny or Ctrl-C.")

    try:
        while True:
            utime.sleep(1)
    except KeyboardInterrupt:
        # CLEAN STOP
        print("Stopping…")
        try: timer.deinit()
        except: pass
        try: pwm.deinit()
        except: pass
        raise  # allow Thonny to regain console


# ===== run =====
try:
    main()
except Exception as e:
    print("Startup error:", e)