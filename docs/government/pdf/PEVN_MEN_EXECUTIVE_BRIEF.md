# Plataforma Educativa Virtual Nacional (PEVN)
## Resumen Ejecutivo de Alto Nivel para la Reunión con el MEN
### Documento Breve de Orientación para Directivos de Tecnología y Sistemas de Información

---

**Iniciativa:** Plataforma Educativa Virtual Nacional (PEVN)  
**Destinatario:** Oficina de Tecnología y Sistemas de Información — Ministerio de Educación Nacional (MEN)  
**Liderazgo Técnico:** Juan Carlos Castro Narváez  
**Fecha:** Octubre 2026 | **Versión:** 1.0-FINAL-MEN  
**Clasificación:** Confidencial Técnico / Uso Institucional  

---

## 1. El Reto y la Oportunidad de País

Las instituciones educativas oficiales de Colombia enfrentan dos problemas estructurales en su gestión cotidiana:
1. **Altos Costos de Licenciamiento Privativo:** Las Secretarías de Educación y colegios destinan recursos recurrentes a contratos de software comercial privativo que cobran por estudiante, limitando la sostenibilidad presupuestal y generando dependencia tecnológica.
2. **Brecha Digital en Sedes Rurales Dispersas:** Las plataformas comerciales pesadas, saturadas de librerías externas y analítica publicitaria, colapsan en sedes educativas con enlaces de bajo ancho de banda (2 Mbps o menos), obligando a docentes rurales a mantener registros en papel o planillas desarticuladas.

**La Oportunidad:** Consolidar a PEVN como un **Bien Público Digital** del Estado colombiano: una plataforma académica moderna, soberana, abierta (licencia Apache 2.0 / AGPLv3) y optimizada para operar en condiciones de baja conectividad sin costo recurrente de licenciamiento por alumno.

---

## 2. Qué es PEVN y Qué Capacidades Están Operativas Hoy

PEVN es un sistema integral de información y gestión académica construido bajo un paradigma desacoplado:
- **Frontend SPA Liviano:** Desarrollado en React 18, TypeScript y Vite, sin fuentes externas ni scripts comerciales; 100% autónomo y preparado para operar localmente.
- **Backend Asíncrono de Alto Rendimiento:** Desarrollado en FastAPI (Python 3.12/3.14) con ORM asíncrono SQLAlchemy 2.0 (`asyncpg`).
- **Persistencia y Sesiones:** PostgreSQL 15 con aislamiento multi-tenant lógico forzado por discriminador institucional (`institution_id`), y Redis 7 para revocación instantánea de sesiones.
- **Gobernanza Territorial DANE:** 33 departamentos, 1,122 municipios (DIVIPOLA) y catálogo de 18,031 colegios y 51,521 sedes precargadas en el modelo relacional.

### Estado Técnico Comprobado (Demostrable en Vivo)
- **Aprovisionamiento Directivo:** Invitación criptográfica con tokens de un solo uso (vigencia de 72 horas) para activación autónoma de Rectores.
- **Gestión Curricular y Académica:** Parametrización de sedes, años lectivos, periodos con ponderación porcentual, grados, grupos y asignación docente.
- **Planilla Evaluativa y Asistencia:** Registro ágil de notas (escala 1.0 a 5.0) y faltas diarias con persistencia transaccional y pista forense inmutable (`AuditLog`).
- **Portales de Autoservicio:** Vistas directas para Estudiantes y Acudientes protegidas contra vulnerabilidades de referencia directa insegura (Anti-IDOR).
- **Aulas Virtuales (BigBlueButton):** Orquestación completa de cliente API para creación de salas seguras y cálculo de checksums SHA1 (requiere conexión a clúster BBB externo para video en vivo).

---

## 3. Postura de Ciberseguridad y Cumplimiento Normativo

- **Control de Acceso Basado en Roles (RBAC de 11 Roles):** Jerarquía estricta que previene el escalamiento vertical de privilegios (`superadmin` a `student/guardian`). Incluye la excepción canónica aprobada de coordinador, mediante la cual el Rector puede habilitar o inhabilitar la delegación de creación de docentes y matrícula en coordinadores de sede.
- **Mitigación Anti-IDOR y Cross-Tenant:** Toda consulta de base de datos exige obligatoriamente el `institution_id` de la sesión activa. Ningún usuario puede visualizar registros de otra sede modificando parámetros en la URL.
- **Protección de Datos Personales (Ley 1581 de 2012):** Tratamiento de datos de menores bajo estándar reforzado; cero analítica comercial, cero rastreadores y contraseñas hasheadas con Argon2id / bcrypt.
- **Sanitización de Traza y Secretos:** Cero contraseñas expuestas en mensajes de error o logs del sistema (máscaras `***` verificadas en pruebas).

---

## 4. Evidencia de Calidad y Pruebas Automatizadas (Auditoría R8)

El estado de la solución está respaldado por evidencia auditable en el repositorio:
- **Censo Dinámico de Pruebas:** **747 pruebas recolectadas** en 72 archivos de prueba.
  - **83 pruebas de integración con PostgreSQL 15 real** en 6 archivos clave.
  - **664 pruebas unitarias y en memoria** en 66 archivos.
- **Batería Ejecutada en Ciclo Acotado:** **57 pruebas ejecutadas con 100% PASS** (13 de hardening de teardown y ciclo de vida de conexiones, 12 de analizador de censo, 17 de aprovisionamiento institucional y 15 de asignación de directivos docentes).
- **Compilación Limpia:** 0 errores en verificación de tipos de TypeScript (`tsc --noEmit`) y 41 comprobaciones automatizadas de documentación aprobadas al 100%.

---

## 5. Hoja de Ruta Propuesta: Colaboración en 4 Fases con Decision Gates

Se propone al MEN un esquema voluntario y estructurado de evaluación institucional:

```
[FASE 1: Mesa Técnica] ──> [COMPUERTA 1: Viabilidad TI]
                                   │
                                   v
[FASE 2: Ciberseguridad y Carga] ──> [COMPUERTA 2: Aval de Seguridad]
                                             │
                                             v
[FASE 3: Piloto en 2-5 Colegios] ──> [COMPUERTA 3: Dictamen de Adopción]
                                             │
                                             v
[FASE 4: Transferencia como Bien Público Digital]
```

- **Fase 1 (Mesa Técnica y Discovery — 2 a 4 semanas):** Inspección conjunta del código fuente, modelos de datos y definición de contratos de interoperabilidad con SIMAT.
- **Fase 2 (Seguridad, Interoperabilidad y Carga — 4 a 6 semanas):** Pruebas de penetración (pentesting), afinamiento de contenedores y simulación de carga masiva.
- **Fase 3 (Piloto Experimental Controlado — 10 a 12 semanas):** Prueba en 2 a 5 colegios oficiales seleccionados por el MEN (combinando sedes urbanas y rurales), operando en paralelo con los sistemas ordinarios para no alterar el historial legal de notas.
- **Fase 4 (Transferencia Institucional):** Cesión formal de activos de software y código fuente al Ministerio bajo licenciamiento abierto.

---

## 6. Preguntas Concretas para la Mesa Técnica del MEN

1. ¿Cuál es el procedimiento institucional y la ventana de oportunidad para instalar una mesa técnica de evaluación de arquitectura en las próximas semanas?
2. ¿Qué lineamientos o requerimientos específicos de infraestructura de nube (o centro de datos oficial) exige el MEN para el despliegue de pruebas?
3. ¿Qué dependencia técnica definirá las especificaciones de interfaz segura (API Gateway o intercambio en lote) para la articulación con SIMAT y DUE?
4. ¿Existe viabilidad institucional para autorizar el diseño de un piloto experimental en una muestra controlada de colegios oficiales bajo rectoría del MEN?

---

*Documento preparado como síntesis ejecutiva para la sesión presencial de trabajo con la Oficina de Tecnología y Sistemas de Información del MEN.*
