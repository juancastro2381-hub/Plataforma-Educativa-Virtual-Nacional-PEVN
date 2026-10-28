#!/usr/bin/env python3
"""
PEVN — Generador de la Presentación Institucional en PDF (22 Diapositivas Widescreen 16:9)
Genera docs/government/pdf/PEVN_PRESENTACION_INSTITUCIONAL_MEN.pdf
utilizando ReportLab canvas y layout de presentación en formato apaisado.
"""

import os
import sys
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph

# Dimensiones 16:9 Widescreen en puntos (13.333 in x 7.5 in = 960 pt x 540 pt)
SLIDE_W = 960.0
SLIDE_H = 540.0

# Paleta de Colores
NAVY = colors.HexColor("#0F2942")
BLUE = colors.HexColor("#1D68A7")
GOLD = colors.HexColor("#C59B27")
DARK_GRAY = colors.HexColor("#1E293B")
MUTED = colors.HexColor("#64748B")
LIGHT_BG = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#CBD5E1")
WHITE = colors.HexColor("#FFFFFF")
GREEN = colors.HexColor("#10955D")
AMBER = colors.HexColor("#D97706")
PURPLE = colors.HexColor("#6D28D9")


class PresentationPDF:
    def __init__(self, filename):
        self.filename = filename
        self.c = canvas.Canvas(filename, pagesize=(SLIDE_W, SLIDE_H))
        self.styles = getSampleStyleSheet()
        self._init_styles()

    def _init_styles(self):
        self.style_body = ParagraphStyle(
            'SlideBody',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=13.5,
            textColor=DARK_GRAY
        )
        self.style_card_title = ParagraphStyle(
            'CardTitle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=15,
            textColor=NAVY
        )

    def draw_header(self, title_text, category="PLATAFORMA EDUCATIVA VIRTUAL NACIONAL (PEVN) — OFICINA DE TECNOLOGÍA (MEN)"):
        # Category
        self.c.setFont("Helvetica-Bold", 8.5)
        self.c.setFillColor(BLUE)
        self.c.drawString(50, SLIDE_H - 30, category.upper())

        # Title
        self.c.setFont("Helvetica-Bold", 17)
        self.c.setFillColor(NAVY)
        self.c.drawString(50, SLIDE_H - 54, title_text)

        # Golden line
        self.c.setStrokeColor(GOLD)
        self.c.setLineWidth(1.5)
        self.c.line(50, SLIDE_H - 64, SLIDE_W - 50, SLIDE_H - 64)

    def draw_footer(self, page_num, total_pages=22):
        self.c.setFont("Helvetica", 7.5)
        self.c.setFillColor(MUTED)
        self.c.drawString(50, 20, "PEVN — Documento Técnico Institucional de Trabajo | No representa adopción ni certificación previa del MEN")
        self.c.drawRightString(SLIDE_W - 50, 20, f"{page_num} / {total_pages}")
        self.c.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.c.setLineWidth(0.5)
        self.c.line(50, 32, SLIDE_W - 50, 32)

    def draw_card(self, x, y, w, h, title, items, bg=LIGHT_BG, border=BORDER, title_color=NAVY):
        # Card background
        self.c.saveState()
        self.c.setFillColor(bg)
        self.c.setStrokeColor(border)
        self.c.setLineWidth(0.8)
        self.c.roundRect(x, y, w, h, 6, fill=1, stroke=1)

        # Title
        curr_y = y + h - 22
        if title:
            self.c.setFont("Helvetica-Bold", 11.5)
            self.c.setFillColor(title_color)
            self.c.drawString(x + 14, curr_y, title)
            curr_y -= 14

        # Items
        for item in items:
            # We format markdown bold **text** to HTML <b>text</b> for ReportLab Paragraph
            html_text = item
            if "**" in html_text:
                parts = html_text.split("**")
                res = []
                for idx, part in enumerate(parts):
                    if not part:
                        continue
                    if idx % 2 == 1:
                        res.append(f"<b><font color='{NAVY.hexval()}'>{part}</font></b>")
                    else:
                        res.append(part)
                html_text = "".join(res)

            p = Paragraph(f"• {html_text}", self.style_body)
            pw, ph = p.wrap(w - 28, curr_y - y - 10)
            if curr_y - ph < y + 8:
                break
            p.drawOn(self.c, x + 14, curr_y - ph)
            curr_y -= (ph + 6)

        self.c.restoreState()

    def add_cover(self, page_num=1):
        # Dark navy background
        self.c.saveState()
        self.c.setFillColor(NAVY)
        self.c.rect(0, 0, SLIDE_W, SLIDE_H, fill=1, stroke=0)

        # Inner container
        self.c.setFillColor(colors.HexColor("#163554"))
        self.c.setStrokeColor(GOLD)
        self.c.setLineWidth(1.5)
        self.c.roundRect(50, 45, SLIDE_W - 100, SLIDE_H - 90, 8, fill=1, stroke=1)

        # Texts
        self.c.setFont("Helvetica-Bold", 10.5)
        self.c.setFillColor(GOLD)
        self.c.drawString(85, SLIDE_H - 105, "REPÚBLICA DE COLOMBIA • SECTOR EDUCATIVO OFICIAL")

        self.c.setFont("Helvetica-Bold", 26)
        self.c.setFillColor(WHITE)
        self.c.drawString(85, SLIDE_H - 148, "Plataforma Educativa Virtual Nacional (PEVN)")

        self.c.setFont("Helvetica", 15)
        self.c.setFillColor(colors.HexColor("#BED7F0"))
        self.c.drawString(85, SLIDE_H - 180, "Presentación Institucional y Dossier Técnico de Ingeniería")

        self.c.setFont("Helvetica", 11.5)
        self.c.setFillColor(WHITE)
        self.c.drawString(85, SLIDE_H - 225, "Sesión de Trabajo con la Oficina de Tecnología y Sistemas de Información")
        self.c.drawString(85, SLIDE_H - 245, "Ministerio de Educación Nacional (MEN)")

        # Divider
        self.c.setStrokeColor(colors.HexColor("#2B6CB0"))
        self.c.setLineWidth(0.8)
        self.c.line(85, SLIDE_H - 275, SLIDE_W - 85, SLIDE_H - 275)

        # Metadata
        self.c.setFont("Helvetica", 9)
        self.c.setFillColor(colors.HexColor("#A0B9D2"))
        self.c.drawString(85, 105, "Autor / Iniciativa Técnica: Juan Carlos Castro Narváez | Versión: 1.0-FINAL-MEN | Octubre 2026")
        self.c.drawString(85, 85, "Nota: Iniciativa técnica independiente. No constituye aprobación, contrato ni certificación previa del MEN.")

        self.c.restoreState()
        self.c.showPage()

    def add_closing(self, page_num=22):
        self.c.saveState()
        self.c.setFillColor(NAVY)
        self.c.rect(0, 0, SLIDE_W, SLIDE_H, fill=1, stroke=0)

        self.c.setFillColor(colors.HexColor("#163554"))
        self.c.setStrokeColor(GOLD)
        self.c.setLineWidth(1.5)
        self.c.roundRect(50, 45, SLIDE_W - 100, SLIDE_H - 90, 8, fill=1, stroke=1)

        self.c.setFont("Helvetica-Bold", 10.5)
        self.c.setFillColor(GOLD)
        self.c.drawString(85, SLIDE_H - 110, "COMPROMISO CON LA EDUCACIÓN PÚBLICA DE COLOMBIA")

        self.c.setFont("Helvetica-Bold", 24)
        self.c.setFillColor(WHITE)
        self.c.drawString(85, SLIDE_H - 150, "Plataforma Educativa Virtual Nacional (PEVN)")

        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(colors.HexColor("#BED7F0"))
        self.c.drawString(85, SLIDE_H - 180, "Un Bien Público Digital al Servicio de los Territorios y la Comunidad Educativa")

        self.c.setFont("Helvetica-Bold", 11)
        self.c.setFillColor(WHITE)
        self.c.drawString(85, SLIDE_H - 240, "Liderazgo Técnico y Contacto Institucional:")
        self.c.setFont("Helvetica", 10.5)
        self.c.setFillColor(colors.HexColor("#E2E8F0"))
        self.c.drawString(85, SLIDE_H - 260, "Juan Carlos Castro Narváez — Desarrollador Principal y Consultor de Transformación Digital")
        self.c.drawString(85, SLIDE_H - 285, "Octubre 2026 — Bogotá D.C., Colombia")

        self.c.restoreState()
        self.c.showPage()


def build_pdf_presentation(output_path):
    p = PresentationPDF(output_path)

    # Slide 1: Cover
    p.add_cover(1)

    # Slide 2: Resumen Ejecutivo
    p.draw_header("Resumen Ejecutivo de la Iniciativa PEVN")
    p.draw_footer(2)
    p.draw_card(50, 50, 265, 410, "Propósito Público", [
        "**Soberanía Tecnológica:** Ecosistema abierto concebido para superar la fragmentación de software y el cobro recurrente por estudiante en colegios oficiales.",
        "**Equidad Territorial:** Diseñado para brindar capacidades de gestión de calidad equivalente a instituciones rurales y urbanas.",
        "**Bien Público Digital:** Código fuente auditable bajo licencia abierta (Apache 2.0 / AGPLv3)."
    ])
    p.draw_card(345, 50, 270, 410, "Solución Técnica", [
        "**Arquitectura Desacoplada:** Frontend SPA en React 18/TypeScript (Vite) + Backend asíncrono en FastAPI (Python 3.12/3.14).",
        "**Persistencia y Sesiones:** PostgreSQL 15 con aislamiento multi-tenant forzado + Redis 7 para revocación instantánea de JWT.",
        "**Catálogo DUE 2024 Precargado:** 1,122 municipios (DIVIPOLA), 18,031 colegios y 51,521 sedes de referencia oficial para evitar digitación manual (32 instituciones de prueba en capa operativa)."
    ])
    p.draw_card(645, 50, 265, 410, "Evidencia y Validación", [
        "**Censo Dinámico (R8):** 747 pruebas recolectadas en 72 archivos de prueba.",
        "**Pruebas Ejecutadas:** 57 pruebas focalizadas con 100% PASS en ciclo acotado (teardown seguro, analizador y aprovisionamiento; 690 no ejecutadas en ciclo).",
        "**Ruta hacia Piloto:** Propuesta de trabajo en 4 fases con compuertas de decisión técnica (Decision Gates) bajo rectoría del MEN."
    ])
    p.c.showPage()

    # Slide 3: Diagnostico del Problema
    p.draw_header("Diagnóstico del Problema en el Sector Oficial")
    p.draw_footer(3)
    p.draw_card(50, 260, 415, 200, "1. Fragmentación y Silos de Datos", [
        "**Planillas Desarticuladas:** Notas y asistencia llevadas en hojas de cálculo locales o libretas en papel sin consolidación central.",
        "**Riesgo de Pérdida:** Falta de respaldos automáticos y trazabilidad de cambios en notas ante quejas o auditorías."
    ])
    p.draw_card(495, 260, 415, 200, "2. Dependencia Financiera Privativa", [
        "**Cobro por Licenciamiento:** Sistemas comerciales que cobran costos recurrentes por alumno, asfixiando presupuestos territoriales.",
        "**Bloqueo de Proveedor (Vendor Lock-in):** Dificultad extrema para extraer históricos de calificaciones al terminar contratos."
    ])
    p.draw_card(50, 50, 415, 195, "3. Brecha de Conectividad Rural", [
        "**Sistemas Comerciales Pesados:** Plataformas saturadas de librerías de rastreo y fuentes externas que colapsan con enlaces rurales de 2 Mbps.",
        "**Inequidad Operativa:** Sedes rurales apartadas quedan excluidas del seguimiento digital pedagógico."
    ])
    p.draw_card(495, 50, 415, 195, "4. Soberanía y Gobernanza de Datos", [
        "**Datos de Menores en Nubes Foráneas:** Información confidencial de niños y adolescentes tratada sin supervisión directa del Estado.",
        "**Desalineación Normativa:** Incompatibilidad con Ley 1581 de 2012 y lineamientos de Gobierno Digital."
    ])
    p.c.showPage()

    # Slide 4: Visión, Misión y Valor Público
    p.draw_header("Visión, Misión y Creación de Valor Público")
    p.draw_footer(4)
    p.draw_card(50, 50, 415, 410, "Misión y Visión Estratégica", [
        "**Misión:** Proveer al sistema educativo oficial de Colombia una infraestructura digital soberana, auditable y de alto rendimiento que unifique los procesos directivos, pedagógicos y comunitarios.",
        "**Visión:** Consolidar a PEVN como el Bien Público Digital de referencia para la educación pública nacional, reduciendo a cero el costo marginal de gestión escolar por estudiante.",
        "**Alineación Institucional:** Armonizado con las metas del Plan Nacional de Desarrollo en materia de transformación digital educativa y cierre de brechas urbano-rurales."
    ])
    p.draw_card(495, 50, 415, 410, "Dimensiones de Valor Público", [
        "**Ahorro Presupuestal Sostenible:** Eliminación de pagos recurrentes de licenciamiento privativo en Secretarías de Educación.",
        "**Soberanía de Datos Nacional:** Residencia de datos en centros de datos del Estado o nubes gubernamentales bajo Ley 1581 de 2012.",
        "**Continuidad y Resiliencia Escolar:** Capacidad de mantener seguimiento evaluativo y comunicación durante emergencias o cierres viales.",
        "**Transparencia y Cero Fraude:** Registro inmutable de cada calificación con marca de tiempo UTC y usuario responsable."
    ])
    p.c.showPage()

    # Slide 5: Alcance del Proyecto
    p.draw_header("Alcance del Proyecto: Inclusiones y Exclusiones Taxativas")
    p.draw_footer(5)
    p.draw_card(50, 50, 415, 410, "Capacidades Incluidas en el Alcance Actual", [
        "**Aprovisionamiento Territorial e Institucional:** Creación de sedes bajo códigos oficiales DANE.",
        "**Activación Criptográfica de Rectores:** Invitaciones con token firmado HMAC y expiración de 72 horas.",
        "**Parametrización Curricular:** Años lectivos, periodos, grados, grupos y asignación académica docente.",
        "**Gestión Evaluativa:** Planilla interactiva de notas con ponderación porcentual y control de asistencia.",
        "**Portales de Autoservicio:** Vistas seguras para Estudiantes y Acudientes protegidas contra IDOR.",
        "**Orquestación de Aulas Virtuales:** Cliente API para salas BigBlueButton con tokens seguros."
    ])
    p.draw_card(495, 50, 415, 410, "Exclusiones Taxativas (Non-Goals)", [
        "**No es un Sustituto Legal del SIMAT:** No reemplaza la potestad del MEN sobre el registro oficial de matrícula; actúa como plataforma operativa complementaria.",
        "**No es Proveedor de Infraestructura Física:** Optimiza el tráfico de red, pero no suministra antenas, enlaces satelitales ni fibra óptica.",
        "**No es Entidad de Certificación Académica:** La validez de certificados y títulos corresponde por ley a cada Institución y Secretaría de Educación.",
        "**No Aloja Clúster WebRTC Embebido:** La transmisión multimedia en vivo requiere la infraestructura BigBlueButton externa descrita."
    ], bg=colors.HexColor("#FEF2F2"), border=colors.HexColor("#FCA5A5"), title_color=colors.HexColor("#991B1B"))
    p.c.showPage()

    # Slide 6: Jerarquia de Roles
    p.draw_header("Usuarios, Jerarquía RBAC (9 Canónicos / 11 en BD) y Delegación")
    p.draw_footer(6)
    p.draw_card(50, 50, 440, 410, "9 Arquetipos Canónicos y 2 Alias Técnicos", [
        "**[100] superadmin:** Operador de infraestructura técnica global.",
        "**[90] national_admin:** Administrador Nacional MEN y auditoría central.",
        "**[80] department_admin:** Secretaría de Educación Departamental.",
        "**[70] municipality_admin:** Secretaría de Educación Municipal.",
        "**[60] rector:** Máxima autoridad directiva (*alias compatibilidad: institution_admin*).",
        "**[50] coordinator:** Coordinador Académico o de Sede (*alias compatibilidad: academic_coordinator*).",
        "**[30] teacher:** Docente de área y registro evaluativo.",
        "**[10] student:** Estudiante matriculado (SIMAT).",
        "**[10] guardian:** Acudiente / Tutor legal familiar."
    ])
    p.draw_card(510, 50, 400, 410, "Fronteras de Autoridad y Excepción Aprobada", [
        "**Prevención de Escalamiento Vertical:** Ningún usuario puede asignar un rol de nivel igual o superior al suyo en la jerarquía.",
        "**Aislamiento de Ámbito:** Los administradores territoriales solo operan sobre municipios o instituciones de su jurisdicción DANE.",
        "**Excepción Canónica de Coordinador:** Por regla general, los coordinadores no crean usuarios. Sin embargo, en la operación escolar colombiana el Rector delega la matrícula y asignación docente.",
        "**Política de Delegación:** PEVN implementa la bandera booleana `coordinator_delegated_provisioning_enabled`. Falla cerrada por defecto (`False`, HTTP 403). Solo si el Rector la habilita, el coordinador puede aprovisionar docentes o estudiantes."
    ])
    p.c.showPage()

    # Slide 7: Arquitectura Funcional
    p.draw_header("Arquitectura Funcional y Módulos Principales")
    p.draw_footer(7)
    p.draw_card(50, 260, 265, 200, "Módulo Territorial / DANE", [
        "**Codificación Nacional:** Integración nativa de DIVIPOLA y Directorio DUE.",
        "**Aislamiento:** Filtrado multi-tenant estricto desde la raíz administrativa."
    ])
    p.draw_card(345, 260, 270, 200, "Aprovisionamiento Directivo", [
        "**Invitaciones Criptográficas:** Tokens temporales con firma HMAC de 72h.",
        "**Activación Autónoma:** El rector valida cédula y activa credenciales seguras."
    ])
    p.draw_card(645, 260, 265, 200, "Gestión Curricular", [
        "**Estructura Académica:** Sedes, jornadas, grados, grupos y asignaturas.",
        "**Carga Docente:** Vinculación de profesores a asignaturas y cursos."
    ])
    p.draw_card(50, 50, 265, 195, "Evaluación y Asistencia", [
        "**Planilla Docente:** Notas numéricas (1.0-5.0), ponderación y faltas.",
        "**Consolidación:** Cálculo automático de promedios de periodo."
    ])
    p.draw_card(345, 50, 270, 195, "Portales Estudiante / Familia", [
        "**Consultas Seguras:** Acceso a boletín y faltas protegido anti-IDOR.",
        "**Acompañamiento:** Visualización de observaciones pedagógicas."
    ])
    p.draw_card(645, 50, 265, 195, "Aulas Virtuales y Auditoría", [
        "**BigBlueButton:** Creación de salas seguras con clave de moderador.",
        "**Pista Forense:** Registro inmutable de transacciones con IP y UTC."
    ])
    p.c.showPage()

    # Slide 8: Flujos Educativos
    p.draw_header("Flujos Educativos Verificados en Código Fuente")
    p.draw_footer(8)
    p.draw_card(50, 50, 265, 410, "1. Aprovisionamiento Institucional", [
        "**1. Solicitud:** Secretaría ingresa código DANE y correo del Rector.",
        "**2. Token Seguro:** Backend genera token UUID v4 firmado con HMAC.",
        "**3. Notificación:** Se despacha enlace con vigencia de 72 horas.",
        "**4. Activación:** Rector valida documento de identidad y define clave.",
        "**5. Vinculación:** Sistema ata al Rector con el `institution_id`."
    ])
    p.draw_card(345, 50, 270, 410, "2. Ciclo Pedagógico y Notas", [
        "**1. Carga Académica:** Docente autenticado visualiza solo sus cursos.",
        "**2. Registro:** Ingreso de notas (1.0 a 5.0) y faltas por sesión.",
        "**3. Validación:** Backend comprueba rangos y asignación curricular.",
        "**4. Persistencia ACID:** Transacción segura en PostgreSQL.",
        "**5. Auditoría:** Creación de registro en `AuditLog` con timestamp UTC."
    ])
    p.draw_card(645, 50, 265, 410, "3. Consulta Protegida (Anti-IDOR)", [
        "**1. Petición:** Alumno solicita reporte de calificaciones.",
        "**2. Extracción:** Backend extrae `student_id` del token JWT verificado.",
        "**3. Bloqueo:** Si el alumno altera el ID en la URL para ver a otro estudiante, la API devuelve HTTP 403 o 404.",
        "**4. Privacidad:** Cero fugas de información personal o notas ajenas."
    ])
    p.c.showPage()

    # Slide 9: Gestion Territorial
    p.draw_header("Gobernanza Territorial: Catálogo Oficial DUE 2024 y DIVIPOLA")
    p.draw_footer(9)
    p.draw_card(50, 50, 415, 410, "Catálogo de Referencia Nacional Precargado", [
        "**Fuente Oficial:** Datos Abiertos MinEducación SODA (`cfw5-qzt5` y `96t6-cfw4`, DUE 2024).",
        "**33 Entidades Territoriales:** 32 departamentos y Bogotá D.C. (códigos DANE de 2 dígitos).",
        "**1,122 Municipios:** Catálogo nacional completo DIVIPOLA (1,119 con sedes activas).",
        "**18,031 Establecimientos Educativos:** Precargados en `official_institution_catalog`.",
        "**51,521 Sedes Educativas:** 17,935 principales y 33,586 anexas en `official_campus_catalog`.",
        "**Aclaración de Adopción:** Datos precargados como catálogo de referencia para evitar digitación. La capa operativa de pruebas contiene 32 instituciones registradas (29 activas)."
    ])
    p.draw_card(495, 50, 415, 410, "Valor Estratégico para el MEN", [
        "**Compatibilidad Inmediata:** Llaves foráneas atadas a códigos DANE oficiales de 12 dígitos.",
        "**Consolidación Estadística:** Agregación confiable por departamento, municipio y sector sin normalizaciones intermedias.",
        "**Aislamiento Territorial Forzado:** Secretarías Departamentales y Municipales delimitadas estrictamente a su jurisdicción legal.",
        "**Cero Fricción en Registro:** Al invitar un rector por DANE, el sistema auto-completa sede, municipio y rectoría oficial."
    ])
    p.c.showPage()

    # Slide 10: Experiencias de Usuario
    p.draw_header("Experiencias de Usuario: Directivos, Docentes y Comunidad")
    p.draw_footer(10)
    p.draw_card(50, 260, 265, 200, "Rector / Director", [
        "**Tablero Institucional:** Estadísticas de matrícula, sedes y docentes.",
        "**Gobernanza:** Creación de calendarios y políticas de delegación."
    ])
    p.draw_card(345, 260, 270, 200, "Coordinador Académico", [
        "**Gestión Operativa:** Armado de grupos, asignación de cursos y horarios.",
        "**Supervisión:** Cierre y consolidación de periodos de notas."
    ])
    p.draw_card(645, 260, 265, 200, "Docente de Aula", [
        "**Planilla Ágil:** Registro de notas y control de asistencia diario.",
        "**Aulas Virtuales:** Inicio de clases sincrónicas BigBlueButton."
    ])
    p.draw_card(50, 50, 265, 195, "Estudiante", [
        "**Seguimiento Personal:** Consulta de notas parciales y boletines.",
        "**Tareas y Enlaces:** Acceso a guías y clases virtuales en vivo."
    ])
    p.draw_card(345, 50, 270, 195, "Padre de Familia / Acudiente", [
        "**Acompañamiento:** Monitoreo del rendimiento académico de hijos.",
        "**Alertas:** Trazabilidad de inasistencias y observaciones escolares."
    ])
    p.draw_card(645, 50, 265, 195, "Secretarías de Educación", [
        "**Supervisión Territorial:** Monitoreo de cobertura municipal.",
        "**Aprovisionamiento:** Emisión de invitaciones oficiales a Rectores."
    ])
    p.c.showPage()

    # Slide 11: BigBlueButton
    p.draw_header("Aulas y Encuentros Virtuales: Integración BigBlueButton")
    p.draw_footer(11)
    p.draw_card(50, 50, 415, 410, "Capacidades Verificadas en Software (Cliente API)", [
        "**Orquestación Completa en FastAPI:** Servicio `bbb_service.py` completamente programado y probado con pruebas automatizadas.",
        "**Salas Dinámicas:** Creación de sesiones de videoconferencia vinculadas a asignaturas, grupos y sedes específicas.",
        "**Seguridad Criptográfica:** Cálculo automático de checksums HMAC-SHA1 según el protocolo oficial de BigBlueButton.",
        "**Diferenciación de Roles:** Emisión de contraseñas de moderador para docentes y de asistente para estudiantes.",
        "**Monitoreo de Sesión:** Consulta de estado en tiempo real y cierre forzoso de salas al finalizar la sesión pedagógica."
    ])
    p.draw_card(495, 50, 415, 410, "Aclaración Factual y Prerrequisito de Infraestructura", [
        "**Infraestructura Multimedia Externa:** PEVN no aloja internamente los servidores WebRTC ni procesa flujos de video/audio en el contenedor de la API.",
        "**Requisito Operativo:** Para videoconferencias en vivo se requiere conectar el cliente PEVN a un clúster BigBlueButton externo dedicado.",
        "**Servidores TURN/STUN:** Indispensables para salvar firewalls y redes móviles con NAT estricto en zonas rurales.",
        "**Propuesta:** Acordar en la Fase 3 del piloto la infraestructura de pruebas para videoconferencia o habilitar solo módulos asíncronos en colegios con baja conectividad."
    ], bg=colors.HexColor("#F5F3FF"), border=colors.HexColor("#C4B5FD"), title_color=PURPLE)
    p.c.showPage()

    # Slide 12: Stack Tecnologico
    p.draw_header("Arquitectura Técnica y Stack Tecnológico")
    p.draw_footer(12)
    p.draw_card(50, 50, 195, 410, "Frontend SPA", [
        "**React 18.3+**",
        "**TypeScript 5.x** (Estricto)",
        "**Vite 5 Bundler**",
        "**TailwindCSS Local**",
        "**Cero Fuentes Externas:** 100% autónomo y offline-ready."
    ])
    p.draw_card(270, 50, 195, 410, "Backend API", [
        "**FastAPI (Python 3.12/3.14)**",
        "**Uvicorn ASGI**",
        "**Pydantic v2**",
        "**SQLAlchemy 2.0 Async**",
        "**asyncpg** (Driver nativo)",
        "**Alembic** (Migraciones)"
    ])
    p.draw_card(490, 50, 195, 410, "Persistencia / Caché", [
        "**PostgreSQL 15**",
        "Esquemas 3FN",
        "Índices optimizados",
        "Aislamiento por `institution_id`",
        "**Redis 7 In-Memory**",
        "Lista negra JWT",
        "Rate limit distribuido"
    ])
    p.draw_card(710, 50, 200, 410, "Seguridad / Integración", [
        "**Argon2id / Bcrypt**",
        "**JWT HMAC-SHA256**",
        "**Anti-IDOR Enforcement**",
        "**BigBlueButton API**",
        "**DIVIPOLA / DANE**",
        "**AuditLog Forense**"
    ])
    p.c.showPage()

    # Slide 13: Ciberseguridad
    p.draw_header("Ciberseguridad, Privacidad y Aislamiento Multi-Tenant")
    p.draw_footer(13)
    p.draw_card(50, 50, 265, 410, "Aislamiento Multi-Tenant", [
        "**Discriminador Lógico Forzado:** Toda consulta a sedes, docentes, alumnos o notas incluye obligatoriamente `WHERE institution_id = :id`.",
        "**Encapsulamiento:** No se delega al programador; se aplica desde la capa base de repositorios.",
        "**Mitigación Anti-IDOR:** Imposibilidad de acceder a registros de otros colegios manipulando parámetros en la URL."
    ])
    p.draw_card(345, 50, 270, 410, "Gestión de Identidades", [
        "**Contraseñas Robustas:** Hasheadas con Argon2id / bcrypt, eliminando el riesgo de tablas rainbow.",
        "**Tokens de Vida Corta:** Access tokens JWT con vigencia de 15 a 30 minutos.",
        "**Revocación Inmediata:** Lista negra en Redis 7 para invalidación instantánea de sesiones.",
        "**Protección de Fuerza Bruta:** Bloqueo temporal por intentos fallidos reiterados."
    ])
    p.draw_card(645, 50, 265, 410, "Privacidad (Ley 1581 / 2012)", [
        "**Datos de Menores:** Tratamiento bajo estándar reforzado; finalidad pedagógica estricta.",
        "**Cero Rastreadores:** Sin analítica comercial, scripts de CDNs foráneas ni cesión de datos a privados.",
        "**Pistas Forenses:** Auditoría inmutable de cambios con usuario, IP y timestamp UTC."
    ])
    p.c.showPage()

    # Slide 14: Gestion de Datos y Auditoria
    p.draw_header("Gestión de Datos, Auditoría Forense y Operaciones")
    p.draw_footer(14)
    p.draw_card(50, 50, 415, 410, "Pista de Auditoría Forense (`AuditLog`)", [
        "**Estructura Inmutable:** Cada modificación sensible registra un evento inmutable con UUID v4.",
        "**Metadatos Registrados:**",
        "- `user_id` y `role`: Identidad y rol del ejecutor.",
        "- `institution_id`: Tenant educativo afectado.",
        "- `action`: Verbo de acción (`LOGIN`, `GRADE_CHANGE`, `CREATE`).",
        "- `table_name` y `record_id`: Objeto de datos alterado.",
        "- `ip_address` y `user_agent`: Origen de red para trazabilidad.",
        "**Defensa ante Disputas:** Permite resolver formalmente reclamos sobre alteración de calificaciones o matrículas."
    ])
    p.draw_card(495, 50, 415, 410, "Continuidad Operativa y Respaldos", [
        "**Estrategia de Backup (RPO / RTO):**",
        "- **RPO < 1 hora:** Archivado continuo de transacciones WAL (Write-Ahead Logging).",
        "- **RTO < 2 horas:** Restauración automatizada de contenedor y esquema ante caída mayor.",
        "**Sanitización de Errores y Logs:** Endurecimiento verificado en R8: los mensajes de fallo ocultan credenciales y contraseñas con máscaras `***`.",
        "**Monitoreo y Salud:** Endpoints `/api/v1/health` para sondas de liveness y readiness en clústeres Kubernetes."
    ])
    p.c.showPage()

    # Slide 15: Matriz de Estado
    p.draw_header("Matriz de Estado Actual de Implementación")
    p.draw_footer(15)
    # Simple custom table in canvas
    table_x = 50
    table_y = 70
    table_w = SLIDE_W - 100
    row_h = 45

    # Headers
    p.c.setFillColor(NAVY)
    p.c.rect(table_x, table_y + 5 * row_h, table_w, row_h, fill=1, stroke=0)
    p.c.setFont("Helvetica-Bold", 10.5)
    p.c.setFillColor(WHITE)
    p.c.drawString(table_x + 15, table_y + 5 * row_h + 17, "Capacidad / Componente")
    p.c.drawString(table_x + 280, table_y + 5 * row_h + 17, "Estado de Madurez")
    p.c.drawString(table_x + 480, table_y + 5 * row_h + 17, "Evidencia en Repositorio")
    p.c.drawString(table_x + 700, table_y + 5 * row_h + 17, "Demo en Vivo")

    rows = [
        ("Autenticación JWT y RBAC (9 Canónicos / 11 BD)", "IMPLEMENTADO", "backend/app/core/security/interfaces.py\napp/models/role.py", "Sí (Verificado local)"),
        ("Aislamiento Multi-Tenant y Anti-IDOR", "IMPLEMENTADO", "backend/app/services/institution_service.py", "Sí (Verificado local)"),
        ("Catálogo Territorial DUE 2024", "CATÁLOGO PRECARGADO", "SODA cfw5-qzt5 / 96t6-cfw4\nofficial_institution_catalog", "Sí (18.031 EE / 51.521 Sedes)"),
        ("Aprovisionamiento de Rectores", "IMPLEMENTADO", "backend/app/services/rector_service.py", "Sí (Token 72h verificado)"),
        ("Planilla de Notas y Asistencia", "IMPLEMENTADO", "backend/app/services/grade_service.py", "Sí (Escala 1.0-5.0 activa)"),
    ]

    for idx, (cap, st, ev, dem) in enumerate(rows):
        ry = table_y + (4 - idx) * row_h
        p.c.setFillColor(LIGHT_BG if idx % 2 == 0 else WHITE)
        p.c.rect(table_x, ry, table_w, row_h, fill=1, stroke=1)

        p.c.setFont("Helvetica-Bold", 9.5)
        p.c.setFillColor(DARK_GRAY)
        p.c.drawString(table_x + 15, ry + 17, cap)

        p.c.setFont("Helvetica-Bold", 9.5)
        p.c.setFillColor(GREEN)
        p.c.drawString(table_x + 280, ry + 17, st)

        p.c.setFont("Helvetica", 8.5)
        p.c.setFillColor(MUTED)
        p.c.drawString(table_x + 480, ry + 17, ev)

        p.c.setFont("Helvetica", 9)
        p.c.setFillColor(DARK_GRAY)
        p.c.drawString(table_x + 700, ry + 17, dem)

    p.c.showPage()

    # Slide 16: Calidad y Pruebas R8
    p.draw_header("Resultados de Pruebas y Aseguramiento de Calidad (R8)")
    p.draw_footer(16)
    p.draw_card(50, 50, 415, 410, "Censo Dinámico de Pruebas (Pytest Suite)", [
        "**747 Pruebas Recolectadas:** Verificadas mediante el analizador dinámico AST en 72 archivos de prueba.",
        "**83 Pruebas de Integración con PostgreSQL 15:** Ejecutadas contra base de datos relacional real en 6 archivos clave (transacciones, claves foráneas, aislamiento institucional).",
        "**664 Pruebas Unitarias y en Memoria:** Distribuidas en 66 archivos de prueba (modelos Pydantic, utilitarios de seguridad, cálculo de notas).",
        "**Cero Advertencias en Documentación:** 41 comprobaciones automatizadas aprobadas con 100% de éxito (`audit_documentation.py`)."
    ])
    p.draw_card(495, 50, 415, 410, "Batería Ejecutada en Ciclo Acotado (57 Pruebas — 100% PASS)", [
        "**13 Pruebas de Teardown Hardening:** Verificación de limpieza garantizada en bloque `finally` para evitar bloqueos en PostgreSQL (`test_teardown_hardening.py`).",
        "**12 Pruebas de Analizador de Censo:** Validación reproducible de la taxonomía de pruebas (`test_census_analyzer.py`).",
        "**17 Pruebas de Aprovisionamiento Institucional:** Creación de instituciones y validación DANE (`test_institution_provisioning.py`).",
        "**15 Pruebas de Aprovisionamiento de Rectores:** Flujo de invitación y control de directivos (`test_nta10_rector_provisioning.py`).",
        "**690 Pruebas Restantes No Ejecutadas:** Excluidas deliberadamente de este ciclo acotado para preservar aislamiento y estabilidad.",
        "**Frontend:** `tsc --noEmit` completado con 0 errores y compilación `npm run build` exitosa."
    ])
    p.c.showPage()

    # Slide 17: Despliegue y Escalabilidad
    p.draw_header("Enfoque de Despliegue y Arquitectura de Producción")
    p.draw_footer(17)
    p.draw_card(50, 50, 415, 410, "Entorno Local Verificado vs. Producción", [
        "**Entorno Actual Verificado:**",
        "- Estación de trabajo Windows 11 / Linux WSL2.",
        "- PostgreSQL 15 local en puerto estándar.",
        "- Redis 7 en memoria para gestión de sesiones.",
        "- Uvicorn ASGI + Vite Dev Server.",
        "**Transparencia Técnica:** La plataforma está probada y operativa en entorno local/servidor de laboratorio, pero **no se encuentra desplegada aún en un clúster de producción masiva nacional**."
    ])
    p.draw_card(495, 50, 415, 410, "Arquitectura Destino Sugerida para el MEN", [
        "**Contenerización Multi-Etapa:**",
        "- Frontend servido mediante contenedor Nginx ultra-liviano.",
        "- Backend en imagen `python:3.12-slim` con usuario sin privilegios.",
        "**Orquestación en Kubernetes:**",
        "- Horizontal Pod Autoscaler (HPA) según tráfico.",
        "- Despliegue de réplicas de lectura de PostgreSQL para consultas de boletines masivas.",
        "- Alojamiento en Nube de Gobierno o centros de datos certificados por MinTIC."
    ])
    p.c.showPage()

    # Slide 18: Brechas y Decisiones
    p.draw_header("Brechas Identificadas, Riesgos y Decisiones Requeridas")
    p.draw_footer(18)
    p.draw_card(50, 50, 415, 410, "Brechas Técnicas y Dependencias Abiertas", [
        "**1. Clúster BigBlueButton Externo:** Requiere provisión de servidores dedicados para streaming de video WebRTC.",
        "**2. Conexión Transaccional con SIMAT:** No existe web service en vivo; se requiere convenio técnico y API Gateway con el MEN.",
        "**3. Firma Digital con Estampa Cronológica:** Las notas se auditan en base de datos, pero no cuentan aún con firma digital PKI de la ONAC.",
        "**4. Auditoría de Accesibilidad WCAG 2.1 AA:** Pendiente de certificación formal por laboratorio acreditado."
    ])
    p.draw_card(495, 50, 415, 410, "Decisiones Requeridas de la Mesa Técnica MEN", [
        "**Decisión 1:** ¿Asumirá el MEN la titularidad del código como Bien Público Digital bajo licencia abierta?",
        "**Decisión 2:** ¿Qué mecanismo de interoperabilidad se habilitará para el intercambio de datos con SIMAT y DUE?",
        "**Decisión 3:** ¿Se autoriza el diseño conjunto de un piloto experimental controlado en 2 a 5 colegios oficiales?",
        "**Decisión 4:** ¿Qué lineamientos de infraestructura y ciberseguridad gubernamental deben armonizarse en Fase 2?"
    ], bg=colors.HexColor("#FFFBEB"), border=colors.HexColor("#FDE68A"), title_color=AMBER)
    p.c.showPage()

    # Slide 19: Plan de Piloto
    p.draw_header("Propuesta de Colaboración Técnica en 4 Fases (Decision Gates)")
    p.draw_footer(19)
    p.draw_card(50, 50, 195, 410, "Fase 1: Mesa Técnica", [
        "**Duración:** 2 a 4 semanas.",
        "**Actividades:**",
        "- Revisión de arquitectura.",
        "- Inspección de repositorios.",
        "- Definición de requisitos.",
        "**Compuerta 1:** Dictamen técnico de viabilidad."
    ])
    p.draw_card(270, 50, 195, 410, "Fase 2: Seguridad", [
        "**Duración:** 4 a 6 semanas.",
        "**Actividades:**",
        "- Auditoría SAST / DAST.",
        "- Pruebas de estrés y carga.",
        "- Contratos de API SIMAT.",
        "**Compuerta 2:** Aval de seguridad y carga."
    ])
    p.draw_card(490, 50, 195, 410, "Fase 3: Piloto", [
        "**Duración:** 1 periodo (10-12 semanas).",
        "**Muestra:** 2 a 5 colegios.",
        "**Actividades:**",
        "- Operación paralela.",
        "- Matrícula y notas.",
        "**Compuerta 3:** Dictamen de adopción y métricas."
    ])
    p.draw_card(710, 50, 200, 410, "Fase 4: Consolidación", [
        "**Duración:** A definir por MEN.",
        "**Actividades:**",
        "- Transferencia formal.",
        "- Escalabilidad nacional.",
        "- Soberanía digital.",
        "**Hito Final:** Adopción como Bien Público Digital."
    ])
    p.c.showPage()

    # Slide 20: Beneficios y Metricas
    p.draw_header("Beneficios Esperados y Métricas de Impacto Propuestas")
    p.draw_footer(20)
    p.draw_card(50, 50, 415, 410, "Beneficios Públicos Proyectados", [
        "**Cero Costo Marginal:** Eliminación del cobro por alumno en software de gestión académica.",
        "**Equidad en Sedes Rurales:** Herramienta liviana que opera sobre enlaces de bajo ancho de banda sin caídas.",
        "**Trazabilidad Forense:** Reducción a cero de quejas por adulteración no autorizada de calificaciones escolares.",
        "**Soberanía Tecnológica:** El Estado mantiene control pleno del código, esquemas de datos y evolución técnica."
    ])
    p.draw_card(495, 50, 415, 410, "Métricas Cuantitativas para el Piloto", [
        "**Tasa de Adopción Docente:** Porcentaje de docentes que registran notas de forma autónoma (Meta: > 85%).",
        "**Tiempo de Carga en Red Rural:** Latencia promedio inferior a 1.5 segundos en enlaces de baja velocidad.",
        "**Incidencias de Seguridad:** Cero eventos de acceso cruzado entre instituciones (Cross-tenant leaks = 0).",
        "**Satisfacción de Rectores y Familias:** Evaluación de usabilidad superior al 80% en encuestas de cierre."
    ])
    p.c.showPage()

    # Slide 21: Proximos Pasos y Preguntas MEN
    p.draw_header("Próximos Pasos Solicitados y Preguntas para el MEN")
    p.draw_footer(21)
    p.draw_card(50, 50, 415, 410, "Próximos Pasos Inmediatos Solicitados", [
        "**1. Instalación de la Mesa Técnica:** Formalizar un canal de trabajo entre el equipo de PEVN y la Oficina de Tecnología del MEN.",
        "**2. Acceso a Repositorios:** Entrega formal del código fuente completo para inspección técnica por auditores del MEN.",
        "**3. Taller de Arquitectura:** Demostración en vivo de los flujos de aprovisionamiento, calificaciones y base de datos relacional.",
        "**4. Definición de Parámetros de Piloto:** Selección concertada de 2 a 5 colegios oficiales para pruebas de campo."
    ])
    p.draw_card(495, 50, 415, 410, "Preguntas Guía para el Equipo de Tecnología MEN", [
        "**Pregunta 1:** ¿Cuál es la ventana de oportunidad institucional para adelantar una prueba de concepto o piloto en 2026/2027?",
        "**Pregunta 2:** ¿Qué estándares de contenedor o nube pública (ej. AWS, Azure, OCI o centros de datos MinTIC) prefiere el MEN?",
        "**Pregunta 3:** ¿Qué dependencia liderará la definición de contratos de interoperabilidad para la integración con SIMAT?",
        "**Pregunta 4:** ¿Qué requisitos adicionales de ciberseguridad exige el MEN antes de autorizar un piloto experimental?"
    ], bg=colors.HexColor("#F0F9FF"), border=colors.HexColor("#BAE6FD"), title_color=BLUE)
    p.c.showPage()

    # Slide 22: Cierre
    p.add_closing(22)

    p.c.save()
    print(f"[SUCCESS] Presentación PDF generada exitosamente en: {output_path}")


if __name__ == "__main__":
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(repo_root, "docs", "government", "pdf")
    os.makedirs(target_dir, exist_ok=True)
    target_pdf = os.path.join(target_dir, "PEVN_PRESENTACION_INSTITUCIONAL_MEN.pdf")
    build_pdf_presentation(target_pdf)
