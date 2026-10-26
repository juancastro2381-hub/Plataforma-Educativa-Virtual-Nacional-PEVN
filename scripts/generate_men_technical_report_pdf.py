#!/usr/bin/env python3
"""
PEVN — Generador del Informe Técnico Institucional en PDF para el MEN
Convierte docs/reports/PEVN_INFORME_TECNICO_INSTITUCIONAL_MEN.md
a docs/reports/PEVN_INFORME_TECNICO_INSTITUCIONAL_MEN.pdf
utilizando ReportLab y NumberedCanvas con estándar tipográfico institucional.
"""

import os
import sys

# Agregar scripts al path para reutilizar motor de generación
sys.path.insert(0, os.path.dirname(__file__))
from generate_government_pdfs import generate_individual_pdf

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_md = os.path.join(repo_root, "docs", "reports", "PEVN_INFORME_TECNICO_INSTITUCIONAL_MEN.md")
    dest_pdf = os.path.join(repo_root, "docs", "reports", "PEVN_INFORME_TECNICO_INSTITUCIONAL_MEN.pdf")

    if not os.path.exists(src_md):
        print(f"[ERROR] Archivo fuente no encontrado: {src_md}")
        sys.exit(1)

    print(f"=== Generando PDF: {dest_pdf} ===")
    generate_individual_pdf(
        src_md_path=src_md,
        dest_pdf_path=dest_pdf,
        doc_title="Informe Técnico Institucional MEN",
        doc_subtitle="Oficina de Tecnología y Sistemas de Información"
    )
    print(f"[SUCCESS] PDF generado exitosamente: {dest_pdf}")

if __name__ == "__main__":
    main()
