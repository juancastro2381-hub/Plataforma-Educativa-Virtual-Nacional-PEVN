"""
Audit script for documentation, screenshot references, and PDF scripts.
"""
import os
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
screenshots_dir = root / "docs" / "manual" / "assets" / "screenshots"
disk_images = sorted([f.name for f in screenshots_dir.glob("*.png")])

print(f"Total screenshots on disk: {len(disk_images)}")
for img in disk_images:
    p = screenshots_dir / img
    print(f"  - {img} ({p.stat().st_size} bytes)")

# 1. Inspect PEVN_INSTITUTIONAL_USER_GUIDE.html
inst_path = root / "docs" / "manual" / "PEVN_INSTITUTIONAL_USER_GUIDE.html"
inst_content = inst_path.read_text(encoding="utf-8")
inst_imgs = re.findall(r'src=["\']([^"\']+\.png)["\']', inst_content)
print(f"\nImages in PEVN_INSTITUTIONAL_USER_GUIDE.html ({len(inst_imgs)} references):")
for img in inst_imgs:
    print(f"  - {img}")

# 2. Inspect index.html
index_path = root / "docs" / "manual" / "index.html"
index_content = index_path.read_text(encoding="utf-8")
index_imgs = re.findall(r'src=["\']([^"\']+\.png)["\']', index_content)
print(f"\nImages in index.html ({len(index_imgs)} references):")
for img in index_imgs:
    print(f"  - {img}")

# 3. Inspect scripts/generate_institutional_user_guide_pdf.py
pdf_inst_script = root / "scripts" / "generate_institutional_user_guide_pdf.py"
pdf_inst_content = pdf_inst_script.read_text(encoding="utf-8")
pdf_inst_imgs = re.findall(r'["\']([^"\']*\d{2}_[^"\']*\.png)["\']', pdf_inst_content)
print(f"\nImages in generate_institutional_user_guide_pdf.py ({len(pdf_inst_imgs)} references):")
for img in set(pdf_inst_imgs):
    print(f"  - {img}")

# 4. Inspect scripts/generate_manual_pdf.py
pdf_manual_script = root / "scripts" / "generate_manual_pdf.py"
pdf_manual_content = pdf_manual_script.read_text(encoding="utf-8")
pdf_manual_imgs = re.findall(r'["\']([^"\']*\d{2}_[^"\']*\.png)["\']', pdf_manual_content)
print(f"\nImages in generate_manual_pdf.py ({len(pdf_manual_imgs)} references):")
for img in set(pdf_manual_imgs):
    print(f"  - {img}")

# 5. Link and Anchor Verification
def verify_links(html_file: Path):
    print(f"\n=== Verificando enlaces y anclas en {html_file.name} ===")
    content = html_file.read_text(encoding="utf-8")
    base = html_file.parent
    
    # Images
    imgs = re.findall(r'src=["\']([^"\']+)["\']', content)
    for img in imgs:
        if not img.startswith("http") and not img.startswith("data:"):
            p = (base / img).resolve()
            assert p.exists(), f"IMAGEN NO ENCONTRADA: {img} -> {p}"
    print(f"  [OK] {len(imgs)} imágenes verificadas en disco.")
    
    # Anchors and Hrefs
    ids = set(re.findall(r'id=["\']([^"\']+)["\']', content))
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', content)
    broken_anchors = []
    missing_files = []
    for h in hrefs:
        if h.startswith("#"):
            a = h[1:]
            if a and a not in ids:
                broken_anchors.append(h)
        elif not h.startswith("http") and not h.startswith("mailto:") and not h.startswith("javascript:"):
            fp = (base / h.split("#")[0]).resolve()
            if not fp.exists():
                missing_files.append((h, fp))
                
    print(f"  [OK] {len(hrefs)} enlaces verificados.")
    if broken_anchors:
        print(f"  [ADVERTENCIA] Anclas internas no resueltas: {broken_anchors}")
    else:
        print(f"  [OK] Cero anclas rotas.")
    if missing_files:
        print(f"  [ERROR] Archivos no encontrados: {missing_files}")
    else:
        print(f"  [OK] Todos los archivos locales referenciados existen.")

verify_links(inst_path)
verify_links(index_path)

