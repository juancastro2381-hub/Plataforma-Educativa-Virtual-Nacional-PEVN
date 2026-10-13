import os
from PIL import Image

for fname in ['10_portal_docente_planeacion.png', '11_portal_estudiante_comunicados.png', '12_portal_estudiante_noticias.png', '13_portal_estudiante_entrega_tarea.png']:
    im = Image.open(os.path.join('docs/manual/assets/screenshots', fname))
    w, h = im.size
    print(f'=== {fname} ({w}x{h}) ===')
    # Devtools border usually around x=700-750
    # Let's check row y=100 from x=650 to x=800
    for x in range(680, 780, 5):
        p = im.getpixel((x, 100))
        # devtools header has light gray / tabs
        print(f'  x={x}: rgb={p[:3]}', end='')
        if x % 25 == 0:
            print()
    print()
