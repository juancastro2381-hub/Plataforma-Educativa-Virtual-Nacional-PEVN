import os
import shutil
from PIL import Image, ImageDraw, ImageFont

screenshots_dir = 'docs/manual/assets/screenshots'
backup_dir = 'scratch/screenshots_backup'

crop_top = {
    '01_portal_inicio.png': 61,
    '02_autenticacion_login.png': 0,
    '03_operaciones_diagnostico_inquilino.png': 43,
    '04_administracion_municipal_invitacion.png': 65,
    '05_rectoria_dashboard.png': 41,
    '06_gestion_academica_periodos.png': 38,
    '07_gestion_academica_estudiantes_simat.png': 38,
    '08_gestion_academica_acudientes.png': 38,
    '09_portal_docente_dashboard.png': 58,
    '10_portal_docente_planeacion.png': 35,
    '11_portal_estudiante_comunicados.png': 59,
    '12_portal_estudiante_noticias.png': 36,
    '13_portal_estudiante_entrega_tarea.png': 50,
}

font_regular = ImageFont.truetype('segoeui.ttf', 11)
font_medium = ImageFont.truetype('segoeuib.ttf', 11)
font_bold = ImageFont.truetype('segoeuib.ttf', 14)
font_title = ImageFont.truetype('segoeuib.ttf', 16)
font_small = ImageFont.truetype('segoeui.ttf', 9)
font_mono = ImageFont.truetype('consola.ttf', 10)

print('Applying master precision sanitization across all 13 screenshots...')

# 1. 01_portal_inicio.png
im01 = Image.open(os.path.join(backup_dir, '01_portal_inicio.png'))
im01.crop((0, crop_top['01_portal_inicio.png'], im01.size[0], im01.size[1])).save(os.path.join(screenshots_dir, '01_portal_inicio.png'))
print('01 done')

# 2. 02_autenticacion_login.png
shutil.copy2(os.path.join(backup_dir, '02_autenticacion_login.png'), os.path.join(screenshots_dir, '02_autenticacion_login.png'))
print('02 done')

# 3. 03_operaciones_diagnostico_inquilino.png
im03 = Image.open(os.path.join(backup_dir, '03_operaciones_diagnostico_inquilino.png'))
im03.crop((0, crop_top['03_operaciones_diagnostico_inquilino.png'], im03.size[0], im03.size[1])).save(os.path.join(screenshots_dir, '03_operaciones_diagnostico_inquilino.png'))
print('03 done')

# 4. 04_administracion_municipal_invitacion.png
im04 = Image.open(os.path.join(backup_dir, '04_administracion_municipal_invitacion.png'))
im04_c = im04.crop((0, crop_top['04_administracion_municipal_invitacion.png'], im04.size[0], im04.size[1]))
draw04 = ImageDraw.Draw(im04_c)
draw04.rectangle([360, 355, 635, 375], fill=(235, 248, 255))
draw04.text((365, 357), "https://pevn.gov.co/auth/accept-invitation?token=DEMO_HASH_32A1", fill=(30, 64, 175), font=font_mono)
im04_c.save(os.path.join(screenshots_dir, '04_administracion_municipal_invitacion.png'))
print('04 done')

# 5. 05_rectoria_dashboard.png
im05 = Image.open(os.path.join(backup_dir, '05_rectoria_dashboard.png'))
im05.crop((0, crop_top['05_rectoria_dashboard.png'], im05.size[0], im05.size[1])).save(os.path.join(screenshots_dir, '05_rectoria_dashboard.png'))
print('05 done')

# 6. 06_gestion_academica_periodos.png
im06 = Image.open(os.path.join(backup_dir, '06_gestion_academica_periodos.png'))
im06.crop((0, crop_top['06_gestion_academica_periodos.png'], im06.size[0], im06.size[1])).save(os.path.join(screenshots_dir, '06_gestion_academica_periodos.png'))
print('06 done')

# 7. 07_gestion_academica_estudiantes_simat.png
im07 = Image.open(os.path.join(backup_dir, '07_gestion_academica_estudiantes_simat.png'))
im07_c = im07.crop((0, crop_top['07_gestion_academica_estudiantes_simat.png'], im07.size[0], im07.size[1]))
draw07 = ImageDraw.Draw(im07_c)
# Clean row 2: y in [398, 471], x in [165, 830]
draw07.rectangle([165, 398, 830, 471], fill=(255, 255, 255))
draw07.line([165, 471, 830, 471], fill=(241, 245, 249), width=1)
# Render synthetic row 2
draw07.text((178, 427), "200388559977", fill=(29, 78, 216), font=font_medium)
draw07.text((253, 420), "Camilo Andrés Torres", fill=(15, 23, 42), font=font_medium)
draw07.text((253, 437), "camilo.torres@colegio.edu.co", fill=(100, 116, 139), font=font_small)
draw07.rounded_rectangle([492, 425, 555, 442], radius=4, fill=(220, 252, 231))
draw07.text((497, 427), "Cuenta Activa", fill=(21, 128, 61), font=font_small)
draw07.text((580, 427), "M • (O+) • Est. 2", fill=(100, 116, 139), font=font_small)
draw07.rounded_rectangle([667, 417, 747, 439], radius=4, outline=(203, 213, 225), fill=(255, 255, 255))
draw07.text((680, 422), "Acudientes", fill=(30, 41, 59), font=font_small)
draw07.rounded_rectangle([751, 417, 817, 439], radius=4, outline=(203, 213, 225), fill=(255, 255, 255))
draw07.text((759, 422), "Desactivar", fill=(30, 41, 59), font=font_small)
draw07.rounded_rectangle([733, 444, 817, 465], radius=4, outline=(203, 213, 225), fill=(255, 255, 255))
draw07.text((748, 448), "Restablecer", fill=(30, 41, 59), font=font_small)
im07_c.save(os.path.join(screenshots_dir, '07_gestion_academica_estudiantes_simat.png'))
print('07 done')

# 8. 08_gestion_academica_acudientes.png
im08 = Image.open(os.path.join(backup_dir, '08_gestion_academica_acudientes.png'))
im08_c = im08.crop((0, crop_top['08_gestion_academica_acudientes.png'], im08.size[0], im08.size[1]))
draw08 = ImageDraw.Draw(im08_c)
w08, h08 = im08_c.size

# Mask background outside modal
draw08.rectangle([0, 0, 342, h08], fill=(70, 75, 87))
draw08.rectangle([660, 0, w08, h08], fill=(70, 75, 87))

# Inside modal: replace input boxes
draw08.rounded_rectangle([348, 254, 485, 281], radius=4, outline=(203, 213, 225), fill=(248, 250, 252))
draw08.text((356, 260), "Esperanza", fill=(30, 41, 59), font=font_regular)

draw08.rounded_rectangle([493, 254, 630, 281], radius=4, outline=(203, 213, 225), fill=(248, 250, 252))
draw08.text((501, 260), "Gómez Valencia", fill=(30, 41, 59), font=font_regular)

draw08.rounded_rectangle([448, 317, 630, 344], radius=4, outline=(203, 213, 225), fill=(248, 250, 252))
draw08.text((456, 323), "52345678", fill=(30, 41, 59), font=font_regular)

draw08.rounded_rectangle([348, 381, 485, 408], radius=4, outline=(203, 213, 225), fill=(248, 250, 252))
draw08.text((356, 387), "3165550199", fill=(30, 41, 59), font=font_regular)

draw08.rounded_rectangle([493, 381, 630, 408], radius=4, outline=(203, 213, 225), fill=(248, 250, 252))
draw08.text((498, 387), "acudiente.demo@iedsanjose.edu.co", fill=(30, 41, 59), font=font_small)

draw08.rounded_rectangle([493, 442, 630, 465], radius=4, outline=(203, 213, 225), fill=(248, 250, 252))
draw08.text((498, 447), "Calle 10 # 5-24, Bogotá", fill=(30, 41, 59), font=font_small)
im08_c.save(os.path.join(screenshots_dir, '08_gestion_academica_acudientes.png'))
print('08 done')

# 9. 09_portal_docente_dashboard.png
im09 = Image.open(os.path.join(backup_dir, '09_portal_docente_dashboard.png'))
im09_c = im09.crop((0, crop_top['09_portal_docente_dashboard.png'], im09.size[0], im09.size[1]))
draw09 = ImageDraw.Draw(im09_c)
banner_bg = im09_c.getpixel((300, 160))
draw09.rectangle([295, 152, 520, 178], fill=banner_bg)
draw09.text((298, 155), "¡Bienvenido, Natalia Castro!", fill=(255, 255, 255), font=font_title)
draw09.rounded_rectangle([298, 132, 405, 148], radius=3, fill=(252, 209, 22))
draw09.text((303, 134), "ESPACIO OPERATIVO DOCENTE", fill=(15, 23, 42), font=font_small)
im09_c.save(os.path.join(screenshots_dir, '09_portal_docente_dashboard.png'))
print('09 done')

# 10. 10_portal_docente_planeacion.png
im10 = Image.open(os.path.join(backup_dir, '10_portal_docente_planeacion.png'))
im10_c = im10.crop((0, crop_top['10_portal_docente_planeacion.png'], 750, im10.size[1]))
im10_c.save(os.path.join(screenshots_dir, '10_portal_docente_planeacion.png'))
print('10 done')

# 11. 11_portal_estudiante_comunicados.png
im11 = Image.open(os.path.join(backup_dir, '11_portal_estudiante_comunicados.png'))
im11_c = im11.crop((0, crop_top['11_portal_estudiante_comunicados.png'], 700, im11.size[1]))
im11_c.save(os.path.join(screenshots_dir, '11_portal_estudiante_comunicados.png'))
print('11 done')

# 12. 12_portal_estudiante_noticias.png
im12 = Image.open(os.path.join(backup_dir, '12_portal_estudiante_noticias.png'))
im12_c = im12.crop((0, crop_top['12_portal_estudiante_noticias.png'], 695, im12.size[1]))
im12_c.save(os.path.join(screenshots_dir, '12_portal_estudiante_noticias.png'))
print('12 done')

# 13. 13_portal_estudiante_entrega_tarea.png
im13 = Image.open(os.path.join(backup_dir, '13_portal_estudiante_entrega_tarea.png'))
im13_c = im13.crop((0, crop_top['13_portal_estudiante_entrega_tarea.png'], 735, im13.size[1]))
im13_c.save(os.path.join(screenshots_dir, '13_portal_estudiante_entrega_tarea.png'))
print('13 done')

print('ALL 13 MASTER PRECISION SCREENSHOTS COMPLETED!')
