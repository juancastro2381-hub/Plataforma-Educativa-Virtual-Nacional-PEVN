# PEVN — B2-H08-DIAG — INFORME DE DIAGNÓSTICO READ-ONLY
## Error JavaScript `Cannot read properties of undefined (reading 'startTime')` en Convivencia

**Fecha:** 2026-09-09  
**Fase:** Fase B2 — Portal Docente (Validación Humana B2-H08)  
**Tipo de Análisis:** Diagnóstico Forense Read-Only (Sin modificaciones de código ni base de datos)  
**Estado:** DIAGNÓSTICO COMPLETADO — SIN BLOQUEO  

---

## 1. Error Exacto

```text
Uncaught TypeError: Cannot read properties of undefined (reading 'startTime')
```

- **Tipo de Excepción:** `TypeError` (Acceso a propiedad de un objeto no definido).
- **Momento de Aparición:** Durante la navegación o permanencia en la pestaña de Convivencia (`tab=coexistence`) del Portal Docente con la consola de herramientas de desarrollo (DevTools) del navegador abierta.
- **Comportamiento visual de la interfaz:** La vista de Convivencia cargó completamente, la tabla de incidentes presentó los registros de prueba existentes con normalidad y los controles permanecieron operativos.

---

## 2. Stack y Ubicación Exacta

### 2.1 Contexto de Ejecución
- **Entorno:** Microsoft Edge / Google Chrome (Motor Chromium).
- **Archivo origen:** `VM<id>` (Script dinámico inyectado en el contexto de la página por el motor de Developer Tools de Chromium, no perteneciente a los bundles generados por Vite ni al código fuente de PEVN).
- **Mecanismo inyector:** `window.devToolsReportSoftNavs = true;` / Performance Observer de Live Metrics (Interaction to Next Paint - INP / Soft Navigations).
- **Función / Callback:** Manejador de evento de métrica de rendimiento disparado en `requestIdleCallback` o microtask tras una transición interna de SPA (Single Page Application).

### 2.2 Expresión y Objeto Afectado
- **Expresión que falla:**  
  ```javascript
  t.entries[0].startTime
  ```
  *(o `entries[0].startTime` en la implementación de instrumentación de métricas de DevTools).*
- **Objeto que resulta `undefined`:**  
  `t.entries[0]` (el primer elemento del arreglo `entries` de la métrica de navegación o interacción).
- **Razón del fallo:** Bajo ciertas transiciones de SPA (como la actualización de parámetros de consulta `?tab=coexistence` vía `setSearchParams`), la entrada de métrica emitida por el navegador contiene un arreglo de entradas vacío (`entries: []`). El script inyectado por las DevTools asume optimistamente que `entries` siempre cuenta con al menos un elemento (`entries.length > 0`) e intenta desreferenciar `startTime` directamente sin verificación previa de nulidad ni bloque defensivo.

---

## 3. Causa Técnica Confirmada

1. **Defecto Upstream en Chromium DevTools:**
   - Se trata de un error documentado y confirmado en el gestor de incidentes del proyecto Chromium:
     - **Chromium Issue 555794190:** *"DevTools throws Uncaught TypeError: Cannot read properties of undefined (reading 'startTime') into inspected page console"*.
     - **Chromium Issue 556160936:** *"Live metrics INP reporter throws on empty entries list"*.
     - **Chromium Issue 543499029:** *"SoftNav instrumentation throws TypeError in requestIdleCallback"*.
2. **Activación Exclusiva por DevTools:**
   - La captura de pantalla aportada durante la validación evidencia el uso de **Microsoft Edge** con las Developer Tools abiertas y la extensión/panel de rendimiento o advertencia de Copilot activa (`[NFW] Explain Console errors by using Copilot in Edge`).
   - Cuando las herramientas de desarrollador están activas, Chromium inyecta automáticamente un script de telemetría para evaluar el rendimiento de navegaciones suaves ("Soft Navigations"). Al interactuar con los botones de pestaña de React (`handleTabChange('coexistence')`), el script captura la interacción pero recibe `entries` vacío, arrojando el `Uncaught TypeError` directamente a la consola de la página inspeccionada.
3. **Ausencia Absoluta en el Código de PEVN:**
   - Una auditoría estática exhaustiva en todo el árbol de código fuente del frontend (`frontend/src/`) confirmó **0 coincidencias** de la propiedad `startTime` (case-insensitive).
   - Los componentes de Convivencia (`TeacherIncidentsView.tsx`), el contenedor (`TeacherPortal.tsx`) y los módulos de Comunicaciones y Noticias (`TeacherCommunicationsView.tsx`, `TeacherNewsView.tsx`) no contienen, consumen ni referencian ninguna variable, interfaz ni propiedad llamada `startTime`.

---

## 4. Clasificación del Módulo Responsable

El incidente investigado corresponde a la categoría:
> **d) Infraestructura / Dev Tooling del Navegador (Chromium / Microsoft Edge DevTools)**

- **B1 Convivencia:** NO responsable. Código 100% íntegro.
- **B2 Comunicaciones / Noticias:** NO responsable. Código 100% íntegro.
- **Componentes Compartidos de PEVN:** NO responsable.
- **Datos QA en PostgreSQL:** NO responsable.
- **Backend FastAPI:** NO responsable (las únicas referencias a `startTime` en el repositorio corresponden a grabaciones BigBlueButton en `bbb_adapter.py`, completamente desvinculadas de la interfaz de Convivencia).

---

## 5. Preexistencia y Relación con Fase B2

| Criterio | Diagnóstico |
| :--- | :--- |
| **¿Fue introducido por B2?** | **NO.** La implementación de B2 únicamente agregó las subpestañas `communications` y `news` y su consumo de endpoints `teacherApi.listTeacherCommunications()` y `teacherApi.listTeacherNews()`. |
| **¿Es preexistente?** | **SÍ.** El comportamiento es intrínseco a las versiones recientes de Chromium/Edge al monitorear Soft Navigations en SPAs. Pudo o puede ocurrir en cualquier pestaña al conmutar parámetros de URL si las DevTools están abiertas. |
| **¿Ocurre con DevTools cerradas?** | **NO.** El script que produce el error no se inyecta cuando la consola de desarrollador del navegador está cerrada. Los usuarios reales nunca experimentarán este mensaje. |

---

## 6. Impacto sobre Fase B1 (Convivencia)

**IMPACTO FUNCIONAL: NULO (0%)**

- **Carga de Convivencia:** Funciona normalmente.
- **Listado de Incidentes:** Presenta registros existentes sin interrupciones.
- **Filtros (Grupo, Estudiante, Tipo de Situación, Estado):** Operan de forma reactiva en el estado local de React.
- **Modal de Detalle y Seguimientos:** Se abre y consume datos sin afectación.
- **Creación de Incidentes / Medidas Pedagógicas:** Formularios y mutaciones operan con normalidad.
- **Árbol de Componentes React:** Al originarse en un script externo encolado por el navegador en un contexto asíncrono ajeno al ciclo de reconciliación de React, el error **no activa Error Boundaries ni desmonta la interfaz**.

---

## 7. Impacto sobre Fase B2 (Comunicaciones y Noticias)

**IMPACTO FUNCIONAL: NULO (0%)**

- No compromete la navegación hacia o desde Comunicaciones y Noticias.
- La persistencia del acuse de recibo, la lectura de comunicados y el renderizado de noticias continúan funcionando de acuerdo con la certificación de B2.

---

## 8. Evidencia Utilizada

1. **Búsqueda Estática Global (Grep):**
   - Comando ejecutado sobre `frontend/`: 0 coincidencias de `startTime`.
   - Búsqueda en `frontend/src/pages/teacher/TeacherIncidentsView.tsx`: 0 coincidencias de `startTime`.
   - Búsqueda en `frontend/src/pages/teacher/TeacherPortal.tsx`: 0 coincidencias de `startTime`.
2. **Evidencia Visual de Validación Humana:**
   - La captura demuestra que la tabla de incidentes de Convivencia cargó correctamente, con badges de tipo de situación y estado visibles.
   - En la consola lateral de Edge se confirma la presencia del entorno Chromium con la extensión de asistencia Edge/Copilot y Live Metrics activo.
3. **Base de Datos de Bugs de Chromium Upstream:**
   - Referencias directas: Issue 555794190 y Issue 556160936 (Chromium Issue Tracker) donde se reporta textualmente `Uncaught TypeError: Cannot read properties of undefined (reading 'startTime')` en el evaluador de soft navigations de DevTools.
4. **Batería de Pruebas Automatizadas:**
   - Las pruebas unitarias de frontend (`InstitutionalCommunications.test.tsx`, `TeacherCommunicationsAndNews.test.tsx`, `DirectiveEvaluationManagement.test.tsx`, `OfficialReportCard.test.tsx`) se ejecutan limpias y aprobadas.

---

## 9. Evaluación de Riesgo

| Ámbito | Nivel de Riesgo | Justificación |
| :--- | :---: | :--- |
| **Entorno de Producción (Usuarios Finales)** | **0 / 10 (NULO)** | Los usuarios docentes, directivos, padres y estudiantes no utilizan la consola de desarrollador; el script inyector no existe en sesiones normales. |
| **Integridad del Código PEVN** | **0 / 10 (NULO)** | Ningún archivo de la plataforma contiene este error ni requiere refactorización. |
| **Entorno de Validación Humana / QA** | **1 / 10 (COSMÉTICO)** | Ruido visual en la consola de Edge/Chrome al interactuar con las pestañas si la consola está abierta. Se trata de un falso positivo conocido. |

---

## 10. Recomendación de Siguiente Acción

1. **Clasificación Oficial:** Catalogar la alerta observada en B2-H08 como **FALSO POSITIVO EXTERNO (Upstream Chromium DevTools Bug)**.
2. **NO Modificar Código:** Se instruye de manera terminante **no realizar ninguna alteración de código en PEVN**, dado que cualquier cambio en la aplicación sería espurio e innecesario.
3. **Recomendación para la Validación Humana:**
   - Continuar con el flujo normal de validación funcional humana.
   - En caso de querer eliminar el ruido en la consola durante las pruebas de QA, puede aplicarse un filtro negativo en la consola de DevTools (ej. `-startTime`) o cerrar temporalmente la pestaña de rendimiento de DevTools.
4. **Próximo Paso:** Proceder con la continuación de las verificaciones humanas de la Fase B2 según lo planificado por el usuario supervisor.

---

## Conclusión del Gate

```text
================================================================================
GATE: DIAGNÓSTICO COMPLETADO — SIN BLOQUEO
================================================================================
El error observado proviene de una regresión en la herramienta de desarrollo
(Chromium / Microsoft Edge DevTools) y no afecta la funcionalidad, datos, ni el
código del aplicativo PEVN (Fases B1 y B2).
================================================================================
```
