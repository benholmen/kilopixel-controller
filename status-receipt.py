# /// script
# dependencies = [
#   "requests",
#   "Pillow",
#   "python-escpos",
#   "pyserial",
# ]
# ///
import requests
from datetime import datetime
from PIL import Image, ImageDraw
from escpos.printer import Serial

PORT = "/dev/ttyUSB0"
BAUD = 115200
MAX_WIDTH = 576
OPTIMAL_HEIGHT = 48

API_URL = "https://kilopx.com/api/1/health"

# Grayscale fill per pixel state (0=black printed, 255=white unprinted)
# Mirrors the TRMNL display: O (off) is darkest, X (on) is lightest
PIXEL_FILL = {
    "O": 0,    # off        → solid black
    "o": 80,   # pending off → dark gray
    "x": 175,  # pending on  → light gray
    "X": 240,  # on          → near white
}
DEFAULT_FILL = 128  # unknown


def render_pixel_grid(state, cell_size=14):
    rows = len(state)
    cols = max(len(row) for row in state) if state else 40

    img = Image.new("L", (MAX_WIDTH, rows * cell_size), 255)
    draw = ImageDraw.Draw(img)

    x_offset = (MAX_WIDTH - cols * cell_size) // 2

    for r, row in enumerate(state):
        for c, pixel in enumerate(row):
            fill = PIXEL_FILL.get(pixel, DEFAULT_FILL)
            x0 = x_offset + c * cell_size
            y0 = r * cell_size
            x1 = x0 + cell_size - 1
            y1 = y0 + cell_size - 1
            draw.rectangle([x0, y0, x1, y1], fill=fill)

    return img


def print_image_chunks(p, img):
    # Convert with dithering to preserve the four gray levels
    img_1bit = img.convert("1")
    h = img.size[1]
    for y in range(0, h, OPTIMAL_HEIGHT):
        box = (0, y, MAX_WIDTH, min(y + OPTIMAL_HEIGHT, h))
        p.image(img_1bit.crop(box), impl="graphics")


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

    p = Serial(devfile=PORT, baudrate=BAUD, dsrdtr=True)
    p.hw("init")

    # Header
    p.set(align="center", bold=True, double_height=True, double_width=True)
    p.text("KILOPIXEL\n")
    p.set(align="center", bold=False, double_height=False, double_width=False)
    p.text(datetime.now().strftime("%Y-%m-%d  %H:%M:%S") + "\n")
    p.text("-" * 48 + "\n")

    # 40×25 pixel grid
    if state:
        grid_img = render_pixel_grid(state)
        print_image_chunks(p, grid_img)

    p.text("\n")
    p.text("-" * 48 + "\n")

    # Stats
    p.set(align="left")
    p.text(f"Mode:           {mode}\n")
    p.text(f"Pending pixels: {pending:,}\n")
    p.text(f"Changed (1h):   {changed_1h}\n")
    p.text(f"Changed (24h):  {changed_24h}\n")
    p.text(f"Total changes:  {total}\n")

    p.text("\n\n\n")
    p.cut()
    p.close()
    print("Done!")


if __name__ == "__main__":
    main()
