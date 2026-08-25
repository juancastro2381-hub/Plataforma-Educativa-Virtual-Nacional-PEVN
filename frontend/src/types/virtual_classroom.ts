/**
 * PEVN Frontend — Virtual Classroom & Meeting Domain Types
 *
 * Strongly-typed data contracts matching the backend Pydantic API schemas
 * for Virtual Classrooms, Join Entry, Attendances, and Recordings.
 */

export type VirtualClassroomStatus =
  | 'SCHEDULED'
  | 'RUNNING'
  | 'ENDED'
  | 'CANCELLED'

export type MeetingParticipantRole = 'MODERATOR' | 'VIEWER'

export interface VirtualClassroomCreateRequest {
  title: string
  description?: string | null
  academic_assignment_id?: string | null
  scheduled_start_time?: string | null
  scheduled_end_time?: string | null
  is_recording_enabled?: boolean
  is_breakout_enabled?: boolean
  max_participants?: number
  provider_metadata?: Record<string, unknown>
}

export interface VirtualClassroomResponse {
  id: string
  institution_id: string
  academic_assignment_id?: string | null
  host_user_id: string
  title: string
  description?: string | null
  bbb_meeting_id: string
  status: VirtualClassroomStatus
  scheduled_start_time?: string | null
  scheduled_end_time?: string | null
  actual_start_time?: string | null
  actual_end_time?: string | null
  is_recording_enabled: boolean
  is_breakout_enabled: boolean
  max_participants: number
  created_at: string
  updated_at: string
}

export interface VirtualClassroomListResponse {
  items: VirtualClassroomResponse[]
  total: number
  skip: number
  limit: number
}

export interface JoinMeetingResponse {
  virtual_classroom_id: string
  join_url: string
  role: MeetingParticipantRole
  meeting_title: string
}

export interface MeetingAttendanceResponse {
  id: string
  virtual_classroom_id: string
  user_id: string
  role: MeetingParticipantRole
  joined_at: string
  left_at?: string | null
  duration_seconds?: number | null
  user_full_name?: string | null
  user_email?: string | null
}

export interface MeetingAttendanceListResponse {
  items: MeetingAttendanceResponse[]
  total: number
}

export interface MeetingRecordingResponse {
  id: string
  institution_id: string
  virtual_classroom_id: string
  bbb_record_id: string
  playback_url: string
  duration_seconds: number
  file_size_bytes?: number | null
  is_published: boolean
  recorded_at: string
  created_at: string
}

export interface MeetingRecordingListResponse {
  items: MeetingRecordingResponse[]
  total: number
}

export interface PublishRecordingRequest {
  is_published: boolean
}
