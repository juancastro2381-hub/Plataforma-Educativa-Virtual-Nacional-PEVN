/**
 * PEVN Frontend — Student Portal API Client Service
 *
 * Encapsulates all backend communication for the authenticated student portal:
 * - Profile and academic enrollment context
 * - Consolidated dashboard KPIs and upcoming alerts
 * - Subjects & educator directory
 * - Tasks, workshops, exams, feedback and submission tracking
 * - Evaluated grades and academic performance reports
 * - Daily attendance logs and rate calculation
 * - Virtual classrooms and lecture recording archive
 *
 * Security:
 * - Never transmits or accepts student_id from the frontend.
 * - Identity is derived server-side from JWT claims.
 */

import apiClient from '@/services/api/client'
import type {
  StudentActivitiesListResponse,
  StudentActivityItemResponse,
  StudentActivityResourceListResponse,
  StudentAttendanceListResponse,
  StudentDashboardResponse,
  StudentGradesListResponse,
  StudentProfileResponse,
  StudentRecordingsListResponse,
  StudentSubjectsListResponse,
  StudentVirtualClassroomItemResponse,
  StudentVirtualClassroomsListResponse,
  StudentSubmissionDetailResponse,
  StudentSubmissionAttempt,
  SubmissionAttachmentItem,
} from '@/types/student'

export const studentApi = {
  /**
   * Retrieve authenticated student's profile and active enrollment context.
   */
  getProfile: async (): Promise<StudentProfileResponse> => {
    const res = await apiClient.get<StudentProfileResponse>('/api/v1/student/profile')
    return res.data
  },

  /**
   * Retrieve consolidated student dashboard summary in a single round-trip.
   */
  getDashboard: async (): Promise<StudentDashboardResponse> => {
    const res = await apiClient.get<StudentDashboardResponse>('/api/v1/student/dashboard')
    return res.data
  },

  /**
   * List all subjects enrolled for the student's active group.
   */
  listSubjects: async (): Promise<StudentSubjectsListResponse> => {
    const res = await apiClient.get<StudentSubjectsListResponse>('/api/v1/student/subjects')
    return res.data
  },

  /**
   * List academic activities/tasks with optional filtering.
   */
  listActivities: async (params?: {
    subject_id?: string
    submission_status?: string
    activity_type?: string
  }): Promise<StudentActivitiesListResponse> => {
    const res = await apiClient.get<StudentActivitiesListResponse>('/api/v1/student/activities', {
      params,
    })
    return res.data
  },

  /**
   * Retrieve specific activity detail, instructions and grading status (Anti-IDOR protected).
   */
  getActivity: async (activityId: string): Promise<StudentActivityItemResponse> => {
    const res = await apiClient.get<StudentActivityItemResponse>(`/api/v1/student/activities/${activityId}`)
    return res.data
  },

  /**
   * List pedagogical resources attached to an activity (Anti-IDOR protected).
   */
  listActivityResources: async (activityId: string): Promise<StudentActivityResourceListResponse> => {
    const res = await apiClient.get<StudentActivityResourceListResponse>(
      `/api/v1/student/activities/${activityId}/resources`
    )
    return res.data
  },

  /**
   * Download a pedagogical resource file attached to an activity (Anti-IDOR protected).
   */
  downloadActivityResource: async (
    activityId: string,
    resourceId: string
  ): Promise<{ data: Blob; filename?: string }> => {
    const res = await apiClient.get<Blob>(
      `/api/v1/student/activities/${activityId}/resources/${resourceId}/download`,
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

  /**
   * Get student submission status, current attempt draft, and historical attempts.
   */
  getSubmissionDetail: async (activityId: string): Promise<StudentSubmissionDetailResponse> => {
    const res = await apiClient.get<StudentSubmissionDetailResponse>(
      `/api/v1/student/activities/${activityId}/submission`
    )
    return res.data
  },

  /**
   * Save / update text answer in the active draft attempt.
   */
  saveSubmissionDraft: async (
    activityId: string,
    data: { student_response: string | null }
  ): Promise<StudentSubmissionAttempt> => {
    const res = await apiClient.post<StudentSubmissionAttempt>(
      `/api/v1/student/activities/${activityId}/submission/draft`,
      data
    )
    return res.data
  },

  /**
   * Upload an attachment file to the active draft attempt.
   */
  uploadSubmissionFile: async (
    activityId: string,
    file: File
  ): Promise<SubmissionAttachmentItem> => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await apiClient.post<SubmissionAttachmentItem>(
      `/api/v1/student/activities/${activityId}/submission/files`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return res.data
  },

  /**
   * Delete an uploaded attachment file from the active draft attempt.
   */
  deleteSubmissionFile: async (activityId: string, attachmentId: string): Promise<boolean> => {
    await apiClient.delete(
      `/api/v1/student/activities/${activityId}/submission/files/${attachmentId}`
    )
    return true
  },

  /**
   * Confirm and formally submit the activity.
   */
  submitActivity: async (activityId: string): Promise<StudentSubmissionDetailResponse> => {
    const res = await apiClient.post<StudentSubmissionDetailResponse>(
      `/api/v1/student/activities/${activityId}/submission/submit`
    )
    return res.data
  },

  /**
   * Download student submission attachment file.
   */
  downloadSubmissionAttachment: async (
    activityId: string,
    attachmentId: string
  ): Promise<{ data: Blob; filename?: string }> => {
    const res = await apiClient.get<Blob>(
      `/api/v1/student/activities/${activityId}/submission/attachments/${attachmentId}/download`,
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

  /**
   * List graded activities and qualitative feedback for the student.
   */
  listGrades: async (params?: { subject_id?: string }): Promise<StudentGradesListResponse> => {
    const res = await apiClient.get<StudentGradesListResponse>('/api/v1/student/grades', {
      params,
    })
    return res.data
  },

  /**
   * List daily attendance history and summary statistics.
   */
  listAttendance: async (params?: {
    start_date?: string
    end_date?: string
    status?: string
  }): Promise<StudentAttendanceListResponse> => {
    const res = await apiClient.get<StudentAttendanceListResponse>('/api/v1/student/attendance', {
      params,
    })
    return res.data
  },

  /**
   * List virtual classrooms for the student's active group.
   */
  listVirtualClassrooms: async (): Promise<StudentVirtualClassroomsListResponse> => {
    const res = await apiClient.get<StudentVirtualClassroomsListResponse>('/api/v1/student/virtual-classrooms')
    return res.data
  },

  /**
   * Retrieve details and join metadata for an authorized virtual classroom.
   */
  getVirtualClassroom: async (classroomId: string): Promise<StudentVirtualClassroomItemResponse> => {
    const res = await apiClient.get<StudentVirtualClassroomItemResponse>(
      `/api/v1/student/virtual-classrooms/${classroomId}`
    )
    return res.data
  },

  /**
   * List recorded lectures for an authorized virtual classroom.
   */
  listRecordings: async (classroomId: string): Promise<StudentRecordingsListResponse> => {
    const res = await apiClient.get<StudentRecordingsListResponse>(
      `/api/v1/student/virtual-classrooms/${classroomId}/recordings`
    )
    return res.data
  },
}
