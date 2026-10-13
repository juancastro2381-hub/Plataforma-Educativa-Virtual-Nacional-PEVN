#!/usr/bin/env python3
"""
PEVN — Script Generador de Paquetes PDF Gubernamentales (DOC-01)
Convierte los artefactos Markdown de docs/government/ a PDFs institucionales profesionales de alta calidad.
Utiliza ReportLab Platypus con numeración de dos pasadas y diseño institucional adaptado para A4.
"""

import os
import re
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# Dimensiones de A4
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 40.0
MARGIN_Y = 45.0
PRINTABLE_WIDTH = PAGE_WIDTH - (2 * MARGIN_X)
PRINTABLE_HEIGHT = PAGE_HEIGHT - (2 * MARGIN_Y)

# Paleta de Colores Institucional
COLOR_PRIMARY = colors.HexColor("#1A365D")    # Azul Oscuro Institucional
COLOR_SECONDARY = colors.HexColor("#2B6CB0")  # Azul Medio Técnico
COLOR_TEXT_DARK = colors.HexColor("#2D3748")  # Texto Grafito Legible
COLOR_TEXT_MUTED = colors.HexColor("#718096") # Texto Secundario
COLOR_BG_LIGHT = colors.HexColor("#F7FAFC")   # Fondo Tablas Alternadas
COLOR_BG_BOX = colors.HexColor("#EDF2F7")     # Fondo Cajas de Alerta
COLOR_BORDER = colors.HexColor("#CBD5E0")     # Bordes Sutiles
COLOR_WHITE = colors.HexColor("#FFFFFF")
COLOR_ACCENT = colors.HexColor("#319795")     # Acento Verde Azulado


class NumberedCanvas(canvas.Canvas):
    """
    Lienzo personalizado para calcular el total de páginas en dos pasadas
    y dibujar encabezados y pies de página institucionales consistentes.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.suppress_header_footer_pages = set()
        self.doc_title = "PLATAFORMA EDUCATIVA VIRTUAL NACIONAL (PEVN)"
        self.doc_subtitle = "Documento de Presentación Institucional"

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if self._pageNumber not in self.suppress_header_footer_pages:
                self.draw_header()
                self.draw_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_header(self):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_TEXT_MUTED)
        self.drawString(MARGIN_X, PAGE_HEIGHT - 32, self.doc_title)
        self.drawRightString(PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 32, self.doc_subtitle)
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(MARGIN_X, PAGE_HEIGHT - 36, PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 36)
        self.restoreState()

    def draw_footer(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_TEXT_MUTED)
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(MARGIN_X, 36, PAGE_WIDTH - MARGIN_X, 36)
        footer_text = "PEVN — Documento Informativo y Técnico para el Sector Oficial Colombiano"
        page_text = f"Página {self._pageNumber} de {total_pages}"
        self.drawString(MARGIN_X, 24, footer_text)
        self.drawRightString(PAGE_WIDTH - MARGIN_X, 24, page_text)
        self.restoreState()


def get_styles():
    styles = getSampleStyleSheet()
    
    body = ParagraphStyle(
        'GovBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=COLOR_TEXT_DARK,
        spaceAfter=5
    )
    
    body_bold = ParagraphStyle(
        'GovBodyBold',
        parent=body,
        fontName='Helvetica-Bold'
    )
    
    title = ParagraphStyle(
        'GovTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=COLOR_PRIMARY,
        spaceAfter=8,
        keepWithNext=True
    )
    
    subtitle = ParagraphStyle(
        'GovSubtitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=COLOR_SECONDARY,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h1 = ParagraphStyle(
        'GovH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=COLOR_PRIMARY,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )
    
    h2 = ParagraphStyle(
        'GovH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=COLOR_SECONDARY,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    h3 = ParagraphStyle(
        'GovH3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12.5,
        textColor=COLOR_PRIMARY,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    bullet = ParagraphStyle(
        'GovBullet',
        parent=body,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )
    
    callout = ParagraphStyle(
        'GovCallout',
        parent=body,
        fontSize=8.5,
        leading=11.5,
        textColor=COLOR_PRIMARY
    )
    
    table_cell = ParagraphStyle(
        'GovTableCell',
        parent=body,
        fontSize=7.5,
        leading=9.5,
        spaceAfter=0
    )
    
    table_header = ParagraphStyle(
        'GovTableHeader',
        parent=table_cell,
        fontName='Helvetica-Bold',
        textColor=COLOR_WHITE
    )
    
    code_block = ParagraphStyle(
        'GovCodeBlock',
        parent=body,
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#2C5282")
    )

    return {
        'body': body,
        'body_bold': body_bold,
        'title': title,
        'subtitle': subtitle,
        'h1': h1,
        'h2': h2,
        'h3': h3,
        'bullet': bullet,
        'callout': callout,
        'table_cell': table_cell,
        'table_header': table_header,
        'code_block': code_block
    }


def sanitize_text(text):
    """
    Limpia texto de rutas locales, tokens y markdown residual problemático.
    """
    text = re.sub(r'\[([^\]]+)\]\(file:///[^\)]+\)', r'\1', text)
    text = re.sub(r'file:///[^\s\)]+', '', text)
    text = re.sub(r'[a-zA-Z]:\\[^\s\)]+', '', text)
    text = re.sub(r'http://localhost:\d+/?', '', text)
    text = re.sub(r'http://127\.0\.0\.1:\d+/?', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'(?<!\[)[a-zA-Z0-9_.+-]+@(?!example\.com)[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+(?!\])', '[CUENTA DEMO]', text)
    text = re.sub(r'[a-zA-Z0-9_.+-]+@example\.com', '[CUENTA DEMO]', text)
    text = re.sub(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b', '[IDENTIFICADOR DEMO]', text)
    return text


def md_inline_to_xml(text):
    """
    Convierte sintaxis inline de Markdown (**negrita**, *cursiva*, `código`) a tags XML de ReportLab.
    """
    text = sanitize_text(text)
    text = text.replace(r'$\ge N$', '>= N').replace(r'$N$', 'N')
    
    code_spans = []
    def save_code(m):
        code_spans.append(m.group(1))
        return f"___CODESPAN_{len(code_spans)-1}___"
        
    text = re.sub(r'`([^`]+)`', save_code, text)
    
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*([^\*]+?)\*(?!\*)', r'<i>\1</i>', text)
    
    for idx, code in enumerate(code_spans):
        esc_code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        text = text.replace(f"___CODESPAN_{idx}___", f'<font name="Courier" color="#2B6CB0"><b>{esc_code}</b></font>')
        
    return text


def parse_markdown_to_flowables(md_content, styles, is_one_page=False):
    lines = md_content.splitlines()
    flowables = []
    i = 0
    total_lines = len(lines)
    
    in_code_block = False
    code_lines = []
    
    in_table = False
    table_lines = []
    
    while i < total_lines:
        line = lines[i]
        stripped = line.strip()
        
        # 1. Bloques de código ```
        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                code_text = "<br/>".join([md_inline_to_xml(cl) for cl in code_lines])
                code_para = Paragraph(code_text, styles['code_block'])
                t = Table([[code_para]], colWidths=[PRINTABLE_WIDTH])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_LIGHT),
                    ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                flowables.append(t)
                flowables.append(Spacer(1, 3 if is_one_page else 5))
            i += 1
            continue
            
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue
            
        # 2. Tablas Markdown
        if stripped.startswith("|") and stripped.endswith("|"):
            if not in_table:
                in_table = True
                table_lines = [line]
            else:
                table_lines.append(line)
            i += 1
            continue
        elif in_table:
            in_table = False
            table_flowable = process_markdown_table(table_lines, styles, is_one_page)
            if table_flowable:
                flowables.append(table_flowable)
                flowables.append(Spacer(1, 3 if is_one_page else 6))
            table_lines = []
            
        # 3. Líneas vacías
        if not stripped:
            i += 1
            continue
            
        # 4. Separador horizontal ---
        if re.match(r'^-{3,}$', stripped) or re.match(r'^\*{3,}$', stripped):
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceBefore=3, spaceAfter=5))
            i += 1
            continue
            
        # 5. Encabezados
        if stripped.startswith("# "):
            h_text = md_inline_to_xml(stripped[2:])
            flowables.append(Paragraph(h_text, styles['title']))
            i += 1
            continue
        elif stripped.startswith("## "):
            h_text = md_inline_to_xml(stripped[3:])
            flowables.append(Paragraph(h_text, styles['h1']))
            i += 1
            continue
        elif stripped.startswith("### "):
            h_text = md_inline_to_xml(stripped[4:])
            flowables.append(Paragraph(h_text, styles['h2']))
            i += 1
            continue
        elif stripped.startswith("#### "):
            h_text = md_inline_to_xml(stripped[5:])
            flowables.append(Paragraph(h_text, styles['h3']))
            i += 1
            continue
            
        # 6. Alertas y citas (> )
        if stripped.startswith(">"):
            quote_lines = []
            while i < total_lines and lines[i].strip().startswith(">"):
                q_line = lines[i].strip()[1:].strip()
                if not re.match(r'^\[!.*\]$', q_line):
                    quote_lines.append(q_line)
                i += 1
            quote_text = " ".join(quote_lines)
            quote_para = Paragraph(md_inline_to_xml(quote_text), styles['callout'])
            t = Table([[quote_para]], colWidths=[PRINTABLE_WIDTH])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_BOX),
                ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('LINELEFT', (0, 0), (0, 0), 3.0, COLOR_SECONDARY),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            flowables.append(t)
            flowables.append(Spacer(1, 3 if is_one_page else 5))
            continue
            
        # 7. Listas con viñetas o numeradas
        if re.match(r'^[-*]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
            item_text = re.sub(r'^[-*]\s+', '• ', stripped)
            item_text = re.sub(r'^(\d+\.)\s+', r'\1 ', item_text)
            flowables.append(Paragraph(md_inline_to_xml(item_text), styles['bullet']))
            i += 1
            continue
            
        # 8. Párrafo normal
        flowables.append(Paragraph(md_inline_to_xml(stripped), styles['body']))
        if not is_one_page:
            flowables.append(Spacer(1, 2.5))
        i += 1
        
    if in_table and table_lines:
        table_flowable = process_markdown_table(table_lines, styles, is_one_page)
        if table_flowable:
            flowables.append(table_flowable)
            
    return flowables


def process_markdown_table(table_lines, styles, is_one_page=False):
    rows = []
    for line in table_lines:
        s = line.strip()
        if not s.startswith("|") or not s.endswith("|"):
            continue
        if re.match(r'^\|[\s:-|]+\|$', s):
            continue
        parts = [p.strip() for p in s[1:-1].split("|")]
        rows.append(parts)
        
    if not rows:
        return None
        
    col_count = max(len(r) for r in rows)
    for r in rows:
        while len(r) < col_count:
            r.append("")
            
    col_widths = []
    if col_count == 2:
        col_widths = [PRINTABLE_WIDTH * 0.35, PRINTABLE_WIDTH * 0.65]
    elif col_count == 3:
        col_widths = [PRINTABLE_WIDTH * 0.20, PRINTABLE_WIDTH * 0.40, PRINTABLE_WIDTH * 0.40]
    elif col_count == 4:
        col_widths = [PRINTABLE_WIDTH * 0.15, PRINTABLE_WIDTH * 0.35, PRINTABLE_WIDTH * 0.25, PRINTABLE_WIDTH * 0.25]
    elif col_count == 5:
        col_widths = [PRINTABLE_WIDTH * 0.06, PRINTABLE_WIDTH * 0.30, PRINTABLE_WIDTH * 0.16, PRINTABLE_WIDTH * 0.24, PRINTABLE_WIDTH * 0.24]
    elif col_count == 6:
        col_widths = [PRINTABLE_WIDTH * 0.06, PRINTABLE_WIDTH * 0.34, PRINTABLE_WIDTH * 0.16, PRINTABLE_WIDTH * 0.12, PRINTABLE_WIDTH * 0.16, PRINTABLE_WIDTH * 0.16]
    elif col_count == 7:
        col_widths = [PRINTABLE_WIDTH * 0.05, PRINTABLE_WIDTH * 0.23, PRINTABLE_WIDTH * 0.28, PRINTABLE_WIDTH * 0.18, PRINTABLE_WIDTH * 0.08, PRINTABLE_WIDTH * 0.09, PRINTABLE_WIDTH * 0.09]
    elif col_count == 8:
        col_widths = [PRINTABLE_WIDTH * 0.30] + [PRINTABLE_WIDTH * 0.10] * 7
    elif col_count == 9:
        col_widths = [PRINTABLE_WIDTH * 0.28] + [PRINTABLE_WIDTH * 0.09] * 8
    else:
        eq_width = PRINTABLE_WIDTH / col_count
        col_widths = [eq_width] * col_count
        
    table_data = []
    for r_idx, r in enumerate(rows):
        row_data = []
        is_header = (r_idx == 0)
        style_to_use = styles['table_header'] if is_header else styles['table_cell']
        for c in r:
            xml_c = md_inline_to_xml(c)
            row_data.append(Paragraph(xml_c, style_to_use))
        table_data.append(row_data)
        
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.0 if is_one_page else 3.0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.0 if is_one_page else 3.0),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.4, COLOR_BORDER),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), COLOR_BG_LIGHT))
            
    t.setStyle(TableStyle(t_style))
    return t


def generate_one_page_executive_summary_pdf(src_md_path, dest_pdf_path):
    """
    Genera el PDF del Resumen Ejecutivo asegurando ESTRICTAMENTE 1 SOLA PÁGINA.
    """
    with open(src_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    styles = getSampleStyleSheet()
    
    p_body = ParagraphStyle(
        'OnePageBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.4,
        leading=9.2,
        textColor=COLOR_TEXT_DARK,
        spaceAfter=1.5
    )
    
    p_bullet = ParagraphStyle(
        'OnePageBullet',
        parent=p_body,
        leftIndent=10,
        firstLineIndent=-7,
        spaceAfter=1.2
    )
    
    p_h2 = ParagraphStyle(
        'OnePageH2',
        fontName='Helvetica-Bold',
        fontSize=8.0,
        leading=10.0,
        textColor=COLOR_PRIMARY,
        spaceBefore=2.5,
        spaceAfter=1.0,
        keepWithNext=True
    )
    
    one_page_styles = {
        'body': p_body,
        'body_bold': ParagraphStyle('OnePageBodyBold', parent=p_body, fontName='Helvetica-Bold'),
        'title': ParagraphStyle('OnePageTitle', fontName='Helvetica-Bold', fontSize=11.5, leading=13.5, textColor=COLOR_PRIMARY, spaceAfter=1.5),
        'subtitle': ParagraphStyle('OnePageSubtitle', fontName='Helvetica-Bold', fontSize=8.0, leading=9.8, textColor=COLOR_SECONDARY, spaceAfter=2.0),
        'h1': ParagraphStyle('OnePageH1', fontName='Helvetica-Bold', fontSize=8.0, leading=10.0, textColor=COLOR_PRIMARY, spaceBefore=1.5, spaceAfter=1.0, keepWithNext=True),
        'h2': p_h2,
        'h3': ParagraphStyle('OnePageH3', fontName='Helvetica-Bold', fontSize=7.6, leading=9.4, textColor=COLOR_PRIMARY, spaceBefore=2.0, spaceAfter=1.0, keepWithNext=True),
        'bullet': p_bullet,
        'callout': p_body,
        'table_cell': p_body,
        'table_header': p_body,
        'code_block': p_body
    }

    doc = SimpleDocTemplate(
        dest_pdf_path,
        pagesize=A4,
        leftMargin=28,
        rightMargin=28,
        topMargin=22,
        bottomMargin=22
    )

    flowables = parse_markdown_to_flowables(content, one_page_styles, is_one_page=True)
    doc.build(flowables)
    print(f"[OK] Generated One-Page Summary: {dest_pdf_path}")


def generate_individual_pdf(src_md_path, dest_pdf_path, doc_title, doc_subtitle):
    with open(src_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    styles = get_styles()
    doc = SimpleDocTemplate(
        dest_pdf_path,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_Y,
        bottomMargin=MARGIN_Y
    )

    flowables = parse_markdown_to_flowables(content, styles, is_one_page=False)
    
    def canvas_factory(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c.doc_title = f"PEVN | {doc_title}"
        c.doc_subtitle = doc_subtitle
        return c

    doc.build(flowables, canvasmaker=canvas_factory)
    print(f"[OK] Generated: {dest_pdf_path}")


def generate_consolidated_package_pdf(src_files, dest_pdf_path):
    styles = get_styles()
    doc = SimpleDocTemplate(
        dest_pdf_path,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_Y,
        bottomMargin=MARGIN_Y
    )

    story = []

    # 1. PORTADA INSTITUCIONAL
    story.append(Spacer(1, 40))
    story.append(Paragraph("PROPUESTA INDEPENDIENTE PARA EVALUACIÓN DEL SECTOR OFICIAL COLOMBIANO", ParagraphStyle('CoverRep', fontName='Helvetica-Bold', fontSize=10.5, leading=13.5, textColor=COLOR_SECONDARY, alignment=1)))
    story.append(Spacer(1, 10))
    story.append(Paragraph("PLATAFORMA EDUCATIVA VIRTUAL NACIONAL", ParagraphStyle('CoverMain', fontName='Helvetica-Bold', fontSize=24, leading=28, textColor=COLOR_PRIMARY, alignment=1)))
    story.append(Paragraph("PEVN", ParagraphStyle('CoverAcronym', fontName='Helvetica-Bold', fontSize=32, leading=38, textColor=COLOR_SECONDARY, alignment=1)))
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="60%", thickness=2.0, color=COLOR_SECONDARY, spaceBefore=5, spaceAfter=20))
    
    story.append(Paragraph("EXPEDIENTE DE PRESENTACIÓN INSTITUCIONAL", ParagraphStyle('CoverSub1', fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=COLOR_PRIMARY, alignment=1)))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Propuesta de Plataforma Educativa Virtual para el Sector Oficial Colombiano", ParagraphStyle('CoverSub2', fontName='Helvetica', fontSize=11, leading=15, textColor=COLOR_TEXT_DARK, alignment=1)))
    story.append(Paragraph("Documento Técnico, Funcional y de Sustentación (DOC-01)", ParagraphStyle('CoverSub3', fontName='Helvetica-Oblique', fontSize=10, leading=14, textColor=COLOR_TEXT_MUTED, alignment=1)))
    story.append(Spacer(1, 35))

    disclaimer_text = (
        "<b>Documento informativo y de evaluación técnica.</b><br/>"
        "No constituye aprobación, certificación ni compromiso de adopción por parte del Estado colombiano.<br/>"
        "Desarrollado bajo principios de soberanía tecnológica e ingeniería abierta (Licencia Apache 2.0 / $0 COP)."
    )
    d_para = Paragraph(disclaimer_text, ParagraphStyle('CoverBox', fontName='Helvetica', fontSize=9, leading=13, textColor=COLOR_PRIMARY, alignment=1))
    d_table = Table([[d_para]], colWidths=[PRINTABLE_WIDTH * 0.85])
    d_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_BOX),
        ('BOX', (0, 0), (-1, -1), 1.0, COLOR_SECONDARY),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(d_table)
    story.append(Spacer(1, 45))

    story.append(Paragraph("<b>Fecha de Expedición:</b> 13 de octubre de 2026", ParagraphStyle('CoverDate', fontName='Helvetica', fontSize=9.5, leading=13, textColor=COLOR_TEXT_DARK, alignment=1)))
    story.append(Paragraph("<b>Destinatarios:</b> Ministerio de Educación Nacional (MEN) · MinTIC · Secretarías de Educación", ParagraphStyle('CoverAudience', fontName='Helvetica', fontSize=9, leading=12, textColor=COLOR_TEXT_MUTED, alignment=1)))
    
    story.append(PageBreak())

    # 2. DECLARACIÓN LEGAL
    story.append(Spacer(1, 20))
    story.append(Paragraph("MARCO LEGAL Y DESCARGO INSTITUCIONAL", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=3, spaceAfter=15))
    
    legal_text = (
        "<b>CLÁUSULA DE NATURALEZA Y DESCARGO DE RESPONSABILIDAD:</b><br/><br/>"
        "PEVN es un proyecto tecnológico desarrollado de manera independiente. El presente expediente tiene carácter "
        "estrictamente informativo y técnico y se presenta como propuesta formal para evaluación por parte de las autoridades competentes. "
        "No constituye aprobación, certificación, adopción, contratación ni compromiso de implementación por parte de ninguna entidad estatal.<br/><br/>"
        "La transferencia de derechos patrimoniales y código fuente planteada se fundamenta en el modelo de software libre bajo "
        "licencia <b>Apache 2.0 ($0 COP en regalías de software)</b>, quedando cualquier despliegue operativo sujeto a los convenios "
        "interadministrativos, acuerdos de voluntades y formalizaciones que determine el Gobierno Nacional de Colombia.<br/><br/>"
        "<b>PROTECCIÓN DE DATOS DE MENORES:</b><br/>"
        "Todos los datos presentados en las demostraciones y capturas del sistema corresponden a <i>datos de demostración del entorno de pruebas, no correspondientes a un entorno productivo</i>. En cumplimiento de la Ley 1581 de 2012 y el Código de la Infancia y la Adolescencia (Ley 1098 de 2006), no se expone información personal real de menores de edad."
    )
    story.append(Paragraph(legal_text, styles['body']))
    story.append(Spacer(1, 25))

    # 3. ÍNDICE GENERAL DEL EXPEDIENTE
    story.append(Paragraph("CONTENIDO DEL EXPEDIENTE CONSOLIDADO", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=3, spaceAfter=12))
    
    index_data = [
        [Paragraph("<b>Sección</b>", styles['table_header']), Paragraph("<b>Título del Documento</b>", styles['table_header']), Paragraph("<b>Propósito y Alcance</b>", styles['table_header'])]
    ]
    for idx, item in enumerate(src_files, 1):
        index_data.append([
            Paragraph(f"<b>{idx:02d}</b>", styles['table_cell']),
            Paragraph(f"<b>{item['title']}</b>", styles['table_cell']),
            Paragraph(item['desc'], styles['table_cell'])
        ])
    t_index = Table(index_data, colWidths=[PRINTABLE_WIDTH * 0.08, PRINTABLE_WIDTH * 0.42, PRINTABLE_WIDTH * 0.50])
    t_index.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    for r in range(1, len(index_data)):
        if r % 2 == 0:
            t_index.setStyle(TableStyle([('BACKGROUND', (0, r), (-1, r), COLOR_BG_LIGHT)]))
    story.append(t_index)
    
    story.append(PageBreak())

    # 4. INCORPORACIÓN DE CADA DOCUMENTO PRINCIPAL
    for idx, item in enumerate(src_files, 1):
        story.append(Spacer(1, 60))
        story.append(Paragraph(f"SECCIÓN {idx:02d}", ParagraphStyle('SecNum', fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=COLOR_SECONDARY)))
        story.append(Paragraph(item['title'], ParagraphStyle('SecTitle', fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=COLOR_PRIMARY)))
        story.append(Paragraph(item['desc'], ParagraphStyle('SecDesc', fontName='Helvetica-Oblique', fontSize=10, leading=14, textColor=COLOR_TEXT_MUTED)))
        story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_PRIMARY, spaceBefore=8, spaceAfter=20))
        story.append(Spacer(1, 20))
        
        with open(item['path'], 'r', encoding='utf-8') as f:
            md_text = f.read()
            
        doc_flowables = parse_markdown_to_flowables(md_text, styles, is_one_page=(idx == 1))
        story.extend(doc_flowables)
        story.append(PageBreak())

    def canvas_factory(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c.suppress_header_footer_pages.add(1)
        c.doc_title = "PEVN | Expediente de Presentación Institucional"
        c.doc_subtitle = "Sector Oficial Colombiano (DOC-01)"
        return c

    doc.build(story, canvasmaker=canvas_factory)
    print(f"[OK] Generated Consolidated Package: {dest_pdf_path}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    gov_dir = os.path.join(base_dir, "docs", "government")
    pdf_dir = os.path.join(gov_dir, "pdf")
    os.makedirs(pdf_dir, exist_ok=True)

    documents = [
        {
            "id": "one_page",
            "file": "PEVN_ONE_PAGE_EXECUTIVE_SUMMARY.md",
            "pdf": "PEVN_ONE_PAGE_EXECUTIVE_SUMMARY.pdf",
            "title": "Resumen Ejecutivo de Una Página",
            "subtitle": "Síntesis para Alta Dirección",
            "desc": "Visión global condensada para ministros, viceministros y secretarios."
        },
        {
            "id": "exec_dossier",
            "file": "PEVN_EXECUTIVE_PRESENTATION_DOSSIER.md",
            "pdf": "PEVN_EXECUTIVE_PRESENTATION_DOSSIER.pdf",
            "title": "Dossier de Presentación Ejecutiva",
            "subtitle": "Expediente Integral de 20 Puntos Clave",
            "desc": "Fundamentación estratégica, modelo DANE, SIEE, portales y propuesta de piloto."
        },
        {
            "id": "current_state",
            "file": "PEVN_CURRENT_STATE_AND_LIMITATIONS.md",
            "pdf": "PEVN_CURRENT_STATE_AND_LIMITATIONS.pdf",
            "title": "Estado Actual y Registro de Limitaciones",
            "subtitle": "Matriz de Transparencia de 29 Capacidades",
            "desc": "Auditoría honesta de capacidades listas, pendientes de infraestructura y gobernanza."
        },
        {
            "id": "tech_dossier",
            "file": "PEVN_TECHNICAL_PRESENTATION_DOSSIER.md",
            "pdf": "PEVN_TECHNICAL_PRESENTATION_DOSSIER.pdf",
            "title": "Dossier de Presentación Técnica",
            "subtitle": "Arquitectura y Clasificación [A] a [G]",
            "desc": "Especificaciones de FastAPI, React, PostgreSQL, RBAC, Anti-IDOR y auditoría."
        },
        {
            "id": "evidence_matrix",
            "file": "PEVN_GOVERNMENT_EVIDENCE_MATRIX.md",
            "pdf": "PEVN_GOVERNMENT_EVIDENCE_MATRIX.pdf",
            "title": "Matriz Forense de Evidencia",
            "subtitle": "Trazabilidad de 32 Afirmaciones Mayores",
            "desc": "Mapeo determinístico de afirmaciones a código, pruebas y esquemas relacionales."
        },
        {
            "id": "runbook",
            "file": "PEVN_GOVERNMENT_DEMONSTRATION_RUNBOOK.md",
            "pdf": "PEVN_GOVERNMENT_DEMONSTRATION_RUNBOOK.pdf",
            "title": "Guion de Demostración en Vivo (Runbook)",
            "subtitle": "23 Hitos con Datos Preexistentes",
            "desc": "Secuencia operativa paso a paso basada en el Colegio Glenn Doman."
        },
        {
            "id": "qa",
            "file": "PEVN_GOVERNMENT_QA.md",
            "pdf": "PEVN_GOVERNMENT_QA.pdf",
            "title": "Banco de Preguntas y Respuestas Gubernamentales",
            "subtitle": "Respuestas Factuales a Preguntas Difíciles",
            "desc": "Respuestas a 35 interrogantes en seguridad, datos, SIMAT, escala y donación."
        },
        {
            "id": "scripts",
            "file": "PEVN_GOVERNMENT_PRESENTATION_SCRIPT.md",
            "pdf": "PEVN_GOVERNMENT_PRESENTATION_SCRIPT.pdf",
            "title": "Guiones de Presentación Oral",
            "subtitle": "Versiones de 5, 10 y 20 Minutos",
            "desc": "Estructura discursiva profesional para expositores oficiales ante comités."
        },
        {
            "id": "checklist",
            "file": "PEVN_GOVERNMENT_PRESENTATION_CHECKLIST.md",
            "pdf": "PEVN_GOVERNMENT_PRESENTATION_CHECKLIST.pdf",
            "title": "Lista de Verificación para Presentación",
            "subtitle": "Protocolo Antes, Durante y Después",
            "desc": "Guía operativa de contingencias, verificación de servicios y seguimiento institucional."
        },
        {
            "id": "donation",
            "file": "PEVN_TECHNOLOGY_DONATION_PROPOSAL.md",
            "pdf": "PEVN_TECHNOLOGY_DONATION_PROPOSAL.pdf",
            "title": "Propuesta Técnica de Donación y Transferencia",
            "subtitle": "Soberanía Tecnológica bajo Licencia Apache 2.0",
            "desc": "Bases técnicas para la cesión de activos de software y código fuente al Estado."
        },
        {
            "id": "index",
            "file": "PEVN_GOVERNMENT_DOCUMENTATION_INDEX.md",
            "pdf": "PEVN_GOVERNMENT_DOCUMENTATION_INDEX.pdf",
            "title": "Inventario General de Documentación",
            "subtitle": "Catálogo Clasificado de 26 Artefactos",
            "desc": "Índice taxonómico con clasificación por rol, madurez y categoría institucional."
        },
        {
            "id": "closing_report",
            "file": "PEVN_DOCUMENTATION_PHASE_0_1_FINAL_REPORT.md",
            "pdf": "PEVN_PHASE_0_1_FINAL_REPORT.pdf",
            "title": "Informe de Cierre de Fase 0.1",
            "subtitle": "Acta Formal de Cierre y Dictamen",
            "desc": "Balance de evidencias, datos preservados, restricciones cumplidas y condiciones."
        }
    ]

    print("=== INICIANDO GENERACIÓN DE PAQUETE PDF GUBERNAMENTAL (DOC-01) ===")

    for doc in documents:
        src = os.path.join(gov_dir, doc["file"])
        dst = os.path.join(pdf_dir, doc["pdf"])
        if not os.path.exists(src):
            print(f"[SKIP] Source markdown not found: {src}")
            continue
        if doc["id"] == "one_page":
            generate_one_page_executive_summary_pdf(src, dst)
        else:
            generate_individual_pdf(src, dst, doc["title"], doc["subtitle"])

    consolidated_pdf = os.path.join(pdf_dir, "PEVN_GOVERNMENT_PRESENTATION_PACKAGE.pdf")
    consolidated_items = []
    for doc in documents:
        src = os.path.join(gov_dir, doc["file"])
        if os.path.exists(src):
            consolidated_items.append({
                "path": src,
                "title": doc["title"],
                "desc": doc["desc"]
            })
    generate_consolidated_package_pdf(consolidated_items, consolidated_pdf)

    print("=== GENERACIÓN DE PAQUETE PDF COMPLETADA CON ÉXITO ===")


if __name__ == "__main__":
    main()
