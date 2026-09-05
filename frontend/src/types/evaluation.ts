/**
 * PEVN Frontend — SIEE Evaluation & Grading TypeScript Types (Phase 16D)
 *
 * Strongly-typed contracts mirroring backend schemas in:
 * - app/schemas/evaluation.py
 * - app/schemas/academic.py (AcademicPeriod)
 * - app/models/evaluation.py
 */

// ===========================================================================
// 1. SIEE Domain Enums & Literals
// ===========================================================================

export type SieePerformanceLevel = 'BAJO' | 'BASICO' | 'ALTO' | 'SUPERIOR'

export type SieeScaleType =
  | 'NUMERIC_1_5'
  | 'NUMERIC_1_10'
  | 'NUMERIC_1_100'
  | 'PERCENTAGE'
  | 'LETTER'

export type SieeRoundingMode = 'ROUND_HALF_UP' | 'TRUNCATE' | 'CEIL' | 'FLOOR'

export type SieePeriodWeightMode = 'EQUAL_WEIGHT' | 'PROGRESSIVE_WEIGHT' | 'CUSTOM_WEIGHT'

export type SieePromotionRuleType =
  | 'MIN_AVERAGE'
  | 'MAX_FAILED_AREAS'
  | 'MAX_FAILED_SUBJECTS'
  | 'ATTENDANCE_PERCENTAGE'
  | 'CORE_AREAS_REQUIRED'

// ===========================================================================
// 2. Academic Period & SIEE Policy Response Types
// ===========================================================================

export interface AcademicPeriodResponse {
  id: string
  academic_year_id: string
  period_number: number
  name: string
  weight_percentage: number
  start_date: string
  end_date: string
  is_closed: boolean
  created_at?: string
  updated_at?: string
}

export interface AcademicPeriodListResponse {
  items: AcademicPeriodResponse[]
  total: number
}

export interface SieePolicyThresholds {
  bajo_max: number
  basico_max: number
  alto_max: number
  superior_max: number
}

export interface SieePolicyResponse {
  id: string
  institution_id: string
  academic_year_id: string
  version: number
  name: string
  description: string | null
  is_active: boolean
  scale_type: SieeScaleType
  scale_min: number
  scale_max: number
  min_passing_score: number
  scale_decimals: number
  rounding_mode: SieeRoundingMode
  period_weight_mode: SieePeriodWeightMode
  allow_remedial_exams: boolean
  recovery_grade_cap: number
  max_remedial_attempts: number
  max_failed_subjects_for_promotion: number
  max_failed_core_subjects: number
  attendance_affects_promotion: boolean
  min_attendance_percentage: number
  threshold_bajo_max: number
  threshold_basico_max: number
  threshold_alto_max: number
  threshold_superior_max: number
  created_at?: string
  updated_at?: string
}

// ===========================================================================
// 3. Period Consolidation Sheet Types
// ===========================================================================

export interface ActivitySummary {
  id: string
  title: string
  activity_type: string
  max_score: number
  weight_percentage: number
  due_date: string | null
}

export interface AchievementSummary {
  id?: string
  code: string | null
  description: string
  performance_level: SieePerformanceLevel
}

export interface RecoverySummary {
  id: string
  initial_score: number
  recovery_score: number
  applied_cap: number
  final_adjusted_score: number
  recovery_date: string
  act_number: string | null
}

export interface StudentGradeRow {
  student_id: string
  enrollment_id: string
  simat_code: string | null
  first_name: string
  last_name: string
  document_number: string | null
  activity_grades: Record<string, number | null>
  calculated_score: number
  final_score: number
  adjustment_reason: string | null
  performance_level: SieePerformanceLevel
  total_absences: number
  unexcused_absences: number
  observations: string | null
  is_locked: boolean
  recoveries: RecoverySummary[]
}

export interface PeriodSheetPeriodInfo {
  id: string
  name: string
  period_number: number
  weight_percentage: number
  is_closed: boolean
}

export interface PeriodSheetGroupInfo {
  id: string
  name: string
  grade_name?: string
  shift?: string
}

export interface PeriodSheetSubjectInfo {
  id: string
  name: string
  weekly_hours?: number
}

export interface PeriodSheetPolicyInfo {
  id: string
  name: string
  min_passing_score: number
  scale_min: number
  scale_max: number
  recovery_grade_cap: number
  scale_decimals?: number
  allow_remedial_exams?: boolean
  [key: string]: unknown
}

export interface PeriodSheetResponse {
  period: PeriodSheetPeriodInfo
  group: PeriodSheetGroupInfo
  subject: PeriodSheetSubjectInfo
  policy: PeriodSheetPolicyInfo
  activities: ActivitySummary[]
  achievements: AchievementSummary[]
  students: StudentGradeRow[]
}

// ===========================================================================
// 4. Mutation Request / Response Payloads
// ===========================================================================

export interface GradeItemRequest {
  student_id: string
  enrollment_id: string
  calculated_score: number
  final_score: number
  adjustment_reason?: string | null
  observations?: string | null
  total_absences?: number
  unexcused_absences?: number
}

export interface AchievementItemRequest {
  code?: string | null
  description: string
  performance_level: SieePerformanceLevel
}

export interface SavePeriodGradesRequest {
  period_id: string
  group_id: string
  subject_id: string
  items: GradeItemRequest[]
  achievements?: AchievementItemRequest[]
}

export interface SavePeriodGradesResponse {
  saved_count: number
  period_id: string
  group_id: string
  subject_id: string
}

export interface RecordRecoveryGradeRequest {
  recovery_score: number
  recovery_date: string
  act_number?: string | null
  observations?: string | null
}

export interface RecoveryGradeResponse {
  id: string
  period_subject_grade_id: string
  initial_score: number
  recovery_score: number
  applied_cap: number
  final_adjusted_score: number
  recovery_date: string
  act_number: string | null
  observations: string | null
  created_at: string
}

export interface ClosePeriodResponse {
  period_id: string
  is_closed: boolean
}

export interface UnlockPeriodRequest {
  reason: string
}

export interface UnlockPeriodResponse {
  period_id: string
  is_closed: boolean
}

// ===========================================================================
// 5. Official Report Card & Academic Reports Types (Phase 16E)
// ===========================================================================

export interface ReportCardAchievementItem {
  code?: string | null
  description: string
  level: string
}

export interface ReportCardRecoveryItem {
  initial_score: number
  recovery_score: number
  applied_cap: number
  final_adjusted_score: number
  recovery_date: string
  act_number?: string | null
}

export interface ReportCardSubjectItem {
  subject_id: string
  subject_name: string
  area_name: string
  weekly_hours: number
  teacher_name: string
  calculated_score: number
  final_score: number
  performance_level: SieePerformanceLevel
  is_passed: boolean
  adjustment_reason?: string | null
  total_absences: number
  unexcused_absences: number
  observations?: string | null
  achievements: ReportCardAchievementItem[]
  recoveries: ReportCardRecoveryItem[]
}

export interface ReportCardSummary {
  average_score: number
  performance_level: SieePerformanceLevel
  total_subjects: number
  failed_subjects: number
  passed_subjects: number
  rank: number
  total_students: number
  total_absences: number
  unexcused_absences: number
}

export interface StudentReportCardResponse {
  institution: {
    id: string
    name: string
    dane_code?: string | null
  }
  campus: {
    id: string | null
    name: string
  }
  student: {
    id: string
    simat_code?: string | null
    full_name: string
    document_number: string
    document_type?: string
  }
  academic_year: {
    id: string
    year: number
  }
  period: {
    id: string
    period_number: number
    name: string
    weight_percentage: number
    is_closed: boolean
  }
  group: {
    id: string
    name: string
    grade_name?: string
  }
  summary: ReportCardSummary
  subjects: ReportCardSubjectItem[]
}

export interface YearEndSubjectItem {
  subject_id: string
  subject_name: string
  area_name: string
  period_grades: Record<string | number, { score: number; weight: number }>
  final_annual_score: number
  performance_level: SieePerformanceLevel
  total_absences: number
  unexcused_absences: number
}

export interface YearEndPromotionInfo {
  status: 'PROMOVIDO' | 'NO_PROMOVIDO' | 'GRADUADO' | 'PENDIENTE_NIVELACION' | 'PENDIENTE' | string
  acta_number?: string | null
  decision_date?: string | null
  observations?: string | null
}

export interface YearEndReportCardResponse {
  institution: {
    id: string
    name: string
    dane_code?: string | null
  }
  campus: {
    id: string | null
    name: string
  }
  student: {
    id: string
    simat_code?: string | null
    full_name: string
    document_number: string
  }
  academic_year: {
    id: string
    year: number
    status?: string
  }
  group: {
    id: string
    name: string
    grade_name?: string
  }
  summary: {
    cumulative_average: number
    performance_level: SieePerformanceLevel
    failed_subjects_count: number
  }
  promotion: YearEndPromotionInfo
  subjects: YearEndSubjectItem[]
}

export interface GroupMatrixStudentRow {
  student_id: string
  student_name: string
  simat_code?: string | null
  subjects: Record<string, { score: number | null; level: SieePerformanceLevel | null }>
  average: number
  total_absences: number
  rank: number
}

export interface GroupConsolidationMatrixResponse {
  group: {
    id: string
    name: string
    grade_name?: string
  }
  period: {
    id: string
    period_number: number
    name: string
  }
  subjects: Array<{
    id: string
    name: string
  }>
  students: GroupMatrixStudentRow[]
  total_students: number
}

