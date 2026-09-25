# PEVN — INFORME DE PREPARACIÓN DE ESCALABILIDAD
## ANÁLISIS DE CAPACIDAD ARQUITECTÓNICA, CUELLOS DE BOTELLA Y ESCALA NACIONAL (FASE 0)

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Marco de Auditoría:** AI Software Factory v1.2 — Scalability & Performance Analysis  
**Fecha:** 21 de Septiembre de 2026  
**Carácter:** Read-Only Architectural Assessment  

---

## 1. Distinción Fundamental de Madurez

> [!IMPORTANT]
> **DECLARACIÓN DE RIGOR TÉCNICO:**
> 1. **Capacidad Arquitectónica (*Architectural Capability*):** La arquitectura de PEVN ha sido concebida y codificada bajo patrones modernos que **soportan teóricamente el escalamiento horizontal sin rediseño del código fuente**: API stateless (sin estado en servidor), frontend SPA desacoplado distribuible en CDN, particionamiento multi-tenant por `institution_id` e índices optimizados en base de datos.
> 2. **Capacidad Empíricamente Validada (*Empirically Validated Capacity*):** El sistema **AÚN NO HA SIDO SOMETIDO A PRUEBAS DE CARGA MASIVA EN PRODUCCIÓN (STRESS / LOAD TESTING)**. No existen métricas empíricas de cuántos miles de usuarios concurrentes puede soportar una instancia determinada bajo estrés real.
> 3. **Prohibición de Inventar Cifras:** Este informe no promete cifras de concurrencia ficticias; en su lugar, analiza los cuellos de botella reales y describe los mecanismos técnicos indispensables para escalar a nivel nacional.

---

## 2. Mecanismos de Escalamiento Arquitectónico

### 2.1 Backend Stateless (Sin Estado en Servidor)
- El backend FastAPI no almacena sesiones en memoria local del proceso Uvicorn.
- La identidad se transmite mediante tokens JWT criptográficos validados mediante clave pública/secreta simétrica.
- El estado de los tokens de refresco y listas de revocación reside en PostgreSQL y/o Redis.
- **Oportunidad de Escala:** Se pueden desplegar múltiples réplicas del contenedor backend detrás de un balanceador de carga (Nginx, HAProxy o AWS ALB) utilizando una política de distribución *Round-Robin* o *Least Connections* sin necesidad de sesiones pegajosas (*sticky sessions*).

### 2.2 Frontend SPA en Red de Distribución de Contenido (CDN)
- La interfaz de usuario es una Single Page Application (SPA) construida en Vite que compila a un conjunto de archivos estáticos (`HTML`, `JS`, `CSS`, imágenes SVG/WebP).
- **Oportunidad de Escala:** Puede alojarse en almacenamiento de bajo costo (S3 / Google Cloud Storage) y distribuirse globalmente mediante CDN (Cloudflare, Fastly o CloudFront). Esto reduce a cero la carga de CPU de los servidores de aplicación para servir la interfaz web, absorbiendo millones de visitas concurrentes sin degradación.

### 2.3 Aislamiento Multi-Inquilino (Multi-Tenancy por Institución)
- El aislamiento de datos se fundamenta en la columna `institution_id`.
- Todas las operaciones del día a día (calificaciones, asistencias, tareas, circulares) operan dentro de los límites de un único colegio.
- **Oportunidad de Escala:** Esta partición lógica natural permite que, en una fase de adopción nacional masiva, la base de datos pueda ser particionada (*sharding*) por regiones geográficas, departamentos o rangos de instituciones educativas sin requerir cambios estructurales en el modelo relacional.

---

## 3. Identificación de Cuellos de Botella Actuales

A continuación se señalan los puntos críticos de contención identificados durante la auditoría forense:

| Componente | Cuello de Botella Identificado | Impacto en Alta Carga | Solución Técnica Planificada |
| :--- | :--- | :--- | :--- |
| **Conexiones a PostgreSQL** | Cada petición API que consulta la base de datos toma una conexión del pool SQLAlchemy (`asyncpg`). Sin un agregador intermedio, el límite máximo de conexiones de PostgreSQL (~200–500) se satura rápidamente con múltiples réplicas backend. | Caída de peticiones con error `Too many connections` o latencias elevadas. | Interponer **PgBouncer** en modo *transaction pooling* frente a PostgreSQL para soportar miles de conexiones backend con pocas conexiones reales al motor. |
| **Almacenamiento Local de Archivos** | Las entregas de tareas y evidencias se guardan en el disco local (`backend/data/storage/`). Si se despliegan 5 réplicas backend en distintos servidores, un archivo subido en el servidor A no será visible por el servidor B. | Error 404 al intentar descargar evidencias desde réplicas diferentes. | Migrar a **S3StorageService** (MinIO o AWS S3) con almacenamiento centralizado de objetos y URLs prefirmadas. |
| **Cálculo de Boletines y Promedios** | El cálculo de notas definitivas, puestos en el grupo y boletines consolidados ejecuta consultas analíticas sobre `activity_grades` y `period_subject_grades`. En épocas de cierre de período (todos los colegios cerrando simultáneamente), la carga de lectura en la base de datos es muy alta. | Aumento en los tiempos de respuesta de la base de datos durante semanas de evaluación. | Enrutar consultas de consulta y reportes hacia **réplicas de lectura de PostgreSQL (Read Replicas)** mediante directivas del ORM. |
| **Renderizado Masivo de PDFs** | Si se implementa la generación de boletines PDF directamente dentro del ciclo de petición-respuesta HTTP de FastAPI, la CPU del backend se saturará rápidamente (un PDF complejo toma de 1 a 3 segundos de cómputo intensivo). | Bloqueo de peticiones HTTP concurrentes y degradación de la experiencia. | Encolar la generación de boletines en **tareas asíncronas de fondo (Celery / ARQ con Redis)** y notificar al usuario cuando el archivo esté listo para descarga. |
| **Videoclases BigBlueButton** | Un solo servidor BBB físico puede albergar aproximadamente 100 a 150 usuarios con cámara y micrófono encendidos. Una demanda nacional de miles de estudiantes colapsaría una sola máquina. | Latencia extrema en WebRTC, audio entrecortado y caídas de sala. | Desplegar el clúster balanceado de código abierto **Scalelite**, distribuyendo las salas entre múltiples servidores BBB dedicados. |

---

## 4. Consideraciones para la Expansión a Escala Nacional

### 4.1 Estrategia de Caché Multinivel (Redis)
Para alcanzar el rendimiento exigido por el sector público, PEVN debe incorporar caching en los siguientes puntos:
1. **Caché de Permisos y Roles:** Almacenar en Redis la lista de permisos de los usuarios activos durante su sesión para evitar consultas repetitivas a la base de datos en cada endpoint protegido.
2. **Caché del Catálogo DANE y Estructura Territorial:** Los datos de departamentos, municipios, colegios y sedes son prácticamente estáticos; deben servirse desde memoria volátil con un Time-To-Live (TTL) de 24 horas.
3. **Caché de Políticas SIEE:** La configuración evaluativa institucional de un colegio rara vez cambia a mitad de año; cachear `SieePolicy` en memoria acelerará significativamente la planilla docente.

### 4.2 Requisitos para la Ejecución de Pruebas de Carga Masiva (Load Testing)
Antes de autorizar el uso de PEVN en un departamento o en todo el país, es **estrictamente obligatorio** ejecutar un plan de pruebas de estrés empírico con herramientas como **k6**, **Locust** o **JMeter**:

```
ESCENARIO 1: INICIO DE JORNADA (Pico de Autenticación)
- Simulación: 10.000 usuarios iniciando sesión simultáneamente en una ventana de 10 minutos.
- Métrica objetivo: Tiempo de respuesta P95 < 500 ms, tasa de error < 0.1%.

ESCENARIO 2: CIERRE DE PERÍODO (Pico Evaluativo)
- Simulación: 2.000 docentes asentando notas y 20.000 familias consultando boletines simultáneamente.
- Métrica objetivo: Cero bloqueos (deadlocks) en PostgreSQL, tiempo de respuesta P95 < 1.0s.

ESCENARIO 3: ENTREGA DE TAREAS (Pico de Almacenamiento)
- Simulación: 5.000 estudiantes subiendo archivos PDF de 5 MB de forma concurrente.
- Métrica objetivo: Cero corrupción de archivos, uso de ancho de banda controlado mediante almacenamiento S3.
```

---

## 5. Resumen de Madurez de Escalabilidad

| Dimensión de Escala | Capacidad Arquitectónica | Validación Empírica | Próximo Paso Requerido |
| :--- | :---: | :---: | :--- |
| **Escalado Horizontal de Backend** | `SOPORTADO` | `PENDIENTE` | Desplegar múltiples réplicas tras Nginx Ingress. |
| **Distribución de Frontend** | `SOPORTADO` | `PENDIENTE` | Desplegar estáticos en bucket con CDN Cloudflare. |
| **Escalado de Base de Datos** | `SOPORTADO` | `PENDIENTE` | Incorporar PgBouncer y réplica de lectura. |
| **Almacenamiento Concurrente** | `REQUIERE TRABAJO` | `PENDIENTE` | Migrar de disco local a S3 / MinIO. |
| **Escalado de Videoclases** | `SOPORTADO (DISEÑO)` | `PENDIENTE` | Desplegar balanceador Scalelite sobre nodos BBB. |
| **Procesamiento Asíncrono** | `REQUIERE TRABAJO` | `PENDIENTE` | Configurar Celery/Redis para tareas pesadas y PDF. |
