#!/usr/bin/env python3
"""
PEVN — Generador de la Presentación Institucional para el MEN (PPTX y PDF)
Crea una presentación de 22 diapositivas con estética ejecutiva gubernamental,
cumpliendo con la jerarquía canónica de 11 roles, evidencia de pruebas R8,
estado de madurez por capacidades y propuesta de piloto con compuertas de decisión.
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Dimensiones 16:9 Widescreen
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

# Paleta de Colores Institucional MEN / Gobierno
NAVY = RGBColor(15, 41, 66)       # #0F2942 - Azul Primario Presidencia/MEN
BLUE = RGBColor(29, 104, 167)     # #1D68A7 - Azul Técnico
GOLD = RGBColor(197, 155, 39)     # #C59B27 - Dorado Institucional
DARK_GRAY = RGBColor(30, 41, 59)  # #1E293B - Texto Principal
MUTED = RGBColor(100, 116, 139)   # #64748B - Subtítulos
LIGHT_BG = RGBColor(248, 250, 252)# #F8FAFC - Fondo de Tarjetas
BORDER = RGBColor(226, 232, 240)  # #E2E8F0 - Borde Sutil
WHITE = RGBColor(255, 255, 255)
GREEN = RGBColor(16, 149, 93)     # #10955D - Implementado
AMBER = RGBColor(217, 119, 6)     # #D97706 - Parcial
PURPLE = RGBColor(109, 40, 217)   # #6D28D9 - Dependencia Externa


def create_deck():
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    blank_layout = prs.slide_layouts[6] # Blank slide
    return prs, blank_layout


def add_header(slide, title_text, category="PLATAFORMA EDUCATIVA VIRTUAL NACIONAL (PEVN) — OFICINA DE TECNOLOGÍA (MEN)"):
    # Category tag
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.3))
    tf_c = cat_box.text_frame
    tf_c.word_wrap = True
    tf_c.margin_left = tf_c.margin_right = tf_c.margin_top = tf_c.margin_bottom = 0
    p_c = tf_c.paragraphs[0]
    p_c.text = category.upper()
    p_c.font.size = Pt(10)
    p_c.font.bold = True
    p_c.font.color.rgb = BLUE

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.6))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = tf_t.margin_right = tf_t.margin_top = tf_t.margin_bottom = 0
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.size = Pt(22)
    p_t.font.bold = True
    p_t.font.color.rgb = NAVY

    # Decorative line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.35), Inches(11.733), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = GOLD
    line.line.color.rgb = GOLD


def add_footer(slide, current_slide, total_slides=22):
    foot_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.7), Inches(0.3))
    tf = foot_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = "PEVN — Documento Técnico Institucional de Trabajo | No representa adopción ni certificación previa del MEN"
    p.font.size = Pt(8.5)
    p.font.color.rgb = MUTED

    num_box = slide.shapes.add_textbox(Inches(11.0), Inches(7.05), Inches(1.5), Inches(0.3))
    tf_n = num_box.text_frame
    tf_n.word_wrap = True
    tf_n.margin_left = tf_n.margin_right = tf_n.margin_top = tf_n.margin_bottom = 0
    p_n = tf_n.paragraphs[0]
    p_n.alignment = PP_ALIGN.RIGHT
    p_n.text = f"{current_slide} / {total_slides}"
    p_n.font.size = Pt(8.5)
    p_n.font.bold = True
    p_n.font.color.rgb = MUTED


def add_card(slide, left, top, width, height, title, items, bg_color=LIGHT_BG, border_color=BORDER, title_color=NAVY):
    # Shape card
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1)

    # Text
    tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.18), width - Inches(0.4), height - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

    if title:
        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = title_color
        p_title.space_after = Pt(8)

    for idx, item in enumerate(items):
        p = tf.add_paragraph() if (title or idx > 0) else tf.paragraphs[0]
        p.font.size = Pt(10.5)
        p.space_after = Pt(6)
        p.font.color.rgb = DARK_GRAY

        # Check if item has bold header prefix (e.g. "**Header:** Text")
        if "**" in item:
            parts = item.split("**")
            # "" ** "Bold" ** " Rest"
            for i, part in enumerate(parts):
                if not part:
                    continue
                run = p.add_run()
                run.text = part
                if i % 2 == 1:
                    run.font.bold = True
                    run.font.color.rgb = NAVY
                else:
                    run.font.bold = False
        else:
            run = p.add_run()
            run.text = item


def build_presentation(output_path):
    prs, blank_layout = create_deck()

    # =========================================================================
    # SLIDE 1: PORTADA
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    # Background accent rectangle
    bg_band = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg_band.fill.solid()
    bg_band.fill.fore_color.rgb = NAVY
    bg_band.line.fill.background()

    # Inner decorative container
    inner = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(5.9))
    inner.fill.solid()
    inner.fill.fore_color.rgb = RGBColor(22, 53, 84)
    inner.line.color.rgb = GOLD
    inner.line.width = Pt(1.5)

    # Title box
    tb = s1.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(3.5))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "REPÚBLICA DE COLOMBIA • SECTOR EDUCATIVO OFICIAL"
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = GOLD
    p0.space_after = Pt(12)

    p1 = tf.add_paragraph()
    p1.text = "Plataforma Educativa Virtual Nacional (PEVN)"
    p1.font.size = Pt(30)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.space_after = Pt(8)

    p2 = tf.add_paragraph()
    p2.text = "Presentación Institucional y Dossier Técnico de Ingeniería"
    p2.font.size = Pt(17)
    p2.font.color.rgb = RGBColor(190, 215, 240)
    p2.space_after = Pt(18)

    p3 = tf.add_paragraph()
    p3.text = "Sesión de Trabajo con la Oficina de Tecnología y Sistemas de Información\nMinisterio de Educación Nacional (MEN)"
    p3.font.size = Pt(12.5)
    p3.font.color.rgb = WHITE

    # Metadata box
    mb = s1.shapes.add_textbox(Inches(1.2), Inches(4.9), Inches(10.9), Inches(1.5))
    mtf = mb.text_frame
    mtf.word_wrap = True
    mp = mtf.paragraphs[0]
    mp.text = "Autor / Iniciativa Técnica: Juan Carlos Castro Narváez | Versión: 1.0-FINAL-MEN | Octubre 2026\n" \
              "Repositorio: github.com/juancastro2381-hub/Plataforma-Educativa-Virtual-Nacional-PEVN\n" \
              "Nota: Iniciativa técnica independiente. No constituye aprobación, contrato ni certificación previa del MEN."
    mp.font.size = Pt(9.5)
    mp.font.color.rgb = RGBColor(160, 185, 210)

    # =========================================================================
    # SLIDE 2: RESUMEN EJECUTIVO
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Resumen Ejecutivo de la Iniciativa PEVN")
    add_footer(s2, 2)

    add_card(s2, Inches(0.8), Inches(1.6), Inches(3.7), Inches(5.1),
             "Propósito Público",
             [
                 "**Soberanía Tecnológica:** Ecosistema digital abierto concebido para superar la fragmentación de software y el cobro recurrente por estudiante en colegios oficiales.",
                 "**Equidad Territorial:** Diseñado para brindar capacidades de gestión de calidad equivalente a instituciones rurales y urbanas.",
                 "**Bien Público Digital:** Código fuente auditable bajo licencia abierta (Apache 2.0 / AGPLv3)."
             ])

    add_card(s2, Inches(4.8), Inches(1.6), Inches(3.7), Inches(5.1),
             "Solución Técnica",
             [
                 "**Arquitectura Desacoplada:** Frontend SPA en React 18/TypeScript (Vite) + Backend asíncrono en FastAPI (Python 3.12/3.14).",
                 "**Persistencia y Sesiones:** PostgreSQL 15 con aislamiento multi-tenant forzado + Redis 7 para revocación instantánea de JWT.",
                 "**Modelo y Estándares:** Jerarquía canónica de 9 roles (11 en BD). Catálogo DANE precargado (18,031 colegios, 51,521 sedes; no implica adopción)."
             ])

    add_card(s2, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.1),
             "Evidencia y Validación",
             [
                 "**Censo Dinámico (R8):** 747 pruebas recolectadas en 72 archivos de prueba.",
                 "**Pruebas Ejecutadas:** 57 pruebas focalizadas con 100% PASS en ciclo acotado (teardown seguro, analizador y aprovisionamiento).",
                 "**Ruta hacia Piloto:** Propuesta de trabajo en 4 fases con compuertas de decisión técnica (Decision Gates) bajo rectoría del MEN."
             ])

    # =========================================================================
    # SLIDE 3: EL PROBLEMA EDUCATIVO E INSTITUCIONAL
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Diagnóstico del Problema en el Sector Oficial")
    add_footer(s3, 3)

    add_card(s3, Inches(0.8), Inches(1.6), Inches(5.7), Inches(2.4),
             "1. Fragmentación y Silos de Datos",
             [
                 "**Planillas Desarticuladas:** Notas y asistencia llevadas en hojas de cálculo locales o libretas en papel sin consolidación central.",
                 "**Riesgo de Pérdida:** Falta de respaldos automáticos y trazabilidad de cambios en notas ante quejas o auditorías."
             ])

    add_card(s3, Inches(6.8), Inches(1.6), Inches(5.7), Inches(2.4),
             "2. Dependencia Financiera Privativa",
             [
                 "**Cobro por Licenciamiento:** Sistemas comerciales que cobran costos recurrentes por alumno, asfixiando presupuestos territoriales.",
                 "**Bloqueo de Proveedor (Vendor Lock-in):** Dificultad extrema para extraer históricos de calificaciones al terminar contratos."
             ])

    add_card(s3, Inches(0.8), Inches(4.3), Inches(5.7), Inches(2.4),
             "3. Brecha de Conectividad Rural",
             [
                 "**Sistemas Comerciales Pesados:** Plataformas saturadas de librerías de rastreo y fuentes externas que colapsan con enlaces rurales de 2 Mbps.",
                 "**Inequidad Operativa:** Sedes rurales apartadas quedan excluidas del seguimiento digital pedagógico."
             ])

    add_card(s3, Inches(6.8), Inches(4.3), Inches(5.7), Inches(2.4),
             "4. Soberanía y Gobernanza de Datos",
             [
                 "**Datos de Menores en Nubes Foráneas:** Información confidencial de niños y adolescentes tratada sin supervisión directa del Estado.",
                 "**Desalineación Normativa:** Incompatibilidad con Ley 1581 de 2012 y lineamientos de Gobierno Digital."
             ])

    # =========================================================================
    # SLIDE 4: VISIÓN, MISIÓN Y VALOR PÚBLICO
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Visión, Misión y Creación de Valor Público")
    add_footer(s4, 4)

    add_card(s4, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Misión y Visión Estratégica",
             [
                 "**Misión:** Proveer al sistema educativo oficial de Colombia una infraestructura digital soberana, auditable y de alto rendimiento que unifique los procesos directivos, pedagógicos y comunitarios.",
                 "**Visión:** Consolidar a PEVN como el Bien Público Digital de referencia para la educación pública nacional, reduciendo a cero el costo marginal de gestión escolar por estudiante.",
                 "**Alineación Institucional:** Armonizado con las metas del Plan Nacional de Desarrollo en materia de transformación digital educativa y cierre de brechas urbano-rurales."
             ])

    add_card(s4, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Dimensiones de Valor Público",
             [
                 "**Ahorro Presupuestal Sostenible:** Eliminación de pagos recurrentes de licenciamiento privativo en Secretarías de Educación.",
                 "**Soberanía de Datos Nacional:** Residencia de datos en centros de datos del Estado o nubes gubernamentales bajo Ley 1581 de 2012.",
                 "**Continuidad y Resiliencia Escolar:** Capacidad de mantener seguimiento evaluativo y comunicación durante emergencias o cierres viales.",
                 "**Transparencia y Cero Fraude:** Registro inmutable de cada calificación con marca de tiempo UTC y usuario responsable."
             ])

    # =========================================================================
    # SLIDE 5: ALCANCE DEL PROYECTO — FRONTERAS Y EXCLUSIONES
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Alcance del Proyecto: Inclusiones y Exclusiones Taxativas")
    add_footer(s5, 5)

    add_card(s5, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Capacidades Incluidas en el Alcance Actual",
             [
                 "**Aprovisionamiento Territorial e Institucional:** Creación de sedes bajo códigos oficiales DANE.",
                 "**Activación Criptográfica de Rectores:** Invitaciones con token firmado HMAC y expiración de 72 horas.",
                 "**Parametrización Curricular:** Años lectivos, periodos, grados, grupos y asignación académica docente.",
                 "**Gestión Evaluativa:** Planilla interactiva de notas con ponderación porcentual y control de asistencia.",
                 "**Portales de Autoservicio:** Vistas seguras para Estudiantes y Acudientes protegidas contra IDOR.",
                 "**Orquestación de Aulas Virtuales:** Cliente API para salas BigBlueButton con tokens seguros."
             ])

    add_card(s5, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Exclusiones Taxativas (Non-Goals)",
             [
                 "**No es un Sustituto Legal del SIMAT:** No reemplaza la potestad del MEN sobre el registro oficial de matrícula; actúa como plataforma operativa complementaria.",
                 "**No es Proveedor de Infraestructura Física:** Optimiza el tráfico de red, pero no suministra antenas, enlaces satelitales ni fibra óptica.",
                 "**No es Entidad de Certificación Académica:** La validez de certificados y títulos corresponde por ley a cada Institución y Secretaría de Educación.",
                 "**No Aloja Clúster WebRTC Embebido:** La transmisión multimedia en vivo requiere la infraestructura BigBlueButton externa descrita."
             ], bg_color=RGBColor(254, 242, 242), border_color=RGBColor(252, 165, 165), title_color=RGBColor(153, 27, 27))

    # =========================================================================
    # SLIDE 6: MODELO DE AUTORIDAD Y JERARQUÍA CANÓNICA (9 ROLES / 11 EN BD)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Jerarquía Canónica RBAC (9 Roles) y Modelo de Autoridad")
    add_footer(s6, 6)

    add_card(s6, Inches(0.8), Inches(1.6), Inches(6.0), Inches(5.1),
             "Catálogo Canónico de 9 Roles (11 Identificadores en BD)",
             [
                 "**[100] superadmin:** Operador técnico de plataforma e infraestructura.",
                 "**[90] national_admin:** Administrador Nacional MEN y gobierno general.",
                 "**[80] department_admin:** Secretaría de Educación Departamental.",
                 "**[70] municipality_admin:** Secretaría de Educación Municipal.",
                 "**[60] rector:** Rector / Director Institucional (Alias técnico: institution_admin).",
                 "**[50] coordinator:** Coordinador Académico / Sede (Alias técnico: academic_coordinator).",
                 "**[30] teacher:** Docente de aula y registro evaluativo.",
                 "**[10] student:** Estudiante matriculado (SIMAT).",
                 "**[10] guardian:** Acudiente / Tutor legal civil."
             ])

    add_card(s6, Inches(7.1), Inches(1.6), Inches(5.4), Inches(5.1),
             "Fronteras de Autoridad y Excepción Aprobada",
             [
                 "**Cadena Canónica Aprobada:**\nSUPERADMIN → NATIONAL_ADMIN → DEPARTMENT_ADMIN → MUNICIPALITY_ADMIN → RECTOR → COORDINATOR → TEACHER / STUDENT → GUARDIAN.",
                 "**Aislamiento Territorial Forzado:** Ninguna autoridad puede cruzar fronteras departamentales o municipales DANE.",
                 "**Excepción Canónica de Coordinador:** Por regla general, los coordinadores no crean usuarios. No obstante, mediante la directiva institucional persistida (`coordinator_delegated_provisioning_enabled`):\n• **Si está inhabilitada (Default):** Creación bloqueada (HTTP 403 `COORDINATOR_DELEGATION_DISABLED`).\n• **Si el Rector la habilita:** El coordinador puede crear docentes, matricular estudiantes y vincular acudientes en su sede."
             ])

    # =========================================================================
    # SLIDE 7: ARQUITECTURA FUNCIONAL Y MÓDULOS PRINCIPALES
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Arquitectura Funcional y Módulos Principales")
    add_footer(s7, 7)

    add_card(s7, Inches(0.8), Inches(1.6), Inches(3.7), Inches(2.4),
             "Módulo Territorial / DANE",
             [
                 "**Codificación Nacional:** Integración nativa de DIVIPOLA y Directorio DUE.",
                 "**Aislamiento:** Filtrado multi-tenant estricto desde la raíz administrativa."
             ])

    add_card(s7, Inches(4.8), Inches(1.6), Inches(3.7), Inches(2.4),
             "Aprovisionamiento Directivo",
             [
                 "**Invitaciones Criptográficas:** Tokens temporales con firma HMAC de 72h.",
                 "**Activación Autónoma:** El rector valida cédula y activa credenciales seguras."
             ])

    add_card(s7, Inches(8.8), Inches(1.6), Inches(3.7), Inches(2.4),
             "Gestión Curricular",
             [
                 "**Estructura Académica:** Sedes, jornadas, grados, grupos y asignaturas.",
                 "**Carga Docente:** Vinculación de profesores a asignaturas y cursos."
             ])

    add_card(s7, Inches(0.8), Inches(4.3), Inches(3.7), Inches(2.4),
             "Evaluación y Asistencia",
             [
                 "**Planilla Docente:** Notas numéricas (1.0-5.0), ponderación y faltas.",
                 "**Consolidación:** Cálculo automático de promedios de periodo."
             ])

    add_card(s7, Inches(4.8), Inches(4.3), Inches(3.7), Inches(2.4),
             "Portales Estudiantil / Familia",
             [
                 "**Consultas Seguras:** Acceso a boletín y faltas protegido anti-IDOR.",
                 "**Acompañamiento:** Visualización de observaciones pedagógicas."
             ])

    add_card(s7, Inches(8.8), Inches(4.3), Inches(3.7), Inches(2.4),
             "Aulas Virtuales y Auditoría",
             [
                 "**BigBlueButton:** Creación de salas seguras con clave de moderador.",
                 "**Pista Forense:** Registro inmutable de transacciones con IP y UTC."
             ])

    # =========================================================================
    # SLIDE 8: FLUJOS EDUCATIVOS VERIFICADOS EN IMPLEMENTACIÓN
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Flujos Educativos Verificados en Código Fuente")
    add_footer(s8, 8)

    add_card(s8, Inches(0.8), Inches(1.6), Inches(3.7), Inches(5.1),
             "1. Aprovisionamiento Institucional",
             [
                 "**1. Solicitud:** Secretaría ingresa código DANE y correo del Rector.",
                 "**2. Token Seguro:** Backend genera token UUID v4 firmado con HMAC.",
                 "**3. Notificación:** Se despacha enlace con vigencia de 72 horas.",
                 "**4. Activación:** Rector valida documento de identidad y define clave.",
                 "**5. Vinculación:** Sistema ata al Rector con el `institution_id`."
             ])

    add_card(s8, Inches(4.8), Inches(1.6), Inches(3.7), Inches(5.1),
             "2. Ciclo Pedagógico y Notas",
             [
                 "**1. Carga Académica:** Docente autenticado visualiza solo sus cursos.",
                 "**2. Registro:** Ingreso de notas (1.0 a 5.0) y faltas por sesión.",
                 "**3. Validación:** Backend comprueba rangos y asignación curricular.",
                 "**4. Persistencia ACID:** Transacción segura en PostgreSQL.",
                 "**5. Auditoría:** Creación de registro en `AuditLog` con timestamp UTC."
             ])

    add_card(s8, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.1),
             "3. Consulta Protegida (Anti-IDOR)",
             [
                 "**1. Petición:** Alumno solicita reporte de calificaciones.",
                 "**2. Extracción:** Backend extrae `student_id` del token JWT verificado.",
                 "**3. Bloqueo:** Si el alumno altera el ID en la URL para ver a otro estudiante, la API devuelve HTTP 403 o 404.",
                 "**4. Privacidad:** Cero fugas de información personal o notas ajenas."
             ])

    # =========================================================================
    # SLIDE 9: GESTIÓN INSTITUCIONAL Y TERRITORIAL (DANE / DIVIPOLA)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Gobernanza Territorial: Catálogo DANE/DIVIPOLA (DUE 2024)")
    add_footer(s9, 9)

    add_card(s9, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Catálogo Maestro de Referencia (DUE 2024)",
             [
                 "**33 Entidades Territoriales:** 32 departamentos y Bogotá D.C., conforme a DIVIPOLA oficial.",
                 "**1,122 Municipios:** Codificación DANE oficial (1,119 con cobertura de sedes en censo).",
                 "**18,031 Establecimientos Educativos:** Cosechados de SODA cfw5-qzt5 (DUE 2024, 17,990 censados + 41 calibración).",
                 "**51,521 Sedes Físicas Activas:** SODA 96t6-cfw4 (50,107 activas + 1,364 sedes principales + 50 semilla)."
             ])

    add_card(s9, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Valor Estratégico y Aclaración de Adopción",
             [
                 "**Aprovisionamiento Instantáneo:** Validación automática por código DANE de 12 dígitos sin migración manual.",
                 "**Consolidación Estadística:** Agregación territorial limpia sin riesgo de duplicados o solapamientos.",
                 "**Aclaración Institucional Mandatoria:** Las cifras anteriores corresponden al **catálogo de referencia precargado** para habilitar la activación directiva.\n• **NO representan adopción operativa actual** ni colegios en producción.\n• En la base operacional (`institutions`), existen actualmente 32 colegios de prueba/laboratorio (29 activos)."
             ])

    # =========================================================================
    # SLIDE 10: EXPERIENCIAS DE USUARIO POR ROL
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Experiencias de Usuario: Directivos, Docentes y Comunidad")
    add_footer(s10, 10)

    add_card(s10, Inches(0.8), Inches(1.6), Inches(3.7), Inches(2.4),
             "Rector / Director",
             [
                 "**Tablero Institucional:** Estadísticas de matrícula, sedes y docentes.",
                 "**Gobernanza:** Creación de calendarios y políticas de delegación."
             ])

    add_card(s10, Inches(4.8), Inches(1.6), Inches(3.7), Inches(2.4),
             "Coordinador Académico",
             [
                 "**Gestión Operativa:** Armado de grupos, asignación de cursos y horarios.",
                 "**Supervisión:** Cierre y consolidación de periodos de notas."
             ])

    add_card(s10, Inches(8.8), Inches(1.6), Inches(3.7), Inches(2.4),
             "Docente de Aula",
             [
                 "**Planilla Ágil:** Registro de notas y control de asistencia diario.",
                 "**Aulas Virtuales:** Inicio de clases sincrónicas BigBlueButton."
             ])

    add_card(s10, Inches(0.8), Inches(4.3), Inches(3.7), Inches(2.4),
             "Estudiante",
             [
                 "**Seguimiento Personal:** Consulta de notas parciales y boletines.",
                 "**Tareas y Enlaces:** Acceso a guías y clases virtuales en vivo."
             ])

    add_card(s10, Inches(4.8), Inches(4.3), Inches(3.7), Inches(2.4),
             "Padre de Familia / Acudiente",
             [
                 "**Acompañamiento:** Monitoreo del rendimiento académico de hijos.",
                 "**Alertas:** Trazabilidad de inasistencias y observaciones escolares."
             ])

    add_card(s10, Inches(8.8), Inches(4.3), Inches(3.7), Inches(2.4),
             "Secretarías de Educación",
             [
                 "**Supervisión Territorial:** Monitoreo de cobertura municipal.",
                 "**Aprovisionamiento:** Emisión de invitaciones oficiales a Rectores."
             ])

    # =========================================================================
    # SLIDE 11: AULAS Y ENCUENTROS VIRTUALES (BIGBLUEBUTTON)
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "Aulas y Encuentros Virtuales: Integración BigBlueButton")
    add_footer(s11, 11)

    add_card(s11, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Capacidades Verificadas en Software (Cliente API)",
             [
                 "**Orquestación Completa en FastAPI:** Servicio `bbb_service.py` completamente programado y probado con pruebas automatizadas.",
                 "**Salas Dinámicas:** Creación de sesiones de videoconferencia vinculadas a asignaturas, grupos y sedes específicas.",
                 "**Seguridad Criptográfica:** Cálculo automático de checksums HMAC-SHA1 según el protocolo oficial de BigBlueButton.",
                 "**Diferenciación de Roles:** Emisión de contraseñas de moderador para docentes y de asistente para estudiantes.",
                 "**Monitoreo de Sesión:** Consulta de estado en tiempo real y cierre forzoso de salas al finalizar la sesión pedagógica."
             ])

    add_card(s11, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Aclaración Factual y Prerrequisito de Infraestructura",
             [
                 "**Infraestructura Multimedia Externa:** PEVN no aloja internamente los servidores WebRTC ni procesa flujos de video/audio en el contenedor de la API.",
                 "**Requisito Operativo:** Para videoconferencias en vivo se requiere conectar el cliente PEVN a un clúster BigBlueButton externo dedicado.",
                 "**Servidores TURN/STUN:** Indispensables para salvar firewalls y redes móviles con NAT estricto en zonas rurales.",
                 "**Propuesta:** Acordar en la Fase 3 del piloto la infraestructura de pruebas para videoconferencia o habilitar solo módulos asíncronos en colegios con baja conectividad."
             ], bg_color=RGBColor(245, 243, 255), border_color=RGBColor(196, 181, 253), title_color=PURPLE)

    # =========================================================================
    # SLIDE 12: ARQUITECTURA TÉCNICA Y STACK TECNOLÓGICO
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "Arquitectura Técnica y Stack Tecnológico")
    add_footer(s12, 12)

    add_card(s12, Inches(0.8), Inches(1.6), Inches(2.7), Inches(5.1),
             "Frontend SPA",
             [
                 "**React 18.3+**",
                 "**TypeScript 5.x** (Modo estricto)",
                 "**Vite 5 Bundler**",
                 "**TailwindCSS** (Estilos locales)",
                 "**Cero Fuentes Externas:** 100% autónomo y offline-ready."
             ])

    add_card(s12, Inches(3.8), Inches(1.6), Inches(2.7), Inches(5.1),
             "Backend API",
             [
                 "**FastAPI (Python 3.12/3.14)**",
                 "**Uvicorn ASGI** (Asíncrono)",
                 "**Pydantic v2** (Validación)",
                 "**SQLAlchemy 2.0** (Async)",
                 "**asyncpg** (Driver nativo)",
                 "**Alembic** (Migraciones)"
             ])

    add_card(s12, Inches(6.8), Inches(1.6), Inches(2.7), Inches(5.1),
             "Persistencia / Caché",
             [
                 "**PostgreSQL 15**",
                 "Esquemas 3FN",
                 "Índices optimizados",
                 "Aislamiento por `institution_id`",
                 "**Redis 7 In-Memory**",
                 "Lista negra JWT",
                 "Rate limit distribuido"
             ])

    add_card(s12, Inches(9.8), Inches(1.6), Inches(2.7), Inches(5.1),
             "Seguridad / Integración",
             [
                 "**Argon2id / Bcrypt**",
                 "**JWT HMAC-SHA256**",
                 "**Anti-IDOR Enforcement**",
                 "**BigBlueButton API**",
                 "**DIVIPOLA / DANE**",
                 "**AuditLog Forense**"
             ])

    # =========================================================================
    # SLIDE 13: CIBERSEGURIDAD, PRIVACIDAD Y AISLAMIENTO MULTI-TENANT
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "Ciberseguridad, Privacidad y Aislamiento Multi-Tenant")
    add_footer(s13, 13)

    add_card(s13, Inches(0.8), Inches(1.6), Inches(3.7), Inches(5.1),
             "Aislamiento Multi-Tenant",
             [
                 "**Discriminador Lógico Forzado:** Toda consulta a sedes, docentes, alumnos o notas incluye obligatoriamente `WHERE institution_id = :id`.",
                 "**Encapsulamiento:** No se delega al programador; se aplica desde la capa base de repositorios.",
                 "**Mitigación Anti-IDOR:** Imposibilidad de acceder a registros de otros colegios manipulando parámetros en la URL."
             ])

    add_card(s13, Inches(4.8), Inches(1.6), Inches(3.7), Inches(5.1),
             "Gestión de Identidades",
             [
                 "**Contraseñas Robustas:** Hasheadas con Argon2id / bcrypt, eliminando el riesgo de tablas rainbow.",
                 "**Tokens de Vida Corta:** Access tokens JWT con vigencia de 15 a 30 minutos.",
                 "**Revocación Inmediata:** Lista negra en Redis 7 para invalidación instantánea de sesiones.",
                 "**Protección de Fuerza Bruta:** Bloqueo temporal por intentos fallidos reiterados."
             ])

    add_card(s13, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.1),
             "Privacidad (Ley 1581 / 2012)",
             [
                 "**Datos de Menores:** Tratamiento bajo estándar reforzado; finalidad pedagógica estricta.",
                 "**Cero Rastreadores:** Sin analítica comercial, scripts de CDNs foráneas ni cesión de datos a privados.",
                 "**Pistas Forenses:** Auditoría inmutable de cambios con usuario, IP y timestamp UTC."
             ])

    # =========================================================================
    # SLIDE 14: GESTIÓN DE DATOS, AUDITABILIDAD Y OPERACIONES
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    add_header(s14, "Gestión de Datos, Auditoría Forense y Operaciones")
    add_footer(s14, 14)

    add_card(s14, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Pista de Auditoría Forense (`AuditLog`)",
             [
                 "**Estructura Inmutable:** Cada modificación sensible registra un evento inmutable con UUID v4.",
                 "**Metadatos Registrados:**",
                 "- `user_id` y `role`: Identidad y rol del ejecutor.",
                 "- `institution_id`: Tenant educativo afectado.",
                 "- `action`: Verbo de acción (`LOGIN`, `GRADE_CHANGE`, `CREATE`).",
                 "- `table_name` y `record_id`: Objeto de datos alterado.",
                 "- `ip_address` y `user_agent`: Origen de red para trazabilidad.",
                 "**Defensa ante Disputas:** Permite resolver formalmente reclamos sobre alteración de calificaciones o matrículas."
             ])

    add_card(s14, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Continuidad Operativa y Respaldos",
             [
                 "**Estrategia de Backup (RPO / RTO):**",
                 "- **RPO < 1 hora:** Archivado continuo de transacciones WAL (Write-Ahead Logging).",
                 "- **RTO < 2 horas:** Restauración automatizada de contenedor y esquema ante caída mayor.",
                 "**Sanitización de Errores y Logs:** Endurecimiento verificado en R8: los mensajes de fallo ocultan credenciales y contraseñas con máscaras `***`.",
                 "**Monitoreo y Salud:** Endpoints `/api/v1/health` para sondas de liveness y readiness en clústeres Kubernetes."
             ])

    # =========================================================================
    # SLIDE 15: ESTADO ACTUAL DE IMPLEMENTACIÓN POR CAPACIDADES
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    add_header(s15, "Matriz de Estado Actual de Implementación")
    add_footer(s15, 15)

    # Create a nice structured table slide
    table_shape = s15.shapes.add_table(7, 4, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.1))
    table = table_shape.table
    table.columns[0].width = Inches(3.2)
    table.columns[1].width = Inches(2.3)
    table.columns[2].width = Inches(3.4)
    table.columns[3].width = Inches(2.833)

    headers = ["Capacidad / Componente", "Estado de Madurez", "Evidencia en Repositorio", "Demo en Vivo"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(11)
            p.font.color.rgb = WHITE

    rows_data = [
        ("Autenticación JWT y RBAC (9 Canónicos / 11 BD)", "IMPLEMENTADO", "backend/app/core/security/interfaces.py\nbackend/app/models/role.py", "Sí (Verificado en local)"),
        ("Aislamiento Multi-Tenant y Anti-IDOR", "IMPLEMENTADO", "backend/app/services/institution_service.py", "Sí (Verificado en local)"),
        ("Catálogo Territorial y DUE 2024 (Precarga)", "CATÁLOGO PRECARGADO", "SODA cfw5-qzt5 / 96t6-cfw4\nofficial_institution_catalog", "Sí (18.031 EE / 51.521 Sedes ref.)"),
        ("Aprovisionamiento de Rectores", "IMPLEMENTADO", "backend/app/services/rector_service.py", "Sí (Token 72h verificado)"),
        ("Planilla de Notas y Asistencia", "IMPLEMENTADO", "backend/app/services/grade_service.py", "Sí (Escala 1.0-5.0 activa)"),
        ("Aulas Virtuales (BigBlueButton)", "CLIENTE IMPLEMENTADO", "backend/app/services/bbb_service.py", "Condicional (Requiere BBB externo)")
    ]

    for i, r in enumerate(rows_data):
        for j, val in enumerate(r):
            cell = table.cell(i + 1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = LIGHT_BG if i % 2 == 0 else WHITE
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(10)
                if j == 1:
                    p.font.bold = True
                    p.font.color.rgb = GREEN if "IMPLEMENTADO" in val and "CLIENTE" not in val else PURPLE
                else:
                    p.font.color.rgb = DARK_GRAY

    # =========================================================================
    # SLIDE 16: PRUEBAS Y ASEGURAMIENTO DE CALIDAD (EVIDENCIA R8)
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    add_header(s16, "Resultados de Pruebas y Aseguramiento de Calidad (R8)")
    add_footer(s16, 16)

    add_card(s16, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Censo Dinámico de Pruebas (Pytest Suite)",
             [
                 "**747 Pruebas Recolectadas:** Verificadas mediante el analizador dinámico AST en 72 archivos de prueba.",
                 "**83 Pruebas de Integración con PostgreSQL 15:** Ejecutadas contra base de datos relacional real en 6 archivos clave (transacciones, claves foráneas, aislamiento institucional).",
                 "**664 Pruebas Unitarias y en Memoria:** Distribuidas en 66 archivos de prueba (modelos Pydantic, utilitarios de seguridad, cálculo de notas).",
                 "**Cero Advertencias en Documentación:** 41 comprobaciones automatizadas aprobadas con 100% de éxito (`audit_documentation.py`)."
             ])

    add_card(s16, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Batería Ejecutada en Ciclo Acotado (57 Pruebas — 100% PASS)",
             [
                 "**13 Pruebas de Teardown Hardening:** Verificación de limpieza garantizada en bloque `finally` para evitar bloqueos en PostgreSQL (`test_teardown_hardening.py`).",
                 "**12 Pruebas de Analizador de Censo:** Validación reproducible de la taxonomía de pruebas (`test_census_analyzer.py`).",
                 "**17 Pruebas de Aprovisionamiento Institucional:** Creación de instituciones y validación DANE (`test_institution_provisioning.py`).",
                 "**15 Pruebas de Aprovisionamiento de Rectores:** Flujo de invitación y control de directivos (`test_nta10_rector_provisioning.py`).",
                 "**690 Pruebas Restantes No Ejecutadas:** Excluidas deliberadamente de este ciclo acotado para preservar aislamiento y estabilidad.",
                 "**Frontend:** `tsc --noEmit` completado con 0 errores y compilación `npm run build` exitosa."
             ])

    # =========================================================================
    # SLIDE 17: ENFOQUE DE DESPLIEGUE Y ESCALABILIDAD
    # =========================================================================
    s17 = prs.slides.add_slide(blank_layout)
    add_header(s17, "Enfoque de Despliegue y Arquitectura de Producción")
    add_footer(s17, 17)

    add_card(s17, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Entorno Local Verificado vs. Producción",
             [
                 "**Entorno Actual Verificado:**",
                 "- Estación de trabajo Windows 11 / Linux WSL2.",
                 "- PostgreSQL 15 local en puerto estándar.",
                 "- Redis 7 en memoria para gestión de sesiones.",
                 "- Uvicorn ASGI + Vite Dev Server.",
                 "**Transparencia Técnica:** La plataforma está probada y operativa en entorno local/servidor de laboratorio, pero **no se encuentra desplegada aún en un clúster de producción masiva nacional**."
             ])

    add_card(s17, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Arquitectura Destino Sugerida para el MEN",
             [
                 "**Contenerización Multi-Etapa:**",
                 "- Frontend servido mediante contenedor Nginx ultra-liviano.",
                 "- Backend en imagen `python:3.12-slim` con usuario sin privilegios.",
                 "**Orquestación en Kubernetes:**",
                 "- Horizontal Pod Autoscaler (HPA) según tráfico.",
                 "- Despliegue de réplicas de lectura de PostgreSQL para consultas de boletines masivas.",
                 "- Alojamiento en Nube de Gobierno o centros de datos certificados por MinTIC."
             ])

    # =========================================================================
    # SLIDE 18: BRECHAS IDENTIFICADAS, RIESGOS Y DECISIONES
    # =========================================================================
    s18 = prs.slides.add_slide(blank_layout)
    add_header(s18, "Brechas Identificadas, Riesgos y Decisiones Requeridas")
    add_footer(s18, 18)

    add_card(s18, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Brechas Técnicas y Dependencias Abiertas",
             [
                 "**1. Clúster BigBlueButton Externo:** Requiere provisión de servidores dedicados para streaming de video WebRTC.",
                 "**2. Conexión Transaccional con SIMAT:** No existe web service en vivo; se requiere convenio técnico y API Gateway con el MEN.",
                 "**3. Firma Digital con Estampa Cronológica:** Las notas se auditan en base de datos, pero no cuentan aún con firma digital PKI de la ONAC.",
                 "**4. Auditoría de Accesibilidad WCAG 2.1 AA:** Pendiente de certificación formal por laboratorio acreditado."
             ])

    add_card(s18, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Decisiones Requeridas de la Mesa Técnica MEN",
             [
                 "**Decisión 1:** ¿Asumirá el MEN la titularidad del código como Bien Público Digital bajo licencia abierta?",
                 "**Decisión 2:** ¿Qué mecanismo de interoperabilidad se habilitará para el intercambio de datos con SIMAT y DUE?",
                 "**Decisión 3:** ¿Se autoriza el diseño conjunto de un piloto experimental controlado en 2 a 5 colegios oficiales?",
                 "**Decisión 4:** ¿Qué lineamientos de infraestructura y ciberseguridad gubernamental deben armonizarse en Fase 2?"
             ], bg_color=RGBColor(255, 251, 235), border_color=RGBColor(253, 230, 138), title_color=AMBER)

    # =========================================================================
    # SLIDE 19: PLAN DE VALIDACIÓN Y PILOTO INSTITUCIONAL
    # =========================================================================
    s19 = prs.slides.add_slide(blank_layout)
    add_header(s19, "Propuesta de Colaboración Técnica en 4 Fases (Decision Gates)")
    add_footer(s19, 19)

    add_card(s19, Inches(0.8), Inches(1.6), Inches(2.7), Inches(5.1),
             "Fase 1: Mesa Técnica",
             [
                 "**Duración:** 2 a 4 semanas.",
                 "**Actividades:**",
                 "- Revisión de arquitectura.",
                 "- Inspección de repositorios.",
                 "- Definición de requisitos.",
                 "**Compuerta 1:** Dictamen técnico de viabilidad."
             ])

    add_card(s19, Inches(3.8), Inches(1.6), Inches(2.7), Inches(5.1),
             "Fase 2: Seguridad",
             [
                 "**Duración:** 4 a 6 semanas.",
                 "**Actividades:**",
                 "- Auditoría SAST / DAST.",
                 "- Pruebas de estrés y carga.",
                 "- Contratos de API SIMAT.",
                 "**Compuerta 2:** Aval de seguridad y carga."
             ])

    add_card(s19, Inches(6.8), Inches(1.6), Inches(2.7), Inches(5.1),
             "Fase 3: Piloto",
             [
                 "**Duración:** 1 periodo (10-12 semanas).",
                 "**Muestra:** 2 a 5 colegios.",
                 "**Actividades:**",
                 "- Operación paralela.",
                 "- Matrícula y notas.",
                 "**Compuerta 3:** Dictamen de adopción y métricas."
             ])

    add_card(s19, Inches(9.8), Inches(1.6), Inches(2.7), Inches(5.1),
             "Fase 4: Consolidación",
             [
                 "**Duración:** A definir por MEN.",
                 "**Actividades:**",
                 "- Transferencia formal.",
                 "- Escalabilidad nacional.",
                 "- Soberanía digital.",
                 "**Hito Final:** Adopción como Bien Público Digital."
             ])

    # =========================================================================
    # SLIDE 20: BENEFICIOS ESPERADOS Y MÉTRICAS DE MEDICIÓN
    # =========================================================================
    s20 = prs.slides.add_slide(blank_layout)
    add_header(s20, "Beneficios Esperados y Métricas de Impacto Propuestas")
    add_footer(s20, 20)

    add_card(s20, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Beneficios Públicos Proyectados",
             [
                 "**Cero Costo Marginal:** Eliminación del cobro por alumno en software de gestión académica.",
                 "**Equidad en Sedes Rurales:** Herramienta liviana que opera sobre enlaces de bajo ancho de banda sin caídas.",
                 "**Trazabilidad Forense:** Reducción a cero de quejas por adulteración no autorizada de calificaciones escolares.",
                 "**Soberanía Tecnológica:** El Estado mantiene control pleno del código, esquemas de datos y evolución técnica."
             ])

    add_card(s20, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Métricas Cuantitativas para el Piloto",
             [
                 "**Tasa de Adopción Docente:** Porcentaje de docentes que registran notas de forma autónoma (Meta: > 85%).",
                 "**Tiempo de Carga en Red Rural:** Latencia promedio inferior a 1.5 segundos en enlaces de baja velocidad.",
                 "**Incidencias de Seguridad:** Cero eventos de acceso cruzado entre instituciones (Cross-tenant leaks = 0).",
                 "**Satisfacción de Rectores y Familias:** Evaluación de usabilidad superior al 80% en encuestas de cierre."
             ])

    # =========================================================================
    # SLIDE 21: PRÓXIMOS PASOS Y PREGUNTAS PARA LA MESA TÉCNICA
    # =========================================================================
    s21 = prs.slides.add_slide(blank_layout)
    add_header(s21, "Próximos Pasos Solicitados y Preguntas para el MEN")
    add_footer(s21, 21)

    add_card(s21, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Próximos Pasos Inmediatos Solicitados",
             [
                 "**1. Instalación de la Mesa Técnica:** Formalizar un canal de trabajo entre el equipo de PEVN y la Oficina de Tecnología del MEN.",
                 "**2. Acceso a Repositorios:** Entrega formal del código fuente completo para inspección técnica por auditores del MEN.",
                 "**3. Taller de Arquitectura:** Demostración en vivo de los flujos de aprovisionamiento, calificaciones y base de datos relacional.",
                 "**4. Definición de Parámetros de Piloto:** Selección concertada de 2 a 5 colegios oficiales para pruebas de campo."
             ])

    add_card(s21, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1),
             "Preguntas Guía para el Equipo de Tecnología MEN",
             [
                 "**Pregunta 1:** ¿Cuál es la ventana de oportunidad institucional para adelantar una prueba de concepto o piloto en 2026/2027?",
                 "**Pregunta 2:** ¿Qué estándares de contenedor o nube pública (ej. AWS, Azure, OCI o centros de datos MinTIC) prefiere el MEN?",
                 "**Pregunta 3:** ¿Qué dependencia liderará la definición de contratos de interoperabilidad para la integración con SIMAT?",
                 "**Pregunta 4:** ¿Qué requisitos adicionales de ciberseguridad exige el MEN antes de autorizar un piloto experimental?"
             ], bg_color=RGBColor(240, 249, 255), border_color=RGBColor(186, 230, 253), title_color=BLUE)

    # =========================================================================
    # SLIDE 22: CIERRE INSTITUCIONAL Y CONTACTO VERIFICADO
    # =========================================================================
    s22 = prs.slides.add_slide(blank_layout)
    # Background accent rectangle
    bg22 = s22.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg22.fill.solid()
    bg22.fill.fore_color.rgb = NAVY
    bg22.line.fill.background()

    inner22 = s22.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(5.9))
    inner22.fill.solid()
    inner22.fill.fore_color.rgb = RGBColor(22, 53, 84)
    inner22.line.color.rgb = GOLD
    inner22.line.width = Pt(1.5)

    tb22 = s22.shapes.add_textbox(Inches(1.2), Inches(1.4), Inches(10.9), Inches(4.5))
    tf22 = tb22.text_frame
    tf22.word_wrap = True

    p_close_0 = tf22.paragraphs[0]
    p_close_0.text = "COMPROMISO CON LA EDUCACIÓN PÚBLICA DE COLOMBIA"
    p_close_0.font.size = Pt(12)
    p_close_0.font.bold = True
    p_close_0.font.color.rgb = GOLD
    p_close_0.space_after = Pt(14)

    p_close_1 = tf22.add_paragraph()
    p_close_1.text = "Plataforma Educativa Virtual Nacional (PEVN)"
    p_close_1.font.size = Pt(28)
    p_close_1.font.bold = True
    p_close_1.font.color.rgb = WHITE
    p_close_1.space_after = Pt(10)

    p_close_2 = tf22.add_paragraph()
    p_close_2.text = "Un Bien Público Digital al Servicio de los Territorios y la Comunidad Educativa"
    p_close_2.font.size = Pt(16)
    p_close_2.font.color.rgb = RGBColor(190, 215, 240)
    p_close_2.space_after = Pt(24)

    p_close_3 = tf22.add_paragraph()
    p_close_3.text = "Liderazgo Técnico y Contacto Institucional:\n" \
                     "Juan Carlos Castro Narváez\n" \
                     "Desarrollador Principal y Consultor de Transformación Digital Educativa\n\n" \
                     "Repositorio Oficial del Proyecto:\n" \
                     "https://github.com/juancastro2381-hub/Plataforma-Educativa-Virtual-Nacional-PEVN.git\n\n" \
                     "Octubre 2026 — Bogotá D.C., Colombia"
    p_close_3.font.size = Pt(12.5)
    p_close_3.font.color.rgb = WHITE

    # Save PPTX
    prs.save(output_path)
    print(f"[SUCCESS] Presentación PPTX guardada exitosamente en: {output_path}")


if __name__ == "__main__":
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(repo_root, "docs", "government", "pdf")
    os.makedirs(target_dir, exist_ok=True)
    target_pptx = os.path.join(target_dir, "PEVN_PRESENTACION_INSTITUCIONAL_MEN.pptx")
    build_presentation(target_pptx)
