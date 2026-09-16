/**
 * PEVN Frontend — Phase 15 Type Definitions
 *
 * Types for:
 * - Institutional Communications & Circulars (Comunicados Oficiales)
 * - Institutional News & Bulletins (Noticias y Periódico Mural)
 * - School Life & Coexistence Incidents (Observador del Estudiante & Ley 1620)
 */

export type CommunicationCategory =
  | 'CIRCULAR_INFORMATIVA'
  | 'CONVOCATORIA_ACUDIENTES'
  | 'RESOLUCION_RECTORAL'
  | 'CRONOGRAMA_ACADEMICO'
  | 'EMERGENCIA_SANITARIA'
  | 'EVENTO_INSTITUCIONAL'
  | 'OTRO'

export type CommunicationPriority = 'BAJA' | 'MEDIA' | 'ALTA' | 'URGENTE'

export type TargetScopeType =
  | 'ALL_INSTITUTION'
  | 'CAMPUS_SPECIFIC'
  | 'GRADE_SPECIFIC'
  | 'GROUP_SPECIFIC'
  | 'ROLE_SPECIFIC'
  | 'STUDENT_SPECIFIC'
  | 'GUARDIAN_SPECIFIC'

export type PublishingStatus = 'BORRADOR' | 'PUBLICADO' | 'ARCHIVADO'

export interface CommunicationAudienceItem {
  id: string
  scope_type: TargetScopeType
  campus_id?: string | null
  campus_name?: string | null
  grade_id?: string | null
  grade_name?: string | null
  group_id?: string | null
  group_name?: string | null
  role_name?: string | null
  student_id?: string | null
  student_name?: string | null
  guardian_id?: string | null
  guardian_name?: string | null
}

export interface InstitutionalCommunicationItem {
  id: string
  institution_id: string
  title: string
  summary?: string
  content: string
  category: CommunicationCategory
  priority: CommunicationPriority
  status: PublishingStatus
  published_at: string | null
  expires_at: string | null
  requires_acknowledgment: boolean
  is_pinned?: boolean
  author_name: string
  has_read?: boolean
  is_read?: boolean
  is_acknowledged?: boolean
  read_at: string | null
  acknowledged_at: string | null
  created_at: string
}

export interface InstitutionalCommunicationDetail extends InstitutionalCommunicationItem {
  audiences: CommunicationAudienceItem[]
  reads_count?: number
  acknowledgments_count?: number
}

export interface InstitutionalCommunicationListResponse {
  items: InstitutionalCommunicationItem[]
  total: number
  unread_count: number
}

// ---------------------------------------------------------------------------
// Institutional News
// ---------------------------------------------------------------------------

export type NewsCategory =
  | 'LOGRO_ACADEMICO'
  | 'EVENTO_CULTURAL'
  | 'EVENTO_DEPORTIVO'
  | 'PROYECTO_INSTITUCIONAL'
  | 'NOTICIA_GENERAL'
  | 'ACADEMICA'
  | 'DEPORTES'
  | 'CULTURAL'
  | 'CIENCIA_TECNOLOGIA'
  | 'COMUNIDAD'
  | 'CONVOCATORIAS'
  | 'LOGROS'

export interface InstitutionalNewsItem {
  id: string
  institution_id: string
  title: string
  summary: string
  content: string
  category: NewsCategory
  cover_image_url: string | null
  is_published?: boolean
  is_featured?: boolean
  published_at: string | null
  author_name: string
  created_at: string
}

export interface InstitutionalNewsListResponse {
  items: InstitutionalNewsItem[]
  total: number
}

// ---------------------------------------------------------------------------
// School Coexistence & Observador del Estudiante
// ---------------------------------------------------------------------------

export type CoexistenceSituationType =
  | 'TIPO_I'
  | 'TIPO_II'
  | 'TIPO_III'
  | 'OBSERVACION_POSITIVA'

export type IncidentStatus = 'ABIERTO' | 'EN_SEGUIMIENTO' | 'CERRADO'

export interface IncidentFollowUpPayload {
  follow_up_date?: string | null
  notes: string
}

export interface StudentIncidentCreateRequest {
  student_id: string
  situation_type: CoexistenceSituationType
  incident_date?: string | null
  location?: string | null
  description: string
  student_version?: string | null
  pedagogical_measures: string
  commitments?: string | null
  status?: IncidentStatus
  is_visible_to_guardian?: boolean
  is_visible_to_student?: boolean
}

export interface StudentIncidentUpdateRequest {
  situation_type?: CoexistenceSituationType
  incident_date?: string | null
  location?: string | null
  description?: string
  student_version?: string | null
  pedagogical_measures?: string
  commitments?: string | null
  status?: IncidentStatus
  is_visible_to_guardian?: boolean
  is_visible_to_student?: boolean
}

export interface IncidentFollowUpItem {
  id: string
  author_user_id: string
  author_name: string
  follow_up_date: string
  notes: string
  created_at: string
}

export interface StudentIncidentItem {
  id: string
  institution_id: string
  student_id: string
  student_name: string
  student_document: string
  reporter_name: string
  situation_type: CoexistenceSituationType
  incident_date: string
  location: string | null
  description: string
  student_version: string | null
  pedagogical_measures: string
  commitments: string | null
  status: IncidentStatus
  is_visible_to_guardian: boolean
  is_visible_to_student: boolean
  closed_at: string | null
  closed_by_name: string | null
  created_at: string
  follow_ups: IncidentFollowUpItem[]
}

export interface StudentIncidentListResponse {
  items: StudentIncidentItem[]
  total: number
}
