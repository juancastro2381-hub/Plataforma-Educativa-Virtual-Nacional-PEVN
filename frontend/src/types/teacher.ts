/**
 * PEVN Frontend — Teacher Portal TypeScript Interfaces
 *
 * Types for operational teacher workspace: dashboard metrics, workload,
 * groups, student rosters, academic activities, grades, attendance, and planning.
 */

export type ActivityType = 'TASK' | 'WORKSHOP' | 'QUIZ' | 'EXAM' | 'PROJECT' | 'CLASS_ACTIVITY'
export type ActivityDeliveryType = 'TEXT' | 'FILE' | 'TEXT_AND_FILE'
export type ActivityStatus = 'DRAFT' | 'PUBLISHED' | 'CLOSED'
export type SubmissionStatus = 'DRAFT' | 'SUBMITTED' | 'LATE' | 'RETURNED' | 'GRADED'
export type ActivitySubmissionStatus = 'PENDING' | 'SUBMITTED' | 'GRADED'
export type AttendanceStatusEnum = 'PRESENT' | 'ABSENT' | 'EXCUSED' | 'LATE'
export type AcademicPlanStatus = 'DRAFT' | 'APPROVED' | 'IN_PROGRESS' | 'COMPLETED'

export interface TeacherDashboardSummaryResponse {
  teacher_id: string
  teacher_name: string
  specialty_area: string | null
  institution_id: string
  institution_name: string
  active_academic_year: string | null
  total_active_assignments: number
  total_assigned_groups: number
  total_assigned_subjects: number
  total_active_activities: number
  total_pending_grades: number
  total_enrolled_students: number
}

export interface TeacherAssignmentItemResponse {
  id: string
  teacher_id: string
  subject_id: string
  subject_name: string
  knowledge_area_name: string | null
  group_id: string
  group_name: string
  grade_name: string | null
  campus_name: string | null
  shift: string | null
  academic_year_id: string
  academic_year_name: string
  weekly_hours: number
  is_active: boolean
}

export interface TeacherAssignmentsListResponse {
  items: TeacherAssignmentItemResponse[]
  total: number
}

export interface TeacherGroupItemResponse {
  group_id: string
  group_name: string
  grade_name: string | null
  campus_name: string | null
  shift: string | null
  academic_year_id: string
  academic_year_name: string
  capacity_limit: number
  active_enrolled_count: number
  subjects_taught: string[]
}

export interface TeacherGroupsListResponse {
  items: TeacherGroupItemResponse[]
  total: number
}

export interface TeacherStudentRosterItem {
  student_id: string
  enrollment_id: string
  first_name: string
  last_name: string
  full_name: string
  document_type: string
  document_number: string
  simat_code: string | null
  enrollment_status: string
  enrollment_date: string
}

export interface TeacherGroupRosterResponse {
  group_id: string
  group_name: string
  academic_year_id: string
  academic_year_name: string
  campus_name: string | null
  shift: string | null
  total_students: number
  students: TeacherStudentRosterItem[]
}

export interface AcademicActivityCreateRequest {
  subject_id: string
  group_id: string
  academic_year_id: string
  title: string
  description?: string | null
  activity_type?: ActivityType
  delivery_type?: ActivityDeliveryType
  due_date?: string | null
  max_score?: number
  instructions?: string | null
  resource_url?: string | null
}

export interface AcademicActivityUpdateRequest {
  title?: string
  description?: string | null
  activity_type?: ActivityType
  delivery_type?: ActivityDeliveryType
  due_date?: string | null
  max_score?: number
  instructions?: string | null
  resource_url?: string | null
}

export type ActivityResourceType = 'URL' | 'FILE'

export interface ActivityResourceResponse {
  id: string
  activity_id: string
  resource_type: ActivityResourceType
  title: string
  description: string | null
  url: string | null
  file_name: string | null
  file_size_bytes: number | null
  mime_type: string | null
  created_at: string
}

export interface ActivityResourceListResponse {
  items: ActivityResourceResponse[]
  total: number
}

export interface AcademicActivityResponse {
  id: string
  institution_id: string
  teacher_id: string
  teacher_name: string | null
  subject_id: string
  subject_name: string | null
  group_id: string
  group_name: string | null
  academic_year_id: string
  academic_year_name: string | null
  title: string
  description: string | null
  activity_type: ActivityType
  delivery_type?: ActivityDeliveryType
  status: ActivityStatus
  publication_date: string | null
  due_date: string | null
  max_score: number
  instructions: string | null
  resource_url: string | null
  resources?: ActivityResourceResponse[]
  total_submissions: number
  total_graded: number
  created_at: string
  updated_at: string
}

export interface AcademicActivityListResponse {
  items: AcademicActivityResponse[]
  total: number
}

// ---------------------------------------------------------------------------
// 4.1 Teacher Submissions Review (Phase B3-H13)
// ---------------------------------------------------------------------------

export interface TeacherSubmissionAttachmentResponse {
  id: string
  original_filename: string
  file_size_bytes: number
  mime_type: string
  created_at: string
}

export interface TeacherSubmissionAttemptResponse {
  id: string
  attempt_number: number
  status: SubmissionStatus
  student_response: string | null
  submitted_at: string | null
  is_late: boolean
  return_feedback: string | null
  returned_at: string | null
  created_at: string
  attachments: TeacherSubmissionAttachmentResponse[]
}

export interface TeacherSubmissionItemResponse {
  student_id: string
  student_name: string
  student_document: string
  submission_id: string | null
  attempt_number: number | null
  status: SubmissionStatus | null
  submitted_at: string | null
  is_late: boolean
  attachments_count: number
  grade_score: number | null
  grade_status: ActivitySubmissionStatus
  graded_at: string | null
}

export interface TeacherSubmissionsListResponse {
  activity_id: string
  activity_title: string
  delivery_type: ActivityDeliveryType
  items: TeacherSubmissionItemResponse[]
  total: number
}

export interface TeacherSubmissionReturnRequest {
  return_feedback: string
}

export interface TeacherSubmissionDetailResponse {
  activity_id: string
  activity_title: string
  delivery_type: ActivityDeliveryType
  student_id: string
  student_name: string
  current_attempt: TeacherSubmissionAttemptResponse | null
  history: TeacherSubmissionAttemptResponse[]
  grade_score: number | null
  grade_feedback: string | null
  graded_at: string | null
}

export interface ActivityGradeItemResponse {
  id: string
  activity_id: string
  student_id: string
  student_name: string
  student_document: string
  score: number | null
  feedback: string | null
  status: ActivitySubmissionStatus
  graded_at: string | null
}

export interface ActivityGradesListResponse {
  activity_id: string
  activity_title: string
  group_name: string
  subject_name: string
  max_score: number
  items: ActivityGradeItemResponse[]
  total: number
}

export interface ActivityGradeEntry {
  student_id: string
  score?: number | null
  feedback?: string | null
}

export interface ActivityGradeBatchUpdateRequest {
  grades: ActivityGradeEntry[]
}

export interface DailyAttendanceStudentItem {
  student_id: string
  student_name: string
  document_number: string
  status: AttendanceStatusEnum
  remarks: string | null
}

export interface DailyAttendanceListResponse {
  group_id: string
  group_name: string
  subject_id: string | null
  subject_name: string | null
  attendance_date: string
  total_students: number
  items: DailyAttendanceStudentItem[]
}

export interface DailyAttendanceEntry {
  student_id: string
  status: AttendanceStatusEnum
  remarks?: string | null
}

export interface DailyAttendanceBatchRequest {
  subject_id?: string | null
  attendance_date: string
  records: DailyAttendanceEntry[]
}

export interface AcademicPlanCreateRequest {
  subject_id: string
  group_id: string
  academic_year_id: string
  unit_name: string
  competencies?: string | null
  learning_objectives?: string | null
  methodology?: string | null
  evaluation_criteria?: string | null
  resources?: string | null
  status?: AcademicPlanStatus
  start_date?: string | null
  end_date?: string | null
}

export interface AcademicPlanUpdateRequest {
  unit_name?: string
  competencies?: string | null
  learning_objectives?: string | null
  methodology?: string | null
  evaluation_criteria?: string | null
  resources?: string | null
  status?: AcademicPlanStatus
  start_date?: string | null
  end_date?: string | null
}

export interface AcademicPlanResponse {
  id: string
  institution_id: string
  teacher_id: string
  teacher_name: string | null
  subject_id: string
  subject_name: string | null
  group_id: string
  group_name: string | null
  academic_year_id: string
  academic_year_name: string | null
  unit_name: string
  competencies: string | null
  learning_objectives: string | null
  methodology: string | null
  evaluation_criteria: string | null
  resources: string | null
  status: AcademicPlanStatus
  start_date: string | null
  end_date: string | null
  created_at: string
  updated_at: string
}

export interface AcademicPlanListResponse {
  items: AcademicPlanResponse[]
  total: number
}
