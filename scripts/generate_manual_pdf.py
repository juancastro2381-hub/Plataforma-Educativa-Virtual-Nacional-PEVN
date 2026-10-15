#!/usr/bin/env python3
"""
PEVN — Generador del Manual de Usuario en PDF (DOC-01)
Genera el documento descargable docs/manual/pdf/PEVN_INTERACTIVE_USER_MANUAL.pdf
incorporando diseño institucional A4, dos pasadas de lienzo (Página X de Y)
y capturas de pantalla auténticas embebidas.
"""

import os
import re
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Image
)
from reportlab.pdfgen import canvas
from PIL import Image as PILImage

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 40.0
MARGIN_Y = 45.0
PRINTABLE_WIDTH = PAGE_WIDTH - (2 * MARGIN_X)

COLOR_PRIMARY = colors.HexColor("#1A365D")
COLOR_SECONDARY = colors.HexColor("#2B6CB0")
COLOR_TEXT_DARK = colors.HexColor("#2D3748")
COLOR_TEXT_MUTED = colors.HexColor("#718096")
COLOR_BG_LIGHT = colors.HexColor("#F7FAFC")
COLOR_BG_BOX = colors.HexColor("#EDF2F7")
COLOR_BORDER = colors.HexColor("#CBD5E0")
COLOR_WHITE = colors.HexColor("#FFFFFF")
COLOR_ACCENT = colors.HexColor("#319795")


class ManualNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.suppress_header_footer_pages = {1}
        self.doc_title = "PEVN | MANUAL DE USUARIO Y GUÍA OPERATIVA"
        self.doc_subtitle = "Sector Oficial Colombiano (DOC-01)"

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
        footer_text = "PEVN — Manual Interactivo de Usuario · Sector Oficial Colombiano"
        page_text = f"Página {self._pageNumber} de {total_pages}"
        self.drawString(MARGIN_X, 24, footer_text)
        self.drawRightString(PAGE_WIDTH - MARGIN_X, 24, page_text)
        self.restoreState()


def get_manual_styles():
    styles = getSampleStyleSheet()
    
    body = ParagraphStyle(
        'ManualBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=COLOR_TEXT_DARK,
        spaceAfter=6
    )
    
    title = ParagraphStyle(
        'ManualTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=COLOR_PRIMARY,
        spaceAfter=10
    )
    
    h1 = ParagraphStyle(
        'ManualH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=COLOR_PRIMARY,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    h2 = ParagraphStyle(
        'ManualH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=COLOR_SECONDARY,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    bullet = ParagraphStyle(
        'ManualBullet',
        parent=body,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )
    
    callout = ParagraphStyle(
        'ManualCallout',
        parent=body,
        fontSize=8.5,
        leading=11.5,
        textColor=COLOR_PRIMARY
    )
    
    caption = ParagraphStyle(
        'ManualCaption',
        parent=body,
        fontSize=8,
        leading=10.5,
        textColor=COLOR_TEXT_MUTED,
        alignment=1
    )

    table_cell = ParagraphStyle(
        'ManualTableCell',
        parent=body,
        fontSize=8,
        leading=10,
        spaceAfter=0
    )
    
    table_header = ParagraphStyle(
        'ManualTableHeader',
        parent=table_cell,
        fontName='Helvetica-Bold',
        textColor=COLOR_WHITE
    )

    return {
        'body': body,
        'title': title,
        'h1': h1,
        'h2': h2,
        'bullet': bullet,
        'callout': callout,
        'caption': caption,
        'table_cell': table_cell,
        'table_header': table_header
    }


def make_callout(text, styles, width=PRINTABLE_WIDTH):
    p = Paragraph(text, styles['callout'])
    t = Table([[p]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_BOX),
        ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LINELEFT', (0, 0), (0, 0), 3.0, COLOR_SECONDARY),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t


def make_screenshot_flowable(img_path, caption_text, route_text, styles, max_h=285):
    if not os.path.exists(img_path):
        return Spacer(1, 1)

    with PILImage.open(img_path) as pil_img:
        orig_w, orig_h = pil_img.size

    aspect = orig_h / orig_w
    pad_x = 4.0
    inner_w = PRINTABLE_WIDTH - (2 * pad_x)
    target_w = inner_w
    target_h = inner_w * aspect
    
    # Limitar altura máxima proporcionalmente si excede el límite vertical para la página
    if max_h is not None and target_h > max_h:
        target_h = max_h
        target_w = target_h / aspect

    img_flowable = Image(img_path, width=target_w, height=target_h)
    
    cap_para = Paragraph(f"<b>{caption_text}</b> · <i>{route_text}</i>", styles['caption'])
    
    # El contenedor de tabla SIEMPRE abarca el 100% del ancho imprimible (márgenes alineados)
    table = Table([[img_flowable], [cap_para]], colWidths=[PRINTABLE_WIDTH])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_LIGHT),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), pad_x),
        ('RIGHTPADDING', (0, 0), (-1, -1), pad_x),
        ('TOPPADDING', (0, 1), (-1, 1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 5),
    ]))
    
    return KeepTogether([table, Spacer(1, 8)])



def build_manual_pdf():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    manual_dir = os.path.join(base_dir, "docs", "manual")
    pdf_dir = os.path.join(manual_dir, "pdf")
    img_dir = os.path.join(manual_dir, "assets", "screenshots")
    os.makedirs(pdf_dir, exist_ok=True)

    dest_pdf_path = os.path.join(pdf_dir, "PEVN_INTERACTIVE_USER_MANUAL.pdf")

    doc = SimpleDocTemplate(
        dest_pdf_path,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_Y,
        bottomMargin=MARGIN_Y
    )

    styles = get_manual_styles()
    story = []

    # =========================================================================
    # PORTADA
    # =========================================================================
    story.append(Spacer(1, 50))
    story.append(Paragraph("MANUAL OFICIAL DE USUARIO Y GUÍA OPERATIVA", ParagraphStyle('Cov1', fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=COLOR_SECONDARY, alignment=1)))
    story.append(Spacer(1, 10))
    story.append(Paragraph("PLATAFORMA EDUCATIVA VIRTUAL NACIONAL", ParagraphStyle('Cov2', fontName='Helvetica-Bold', fontSize=24, leading=28, textColor=COLOR_PRIMARY, alignment=1)))
    story.append(Paragraph("PEVN", ParagraphStyle('Cov3', fontName='Helvetica-Bold', fontSize=32, leading=38, textColor=COLOR_SECONDARY, alignment=1)))
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="60%", thickness=2.0, color=COLOR_SECONDARY, spaceBefore=5, spaceAfter=20))
    story.append(Paragraph("Guía Integral de Roles, Módulos Pedagógicos, Administrativos y de Convivencia", ParagraphStyle('Cov4', fontName='Helvetica', fontSize=11, leading=15, textColor=COLOR_TEXT_DARK, alignment=1)))
    story.append(Paragraph("Para Rectores, Docentes, Familias y Autoridades Territoriales", ParagraphStyle('Cov5', fontName='Helvetica-Oblique', fontSize=10, leading=14, textColor=COLOR_TEXT_MUTED, alignment=1)))
    story.append(Spacer(1, 40))

    disclaimer = (
        "<b>Documento técnico de acompañamiento operativo.</b><br/>"
        "Describe las funciones reales, flujos y perfiles implementados en la plataforma PEVN.<br/>"
        "Desarrollado bajo principios de soberanía tecnológica e ingeniería pública (Licencia Apache 2.0)."
    )
    d_table = Table([[Paragraph(disclaimer, ParagraphStyle('CovD', fontName='Helvetica', fontSize=8.5, leading=12, textColor=COLOR_PRIMARY, alignment=1))]], colWidths=[PRINTABLE_WIDTH * 0.85])
    d_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_BOX),
        ('BOX', (0, 0), (-1, -1), 1.0, COLOR_SECONDARY),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(d_table)
    story.append(Spacer(1, 50))
    story.append(Paragraph("<b>Fecha de Publicación:</b> 13 de octubre de 2026 · Versión 1.0 (DOC-01)", ParagraphStyle('CovDate', fontName='Helvetica', fontSize=9, leading=12, textColor=COLOR_TEXT_DARK, alignment=1)))
    story.append(PageBreak())

    # =========================================================================
    # CAPÍTULO 1: INTRODUCCIÓN Y PRIMEROS PASOS
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 01: INTRODUCCIÓN Y PRIMEROS PASOS", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "La Plataforma Educativa Virtual Nacional (PEVN) es una solución integral diseñada para el sector oficial colombiano. "
        "Opera como una Aplicación Web Progresiva (PWA) accesible desde cualquier navegador moderno (Chrome, Firefox, Edge, Safari) "
        "en computadores, tabletas y teléfonos inteligentes.",
        styles['body']
    ))
    story.append(make_callout(
        "<b>Requisitos de Conectividad:</b> Ancho de banda mínimo recomendado de 2 Mbps por usuario concurrente. "
        "Cero instalación de ejecutables locales ni dependencias de software privativo.", styles
    ))
    story.append(Spacer(1, 6))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "01_portal_inicio.png"), "Figura 1.1: Portal de Bienvenida Institucional", "Ruta: /", styles))
    story.append(Paragraph(
        "<b>Flujo de Inicio de Sesión y Recuperación:</b><br/>"
        "• <b>Autenticación Segura:</b> Ingrese su usuario/correo institucional y contraseña cifrada con Argon2id.<br/>"
        "• <b>Tokens Efímeros:</b> Los tokens JWT residen exclusivamente en la memoria volátil de React (mitigación frente a XSS).<br/>"
        "• <b>Recuperación de Contraseña:</b> Mediante el enlace <i>'¿Olvidó su contraseña?'</i>, el sistema genera un token de un solo uso de 15 minutos para restaurar el acceso sin exponer claves.",
        styles['body']
    ))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "02_autenticacion_login.png"), "Figura 1.2: Pantalla de Autenticación Segura", "Ruta: /login", styles))
    story.append(PageBreak())

    # =========================================================================
    # CAPÍTULO 2 & 3: GOBERNANZA NACIONAL Y MUNICIPAL
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 02: GOBERNANZA TERRITORIAL Y CATÁLOGO DANE", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "El Administrador Nacional (<code>national_admin</code>) y el Administrador Departamental (<code>department_admin</code>) "
        "supervisan el catálogo oficial integrado de Colombia: <b>18,031 Establecimientos Educativos y 51,521 Sedes Físicas</b>, "
        "provenientes de los conjuntos de datos abiertos DUE 2024 (<code>cfw5-qzt5</code>) y Sedes (<code>x5ay-984n</code>).",
        styles['body']
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("CAPÍTULO 03: ADMINISTRACIÓN MUNICIPAL E INVITACIONES", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "El Administrador Municipal (<code>municipality_admin</code>) gestiona los colegios de su municipio oficial. "
        "Posee la atribución canónica de emitir invitaciones tokenizadas seguras para los Rectores de su jurisdicción.",
        styles['body']
    ))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "04_administracion_municipal_invitacion.png"), "Figura 3.1: Consola de Aprovisionamiento e Invitación Municipal", "Ruta: /admin/municipality-admins", styles))
    story.append(PageBreak())

    # =========================================================================
    # CAPÍTULO 4 & 5: RECTORÍA Y COORDINACIÓN ACADÉMICA
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 04: GESTIÓN DIRECTIVA Y RECTORÍA", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "El Rector gestiona el calendario escolar, sedes principales y anexas, y formaliza los cierres y sellados de períodos SIEE. "
        "Una vez sellado un período, queda inmutablemente protegido frente a modificaciones no auditadas.",
        styles['body']
    ))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "05_rectoria_dashboard.png"), "Figura 4.1: Panel Principal de Rectoría", "Ruta: /dashboard", styles))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "06_gestion_academica_periodos.png"), "Figura 4.2: Configuración de Períodos Académicos SIEE", "Ruta: /academic?tab=periods", styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("CAPÍTULO 05: COORDINACIÓN ACADÉMICA Y PADRÓN SIMAT", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "La coordinación vincula estudiantes (compatibles con SIMAT), grupos y asignaciones docentes con control de cupos máximos.",
        styles['body']
    ))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "07_gestion_academica_estudiantes_simat.png"), "Figura 5.1: Padrón Institucional de Estudiantes", "Ruta: /academic?tab=students", styles))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "08_gestion_academica_acudientes.png"), "Figura 5.2: Registro de Acudientes y Vinculación Familiar", "Ruta: /academic?tab=guardians", styles))
    story.append(PageBreak())

    # =========================================================================
    # CAPÍTULO 6: PORTAL DEL DOCENTE
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 06: PORTAL DEL DOCENTE DE AULA", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "El Portal Docente (<code>/teacher</code>) organiza la jornada pedagógica bajo el principio de <i>Teacher Scope</i>. "
        "El docente administra sus planillas de notas SIEE, asistencia diaria, creación de tareas y unidades didácticas.",
        styles['body']
    ))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "09_portal_docente_dashboard.png"), "Figura 6.1: Consola de Trabajo del Docente", "Ruta: /teacher?tab=dashboard", styles))
    story.append(Paragraph(
        "<b>Planeación Curricular y Didáctica:</b> Los profesores estructuran sus unidades articuladas con los "
        "Derechos Básicos de Aprendizaje (DBA) y los estándares básicos del Ministerio de Educación Nacional.",
        styles['body']
    ))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "10_portal_docente_planeacion.png"), "Figura 6.2: Módulo de Planeación Curricular Docente", "Ruta: /teacher?tab=planning", styles))
    story.append(PageBreak())

    # =========================================================================
    # CAPÍTULO 7 & 8: PORTAL ESTUDIANTE Y FAMILIAR
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 07: PORTAL DEL ESTUDIANTE", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "El estudiante accede a sus materias, calificaciones del período actual, observador personal, periódico escolar "
        "y realiza la entrega digital de evidencias de tareas con cálculo determinístico de puntualidad UTC.",
        styles['body']
    ))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "13_portal_estudiante_entrega_tarea.png"), "Figura 7.1: Modal de Entrega de Tareas Escolares", "Ruta: /student?tab=tasks", styles))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "11_portal_estudiante_comunicados.png"), "Figura 7.2: Circulares con Acuse de Recibo", "Ruta: /student?tab=communications", styles))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "12_portal_estudiante_noticias.png"), "Figura 7.3: Periódico Escolar Institucional", "Ruta: /student?tab=news", styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("CAPÍTULO 08: PORTAL FAMILIAR Y ACUDIENTES", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "El Portal del Acudiente (<code>/guardian</code>) implementa la Identidad Desacoplada y un <b>selector dinámico de hijos</b> "
        "para consultar calificaciones, asistencias y confirmar acuses de recibo electrónico con registro de timestamp UTC e IP.",
        styles['body']
    ))
    story.append(PageBreak())

    # =========================================================================
    # CAPÍTULO 9 & 10: DIAGNÓSTICO Y SIEE
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 09: DIAGNÓSTICO OPERACIONAL Y AUDITORÍA", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "La consola <code>/operations/tenant-diagnostics</code> permite a SuperAdmin y Administrador Nacional evaluar la salud del colegio, "
        "verificar su código DANE y consultar la tabla inmutable <code>audit_logs</code> con censura de datos sensibles (<code>[REDACTED]</code>).",
        styles['body']
    ))
    story.append(make_screenshot_flowable(os.path.join(img_dir, "03_operaciones_diagnostico_inquilino.png"), "Figura 9.1: Consola de Diagnóstico de Inquilinos", "Ruta: /operations/tenant-diagnostics", styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("CAPÍTULO 10: SISTEMA SIEE (DECRETO 1290 DE 2009)", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))
    
    siee_table_data = [
        [Paragraph("<b>Escala Nacional MEN</b>", styles['table_header']), Paragraph("<b>Rango Numérico</b>", styles['table_header']), Paragraph("<b>Criterio Institucional</b>", styles['table_header'])],
        [Paragraph("Desempeño Superior", styles['table_cell']), Paragraph("4.60 a 5.00", styles['table_cell']), Paragraph("Supera con excelencia los objetivos propuestos.", styles['table_cell'])],
        [Paragraph("Desempeño Alto", styles['table_cell']), Paragraph("4.00 a 4.59", styles['table_cell']), Paragraph("Alcanza la totalidad de los desempeños esperados.", styles['table_cell'])],
        [Paragraph("Desempeño Básico", styles['table_cell']), Paragraph("3.00 a 3.99", styles['table_cell']), Paragraph("Alcanza los desempeños mínimos necesarios (Aprobatorio).", styles['table_cell'])],
        [Paragraph("Desempeño Bajo", styles['table_cell']), Paragraph("1.00 a 2.99", styles['table_cell']), Paragraph("No alcanza desempeños mínimos; requiere plan de mejoramiento.", styles['table_cell'])],
    ]
    t_siee = Table(siee_table_data, colWidths=[PRINTABLE_WIDTH * 0.28, PRINTABLE_WIDTH * 0.22, PRINTABLE_WIDTH * 0.50])
    t_siee.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_siee)
    story.append(Spacer(1, 10))

    # =========================================================================
    # CAPÍTULO 11 & 12: CONVIVENCIA Y PREGUNTAS FRECUENTES
    # =========================================================================
    story.append(Paragraph("CAPÍTULO 11: CONVIVENCIA ESCOLAR (LEY 1620 DE 2013)", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "El módulo de Convivencia Escolar tipifica situaciones Tipos I (conflictos cotidianos), Tipo II (acoso escolar o agresión) "
        "y Tipo III (presuntos delitos penales/sexuales), registrando descargos, medidas pedagógicas, acuerdos y reserva legal absoluta.",
        styles['body']
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("CAPÍTULO 12: PREGUNTAS FRECUENTES Y SOPORTE", styles['h1']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "• <b>¿Cómo cambio de hijo en el portal familiar?</b> Utilice el selector de estudiantes ubicado en el encabezado superior.<br/>"
        "• <b>¿Por qué no veo materias como docente?</b> Verifique que su carga académica haya sido vinculada en Coordinación.<br/>"
        "• <b>¿Qué sucede si cierro el período SIEE?</b> Las notas quedan selladas e inmutables; solo el Rector puede autorizar reaperturas auditadas.",
        styles['body']
    ))

    doc.build(story, canvasmaker=ManualNumberedCanvas)
    print(f"[OK] Generated Manual PDF: {dest_pdf_path}")


if __name__ == "__main__":
    build_manual_pdf()
