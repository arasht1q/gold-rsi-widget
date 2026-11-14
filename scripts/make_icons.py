"""Generate PWA icons for the gold RSI widget app."""
import os
from PIL import Image, ImageDraw, ImageFont

PUBLIC_DIR = "/home/z/my-project/public"
os.makedirs(PUBLIC_DIR, exist_ok=True)

def make_icon(size: int, path: str):
    """Create a square gold-themed icon with RSI gauge."""
    img = Image.new('RGBA', (size, size), (15, 23, 42, 255))  # slate-900
    draw = ImageDraw.Draw(img)

    # Background gradient (simulated with concentric circles)
    cx, cy = size // 2, size // 2
    for r in range(size, 0, -2):
        # interpolate from slate-900 to amber-500
        t = r / size
        r_col = int(15 * t + 245 * (1 - t))
        g_col = int(23 * t + 158 * (1 - t))
        b_col = int(42 * t + 11 * (1 - t))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(r_col, g_col, b_col, 255))

    # Inner dark circle for content
    inner_r = int(size * 0.36)
    draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
                 fill=(15, 23, 42, 240))

    # Draw RSI gauge bar (amber)
    bar_w = int(size * 0.42)
    bar_h = int(size * 0.08)
    bar_x = cx - bar_w // 2
    bar_y = cy + int(size * 0.18)
    # background
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                            radius=bar_h // 2, fill=(30, 41, 59, 255))
    # fill (about 60%)
    fill_w = int(bar_w * 0.6)
    draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h],
                            radius=bar_h // 2, fill=(251, 191, 36, 255))  # amber-400

    # Draw "RSI" text in center
    try:
        font_size = int(size * 0.18)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    text = "RSI"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = cx - tw // 2
    ty = cy - th // 2 - int(size * 0.05)
    draw.text((tx, ty), text, fill=(251, 191, 36, 255), font=font)  # amber-400

    # "30" subscript below
    try:
        sub_size = int(size * 0.08)
        sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", sub_size)
    except Exception:
        sub_font = ImageFont.load_default()
    sub_text = "30 · M30"
    bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
    sw = bbox[2] - bbox[0]
    sx = cx - sw // 2
    sy = cy + int(size * 0.04)
    draw.text((sx, sy), sub_text, fill=(148, 163, 184, 255), font=sub_font)  # slate-400

    img.save(path, 'PNG')
    print(f"✓ {path}  ({size}x{size})")

# Generate standard PWA icon sizes
make_icon(192, f"{PUBLIC_DIR}/icon-192.png")
make_icon(512, f"{PUBLIC_DIR}/icon-512.png")
make_icon(180, f"{PUBLIC_DIR}/icon-180.png")  # Apple touch icon
make_icon(32,  f"{PUBLIC_DIR}/icon-32.png")
make_icon(16,  f"{PUBLIC_DIR}/icon-16.png")

# Also generate favicon
make_icon(64, f"{PUBLIC_DIR}/favicon.png")

print("\nAll icons generated.")
