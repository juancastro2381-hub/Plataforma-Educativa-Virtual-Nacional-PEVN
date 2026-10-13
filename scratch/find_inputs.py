import os
from PIL import Image

im = Image.open('docs/manual/assets/screenshots/08_gestion_academica_acudientes.png')

# The modal inputs have light bluish/gray background (e.g. #EBF4FE or #F1F5F9) or white with gray border
# Let's inspect column 400 from y=250 to y=520
for y in range(250, 520, 5):
    p = im.getpixel((400, y))
    print(f'y={y}: rgb={p[:3]}')
