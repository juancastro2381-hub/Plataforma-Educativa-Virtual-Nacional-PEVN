import os
from PIL import Image

im = Image.open('docs/manual/assets/screenshots/08_gestion_academica_acudientes.png')
w, h = im.size

# Find white modal box
# Modal has white background (255, 255, 255)
modal_pixels = []
for y in range(50, h):
    row_white = [x for x in range(w) if im.getpixel((x, y))[:3] == (255, 255, 255)]
    if len(row_white) > 100:
        modal_pixels.append((y, min(row_white), max(row_white)))

if modal_pixels:
    y_min = modal_pixels[0][0]
    y_max = modal_pixels[-1][0]
    x_min = min(p[1] for p in modal_pixels)
    x_max = max(p[2] for p in modal_pixels)
    print(f'Modal box: x=[{x_min}, {x_max}], y=[{y_min}, {y_max}], width={x_max - x_min}, height={y_max - y_min}')
