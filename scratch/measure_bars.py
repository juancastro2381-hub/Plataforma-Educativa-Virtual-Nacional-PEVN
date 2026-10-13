from PIL import Image

for fname in ['10_portal_docente_planeacion.png', '11_portal_estudiante_comunicados.png', '12_portal_estudiante_noticias.png', '13_portal_estudiante_entrega_tarea.png']:
    im = Image.open('scratch/screenshots_backup/' + fname)
    im_crop = im.crop((0, 38, im.size[0], im.size[1]))
    # Find where top dark navbar ends (color is dark navy ~ (15, 23, 42) or (1, 0, 102))
    navbar_h = 0
    for y in range(0, 100):
        if im_crop.getpixel((10, y))[:3] != im_crop.getpixel((10, 10))[:3]:
            navbar_h = y
            break
    # Find where footer starts
    h = im_crop.size[1]
    footer_h = 0
    for y in range(h - 1, h - 100, -1):
        if im_crop.getpixel((10, y))[:3] != im_crop.getpixel((10, h - 5))[:3]:
            footer_h = h - y
            break
    print(f'{fname}: navbar_height={navbar_h}, footer_height={footer_h}, total_h={h}')
