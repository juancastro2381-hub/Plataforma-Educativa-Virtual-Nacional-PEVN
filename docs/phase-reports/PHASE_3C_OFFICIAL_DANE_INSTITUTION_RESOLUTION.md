# ARQUITECTURA Y RESOLUCIÓN OFICIAL DE IDENTIDAD INSTITUCIONAL DANE / MEN
**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fase:** Fase 3C — Endurecimiento Pre-Pruebas Funcionales  
**Fecha:** 26 de Agosto de 2026  
**Estado:** `CERTIFIED & FROZEN`  
**Autor:** Antigravity AI Engineering Team  

---

## 1. Objetivos y Alcance

El presente documento establece formalmente la arquitectura de resolución de identidad institucional oficial para la **Plataforma Educativa Virtual Nacional (PEVN)** basada en fuentes autorizadas del Estado Colombiano (DANE y Ministerio de Educación Nacional).

### Principio Fundamental
Cuando el Administrador Nacional ingresa un código DANE de 12 dígitos en el panel de aprovisionamiento, PEvN resuelve el establecimiento educativo y **puebla automáticamente toda la información oficial autorizada**, protegiendo al usuario de reingresar manualmente datos ya disponibles en fuentes gubernamentales.

---

## 2. Fuentes Oficiales Autorizadas

| Entidad Propietaria | Sistema de Origen | Identificador de Conjunto de Datos / API | Frecuencia de Actualización | Tipo de Entidad | Alcance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ministerio de Educación Nacional (MEN)** | Directorio Único de Establecimientos (DUE) / SIMAT | `datos.gov.co/c36d-tcj8` | Mensual / Semestral | Establecimientos & Sedes Educativas | Nacional Oficial y No Oficial |
| **Departamento Administrativo Nacional de Estadística (DANE)** | Directorio Estadístico de Educación (DIREDU) / C600 | `dane.gov.co / C600 Educación Formal` | Anual | Establecimientos & Sedes | Censo Nacional de Educación Formal |
| **DANE / IGAC** | División Político-Administrativa de Colombia (DIVIPOLA) | `geoportal.dane.gov.co` | Continua | Departamentos & Municipios | Taxonomía Territorial Oficial |

### Exclusiones Estrictas
- No se utilizan motores de búsqueda comerciales (Google Search, Bing).
- No se utilizan directorios comerciales, wikis ni raspado web (web scraping).
- No se exponen consultas directas desde el navegador a APIs gubernamentales externas, garantizando resiliencia y soberanía del dato en PEvN.

---

## 3. Modelo de Dominio: Establecimiento vs. Sede Educativa

En la taxonomía educativa colombiana:

```
[ Establecimiento Educativo / Institución ] (Código DANE 12 dígitos)
       |
       +---> [ Sede Principal ] (Código DANE Sede - is_main = True)
       |
       +---> [ Sede Adscrita 1 ] (Código DANE Sede - is_main = False)
       +---> [ Sede Adscrita 2 ] (Código DANE Sede - is_main = False)
       +---> [ ... ]
```

- **Institución Educativa (Establecimiento):** Constituye el límite primario de aislamiento multitenant (*Tenant Boundary*) y personería académica.
- **Sedes Educativas (Campuses):** Subdivisiones operativas donde se imparten las clases físicas o se administran los grupos académicos.

---

## 4. Arquitectura de Ingestión y Catálogo Local PEvN

```
+-------------------------------------------------------------+
|        Fuentes Gubernamentales Oficiales (MEN DUE / DANE)   |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|    Servicio de Ingestión y Sincronización Oficial PEvN      |
|    (Normalización, validación DANE 12 dígitos, sedes)       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|              Catálogo Oficial Local PEvN                    |
|    - official_institution_catalog (Establecimientos)        |
|    - official_campus_catalog (Sedes asociadas)              |
|    - Trazabilidad de Procedencia (Provenance Metadata)      |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|              Servicio de Dominio (InstitutionService)       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|          REST API: GET /api/v1/institutions/resolve-dane    |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|     Frontend PEvN: Modal de Aprovisionamiento Nacional      |
|     (Campos oficiales de solo lectura 🔒 + Sedes oficiales) |
+-------------------------------------------------------------+
```

---

## 5. Contrato de Datos y Procedencia (Data Provenance)

### 5.1 Campos Oficiales Autorizados (Solo Lectura 🔒)
- **Código DANE:** 12 dígitos numéricos en formato `STRING` (preservando ceros a la izquierda).
- **Nombre Oficial:** Razón social registrada en el DUE.
- **Departamento:** Código DANE (2 dígitos) y Nombre.
- **Municipio:** Código DANE (5 dígitos) y Nombre.
- **Secretaría de Educación (ETC):** Entidad Territorial Certificada competente.
- **Sector:** `OFICIAL` (Público) / `NO OFICIAL` (Privado).
- **Zona:** `URBANA` / `RURAL`.
- **Calendario:** `A` / `B` / `CONTINUO`.
- **Carácter / Modalidad:** `ACADÉMICO` / `TÉCNICO` / `NORMALISTA`.
- **Dirección Oficial:** Dirección legal registrada.
- **Sedes Asociadas:** Lista completa de Sedes Educativas con designación `Principal` o `Adscrita`.

### 5.2 Metadatos de Procedencia (*Provenance*)
Cada registro oficial en PEvN conserva:
- `source_system`: Sistema de origen oficial (`MINISTERIO DE EDUCACION NACIONAL (DUE) / DANE`).
- `source_dataset`: Identificador del dataset (`datos.gov.co/c36d-tcj8`).
- `source_record_id`: Identificador original del registro gubernamental.
- `source_updated_at`: Fecha de emisión/publicación por el Estado.
- `synced_at`: Marca de tiempo exacta en que PEvN sincronizó el catálogo.

### 5.3 Distinción entre Datos Oficiales y Datos Operativos PEvN
- **Datos Oficiales:** Bloqueados con distintivo 🔒.
- **Datos Operativos PEvN:** Correo institucional de notificaciones y teléfono de contacto operativo. Si el correo no viene en el DUE, se solicita explícitamente al Administrador Nacional con la indicación: *"Dato operativo requerido por PEvN"*.

---

## 6. Endpoints REST API

### 6.1 `GET /api/v1/institutions/resolve-dane/{dane_code}`
- **Autenticación:** Requerida (Bearer JWT).
- **Autorización:** Restringida a Administradores Nacionales (`NATIONAL_ADMIN`, `SUPERADMIN` o alcance nacional).
- **Validaciones:**
  - Código DANE de exactamente 12 dígitos numéricos (`422 INVALID_DANE_CODE` si es inválido).
  - Consulta en el catálogo oficial local (`404 OFFICIAL_DANE_RECORD_NOT_FOUND` si no existe).
- **Pista de Auditoría:** Registra evento `official_dane.resolved` con actor y código consultado.

### 6.2 `POST /api/v1/institutions`
- Cuando se aprovisiona utilizando un código DANE del catálogo oficial, se crean automáticamente la institución y todas sus sedes registradas (Principal y Adscritas).
- Registra el evento de auditoría `institution.provisioned_from_catalog` con metadatos de procedencia (`source_system`, `source_dataset`, `catalog_id`).

---

## 7. Experiencia de Usuario (Frontend UX)

El modal de aprovisionamiento en `/admin/institutions` implementa una máquina de estados limpia:

1. **Entrada de Código DANE:** Validación reactiva de 12 dígitos numéricos.
2. **Estado de Consulta:** Indicador *"Consultando catálogo oficial del Ministerio de Educación Nacional / DANE..."*.
3. **Estado Encontrado:**
   - Despliegue de cuadrícula con datos oficiales protegidos 🔒.
   - Lista desglosada de Sedes Educativas (`[Principal]` y `[Adscrita]`).
   - Sección de datos operativos PEvN (correo y teléfono).
   - Pie de trazabilidad con dataset y fecha de sincronización.
4. **Estado No Encontrado:**
   - Mensaje claro: *"No encontramos un registro oficial asociado a este Código DANE en el catálogo nacional."*
   - Opción de excepción administrativa manual debidamente advertida y auditada.

---

## 8. Certificación de Pruebas y Regresión

| Suite de Pruebas | Archivo | Total Pruebas | Estado |
| :--- | :--- | :---: | :---: |
| **Línea Base Fase 3B** | `tests/test_academic_api.py`, `test_academic_e2e_integration.py`, `test_domain_services.py` | 109 | **100% PASS** |
| **Aprovisionamiento Fase 3C (Paso 2)** | `tests/test_institution_provisioning.py` | 14 | **100% PASS** |
| **Resolución DANE Oficial (Paso 3)** | `tests/test_official_dane_resolution.py` | 8 | **100% PASS** |
| **Total Regresión Backend** | — | **131** | **100% PASS (0 errores)** |
| **Compilación Frontend** | `tsc -b && vite build` | — | **100% PASS (0 errores)** |
