/**
 * PEVN Frontend — SIEE Evaluation & Grading API Service (Phase 16D)
 *
 * Strongly-typed API client service for all evaluation domain endpoints:
 * - SIEE Active Policy discovery
 * - Consolidated Period Grading Sheet (Sabana de Notas)
 * - Period Grades Batch Saving with mandatory hybrid adjustment reason
 * - Recovery / Remediation Grade Recording with backend cap enforcement
 * - Period Closure (Directive) & Reopening with mandatory audit justification
 * - Academic Year Term Periods discovery
 */

import apiClient from '@/services/api/client'
import type {
  AcademicPeriodListResponse,
  ClosePeriodResponse,
  GroupConsolidationMatrixResponse,
  PeriodSheetResponse,
  RecordRecoveryGradeRequest,
  RecoveryGradeResponse,
  SavePeriodGradesRequest,
  SavePeriodGradesResponse,
  SieePolicyResponse,
  StudentReportCardResponse,
  UnlockPeriodRequest,
  UnlockPeriodResponse,
  YearEndReportCardResponse,
} from '@/types'

export const evaluationApi = {
  // =========================================================================
  // 1. SIEE Institutional Policy
  // =========================================================================

  /**
   * Retrieves the active SIEE policy for the current institution.
   * Authoritative source of scale bounds, passing grade, and recovery caps.
   */
  async getActiveSieePolicy(academicYearId?: string): Promise<SieePolicyResponse> {
    const params: Record<string, string> = {}
    if (academicYearId) {
      params.academic_year_id = academicYearId
    }
    const response = await apiClient.get<SieePolicyResponse>(
      '/api/v1/siee-policies/active',
      { params }
    )
    return response.data
  },

  // =========================================================================
  // 2. Consolidated Period Grading Sheet (Sábana de Calificaciones)
  // =========================================================================

  /**
   * Fetches the complete period consolidation sheet for a group, subject, and period.
   * Returns calculated scores, final scores, absences, and recovery records.
   */
  async getPeriodSheet(params: {
    periodId: string
    groupId: string
    subjectId: string
  }): Promise<PeriodSheetResponse> {
    const response = await apiClient.get<PeriodSheetResponse>(
      '/api/v1/evaluations/period-sheet',
      {
        params: {
          period_id: params.periodId,
          group_id: params.groupId,
          subject_id: params.subjectId,
        },
      }
    )
    return response.data
  },

  /**
   * Saves or updates consolidated period grades for students in a group x subject.
   * Requires adjustment_reason if final_score !== calculated_score.
   */
  async savePeriodGrades(
    payload: SavePeriodGradesRequest
  ): Promise<SavePeriodGradesResponse> {
    const response = await apiClient.post<SavePeriodGradesResponse>(
      '/api/v1/evaluations/period-grades',
      payload
    )
    return response.data
  },

  // =========================================================================
  // 3. Recovery / Remediation Grade Recording
  // =========================================================================

  /**
   * Records a remedial recovery grade for a student's period subject grade.
   * The backend applies the institutional SIEE cap (min(recovery, cap)).
   */
  async recordRecoveryGrade(
    gradeId: string,
    payload: RecordRecoveryGradeRequest
  ): Promise<RecoveryGradeResponse> {
    const response = await apiClient.post<RecoveryGradeResponse>(
      `/api/v1/evaluations/grades/${gradeId}/recoveries`,
      payload
    )
    return response.data
  },

  // =========================================================================
  // 4. Period Closure & Reopening Lifecycle (Directive Authority)
  // =========================================================================

  /**
   * Officially closes and seals an academic evaluation period.
   * Requires evaluations:close_period permission.
   */
  async closePeriod(periodId: string): Promise<ClosePeriodResponse> {
    const response = await apiClient.post<ClosePeriodResponse>(
      `/api/v1/evaluations/periods/${periodId}/close`
    )
    return response.data
  },

  /**
   * Reopens a previously closed academic period.
   * Requires evaluations:reopen_period permission and a mandatory justification string.
   */
  async unlockPeriod(
    periodId: string,
    payload: UnlockPeriodRequest
  ): Promise<UnlockPeriodResponse> {
    const response = await apiClient.post<UnlockPeriodResponse>(
      `/api/v1/evaluations/periods/${periodId}/unlock`,
      payload
    )
    return response.data
  },

  // =========================================================================
  // 5. Academic Periods Discovery
  // =========================================================================

  /**
   * Lists all academic term periods associated with an academic school year.
   */
  async listAcademicPeriods(yearId: string): Promise<AcademicPeriodListResponse> {
    const response = await apiClient.get<AcademicPeriodListResponse>(
      `/api/v1/academic-years/${yearId}/periods`
    )
    return response.data
  },

  // =========================================================================
  // 6. Official Report Cards & Academic Reports (Phase 16E)
  // =========================================================================

  /**
   * Generates the authoritative official period report card for a student.
   * Anti-IDOR protected: Students can only view their own; Guardians can only view linked children.
   */
  async getStudentReportCard(
    studentId: string,
    periodId: string,
    institutionId?: string
  ): Promise<StudentReportCardResponse> {
    const params: Record<string, string> = { period_id: periodId }
    if (institutionId) {
      params.institution_id = institutionId
    }
    const response = await apiClient.get<StudentReportCardResponse>(
      `/api/v1/evaluations/report-cards/student/${studentId}`,
      { params }
    )
    return response.data
  },

  /**
   * Generates the cumulative year-end report card with weighted annual averages
   * and official promotion/graduation outcome.
   */
  async getStudentYearEndReportCard(
    studentId: string,
    academicYearId: string,
    institutionId?: string
  ): Promise<YearEndReportCardResponse> {
    const params: Record<string, string> = { academic_year_id: academicYearId }
    if (institutionId) {
      params.institution_id = institutionId
    }
    const response = await apiClient.get<YearEndReportCardResponse>(
      `/api/v1/evaluations/report-cards/student/${studentId}/year-end`,
      { params }
    )
    return response.data
  },

  /**
   * Generates the group consolidation matrix (Sábana de Notas) including
   * student averages and ranking.
   * Authorized for Directives and Teachers.
   */
  async getGroupConsolidationMatrix(
    groupId: string,
    periodId: string,
    institutionId?: string
  ): Promise<GroupConsolidationMatrixResponse> {
    const params: Record<string, string> = { period_id: periodId }
    if (institutionId) {
      params.institution_id = institutionId
    }
    const response = await apiClient.get<GroupConsolidationMatrixResponse>(
      `/api/v1/evaluations/report-cards/group/${groupId}/matrix`,
      { params }
    )
    return response.data
  },
}

export default evaluationApi
