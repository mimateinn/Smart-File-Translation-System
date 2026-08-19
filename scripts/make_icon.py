"""Draw the pictorial app icon: documents + globe + arrows. No letters."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "icon.png"
SIZE = 256


def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def main() -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Rounded white card
    draw.rounded_rectangle((8, 8, 248, 248), radius=48, fill=(255, 255, 255, 255))
    teal = (20, 184, 166)
    blue = (37, 99, 235)

    def stroke(xy, width=10):
        draw.line(xy, fill=_lerp(teal, blue, 0.45), width=width, joint="curve")

    # Back document
    draw.rounded_rectangle((118, 52, 198, 196), radius=10, outline=_lerp(teal, blue, 0.7), width=8)
    # Front document
    draw.rounded_rectangle((58, 64, 158, 210), radius=10, outline=teal, width=8)
    # Globe
    cx, cy, r = 108, 132, 28
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=blue, width=6)
    draw.arc((cx - 14, cy - r, cx + 14, cy + r), 0, 360, fill=blue, width=5)
    draw.line((cx - r + 2, cy, cx + r - 2, cy), fill=blue, width=5)
    draw.arc((cx - r, cy - 12, cx + r, cy + 12), 0, 360, fill=blue, width=5)
    # Curved arrows around the globe
    for start, end, flip in ((210, 330, False), (30, 150, True)):
        box = (cx - 46, cy - 46, cx + 46, cy + 46)
        draw.arc(box, start, end, fill=teal, width=7)
    # Arrow heads
    draw.polygon([(148, 100), (160, 96), (152, 112)], fill=teal)
    draw.polygon([(68, 164), (56, 168), (64, 152)], fill=blue)
    img = img.convert("RGB")
    img.save(OUT, "PNG")
    print(OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
