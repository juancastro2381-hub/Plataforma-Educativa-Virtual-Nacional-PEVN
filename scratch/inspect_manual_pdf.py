import fitz

doc = fitz.open('docs/manual/pdf/PEVN_INTERACTIVE_USER_MANUAL.pdf')
for i, page in enumerate(doc):
    imgs = page.get_images()
    text = page.get_text()
    first_lines = [l.strip() for l in text.split('\n') if l.strip()][:4]
    print(f'Page {i+1}: {len(imgs)} images, sample text: {first_lines}')
    for img_info in imgs:
        xref = img_info[0]
        base_img = doc.extract_image(xref)
        print(f'   Image xref {xref}: format {base_img.get("ext")}, size {base_img.get("width")}x{base_img.get("height")}')
doc.close()
