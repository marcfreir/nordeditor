# # generate_icon.py — run once to create the icon
# from PIL import Image, ImageDraw

# img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
# draw = ImageDraw.Draw(img)
# # Dark background circle
# draw.ellipse([8, 8, 248, 248], fill="#1e1f2b", outline="#89b4fa", width=8)
# # Letter "N"
# draw.rectangle([60, 60, 90, 196], fill="#89b4fa")
# draw.rectangle([166, 60, 196, 196], fill="#89b4fa")
# draw.polygon([(60, 60), (90, 60), (196, 196), (166, 196)], fill="#cba6f7")
# img.save("assets/icon.png")
# img.save("assets/icon.ico")


# ==========================

#!/usr/bin/env python3
"""
generate_icon.py \u2014 Run this once to create assets/icon.png and assets/icon.ico
Requires Pillow:  pip install Pillow
"""

import os
from PIL import Image, ImageDraw, ImageFont

# \u2500\u2500 Colours (match NordEditor's palette) \u2500\u2500
BG      = "#1e1f2b"
BORDER  = "#89b4fa"   # ACCENT blue
LETTER  = "#cdd6f4"   # TEXT_FG
ACCENT2 = "#cba6f7"   # purple diagonal stroke

SIZE = 256


def make_icon(size=SIZE) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad   = size // 16
    r     = size // 10          # corner radius

    # Rounded-rectangle background
    draw.rounded_rectangle([pad, pad, size - pad, size - pad],
                           radius=r, fill=BG, outline=BORDER,
                           width=max(2, size // 32))

    # Draw a stylised "N"
    lw  = max(3, size // 20)    # stroke width
    m   = size // 5             # horizontal margin
    t   = size // 4             # top of letter
    b   = size * 3 // 4         # bottom of letter

    # Left vertical bar
    draw.rectangle([m, t, m + lw, b], fill=LETTER)
    # Right vertical bar
    draw.rectangle([size - m - lw, t, size - m, b], fill=LETTER)
    # Diagonal \u2014 drawn as a thick line
    draw.line([(m + lw // 2, t), (size - m - lw // 2, b)],
              fill=ACCENT2, width=lw)

    return img


def main():
    os.makedirs("assets", exist_ok=True)

    icon = make_icon(SIZE)
    icon.save("assets/icon.png")
    print("Saved assets/icon.png")

    # .ico needs multiple sizes for Windows
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    frames = [make_icon(s[0]) for s in sizes]
    frames[0].save(
        "assets/icon.ico",
        format="ICO",
        sizes=sizes,
        append_images=frames[1:],
    )
    print("Saved assets/icon.ico")
    print("\nDone! Run nordeditor.py and you should see the icon.")


if __name__ == "__main__":
    main()