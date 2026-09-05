/**
 * PEVN Frontend — Guardian Portal API Client Service (Phase 14C)
 *
 * Encapsulates all backend communication for the authenticated guardian portal:
 * - Guardian Profile & contact context
 * - Authorized children list (Context switcher)
 * - Single child consolidated academic overview & alerts
 * - Child tasks & homework follow-up (Read-only observation)
 * - Child official grades & qualitative feedback
 * - Child daily attendance & absence history
 * - Child virtual classrooms schedule & recordings
 *
 * Security:
 * - Anti-IDOR: Only queries child student IDs authorized by /guardian/students.
 * - Identity is derived server-side from JWT claims.
 */

import apiClient from '@/services/api/client'
import type {
  GuardianChildActivitiesListResponse,
  GuardianChildAttendanceListResponse,
  GuardianChildGradesListResponse,
  GuardianChildOverviewResponse,
  GuardianChildVirtualClassroomsListResponse,
  GuardianChildrenListResponse,
  GuardianProfileResponse,
} from '@/types/guardian'
import type { StudentVirtualClassroomItemResponse } from '@/types/student'

export const guardianApi = {
  /**
   * Retrieve authenticated guardian's profile and contact information.
   */
  getProfile: async (): Promise<GuardianProfileResponse> => {
    const res = await apiClient.get<GuardianProfileResponse>('/api/v1/guardian/profile')
    return res.data
  },

  /**
   * List all authorized children legally linked to the authenticated guardian.
   */
  listStudents: async (): Promise<GuardianChildrenListResponse> => {
    const res = await apiClient.get<GuardianChildrenListResponse>('/api/v1/guardian/students')
    return res.data
  },

  /**
   * Retrieve consolidated academic follow-up summary for a single selected child.
   */
  getChildOverview: async (studentId: string): Promise<GuardianChildOverviewResponse> => {
    const res = await apiClient.get<GuardianChildOverviewResponse>(
      `/api/v1/guardian/students/${studentId}/overview`
    )
    return res.data
  },

  /**
   * List homework activities and tasks for parental monitoring (Read-only).
   */
  listChildActivities: async (
    studentId: string,
    params?: {
      subject_id?: string
      submission_status?: string
    }
  ): Promise<GuardianChildActivitiesListResponse> => {
    const res = await apiClient.get<GuardianChildActivitiesListResponse>(
      `/api/v1/guardian/students/${studentId}/activities`,
      { params }
    )
    return res.data
  },

  /**
   * List evaluation records and official grades for the selected child.
   */
  listChildGrades: async (
    studentId: string,
    params?: {
      subject_id?: string
    }
  ): Promise<GuardianChildGradesListResponse> => {
    const res = await apiClient.get<GuardianChildGradesListResponse>(
      `/api/v1/guardian/students/${studentId}/grades`,
      { params }
    )
    return res.data
  },

  /**
   * List attendance logs and statistics for the selected child.
   */
  listChildAttendance: async (
    studentId: string,
    params?: {
      start_date?: string
      end_date?: string
    }
  ): Promise<GuardianChildAttendanceListResponse> => {
    const res = await apiClient.get<GuardianChildAttendanceListResponse>(
      `/api/v1/guardian/students/${studentId}/attendance`,
      { params }
    )
    return res.data
  },

  /**
   * List scheduled virtual classroom sessions for the selected child's group.
   */
  listChildVirtualClassrooms: async (
    studentId: string
  ): Promise<GuardianChildVirtualClassroomsListResponse> => {
    const res = await apiClient.get<GuardianChildVirtualClassroomsListResponse>(
      `/api/v1/guardian/students/${studentId}/virtual-classrooms`
    )
    return res.data
  },

  /**
   * Retrieve detailed information for a specific virtual classroom session.
   */
  getChildVirtualClassroom: async (
    studentId: string,
    classroomId: string
  ): Promise<StudentVirtualClassroomItemResponse> => {
    const res = await apiClient.get<StudentVirtualClassroomItemResponse>(
      `/api/v1/guardian/students/${studentId}/virtual-classrooms/${classroomId}`
    )
    return res.data
  },
}
