import os
from PIL import Image

screenshots_dir = 'docs/manual/assets/screenshots'
for fname in sorted(os.listdir(screenshots_dir)):
    if fname.endswith('.png'):
        fpath = os.path.join(screenshots_dir, fname)
        im = Image.open(fpath)
        print(f'{fname}: size={im.size}')
