# Plataforma Educativa Virtual Nacional (PEVN)
## Paquete Documental Institucional y Dossier Técnico para el MEN
### Directorio Oficial de Entrega: `docs/government/pdf/`

---

**Iniciativa:** Plataforma Educativa Virtual Nacional (PEVN)  
**Destinatario Institucional:** Oficina de Tecnología y Sistemas de Información — Ministerio de Educación Nacional (MEN), República de Colombia  
**Fecha de Entrega:** Octubre 2026 | **Versión del Paquete:** 1.0-FINAL-MEN  
**Repositorio Principal:** `https://github.com/juancastro2381-hub/Plataforma-Educativa-Virtual-Nacional-PEVN.git`  
**Commit de Referencia Verificado:** `7b974951382bbd2f102274292539e98505cdae58` (rama `main`)  

---

## 1. Guía de Orientación y Documentos Autoritativos Vigentes

Este directorio contiene el paquete documental y técnico definitivo preparado para la sesión presencial de trabajo con la **Oficina de Tecnología y Sistemas de Información del Ministerio de Educación Nacional**.

Para evitar cualquier dispersión, los siguientes archivos constituyen los **documentos autoritativos vigentes** que deben ser tomados como referencia principal por los evaluadores del MEN:

| Archivo | Formato | Propósito y Audiencia Principal |
| :--- | :--- | :--- |
| **`PEVN_PRESENTACION_INSTITUCIONAL_MEN.pptx`** | PPTX (16:9) | **Presentación Oficial Editable:** 22 diapositivas estructuradas con diseño institucional gubernamental para proyección y ajuste colaborativo. |
| **`PEVN_PRESENTACION_INSTITUCIONAL_MEN.pdf`** | PDF (16:9) | **Presentación Oficial en PDF:** Versión apaisada de alta fidelidad para lectura o proyección directa en cualquier visor de PDF. |
| **`PEVN_INFORME_TECNICO_INTEGRAL_PARA_REVISION_MEN.pdf`** | PDF (A4) | **Dossier de Ingeniería Principal (16 páginas):** Informe exhaustivo con las 27 secciones técnicas, arquitectura, ciberseguridad, censo de 747 pruebas, modelo RBAC de 9 roles canónicos (11 en BD) y aspectos sujetos a validación MEN. |
| **`PEVN_INFORME_TECNICO_INTEGRAL_PARA_REVISION_MEN.md`** | Markdown | **Fuente Editable del Informe Técnico:** Archivo fuente en Markdown para control de cambios y revisión directa en repositorios de código. |
| **`PEVN_MEN_EXECUTIVE_BRIEF.pdf`** | PDF (A4) | **Resumen Ejecutivo de Alto Nivel (3 páginas):** Síntesis estratégica para directores y asesores de despacho que requieren una visión rápida en 5 minutos. |
| **`PEVN_MEN_EXECUTIVE_BRIEF.md`** | Markdown | Fuente editable del resumen ejecutivo. |
| **`PEVN_MEN_MEETING_CHECKLIST.pdf`** | PDF (A4) | **Lista de Chequeo y Protocolo de Reunión:** Protocolo para la sesión presencial, banco de preguntas críticas, evidencias a llevar y decisiones solicitadas. |
| **`PEVN_MEN_MEETING_CHECKLIST.md`** | Markdown | Fuente editable de la lista de chequeo operativa. |
| **`PEVN_MEN_DOCUMENT_INVENTORY_AND_CHANGELOG.pdf`** | PDF (A4) | **Inventario Formal y Registro de Cambios:** Tabla de conciliación de todos los archivos del directorio, mapeo de versiones y changelog formal. |
| **`PEVN_MEN_DOCUMENT_INVENTORY_AND_CHANGELOG.md`** | Markdown | Fuente editable del inventario documental. |
| **`PEVN_MEN_FINAL_CONSISTENCY_AND_RELEASE_READINESS_AUDIT.pdf`** | PDF (A4) | **Dictamen Final de Auditoría y Preparación de Lanzamiento:** Dictamen independiente de consistencia, evidencia empírica de código y catálogo, y preparación para revisión técnica del MEN. |
| **`PEVN_MEN_FINAL_CONSISTENCY_AND_RELEASE_READINESS_AUDIT.md`** | Markdown | Fuente editable del dictamen de auditoría final. |

---

## 2. Ruta de Lectura Recomendada por Perfil Institucional

- **Directores de Tecnología y Asesores de Despacho (MEN):**
  1. Iniciar con `PEVN_MEN_EXECUTIVE_BRIEF.pdf` (resumen de 3 páginas).
  2. Revisar la estructura visual en `PEVN_PRESENTACION_INSTITUCIONAL_MEN.pdf`.
  3. Consultar las preguntas clave y compromisos en `PEVN_MEN_MEETING_CHECKLIST.pdf`.
- **Arquitectos de Software e Ingenieros de Ciberseguridad (OTSI):**
  1. Examinar en detalle `PEVN_INFORME_TECNICO_INTEGRAL_PARA_REVISION_MEN.pdf`.
  2. Enfocarse en las Secciones 5 a 12 (Arquitectura, Ciberseguridad, RBAC de 9 roles canónicos / 11 en BD y Anti-IDOR).
  3. Revisar las Secciones 19 y 20 (Censo de 747 pruebas, 57 pruebas ejecutadas con 100% PASS, 690 no ejecutadas en ciclo acotado, teardown hardening y sanitización).
  4. Revisar la Sección 26 (**Aspectos sujetos a validación institucional del MEN**).
  5. Consultar el dictamen en `PEVN_MEN_FINAL_CONSISTENCY_AND_RELEASE_READINESS_AUDIT.pdf`.
- **Líderes de Sistemas Misionales (SIMAT, DUE, SINEB):**
  1. Revisar Secciones 8, 9 y 15 del informe técnico (Modelo de datos DANE, DIVIPOLA, catálogo DUE 2024 e interoperabilidad).
  2. Revisar la propuesta de piloto en Secciones 23 y 25.

---

## 3. Catálogo de Documentos Históricos Preservados

Los siguientes 13 archivos corresponden a etapas previas de trabajo (Fase 0.1 temprana) y se conservan en este directorio para garantizar la trazabilidad de ingeniería y el archivo histórico del proyecto. Se aclara que sus cifras han sido actualizadas y consolidadas en el nuevo paquete autoritativo 1.0-FINAL-MEN:

1. `PEVN_CURRENT_STATE_AND_LIMITATIONS.pdf` (Registro temprano de limitaciones).
2. `PEVN_EXECUTIVE_PRESENTATION_DOSSIER.pdf` (Dossier preliminar).
3. `PEVN_GOVERNMENT_DEMONSTRATION_RUNBOOK.pdf` (Guión de demo previo).
4. `PEVN_GOVERNMENT_DOCUMENTATION_INDEX.pdf` (Índice de fase 0.1).
5. `PEVN_GOVERNMENT_EVIDENCE_MATRIX.pdf` (Matriz de pruebas inicial).
6. `PEVN_GOVERNMENT_PRESENTATION_CHECKLIST.pdf` (Lista de chequeo previa).
7. `PEVN_GOVERNMENT_PRESENTATION_PACKAGE.pdf` (Paquete consolidado fase 0.1).
8. `PEVN_GOVERNMENT_PRESENTATION_SCRIPT.pdf` (Guión oral previo).
9. `PEVN_GOVERNMENT_QA.pdf` (Banco de preguntas temprano).
10. `PEVN_ONE_PAGE_EXECUTIVE_SUMMARY.pdf` (Resumen de una página previo).
11. `PEVN_PHASE_0_1_FINAL_REPORT.pdf` (Acta de cierre de fase 0.1).
12. `PEVN_TECHNICAL_PRESENTATION_DOSSIER.pdf` (Dossier técnico preliminar).
13. `PEVN_TECHNOLOGY_DONATION_PROPOSAL.pdf` (Propuesta de donación Apache 2.0).

---

## 4. Declaración de Integridad, Verificación y Estado OneDrive

- Todos los archivos en este directorio han sido inspeccionados, verificados en su estructura y validados contra el código fuente del proyecto en el commit verificado `7b974951382bbd2f102274292539e98505cdae58`.
- No se han realizado operaciones destructivas en el repositorio Git (`git reset`, `git clean` ni `git push`).
- **Verificación Local vs. Sincronización OneDrive:** La integridad binaria, legibilidad y completitud de todos los archivos fueron verificadas directamente sobre el sistema de archivos local de Windows. El estado de sincronización remota del cliente de Microsoft OneDrive no puede ser determinado programáticamente desde la consola de desarrollo, por lo que su confirmación en la nube permanece como una validación operativa del usuario en Windows.

---

*Directorio mantenido y administrado para la presentación oficial ante el Ministerio de Educación Nacional de Colombia.*
