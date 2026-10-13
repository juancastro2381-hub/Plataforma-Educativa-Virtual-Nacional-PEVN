import os
from PIL import Image

im = Image.open('docs/manual/assets/screenshots/07_gestion_academica_estudiantes_simat.png')
w, h = im.size
print(f'07 image size: {w}x{h}')

# Let's inspect rows around y=350 to 528
# Search for the SIMAT codes column around x=190
for y in range(400, h, 10):
    p = im.getpixel((200, y))
    print(f'y={y}: rgb={p[:3]}')
