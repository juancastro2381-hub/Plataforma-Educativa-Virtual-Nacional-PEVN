# PEVN — INFORME DE PREPARACIÓN DE AULAS VIRTUALES (BIGBLUEBUTTON)
## SEPARACIÓN ENTRE IMPLEMENTACIÓN DE SOFTWARE Y COMISIONAMIENTO DE INFRAESTRUCTURA FÍSICA (FASE 0)

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Módulo:** Aulas Virtuales Sincrónicas & Integración BigBlueButton (BBB)  
**Marco de Auditoría:** AI Software Factory v1.2 — Physical vs. Logical Separation  
**Fecha:** 21 de Septiembre de 2026  
**Carácter:** Read-Only Forensic Assessment  

---

## 1. Declaración Autoritativa de Estado

> [!IMPORTANT]
> **DICTAMEN FORENSE CRÍTICO:**
> 1. **A Nivel de Software:** La capa de software para clases virtuales en PEVN está **100% IMPLEMENTADA, ARQUITECTADA Y VERIFICADA**. Cuenta con adaptadores completos, firma criptográfica de peticiones, telemetría de conexión, reproductor de grabaciones, control RBAC y aislamiento multi-inquilino.
> 2. **A Nivel de Infraestructura:** **NO SE HA DESPLEGADO, COMISIONADO NI CONECTADO NINGÚN SERVIDOR FÍSICO BIGBLUEBUTTON NI SERVIDOR DE RELAY COTURN (TURN/STUN).**
> 3. **Estado del Entorno:** La plataforma opera actualmente configurada con el proveedor simulado en memoria (`MockMeetingProvider`).
> 4. **Conclusión Gubernamental:** Es mandatorio clarificar a los evaluadores del Estado que el sistema cuenta con el software terminado para conectarse a BigBlueButton, pero que **el servicio de videoclases reales en vivo requiere el comisionamiento de servidores físicos dedicados**.

---

## 2. Arquitectura del Subsistema de Clases Virtuales

El diseño arquitectónico sigue el principio de inversión de dependencias mediante el protocolo abstracto `IMeetingProvider`, permitiendo conmutar entre proveedores sin alterar la lógica de negocio escolar:

```
                  ┌─────────────────────────────────────┐
                  │    VirtualClassroomService (Core)   │
                  └──────────────────┬──────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │    MeetingProviderFactory       │
                    └───────┬─────────────────┬───────┘
                            │                 │
              (MEETING_PROVIDER_TYPE="bbb")   │ (MEETING_PROVIDER_TYPE="mock")
                            │                 │
            ┌───────────────▼──┐       ┌──────▼──────────────┐
            │    BBBAdapter    │       │  MockMeetingProvider │
            └───────┬──────────┘       └─────────────────────┘
                    │
                    ▼ (HTTPS / XML API / SHA Checksums)
    ┌─────────────────────────────────────────┐
    │    Servidor Físico BigBlueButton 2.7+   │
    │  [ REQUIERE COMISIONAMIENTO FÍSICO ]    │
    └─────────────────────────────────────────┘
```

### 2.1 Componentes de Software Implementados

| Componente | Archivo / Ubicación | Responsabilidad Técnica | Estado de Software |
| :--- | :--- | :--- | :---: |
| **`IMeetingProvider`** | `backend/app/core/meeting/interfaces.py` | Protocolo abstracto que estandariza los métodos: `create_meeting()`, `generate_join_url()`, `end_meeting()`, `is_meeting_running()`, `get_meeting_info()`, `get_recordings()`, `delete_recording()`. | `VERIFIED` |
| **`BBBAdapter`** | `backend/app/core/meeting/bbb_adapter.py` | Implementación de bajo nivel de la API REST/XML de BigBlueButton. Genera checksums criptográficos obligatorios (SHA-1 o SHA-256), concatena llamadas HTTP asíncronas con `httpx` y deserializa respuestas XML a objetos tipados. | `VERIFIED` |
| **`MockMeetingProvider`** | `backend/app/core/meeting/mock_provider.py` | Simulador en memoria determinístico que almacena reuniones, emite URLs simuladas de ingreso y genera grabaciones sintéticas para desarrollo y pruebas. | `VERIFIED` |
| **`MeetingProviderFactory`** | `backend/app/core/meeting/factory.py` | Fábrica singleton que instancia el proveedor adecuado según la configuración de entorno (`MEETING_PROVIDER_TYPE`). | `VERIFIED` |
| **`VirtualClassroomService`**| `backend/app/services/virtual_classroom_service.py` | Orquestación misional: Creación de sala con ID único institucional, validación de pertenencia al grupo escolar, resolución de rol (`MODERATOR` vs `VIEWER`) y finalización. | `VERIFIED` |
| **`AttendanceService`** | `backend/app/services/attendance_service.py` | Telemetría de asistencia: Registro de ingresos (`joined_at`), salidas (`left_at`), duración efectiva de conexión en segundos y participantes únicos. | `VERIFIED` |
| **`RecordingService`** | `backend/app/services/recording_service.py` | Sincronización asíncrona de grabaciones procesadas por el servidor, visibilidad institucional controlada por el docente y reproducción. | `VERIFIED` |
| **Frontend Web Views** | `pages/virtual-classrooms/VirtualClassroomsView.tsx` | Pantalla directiva y docente: Filtros (En Vivo, Programadas, Finalizadas), creación de salas, botón "Iniciar", "Unirse", modal de asistencias y visor de grabaciones. | `VERIFIED` |
| **Frontend Portales** | `pages/student/StudentVirtualClassesView.tsx`, `guardian/...` | Pestaña de clases en vivo y grabaciones para el alumno matriculado y su acudiente con Anti-IDOR estricto. | `VERIFIED` |

---

## 3. Auditoría del Ciclo de Vida de una Clase Virtual

1. **Creación y Programación:**
   - Se crea el registro en la tabla `virtual_classrooms` con estado `SCHEDULED`.
   - Generación de identificador único de reunión: `pevn-{institution_id[:8]}-{uuid4[:12]}` (garantiza que no existan colisiones entre instituciones en un servidor compartido).
   - Generación aleatoria de contraseñas de sesión de 16 bytes urlsafe independientes: `moderator_pw` y `attendee_pw`.
2. **Inicio (Launch):**
   - El docente pulsa "Iniciar Clase" $\rightarrow$ El backend transiciona a `RUNNING` y registra `actual_start_time` (UTC).
   - El backend invoca `create_meeting` en el proveedor BBB para inicializar la sala en memoria del clúster de medios.
3. **Ingreso Docente (Moderator):**
   - El servicio resuelve el rol institucional: asigna `MODERATOR`.
   - Se genera una URL firmada con el checksum criptográfico y se abre la interfaz de BigBlueButton en pestaña externa.
   - Se crea un registro en `meeting_attendances`.
4. **Ingreso Estudiante (Viewer / SIMAT Gating):**
   - El estudiante pulsa "Entrar a Clase".
   - **Validación de Matrícula (SIMAT Gating):** El backend comprueba en base de datos que el estudiante cuente con una matrícula activa (`Enrollment.status == 'ACTIVE'`) en el grupo específico asignado a esa clase virtual.
   - Si no está matriculado: Se rechaza inmediatamente con `HTTP 403 Forbidden` (`UnauthorizedMeetingAccessError`).
   - Si está matriculado: Asigna rol `VIEWER`, genera la URL firmada con la contraseña de asistente y registra el ingreso en telemetría.
5. **Telemetría y Control de Asistencia:**
   - La entrada a la sala estampa `joined_at` con hora del servidor UTC.
   - Al desconectarse o pulsar salir, el endpoint `/api/v1/virtual-classrooms/{id}/leave` registra `left_at` y calcula automáticamente `duration_seconds`.
6. **Finalización (End):**
   - Solo el docente anfitrión o el rector/coordinador pueden invocar `/api/v1/virtual-classrooms/{id}/end`.
   - Se invoca `end_meeting` en el proveedor externo (expulsando a los participantes de la sala BBB).
   - El estado pasa a `ENDED` y se cierran automáticamente todas las sesiones de asistencia abiertas calculando su duración.
7. **Grabaciones y Reproducción:**
   - Tras terminar la clase, BigBlueButton procesa las pistas de audio, video y diapositivas de forma asíncrona.
   - El directivo/docente ejecuta la sincronización manual o programada (`/recordings/classroom/{id}/sync`).
   - Por política de privacidad, el docente puede conmutar `is_published = False` para ocultar la grabación. Los estudiantes y acudientes solo pueden visualizar y reproducir grabaciones con `is_published == True`.

---

## 4. Estado Actual de Configuración y Credenciales

La inspección de la configuración en `backend/app/core/config.py` y `backend/.env` revela la siguiente realidad técnica:

| Variable de Entorno | Valor Actual por Defecto | Estado en el Repositorio | Diagnóstico Forense |
| :--- | :--- | :--- | :--- |
| `MEETING_PROVIDER_TYPE` | `"mock"` | No declarada en `.env` (usa fallback `"mock"`) | **ACTIVO EN MODO SIMULADOR** |
| `BBB_API_URL` | `"http://localhost:8090/bigbluebutton/api"` | No declarada en `.env` | **URL DE DESARROLLO FICTICIA** |
| `BBB_SHARED_SECRET` | `""` | No declarada en `.env` | **SECRETO VACÍO / NO CONFIGURADO** |
| `BBB_SIGNING_ALGORITHM`| `"sha1"` | Predeterminada | Conforme al estándar nativo BBB |
| `BBB_TIMEOUT_SECONDS` | `10.0` | Predeterminada | Adecuada para llamadas síncronas |

> [!CAUTION]
> Si en este momento un operador cambia `MEETING_PROVIDER_TYPE="bbb"` en el archivo `.env`, la aplicación lanzará un error crítico `MeetingProviderConfigError("BBB_SHARED_SECRET no está configurado.")`, impidiendo la creación o ingreso a cualquier aula virtual. Esto demuestra fehacientemente que la conexión a un servidor real aún no está enlazada.

---

## 5. Requerimientos de Infraestructura Física para la Salida en Vivo

Para transformar el subsistema de clases virtuales de "Software Preparado" a "Operación en Vivo", la entidad gubernamental (MEN / MinTIC) debe proveer y configurar los siguientes elementos:

### 5.1 Servidor Dedicado BigBlueButton
- **Sistema Operativo:** Ubuntu 22.04 LTS x64 (instalación limpia en servidor físico o máquina virtual bare-metal con virtualización KVM).
- **Especificaciones Mínimas por Servidor (para 100 usuarios concurrentes):**
  - CPU: 16 vCPU (procesador moderno a 3.0+ GHz).
  - Memoria RAM: 32 GB.
  - Almacenamiento: 500 GB en disco SSD/NVMe de alta velocidad.
  - Ancho de Banda: Conexión simétrica dedicada de mínimo 1 Gbps con transferencia ilimitada.
- **Herramienta de Despliegue:** Script oficial `bbb-install-2.7.sh` con certificados Let's Encrypt automatizados.

### 5.2 Servidor de Relay Coturn (STUN/TURN en TCP 443)
- **Problema en Escuelas Públicas de Colombia:** La inmensa mayoría de instituciones educativas en zonas rurales y municipios no certificados operan tras redes con **CGNAT (Carrier-Grade NAT)** y cortafuegos restrictivos que bloquean los puertos UDP estándar de WebRTC (`16384–32768`), provocando fallos de conexión (Errores 1007 y 1020 en BigBlueButton).
- **Solución Obligatoria:** Desplegar un servidor Coturn dedicado escuchando en el **puerto TCP 443 con certificado TLS**. De este modo, los flujos de audio y video viajan encapsulados por el mismo puerto que el tráfico web HTTPS ordinario, atravesando cualquier firewall institucional sin bloqueos.
- **Evidencia Técnica de Diseño:** El diseño y puertos de Coturn se encuentran formalmente especificados en el documento del repositorio `docs/PHASE_8_NETWORK_COTURN_VALIDATION.md`.

### 5.3 Nombres de Dominio y Certificados SSL/TLS
- Registro de registros DNS tipo A oficiales:
  - `bbb.pevn.gov.co` $\rightarrow$ IP pública del servidor BigBlueButton.
  - `turn.pevn.gov.co` $\rightarrow$ IP pública del servidor Coturn.
- Certificados SSL/TLS válidos emitidos por una Autoridad de Certificación reconocida.

### 5.4 Balanceo y Escala Masiva (Scalelite)
- Para atender una demanda nacional que supere los 50 salones concurrentes simultáneos, se debe interponer el balanceador de carga de código abierto **Scalelite** frente a un clúster de múltiples nodos BigBlueButton trabajadores (*workers*).

---

## 6. Registro de Limitaciones del Módulo de Clases Virtuales

| ID | Descripción de la Limitación | Impacto | Mitigación Planificada |
| :--- | :--- | :--- | :--- |
| **LIM-BBB-01** | Servidor BigBlueButton real no desplegado. | No se pueden emitir clases sincrónicas en vivo actualmente. | Ejecutar runbook de instalación física en `docs/PHASE_10_INFRASTRUCTURE_HANDOFF.md`. |
| **LIM-BBB-02** | Servidor Coturn TURN no desplegado. | Clases fallarán en redes escolares con firewall UDP bloqueado. | Desplegar Coturn en TCP 443 con certificado TLS. |
| **LIM-BBB-03** | `BBB_SHARED_SECRET` vacío en entorno. | Backend rechaza peticiones en modo `"bbb"`. | Inyectar secreto generado por `bbb-conf --secret` en variables de producción. |
| **LIM-BBB-04** | Sincronización de grabaciones bajo demanda. | Las grabaciones requieren petición manual de sincronización. | Implementar Webhook de recepción de eventos de BigBlueButton en backend. |
