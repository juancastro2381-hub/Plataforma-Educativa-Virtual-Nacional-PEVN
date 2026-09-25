# PEVN — REGISTRO FORMAL DE LIMITACIONES ACTUALES
## CATÁLOGO DE LIMITACIONES TÉCNICAS, OPERATIVAS, DE INFRAESTRUCTURA Y JURÍDICAS (FASE 0)

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Marco Metodológico:** AI Software Factory v1.2 — Transparent Limitations Governance  
**Fecha:** 21 de Septiembre de 2026  
**Carácter:** Read-Only Audit Evidence  

---

## 1. Declaración de Transparencia

> [!IMPORTANT]
> **POLÍTICA DE TRANSPARENCIA RADICAL:**
> En cumplimiento estricto de las directrices de **AI Software Factory v1.2**, ninguna limitación, brecha o asunto pendiente debe ocultarse o minimizarse. El valor de este informe ante las autoridades del Estado radica en su honestidad técnica absoluta. Identificar los límites actuales permite trazar una hoja de ruta certera hacia la fase de comisionamiento en producción.

---

## 2. Registro Exhaustivo de Limitaciones

| ID | Descripción de la Limitación | Impacto Operativo | Estado Actual | Nivel de Riesgo | Evidencia en el Repositorio | Acción Recomendada | Responsable / Owner | ¿Requiere Código? | ¿Requiere Infra? | ¿Requiere Decisión Jurídica/Inst.? |
| :-: | :--- | :--- | :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: |
| **LIM-01** | **Clúster físico BigBlueButton no comisionado.** | No se pueden impartir clases virtuales en vivo en este momento. | Software listo (100% probado); servidor físico ausente. | **ALTO** | `backend/app/core/meeting/mock_provider.py` | Desplegar servidor Ubuntu 22.04 LTS y ejecutar `bbb-install`. | Infraestructura / DevOps | No | **SÍ** | No |
| **LIM-02** | **Servidor Coturn (STUN/TURN) en TCP 443 no desplegado.** | Clases virtuales fallarán en colegios rurales con firewalls restrictivos o CGNAT. | Especificación lista en `docs/PHASE_8_...`; servidor ausente. | **ALTO** | `docs/PHASE_8_NETWORK_COTURN_VALIDATION.md` | Desplegar Coturn en TCP 443 con certificado TLS. | Redes / Infraestructura | No | **SÍ** | No |
| **LIM-03** | **Almacenamiento de tareas en disco local (`backend/data/storage/`).** | Impide el escalado horizontal multi-instancia en la nube sin almacenamiento compartido. | Almacenamiento local particionado por colegio operativo. | **MEDIO** | `backend/app/core/storage/service.py` | Implementar adaptador `S3StorageService` (AWS S3 / MinIO). | Backend / Cloud | **SÍ** | **SÍ** | No |
| **LIM-04** | **Motor de generación masiva de Boletines en PDF no implementado.** | Los boletines se visualizan reactivamente en pantalla y JSON, pero no se pueden imprimir en PDF masivo. | Visualizador web y matrices SIEE operativas. | **MEDIO** | `pages/academic/DirectiveEvaluationManagementView.tsx` | Implementar renderizador de PDFs (WeasyPrint) con código QR. | Backend Developer | **SÍ** | No | No |
| **LIM-05** | **Notificaciones en tiempo real y Push no implementadas.** | Circulares y avisos se consultan bajo demanda; el usuario no recibe alerta instantánea en el celular. | Almacenamiento en base de datos operativo. | **BAJO** | `backend/app/models/communication.py` | Integrar WebSockets o servicio WebPush / Firebase FCM. | Fullstack Developer | **SÍ** | No | No |
| **LIM-06** | **Pasarela de correo transaccional (SMTP) no conectada en producción.** | Los correos de reseteo de contraseña e invitaciones se imprimen en consola/log en desarrollo. | Flujo lógico y tokens de uso único 100% probados. | **MEDIO** | `backend/app/services/auth_service.py` | Configurar servidor SMTP institucional o servicio Gov.co. | DevOps / SysAdmin | No | **SÍ** | No |
| **LIM-07** | **Ausencia de Single Sign-On (SSO) con Gov.co / Carpeta Ciudadana.** | Los usuarios deben autenticarse con credenciales locales de PEVN en lugar de su identidad digital ciudadana. | Autenticación local Argon2id operativa. | **BAJO** | `backend/app/core/security/` | Diseñar integración OpenID Connect / SAML con Gov.co. | Arquitecto de Software | **SÍ** | No | **SÍ** |
| **LIM-08** | **Interoperabilidad SIMAT basada en archivos estructurados (no API en vivo).** | La sincronización de matrícula requiere importación periódica en lugar de enlace en tiempo real. | Modelos compatibles con SIMAT probados. | **MEDIO** | `backend/app/models/enrollment.py` | Suscribir convenio interinstitucional con MEN para enlace de API. | Dirección / Jurídica | **SÍ** | No | **SÍ** |
| **LIM-09** | **Consola de emisión web de circulares y convivencia asimétrica.** | Estudiantes y acudientes consumen y firman en web; los directivos/docentes emiten mediante API en desarrollo. | Endpoints backend completos (17 endpoints). | **MEDIO** | `AUDITORIA_FASE15_COMUNICACIONES_NOTICIAS_CONVIVENCIA.md` | Construir vistas web de redacción de circulares en portal docente. | Frontend Developer | **SÍ** | No | No |
| **LIM-10** | **Ausencia de pruebas de carga masiva empíricas (*Load Testing*).** | Se desconoce la concurrencia máxima empírica que soporta una instancia bajo estrés nacional. | Arquitectura teóricamente escalable (stateless). | **ALTO** | `docs/reports/PEVN_SCALABILITY_READINESS.md` | Ejecutar batería de pruebas de estrés con k6/Locust en Staging. | QA / Performance Eng | No | **SÍ** | No |
| **LIM-11** | **PgBouncer no desplegado frente a PostgreSQL.** | Posible saturación de conexiones de base de datos bajo miles de usuarios concurrentes. | Pool de SQLAlchemy local (`asyncpg`) operativo. | **MEDIO** | `docs/DATABASE.md` | Configurar PgBouncer en la plantilla de despliegue Docker/K8s. | DBA / Infraestructura | No | **SÍ** | No |
| **LIM-12** | **Respaldos automatizados continuos (WAL-G) no configurados en prod.** | Respaldo manual en desarrollo; falta automatización de punto de recuperación RPO < 15 min. | Scripts de dump manual disponibles. | **ALTO** | `docs/OPERATIONS.md` | Configurar replicación continua de WALs hacia almacenamiento S3. | DBA / SysAdmin | No | **SÍ** | No |
| **LIM-13** | **Dominio gubernamental `.gov.co` y certificados SSL de producción ausentes.** | El sistema opera en dominios locales de desarrollo (`localhost`, `127.0.0.1`). | Soporte TLS configurado en código y middleware. | **MEDIO** | `backend/app/middleware/security_headers.py` | Solicitar registro de subdominios oficiales ante MinTIC. | Líder de Proyecto | No | **SÍ** | **SÍ** |
| **LIM-14** | **Auditoría formal de penetración (*Ethical Hacking*) no ejecutada.** | Aunque el código cumple controles OWASP, se requiere certificación externa de seguridad. | Verificaciones automáticas de linter Bandit aprobadas. | **ALTO** | `docs/SECURITY_THREAT_MODEL.md` | Contratar auditoría de penetración de caja negra previa a producción. | CISO / Seguridad | No | No | **SÍ** |
| **LIM-15** | **Política de Tratamiento de Datos de Menores no formalizada jurídicamente.** | Falta la redacción formal de los términos y condiciones conforme a directrices del MEN. | Minimización técnica y aislamiento multi-tenant listos. | **ALTO** | `docs/reports/PEVN_DATA_PROTECTION_READINESS.md` | Redactar autorización parental con equipo jurídico ministerial. | Dirección Jurídica | No | No | **SÍ** |
| **LIM-16** | **Convenio formal de donación de software al Estado no elaborado.** | El código tiene licencia Apache-2.0, pero falta el documento legal de cesión de derechos patrimoniales. | Licencia Apache-2.0 en el repositorio. | **MEDIO** | `LICENSE`, `THIRD_PARTY_LICENSES.md` | Elaborar minuta de donación de software con el Ministerio. | Jurídica / Donante | No | No | **SÍ** |
| **LIM-17** | **Desalineación de mocks heredados en 4 pruebas de frontend (vitest).** | La suite frontend reporta 119/123 tests aprobados (96.7%) debido a cambios en firmas de B3-H13. | Cero fallos en producto real; error exclusivo de mocks. | **BAJO** | `frontend/src/test/StudentPortal.test.tsx` | Actualizar los fixtures de mock en los 2 archivos de prueba afectados. | Frontend QA | **SÍ** | No | No |
| **LIM-18** | **Sin soporte de sincronización offline para escuelas rurales sin internet.** | La plataforma exige conectividad web activa para todas las operaciones. | PWA almacena estáticos pero no sincroniza datos offline. | **MEDIO** | `frontend/vite.config.ts` | Diseñar estrategia offline-first con IndexedDB y sincronización en fondo. | Arquitecto de Software | **SÍ** | No | No |
| **LIM-19** | **Módulos financieros y de inventario fuera de alcance.** | La plataforma no gestiona fondos de servicios docentes ni compras del colegio. | Alcance acotado exclusivamente a lo académico/convivencial. | **BAJO** | `docs/ARCHITECTURE.md` | Mantener integración con sistemas contables oficiales del Estado. | Producto / Negocio | No | No | **SÍ** |
| **LIM-20** | **`BBB_SHARED_SECRET` vacío en configuración predeterminada.** | Backend rechaza peticiones si se cambia a modo `"bbb"` sin configurar la clave secreta. | Validación fail-fast en `BBBAdapter` opera correctamente. | **MEDIO** | `backend/app/core/meeting/bbb_adapter.py` | Inyectar secreto generado por el servidor BBB físico al desplegarlo. | DevOps / Deployer | No | **SÍ** | No |

---

## 3. Clasificación de Acciones por Naturaleza

- **Requieren Implementación de Código de Software:** 6 limitaciones (LIM-03, LIM-04, LIM-05, LIM-07, LIM-08, LIM-09, LIM-17, LIM-18).
- **Requieren Infraestructura Física Externa o Configuración:** 9 limitaciones (LIM-01, LIM-02, LIM-03, LIM-06, LIM-10, LIM-11, LIM-12, LIM-13, LIM-20).
- **Requieren Decisión Jurídica o Institucional:** 6 limitaciones (LIM-07, LIM-08, LIM-13, LIM-14, LIM-15, LIM-16, LIM-19).
