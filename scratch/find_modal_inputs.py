from PIL import Image

im08 = Image.open('scratch/screenshots_backup/08_gestion_academica_acudientes.png')
im08_crop = im08.crop((0, 38, im08.size[0], im08.size[1]))

# Find input boxes inside modal (x between 340 and 650)
# Input boxes have white background surrounded by borders or autofill blue
for y in range(200, 480, 5):
    p = im08_crop.getpixel((400, y))
    p_right = im08_crop.getpixel((520, y))
    print(f'y={y}: left={p[:3]}, right={p_right[:3]}')
