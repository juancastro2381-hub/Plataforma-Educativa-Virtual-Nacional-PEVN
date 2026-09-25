# PEVN — INVENTARIO DE ARTEFACTOS DE ENTREGA TÉCNICA Y DONACIÓN AL ESTADO
## DOSSIER DE TRANSFERENCIA TECNOLÓGICA, LICENCIAMIENTO E INTEROPERABILIDAD GUBERNAMENTAL (FASE 0)

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Marco de Auditoría:** AI Software Factory v1.2 — Handover & Technological Transfer  
**Destinatarios:** Equipos Técnicos, Jurídicos y de Planeación del Ministerio de Educación Nacional (MEN) y MinTIC  
**Fecha:** 21 de Septiembre de 2026  
**Carácter:** Read-Only Inventory Assessment  

---

## 1. Alcance y Propósito de la Entrega Técnica

El presente documento consolida el **inventario exhaustivo de todos los activos de software, artefactos arquitectónicos, contratos de interfaz, esquemas de bases de datos, evidencias de calidad y manuales operativos** que componen la Plataforma Educativa Virtual Nacional (PEVN).

Este inventario ha sido estructurado para respaldar un eventual proceso de **donación, cesión de derechos o entrega técnica oficial al Estado colombiano**, garantizando que las autoridades públicas cuenten con la totalidad de insumos necesarios para operar, mantener y evolucionar la plataforma con plena soberanía tecnológica e independencia de proveedores.

---

## 2. Inventario de Activos y Artefactos de Software

### 2.1 Código Fuente del Sistema
- **Backend Service:**
  - Repositorio: Directorio `backend/`.
  - Lenguaje y Versión: Python 3.12.
  - Framework Principal: FastAPI 0.110+ con Uvicorn.
  - Capa de Datos: SQLAlchemy 2.0 (AsyncIO) + driver `asyncpg`.
  - Validación y Esquemas: Pydantic v2.
  - Módulos de Dominio: 24 archivos de modelo (`backend/app/models/`), 28 controladores REST (`backend/app/api/v1/endpoints/`), 18 servicios de dominio (`backend/app/services/`).
- **Frontend SPA Service:**
  - Repositorio: Directorio `frontend/`.
  - Lenguaje y Versión: TypeScript 5.7.3 sobre Node.js 20+.
  - Framework Principal: React 18.3.1 con Vite 6.0.5.
  - Estilos y Diseño: Tailwind CSS 3.4.17.
  - Enrutamiento: React Router DOM 6.28.0.
  - Cliente HTTP: Axios 1.7.9 tipado con interceptores de refresco.
  - Vistas y Portales: 8 portales especializados organizados en `frontend/src/pages/`.
- **Scripts de Infraestructura:**
  - `docker-compose.yml`: Orquestación local para desarrollo.
  - `Dockerfile`: Construcción multi-etapa con usuario no root (`UID 1001:pevn`).
  - `infrastructure/docker/postgres/01-init-app-user.sh`: Script de configuración de usuario de base de datos de mínimos privilegios (`pevn_app`).
  - `infrastructure/scripts/check_env.sh`: Script de validación de variables de entorno y conectividad.

---

### 2.2 Documentación de Arquitectura y Diseño
1. [docs/ARCHITECTURE.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/ARCHITECTURE.md): Visión general del sistema, jerarquía territorial y desacoplamiento de capas.
2. [docs/ADR/ADR-001-foundation-architecture.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/ADR/ADR-001-foundation-architecture.md): Decisión arquitectónica de la infraestructura base.
3. [docs/ADR/ADR-002-auth-architecture.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/ADR/ADR-002-auth-architecture.md): Decisión arquitectónica de identidad y control de acceso.
4. [docs/ADR/ADR-003-academic-domain-architecture.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/ADR/ADR-003-academic-domain-architecture.md): Decisión arquitectónica del modelo de dominio escolar colombiano.
5. [docs/phase15_institutional_communications_forensic_architecture.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/phase15_institutional_communications_forensic_architecture.md): Arquitectura de circulares, periódico y convivencia Ley 1620.
6. [docs/phase16_forensic_architecture.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/phase16_forensic_architecture.md): Arquitectura del Sistema Institucional de Evaluación (SIEE) y promoción escolar.

---

### 2.3 Documentación de Base de Datos y Persistencia
1. [docs/DATABASE.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/DATABASE.md): Especificación del motor PostgreSQL 16, modelo de usuarios (`pevn_admin` vs `pevn_app`) y parámetros de conexión.
2. **Migraciones Lineales Alembic:** 23 archivos de migración numerados consecutivamente en `backend/migrations/versions/` (revisión 001 a 023).

---

### 2.4 Documentación de Contratos de API
1. **Especificación OpenAPI v3:** Generada dinámicamente en `/api/v1/openapi.json` con esquemas Pydantic completos de petición y respuesta.
2. [docs/AUTHENTICATION.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/AUTHENTICATION.md): Contratos de endpoints de login, refresh, logout, password reset y gestión de sesiones.
3. [docs/AUTHORIZATION.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/AUTHORIZATION.md): Matriz de permisos RBAC granular y regla de contención territorial.
4. [docs/reports/B3-H12_1_SUBMISSIONS_FUNCTIONAL_CONTRACT.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/B3-H12_1_SUBMISSIONS_FUNCTIONAL_CONTRACT.md): Contrato funcional de entregas y devoluciones de tareas de estudiantes.

---

### 2.5 Documentación de Ciberseguridad y Auditoría
1. [docs/SECURITY.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/SECURITY.md): Política general de seguridad de la información y controles defensivos.
2. [docs/SECURITY_THREAT_MODEL.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/SECURITY_THREAT_MODEL.md): Modelo de amenazas STRIDE aplicado a la plataforma.
3. [docs/AUDIT.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/AUDIT.md): Estructura de la tabla `audit_logs` y política de censura automática de datos sensibles.

---

### 2.6 Documentación de Operaciones y Despliegue
1. [docs/DEPLOYMENT.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/DEPLOYMENT.md): Guía de despliegue en desarrollo y preparación para producción.
2. [docs/OPERATIONS.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/OPERATIONS.md): Monitoreo de sondas de salud, rotación de secretos y gestión de logs.
3. [docs/PHASE_8_PRODUCTION_OPERATIONS_RUNBOOK.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/PHASE_8_PRODUCTION_OPERATIONS_RUNBOOK.md): Manual de operaciones de producción y mantenimiento preventivo.
4. [docs/PHASE_10_INFRASTRUCTURE_HANDOFF.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/PHASE_10_INFRASTRUCTURE_HANDOFF.md): Especificación técnica de handoff para instalación física de BigBlueButton y Coturn.

---

### 2.7 Evidencias de Pruebas y Certificación de Fases
1. [docs/reports/PROJECT_MASTER_STATUS.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/PROJECT_MASTER_STATUS.md): Cuadro de mando maestro de fases del proyecto.
2. 52 archivos de prueba automatizada en `backend/tests/` (432 casos de prueba).
3. 18 suites de prueba en `frontend/src/test/` (123 casos de prueba).
4. 70+ reportes y actas de cierre de fase formalizadas en `docs/` y `docs/phase-reports/`.

---

## 3. Régimen de Licenciamiento y Dependencias de Terceros

### 3.1 Licencia Principal del Proyecto
- El proyecto PEVN se distribuye bajo la **Apache License, Version 2.0** ([LICENSE](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/LICENSE)).
- **Implicaciones para el Estado:**
  - Concesión irrevocable de derechos de uso, modificación, reproducción y distribución.
  - Concesión expresa de licencias de patentes de los colaboradores.
  - Libertad absoluta de auditoría del código fuente y personalización sin pago de cánones.

### 3.2 Licencias de Dependencias de Terceros
El archivo [THIRD_PARTY_LICENSES.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/THIRD_PARTY_LICENSES.md) consolida el inventario de todas las bibliotecas utilizadas en backend y frontend.
- **Tipología de Licencias:** Exclusivamente licencias permisivas de código abierto:
  - MIT License (FastAPI, Starlette, Uvicorn, React, Vite, Axios, Tailwind CSS, Vitest).
  - BSD 2-Clause / 3-Clause License (Pydantic, Click).
  - Apache-2.0 (asyncpg, cryptography, SQLAlchemy).
  - LGPL / EPL (BigBlueButton core).
- **Conformidad:** Cero dependencias bajo licencias restrictivas de tipo "Copyleft Viral" (como GPLv3 pura en librerías vinculadas al backend), garantizando la viabilidad jurídica de su adopción estatal.

---

## 4. Auditoría de Preparación para la Interoperabilidad Gubernamental

La plataforma ha sido concebida para integrarse con los sistemas estratégicos del Estado colombiano:

| Sistema Externo Gubernamental | Entidad Rectora | Estado Actual de Integración | Mecanismo de Integración Futura |
| :--- | :--- | :--- | :--- |
| **DUE / Directorio DANE** | DANE / MEN | `IMPLEMENTED` (Caché local con ingesta estructurada) | Consumo periódico de datasets abiertos de datos.gov.co o API DANE. |
| **SIMAT (Matrícula Escolar)** | Ministerio de Educación | `COMPATIBLE` (Modelos alineados con el estándar SIMAT) | Enlace mediante Web Service REST/SOAP seguro o importador masivo CSV. |
| **Carpeta Ciudadana / Gov.co** | MinTIC | `PLANNED` (No implementado actualmente) | Integración OpenID Connect (OIDC) para inicio de sesión único ciudadano. |
| **BigBlueButton (Videoclases)** | Clúster Estatal / MinTIC | `IMPLEMENTED (SOFTWARE)` (Requiere comisionamiento) | Conexión HTTP/XML con firma SHA-1/256 al clúster comisionado. |
| **Notificaciones SMS / Email** | Proveedor Estatal (4-72 / Gov.co) | `PLANNED` (Actualmente por log/consola) | Enlace mediante API REST de mensajería masiva oficial. |
| **Archivo General de la Nación** | AGN | `PLANNED` (Audit logs inmutables en base de datos) | Exportación de expedientes académicos bajo formato estándar PDF/A-1b. |

---

## 5. Documentación Faltante para una Entrega Integral

Para completar un expediente de entrega técnica definitiva al Estado, se identifican los siguientes documentos pendientes de elaboración:

1. **Manual del Usuario Final por Perfiles:**
   - Guía ilustrada para el Docente (creación de tareas, calificaciones y asistencia).
   - Guía ilustrada para la Familia / Acudiente (seguimiento escolar y firmas de circulares).
   - Guía ilustrada para el Estudiante (entregas y clases virtuales).
2. **Manual de Administración de la Infraestructura en Producción:**
   - Procedimientos de escalado de clúster Kubernetes y políticas de autoscaling.
   - Guía de instalación paso a paso de BigBlueButton y Coturn para administradores de Linux del Ministerio.
3. **Plan de Capacitación y Transferencia de Conocimiento:**
   - Cronograma de talleres técnicos dirigidos al equipo de sistemas del MEN/MinTIC.
4. **Matriz de Niveles de Servicio (SLA) y Soporte Técnico:**
   - Definición de tiempos de respuesta y criticidad de incidentes durante la operación nacional.
5. **Acta de Cesión / Donación de Derechos Patrimoniales:**
   - Documento jurídico suscrito ante notario o autoridad competente formalizando la transferencia técnica del software al Estado colombiano.
