/**
 * PEVN Frontend — Student Portal Type Definitions
 *
 * Types for the authenticated student self-service portal:
 * - Profile and Institutional Context
 * - Consolidated Dashboard
 * - Enrolled Subjects & Teachers
 * - Academic Activities & Deadlines
 * - Evaluations & Qualitative Teacher Feedback
 * - Daily Attendance & Metrics
 * - Virtual Classrooms & Lecture Recordings
 */

export type StudentTab =
  | 'dashboard'
  | 'subjects'
  | 'tasks'
  | 'grades'
  | 'attendance'
  | 'virtual-classes'
  | 'communications'
  | 'news'
  | 'incidents'
  | 'profile'

export type ActivitySubmissionStatus = 'PENDING' | 'OVERDUE' | 'SUBMITTED' | 'GRADED'
export type ActivityType = 'HOMEWORK' | 'WORKSHOP' | 'EXAM' | 'QUIZ' | 'PROJECT' | 'CLASS_PARTICIPATION'
export type ActivityStatus = 'DRAFT' | 'PUBLISHED' | 'CLOSED'
export type AttendanceStatus = 'PRESENT' | 'ABSENT' | 'EXCUSED' | 'LATE'
export type VirtualClassroomStatus = 'SCHEDULED' | 'RUNNING' | 'ENDED' | 'CANCELLED'

// ---------------------------------------------------------------------------
// 1. Student Profile
// ---------------------------------------------------------------------------

export interface StudentProfileResponse {
  student_id: string
  user_id: string
  first_name: string
  last_name: string
  full_name: string
  email: string
  document_type: string
  document_number: string
  code_simat: string
  birth_date: string
  institution_id: string
  institution_name: string
  campus_name: string | null
  grade_name: string | null
  group_id: string | null
  group_name: string | null
  academic_year_id: string | null
  academic_year_name: string | null
  enrollment_status: string | null
}

// ---------------------------------------------------------------------------
// 2. Enrolled Subjects
// ---------------------------------------------------------------------------

export interface StudentSubjectItemResponse {
  subject_id: string
  name: string
  weekly_hours: number
  knowledge_area_name: string | null
  teacher_id: string | null
  teacher_name: string | null
  teacher_email: string | null
}

export interface StudentSubjectsListResponse {
  items: StudentSubjectItemResponse[]
  total: number
}

// ---------------------------------------------------------------------------
// 3. Academic Activities / Tasks
// ---------------------------------------------------------------------------

export interface StudentActivityItemResponse {
  id: string
  title: string
  description: string | null
  activity_type: ActivityType
  status: ActivityStatus
  submission_status: ActivitySubmissionStatus
  publication_date: string | null
  due_date: string | null
  max_score: number | string
  score: number | string | null
  feedback: string | null
  graded_at: string | null
  subject_id: string
  subject_name: string
  teacher_name: string | null
  instructions: string | null
  resource_url: string | null
}

export interface StudentActivitiesListResponse {
  items: StudentActivityItemResponse[]
  total: number
}

// ---------------------------------------------------------------------------
// 4. Grades & Evaluations
// ---------------------------------------------------------------------------

export interface StudentGradeItemResponse {
  grade_id: string | null
  activity_id: string
  activity_title: string
  activity_type: ActivityType
  subject_id: string
  subject_name: string
  score: number | string | null
  max_score: number | string
  feedback: string | null
  status: ActivitySubmissionStatus
  graded_at: string | null
  teacher_name: string | null
}

export interface StudentGradesListResponse {
  items: StudentGradeItemResponse[]
  total: number
  average_score: number | string | null
}

// ---------------------------------------------------------------------------
// 5. Attendance
// ---------------------------------------------------------------------------

export interface StudentAttendanceItemResponse {
  id: string
  attendance_date: string
  status: AttendanceStatus
  remarks: string | null
  subject_name: string | null
  teacher_name: string | null
}

export interface StudentAttendanceSummary {
  total_sessions: number
  present_count: number
  absent_count: number
  excused_count: number
  late_count: number
  attendance_rate: number
}

export interface StudentAttendanceListResponse {
  items: StudentAttendanceItemResponse[]
  total: number
  summary: StudentAttendanceSummary
}

// ---------------------------------------------------------------------------
// 6. Virtual Classrooms & Recordings
// ---------------------------------------------------------------------------

export interface StudentVirtualClassroomItemResponse {
  id: string
  title: string
  description: string | null
  status: VirtualClassroomStatus | string
  scheduled_start_time: string | null
  scheduled_end_time: string | null
  subject_name: string | null
  teacher_name: string | null
  can_join: boolean
  room_name: string | null
  has_recordings: boolean
}

export interface StudentVirtualClassroomsListResponse {
  items: StudentVirtualClassroomItemResponse[]
  total: number
}

export interface StudentRecordingItemResponse {
  id: string
  virtual_classroom_id: string
  title: string
  duration_seconds: number | null
  file_size_bytes: number | null
  playback_url: string | null
  created_at: string
}

export interface StudentRecordingsListResponse {
  items: StudentRecordingItemResponse[]
  total: number
}

// ---------------------------------------------------------------------------
// 7. Student Dashboard (Consolidated)
// ---------------------------------------------------------------------------

export interface StudentDashboardResponse {
  profile: StudentProfileResponse
  total_subjects: number
  pending_activities_count: number
  overdue_activities_count: number
  graded_activities_count: number
  attendance_summary: StudentAttendanceSummary
  upcoming_virtual_classrooms: StudentVirtualClassroomItemResponse[]
  upcoming_activities: StudentActivityItemResponse[]
  recent_grades: StudentGradeItemResponse[]
}
