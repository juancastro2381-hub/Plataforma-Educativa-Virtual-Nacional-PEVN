/**
 * PEVN Frontend — Academic Domain API Service
 *
 * Strongly-typed API client service for all Academic Management modules:
 * Academic Years, Groups, Students, Teachers, Guardians, Enrollments,
 * Transfers, and Academic Assignments.
 */

import apiClient from '@/services/api/client'
import type {
  AcademicAssignmentCreateRequest,
  AcademicAssignmentListResponse,
  AcademicAssignmentResponse,
  AcademicYearCreateRequest,
  AcademicYearListResponse,
  AcademicYearResponse,
  AcademicYearStatus,
  AssociateGuardianRequest,
  AssignGroupDirectorRequest,
  EnrollmentCreateRequest,
  EnrollmentGraduateRequest,
  EnrollmentListResponse,
  EnrollmentResponse,
  EnrollmentStatus,
  EnrollmentWithdrawRequest,
  GradeListResponse,
  GroupCapacityResponse,
  GroupCreateRequest,
  GroupListResponse,
  GroupResponse,
  GroupTransferHistoryListResponse,
  GroupTransferRequest,
  GuardianAccountActionResponse,
  GuardianAccountProvisionRequest,
  GuardianAccountStatusUpdateRequest,
  GuardianCreateRequest,
  GuardianListResponse,
  GuardianResponse,
  StudentAccountActionResponse,
  StudentAccountProvisionRequest,
  StudentAccountStatusUpdateRequest,
  StudentCreateRequest,
  StudentGuardianResponse,
  StudentListResponse,
  StudentResponse,
  SubjectCreateRequest,
  SubjectListResponse,
  SubjectResponse,
  TeacherAccountActionResponse,
  TeacherAccountProvisionRequest,
  TeacherContractType,
  TeacherCreateRequest,
  TeacherEligibilityResponse,
  TeacherListResponse,
  TeacherReplacementRequest,
  TeacherReplacementResponse,
  TeacherResponse,
  TransferExecutionResponse,
} from '@/types'

export const academicApi = {
  // =========================================================================
  // 0. Grade Catalog (National Curriculum)
  // =========================================================================

  async listGrades(): Promise<GradeListResponse> {
    const response = await apiClient.get<GradeListResponse>('/api/v1/grades')
    return response.data
  },

  // =========================================================================
  // 0.1. Curricular Subjects Catalog
  // =========================================================================

  async listSubjects(filter?: {
    gradeId?: string
    knowledgeAreaId?: string
    institutionIdOverride?: string
  }): Promise<SubjectListResponse> {
    const params: Record<string, string> = {}
    if (filter?.gradeId) params.grade_id = filter.gradeId
    if (filter?.knowledgeAreaId) params.knowledge_area_id = filter.knowledgeAreaId
    if (filter?.institutionIdOverride) params.institution_id = filter.institutionIdOverride

    const response = await apiClient.get<SubjectListResponse>('/api/v1/subjects', { params })
    return response.data
  },

  async createSubject(
    payload: SubjectCreateRequest,
    institutionIdOverride?: string
  ): Promise<SubjectResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<SubjectResponse>('/api/v1/subjects', payload, { params })
    return response.data
  },

  // =========================================================================
  // 1. Academic Years
  // =========================================================================

  async createAcademicYear(
    payload: AcademicYearCreateRequest,
    institutionIdOverride?: string
  ): Promise<AcademicYearResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<AcademicYearResponse>(
      '/api/v1/academic-years',
      payload,
      { params }
    )
    return response.data
  },

  async getAcademicYear(
    yearId: string,
    institutionIdOverride?: string
  ): Promise<AcademicYearResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.get<AcademicYearResponse>(
      `/api/v1/academic-years/${yearId}`,
      { params }
    )
    return response.data
  },

  async listAcademicYears(
    statusFilter?: AcademicYearStatus,
    institutionIdOverride?: string
  ): Promise<AcademicYearListResponse> {
    const params: Record<string, string> = {}
    if (statusFilter) params.status = statusFilter
    if (institutionIdOverride) params.institution_id = institutionIdOverride

    const response = await apiClient.get<AcademicYearListResponse>(
      '/api/v1/academic-years',
      { params }
    )
    return response.data
  },

  async activateAcademicYear(
    yearId: string,
    institutionIdOverride?: string
  ): Promise<AcademicYearResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<AcademicYearResponse>(
      `/api/v1/academic-years/${yearId}/activate`,
      {},
      { params }
    )
    return response.data
  },

  async closeAcademicYear(
    yearId: string,
    institutionIdOverride?: string
  ): Promise<AcademicYearResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<AcademicYearResponse>(
      `/api/v1/academic-years/${yearId}/close`,
      {},
      { params }
    )
    return response.data
  },

  // =========================================================================
  // 2. Groups / Classrooms
  // =========================================================================

  async createGroup(
    payload: GroupCreateRequest,
    institutionIdOverride?: string
  ): Promise<GroupResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<GroupResponse>(
      '/api/v1/groups',
      payload,
      { params }
    )
    return response.data
  },

  async getGroup(
    groupId: string,
    institutionIdOverride?: string
  ): Promise<GroupResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.get<GroupResponse>(
      `/api/v1/groups/${groupId}`,
      { params }
    )
    return response.data
  },

  async listGroups(filter?: {
    campusId?: string
    academicYearId?: string
    gradeId?: string
    institutionIdOverride?: string
  }): Promise<GroupListResponse> {
    const params: Record<string, string> = {}
    if (filter?.campusId) params.campus_id = filter.campusId
    if (filter?.academicYearId) params.academic_year_id = filter.academicYearId
    if (filter?.gradeId) params.grade_id = filter.gradeId
    if (filter?.institutionIdOverride) params.institution_id = filter.institutionIdOverride

    const response = await apiClient.get<GroupListResponse>(
      '/api/v1/groups',
      { params }
    )
    return response.data
  },

  async getGroupCapacity(
    groupId: string,
    institutionIdOverride?: string
  ): Promise<GroupCapacityResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.get<GroupCapacityResponse>(
      `/api/v1/groups/${groupId}/capacity`,
      { params }
    )
    return response.data
  },

  async assignGroupDirector(
    groupId: string,
    payload: AssignGroupDirectorRequest,
    institutionIdOverride?: string
  ): Promise<GroupResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<GroupResponse>(
      `/api/v1/groups/${groupId}/assign-director`,
      payload,
      { params }
    )
    return response.data
  },

  // =========================================================================
  // 3. Students
  // =========================================================================

  async createStudent(
    payload: StudentCreateRequest,
    institutionIdOverride?: string
  ): Promise<StudentResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<StudentResponse>(
      '/api/v1/students',
      payload,
      { params }
    )
    return response.data
  },

  async getStudent(
    studentId: string,
    institutionIdOverride?: string
  ): Promise<StudentResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.get<StudentResponse>(
      `/api/v1/students/${studentId}`,
      { params }
    )
    return response.data
  },

  async listStudents(
    codeSimat?: string,
    institutionIdOverride?: string
  ): Promise<StudentListResponse> {
    const params: Record<string, string> = {}
    if (codeSimat) params.code_simat = codeSimat
    if (institutionIdOverride) params.institution_id = institutionIdOverride

    const response = await apiClient.get<StudentListResponse>(
      '/api/v1/students',
      { params }
    )
    return response.data
  },

  async getStudentGuardians(
    studentId: string,
    institutionIdOverride?: string
  ): Promise<StudentGuardianResponse[]> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.get<StudentGuardianResponse[]>(
      `/api/v1/students/${studentId}/guardians`,
      { params }
    )
    return response.data
  },

  async provisionStudentAccount(
    studentId: string,
    payload?: StudentAccountProvisionRequest,
    institutionIdOverride?: string
  ): Promise<StudentAccountActionResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<StudentAccountActionResponse>(
      `/api/v1/students/${studentId}/account/provision`,
      payload ?? {},
      { params }
    )
    return response.data
  },

  async updateStudentAccountStatus(
    studentId: string,
    isActive: boolean,
    institutionIdOverride?: string
  ): Promise<StudentAccountActionResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const payload: StudentAccountStatusUpdateRequest = { is_active: isActive }
    const response = await apiClient.post<StudentAccountActionResponse>(
      `/api/v1/students/${studentId}/account/status`,
      payload,
      { params }
    )
    return response.data
  },

  async resetStudentPassword(
    studentId: string,
    institutionIdOverride?: string
  ): Promise<StudentAccountActionResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<StudentAccountActionResponse>(
      `/api/v1/students/${studentId}/account/reset-password`,
      {},
      { params }
    )
    return response.data
  },

  async associateGuardianFromStudent(
    studentId: string,
    guardianId: string,
    payload: AssociateGuardianRequest,
    institutionIdOverride?: string
  ): Promise<StudentGuardianResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<StudentGuardianResponse>(
      `/api/v1/students/${studentId}/guardians/${guardianId}`,
      payload,
      { params }
    )
    return response.data
  },

  async dissociateGuardianFromStudent(
    studentId: string,
    guardianId: string,
    institutionIdOverride?: string
  ): Promise<{ message: string }> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.delete<{ message: string }>(
      `/api/v1/students/${studentId}/guardians/${guardianId}`,
      { params }
    )
    return response.data
  },

  // =========================================================================
  // 4. Teachers
  // =========================================================================

  async createTeacher(
    payload: TeacherCreateRequest,
    institutionIdOverride?: string
  ): Promise<TeacherResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<TeacherResponse>(
      '/api/v1/teachers',
      payload,
      { params }
    )
    return response.data
  },

  async getTeacher(
    teacherId: string,
    institutionIdOverride?: string
  ): Promise<TeacherResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.get<TeacherResponse>(
      `/api/v1/teachers/${teacherId}`,
      { params }
    )
    return response.data
  },

  async listTeachers(
    contractType?: TeacherContractType,
    institutionIdOverride?: string
  ): Promise<TeacherListResponse> {
    const params: Record<string, string> = {}
    if (contractType) params.contract_type = contractType
    if (institutionIdOverride) params.institution_id = institutionIdOverride

    const response = await apiClient.get<TeacherListResponse>(
      '/api/v1/teachers',
      { params }
    )
    return response.data
  },

  async validateTeacherEligibility(
    teacherId: string,
    institutionIdOverride?: string
  ): Promise<TeacherEligibilityResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.get<TeacherEligibilityResponse>(
      `/api/v1/teachers/${teacherId}/eligibility`,
      { params }
    )
    return response.data
  },

  async provisionTeacherAccount(
    teacherId: string,
    payload?: TeacherAccountProvisionRequest,
    institutionIdOverride?: string
  ): Promise<TeacherAccountActionResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<TeacherAccountActionResponse>(
      `/api/v1/teachers/${teacherId}/account/provision`,
      payload ?? {},
      { params }
    )
    return response.data
  },

  async updateTeacherAccountStatus(
    teacherId: string,
    isActive: boolean,
    institutionIdOverride?: string
  ): Promise<TeacherAccountActionResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<TeacherAccountActionResponse>(
      `/api/v1/teachers/${teacherId}/account/status`,
      { is_active: isActive },
      { params }
    )
    return response.data
  },

  async resetTeacherPassword(
    teacherId: string,
    institutionIdOverride?: string
  ): Promise<TeacherAccountActionResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<TeacherAccountActionResponse>(
      `/api/v1/teachers/${teacherId}/account/reset-password`,
      {},
      { params }
    )
    return response.data
  },

  // =========================================================================
  // 5. Guardians
  // =========================================================================

  async createGuardian(payload: GuardianCreateRequest): Promise<GuardianResponse> {
    const response = await apiClient.post<GuardianResponse>(
      '/api/v1/guardians',
      payload
    )
    return response.data
  },

  async getGuardian(guardianId: string): Promise<GuardianResponse> {
    const response = await apiClient.get<GuardianResponse>(
      `/api/v1/guardians/${guardianId}`
    )
    return response.data
  },

  async listGuardians(documentNumber?: string): Promise<GuardianListResponse> {
    const params: Record<string, string> = {}
    if (documentNumber) params.document_number = documentNumber

    const response = await apiClient.get<GuardianListResponse>(
      '/api/v1/guardians',
      { params }
    )
    return response.data
  },

  async provisionGuardianAccount(
    guardianId: string,
    payload?: GuardianAccountProvisionRequest,
    institutionIdOverride?: string
  ): Promise<GuardianAccountActionResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<GuardianAccountActionResponse>(
      `/api/v1/guardians/${guardianId}/account/provision`,
      payload ?? {},
      { params }
    )
    return response.data
  },

  async updateGuardianAccountStatus(
    guardianId: string,
    isActive: boolean,
    institutionIdOverride?: string
  ): Promise<GuardianAccountActionResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const payload: GuardianAccountStatusUpdateRequest = { is_active: isActive }
    const response = await apiClient.post<GuardianAccountActionResponse>(
      `/api/v1/guardians/${guardianId}/account/status`,
      payload,
      { params }
    )
    return response.data
  },

  async resetGuardianPassword(
    guardianId: string,
    institutionIdOverride?: string
  ): Promise<GuardianAccountActionResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<GuardianAccountActionResponse>(
      `/api/v1/guardians/${guardianId}/account/reset-password`,
      {},
      { params }
    )
    return response.data
  },

  async associateGuardianToStudent(
    guardianId: string,
    studentId: string,
    payload: AssociateGuardianRequest,
    institutionIdOverride?: string
  ): Promise<StudentGuardianResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<StudentGuardianResponse>(
      `/api/v1/guardians/${guardianId}/students/${studentId}`,
      payload,
      { params }
    )
    return response.data
  },

  async dissociateGuardian(
    guardianId: string,
    studentId: string,
    institutionIdOverride?: string
  ): Promise<{ message: string }> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.delete<{ message: string }>(
      `/api/v1/guardians/${guardianId}/students/${studentId}`,
      { params }
    )
    return response.data
  },

  async getGuardianStudents(
    guardianId: string,
    institutionIdOverride?: string
  ): Promise<StudentGuardianResponse[]> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.get<StudentGuardianResponse[]>(
      `/api/v1/guardians/${guardianId}/students`,
      { params }
    )
    return response.data
  },

  // =========================================================================
  // 6. Enrollments
  // =========================================================================

  async createEnrollment(
    payload: EnrollmentCreateRequest,
    institutionIdOverride?: string
  ): Promise<EnrollmentResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<EnrollmentResponse>(
      '/api/v1/enrollments',
      payload,
      { params }
    )
    return response.data
  },

  async getEnrollment(
    enrollmentId: string,
    institutionIdOverride?: string
  ): Promise<EnrollmentResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.get<EnrollmentResponse>(
      `/api/v1/enrollments/${enrollmentId}`,
      { params }
    )
    return response.data
  },

  async listEnrollments(filter?: {
    studentId?: string
    groupId?: string
    academicYearId?: string
    status?: EnrollmentStatus
    institutionIdOverride?: string
  }): Promise<EnrollmentListResponse> {
    const params: Record<string, string> = {}
    if (filter?.studentId) params.student_id = filter.studentId
    if (filter?.groupId) params.group_id = filter.groupId
    if (filter?.academicYearId) params.academic_year_id = filter.academicYearId
    if (filter?.status) params.status = filter.status
    if (filter?.institutionIdOverride) params.institution_id = filter.institutionIdOverride

    const response = await apiClient.get<EnrollmentListResponse>(
      '/api/v1/enrollments',
      { params }
    )
    return response.data
  },

  async activateEnrollment(
    enrollmentId: string,
    institutionIdOverride?: string
  ): Promise<EnrollmentResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<EnrollmentResponse>(
      `/api/v1/enrollments/${enrollmentId}/activate`,
      {},
      { params }
    )
    return response.data
  },

  async withdrawEnrollment(
    enrollmentId: string,
    payload: EnrollmentWithdrawRequest,
    institutionIdOverride?: string
  ): Promise<EnrollmentResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<EnrollmentResponse>(
      `/api/v1/enrollments/${enrollmentId}/withdraw`,
      payload,
      { params }
    )
    return response.data
  },

  async graduateEnrollment(
    enrollmentId: string,
    payload: EnrollmentGraduateRequest,
    institutionIdOverride?: string
  ): Promise<EnrollmentResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<EnrollmentResponse>(
      `/api/v1/enrollments/${enrollmentId}/graduate`,
      payload,
      { params }
    )
    return response.data
  },

  // =========================================================================
  // 7. Transfers
  // =========================================================================

  async transferStudentGroup(
    payload: GroupTransferRequest,
    institutionIdOverride?: string
  ): Promise<TransferExecutionResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<TransferExecutionResponse>(
      '/api/v1/transfers',
      payload,
      { params }
    )
    return response.data
  },

  async getTransferHistory(
    enrollmentId: string,
    institutionIdOverride?: string
  ): Promise<GroupTransferHistoryListResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.get<GroupTransferHistoryListResponse>(
      `/api/v1/transfers/enrollments/${enrollmentId}/history`,
      { params }
    )
    return response.data
  },

  // =========================================================================
  // 8. Academic Assignments
  // =========================================================================

  async createAssignment(
    payload: AcademicAssignmentCreateRequest,
    institutionIdOverride?: string
  ): Promise<AcademicAssignmentResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<AcademicAssignmentResponse>(
      '/api/v1/academic-assignments',
      payload,
      { params }
    )
    return response.data
  },

  async getAssignment(
    assignmentId: string,
    institutionIdOverride?: string
  ): Promise<AcademicAssignmentResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.get<AcademicAssignmentResponse>(
      `/api/v1/academic-assignments/${assignmentId}`,
      { params }
    )
    return response.data
  },

  async listAssignments(filter?: {
    teacherId?: string
    groupId?: string
    subjectId?: string
    academicYearId?: string
    isActive?: boolean
    institutionIdOverride?: string
  }): Promise<AcademicAssignmentListResponse> {
    const params: Record<string, string> = {}
    if (filter?.teacherId) params.teacher_id = filter.teacherId
    if (filter?.groupId) params.group_id = filter.groupId
    if (filter?.subjectId) params.subject_id = filter.subjectId
    if (filter?.academicYearId) params.academic_year_id = filter.academicYearId
    if (filter?.isActive !== undefined) params.is_active = String(filter.isActive)
    if (filter?.institutionIdOverride) params.institution_id = filter.institutionIdOverride

    const response = await apiClient.get<AcademicAssignmentListResponse>(
      '/api/v1/academic-assignments',
      { params }
    )
    return response.data
  },

  async deactivateAssignment(
    assignmentId: string,
    institutionIdOverride?: string
  ): Promise<AcademicAssignmentResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<AcademicAssignmentResponse>(
      `/api/v1/academic-assignments/${assignmentId}/deactivate`,
      {},
      { params }
    )
    return response.data
  },

  async replaceTeacher(
    assignmentId: string,
    payload: TeacherReplacementRequest,
    institutionIdOverride?: string
  ): Promise<TeacherReplacementResponse> {
    const params = institutionIdOverride ? { institution_id: institutionIdOverride } : undefined
    const response = await apiClient.post<TeacherReplacementResponse>(
      `/api/v1/academic-assignments/${assignmentId}/replace-teacher`,
      payload,
      { params }
    )
    return response.data
  },
}

export default academicApi
