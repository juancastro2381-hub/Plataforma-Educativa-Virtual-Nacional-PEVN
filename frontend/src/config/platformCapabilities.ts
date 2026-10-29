/**
 * PEVN Frontend — Platform Capabilities and Maturity Status
 *
 * Centralized, authoritative source of truth for the platform's
 * capability maturity, security remediation state, and external dependencies.
 *
 * Standardized status model:
 *   - IMPLEMENTADA_Y_VERIFICADA: Implemented and validated via automated tests or certified evidence.
 *   - IMPLEMENTADA: Fully implemented in code within its stated scope.
 *   - SOFTWARE_INTEGRADO_INFRAESTRUCTURA_PENDIENTE: Software layer completed; physical or third-party service pending.
 *   - EN_ALISTAMIENTO: Field validation, production infrastructure, domain or institutional authorization pending.
 *   - NO_VERIFICADA: Insufficient evidence to establish implementation or verification status.
 */

export type CapabilityStatus =
  | 'IMPLEMENTADA_Y_VERIFICADA'
  | 'IMPLEMENTADA'
  | 'SOFTWARE_INTEGRADO_INFRAESTRUCTURA_PENDIENTE'
  | 'EN_ALISTAMIENTO'
  | 'NO_VERIFICADA'

export interface PlatformCapability {
  id: number
  title: string
  description: string
  status: CapabilityStatus
  statusLabel: string
  statusDetail?: string
  badgeVariant: 'verified' | 'implemented' | 'dependency_pending' | 'pending' | 'unverified'
  iconText: string
}

export const HERO_STATUS_BADGE = {
  text: 'Plataforma Integral · Gestión Académica, Portales, SIEE y Convivencia Implementados y Verificados',
}

export const EVOLUTION_NOTICE_TEXT =
  'Plataforma en evolución continua. Las capacidades de seguridad, gestión escolar, portales soberanos, evaluación SIEE y convivencia se encuentran implementadas y verificadas en código; aulas sincrónicas y despliegue productivo se encuentran en alistamiento e integración de infraestructura.'

export const PLATFORM_CAPABILITIES: PlatformCapability[] = [
  {
    id: 1,
    title: '1. Fundación, Seguridad e Identidad',
    description:
      'Autenticación robusta con Argon2id, tokens efímeros en memoria y trazabilidad inmutable de auditoría. Control de acceso RBAC verificado con estricta separación de poderes: roles administrativos externos (SuperAdmin, MEN, SED, SEM) restringidos sin acceso a la vida académica escolar ordinaria, preservando la autonomía institucional.',
    status: 'IMPLEMENTADA_Y_VERIFICADA',
    statusLabel: '✓ Implementada y Verificada',
    badgeVariant: 'verified',
    iconText: '✓',
  },
  {
    id: 2,
    title: '2. Estructura Institucional y Matrícula',
    description:
      'Catálogo referencial DANE de departamentos, municipios, colegios y sedes; vigencias lectivas, períodos, grados, grupos y cupos. Estructura de matrícula estudiantil alineada al estándar SIMAT (gestión interna sobre datos de referencia, sin enlace transaccional directo en tiempo real a servidores centrales del MEN).',
    status: 'IMPLEMENTADA_Y_VERIFICADA',
    statusLabel: '✓ Implementada y Verificada',
    statusDetail: 'Catálogo de referencia · Sin enlace en tiempo real al MEN',
    badgeVariant: 'verified',
    iconText: '✓',
  },
  {
    id: 3,
    title: '3. Gestión Académica y Portales Soberanos',
    description:
      'Portales soberanos y tableros independientes para directivos institucionales (Rector), coordinadores, docentes, estudiantes y acudientes con asignación académica de sede. Fronteras RBAC blindadas: la restricción a roles administrativos externos protege la soberanía de la sede sin menoscabar las facultades educativas de la comunidad escolar.',
    status: 'IMPLEMENTADA_Y_VERIFICADA',
    statusLabel: '✓ Implementada y Verificada',
    badgeVariant: 'verified',
    iconText: '✓',
  },
  {
    id: 4,
    title: '4. Actividades Pedagógicas y Asistencia',
    description:
      'Gestión y asignación de tareas pedagógicas, recepción y revisión de entregas estudiantiles con archivos adjuntos o texto en línea, control de asistencia diaria por clase y módulo de planeación curricular docente verificado en pruebas.',
    status: 'IMPLEMENTADA_Y_VERIFICADA',
    statusLabel: '✓ Implementada y Verificada',
    badgeVariant: 'verified',
    iconText: '✓',
  },
  {
    id: 5,
    title: '5. Evaluación SIEE y Promoción Escolar',
    description:
      'Configuración autónoma de criterios y escalas institucionales acorde a los lineamientos del Decreto 1290: planillas de evaluación periódica, nivelaciones con tope legal reglamentario, generación de boletines y actas de promoción anual (implementación de software sin constituir certificación jurídica externa).',
    status: 'IMPLEMENTADA_Y_VERIFICADA',
    statusLabel: '✓ Implementada y Verificada',
    badgeVariant: 'verified',
    iconText: '✓',
  },
  {
    id: 6,
    title: '6. Comunicaciones y Convivencia Escolar',
    description:
      'Emisión de circulares institucionales oficiales con acuse de recibido digital, cartelera digital de noticias escolares y observador formativo del estudiante con tipificación de situaciones disciplinarias conforme a la Ley 1620.',
    status: 'IMPLEMENTADA_Y_VERIFICADA',
    statusLabel: '✓ Implementada y Verificada',
    badgeVariant: 'verified',
    iconText: '✓',
  },
  {
    id: 7,
    title: '7. Aulas Virtuales Sincrónicas',
    description:
      'Adaptador de software BigBlueButton con generación de firmas criptográficas SHA verificado. Servidores físicos de videoconferencia, configuración STUN/TURN y conectividad de producción en territorio pendientes de aprovisionamiento institucional.',
    status: 'SOFTWARE_INTEGRADO_INFRAESTRUCTURA_PENDIENTE',
    statusLabel: '● Software Integrado',
    statusDetail: 'Validación de infraestructura BBB real y TURN/STUN pendiente',
    badgeVariant: 'dependency_pending',
    iconText: '⚡',
  },
  {
    id: 8,
    title: '8. Validación en Campo y Despliegue',
    description:
      'Preparación de infraestructura de producción pública, gestión de asignación de dominio gubernamental .gov.co, pruebas de carga masiva concurrente y formalización de autorizaciones institucionales para despliegue de pilotos controlados.',
    status: 'EN_ALISTAMIENTO',
    statusLabel: 'En Alistamiento',
    statusDetail: 'Pendiente autorización formal de piloto y dominio .gov.co',
    badgeVariant: 'pending',
    iconText: '8',
  },
]

