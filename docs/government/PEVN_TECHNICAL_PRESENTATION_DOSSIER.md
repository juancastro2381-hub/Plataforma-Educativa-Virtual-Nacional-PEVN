# PEVN — DOSSIER DE PRESENTACIÓN TÉCNICA
## ARQUITECTURA DETALLADA, COMPONENTES, MODELOS DE DATOS Y ESTADO DE PREPARACIÓN (DOC-01)

**Destinatarios:** Comités Técnicos Evaluadores, Arquitectos de Software de MinTIC y MEN, Equipos de Ciberseguridad (ColCERT) e Ingenieros de Sistemas  
**Marco Metodológico:** AI Software Factory v1.2 — Technical Evaluation Dossier  
**Fecha:** 13 de Octubre de 2026 (Actualización Consolidada)  
**Carácter:** Read-Only Technical Assessment  

---

## 1. Taxonomía de Evaluación Técnica Obligatoria

En este informe técnico, cada aseveración, subsistema o capacidad de PEVN se clasifica explícitamente en una o varias de las siguientes siete dimensiones taxonómicas:
- **[A] Implemented:** Código fuente estructurado, compilable y presente en el repositorio.
- **[B] Tested:** Verificado y validado mediante pruebas automatizadas (unitarias, integración o E2E).
- **[C] Architecturally Prepared:** Diseñado bajo patrones desacoplados que permiten la extensión sin rediseño estructural.
- **[D] Requires External Infrastructure:** Requiere servidores físicos, clústeres, proxies o hardware que debe ser provisto externamente.
- **[E] Requires Institutional Decision:** Depende de una directriz, acuerdo de gobierno o decisión del Ministerio o Secretaría de Educación.
- **[F] Requires Legal Review:** Requiere concepto o formalización por parte de asesores jurídicos del Estado.
- **[G] Not Yet Empirically Validated:** Funciona a nivel de diseño y pruebas locales, pero no ha sido probado con estrés de carga en producción.

---

## 2. Topología Arquitectónica General

PEVN adopta el patrón de **Micro-Monolito Modular Asíncrono** desacoplado de una **Single Page Application (SPA)** reactiva, complementado con bases de datos relacionales ACID y cachés en memoria:

```
[ NAVEGADOR WEB / PWA ] 
        │
        ▼ (HTTPS / TLS 1.3 en Producción)
[ REVERSE PROXY / INGRESS / NGINX / WAF ]
        │
        ├──► /assets/* ──► [ Frontend SPA: React 18 / TypeScript 5.7 / Vite 6 ]
        │
        └──► /api/v1/* ──► [ Backend REST: FastAPI 0.110+ / Python 3.12 ]
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
            [ PostgreSQL 16 ]  [ Redis 7 ]  [ IMeetingProvider ]
            (Datos ACID/JSONB   (Sesiones/   (BigBlueButton /
             32 Migraciones)    Caché/Queue)   Mock Adapter)
                    │
                    ▼
            [ Local / S3 File Storage ]
            (Evidencias / Tareas / Adjuntos)
```

- **Clasificación:** `[A] Implemented` | `[B] Tested` | `[C] Architecturally Prepared`.

---

## 3. Arquitectura del Backend
- **Tecnologías:** Python 3.12, FastAPI 0.110+, Uvicorn ASGI server, SQLAlchemy 2.0 (AsyncIO con `asyncpg`), Pydantic v2 Settings.
- **Estructura de Capas:**
  - Capa de Controladores REST: `backend/app/api/v1/endpoints/` (30 controladores modulares).
  - Capa de Inyección de Dependencias y Seguridad: `backend/app/api/deps.py`.
  - Capa de Servicios de Dominio: `backend/app/services/` (20 servicios especializados).
  - Capa de Modelado ORM: `backend/app/models/` (26 archivos de modelo relacional).
  - Capa de Auditoría Inmutable: `backend/app/audit/database_service.py`.
- **Delimitación Transaccional:** Control explícito de confirmación a nivel de controlador (`await db.commit()`), garantizando atomicidad y previniendo rollbacks implícitos tras peticiones exitosas.
- **Cobertura de Pruebas Automatizadas:** **704 pruebas de backend colectadas** en `pytest` (suites unitarias y de endpoints ejecutadas con 100% de éxito; 196 pruebas de frontend ejecutadas con 100% PASS en `vitest`).
- **Clasificación:** `[A] Implemented` | `[B] Tested`.

---

## 4. Arquitectura del Frontend
- **Tecnologías:** React 18.3.1, TypeScript 5.7.3, Vite 6.0.5, Tailwind CSS 3.4.17, React Router DOM 6.28.0, Axios 1.7.9.
- **Gestión de Estado y Seguridad de Tokens:** Estado en memoria volátil de React (`AuthContext`). **Cero almacenamiento en `localStorage`, `sessionStorage` ni `IndexedDB`**, como medida de mitigación frente al robo persistente de credenciales mediante XSS.
- **Soporte PWA:** Integración de Service Worker (`vite-plugin-pwa`) para almacenamiento en caché de activos estáticos y soporte de instalación en navegadores modernos.
- **Cliente HTTP y Single-Flight Refresh:** Interceptores Axios que inyectan el token Bearer en memoria y manejan transparentemente errores 401 mediante una cola *single-flight refresh* llamando a `/api/v1/auth/refresh`.
- **Cobertura de Pruebas:** **196 pruebas en 29 archivos de suite (100% PASS)** en `vitest`.
- **Clasificación:** `[A] Implemented` | `[B] Tested` | `[C] Architecturally Prepared`.

---

## 5. Arquitectura de Base de Datos y Persistencia
- **Motor:** PostgreSQL 16.4 con driver asíncrono de alto rendimiento `asyncpg`.
- **Evolución del Esquema:** **32 migraciones lineales y determinísticas** gestionadas con Alembic (`backend/migrations/versions/`).
- **Modelo de Doble Usuario:**
  - `pevn_admin`: Propietario del esquema para ejecución de migraciones.
  - `pevn_app`: Usuario de mínimos privilegios para el runtime (`SELECT`, `INSERT`, `UPDATE`, `DELETE`), con privilegios `CREATE TABLE/SCHEMA` expresamente revocados.
- **Catálogo Oficial DANE:**
  - `official_institution_catalog`: 18,031 Establecimientos Educativos con índice B-Tree en `dane_code`.
  - `official_campus_catalog`: 51,521 Sedes físicas con vinculación a la institución principal.
  - `institutions`: 38 Tenants operacionales aprovisionados.
- **Clasificación:** `[A] Implemented` | `[B] Tested`.

---

## 6. Modelo RBAC de 11 Roles y Aclaración de Auditoría
El sistema implementa 11 roles canónicos con jerarquía numérica estricta:
- `superadmin` (Nivel 100): Operaciones técnicas globales, diagnósticos de tenant.
- `national_admin` (Nivel 90): Supervisión ministerial y catálogo nacional.
- `department_admin` (Nivel 80): Secretaría departamental, supervisión de municipios no certificados.
- `municipality_admin` (Nivel 70): Secretaría municipal, activación de rectores locales.
- `institution_admin` (Nivel 60): Soporte técnico de la institución educativa.
- `rector` (Nivel 50): Máxima autoridad institucional, sellado de períodos SIEE.
- `coordinator` (Nivel 40): Coordinación general y directiva delegada.
- `academic_coordinator` (Nivel 40): Gestión de asignaciones docentes y planes curriculares.
- `teacher` (Nivel 30): Gestión de salones y materias dentro de su *Teacher Scope*.
- `student` (Nivel 20): Portal del estudiante con tareas, notas y observador.
- `guardian` (Nivel 10): Portal familiar con selector dinámico de hijos (N:M).

> [!NOTE]
> **ACLARACIÓN SOBRE AUDITORÍA TÉCNICA:**
> El rol `AUDITOR` **no existe como rol configurado de usuario en el sistema**. La auditoría técnica se ejecuta mediante `superadmin`/`national_admin` a través de `/operations/tenant-diagnostics` y la tabla inmutable `audit_logs`.
- **Clasificación:** `[A] Implemented` | `[B] Tested`.

---

## 7. Módulos Funcionales Principales y su Clasificación

### 7.1 Evaluación SIEE (Decreto 1290 de 2009)
- Parámetros por institución (`SieePolicy`), 4 escalas nacionales (Superior, Alto, Básico, Bajo), consolidación híbrida con justificación obligatoria (`adjustment_reason`), nivelaciones con tope y cierre de período sellado.
- **Clasificación:** `[A] Implemented` | `[B] Tested`.

### 7.2 Compatibilidad SIMAT y Matrícula
- Fichas civiles con código SIMAT, documentos nacionales (C.C., T.I., R.C., PPT), control de cupos máximos por aula. Separación de identidad digital desacoplada.
- **Clasificación:** `[A] Implemented` | `[B] Tested` | `[C] Architecturally Prepared` | `[E] Requires Institutional Decision`.

### 7.3 Aulas Virtuales Sincrónicas (BigBlueButton)
- Interfaz abstracta `IMeetingProvider` con adaptador `BBBAdapter`, firmas criptográficas SHA-1/256, telemetría de asistencia y grabaciones.
- Verificado mediante proveedor simulado Mock.
- **Clasificación:** `[A] Implemented` | `[B] Tested` | `[D] Requires External Infrastructure`.

### 7.4 Convivencia Escolar (Ley 1620 de 2013)
- Observador del estudiante Tipos I, II y III con descargos, compromisos restaurativos y reserva legal con aislamiento `Blind 404`.
- **Clasificación:** `[A] Implemented` | `[B] Tested`.

### 7.5 Comunicaciones Institucionales y Acuses Electrónicos
- Circulares con segmentación de audiencia y acuse de recibo electrónico con registro de timestamp UTC e IP.
- **Clasificación:** `[A] Implemented` | `[B] Tested`.

### 7.6 Planeación Curricular Docente
- Módulo de unidades didácticas, DBA y estándares de competencias articulados con tareas escolares.
- **Clasificación:** `[A] Implemented` | `[B] Tested`.

---

## 8. Seguridad y Protección Anti-IDOR
- Hashing de contraseñas con **Argon2id** (64 MB, 3 iteraciones, 16 bytes de sal).
- Tokens JWT de acceso volátiles en memoria de React; refresh tokens en cookies HttpOnly con rotación de familia y detección de replay.
- Aislamiento multi-tenant con verificación obligatoria de `institution_id` y respuestas `Blind 404` para prevenir ataques IDOR.
- Sanitización de entradas, parametrización de consultas y análisis de Magic Bytes en adjuntos (límite 10 MB).
- **Clasificación:** `[A] Implemented` | `[B] Tested`.
