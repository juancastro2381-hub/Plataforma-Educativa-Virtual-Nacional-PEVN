import fitz
from PIL import Image
import io

doc = fitz.open('docs/manual/pdf/PEVN_INTERACTIVE_USER_MANUAL.pdf')
# Page 5
p5 = doc[4]
imgs5 = p5.get_images()
print(f'Page 5 images: {len(imgs5)}')
for i, img in enumerate(imgs5):
    xref = img[0]
    base = doc.extract_image(xref)
    im = Image.open(io.BytesIO(base["image"]))
    print(f'  P5 Image {i+1} (xref {xref}): size={im.size}, mode={im.mode}')

# Page 6
p6 = doc[5]
imgs6 = p6.get_images()
print(f'Page 6 images: {len(imgs6)}')
for i, img in enumerate(imgs6):
    xref = img[0]
    base = doc.extract_image(xref)
    im = Image.open(io.BytesIO(base["image"]))
    print(f'  P6 Image {i+1} (xref {xref}): size={im.size}, mode={im.mode}')

doc.close()
