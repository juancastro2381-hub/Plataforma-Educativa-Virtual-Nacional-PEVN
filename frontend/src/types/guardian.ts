/**
 * PEVN Frontend — Guardian Portal Type Definitions (Phase 14C)
 *
 * Types for the authenticated guardian / parent monitoring portal:
 * - Guardian Profile and Institutional Context
 * - Linked Children / Selector Navigation
 * - Academic Child Overview & Metrics
 * - Homework / Task Follow-up (Non-submitting supervisor view)
 * - Child Grades, Evaluations & Educator Comments
 * - Child Attendance & Absence Records
 * - Scheduled Virtual Classroom Agendas
 */

import type {
  ActivitySubmissionStatus,
  ActivityType,
  AttendanceStatus,
  StudentActivityItemResponse,
  StudentAttendanceItemResponse,
  StudentAttendanceSummary,
  StudentGradeItemResponse,
  StudentVirtualClassroomItemResponse,
} from './student'

export type {
  ActivitySubmissionStatus,
  ActivityType,
  AttendanceStatus,
  StudentActivityItemResponse,
  StudentAttendanceItemResponse,
  StudentAttendanceSummary,
  StudentGradeItemResponse,
  StudentVirtualClassroomItemResponse,
}

export type GuardianTab =
  | 'dashboard'
  | 'students'
  | 'academic'
  | 'tasks'
  | 'grades'
  | 'attendance'
  | 'virtual-classes'
  | 'communications'
  | 'news'
  | 'incidents'
  | 'profile'

// ---------------------------------------------------------------------------
// 1. Guardian Profile
// ---------------------------------------------------------------------------

export interface GuardianProfileResponse {
  guardian_id: string
  user_id: string
  first_name: string
  last_name: string
  full_name: string
  email: string | null
  document_type: string
  document_number: string
  phone: string
  address: string | null
  institution_id: string
  institution_name: string
  total_linked_students: number
}

// ---------------------------------------------------------------------------
// 2. Linked Children / Selector
// ---------------------------------------------------------------------------

export interface GuardianChildItemResponse {
  student_id: string
  first_name: string
  last_name: string
  full_name: string
  code_simat: string
  document_type: string
  document_number: string
  birth_date: string
  relationship_type: string
  is_primary_contact: boolean
  is_authorized_pickup: boolean
  institution_id: string
  institution_name: string
  campus_name: string | null
  grade_name: string | null
  group_id: string | null
  group_name: string | null
  academic_year_name: string | null
  enrollment_status: string | null
}

export interface GuardianChildrenListResponse {
  items: GuardianChildItemResponse[]
  total: number
}

// ---------------------------------------------------------------------------
// 3. Child Academic Overview (Single Child)
// ---------------------------------------------------------------------------

export interface GuardianChildOverviewResponse {
  child: GuardianChildItemResponse
  total_subjects: number
  pending_tasks_count: number
  overdue_tasks_count: number
  graded_tasks_count: number
  average_score: number | string | null
  attendance_summary: StudentAttendanceSummary
  upcoming_virtual_classrooms: StudentVirtualClassroomItemResponse[]
  pending_activities: StudentActivityItemResponse[]
  recent_grades: StudentGradeItemResponse[]
}

// ---------------------------------------------------------------------------
// 4. Child Activities / Homework Follow-up
// ---------------------------------------------------------------------------

export interface GuardianChildActivitiesListResponse {
  student_id: string
  student_name: string
  items: StudentActivityItemResponse[]
  total: number
}

// ---------------------------------------------------------------------------
// 5. Child Grades & Evaluations
// ---------------------------------------------------------------------------

export interface GuardianChildGradesListResponse {
  student_id: string
  student_name: string
  items: StudentGradeItemResponse[]
  total: number
  average_score: number | string | null
}

// ---------------------------------------------------------------------------
// 6. Child Attendance
// ---------------------------------------------------------------------------

export interface GuardianChildAttendanceListResponse {
  student_id: string
  student_name: string
  items: StudentAttendanceItemResponse[]
  total: number
  summary: StudentAttendanceSummary
}

// ---------------------------------------------------------------------------
// 7. Child Virtual Classrooms (Agenda View)
// ---------------------------------------------------------------------------

export interface GuardianChildVirtualClassroomsListResponse {
  student_id: string
  student_name: string
  items: StudentVirtualClassroomItemResponse[]
  total: number
}
