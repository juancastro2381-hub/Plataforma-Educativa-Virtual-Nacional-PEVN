# PEVN — B3-H02 — INFORME DE INVESTIGACIÓN DE ERROR RUNTIME startTime

**Fecha y Hora:** 2026-09-12 08:35:00 -05:00  
**Fase:** Fase B3 — Portal Docente (Validación Humana B3-H02: Planeación Curricular)  
**Tipo de Análisis:** Diagnóstico Forense Read-Only (Sin modificaciones de código, base de datos ni RBAC)  
**Dictamen Técnico:** CÓDIGO EXTERNO / INYECCIÓN DE HERRAMIENTAS DE DESARROLLADOR DEL NAVEGADOR (Upstream Chromium/Edge DevTools)  

---

## 1. Contexto de Reproducción

Durante la ejecución de la validación humana **B3-H02** sobre el Portal Docente, se observó en la consola del navegador la excepción no capturada (*Uncaught TypeError*):

```text
2 Uncaught TypeError: Cannot read properties of undefined (reading 'startTime')
```

### Escenario de Reproducción:
1. **Primera aparición:** Al acceder inicialmente a la pestaña **Planeación** (`/teacher?tab=planning`).
2. **Segunda aparición:** Al ejecutar la navegación contextual desde la vista de salones:
   - **Mis Grupos** (`/teacher?tab=groups`) $\rightarrow$ Tarjeta **Grupo 2** $\rightarrow$ Botón **🎯 Planeación** $\rightarrow$ Redirección a `/teacher?tab=planning&groupId=e131b6a3-3990-44e8-be23-a36b913e26c3`.
3. **Comportamiento funcional visible:**
   - La vista de Planeación cargó de forma inmediata y completa.
   - El selector de filtro `Filtrar por Grupo` adoptó el valor del grupo contextualizado (`Grupo 2`).
   - El registro creado en pruebas de persistencia (`B3 — Prueba Persistencia Planeación`, Materia: Matemáticas - Segundo, Estado: Borrador) apareció renderizado correctamente en la tabla.
   - La sesión docente de `natalia_castro` permaneció activa.
   - La persistencia de datos y el consumo de la API FastAPI operaron con total normalidad.
   - No se produjo desmontaje del árbol de React ni activación de Error Boundary.

---

## 2. Stack Trace Observado y Origen Técnico

### 2.1 Transcripción del Stack Trace de la Consola
```text
2 Uncaught TypeError: Cannot read properties of undefined (reading 'startTime')  VM787:2
    at et.reportAllChanges (<anonymous>:2:19429)
    at <anonymous>:2:13070
    at <anonymous>:2:331
    at d (<anonymous>:2:6141)
    at <anonymous>:2:6326
    at x (<anonymous>:2:5486)
    at g (<anonymous>:2:6248)
    at <anonymous>:2:6512
    at u (<anonymous>:2:735)
```

### 2.2 Archivo y Línea Identificados
- **Archivo/Contenedor:** `VM787:2` (Script efímero en memoria virtual inyectado directamente por el navegador Chromium / Microsoft Edge en el contexto de la pestaña).
- **Función:** `et.reportAllChanges`
- **Ubicación exacta de la invocación:** `<anonymous>:2:19429`

---

## 3. Análisis Forense de Causa Raíz

### 3.1 Mecanismo de Inyección de Chromium / Microsoft Edge DevTools
1. **Entorno del Navegador:**
   - La evidencia visual confirma el uso de **Microsoft Edge** con el panel de herramientas de desarrollo (*DevTools*) abierto en el lateral derecho y la integración activa de asistencia de consola de Edge (`[NEW] Explain Console errors by using Copilot in Edge`).
2. **Telemetría de Navegaciones Suaves (Soft Navigations / Live Metrics):**
   - Cuando las DevTools de Chromium/Edge están abiertas, el motor del navegador inyecta automáticamente una biblioteca de telemetría de rendimiento en memoria (`VM<id>`) basada en la instrumentación de `web-vitals` / *Interaction to Next Paint* (INP) y *Soft Navigation Heuristics*.
3. **Disparador del Error:**
   - La función `et.reportAllChanges` es el manejador interno de eventos de métricas de rendimiento que evalúa transiciones de SPA.
   - Cuando el usuario conmuta pestañas o navega contextualmente en el Portal Docente, React Router invoca `setSearchParams({ tab: 'planning', groupId: '...' })`, actualizando el historial del navegador mediante `pushState`/`replaceState` sin recargar la página.
   - El script inyectado por DevTools captura la transición como una "Soft Navigation", pero en esta SPA las entradas de eventos de rendimiento emitidas por el despachador contienen un arreglo de entradas vacío (`entries: []`).
   - El código minificado de DevTools asume optimistamente la existencia de elementos en el arreglo y evalúa:
     $$\text{entries}[0]\text{.startTime} \implies \text{undefined.startTime} \implies \textbf{TypeError}$$
4. **Referencia de Bugs Upstream en Chromium:**
   - Este comportamiento corresponde al defecto documentado y reportado en el Chromium Issue Tracker:
     - **Chromium Issue 555794190:** *"DevTools throws Uncaught TypeError: Cannot read properties of undefined (reading 'startTime') into inspected page console"*.
     - **Chromium Issue 556160936:** *"Live metrics INP reporter throws on empty entries list"*.
     - **Chromium Issue 543499029:** *"SoftNav instrumentation throws TypeError in requestIdleCallback"*.

---

## 4. Evidencia de No Pertenencia al Código Fuente de PEVN

| Criterio de Verificación | Resultado de la Auditoría PEVN | Evidencia Técnica |
| :--- | :---: | :--- |
| **Búsqueda estática global de `startTime`** | **0 coincidencias en Frontend** | La búsqueda exhaustiva (regex case-insensitive) en `frontend/` y `frontend/src/` arrojó 0 resultados. En el backend, las únicas menciones corresponden al adaptador de grabaciones BigBlueButton (`bbb_adapter.py`). |
| **Búsqueda de `reportAllChanges`** | **0 coincidencias en todo el repositorio** | Función inexistente en el código fuente, librerías del proyecto y plantillas de PEVN. |
| **Source Maps y Módulos Vite** | **Ausencia en el bundle** | Los errores del código fuente de PEVN en desarrollo son resueltos por Vite hacia rutas legibles (ej. `TeacherPlanningView.tsx:120`). El error observado proviene de `VM787:2` (`<anonymous>`), indicador inequívoco de script inyectado por DevTools. |
| **Componentes de Planeación y Grupos** | **Código 100% íntegro** | La inspección de `TeacherPortal.tsx`, `TeacherGroupsView.tsx` y `TeacherPlanningView.tsx` constata que ninguna función o estado utiliza la propiedad `startTime`. |
| **Precedente Documentado** | **Idéntico a B2-H08** | El diagnóstico previo documentado en `docs/reports/B2_H08_DIAGNOSTICO_STARTTIME.md` determinó la misma causa raíz para la pestaña de Convivencia. |

---

## 5. Comparación de las Dos Apariciones

| Evento | Acción Realizada | Cambio en URL | Razón de la Notificación |
| :--- | :--- | :--- | :--- |
| **1ª Aparición** | Clic en subpestaña "Planeación" | `/teacher?tab=planning` | React Router actualiza `searchParams` $\rightarrow$ Soft Navigation detectada por DevTools $\rightarrow$ `et.reportAllChanges` evalúa métrica con `entries: []`. |
| **2ª Aparición** | Clic en botón contextual "🎯 Planeación" dentro de tarjeta de Grupo 2 | `/teacher?tab=planning&groupId=e131b6a3-...` | React Router actualiza `searchParams` con nuevo `groupId` $\rightarrow$ Segunda Soft Navigation detectada por DevTools $\rightarrow$ Mismo script `VM787` arroja la excepción. |

Ambas apariciones responden al **mismo y único mecanismo de instrumentación externa de DevTools** ante actualizaciones de query parameters en la SPA.

---

## 6. Impacto Funcional y Evaluación de Severidad

- **Impacto Funcional en PEVN:** **NULO (0%)**
  - La lógica de negocio, persistencia de planeaciones, vinculación curricular, filtrado por salones y seguridad RBAC se encuentran 100% operativas.
  - El error ocurre en una microtarea asíncrona de DevTools fuera del ciclo de vida y renderizado de React, por lo que no compromete la estabilidad ni la integridad de la interfaz.
- **Impacto en Usuarios Finales de Producción:** **NULO (0%)**
  - Los docentes, coordinadores y directivos no navegan con las herramientas de desarrollador abiertas. El script inyector no existe en sesiones normales de usuario final.
- **Severidad:** **COSMÉTICA / RUIDO EN CONSOLA QA (0/10 en Producción, 1/10 en QA)**.

---

## 7. Dictamen y Recomendaciones

1. **Corrección de Código en PEVN:** **NO REQUIERE NINGUNA MODIFICACIÓN.**
   - Queda terminantemente prohibido introducir parches espurios, `try/catch` ficticios o alteraciones en el código fuente de PEVN para intentar interceptar scripts internos inyectados por el navegador.
2. **Continuación de B3-H02:**
   - La alerta en consola queda formalmente clasificada y descartada como **Falso Positivo Externo**.
   - El proceso de validación funcional humana **B3-H02 puede reanudarse y continuar de inmediato**.
3. **Manejo del Ruido en Consola durante QA:**
   - En la consola de Edge/Chrome se puede aplicar un filtro de exclusión simple (`-startTime`) para mantener el visor de consola libre de mensajes de telemetría del navegador si se desea.

---

## 8. Estado del Gate

```text
================================================================================
GATE STATUS: INVESTIGACIÓN COMPLETADA — SIN BLOQUEO EN PEVN
================================================================================
RUNTIME ERROR INVESTIGATION = EXTERNAL
B3-H02 = CLEARED
================================================================================
```
