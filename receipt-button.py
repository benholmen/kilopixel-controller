#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests",
#   "Pillow",
#   "python-escpos",
#   "pyserial",
#   "pigpio",
# ]
# ///
#
# Wiring:
#   Button: GPIO BUTTON_GPIO → button → GND  (internal pull-up enabled)
#   LED:    GPIO LED_GPIO → 220Ω resistor → LED+ → LED− → GND

import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import pigpio
import requests
from PIL import Image
from escpos.printer import Serial

BUTTON_GPIO = 17  # BCM pin; wired button-to-GND
LED_GPIO = 27  # BCM pin; wired via resistor to LED anode

SERIAL_PORT = "/dev/ttyUSB0"
BAUD = 115200
MAX_WIDTH = 512
OPTIMAL_HEIGHT = 400

API_URL = "https://kilopx.com/api/1/health"
LOG_FILE = Path.home() / "receipts.log"

GLITCH_FILTER_US = 50_000  # pigpio drops transitions shorter than this (µs)
COOLDOWN_S = 5.0  # ignore re-presses within this window

PIXEL_FILL = {
    "X": 0,  # on          → solid black
    "x": 80,  # pending on  → dark gray
    "o": 175,  # pending off → light gray
    "O": 240,  # off         → near white
}
DEFAULT_FILL = 128


def render_pixel_grid(state):
    rows = len(state)
    cols = max(len(row) for row in state) if state else 40
    native = Image.new("L", (cols, rows), 255)
    for r, row in enumerate(state):
        for c, pixel in enumerate(row):
            native.putpixel((c, r), PIXEL_FILL.get(pixel, DEFAULT_FILL))
    out_h = MAX_WIDTH * rows // cols
    return native.resize((MAX_WIDTH, out_h), Image.Resampling.NEAREST)


def print_image_chunks(p, img):
    img_1bit = img.convert("1")
    h = img.size[1]
    for y in range(0, h, OPTIMAL_HEIGHT):
        box = (0, y, MAX_WIDTH, min(y + OPTIMAL_HEIGHT, h))
        p.image(img_1bit.crop(box), impl="graphics", center=False)


def print_receipt():
    resp = requests.get(API_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    state = data.get("state", [])
    mode = data.get("mode", "Unknown")
    pending = data.get("pending_pixel_count", 0)
    changed_1h = data.get("pixels_changed_last_hour_formatted", "0")
    changed_24h = data.get("pixels_changed_last_day_formatted", "0")
    total = data.get("pixel_change_count_formatted", "0")

    p = Serial(devfile=SERIAL_PORT, baudrate=BAUD, dsrdtr=True)
    p.hw("init")

    if state:
        grid_img = render_pixel_grid(state)
        print_image_chunks(p, grid_img)

    now = datetime.now()
    p.text("\n\n")
    p.text(f"Status as of:    {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
    p.text(f"Mode:            {mode}\n")
    p.text(f"Pending pixels:  {pending:,}\n")
    p.text(f"Changed 1h:      {changed_1h}\n")
    p.text(f"Changed 24h:     {changed_24h}\n")
    p.text(f"Total changes:   {total}\n")
    p.cut()
    p.close()

    with open(LOG_FILE, "a") as f:
        f.write(now.isoformat() + "\n")

    print(f"[{now}] Receipt printed.")


class ButtonHandler:
    def __init__(self, pi):
        self.pi = pi
        self._last_press = 0.0
        self._busy = False

        pi.set_mode(BUTTON_GPIO, pigpio.INPUT)
        pi.set_pull_up_down(BUTTON_GPIO, pigpio.PUD_UP)
        pi.set_glitch_filter(BUTTON_GPIO, GLITCH_FILTER_US)

        pi.set_mode(LED_GPIO, pigpio.OUTPUT)
        pi.write(LED_GPIO, 0)

        self._cb = pi.callback(BUTTON_GPIO, pigpio.FALLING_EDGE, self._on_press)

    def _on_press(self, gpio, level, tick):
        now = time.monotonic()
        if self._busy or (now - self._last_press) < COOLDOWN_S:
            return
        self._last_press = now
        self._busy = True
        self.pi.write(LED_GPIO, 1)
        try:
            print_receipt()
        except Exception as e:
            print(f"[ERROR] Receipt failed: {e}", file=sys.stderr)
        finally:
            self.pi.write(LED_GPIO, 0)
            self._busy = False

    def cancel(self):
        self._cb.cancel()
        self.pi.write(LED_GPIO, 0)


def main():
    pi = pigpio.pi()
    if not pi.connected:
        print("Cannot connect to pigpiod — run: sudo pigpiod", file=sys.stderr)
        sys.exit(1)

    handler = ButtonHandler(pi)

    def shutdown(sig, frame):
        print("\nShutting down.")
        handler.cancel()
        pi.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"Ready. Waiting for button press on GPIO {BUTTON_GPIO}.")
    signal.pause()


if __name__ == "__main__":
    main()
