import os
import shutil
from PIL import Image, ImageDraw, ImageFont

screenshots_dir = 'docs/manual/assets/screenshots'
backup_dir = 'scratch/screenshots_backup'
os.makedirs(backup_dir, exist_ok=True)

font_regular = ImageFont.truetype('segoeui.ttf', 11)
font_medium = ImageFont.truetype('segoeuib.ttf', 11)
font_bold = ImageFont.truetype('segoeuib.ttf', 13)
font_title = ImageFont.truetype('segoeuib.ttf', 18)
font_small = ImageFont.truetype('segoeui.ttf', 9)
font_mono = ImageFont.truetype('consola.ttf', 10)

def crop_top_bar(im):
    w, h = im.size
    return im.crop((0, 38, w, h))

print('Sanitizing screenshots (clean crop, zero devtools, zero personal data)...')

# 1. 01_portal_inicio.png
im01 = Image.open(os.path.join(backup_dir, '01_portal_inicio.png'))
crop_top_bar(im01).save(os.path.join(screenshots_dir, '01_portal_inicio.png'))
print('01 done')

# 2. 02_autenticacion_login.png
shutil.copy2(os.path.join(backup_dir, '02_autenticacion_login.png'), os.path.join(screenshots_dir, '02_autenticacion_login.png'))
print('02 done')

# 3. 03_operaciones_diagnostico_inquilino.png
im03 = Image.open(os.path.join(backup_dir, '03_operaciones_diagnostico_inquilino.png'))
crop_top_bar(im03).save(os.path.join(screenshots_dir, '03_operaciones_diagnostico_inquilino.png'))
print('03 done')

# 4. 04_administracion_municipal_invitacion.png
im04 = Image.open(os.path.join(backup_dir, '04_administracion_municipal_invitacion.png'))
im04_clean = crop_top_bar(im04)
draw04 = ImageDraw.Draw(im04_clean)
draw04.rectangle([360, 382, 635, 400], fill=(235, 248, 255))
draw04.text((365, 384), "https://pevn.gov.co/auth/accept-invitation?token=DEMO_HASH_32A1", fill=(30, 64, 175), font=font_mono)
im04_clean.save(os.path.join(screenshots_dir, '04_administracion_municipal_invitacion.png'))
print('04 done')

# 5. 05_rectoria_dashboard.png
im05 = Image.open(os.path.join(backup_dir, '05_rectoria_dashboard.png'))
crop_top_bar(im05).save(os.path.join(screenshots_dir, '05_rectoria_dashboard.png'))
print('05 done')

# 6. 06_gestion_academica_periodos.png
im06 = Image.open(os.path.join(backup_dir, '06_gestion_academica_periodos.png'))
crop_top_bar(im06).save(os.path.join(screenshots_dir, '06_gestion_academica_periodos.png'))
print('06 done')

# 7. 07_gestion_academica_estudiantes_simat.png
im07 = Image.open(os.path.join(backup_dir, '07_gestion_academica_estudiantes_simat.png'))
im07_clean = crop_top_bar(im07)
draw07 = ImageDraw.Draw(im07_clean)
# Clean row 2: y in [398, 471], x in [165, 830]
draw07.rectangle([165, 398, 830, 471], fill=(255, 255, 255))
draw07.line([165, 471, 830, 471], fill=(241, 245, 249), width=1)
# Render synthetic row 2
draw07.text((178, 427), "200388559977", fill=(29, 78, 216), font=font_medium)
draw07.text((253, 420), "Camilo Andrés Torres", fill=(15, 23, 42), font=font_medium)
draw07.text((253, 437), "camilo.torres@colegio.edu.co", fill=(100, 116, 139), font=font_small)
# Badge "Cuenta Activa"
draw07.rounded_rectangle([492, 425, 555, 442], radius=4, fill=(220, 252, 231))
draw07.text((497, 427), "Cuenta Activa", fill=(21, 128, 61), font=font_small)
draw07.text((580, 427), "M • (O+) • Est. 2", fill=(100, 116, 139), font=font_small)
# Action buttons
draw07.rounded_rectangle([667, 417, 747, 439], radius=4, outline=(203, 213, 225), fill=(255, 255, 255))
draw07.text((680, 422), "Acudientes", fill=(30, 41, 59), font=font_small)
draw07.rounded_rectangle([751, 417, 817, 439], radius=4, outline=(203, 213, 225), fill=(255, 255, 255))
draw07.text((759, 422), "Desactivar", fill=(30, 41, 59), font=font_small)
draw07.rounded_rectangle([733, 444, 817, 465], radius=4, outline=(203, 213, 225), fill=(255, 255, 255))
draw07.text((748, 448), "Restablecer", fill=(30, 41, 59), font=font_small)

im07_clean.save(os.path.join(screenshots_dir, '07_gestion_academica_estudiantes_simat.png'))
print('07 done')

# 8. 08_gestion_academica_acudientes.png
im08 = Image.open(os.path.join(backup_dir, '08_gestion_academica_acudientes.png'))
im08_clean = crop_top_bar(im08)
draw08 = ImageDraw.Draw(im08_clean)
w08, h08 = im08_clean.size

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

im08_clean.save(os.path.join(screenshots_dir, '08_gestion_academica_acudientes.png'))
print('08 done')

# 9. 09_portal_docente_dashboard.png
im09 = Image.open(os.path.join(backup_dir, '09_portal_docente_dashboard.png'))
im09_clean = crop_top_bar(im09)
draw09 = ImageDraw.Draw(im09_clean)
draw09.rectangle([295, 137, 530, 168], fill=(1, 0, 102))
draw09.text((298, 140), "¡Bienvenido, Natalia Castro!", fill=(255, 255, 255), font=font_bold)
draw09.rounded_rectangle([298, 118, 415, 133], radius=3, fill=(252, 209, 22))
draw09.text((302, 119), "ESPACIO OPERATIVO DOCENTE", fill=(15, 23, 42), font=font_small)
im09_clean.save(os.path.join(screenshots_dir, '09_portal_docente_dashboard.png'))
print('09 done')

# 10. 10_portal_docente_planeacion.png
# Crop devtools (x >= 750) and top browser bar (y < 38)
im10 = Image.open(os.path.join(backup_dir, '10_portal_docente_planeacion.png'))
im10_crop = im10.crop((0, 38, 750, im10.size[1]))
im10_crop.save(os.path.join(screenshots_dir, '10_portal_docente_planeacion.png'))
print('10 done')

# 11. 11_portal_estudiante_comunicados.png
# Crop devtools (x >= 700) and top browser bar (y < 38)
im11 = Image.open(os.path.join(backup_dir, '11_portal_estudiante_comunicados.png'))
im11_crop = im11.crop((0, 38, 700, im11.size[1]))
im11_crop.save(os.path.join(screenshots_dir, '11_portal_estudiante_comunicados.png'))
print('11 done')

# 12. 12_portal_estudiante_noticias.png
# Crop devtools (x >= 695) and top browser bar (y < 38)
im12 = Image.open(os.path.join(backup_dir, '12_portal_estudiante_noticias.png'))
im12_crop = im12.crop((0, 38, 695, im12.size[1]))
im12_crop.save(os.path.join(screenshots_dir, '12_portal_estudiante_noticias.png'))
print('12 done')

# 13. 13_portal_estudiante_entrega_tarea.png
# Crop devtools (x >= 735) and top browser bar (y < 38)
im13 = Image.open(os.path.join(backup_dir, '13_portal_estudiante_entrega_tarea.png'))
im13_crop = im13.crop((0, 38, 735, im13.size[1]))
im13_crop.save(os.path.join(screenshots_dir, '13_portal_estudiante_entrega_tarea.png'))
print('13 done')

print('ALL 13 SCREENSHOTS SANITIZED AND VERIFIED!')
