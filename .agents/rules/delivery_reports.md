# Regla: Entrega de Informes de Ejecución y Evidencia Técnica
**Marco de Gobernanza:** AI Software Factory v1.2 — Implementation Evidence & Reporting Standard

Siempre que se termine una ejecución, implementación, corrección, refactorización, cambio de interfaz o remediación técnica en este repositorio:

1. **Obligatoriedad del Informe Físico:** NINGUNA IMPLEMENTACIÓN SE CONSIDERA COMPLETA SIN UN INFORME FÍSICO ESTRUCTURADO DENTRO DE `docs/reports/`.
2. **Estándar de Nomenclatura:**
   - Implementaciones: `docs/reports/PEVN_<TASK_IDENTIFIER>_IMPLEMENTATION_REPORT.md`
   - Correcciones: `docs/reports/PEVN_<ISSUE>_CORRECTION_REPORT.md`
   - Auditorías: `docs/reports/PEVN_<SUBJECT>_FORENSIC_AUDIT.md`
3. **Plantilla Mandatoria:** Debe utilizarse la estructura de 20 secciones definida en:
   `docs/reports/PEVN_IMPLEMENTATION_REPORT_TEMPLATE.md`
4. **Estructura Requerida (20 Secciones):**
   - 1. Identificación de la Tarea (fecha, rama, commit HEAD previo, clasificación, alcance)
   - 2. Objetivo del Usuario / Propietario (descripción fidedigna sin reinterpretar)
   - 3. Fuentes de Verdad Consultadas (documentos, auditorías, contratos)
   - 4. Estado Previo a la Implementación (línea base, limitaciones, defectos)
   - 5. Implementación Realizada (tabla: Archivo | Cambio | Razón)
   - 6. Archivos NO Modificados (demostración de contención de alcance)
   - 7. Reglas de Negocio / Funcionales Preservadas
   - 8. Impacto en Seguridad (modelo de seguridad, auth, RBAC, multi-tenant)
   - 9. Impacto en Base de Datos (migraciones, esquemas, datos, índices)
   - 10. Impacto en API (contratos, endpoints, dependencias frontend)
   - 11. Pruebas Ejecutadas (tabla: Suite | Comando | Resultado exacto)
   - 12. Validación Manual (entorno, ruta, rol, escenario, resultado observado; sin requerir capturas de pantalla)
   - 13. Evidencia Técnica y Registro de Trazabilidad
   - 14. Revisión de Afirmaciones y Veracidad Pública (sin sobrestimaciones; WCAG, BBB, SIMAT, despliegue nacional)
   - 15. Limitaciones Conocidas y Trabajo Pendiente
   - 16. Evaluación de Riesgo de Regresión (con justificación técnica)
   - 17. Seguridad Git (estado exacto de ramas, archivos modificados y cambios preexistentes)
   - 18. Política de Commit / Push (COMMIT = NO, PUSH = NO salvo instrucción explícita)
   - 19. Compuerta Final (PASS | CONDITIONAL PASS | BLOCKED)
   - 20. Próxima Acción Controlada (Human-in-the-Loop)
5. **Autosuficiencia:** El informe debe contener suficiente evidencia para que un revisor externo (incluyendo modelos de auditoría o ChatGPT) verifique y comprenda la ejecución sin requerir capturas de pantalla del asistente.
6. **No Modificación de Código de Producto:** Esta regla es estrictamente de gobernanza y no altera la lógica de negocio ni la metodología congelada.
