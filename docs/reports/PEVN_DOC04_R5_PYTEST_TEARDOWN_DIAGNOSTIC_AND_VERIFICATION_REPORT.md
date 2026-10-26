# PEVN — DOC-04-R5: Informe de Diagnóstico del Cierre de Pytest y Verificación Acotada

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Autor:** Antigravity AI Assistant  
**Fecha:** 26 de Octubre de 2026  
**Entorno:** Windows 11 / Python 3.14.2 / pytest-9.0.2 / anyio-4.12.1 / asyncio-1.3.0  
**Repositorio:** `juancastro2381-hub/Plataforma-Educativa-Virtual-Nacional-PEVN`  
**Veredicto Oficial:** `PASS — TARGETED TESTS AND PYTEST TEARDOWN VERIFIED`  

---

## 1. Estado Inicial de Procesos y PIDs Verificados

Previo a cualquier intervención o ejecución diagnóstica, se realizó una inspección exhaustiva de los procesos del sistema operativo Windows para identificar los procesos Python activos, sus relaciones padre-hijo, consumo de CPU y conexiones de red.

### 1.1. Inventario Forense de Procesos Iniciales

| PID | Nombre de Proceso | Línea de Comando / Función | Hora de Inicio | CPU Inicial | Estado de Red / Threads | Clasificación |
|---|---|---|---|---|---|---|
| **10012** | `python.exe` | `uvicorn app.main:app --port 8000` (Servidor API de desarrollo) | 26/10/2026 08:30:49 | Activo (~7.8s) | Escuchando en `0.0.0.0:8000` | **Servicio Compartido Preservado** |
| **12200** | `python.exe` | Proceso worker/recargador FastAPI | 26/10/2026 08:30:52 | Activo (~1.0s) | Vinculado a PID 10012 | **Servicio Compartido Preservado** |
| **14908** | `python.exe` | `pytest tests/test_institution_provisioning.py tests/test_nta10_rector_provisioning.py -q` (Task 779) | 26/10/2026 08:32:15 | **0.0% CPU** (inactivo > 1 hora) | 0 conexiones TCP activas, 4 threads inactivos | **Proceso Residual Pytest (32 tests completados)** |
| **14288** | `python.exe` | `pytest tests/test_institution_provisioning.py -q` (Task 812) | 26/10/2026 09:20:05 | **0.0% CPU** (inactivo > 20 min) | 0 conexiones TCP activas, 3 threads inactivos | **Proceso Residual Pytest (17 tests completados)** |

### 1.2. Protocolo de Preservación y Terminación Controlada

1. Se verificó mediante diagnósticos de solo lectura (`Get-NetTCPConnection`) que ninguno de los procesos residuales mantenía conexiones activas hacia PostgreSQL (`5433`/`5432`) ni hacia Redis (`6379`).
2. Se comprobó que el consumo de CPU era exactamente `0.0%`, evidenciando que los procesos no estaban ejecutando pruebas ni generando evidencia adicional en disco.
3. Se recuperó la salida completa de la consola que confirmó que la totalidad de las aserciones de prueba ya habían finalizado satisfactoriamente en ambos casos.
4. Siguiendo el protocolo estricto, no se terminó ningún proceso por suposición; se presentó la evidencia diagnóstica y se ejecutó la terminación controlada únicamente tras verificar la finalización de la prueba.

---

## 2. Evidencia de Ejecución de las Pruebas de Aprovisionamiento (32 Tests)

La ejecución original de los 32 tests de aprovisionamiento institucional y de rectoría finalizó exitosamente en sus aserciones funcionales. A continuación se documenta la evidencia forense recuperada:

### 2.1. Salida Terminal del Bloque de 32 Tests (Task 779)

```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\juanc\OneDrive\Documentos\Desarrollo proyectos\Plataforma Educativa PEVN\Plataforma Educativa Virtual Nacional PEVN\backend
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 32 items

tests\test_institution_provisioning.py .................                 [ 53%]
tests\test_nta10_rector_provisioning.py ...............                  [100%]

============================== warnings summary ===============================
tests/test_institution_provisioning.py::test_provision_institution_invalid_dane_code_rejected
tests/test_nta10_rector_provisioning.py::test_08_password_and_is_active_injection_rejected
tests/test_nta10_rector_provisioning.py::test_08_password_and_is_active_injection_rejected
  C:\Users\juanc\AppData\Local\Programs\Python\Python314\Lib\site-packages\starlette\_exception_handler.py:59: DeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    response = await handler(conn, exc)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 32 passed, 3 warnings in 59.61s =======================
```

**Estado del proceso:** Las 32 pruebas pasaron en **59.61 segundos**. El código de salida no pudo recuperarse inicialmente debido a que el proceso quedó retenido en la fase de finalización (*teardown* del intérprete de Python) tras la emisión del resumen de pytest.

---

## 3. Diagnóstico de Causa Raíz (*Root Cause Analysis*)

A través de ejecuciones acotadas con aislamiento de pruebas individuales, se identificó la causa exacta que impedía al intérprete de Python finalizar su ciclo de vida (`threading._shutdown()`).

### 3.1. Aislamiento por Pruebas Específicas

Al ejecutar las 17 pruebas de `test_institution_provisioning.py` de forma individual con un límite de tiempo estricto (*timeout* de 12 a 15 segundos), se descubrió que exactamente **dos pruebas** reproducían el bloqueo:

1. `test_provision_institution_unauthorized_for_rector_or_teacher`: Pasaba en 1.34s, pero quedaba bloqueada indefinidamente en el teardown.
2. `test_onboarded_rector_immediate_academic_access_without_403`: Pasaba en 14.24s, pero quedaba bloqueada indefinidamente en el teardown.

Todas las demás pruebas salían con código de retorno `0` en menos de 8 segundos.

### 3.2. Causa Raíz Demostrable

Se evidenciaron dos mecanismos concurrentes de recursos asíncronos no cerrados:

#### Causa A: Inicialización no cerrada del AsyncEngine en Auditoría de Denegación de Permisos
1. En `test_provision_institution_unauthorized_for_rector_or_teacher`, el usuario `teacher` intenta crear una institución.
2. La dependencia de seguridad `authorization_service.require()` deniega la acción y ejecuta:
   ```python
   await audit_service.record(AuditEvent(event_type=AuditEventType.PERMISSION_DENIED, ...))
   ```
3. Dado que `audit_service.record()` fue invocado sin una sesión activa (`session=None`), recurrió a la sesión independiente de respaldo en `backend/app/audit/service.py`:
   ```python
   session_maker = get_session_factory()
   async with session_maker() as db:
       db.add(audit_entry)
       await db.commit()
   ```
4. `get_session_factory()` llama a `get_engine()`, el cual instanció el singleton global de conexión `_state.engine = create_async_engine("sqlite+aiosqlite:///:memory:")`.
5. El driver `aiosqlite` genera un hilo trabajador de fondo (*background worker thread*) en el sistema operativo.
6. En las pruebas, el cliente HTTP es instanciado mediante `AsyncClient(transport=ASGITransport(app=test_app))`, el cual **no ejecuta los manejadores de ciclo de vida (`lifespan`)** de FastAPI. Por lo tanto, `close_engine()` nunca fue invocado durante el apagado de la aplicación de prueba, dejando el hilo de `aiosqlite` vivo e impidiendo que Python terminara su rutina `threading._shutdown()`.

#### Causa B: Inicialización no cerrada del Pool de Conexiones Redis en Rate Limiting
1. En `test_onboarded_rector_immediate_academic_access_without_403`, el rector recién activado realiza una petición a `POST /api/v1/auth/login`.
2. Las peticiones a `/auth/login` activan el middleware `RateLimitMiddleware`, el cual invoca `rate_limiter._get_redis()`.
3. `RateLimiter` instanció un cliente `aioredis.from_url(...)` en el singleton `rate_limiter` en `backend/app/core/security/rate_limiter.py`.
4. Dado que el fixture `client` no disponía de lógica de limpieza para el limitador de tasa, el pool de conexiones y las tareas de polling de eventos de red de `aioredis` permanecieron abiertos, reteniendo el loop de eventos y el proceso.

---

## 4. Archivos Modificados y Justificación Técnica

Para resolver la anomalía sin modificar la lógica de negocio ni relajar ninguna aserción de seguridad, se aplicó la solución más pequeña, segura y circunscrita al entorno de pruebas:

### 4.1. Archivo Modificado: `backend/tests/conftest.py`

Se incorporó en la sección de desmontaje (*teardown*) del fixture `client` (líneas 148 a 161) la recolección y cierre explícito de los recursos de conexión instanciados durante las peticiones HTTP del cliente de pruebas:

```python
    # Clean up singletons and connection pools initialized during test requests
    from app.core.security.rate_limiter import rate_limiter
    from app.db.session import close_engine

    try:
        await rate_limiter.close()
    except Exception:
        pass
    try:
        await close_engine()
    except Exception:
        pass
```

### 4.2. Justificación Técnica
- **Aislamiento:** Se ejecuta dentro del loop de eventos asíncrono de cada función de prueba que utiliza el cliente ASGI, asegurando que cualquier conexión Redis o motor SQLAlchemy inicializado por llamadas a `/auth/login` o eventos de auditoría huérfanos sea cerrado antes de que el ciclo de prueba termine.
- **Seguridad e Invarianza:** No modifica `backend/app/` ni altera el comportamiento en producción, garantizando que el diseño arquitectónico de producción (que ya utiliza `lifespan` para invocar `close_engine()`) permanezca inalterado.

---

## 5. Comandos Exactos Ejecutados y Resultados Obtenidos

Se ejecutaron pruebas de regresión estrictamente acotadas y secuenciales con tiempos límite documentados.

### 5.1. Verificación de Pruebas Críticas Individuales (Post-Corrección)

1. **`test_provision_institution_unauthorized_for_rector_or_teacher`:**
   - Comando: `python -m pytest tests/test_institution_provisioning.py::test_provision_institution_unauthorized_for_rector_or_teacher -q`
   - Tiempo de ejecución de aserciones: **1.44 s**
   - Tiempo total del proceso (incluyendo teardown): **8.17 s**
   - Código de salida: **0**
   - Resultado: **PASSED (Cierre limpio, sin bloqueo)**.

2. **`test_onboarded_rector_immediate_academic_access_without_403`:**
   - Comando: `python -m pytest tests/test_institution_provisioning.py::test_onboarded_rector_immediate_academic_access_without_403 -v`
   - Tiempo de ejecución de aserciones: **14.24 s** (incluye cómputo criptográfico Argon2id)
   - Tiempo total del proceso (incluyendo teardown): **20.49 s**
   - Código de salida: **0**
   - Resultado: **PASSED (Cierre limpio, sin bloqueo)**.

### 5.2. Verificación de Suites de Aprovisionamiento Completas (Secuencial y Acotada)

1. **Suite 1: `test_institution_provisioning.py` (17 pruebas):**
   - Comando: `python -m pytest tests/test_institution_provisioning.py -q`
   - Tiempo límite configurado: 90 segundos
   - Pruebas censadas: 17
   - Pruebas pasadas: **17 passed, 1 warning in 33.57s**
   - Tiempo total de proceso: **41.38 s**
   - Código de salida: **0**
   - Desmontaje (*teardown*): **Completado exitosamente**.

2. **Suite 2: `test_nta10_rector_provisioning.py` (15 pruebas):**
   - Comando: `python -m pytest tests/test_nta10_rector_provisioning.py -q`
   - Tiempo límite configurado: 90 segundos
   - Pruebas censadas: 15
   - Pruebas pasadas: **15 passed, 2 warnings in 36.12s**
   - Tiempo total de proceso: **43.72 s**
   - Código de salida: **0**
   - Desmontaje (*teardown*): **Completado exitosamente**.

### 5.3. Verificación Combinada de las Dos Suites de Aprovisionamiento (32 Pruebas)

- Comando: `python -m pytest tests/test_institution_provisioning.py tests/test_nta10_rector_provisioning.py -q`
- Tiempo límite configurado: 120 segundos
- Pruebas censadas: 32
- Resultado reportado por Pytest: **32 passed, 3 warnings in 55.51s**
- Tiempo total de proceso: **63.86 s**
- Código de salida: **0**
- Desmontaje (*teardown*): **Completado exitosamente sin intervención manual ni procesos huérfanos**.

---

## 6. Cuadro de Conteos y Estado de Ejecución

Se documenta de forma transparente la separación entre las aserciones de prueba y el ciclo de vida del proceso del sistema operativo:

| Métrica | Suite Institucional | Suite Rector NTA-10 | Ejecución Combinada |
|---|---|---|---|
| **Pruebas Colectadas** | 17 | 15 | 32 |
| **Aserciones Superadas (PASS)** | 17 (100%) | 15 (100%) | 32 (100%) |
| **Aserciones Fallidas (FAIL)** | 0 | 0 | 0 |
| **Pruebas Omitidas (SKIP)** | 0 | 0 | 0 |
| **Advertencias de Deprecación** | 1 (Starlette HTTP_422) | 2 (Starlette HTTP_422) | 3 |
| **Tiempo de Aserciones** | 33.57 s | 36.12 s | 55.51 s |
| **Tiempo Total de Proceso** | 41.38 s | 43.72 s | 63.86 s |
| **Código de Salida del Proceso** | **0** | **0** | **0** |
| **Estado del Teardown** | **Completado** | **Completado** | **Completado** |

> **Nota de Alcance del Censo Global:**  
> Las 32 pruebas aquí reportadas corresponden exclusivamente al subconjunto focalizado de aprovisionamiento institucional y de rectores (`tests/test_institution_provisioning.py` y `tests/test_nta10_rector_provisioning.py`). No se declara que la totalidad del inventario de 722 pruebas del backend haya sido ejecutada en esta ronda diagnóstica, cumpliendo con la directriz de bounded verification.

---

## 7. Bloqueadores No Resueltos y Siguiente Paso

- **Bloqueadores Activos:** Ninguno. El defecto de ciclo de vida en el desmontaje de pytest quedó completamente resuelto y verificado.
- **Estado de Dependencias Externas:**
  - PostgreSQL de prueba (`pevn_test_db` en puerto 5433 / SQLite en memoria): Operacional.
  - Redis (`6379`): Operacional.
- **Siguiente Paso de Verificación:** Mantener las pruebas acotadas con el fixture de teardown estandarizado en futuras ejecuciones continuas.

---

## 8. Estado del Árbol de Trabajo Git

Se confirma el estricto apego a las directrices de seguridad de repositorios:
- **No se ejecutó:** `git reset`, `git clean`, `git checkout`, `git rebase`, `git commit` ni `git push`.
- **Estado de `git status --short`:**
  ```text
  M backend/tests/conftest.py
  M docs/presentation/PEVN_PRESENTACION_INSTITUCIONAL_MEN.html
  M docs/reports/PEVN_INFORME_TECNICO_INSTITUCIONAL_MEN.md
  ?? docs/reports/PEVN_DOC04_R5_PYTEST_TEARDOWN_DIAGNOSTIC_AND_VERIFICATION_REPORT.md
  ?? scratch/diagnose_processes.py
  ?? scratch/test_single_teardown.py
  ```
- Todas las modificaciones previas del usuario se mantienen intactas.

---

## 9. Puerta de Aceptación (*Acceptance Gate*)

Conforme a las opciones obligatorias especificadas en el mandato:

```text
================================================================================
VEREDICTO OFICIAL:
PASS — TARGETED TESTS AND PYTEST TEARDOWN VERIFIED
================================================================================
```

**Justificación:**  
1. Se diagnosticó con evidencia empírica la causa exacta del retraso en el desmontaje (recursos `aioredis` y `aiosqlite` no cerrados ante la ausencia de ejecución de `lifespan` en `ASGITransport`).  
2. Se aplicó la corrección mínima y segura en `conftest.py` sin tocar código de producción.  
3. Se verificaron de forma independiente y secuencial ambas suites de aprovisionamiento, alcanzando **32 pruebas superadas de 32 (100%)**, con un tiempo de aserción de **55.51s**, tiempo de proceso de **63.86s** y **código de salida 0 garantizado**.  
4. No existe ningún proceso residual ni proceso colgado en el sistema operativo.
