#!/usr/bin/env python3
import argparse
import serial
import struct
import time
import numpy as np
import matplotlib.pyplot as plt

# CONFIG — must match Pico
MAGIC = 0xA55A             # your CRLF magic
HEADER_SIZE = 4            # uint16_t magic + uint16_t size
N_MFCC = 32
TIME_FRAMES = 80
EXPECTED_PAYLOAD = N_MFCC * TIME_FRAMES  # 2560

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--port', '-p', required=True)
    p.add_argument('--baud', '-b', type=int, default=115200)
    args = p.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=0.2)
    print(f"Opened {args.port} @ {args.baud}")

    # matplotlib setup
    plt.ion()
    fig, ax = plt.subplots()
    img = ax.imshow(np.zeros((N_MFCC, TIME_FRAMES)),
                    origin='lower', aspect='auto', interpolation='nearest')
    plt.colorbar(img)
    ax.set_title("Live spectrogram")
    ax.set_xlabel("Time frames")
    ax.set_ylabel("Bins")

    rx = bytearray()
    frames = 0
    last_update = time.time()

    try:
        while True:
            # read available bytes (non-blocking-ish, chunked)
            chunk = ser.read(512)
            if chunk:
                rx.extend(chunk)

            # parse any full frames available in rx buffer
            while True:
                if len(rx) < HEADER_SIZE:
                    break  # need more bytes

                # peek header
                magic, size = struct.unpack_from('<HH', rx, 0)

                if magic != MAGIC:
                    # not a valid header — drop first byte and keep trying
                    # (this incrementally finds sync)
                    del rx[0]
                    continue

                # valid magic; do we have full payload?
                if len(rx) < HEADER_SIZE + EXPECTED_PAYLOAD:
                    break  # wait for more bytes

                payload = bytes(rx[HEADER_SIZE:HEADER_SIZE + EXPECTED_PAYLOAD])
                print("payload", payload)
                
                # consume the parsed frame
                del rx[:HEADER_SIZE + EXPECTED_PAYLOAD]

                # We have a valid frame -> visualize
                frames += 1
                # payload is int8 sequence; reshape to (TIME_FRAMES, N_MFCC) then transpose
                spec = np.frombuffer(payload, dtype=np.int8)
                try:
                    spec = spec.reshape(TIME_FRAMES, N_MFCC).T  # (N_MFCC, TIME_FRAMES)
                except Exception as e:
                    print("Reshape error:", e)
                    continue

                # update image
                img.set_data(spec)
                img.set_clim(vmin=-128, vmax=127)

                # throttle redraw to ~20-30 FPS
                now = time.time()
                if now - last_update > 0.03:
                    plt.pause(0.001)
                    last_update = now

            # small sleep so this loop doesn't spin too hot
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("Exiting")
    finally:
        ser.close()

if __name__ == '__main__':
    main()