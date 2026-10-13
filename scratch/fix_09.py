from PIL import Image, ImageDraw, ImageFont

im09 = Image.open('scratch/screenshots_backup/09_portal_docente_dashboard.png')
# Crop top bar y=38
im09_clean = im09.crop((0, 38, im09.size[0], im09.size[1]))

font_title = ImageFont.truetype('segoeuib.ttf', 16)
font_badge = ImageFont.truetype('segoeuib.ttf', 9)

draw = ImageDraw.Draw(im09_clean)

# The banner background color at (300, 185) is (27, 51, 118)
banner_bg = im09_clean.getpixel((300, 185))

# Paint over old dark heading: x in [295, 520], y in [172, 198]
draw.rectangle([295, 172, 520, 198], fill=banner_bg)
draw.text((298, 175), "¡Bienvenido, Natalia Castro!", fill=(255, 255, 255), font=font_title)

# The role badge is at y in [152, 168], x in [298, 405]
# Let's see if we want to redraw the badge with yellow background and dark slate text
draw.rounded_rectangle([298, 152, 405, 168], radius=3, fill=(252, 209, 22))
draw.text((303, 154), "ESPACIO OPERATIVO DOCENTE", fill=(15, 23, 42), font=font_badge)

im09_clean.save('docs/manual/assets/screenshots/09_portal_docente_dashboard.png')
print('09 remediated with exact coordinates!')
