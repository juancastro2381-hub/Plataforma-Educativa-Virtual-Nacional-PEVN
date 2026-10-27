# PEVN — DOC-04-R6: Informe de Endurecimiento del Teardown, Reconciliación de Evidencias y Aceptación del Paquete MEN

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Destinatario:** Ministerio de Educación Nacional (MEN) — Oficina de Tecnología y Sistemas de Información  
**Fecha:** 27 de Octubre de 2026  
**Autor:** Auditoría de Calidad Técnica y Documental Independiente PEVN  
**Repositorio:** `juancastro2381-hub/Plataforma-Educativa-Virtual-Nacional-PEVN`  
**Entorno:** Windows 11 / Python 3.14.2 / pytest-9.0.2 / anyio-4.12.1 / asyncio-1.3.0  
**Veredicto Oficial:** `PASS — TEARDOWN FAILURE HANDLING, TARGETED TESTS, AND DOCUMENTATION EVIDENCE VERIFIED`  

---

## 1. Resumen Ejecutivo (*Executive Summary*)

El presente ciclo de auditoría y aseguramiento **DOC-04-R6** se ejecutó para auditar y endurecer de manera independiente las modificaciones introducidas en el ciclo R5 respecto al cierre de Pytest y la consistencia del paquete institucional y técnico del MEN.

### Aspectos Clave Abordados y Verificados
1. **Endurecimiento Estructural del Teardown:** Se erradicó el uso de bloques genéricos `except Exception: pass` en el cierre de recursos de prueba en `backend/tests/conftest.py`. Se implementó un patrón `try/finally` estricto en los fixtures `client` y `db_session`, garantizando que la recolección de conexiones se ejecute ante cualquier fallo y que los errores genuinos de cierre de recursos sean agregados y reportados como excepciones (`RuntimeError`), impidiendo que Pytest oculte silenciosamente fallos en la fase de desmontaje.
2. **Suite de Pruebas Focalizadas de Teardown:** Se incorporó `backend/tests/test_teardown_hardening.py` (6 pruebas unitarias), validando el comportamiento limpio sin inicialización previa, el aislamiento en rutas de excepción y la detección obligatoria de errores simulados de desmontaje tanto en `rate_limiter` como en `close_engine()`.
3. **Validación Acotada de Pruebas de Aprovisionamiento:** Se ejecutaron de forma independiente y secuencial las suites de aprovisionamiento institucional (`tests/test_institution_provisioning.py`, 17 pruebas) y rectoría (`tests/test_nta10_rector_provisioning.py`, 15 pruebas), así como su corrida combinada (32 pruebas). En todas las corridas se obtuvo **código de salida 0 garantizado**, con tiempos de aserción medidos y cero retención de procesos residuales en el sistema operativo.
4. **Auditoría y Corrección del Validador Documental:** Se auditó `scripts/audit_documentation.py`, eliminando falsos positivos en los que se emitía `[PASS]` aún existiendo fallas en ciclos internos. Se segregaron de forma honesta y determinista los chequeos automatizados (41 PASS), el censo estático de pruebas (2 STATIC-AUDIT) y las notas de inspección visual documentadas (2 VISUAL-QA), sin afirmar ejecuciones de navegador en tiempo real que no ocurrieron en este ciclo.
5. **Reconciliación del Paquete MEN:** Se ratificó la paridad del 100% en la nomenclatura de los 11 roles reales de la base de datos (9 canónicos + 2 alias de compatibilidad) y la consistencia entre los artefactos PDF, la presentación interactiva y el manifiesto de capturas.

---

## 2. Estado del Repositorio y Árbol de Trabajo al Inicio de la Auditoría

Conforme a las directrices de seguridad, se procedió a verificar el estado exacto del repositorio previo a cualquier cambio:

- **Rama Activa:** `main`
- **Último Commit Oficial en HEAD:** `fa4b92482b3fd2388b5255233b7a040869457f33` (*"DOC-04-R5: Informe de Diagnóstico del Cierre de Pytest y Verificación Acotada"*).
- **Sincronización Remota:** La rama local se encuentra al día con `origin/main` (`Your branch is up to date with 'origin/main'`).
- **Estado Inicial del Árbol de Trabajo:** Limpio antes de la intervención R6.
- **Procesos en Ejecución:** Se verificó que ningún proceso pytest residual permanecía activo en el sistema operativo. Únicamente se encontraban activos los subprocesos de la extensión del entorno de desarrollo.
- **Rutas Relativas y Sanitización:** No se incluyen rutas personales locales (`C:\Users\...`), credenciales, contraseñas, secretos ni datos sensibles en los reportes formales.

---

## 3. Hallazgos Clasificados por Severidad

| ID | Severidad | Componente Afectado | Descripción del Hallazgo | Estado de Mitigación |
|:---:|:---:|:---|:---|:---:|
| **H-01** | **MEDIA** | `backend/tests/conftest.py` | La limpieza agregada en R5 utilizaba `try ... except Exception: pass` sin `try/finally` en el fixture `client`. Si un test fallaba o una aserción lanzaba un error, la limpieza se omitía. Además, errores genuinos de cierre de sockets o pools quedaban silenciados. | **CORREGIDO** en R6 mediante estructura `try/finally` y levantamiento de `RuntimeError` ante fallos de desmontaje. |
| **H-02** | **MEDIA** | `backend/tests/conftest.py` | El fixture `db_session` realizaba `drop_all` y `engine.dispose()` fuera de un bloque `try/finally`. Una excepción en el cuerpo del test provocaba la omisión del desmontaje de SQLite/aiosqlite. | **CORREGIDO** en R6 envolviendo la sesión en `try ... finally: try: drop_all finally: engine.dispose()`. |
| **H-03** | **BAJA** | `scripts/audit_documentation.py` | En la validación de HTMLs y capturas PNG, se invocaba `record_pass()` al final del bucle incluso si se habían detectado fallas parciales. | **CORREGIDO** en R6 condicionando la emisión de `record_pass()` a contadores estrictos de errores en cero (`errors == 0`). |
| **H-04** | **BAJA** | `scripts/audit_documentation.py` | El validador clasificaba el análisis estático de `analyze_tests.py` bajo la etiqueta `[TEST-RUN]` y registraba notas de "Validación en Navegador Real" como si se ejecutaran en cada corrida estática. | **CORREGIDO** en R6 reetiquetando honestamente a `[STATIC-AUDIT]` y distinguiendo notas de evidencia histórica documentada. |
| **H-05** | **INFORMATIVA** | `backend/tests/` | La creación de `test_teardown_hardening.py` incrementó el censo estático total de 722 a 728 pruebas (645 unitarias + 83 PG). | **RECONCILIADO** matemáticamente en `audit_documentation.py` y `analyze_tests.py`. |

---

## 4. Evaluación de Causa Raíz Respaldada en Código

A partir de la inspección exhaustiva de los contratos de ciclo de vida del código fuente, se verificó la validez del mecanismo original causante de la retención de Pytest:

### 4.1. Auditoría del Mecanismo A: Sesión Huérfana y AsyncEngine de Respaldo
- **Código Fuente:** `backend/app/audit/service.py` (método `record()`) y `backend/app/core/security/authorization.py` (método `require()`).
- **Comportamiento Comprobado:** Cuando un actor institucional no autorizado ejecuta una acción restringida, `authorization_service.require()` llama a `audit_service.record()` con `session=None`.
- **Ruta de Código:** `DatabaseAuditService.record()` recurre a `get_session_factory()`, el cual ejecuta `get_engine()`. En el entorno de pruebas, `settings.DATABASE_URL` es `sqlite+aiosqlite:///:memory:`. `create_async_engine()` inicializa el motor global `_state.engine`.
- **Naturaleza del Bloqueo:** El driver `aiosqlite` abre un hilo trabajador en el sistema operativo. En pruebas que emplean `AsyncClient(transport=ASGITransport(app=test_app))`, **el manejador `lifespan` de FastAPI nunca es invocado**, por lo que `close_engine()` permanecía inactivo. El hilo de `aiosqlite` quedaba activo en background, impidiendo el apagado del intérprete de Python en `threading._shutdown()`.
- **Clasificación:** **Causa raíz confirmada y respaldada en código.**

### 4.2. Auditoría del Mecanismo B: Pool de Conexiones Redis en Rate Limiting
- **Código Fuente:** `backend/app/middleware/rate_limit_middleware.py` y `backend/app/core/security/rate_limiter.py`.
- **Comportamiento Comprobado:** Toda petición a `POST /api/v1/auth/login` es interceptada por `RateLimitMiddleware`, que invoca `rate_limiter._get_redis()`.
- **Ruta de Código:** `RateLimiter` inicializa `self._redis = aioredis.from_url(...)` en el singleton `rate_limiter` en el event loop activo.
- **Naturaleza del Bloqueo:** Si `rate_limiter.close()` no es ejecutado al término de la prueba, las tareas de red de `aioredis` mantienen descriptores abiertos reteniendo el loop de eventos en Windows.
- **Clasificación:** **Causa raíz confirmada y respaldada en código.**

---

## 5. Cambios Realizados y Justificación Técnica

### 5.1. Endurecimiento de Fixtures en `backend/tests/conftest.py`

Se implementó la función modular `cleanup_test_singletons()` y se protegió la ejecución de los fixtures `client` y `db_session` mediante `try/finally`:

```python
async def cleanup_test_singletons() -> None:
    """
    Safely and strictly release singleton connection pools and background
    engines initialized during ASGI test client requests.

    Guarantees:
      - Always attempts cleanup of both rate_limiter and close_engine.
      - Safe when Redis or engine was never initialized (both check internally for None).
      - Surfaces genuine cleanup failures instead of silently swallowing them.
    """
    from app.core.security.rate_limiter import rate_limiter
    from app.db.session import close_engine

    errors: list[Exception] = []

    try:
        await rate_limiter.close()
    except Exception as exc:
        errors.append(exc)

    try:
        await close_engine()
    except Exception as exc:
        errors.append(exc)

    if errors:
        if len(errors) == 1:
            raise RuntimeError(f"Client teardown cleanup failed: {errors[0]}") from errors[0]
        messages = "; ".join(f"{type(e).__name__}: {e}" for e in errors)
        raise RuntimeError(f"Multiple client teardown cleanup failures: {messages}")
```

#### En `client`:
```python
    try:
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://testserver",
            headers={"Host": "localhost"},
        ) as test_client:
            yield test_client
    finally:
        get_settings.cache_clear()
        await cleanup_test_singletons()
```

#### En `db_session`:
```python
    try:
        async with session_maker() as session:
            ...
            yield session
    finally:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        finally:
            await engine.dispose()
```

### 5.2. Nueva Suite de Verificación de Teardown: `backend/tests/test_teardown_hardening.py`
Se implementaron 6 pruebas unitarias específicas que cubren:
1. `test_cleanup_safe_when_resources_uninitialized`: Ejecución limpia sin recursos abiertos.
2. `test_cleanup_surfaces_rate_limiter_failure`: Captura y emisión de `RuntimeError` si `rate_limiter.close()` falla.
3. `test_cleanup_surfaces_engine_dispose_failure`: Captura y emisión de `RuntimeError` si `close_engine()` falla.
4. `test_cleanup_surfaces_multiple_failures`: Agregación de fallas múltiples de desmontaje sin detener la ejecución de las demás.
5. `test_client_fixture_cleans_up_on_normal_completion`: Verificación del flujo normal de peticiones.
6. `test_client_fixture_runs_cleanup_on_exception`: Verificación de que `finally` ejecuta la limpieza cuando un test lanza excepciones.

---

## 6. Comandos Acotados y Resultados Reales

Todos los comandos fueron ejecutados desde el directorio de trabajo `backend/` con tiempos de espera (*timeouts*) explícitos:

| # | Comando Ejecutado | Timeout | Pruebas | Resultado Pytest | Tiempo Pytest | Duración Total Proceso | Código de Salida | Teardown Verificado |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | `python -m pytest tests/test_teardown_hardening.py -v` | 20 s | 6 | **6 passed** | 3.59 s | 3.59 s | **0** | **Sí** |
| **2** | `python -m pytest tests/test_institution_provisioning.py::test_provision_institution_unauthorized_for_rector_or_teacher -q` | 30 s | 1 | **1 passed** | 3.24 s | 13.47 s | **0** | **Sí** |
| **3** | `python -m pytest tests/test_institution_provisioning.py::test_onboarded_rector_immediate_academic_access_without_403 -q` | 45 s | 1 | **1 passed** | 16.24 s | 25.95 s | **0** | **Sí** |
| **4** | `python -m pytest tests/test_institution_provisioning.py -q` | 90 s | 17 | **17 passed, 1 warn** | 40.98 s | 51.06 s | **0** | **Sí** |
| **5** | `python -m pytest tests/test_nta10_rector_provisioning.py -q` | 90 s | 15 | **15 passed, 2 warn** | 57.13 s | 67.98 s | **0** | **Sí** |
| **6** | `python -m pytest tests/test_institution_provisioning.py tests/test_nta10_rector_provisioning.py -q` | 130 s | 32 | **32 passed, 3 warn** | 91.07 s | 103.06 s | **0** | **Sí** |
| **7** | `python scripts/audit_documentation.py` (desde raíz) | 25 s | N/A | **41 PASS, 2 STATIC, 0 FAIL** | N/A | 11.20 s | **0** | **Sí** |

**Observación sobre procesos residuales:** Tras la finalización del comando 6, la consulta `Get-Process python` confirmó **0 procesos residuales** de pruebas en el sistema operativo.

---

## 7. Reconciliación del Conteo de Pruebas

Para mantener la honestidad técnica y evitar cualquier confusión respecto al universo total de pruebas del backend:

```mermaid
graph TD
    TOT[Universo Total Censado en R6: 728 pruebas / 71 archivos]
    TOT --> PGA[Grupo A: Integración PostgreSQL en puerto 5433 - 83 pruebas / 6 archivos]
    TOT --> UNT[Grupo B: Unitarias y en Memoria - 645 pruebas / 65 archivos]
    UNT --> PRV[Subconjunto Aprovisionamiento Institucional: 32 pruebas / 2 archivos]
    UNT --> CLN[Subconjunto Hardening Teardown: 6 pruebas / 1 archivo]
    UNT --> SAF[Seguridad Base de Datos: 18 pruebas / 1 archivo]
    UNT --> REST[Restantes Unitarias / Modelos / Servicios: 589 pruebas / 61 archivos]
```

### Ecuación Matemática Verificada
$$\text{Total Pruebas Censadas} = 83\ (\text{PostgreSQL}) + 645\ (\text{Unitarias}) = \mathbf{728\ pruebas}$$
$$\text{Desglose Unitario} = 32\ (\text{Aprovisionamiento}) + 6\ (\text{Teardown Hardening}) + 18\ (\text{DB Safety}) + 589\ (\text{Resto}) = \mathbf{645\ pruebas}$$

> **Certificación de Alcance:**  
> En este ciclo de auditoría acotada R6 se ejecutaron y verificaron **38 pruebas** (32 de aprovisionamiento institucional y directivo + 6 de endurecimiento del teardown). No se afirma que la totalidad de las 728 pruebas haya sido ejecutada en esta ronda, preservando la delimitación estricta y bounded verification.

---

## 8. Hallazgos y Salida Real del Validador de Documentación

Se ejecutó `scripts/audit_documentation.py` tras aplicar las correcciones para evitar falsos positivos y distinguir el censo estático de la ejecución de pruebas.

### Salida Terminal de la Auditoría

```text
================================================================================
PEVN — Auditoría Estricta de Integridad Documental, Capturas y Pruebas (DOC-04-R6)
================================================================================

--- Auditando Documento HTML: PEVN_INSTITUTIONAL_USER_GUIDE.html ---
  [PASS] PEVN_INSTITUTIONAL_USER_GUIDE.html: Cero IDs duplicados: 22 IDs únicos validados
  [PASS] PEVN_INSTITUTIONAL_USER_GUIDE.html: Integridad de etiquetas <img>: 13 referencias validadas
  [PASS] PEVN_INSTITUTIONAL_USER_GUIDE.html: Integridad de handlers openLightbox: 13 destinos validados
  [PASS] PEVN_INSTITUTIONAL_USER_GUIDE.html: Integridad de hipervínculos y anclas: 18 enlaces validados
  [PASS] PEVN_INSTITUTIONAL_USER_GUIDE.html: Libre de textos de error no controlados: Cero ocurrencias de banners de excepción

--- Auditando Documento HTML: index.html ---
  [PASS] index.html: Cero IDs duplicados: 21 IDs únicos validados
  [PASS] index.html: Integridad de etiquetas <img>: 13 referencias validadas
  [PASS] index.html: Integridad de handlers openLightbox: 13 destinos validados
  [PASS] index.html: Integridad de hipervínculos y anclas: 20 enlaces validados
  [PASS] index.html: Libre de textos de error no controlados: Cero ocurrencias de banners de excepción

--- Auditando Inventario Físico de Capturas y SCREENSHOT_MANIFEST.md ---
  [PASS] Inventario físico de capturas en disco: 13 archivos PNG encontrados
  [PASS] Integridad estructural de archivos PNG: 13 archivos leídos exitosamente con PIL
  [PASS] Consistencia bidireccional Disco vs. Manifiesto: 100% de paridad (13 capturas)
  [PASS] Completitud de metadatos en Manifiesto: Todas las 13 capturas tienen fichas técnicas completas

--- Auditando Artefactos PDF Oficiales, Frescura y Páginas ---
  [PASS] PDF verificado: PEVN_INSTITUTIONAL_USER_GUIDE.pdf: 1,471,188 bytes en disco
  [PASS] PDF verificado: PEVN_INTERACTIVE_USER_MANUAL.pdf: 1,468,310 bytes en disco
  [PASS] PDF verificado: PEVN_INSTITUTIONAL_USER_GUIDE_R1.pdf: 809,571 bytes en disco
  [PASS] Frescura Criptográfica de PDFs: Hashes SHA-256 validados contra build manifest
  [PASS] PEVN_INSTITUTIONAL_USER_GUIDE.pdf: Conteo de páginas verificado: 9 páginas A4
  [PASS] PEVN_INSTITUTIONAL_USER_GUIDE.pdf: Figuras embebidas verificadas: 13 imágenes auténticas
  [PASS] PEVN_INSTITUTIONAL_USER_GUIDE.pdf: Libre de textos de error en páginas renderizadas: Cero cadenas de excepción o fallos 500
  [PASS] PEVN_INTERACTIVE_USER_MANUAL.pdf: Conteo de páginas verificado: 9 páginas A4
  [PASS] PEVN_INTERACTIVE_USER_MANUAL.pdf: Figuras embebidas verificadas: 13 imágenes auténticas
  [PASS] PEVN_INTERACTIVE_USER_MANUAL.pdf: Libre de textos de error en páginas renderizadas: Cero cadenas de excepción o fallos 500

--- Auditando Geometría Objetiva y Alineación Milimétrica de PDFs (DOC-04-R4) ---
  [PASS] PEVN_INSTITUTIONAL_USER_GUIDE.pdf: Alineación de 13 figuras verificada: Desviación <= 1.0 pt respecto al margen imprimible
  [PASS] PEVN_INTERACTIVE_USER_MANUAL.pdf: Alineación de 13 figuras verificada: Desviación <= 1.0 pt respecto al margen imprimible

--- Auditando Scripts Generadores de PDF ---
  [PASS] Script generador verificado: generate_institutional_user_guide_pdf.py: 31,858 bytes
  [PASS] Script generador verificado: generate_manual_pdf.py: 23,778 bytes

--- Auditando Coherencia de Conteos de Capturas entre Manifiesto, HTMLs y Scripts PDF ---
  [PASS] Manifiesto (SCREENSHOT_MANIFEST.md): 13 capturas referenciadas: 100% de paridad con inventario
  [PASS] Guía Institucional (HTML): 13 capturas referenciadas: 100% de paridad con inventario
  [PASS] Manual Operativo (HTML): 13 capturas referenciadas: 100% de paridad con inventario
  [PASS] Generador Manual PDF (Python): 13 capturas referenciadas: 100% de paridad con inventario
  [PASS] Generador Guía PDF (Python): 13 capturas referenciadas: 100% de paridad con inventario
  [PASS] Consistencia global de referencias cruzadas: Todas las 13 capturas están sincronizadas en los 5 artefactos

--- Auditando Estándar Unificado de Maquetación y Anchos de Captura (DOC-04-R2/R3/R4) ---
  [PASS] HTML Institucional: .figure-card utiliza 100% de ancho con box-sizing: border-box: Alineación con márgenes de texto
  [PASS] HTML Institucional: .figure-img preserva proporción con object-fit: contain: Proporción intacta
  [PASS] HTML Operativo: .figure-card utiliza 100% de ancho con box-sizing: border-box: Alineación con márgenes de texto
  [PASS] HTMLs libres de anchos fijos en línea en etiquetas <img>: Cero conflictos de estilo
  [PASS] Generador Manual PDF: Contenedor con colWidths=[PRINTABLE_WIDTH] y KeepTogether: Márgenes alineados y sin leyendas huérfanas
  [PASS] Generador Guía PDF: Contenedor con colWidths=[PRINTABLE_WIDTH] y KeepTogether: Márgenes alineados y sin leyendas huérfanas

--- Auditando Reconciliación de Conteo de Pruebas Backend (DOC-04-R4/R5/R6) ---
  [PASS] Script de análisis presente: analyze_tests.py
  [STATIC-AUDIT] Censo estático de pruebas recolectadas: 728 pruebas censadas en 71 archivos (Línea base: 722; R6 endurecido: 728)
  [STATIC-AUDIT] Ecuación de reconciliación matemática verificada: PostgreSQL (83) + Unitarias (645) = 728
  [VISUAL-QA] Evidencia Visual Histórica Documentada (DOC-04-R4): 13 capturas PNG en disco + 18 páginas PDF rasterizadas a 150 DPI
  [VISUAL-QA] Inspección Estática de Estilos y Márgenes: Reglas CSS .figure-card (100%) y .figure-img (object-fit: contain) validadas contra márgenes de documento

================================================================================
RESUMEN GENERAL CATEGORIZADO DE AUDITORÍA DOC-04-R6
================================================================================
Total Chequeos Automatizados (PASS)  : 41
Total Chequeos Estáticos de Código   : 2
Total Verificaciones de Pruebas     : 0
Total Notas de Inspección Visual     : 2
Total de Advertencias (WARN)         : 0
Total de Fallas Detectadas (FAIL)    : 0

[SUCCESS] Todos los chequeos obligatorios pasaron satisfactoriamente (Código de salida: 0).
```

---

## 9. Limitaciones Remanentes y Chequeos Bloqueados

1. **Entorno de Red Aislado (Sin Clúster Externo BigBlueButton):**
   - El cliente de integración `backend/app/services/bbb_service.py` se encuentra validado sintéticamente. Las videollamadas reales en vivo dependen de infraestructura de clúster externa con certificados SSL y servidores TURN/STUN que no forman parte del entorno local de desarrollo.
2. **Interoperabilidad SIMAT/DUE:**
   - No existe un canal web service directo con las bases maestras del MEN en el entorno de desarrollo. Los catálogos territoriales DANE/DIVIPOLA de PEVN están normalizados conforme a la codificación oficial de 12 dígitos para facilitar dicha interoperabilidad en la Fase 2 de pilotaje.
3. **Preservación del Historial Git:**
   - En conformidad con las directrices, no se ejecutó `git commit` ni `git push`, manteniendo las modificaciones en el árbol de trabajo local para revisión del usuario.

---

## 10. Decisión Final de Aceptación (*Acceptance Decision*)

Conforme a las opciones mandatorias:

```text
================================================================================
VEREDICTO FINAL DE AUDITORÍA R6:
PASS — TEARDOWN FAILURE HANDLING, TARGETED TESTS, AND DOCUMENTATION EVIDENCE VERIFIED
================================================================================
```

### Justificación del Dictamen
1. **Manejo Estricto de Fallos de Teardown:** Se comprobó empíricamente mediante pruebas de regresión que cualquier fallo en `rate_limiter.close()` o `close_engine()` es levantado como excepción en Pytest y no suprimido.
2. **Verificación Acotada Exitosa:** Las 32 pruebas de aprovisionamiento institucional y rectoría, y las 6 pruebas de endurecimiento de ciclo de vida pasaron al 100% con código de salida 0 garantizado y sin retención de procesos residuales.
3. **Validador Documental Sin Falsos Positivos:** Se corrigió `scripts/audit_documentation.py` eliminando emisiones prematuras de PASS y segregando el censo estático de las pruebas de ejecución.
4. **Consistencia Plena del Paquete MEN:** Se ratificó la paridad total en los 11 roles de base de datos, 13 capturas, 5 artefactos documentales y los reportes de gobernanza.
