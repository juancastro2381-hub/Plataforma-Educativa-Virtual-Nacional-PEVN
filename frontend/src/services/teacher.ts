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
  DailyAttendanceBatchRequest,
  DailyAttendanceListResponse,
  TeacherAssignmentsListResponse,
  TeacherDashboardSummaryResponse,
  TeacherGroupRosterResponse,
  TeacherGroupsListResponse,
} from '@/types/teacher'

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
}
