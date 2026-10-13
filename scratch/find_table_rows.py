from PIL import Image

im07 = Image.open('scratch/screenshots_backup/07_gestion_academica_estudiantes_simat.png')
im07_crop = im07.crop((0, 38, im07.size[0], im07.size[1]))

for y in range(350, 490):
    row_non_white = [x for x in range(160, 830) if im07_crop.getpixel((x, y))[:3] != (255, 255, 255)]
    if len(row_non_white) > 20:
        print(f'y={y}: non_white_count={len(row_non_white)}, min_x={min(row_non_white)}, max_x={max(row_non_white)}')
