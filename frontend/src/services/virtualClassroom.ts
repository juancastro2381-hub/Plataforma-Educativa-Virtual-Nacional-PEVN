/**
 * PEVN Frontend — Virtual Classroom & Meetings API Service
 *
 * Strongly-typed API client service for Virtual Classroom lifecycle,
 * participant join token generation, real-time attendance telemetry,
 * and recording synchronization.
 */

import apiClient from '@/services/api/client'
import type {
  JoinMeetingResponse,
  MeetingAttendanceListResponse,
  MeetingAttendanceResponse,
  MeetingRecordingListResponse,
  MeetingRecordingResponse,
  PublishRecordingRequest,
  VirtualClassroomCreateRequest,
  VirtualClassroomListResponse,
  VirtualClassroomResponse,
  VirtualClassroomStatus,
} from '@/types'

export const virtualClassroomApi = {
  // =========================================================================
  // 1. Virtual Classroom Lifecycle
  // =========================================================================

  async createVirtualClassroom(
    payload: VirtualClassroomCreateRequest
  ): Promise<VirtualClassroomResponse> {
    const res = await apiClient.post<VirtualClassroomResponse>(
      '/api/v1/virtual-classrooms',
      payload
    )
    return res.data
  },

  async listVirtualClassrooms(params?: {
    academic_assignment_id?: string
    status?: VirtualClassroomStatus
    skip?: number
    limit?: number
  }): Promise<VirtualClassroomListResponse> {
    const res = await apiClient.get<VirtualClassroomListResponse>(
      '/api/v1/virtual-classrooms',
      { params }
    )
    return res.data
  },

  async getVirtualClassroom(
    classroomId: string
  ): Promise<VirtualClassroomResponse> {
    const res = await apiClient.get<VirtualClassroomResponse>(
      `/api/v1/virtual-classrooms/${classroomId}`
    )
    return res.data
  },

  async launchVirtualClassroom(
    classroomId: string
  ): Promise<VirtualClassroomResponse> {
    const res = await apiClient.post<VirtualClassroomResponse>(
      `/api/v1/virtual-classrooms/${classroomId}/launch`
    )
    return res.data
  },

  async joinVirtualClassroom(
    classroomId: string,
    redirectUrl?: string
  ): Promise<JoinMeetingResponse> {
    const res = await apiClient.post<JoinMeetingResponse>(
      `/api/v1/virtual-classrooms/${classroomId}/join`,
      null,
      { params: redirectUrl ? { redirect_url: redirectUrl } : undefined }
    )
    return res.data
  },

  async endVirtualClassroom(
    classroomId: string
  ): Promise<VirtualClassroomResponse> {
    const res = await apiClient.post<VirtualClassroomResponse>(
      `/api/v1/virtual-classrooms/${classroomId}/end`
    )
    return res.data
  },

  // =========================================================================
  // 2. Attendance Telemetry
  // =========================================================================

  async listAttendances(
    classroomId: string,
    skip = 0,
    limit = 100
  ): Promise<MeetingAttendanceListResponse> {
    const res = await apiClient.get<MeetingAttendanceListResponse>(
      `/api/v1/virtual-classrooms/${classroomId}/attendances`,
      { params: { skip, limit } }
    )
    return res.data
  },

  async leaveVirtualClassroom(
    classroomId: string
  ): Promise<MeetingAttendanceResponse | null> {
    const res = await apiClient.post<MeetingAttendanceResponse | null>(
      `/api/v1/virtual-classrooms/${classroomId}/leave`
    )
    return res.data
  },

  // =========================================================================
  // 3. Recordings Management
  // =========================================================================

  async listRecordings(
    classroomId: string,
    skip = 0,
    limit = 50
  ): Promise<MeetingRecordingListResponse> {
    const res = await apiClient.get<MeetingRecordingListResponse>(
      `/api/v1/recordings/classroom/${classroomId}`,
      { params: { skip, limit } }
    )
    return res.data
  },

  async syncRecordings(
    classroomId: string
  ): Promise<MeetingRecordingListResponse> {
    const res = await apiClient.post<MeetingRecordingListResponse>(
      `/api/v1/recordings/classroom/${classroomId}/sync`
    )
    return res.data
  },

  async publishRecording(
    recordingId: string,
    isPublished: boolean
  ): Promise<MeetingRecordingResponse> {
    const payload: PublishRecordingRequest = { is_published: isPublished }
    const res = await apiClient.patch<MeetingRecordingResponse>(
      `/api/v1/recordings/${recordingId}/publish`,
      payload
    )
    return res.data
  },

  async deleteRecording(recordingId: string): Promise<void> {
    await apiClient.delete(`/api/v1/recordings/${recordingId}`)
  },
}
