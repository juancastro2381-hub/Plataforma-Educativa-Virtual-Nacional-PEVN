/**
 * PEVN Frontend — Academic Domain TypeScript Types
 *
 * Strongly-typed contracts mirroring backend schemas in app/schemas/academic.py
 * for Academic Years, Groups, Students, Teachers, Guardians, Enrollments,
 * Transfers, and Academic Assignments.
 */

import type { DocumentType, User } from './auth'

// ===========================================================================
// 1. Domain Enums
// ===========================================================================

export type AcademicYearCalendarType = 'CALENDAR_A' | 'CALENDAR_B'

export type AcademicYearStatus = 'PLANNING' | 'ACTIVE' | 'CLOSED'

export type ShiftEnum = 'MANANA' | 'TARDE' | 'NOCHE' | 'UNICA' | 'SABATINA'

export type EducationalLevel = 'PREESCOLAR' | 'PRIMARIA' | 'SECUNDARIA' | 'MEDIA'

export type StudentGender = 'M' | 'F' | 'OTHER'

export type TeacherContractType =
  | 'PROPIEDAD'
  | 'PERIODO_PRUEBA'
  | 'PROVISIONAL'
  | 'TEMPORAL'
  | 'HORA_CATEDRA'

export type GuardianRelationshipType =
  | 'PADRE'
  | 'MADRE'
  | 'ABUELO'
  | 'ABUELA'
  | 'TIO'
  | 'TIA'
  | 'HERMANO'
  | 'HERMANA'
  | 'TUTOR_LEGAL'
  | 'OTRO'

export type EnrollmentStatus = 'PRE_ENROLLED' | 'ACTIVE' | 'WITHDRAWN' | 'GRADUATED'

// ===========================================================================
// 2. Academic Year Types
// ===========================================================================

export interface AcademicYearCreateRequest {
  year: number
  name: string
  start_date: string
  end_date: string
  calendar_type?: AcademicYearCalendarType
  status?: AcademicYearStatus
}

export interface AcademicYearResponse {
  id: string
  institution_id: string
  year: number
  name: string
  start_date: string
  end_date: string
  calendar_type: AcademicYearCalendarType
  status: AcademicYearStatus
  created_at: string
  updated_at: string
}

export interface AcademicYearListResponse {
  items: AcademicYearResponse[]
  total: number
}

// ===========================================================================
// 3. Group Types
// ===========================================================================

export interface GroupCreateRequest {
  campus_id: string
  academic_year_id: string
  grade_id: string
  name: string
  shift?: ShiftEnum
  capacity_limit?: number
  director_teacher_id?: string | null
}

export interface AssignGroupDirectorRequest {
  teacher_id: string
}

export interface GroupResponse {
  id: string
  campus_id: string
  academic_year_id: string
  grade_id: string
  name: string
  shift: ShiftEnum
  capacity_limit: number
  group_director_teacher_id: string | null
  created_at: string
  updated_at: string
}

export interface GroupCapacityResponse {
  group_id: string
  capacity_limit: number
  active_enrolled_count: number
  available_slots: number
}

export interface GroupListResponse {
  items: GroupResponse[]
  total: number
}

// ===========================================================================
// 4. Student Types
// ===========================================================================

export interface StudentCreateRequest {
  user_id: string
  code_simat: string
  birth_date: string
  gender?: StudentGender
  blood_type?: string | null
  stratum?: number | null
  eps_health_provider?: string | null
  has_disability?: boolean
  disability_type?: string | null
}

export interface StudentResponse {
  id: string
  user_id: string
  institution_id: string
  code_simat: string
  birth_date: string
  gender: StudentGender
  blood_type: string | null
  stratum: number | null
  eps_health_provider: string | null
  has_disability: boolean
  disability_type: string | null
  user?: User | null
  created_at: string
  updated_at: string
}

export interface StudentListResponse {
  items: StudentResponse[]
  total: number
}

// ===========================================================================
// 5. Teacher Types
// ===========================================================================

export interface TeacherCreateRequest {
  user_id: string
  specialty_area?: string | null
  contract_type?: TeacherContractType
  escalafon_grade?: string | null
}

export interface TeacherResponse {
  id: string
  user_id: string
  institution_id: string
  specialty_area: string | null
  contract_type: TeacherContractType
  escalafon_grade: string | null
  user?: User | null
  created_at: string
  updated_at: string
}

export interface TeacherEligibilityResponse {
  teacher_id: string
  is_eligible: boolean
  message: string
}

export interface TeacherListResponse {
  items: TeacherResponse[]
  total: number
}

// ===========================================================================
// 6. Guardian Types
// ===========================================================================

export interface GuardianCreateRequest {
  first_name: string
  last_name: string
  document_type?: DocumentType
  document_number: string
  phone: string
  email?: string | null
  address?: string | null
  relationship_type?: GuardianRelationshipType
  user_id?: string | null
}

export interface AssociateGuardianRequest {
  relationship_type?: GuardianRelationshipType
  is_primary_contact?: boolean
  is_authorized_pickup?: boolean
}

export interface GuardianResponse {
  id: string
  first_name: string
  last_name: string
  document_type: DocumentType
  document_number: string
  phone: string
  email: string | null
  address: string | null
  relationship_type: GuardianRelationshipType
  user_id: string | null
  created_at: string
  updated_at: string
}

export interface StudentGuardianResponse {
  id: string
  student_id: string
  guardian_id: string
  relationship_type: GuardianRelationshipType
  is_primary_contact: boolean
  is_authorized_pickup: boolean
  guardian?: GuardianResponse | null
  created_at: string
  updated_at: string
}

export interface GuardianListResponse {
  items: GuardianResponse[]
  total: number
}

// ===========================================================================
// 7. Enrollment Types
// ===========================================================================

export interface EnrollmentCreateRequest {
  student_id: string
  group_id: string
  academic_year_id: string
  enrollment_date?: string | null
  status?: EnrollmentStatus
  status_reason?: string | null
}

export interface EnrollmentWithdrawRequest {
  reason: string
}

export interface EnrollmentGraduateRequest {
  reason?: string
}

export interface EnrollmentResponse {
  id: string
  student_id: string
  group_id: string
  academic_year_id: string
  enrollment_date: string
  status: EnrollmentStatus
  status_reason: string | null
  created_at: string
  updated_at: string
}

export interface EnrollmentListResponse {
  items: EnrollmentResponse[]
  total: number
}

// ===========================================================================
// 8. Transfer Types
// ===========================================================================

export interface GroupTransferRequest {
  enrollment_id: string
  target_group_id: string
  reason: string
}

export interface GroupTransferHistoryResponse {
  id: string
  enrollment_id: string
  previous_group_id: string
  new_group_id: string
  transferred_by_user_id: string
  transfer_date: string
  reason: string
  created_at: string
}

export interface TransferExecutionResponse {
  enrollment: EnrollmentResponse
  transfer_history: GroupTransferHistoryResponse
}

export interface GroupTransferHistoryListResponse {
  items: GroupTransferHistoryResponse[]
  total: number
}

// ===========================================================================
// 9. Academic Assignment Types
// ===========================================================================

export interface AcademicAssignmentCreateRequest {
  teacher_id: string
  subject_id: string
  group_id: string
  academic_year_id: string
  weekly_hours: number
  is_active?: boolean
}

export interface TeacherReplacementRequest {
  new_teacher_id: string
}

export interface AcademicAssignmentResponse {
  id: string
  teacher_id: string
  subject_id: string
  group_id: string
  academic_year_id: string
  weekly_hours: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TeacherReplacementResponse {
  previous_assignment: AcademicAssignmentResponse
  new_assignment: AcademicAssignmentResponse
}

export interface AcademicAssignmentListResponse {
  items: AcademicAssignmentResponse[]
  total: number
}
