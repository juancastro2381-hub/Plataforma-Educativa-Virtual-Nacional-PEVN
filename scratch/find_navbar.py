import os
from PIL import Image

im = Image.open('docs/manual/assets/screenshots/08_gestion_academica_acudientes.png')
print(f'Mode: {im.mode}, Size: {im.size}')

# Let's inspect where the browser bar ends:
# The browser bar at top has URL and tabs. Around y=40 or y=50 is the yellow/blue/red top bar of PEVN or the dark navy navbar.
for y in range(0, 100, 5):
    pixel = im.getpixel((500, y))
    print(f'y={y}: pixel={pixel}')
