# RESUMEN EJECUTIVO: PLATAFORMA EDUCATIVA VIRTUAL NACIONAL (PEVN)
## Síntesis Técnica e Institucional para el Sector Oficial Colombiano

**Fecha:** 21 de septiembre de 2026 | **Licencia Propuesta:** Apache 2.0 (Código Abierto / $0 COP en Regalías) | **Estado:** Documentación preparada para evaluación institucional

---

### 1. ¿Qué es PEVN?
La **Plataforma Educativa Virtual Nacional (PEVN)** es un sistema de información web modular y multi-inquilino, diseñado bajo un enfoque de soberanía tecnológica para el sector oficial colombiano. Unifica la gestión territorial de sedes (DANE/DUE), matrícula, asignaciones docentes, evaluación formativa (**Decreto 1290/2009**), observador de convivencia (**Ley 1620/2013**), comunicaciones oficiales con firma digital y soporte para aulas virtuales sincrónicas.

### 2. ¿Qué problema aborda?
Mitiga la fragmentación tecnológica en las instituciones educativas oficiales, donde coexisten planillas manuales, herramientas de propósito general y canales informales no auditables. PEVN reduce la sobrecarga operativa de los docentes, fortalece el acompañamiento formativo de las familias y asegura la custodia institucional de los datos educativos bajo estándares soberanos.

### 3. ¿Qué está implementado?
- **Portales Especializados:** Interfaces independientes para Rectoría, Coordinación, Docentes, Estudiantes y Acudientes.
- **Gestión Escolar y Matrícula:** Sedes, grados, grupos y asignaciones académicas. Estructuras compatibles con el modelo de matrícula oficial y control de cupos máximos por aula.
- **Evaluación SIEE (D. 1290):** Políticas autónomas por colegio, cálculo ponderado, ajustes justificados, nivelaciones con tope y sellado inmutable.
- **Convivencia (L. 1620) y Circulares:** Observador escolar Tipos I, II y III con debido proceso y circulares con acuse electrónico (timestamp e IP).
- **Aulas Virtuales:** Adaptador de software BigBlueButton (`BBBAdapter`), firma de URLs y telemetría de conexión mediante mock verificado.

### 4. ¿Qué está técnicamente verificado?
- **Pruebas Automatizadas:** 432 pruebas en backend aprobadas (100% de éxito) y 119 pruebas en frontend aprobadas (96.7%).
- **Calidad de Código:** Tipado estricto al 100% sin errores en `mypy` y `TypeScript`.
- **Controles de Seguridad:** Hashing Argon2id (64 MB), tokens JWT volátiles exclusivamente en memoria de React (mitigación frente a robo de tokens por XSS), cookies HttpOnly rotativas y aislamiento multi-tenant con respuestas `Blind 404` (Anti-IDOR). No se identificaron vulnerabilidades críticas en el alcance auditado.

### 5. ¿Qué permanece pendiente para producción?
- **Infraestructura Física:** Servidores dedicados BigBlueButton y servidor de relay Coturn (STUN/TURN en TCP 443) para redes escolares.
- **Servicios de Nube:** Almacenamiento de objetos (S3/MinIO), servidor transaccional de correo SMTP y worker asíncrono para PDFs masivos.
- **Validación y Acuerdos:** Pruebas de carga empíricas para determinar la capacidad a escala nacional, formalización de la política de datos (Ley 1581) y acuerdos técnicos de interoperabilidad con SIMAT. No reemplaza los sistemas oficiales del MEN ni DANE.

### 6. ¿Qué se propone al Estado colombiano?
Una **propuesta técnica de donación y transferencia tecnológica** bajo licencia de código abierto **Apache 2.0**. El Estado adquiere el código fuente completo, esquemas de base de datos relacional y documentación sin costos de licenciamiento ($0 COP en software), sujeta a revisión jurídica y a los instrumentos que determine la entidad competente.

### 7. ¿Cuál es el próximo paso?
Realizar una demostración técnica en vivo ante los comités evaluadores del MEN, MinTIC y Secretarías de Educación, acordando las bases para una **Fase Piloto en 5 a 10 colegios oficiales** durante un período académico escolar.
