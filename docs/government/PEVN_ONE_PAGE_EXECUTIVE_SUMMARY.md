# RESUMEN EJECUTIVO: PLATAFORMA EDUCATIVA VIRTUAL NACIONAL (PEVN)
## Síntesis Técnica e Institucional para el Sector Oficial Colombiano

**Fecha:** 13 de octubre de 2026 | **Licencia Propuesta:** Apache 2.0 (Código Abierto / $0 COP en Regalías) | **Estado:** Evaluación Institucional

---

### 1. ¿Qué es PEVN?
La **Plataforma Educativa Virtual Nacional (PEVN)** es un sistema de información web modular y multi-inquilino, diseñado bajo un enfoque de soberanía tecnológica para el sector oficial colombiano. Unifica la jerarquía territorial (Nacional, Departamental, Municipal, Institucional, Sede), catálogo DANE (18,031 colegios y 51,521 sedes), matrícula, asignaciones docentes, evaluación formativa (**Decreto 1290/2009**), observador de convivencia (**Ley 1620/2013**), circulares con acuse electrónico y soporte para aulas virtuales.

### 2. ¿Qué problema aborda?
Mitiga la dispersión tecnológica en las instituciones públicas, donde coexisten planillas manuales, plataformas comerciales extranjeras y canales informales no auditables. PEVN reduce la sobrecarga administrativa docente, fortalece el acompañamiento familiar con identidad desacoplada y asegura la custodia institucional de los datos educativos bajo estándares soberanos.

### 3. ¿Qué está implementado?
- **11 Roles del Sistema:** Portales para Rectoría, Coordinación, Docentes, Estudiantes, Acudientes, Administradores Territoriales (Municipal, Departamental, Nacional y SuperAdmin).
- **Gestión Escolar y Matrícula:** Sedes, grados, grupos, cargas docentes y estructuras compatibles con SIMAT con control de cupos máximos por aula.
- **Evaluación SIEE (D. 1290):** Políticas autónomas, 4 escalas nacionales, cálculo ponderado, ajustes justificados, nivelaciones con tope y sellado inmutable.
- **Convivencia (L. 1620) y Circulares:** Observador escolar Tipos I, II y III con debido proceso y circulares con acuse de recibo electrónico (timestamp UTC e IP).
- **Aulas Virtuales:** Capa de software BigBlueButton (`BBBAdapter`), firma SHA-1/256 y telemetría de conexión mediante mock verificado.

### 4. ¿Qué está técnicamente verificado?
- **Pruebas Automatizadas:** 704 pruebas de backend colectadas (suites unitarias y de API ejecutadas con 100% de éxito) y 196 pruebas de frontend ejecutadas (100% en 29 suites; 242 pruebas dinámicas verificadas).
- **Base de Datos y Calidad:** 32 migraciones lineales Alembic en PostgreSQL 16 y tipado estricto al 100% en TypeScript y Python.
- **Controles de Seguridad:** Hashing Argon2id (64 MB), tokens JWT volátiles exclusivamente en memoria de React (mitigación frente a XSS), cookies HttpOnly con rotación de familia y aislamiento multi-tenant con respuestas `Blind 404` (Anti-IDOR). No se identificaron vulnerabilidades críticas en el alcance auditado.

### 5. ¿Qué permanece pendiente para producción?
- **Infraestructura Física:** Servidores dedicados BigBlueButton y servidor de relay Coturn (STUN/TURN en TCP 443) para redes escolares.
- **Servicios de Nube:** Almacenamiento de objetos (S3/MinIO), pasarela transaccional de correo SMTP y worker asíncrono para PDFs masivos en lote.
- **Validación y Acuerdos:** Pruebas de estrés de carga para concurrencia nacional y convenios interadministrativos de interoperabilidad en tiempo real con SIMAT y MinTIC (Carpeta Ciudadana). No reemplaza los sistemas oficiales del MEN ni DANE.

### 6. ¿Qué se propone al Estado colombiano?
Una **propuesta técnica de donación y transferencia tecnológica** bajo licencia de código abierto **Apache 2.0**. La propuesta contempla poner a disposición del Estado el código fuente íntegro, esquemas de bases de datos relacionales, 32 migraciones y documentación sin costos de licenciamiento ($0 COP en software), sujeta a revisión jurídica y a los instrumentos que determine la entidad competente.

### 7. ¿Cuál es el próximo paso?
Realizar una demostración técnica en vivo ante los comités evaluadores del MEN, MinTIC y Secretarías de Educación, acordando las bases para una **Fase Piloto en 5 a 10 colegios oficiales** durante un período académico escolar.
