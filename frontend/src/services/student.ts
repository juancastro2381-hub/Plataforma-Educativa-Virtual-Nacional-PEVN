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
  StudentAttendanceListResponse,
  StudentDashboardResponse,
  StudentGradesListResponse,
  StudentProfileResponse,
  StudentRecordingsListResponse,
  StudentSubjectsListResponse,
  StudentVirtualClassroomItemResponse,
  StudentVirtualClassroomsListResponse,
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
