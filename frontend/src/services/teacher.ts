/**
 * PEVN Frontend — Teacher Portal API Service Client
 *
 * Provides typed methods for interacting with teacher portal backend endpoints:
 * dashboard KPIs, assignments, groups, rosters, activities, grades, attendance, and planning.
 */

import apiClient from '@/services/api/client'
import type {
  AcademicActivityCreateRequest,
  AcademicActivityListResponse,
  AcademicActivityResponse,
  AcademicActivityUpdateRequest,
  AcademicPlanCreateRequest,
  AcademicPlanListResponse,
  AcademicPlanResponse,
  AcademicPlanUpdateRequest,
  ActivityGradeBatchUpdateRequest,
  ActivityGradesListResponse,
  ActivityResourceListResponse,
  ActivityResourceResponse,
  DailyAttendanceBatchRequest,
  DailyAttendanceListResponse,
  TeacherAssignmentsListResponse,
  TeacherDashboardSummaryResponse,
  TeacherGroupRosterResponse,
  TeacherGroupsListResponse,
  TeacherSubmissionsListResponse,
  TeacherSubmissionDetailResponse,
} from '@/types/teacher'
import type {
  CoexistenceSituationType,
  IncidentFollowUpItem,
  IncidentFollowUpPayload,
  IncidentStatus,
  StudentIncidentCreateRequest,
  StudentIncidentItem,
  StudentIncidentListResponse,
  StudentIncidentUpdateRequest,
} from '@/types/communication'

export const teacherApi = {
  // 1. Dashboard
  getDashboardSummary: async (): Promise<TeacherDashboardSummaryResponse> => {
    const res = await apiClient.get<TeacherDashboardSummaryResponse>('/api/v1/teacher/dashboard')
    return res.data
  },

  // 2. Assignments
  listAssignments: async (isActive = true): Promise<TeacherAssignmentsListResponse> => {
    const res = await apiClient.get<TeacherAssignmentsListResponse>('/api/v1/teacher/assignments', {
      params: { is_active: isActive },
    })
    return res.data
  },

  // 3. Groups & Rosters
  listGroups: async (): Promise<TeacherGroupsListResponse> => {
    const res = await apiClient.get<TeacherGroupsListResponse>('/api/v1/teacher/groups')
    return res.data
  },

  getGroupRoster: async (groupId: string): Promise<TeacherGroupRosterResponse> => {
    const res = await apiClient.get<TeacherGroupRosterResponse>(`/api/v1/teacher/groups/${groupId}/roster`)
    return res.data
  },

  // 4. Academic Activities
  listActivities: async (params?: {
    group_id?: string
    subject_id?: string
    status?: string
  }): Promise<AcademicActivityListResponse> => {
    const res = await apiClient.get<AcademicActivityListResponse>('/api/v1/teacher/activities', {
      params,
    })
    return res.data
  },

  getActivity: async (activityId: string): Promise<AcademicActivityResponse> => {
    const res = await apiClient.get<AcademicActivityResponse>(`/api/v1/teacher/activities/${activityId}`)
    return res.data
  },

  createActivity: async (data: AcademicActivityCreateRequest): Promise<AcademicActivityResponse> => {
    const res = await apiClient.post<AcademicActivityResponse>('/api/v1/teacher/activities', data)
    return res.data
  },

  updateActivity: async (
    activityId: string,
    data: AcademicActivityUpdateRequest
  ): Promise<AcademicActivityResponse> => {
    const res = await apiClient.patch<AcademicActivityResponse>(`/api/v1/teacher/activities/${activityId}`, data)
    return res.data
  },

  publishActivity: async (activityId: string): Promise<AcademicActivityResponse> => {
    const res = await apiClient.post<AcademicActivityResponse>(`/api/v1/teacher/activities/${activityId}/publish`)
    return res.data
  },

  closeActivity: async (activityId: string): Promise<AcademicActivityResponse> => {
    const res = await apiClient.post<AcademicActivityResponse>(`/api/v1/teacher/activities/${activityId}/close`)
    return res.data
  },

  deleteActivity: async (activityId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/teacher/activities/${activityId}`)
  },

  // 4.1. Pedagogical Activity Resources (B3-H11)
  listActivityResources: async (activityId: string): Promise<ActivityResourceListResponse> => {
    const res = await apiClient.get<ActivityResourceListResponse>(
      `/api/v1/teacher/activities/${activityId}/resources`
    )
    return res.data
  },

  createUrlResource: async (
    activityId: string,
    data: { title: string; url: string; description?: string | null }
  ): Promise<ActivityResourceResponse> => {
    const res = await apiClient.post<ActivityResourceResponse>(
      `/api/v1/teacher/activities/${activityId}/resources/url`,
      data
    )
    return res.data
  },

  uploadFileResource: async (
    activityId: string,
    data: { title: string; file: File; description?: string | null }
  ): Promise<ActivityResourceResponse> => {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('resource_type', 'FILE')
    formData.append('file', data.file)
    if (data.description) {
      formData.append('description', data.description)
    }
    const res = await apiClient.post<ActivityResourceResponse>(
      `/api/v1/teacher/activities/${activityId}/resources`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return res.data
  },

  deleteResource: async (activityId: string, resourceId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/teacher/activities/${activityId}/resources/${resourceId}`)
  },

  downloadActivityResource: async (
    activityId: string,
    resourceId: string
  ): Promise<{ data: Blob; filename?: string }> => {
    const res = await apiClient.get<Blob>(
      `/api/v1/teacher/activities/${activityId}/resources/${resourceId}/download`,
      {
        responseType: 'blob',
      }
    )
    let filename: string | undefined = undefined
    const rawHeaders = res.headers as unknown as Record<string, unknown>
    const disposition = typeof rawHeaders['content-disposition'] === 'string' ? rawHeaders['content-disposition'] : undefined
    if (disposition && disposition.includes('filename=')) {
      const filenameMatch = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition)
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '')
      }
    }
    return { data: res.data, filename }
  },

  // 4.2. Student Submissions Review & Returns (Phase B3-H13)
  getActivitySubmissions: async (activityId: string): Promise<TeacherSubmissionsListResponse> => {
    const res = await apiClient.get<TeacherSubmissionsListResponse>(
      `/api/v1/teacher/activities/${activityId}/submissions`
    )
    return res.data
  },

  getStudentSubmissionDetail: async (
    activityId: string,
    studentId: string
  ): Promise<TeacherSubmissionDetailResponse> => {
    const res = await apiClient.get<TeacherSubmissionDetailResponse>(
      `/api/v1/teacher/activities/${activityId}/submissions/${studentId}`
    )
    return res.data
  },

  returnStudentSubmission: async (
    activityId: string,
    studentId: string,
    returnFeedback: string
  ): Promise<TeacherSubmissionDetailResponse> => {
    const res = await apiClient.post<TeacherSubmissionDetailResponse>(
      `/api/v1/teacher/activities/${activityId}/submissions/${studentId}/return`,
      { return_feedback: returnFeedback }
    )
    return res.data
  },

  downloadStudentSubmissionAttachment: async (
    activityId: string,
    studentId: string,
    attachmentId: string
  ): Promise<{ data: Blob; filename?: string }> => {
    const res = await apiClient.get<Blob>(
      `/api/v1/teacher/activities/${activityId}/submissions/${studentId}/attachments/${attachmentId}/download`,
      {
        responseType: 'blob',
      }
    )
    let filename: string | undefined = undefined
    const rawHeaders = res.headers as unknown as Record<string, unknown>
    const disposition = typeof rawHeaders['content-disposition'] === 'string' ? rawHeaders['content-disposition'] : undefined
    if (disposition && disposition.includes('filename=')) {
      const filenameMatch = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition)
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '')
      }
    }
    return { data: res.data, filename }
  },

  // 5. Grades & Evaluations
  getActivityGrades: async (activityId: string): Promise<ActivityGradesListResponse> => {
    const res = await apiClient.get<ActivityGradesListResponse>(`/api/v1/teacher/activities/${activityId}/grades`)
    return res.data
  },

  batchUpdateActivityGrades: async (
    activityId: string,
    data: ActivityGradeBatchUpdateRequest
  ): Promise<ActivityGradesListResponse> => {
    const res = await apiClient.put<ActivityGradesListResponse>(`/api/v1/teacher/activities/${activityId}/grades`, data)
    return res.data
  },

  // 6. Daily Attendance
  getDailyAttendance: async (
    groupId: string,
    attendanceDate: string,
    subjectId?: string
  ): Promise<DailyAttendanceListResponse> => {
    const res = await apiClient.get<DailyAttendanceListResponse>(`/api/v1/teacher/groups/${groupId}/attendance`, {
      params: {
        attendance_date: attendanceDate,
        subject_id: subjectId,
      },
    })
    return res.data
  },

  recordDailyAttendance: async (
    groupId: string,
    data: DailyAttendanceBatchRequest
  ): Promise<DailyAttendanceListResponse> => {
    const res = await apiClient.post<DailyAttendanceListResponse>(`/api/v1/teacher/groups/${groupId}/attendance`, data)
    return res.data
  },

  // 7. Curricular Planning
  listPlanning: async (params?: {
    group_id?: string
    subject_id?: string
  }): Promise<AcademicPlanListResponse> => {
    const res = await apiClient.get<AcademicPlanListResponse>('/api/v1/teacher/planning', {
      params,
    })
    return res.data
  },

  createPlanning: async (data: AcademicPlanCreateRequest): Promise<AcademicPlanResponse> => {
    const res = await apiClient.post<AcademicPlanResponse>('/api/v1/teacher/planning', data)
    return res.data
  },

  updatePlanning: async (
    planId: string,
    data: AcademicPlanUpdateRequest
  ): Promise<AcademicPlanResponse> => {
    const res = await apiClient.patch<AcademicPlanResponse>(`/api/v1/teacher/planning/${planId}`, data)
    return res.data
  },

  deletePlanning: async (planId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/teacher/planning/${planId}`)
  },

  // 8. Coexistence & Observador del Estudiante
  getIncidents: async (params?: {
    student_id?: string
    situation_type?: CoexistenceSituationType
    status?: IncidentStatus
  }): Promise<StudentIncidentListResponse> => {
    const res = await apiClient.get<StudentIncidentListResponse>('/api/v1/incidents', {
      params,
    })
    return res.data
  },

  getIncident: async (incidentId: string): Promise<StudentIncidentItem> => {
    const res = await apiClient.get<StudentIncidentItem>(`/api/v1/incidents/${incidentId}`)
    return res.data
  },

  createIncident: async (
    payload: StudentIncidentCreateRequest
  ): Promise<StudentIncidentItem> => {
    const res = await apiClient.post<StudentIncidentItem>('/api/v1/incidents', payload)
    return res.data
  },

  updateIncident: async (
    incidentId: string,
    payload: StudentIncidentUpdateRequest
  ): Promise<StudentIncidentItem> => {
    const res = await apiClient.put<StudentIncidentItem>(
      `/api/v1/incidents/${incidentId}`,
      payload
    )
    return res.data
  },

  addFollowUp: async (
    incidentId: string,
    payload: IncidentFollowUpPayload
  ): Promise<IncidentFollowUpItem> => {
    const res = await apiClient.post<IncidentFollowUpItem>(
      `/api/v1/incidents/${incidentId}/follow-ups`,
      payload
    )
    return res.data
  },
}
