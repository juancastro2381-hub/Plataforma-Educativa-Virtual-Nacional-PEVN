# PEVN — INFORME DE PREPARACIÓN DE INFRAESTRUCTURA Y DESPLIEGUE
## REQUERIMIENTOS POR NIVELES: DESARROLLO, PILOTO Y PRODUCCIÓN NACIONAL (FASE 0)

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Marco de Auditoría:** AI Software Factory v1.2 — Infrastructure & Operational Sizing  
**Fecha:** 21 de Septiembre de 2026  
**Carácter:** Read-Only Infrastructure Dossier  

---

## 1. Declaración de Estado de Infraestructura

> [!WARNING]
> **NO EXISTE INFRAESTRUCTURA DE PRODUCCIÓN DESPLEGADA ACTUALMENTE.**
> El proyecto PEVN se encuentra operando y certificado en su **Entorno de Desarrollo Local y Pruebas Integradas** mediante contenedores Docker. Los requerimientos descritos a continuación constituyen el dimensionamiento técnico y la hoja de ruta física indispensable para avanzar hacia una fase de **Piloto Institucional** y posteriormente a **Producción Nacional**.

---

## 2. Matriz de Requerimientos por Nivel de Despliegue

A continuación se contrastan las necesidades técnicas para los tres horizontes de despliegue:
- **Nivel A: Entorno de Desarrollo (Estado Actual).**
- **Nivel B: Entorno de Piloto Controlado (5 a 10 Colegios, ~5.000 a 10.000 usuarios).**
- **Nivel C: Entorno de Producción Nacional (Escala Territorial MEN, cientos de miles de usuarios).**

| Componente | Nivel A: Desarrollo (Actual) | Nivel B: Piloto Controlado (Requerido) | Nivel C: Producción Nacional (Objetivo) |
| :--- | :--- | :--- | :--- |
| **Servidores de Aplicación (Backend)** | 1 contenedor Docker local (Uvicorn / FastAPI, 2 workers) en host de desarrollo. | 2 a 3 instancias balanceadas (Nginx Ingress + Uvicorn, 4 vCPU, 8 GB RAM c/u). | Clúster Kubernetes (EKS / GKE / On-Premise) con Horizontal Pod Autoscaler (HPA), 10 a 50 réplicas. |
| **Servidores Web (Frontend SPA)** | Servidor de desarrollo Vite en puerto 3000 con Hot Module Replacement (HMR). | 2 réplicas Nginx sirviendo bundle estático comprimido (Gzip/Brotli). | Distribución global en CDN gubernamental (Cloudflare Gov o CloudFront) con almacenamiento en bucket S3. |
| **Base de Datos (PostgreSQL)** | 1 contenedor PostgreSQL 16 local con almacenamiento en volumen Docker (`pevn_pgdata`). | Instancia gestionada (Cloud SQL / RDS) PostgreSQL 16 (4 vCPU, 16 GB RAM, SSD) con réplica de lectura. | Clúster PostgreSQL 16 HA (Patroni / Cloud RDS Multi-AZ), 1 nodo maestro + 2 réplicas de lectura + PgBouncer. |
| **Caché y Mensajería (Redis)** | 1 contenedor Redis 7 local en puerto 6379 sin autenticación estricta. | Instancia gestionada Redis 7 (MemoryDB / ElastiCache, 4 GB RAM) con persistencia RDB. | Clúster Redis 7 HA con Sentinel / Cluster Mode habilitado para alta concurrencia y revocación de sesiones. |
| **Almacenamiento de Archivos (Storage)** | Sistema de archivos local (`backend/data/storage/`). | Bucket de objetos S3 / MinIO dedicado con cifrado en reposo (SSE-S3). | Clúster de almacenamiento de objetos distribuido multi-región (S3 / Ceph) con ciclo de vida automatizado y CDN. |
| **Aulas Virtuales (BigBlueButton)** | Simulador en memoria (`MockMeetingProvider`). Cero servidores físicos. | 1 servidor físico Ubuntu 22.04 (16 vCPU, 32 GB RAM, 1 Gbps) enlazado con `BBBAdapter`. | Clúster de múltiples nodos BigBlueButton coordinados por el balanceador de carga de código abierto **Scalelite**. |
| **Relay WebRTC (Coturn / TURN)** | Ninguno (tráfico local). | 1 servidor Coturn dedicado escuchando en TCP puerto 443 con certificado TLS para saltar firewalls escolares. | Par de servidores Coturn de alta disponibilidad con IP pública estática y balanceo DNS para tolerancia a fallos. |
| **Almacenamiento de Grabaciones** | Simulador en memoria (metadatos en base de datos local). | Volumen de almacenamiento local en el servidor BBB (500 GB SSD) con script de sincronización. | Montaje de almacenamiento de red NFS/S3 para publicación masiva de grabaciones con compresión MP4/WebM. |
| **DNS y Nombres de Dominio** | `localhost` / `127.0.0.1` en archivo `hosts`. | Subdominios oficiales de prueba: `piloto.pevn.gov.co`, `bbb-piloto.pevn.gov.co`. | Zona DNS delegada oficial `.gov.co` con DNSSEC habilitado y mitigación Anycast contra DDoS. |
| **Seguridad de Red y WAF** | Cortafuegos local de Windows/Linux. | Reverse Proxy Nginx con módulo ModSecurity y listas de control de acceso (ACL). | Web Application Firewall (WAF) corporativo gubernamental con mitigación de DDoS L3/L4/L7 y reglas OWASP. |
| **Certificados SSL / TLS** | Certificados autofirmados o HTTP plano en red interna. | Certificados Let's Encrypt automatizados mediante Certbot con renovación automática vía cron. | Certificados TLS 1.3 emitidos por Autoridad Certificadora reconocida con soporte de comodín (*wildcard*) y EV. |
| **Gestión de Secretos** | Archivo plano `.env` excluido en `.gitignore`. | Variables de entorno inyectadas mediante Docker Secrets o archivos protegidos con permisos `chmod 600`. | Sistema centralizado de secretos: HashiCorp Vault o AWS Secrets Manager con rotación criptográfica periódica. |
| **Estrategia de Respaldos (Backups)** | Dumps manuales mediante `pg_dump` bajo demanda. | Respaldo diario automatizado de base de datos (`pg_dump` comprimido) transferido a almacenamiento secundario. | Respaldos continuos en tiempo real con WAL archiving (pgBackRest o WAL-G). **RPO < 15 minutos, RTO < 2 horas.** |
| **Recuperación de Desastres (DR)** | Reconstrucción manual desde el repositorio Git y scripts SQL. | Procedimiento de restauración documentado con tiempo estimado de recuperación inferior a 8 horas. | Plan de Recuperación de Desastres (DRP) automatizado en región secundaria con ejercicios de conmutación semestrales. |
| **Observabilidad y Métricas** | Logs en consola de terminal (stdout) y sondas `/health` y `/ready`. | Pila centralizada Grafana + Loki + Prometheus con métricas básicas de servidor (CPU, memoria, latencia HTTP). | Ecosistema completo APM (OpenTelemetry / Datadog / Grafana Enterprise) con alertas a guardia 24/7 (PagerDuty/Slack). |

---

## 3. Plan de Despliegue de la Fase Piloto (5 a 10 Colegios)

Para la ejecución de una prueba piloto institucional con autoridades gubernamentales, se recomienda la siguiente arquitectura mínima provisionable en un período de 2 a 3 semanas:

```
                            INTERNET
                               │
                        [ DNS .gov.co ]
                               │ (HTTPS :443)
                  [ Servidor Proxy Inverso Nginx ]
                  (Certificado Let's Encrypt / WAF)
                               │
        ┌──────────────────────┴──────────────────────┐
        ▼                                             ▼
[ Instancia Web/API ]                        [ Servidor BigBlueButton ]
- Frontend React SPA (Nginx)                 - Ubuntu 22.04 LTS (16 vCPU, 32 GB)
- Backend FastAPI (Python 3.12)              - bbb-install-2.7 con SSL
- Almacenamiento Local Particionado          - Coturn TURN en TCP 443
        │
        ▼
[ Instancia de Base de Datos ]
- PostgreSQL 16 (pevn_db)
- Redis 7 (pevn_cache)
- Respaldo diario automatizado (Cron)
```

### Costos Estimados de Infraestructura para Fase Piloto (Mensual)
- Servidor de Aplicación + Base de Datos (Cloud VPS 8 vCPU, 32 GB RAM, 200 GB SSD): ~$120 – $180 USD / mes.
- Servidor Dedicado BigBlueButton + Coturn (Bare-metal o VPS 16 vCPU, 32 GB RAM, 500 GB NVMe, 1 Gbps): ~$150 – $250 USD / mes.
- Almacenamiento y Respaldos secundarios (S3 / B2 ~1 TB): ~$15 – $25 USD / mes.
- Dominio y DNS gubernamental: Administrado por la entidad pública sin costo adicional.
- **Costo Total Estimado para Piloto:** Entre **$285 y $455 USD mensuales**.

---

## 4. Conclusiones y Prerrequisitos de Despliegue

1. **El software se encuentra preparado para ser empaquetado y subido a cualquier nube o infraestructura física del Estado** (AWS, Azure, Google Cloud, Huawei Cloud o Datacenter propio de MinTIC / RTVC).
2. **Ningún paso de comisionamiento físico puede ejecutarse sin la asignación presupuestal y técnica previa por parte de la entidad oficial interesada.**
3. **El repositorio incluye los manuales y especificaciones operativas completas** en la carpeta `docs/` (`PHASE_8_PRODUCTION_OPERATIONS_RUNBOOK.md` y `PHASE_10_INFRASTRUCTURE_HANDOFF.md`) para que el equipo de infraestructura gubernamental despliegue los servicios sin requerir reingeniería.
