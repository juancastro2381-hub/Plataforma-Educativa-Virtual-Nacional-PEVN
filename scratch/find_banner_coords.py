from PIL import Image

im09 = Image.open('scratch/screenshots_backup/09_portal_docente_dashboard.png')
im09_crop = im09.crop((0, 38, im09.size[0], im09.size[1]))

# Find where the banner is:
# Banner is around y=140 to 220, x=290 to 710
for y in range(140, 230, 5):
    p = im09_crop.getpixel((350, y))
    print(f'y={y}: rgb={p[:3]}')
