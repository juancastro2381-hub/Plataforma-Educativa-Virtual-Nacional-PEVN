from PIL import Image

im07 = Image.open('scratch/screenshots_backup/07_gestion_academica_estudiantes_simat.png')
im07_crop = im07.crop((0, 38, im07.size[0], im07.size[1]))

# In im07_crop, let's find where the text in Row 2 is located
# The text contains "Juan Carlos Castro"
# Let's inspect rows from y=380 to 450
for y in range(380, 460, 5):
    p = im07_crop.getpixel((250, y))
    print(f'y={y}: rgb={p[:3]}')
