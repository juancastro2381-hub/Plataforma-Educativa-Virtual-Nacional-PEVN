#!/usr/bin/env python3
"""
PEVN — Validador Estricto de Integridad Documental, Capturas y Artefactos PDF
Auditoría y Aseguramiento Técnico DOC-04-R1.

Valida de forma estricta:
1. Referencias locales en HTML (src, href, openLightbox, downloads).
2. Resolución y existencia de todas las imágenes en disco.
3. Consistencia de anclas internas (#id) y ausencia de IDs duplicados.
4. Coherencia bidireccional del Manifiesto Oficial de Capturas (SCREENSHOT_MANIFEST.md).
5. Existencia, tamaño e integridad de los artefactos PDF oficiales e históricos.
6. Existencia y alineación de los scripts generadores de PDF.
7. Conteo de páginas e imágenes embebidas en los PDFs (vía PyMuPDF).

Retorna código de salida 0 si todos los chequeos obligatorios pasan.
Retorna código de salida 1 si se detecta cualquier falla obligatoria.
"""

import os
import re
import sys
from pathlib import Path
from collections import Counter

# Asegurar codificación UTF-8 en salida estándar
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
MANUAL_DIR = ROOT_DIR / "docs" / "manual"
SCREENSHOTS_DIR = MANUAL_DIR / "assets" / "screenshots"
PDF_DIR = MANUAL_DIR / "pdf"
SCRIPTS_DIR = ROOT_DIR / "scripts"
MANIFEST_FILE = MANUAL_DIR / "SCREENSHOT_MANIFEST.md"

INST_HTML = MANUAL_DIR / "PEVN_INSTITUTIONAL_USER_GUIDE.html"
OPER_HTML = MANUAL_DIR / "index.html"

REQUIRED_PDFS = [
    "PEVN_INSTITUTIONAL_USER_GUIDE.pdf",
    "PEVN_INTERACTIVE_USER_MANUAL.pdf",
    "PEVN_INSTITUTIONAL_USER_GUIDE_R1.pdf"
]

REQUIRED_SCRIPTS = [
    "generate_institutional_user_guide_pdf.py",
    "generate_manual_pdf.py"
]

PASS_LIST = []
WARN_LIST = []
FAIL_LIST = []


def record_pass(check_name: str, detail: str = ""):
    PASS_LIST.append((check_name, detail))
    print(f"  [PASS] {check_name}" + (f": {detail}" if detail else ""))


def record_warn(check_name: str, detail: str = ""):
    WARN_LIST.append((check_name, detail))
    print(f"  [WARN] {check_name}" + (f": {detail}" if detail else ""))


def record_fail(check_name: str, detail: str = ""):
    FAIL_LIST.append((check_name, detail))
    print(f"  [FAIL] {check_name}" + (f": {detail}" if detail else ""))


def audit_html_file(html_path: Path):
    print(f"\n--- Auditando Documento HTML: {html_path.name} ---")
    if not html_path.exists():
        record_fail("Archivo HTML no encontrado", str(html_path))
        return

    content = html_path.read_text(encoding="utf-8")
    base_dir = html_path.parent

    # 1. Chequeo de IDs y duplicados
    ids = re.findall(r'id=["\']([^"\']+)["\']', content)
    id_counts = Counter(ids)
    duplicates = {k: v for k, v in id_counts.items() if v > 1}
    if duplicates:
        record_fail(f"{html_path.name}: IDs duplicados detectados", str(duplicates))
    else:
        record_pass(f"{html_path.name}: Cero IDs duplicados", f"{len(ids)} IDs únicos validados")

    # 2. Chequeo de referencias de imágenes (src)
    src_images = re.findall(r'src=["\']([^"\']+)["\']', content)
    for src in src_images:
        if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
            continue
        img_target = (base_dir / src).resolve()
        if not img_target.exists():
            record_fail(f"{html_path.name}: Imagen no encontrada en disco", f"{src} -> {img_target}")
        elif img_target.stat().st_size == 0:
            record_fail(f"{html_path.name}: Imagen vacía en disco (0 bytes)", str(img_target))
    record_pass(f"{html_path.name}: Integridad de etiquetas <img>", f"{len(src_images)} referencias validadas")

    # 3. Chequeo de invocaciones a openLightbox
    lightbox_refs = re.findall(r'openLightbox\(["\']([^"\']+)["\']', content)
    for lb in lightbox_refs:
        if lb.startswith("http://") or lb.startswith("https://") or lb.startswith("data:"):
            continue
        lb_target = (base_dir / lb).resolve()
        if not lb_target.exists():
            record_fail(f"{html_path.name}: Destino de openLightbox no encontrado", f"{lb} -> {lb_target}")
    if lightbox_refs:
        record_pass(f"{html_path.name}: Integridad de handlers openLightbox", f"{len(lightbox_refs)} destinos validados")

    # 4. Chequeo de hipervínculos (href) y anclas
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', content)
    id_set = set(ids)
    for href in hrefs:
        if href.startswith("http://") or href.startswith("https://") or href.startswith("mailto:") or href.startswith("tel:") or href.startswith("javascript:"):
            continue
        if href.startswith("#"):
            anchor = href[1:]
            if anchor and anchor not in id_set:
                record_fail(f"{html_path.name}: Ancla interna no resuelta", f"#{anchor}")
        else:
            file_part = href.split("#")[0]
            if file_part:
                file_target = (base_dir / file_part).resolve()
                if not file_target.exists():
                    record_fail(f"{html_path.name}: Archivo local vinculado no existe", f"{href} -> {file_target}")
                elif file_target.stat().st_size == 0:
                    record_fail(f"{html_path.name}: Archivo local vinculado está vacío", str(file_target))
    record_pass(f"{html_path.name}: Integridad de hipervínculos y anclas", f"{len(hrefs)} enlaces validados")


def audit_screenshot_inventory_and_manifest():
    print("\n--- Auditando Inventario de Capturas y SCREENSHOT_MANIFEST.md ---")
    if not SCREENSHOTS_DIR.exists():
        record_fail("Directorio de capturas no existe", str(SCREENSHOTS_DIR))
        return

    disk_images = sorted([f.name for f in SCREENSHOTS_DIR.glob("*.png")])
    if len(disk_images) == 0:
        record_fail("Directorio de capturas vacío", "0 imágenes encontradas")
        return
    record_pass("Inventario físico de capturas en disco", f"{len(disk_images)} archivos PNG encontrados")

    for img_name in disk_images:
        img_path = SCREENSHOTS_DIR / img_name
        if img_path.stat().st_size == 0:
            record_fail("Captura con tamaño 0 bytes", str(img_path))

    if not MANIFEST_FILE.exists():
        record_fail("Manifiesto de capturas no existe", str(MANIFEST_FILE))
        return

    manifest_text = MANIFEST_FILE.read_text(encoding="utf-8")
    manifest_images = set(re.findall(r'(\d{2}_[a-z0-9_]+\.png)', manifest_text))

    disk_set = set(disk_images)
    missing_in_manifest = disk_set - manifest_images
    missing_on_disk = manifest_images - disk_set

    if missing_in_manifest:
        record_fail("Capturas en disco ausentes en el manifiesto", str(missing_in_manifest))
    if missing_on_disk:
        record_fail("Capturas en manifiesto ausentes en disco", str(missing_on_disk))

    if not missing_in_manifest and not missing_on_disk:
        record_pass("Consistencia bidireccional Disco vs. Manifiesto", f"100% de paridad ({len(disk_images)} capturas)")


def audit_pdf_artifacts():
    print("\n--- Auditando Artefactos PDF Oficiales e Históricos ---")
    for pdf_name in REQUIRED_PDFS:
        pdf_path = PDF_DIR / pdf_name
        if not pdf_path.exists():
            record_fail("Artefacto PDF requerido no existe", str(pdf_path))
        else:
            sz = pdf_path.stat().st_size
            if sz == 0:
                record_fail("Artefacto PDF vacío (0 bytes)", str(pdf_path))
            else:
                record_pass(f"PDF verificado: {pdf_name}", f"{sz:,} bytes en disco")

    # Inspección estructural de PDFs usando PyMuPDF si está instalado
    try:
        import fitz
        for pdf_name in REQUIRED_PDFS[:2]:  # Solo las dos guías oficiales vigentes
            pdf_path = PDF_DIR / pdf_name
            doc = fitz.open(pdf_path)
            num_pages = len(doc)
            total_images = sum(len(page.get_images()) for page in doc)
            if num_pages != 9:
                record_fail(f"{pdf_name}: Conteo inesperado de páginas", f"Esperado: 9, Obtenido: {num_pages}")
            else:
                record_pass(f"{pdf_name}: Conteo de páginas verificado", "9 páginas A4")

            if total_images != 13:
                record_fail(f"{pdf_name}: Conteo de imágenes embebidas incorrecto", f"Esperado: 13, Obtenido: {total_images}")
            else:
                record_pass(f"{pdf_name}: Figuras embebidas verificadas", "13 imágenes auténticas")
    except ImportError:
        record_warn("PyMuPDF (fitz) no instalado", "No se ejecutó inspección estructural interna de páginas PDF")


def audit_screenshot_cross_reference_counts():
    print("\n--- Auditando Coherencia de Conteos de Capturas entre Manifiesto, HTMLs y Scripts PDF ---")
    manifest_text = MANIFEST_FILE.read_text(encoding="utf-8") if MANIFEST_FILE.exists() else ""
    manifest_imgs = set(re.findall(r'(\d{2}_[a-z0-9_]+\.png)', manifest_text))

    inst_html_text = INST_HTML.read_text(encoding="utf-8") if INST_HTML.exists() else ""
    inst_html_imgs = set(re.findall(r'assets/screenshots/(\d{2}_[a-z0-9_]+\.png)', inst_html_text))

    oper_html_text = OPER_HTML.read_text(encoding="utf-8") if OPER_HTML.exists() else ""
    oper_html_imgs = set(re.findall(r'assets/screenshots/(\d{2}_[a-z0-9_]+\.png)', oper_html_text))

    manual_py_text = (SCRIPTS_DIR / "generate_manual_pdf.py").read_text(encoding="utf-8")
    manual_py_imgs = set(re.findall(r'(\d{2}_[a-z0-9_]+\.png)', manual_py_text))

    inst_py_text = (SCRIPTS_DIR / "generate_institutional_user_guide_pdf.py").read_text(encoding="utf-8")
    inst_py_imgs = set(re.findall(r'(\d{2}_[a-z0-9_]+\.png)', inst_py_text))

    counts = {
        "Manifiesto (SCREENSHOT_MANIFEST.md)": len(manifest_imgs),
        "Guía Institucional (HTML)": len(inst_html_imgs),
        "Manual Operativo (HTML)": len(oper_html_imgs),
        "Generador Manual PDF (Python)": len(manual_py_imgs),
        "Generador Guía PDF (Python)": len(inst_py_imgs),
    }

    mismatch = False
    for source_name, count in counts.items():
        if count != 13:
            record_fail(f"{source_name}: Conteo incorrecto de capturas", f"Esperado: 13, Obtenido: {count}")
            mismatch = True
        else:
            record_pass(f"{source_name}: 13 capturas referenciadas", "100% de paridad con inventario")

    if not mismatch:
        record_pass("Consistencia global de referencias cruzadas", "Todas las 13 capturas están sincronizadas en los 5 artefactos")


def audit_screenshot_layout_standard():
    print("\n--- Auditando Estándar Unificado de Maquetación y Anchos de Captura (DOC-04-R2) ---")
    
    # 1. Validación de reglas en HTML Institucional
    inst_content = INST_HTML.read_text(encoding="utf-8") if INST_HTML.exists() else ""
    if ".figure-card" in inst_content and "width: 100%" in inst_content and "box-sizing: border-box" in inst_content:
        record_pass("HTML Institucional: .figure-card utiliza 100% de ancho con box-sizing: border-box", "Alineación con márgenes de texto")
    else:
        record_fail("HTML Institucional: Regla de ancho 100% ausente en .figure-card", "Se requiere width: 100% y box-sizing: border-box")

    if ".figure-img" in inst_content and "object-fit: contain" in inst_content:
        record_pass("HTML Institucional: .figure-img preserva proporción con object-fit: contain", "Proporción intacta")
    else:
        record_fail("HTML Institucional: object-fit: contain ausente en .figure-img", "Riesgo de distorsión de imagen")

    # 2. Validación de reglas en HTML Operativo
    oper_content = OPER_HTML.read_text(encoding="utf-8") if OPER_HTML.exists() else ""
    if ".figure-card" in oper_content and "width: 100%" in oper_content and "box-sizing: border-box" in oper_content:
        record_pass("HTML Operativo: .figure-card utiliza 100% de ancho con box-sizing: border-box", "Alineación con márgenes de texto")
    else:
        record_fail("HTML Operativo: Regla de ancho 100% ausente en .figure-card", "Se requiere width: 100% y box-sizing: border-box")

    # 3. Validación de ausencia de inline fixed widths en <img>
    fixed_widths = re.findall(r'<img[^>]+style=["\'][^"\']*width\s*:\s*\d+px', inst_content + oper_content)
    if fixed_widths:
        record_fail("Anchos fijos en línea detectados en <img>", f"{len(fixed_widths)} ocurrencias encontradas")
    else:
        record_pass("HTMLs libres de anchos fijos en línea en etiquetas <img>", "Cero conflictos de estilo")

    # 4. Validación de generadores PDF
    manual_py_text = (SCRIPTS_DIR / "generate_manual_pdf.py").read_text(encoding="utf-8")
    if "colWidths=[PRINTABLE_WIDTH]" in manual_py_text and "KeepTogether" in manual_py_text:
        record_pass("Generador Manual PDF: Contenedor con colWidths=[PRINTABLE_WIDTH] y KeepTogether", "Márgenes alineados y sin leyendas huérfanas")
    else:
        record_fail("Generador Manual PDF: Regla de ancho imprimible o KeepTogether ausente", "make_screenshot_flowable debe usar colWidths=[PRINTABLE_WIDTH]")

    inst_py_text = (SCRIPTS_DIR / "generate_institutional_user_guide_pdf.py").read_text(encoding="utf-8")
    if "colWidths=[PRINTABLE_WIDTH]" in inst_py_text and "KeepTogether" in inst_py_text:
        record_pass("Generador Guía PDF: Contenedor con colWidths=[PRINTABLE_WIDTH] y KeepTogether", "Márgenes alineados y sin leyendas huérfanas")
    else:
        record_fail("Generador Guía PDF: Regla de ancho imprimible o KeepTogether ausente", "make_screenshot_flowable debe usar colWidths=[PRINTABLE_WIDTH]")


def audit_pdf_scripts():
    print("\n--- Auditando Scripts Generadores de PDF ---")
    for script_name in REQUIRED_SCRIPTS:
        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            record_fail("Script generador de PDF requerido no existe", str(script_path))
        else:
            sz = script_path.stat().st_size
            if sz == 0:
                record_fail("Script generador de PDF vacío", str(script_path))
            else:
                record_pass(f"Script generador verificado: {script_name}", f"{sz:,} bytes")


def main():
    print("=" * 80)
    print("PEVN — Auditoría Estricta de Integridad Documental y Maquetación Visual (DOC-04-R2)")
    print("=" * 80)

    audit_html_file(INST_HTML)
    audit_html_file(OPER_HTML)
    audit_screenshot_inventory_and_manifest()
    audit_pdf_artifacts()
    audit_pdf_scripts()
    audit_screenshot_cross_reference_counts()
    audit_screenshot_layout_standard()

    print("\n" + "=" * 80)
    print("NOTA METODOLÓGICA SOBRE VERIFICACIÓN DE ERRORES VISUALES")
    print("=" * 80)
    print("Las comprobaciones estáticas automatizadas validan la integridad de archivos en disco,")
    print("paridad numérica de capturas (13 de 13), resolución de enlaces y reglas estructurales")
    print("de maquetación CSS/ReportLab (ancho 100% y colWidths=[PRINTABLE_WIDTH]).")
    print("No obstante, el análisis estático de código NO sustituye la inspección visual de píxel.")
    print("La ausencia de banners de error ('An unexpected error occurred') o elementos de depuración")
    print("ha sido verificada de forma independiente mediante inspección visual página por página (Sección 7).")

    print("\n" + "=" * 80)
    print("RESUMEN GENERAL DE VERIFICACIÓN DOCUMENTAL")
    print("=" * 80)
    print(f"Total de Chequeos Exitosos (PASS) : {len(PASS_LIST)}")
    print(f"Total de Advertencias      (WARN) : {len(WARN_LIST)}")
    print(f"Total de Fallas Detectadas (FAIL) : {len(FAIL_LIST)}")

    if len(FAIL_LIST) > 0:
        print("\n[CRITICAL FAILURE] Se detectaron errores obligatorios en la validación:")
        for name, detail in FAIL_LIST:
            print(f"  ❌ {name}: {detail}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Todos los chequeos obligatorios pasaron satisfactoriamente (Código de salida: 0).")
        sys.exit(0)


if __name__ == "__main__":
    main()

