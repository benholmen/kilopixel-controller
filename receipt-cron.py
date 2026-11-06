#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests",
#   "Pillow",
#   "python-escpos",
#   "pyserial",
# ]
# ///

from datetime import datetime

import requests
from PIL import Image
from escpos.printer import Serial

SERIAL_PORT = "/dev/printer"
BAUD = 115200
MAX_WIDTH = 512
OPTIMAL_HEIGHT = 400

API_URL = "https://kilopx.com/api/1/health"

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


def main():
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
    p.profile.profile_data["media"]["width"]["pixels"] = MAX_WIDTH
    p.hw("init")

    p.set(align="center", bold=True, double_height=True, double_width=True)
    p.text("kilopixel\n")
    p.hw("init")
    p.set(align="center", bold=True)
    p.text("\nSHIFT - Eau Claire, WI\n\n")
    p.hw("init")

    if state:
        grid_img = render_pixel_grid(state)
        print_image_chunks(p, grid_img)

    now = datetime.now()
    p.text("\n\n")
    p.text(f"    Status as of:      {now.strftime('%Y-%m-%d %H:%M')}\n")
    p.text(f"    Mode:              {mode}\n")
    p.text(f"    Pending pixels:    {pending:,}\n")
    p.text(f"    Changed 1h:        {changed_1h}\n")
    p.text(f"    Changed 24h:       {changed_24h}\n")
    p.text(f"    Changed all time:  {total}\n\n")
    p.set(align="center")
    p.text("kilopx.com")
    p.cut()
    p.close()

    print(f"[{now}] Receipt printed.")


if __name__ == "__main__":
    main()
