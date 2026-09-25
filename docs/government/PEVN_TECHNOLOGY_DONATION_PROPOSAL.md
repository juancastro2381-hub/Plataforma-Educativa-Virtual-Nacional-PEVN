# PEVN — PROPUESTA TÉCNICA DE DONACIÓN Y TRANSFERENCIA TECNOLÓGICA
## EXPEDIENTE DE CESIÓN DE BIENES DE SOFTWARE PARA EL ESTADO COLOMBIANO (FASE 0.1)

**Entidades Destinatarias:** Ministerio de Educación Nacional (MEN), Ministerio de Tecnologías de la Información y las Comunicaciones (MinTIC), Secretarías de Educación Certificadas y Entidades Públicas del Sector Social  
**Marco de Gobernanza:** AI Software Factory v1.2 — Open Technology Transfer Protocol  
**Régimen de Licenciamiento:** Apache License, Version 2.0 (Código Abierto / Sin Regalías)  
**Fecha:** 21 de Septiembre de 2026  
**Naturaleza del Documento:** **PROPUESTA TÉCNICA INSTITUCIONAL (NO CONSTITUYE CONTRATO NI INSTRUMENTO LEGAL VINCULANTE)**  

---

## 1. Advertencia Legal y Carácter de la Propuesta

> [!IMPORTANT]
> **DECLARACIÓN DE NATURALEZA DEL DOCUMENTO:**
> El presente documento constituye una **propuesta técnica y descriptiva de transferencia de activos de software** elaborada con fines informativos y de sustentación técnica. 
> **ESTE DOCUMENTO NO ES UN CONTRATO DE DONACIÓN, NI UN CONVENIO INTERADMINISTRATIVO, NI UN ACTO ADMINISTRATIVO VINCULANTE.**
> Cualquier transferencia formal de derechos de propiedad intelectual, derechos patrimoniales o aceptación de bienes intangibles por parte del Estado colombiano requerirá la suscripción de los instrumentos contractuales y notariales pertinentes, con estricto apego a la Ley 80 de 1993, la Ley 1150 de 2007, el Código Civil Colombiano y las normas presupuestales vigentes.

---

## 2. Origen, Filosofía y Motivación de PEVN

La **Plataforma Educativa Virtual Nacional (PEVN)** fue concebida y desarrollada como una iniciativa de ingeniería de software de alto impacto para abordar una de las mayores deudas sociales de Colombia: la brecha digital y la dispersión administrativa en las instituciones educativas oficiales.

Frente a esquemas tradicionales basados en licenciamientos cerrados o herramientas desarticuladas, PEVN fue concebida bajo un enfoque de **Soberanía Tecnológica Digital**:
- Un sistema diseñado de raíz para el marco regulatorio colombiano (Ley 115/1994, Decreto 1290/2009, Ley 1620/2013).
- Un activo digital concebido con la vocación de ponerse a disposición del patrimonio público del país.
- Un bien público digital concebido para fortalecer la autonomía institucional del magisterio y cualificar la experiencia escolar en las comunidades educativas oficiales.

---

## 3. ¿Qué se plantea en esta Propuesta Técnica?

La propuesta plantea las bases técnicas para una eventual **cesión y transferencia de los activos de software y código fuente de PEVN**, bajo condiciones sin cobro de regalías (*royalty-free*), sujetas a revisión jurídica, aprobación institucional, instrumentos legales aplicables al sector público y revisión formal de propiedad intelectual:

### 3.1 Activos de Software y Código Fuente
1. **Servicio Backend Completo:**
   - 100% del código fuente en Python 3.12 con FastAPI.
   - 28 controladores REST con contratos de API OpenAPI v3.
   - 18 servicios de dominio que resuelven la lógica académica, evaluativa y convivencial.
   - 24 archivos de modelos de base de datos relacionales en SQLAlchemy 2.0.
   - 23 scripts de migración lineales y determinísticos en Alembic.
   - Adaptador para clases virtuales BigBlueButton (`BBBAdapter`) con criptografía SHA-1/256.
2. **Servicio Frontend SPA Completo:**
   - 100% del código fuente en React 18, TypeScript 5.7 y Vite.
   - 8 portales web soberanos e independientes (SuperAdmin, MEN, Territorio, Rector, Coordinador, Docente, Estudiante y Acudiente).
   - Componentes reactivos accesibles estilizados con Tailwind CSS.
   - Configuración PWA con Service Worker para almacenamiento en caché de activos estáticos.
3. **Scripts de Infraestructura y Orquestación:**
   - Manifiestos Docker y Docker Compose para despliegue en contenedores.
   - Scripts de configuración de usuarios de base de datos de mínimos privilegios (`pevn_app`).
   - Sondas de salud y verificación de entorno (`check_env.sh`).

### 3.2 Suites de Pruebas Automatizadas y Aseguramiento de Calidad
- **432 pruebas automatizadas en backend** (`pytest`) con 100% de éxito y cobertura en todos los dominios de negocio.
- **119 pruebas en frontend aprobadas de 123** (`vitest`, 96.7% PASS) con pruebas de integración y renderizado.
- Configuraciones estrictas de tipado (`mypy`, `tsc`) y análisis de seguridad estático (`ruff`, `bandit`).

### 3.3 Repositorio Documental Completo
- Documentación técnica, actas de fase, ADRs y contratos funcionales formalizados en el repositorio.
- Dossiers de preparación gubernamental, catálogo de preguntas técnicas y runbooks de demostración en vivo.
- Especificaciones de arquitectura de producción y manuales de operaciones.

---

## 4. Posición de Licenciamiento y Régimen Jurídico

- **Licencia de Código Abierto:** PEVN se encuentra licenciada bajo la **Apache License, Version 2.0**.
- **Prerrogativas para el Estado Colombiano:**
  - Plena libertad para utilizar, inspeccionar, auditar, modificar, adaptar y compilar el software.
  - Plena libertad para desplegar la plataforma en servidores gubernamentales o de terceros sin límite de usuarios ni colegios.
  - Plena libertad para redistribuir el software a Secretarías de Educación o instituciones públicas.
  - Concesión expresa de licencias de patentes de los colaboradores conforme a la sección 3 de la licencia Apache 2.0.
  - **Cero Regalías ($0 COP):** La plataforma no exige pagos recurrentes por licencias de uso ni cánones por alumno matriculado.
- **Dependencias de Terceros:** Todas las librerías utilizadas (FastAPI, React, PostgreSQL, Redis, BigBlueButton) cuentan con licencias permisivas de código abierto (MIT, BSD, Apache, LGPL) sin dependencias virales restrictivas (verificado en `THIRD_PARTY_LICENSES.md`).

---

## 5. Posibles Entidades Receptoras en Colombia

La donación técnica puede estructurarse hacia una o varias de las siguientes entidades del orden nacional o territorial:
1. **Ministerio de Educación Nacional (MEN):** Como autoridad rectora de la política educativa, para operar PEVN como plataforma estándar del sector oficial o como plataforma de respaldo nacional.
2. **Ministerio de Tecnologías de la Información y las Comunicaciones (MinTIC):** Como rector de la política de Gobierno Digital y proyectos de conectividad escolar.
3. **Radio Televisión Nacional de Colombia (RTVC / Sistema de Medios Públicos):** Como entidad operadora de medios y contenidos educativos convergentes del Estado.
4. **Secretarías de Educación Departamentales o Distritales (ETC):** Para adopción directa como sistema de gestión escolar territorial en sus colegios adscritos.

---

## 6. Proceso Propuesto de Evaluación y Transferencia

Para garantizar una transición técnica rigurosa y transparente, se propone una hoja de ruta en cuatro etapas:

```
[ ETAPA 1: SUSTENTACIÓN TÉCNICA & DEMOSTRACIÓN EN VIVO ]
- Ejecución del Runbook formalizado ante comités técnicos del MEN y MinTIC.
- Inspección directa del código fuente, arquitectura y suites de prueba.
                       │
                       ▼
[ ETAPA 2: FASE PILOTO CONTROLADA (5 A 10 COLEGIOS) ]
- Despliegue de un entorno de prueba en infraestructura provista por la entidad pública.
- Operación durante 1 período académico escolar con docentes, estudiantes y familias en un entorno escolar piloto.
- Recolección de telemetría de rendimiento y retroalimentación pedagógica.
                       │
                       ▼
[ ETAPA 3: MESAS JURÍDICAS, DE CIBERSEGURIDAD Y HABEAS DATA ]
- Revisión de la política de protección de datos de menores (Ley 1581/2012).
- Auditoría técnica de ciberseguridad y escaneo estático por parte de ColCERT/MinTIC.
- Redacción de la minuta de cesión de derechos patrimoniales o convenio de adopción.
                       │
                       ▼
[ ETAPA 4: SUSCRIPCIÓN FORMAL Y TRANSFERENCIA DE CONOCIMIENTO ]
- Firma del instrumento jurídico que determine la entidad competente (convenio o acta de donación al Estado).
- Talleres de transferencia técnica al equipo de ingeniería y operaciones de la entidad pública.
```

---

## 7. Responsabilidades e Infraestructura que la Entidad Pública Debe Proveer

La donación corresponde exclusivamente a los **activos de software, código fuente, arquitectura y documentación**. La entidad pública receptora deberá contemplar dentro de su planeación presupuestal y operativa:

1. **Infraestructura de Servidores y Cómputo:**
   - Servidores para la API y el Frontend (máquinas virtuales en nube pública o centro de datos gubernamental).
   - Servidor físico dedicado para BigBlueButton (16 vCPU, 32 GB RAM) y Coturn TURN en TCP 443 para clases virtuales.
   - Instancias gestionadas de PostgreSQL 16 y Redis 7.
   - Almacenamiento de objetos en nube (S3 o compatible) para adjuntos de tareas y grabaciones.
2. **Nombres de Dominio y Certificados:**
   - Asignación de subdominios oficiales `.gov.co` y emisión de certificados SSL/TLS.
3. **Operaciones y Mesa de Ayuda:**
   - Personal técnico para administración de sistemas, monitoreo continuo y atención a usuarios finales (docentes y familias).
4. **Conectividad Escolar:**
   - La plataforma optimiza el consumo de datos y soporta PWA, pero requiere acceso a internet en las sedes o en los hogares para sincronizar datos.

---

## 8. Asuntos Legales y Regulatorios Sujetos a Formalización

Antes de la puesta en servicio masivo con datos en producción, la entidad pública receptora deberá formalizar jurídicamente:
- **La Titularidad y Responsabilidad del Tratamiento de Datos:** Declarar formalmente si el MEN o las Secretarías de Educación ostentan la calidad de "Responsables del Tratamiento" de los datos personales de los menores conforme a la Ley 1581 de 2012.
- **Autorización Parental Informada:** Formalizar el modelo de consentimiento de los acudientes para el tratamiento de datos de los estudiantes.
- **Tablas de Retención Documental (TRD):** Plazos oficiales de custodia y archivo histórico digital de los boletines de calificaciones y actas de grado en armonía con el Archivo General de la Nación.
- **Protocolo de Interoperabilidad con SIMAT:** Formalizar los canales seguros de intercambio de datos de matrícula con la Oficina de Tecnología del MEN.

---

## 9. Conclusión de la Propuesta

La presente propuesta técnica pone a disposición del Estado colombiano un desarrollo tecnológico maduro y rigurosamente documentado, diseñado bajo un enfoque de soberanía tecnológica con profundo respeto por la institucionalidad educativa del país. Sujeta a la revisión jurídica y a los acuerdos institucionales que determine la entidad competente, esta propuesta no constituye un contrato vinculante previo.

El equipo creador reitera su plena disposición para acompañar a los comités técnicos gubernamentales en la sustentación, inspección y evaluación de esta plataforma al servicio de la educación pública de Colombia.
