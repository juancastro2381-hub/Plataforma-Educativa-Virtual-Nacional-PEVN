/**
 * PEVN Frontend — Virtual Classrooms Unit & Component Tests
 *
 * Tests for VirtualClassroomsView, room listing, creation modal,
 * launch action, join action, detail modal, and recordings management.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { VirtualClassroomsView } from '@/pages/virtual-classrooms/VirtualClassroomsView'
import type {
  JoinMeetingResponse,
  MeetingAttendanceListResponse,
  MeetingRecordingListResponse,
  MeetingRecordingResponse,
  User,
  VirtualClassroomListResponse,
  VirtualClassroomResponse,
} from '@/types'

const mockTeacherUser: User = {
  id: 'u-teacher-01',
  email: 'prof.matematicas@pevn.edu.co',
  username: 'prof_mate',
  first_name: 'Leonardo',
  last_name: 'Euler',
  full_name: 'Leonardo Euler',
  document_type: 'CC',
  document_number: '98765432',
  institution_id: 'inst-001',
  is_active: true,
  is_verified: true,
  must_change_password: false,
  roles: ['teacher'],
  permissions: ['virtual_classrooms:create', 'virtual_classrooms:read'],
  scope: {
    country_code: 'CO',
    department_id: 'DEP-11',
    municipality_id: 'MUN-11001',
    institution_id: 'inst-001',
    campus_id: null,
    is_national: false,
    is_institution: true,
  },
}

// Mock auth service
vi.mock('@/services/auth', () => ({
  authApi: {
    refresh: (): Promise<string> => Promise.resolve('mock-token'),
    getMyProfile: (): Promise<User> => Promise.resolve(mockTeacherUser),
  },
  default: {
    refresh: (): Promise<string> => Promise.resolve('mock-token'),
    getMyProfile: (): Promise<User> => Promise.resolve(mockTeacherUser),
  },
}))

// Mock virtual classroom service
const mockListClassrooms = vi.fn<() => Promise<VirtualClassroomListResponse>>()
const mockCreateClassroom = vi.fn<(p: unknown) => Promise<VirtualClassroomResponse>>()
const mockLaunchClassroom = vi.fn<(id: string) => Promise<VirtualClassroomResponse>>()
const mockJoinClassroom = vi.fn<(id: string) => Promise<JoinMeetingResponse>>()
const mockEndClassroom = vi.fn<(id: string) => Promise<VirtualClassroomResponse>>()
const mockListAttendances = vi.fn<(id: string) => Promise<MeetingAttendanceListResponse>>()
const mockListRecordings = vi.fn<(id: string) => Promise<MeetingRecordingListResponse>>()
const mockSyncRecordings = vi.fn<(id: string) => Promise<MeetingRecordingListResponse>>()
const mockPublishRecording = vi.fn<(id: string, pub: boolean) => Promise<MeetingRecordingResponse>>()
const mockDeleteRecording = vi.fn<(id: string) => Promise<void>>()
const mockWindowOpen = vi.fn()

vi.mock('@/services/virtualClassroom', () => ({
  virtualClassroomApi: {
    listVirtualClassrooms: () => mockListClassrooms(),
    createVirtualClassroom: (p: unknown) => mockCreateClassroom(p),
    launchVirtualClassroom: (id: string) => mockLaunchClassroom(id),
    joinVirtualClassroom: (id: string) => mockJoinClassroom(id),
    endVirtualClassroom: (id: string) => mockEndClassroom(id),
    listAttendances: (id: string) => mockListAttendances(id),
    listRecordings: (id: string) => mockListRecordings(id),
    syncRecordings: (id: string) => mockSyncRecordings(id),
    publishRecording: (id: string, pub: boolean) => mockPublishRecording(id, pub),
    deleteRecording: (id: string) => mockDeleteRecording(id),
  },
}))

const sampleClassroom: VirtualClassroomResponse = {
  id: 'vc-001',
  institution_id: 'inst-001',
  academic_assignment_id: 'assign-001',
  host_user_id: 'u-teacher-01',
  title: 'Cálculo Diferencial: Límites y Continuidad',
  description: 'Clase sincrónica de cálculo diferencial para grado 11-A',
  bbb_meeting_id: 'vc-bbb-meet-001',
  status: 'SCHEDULED',
  scheduled_start_time: '2026-08-25T08:00:00Z',
  scheduled_end_time: '2026-08-25T10:00:00Z',
  actual_start_time: null,
  actual_end_time: null,
  is_recording_enabled: true,
  is_breakout_enabled: false,
  max_participants: 40,
  created_at: '2026-08-23T10:00:00Z',
  updated_at: '2026-08-23T10:00:00Z',
}

describe('Virtual Classrooms View & Actions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    window.open = mockWindowOpen
  })

  it('renders VirtualClassroomsView and displays classroom list', async () => {
    mockListClassrooms.mockResolvedValueOnce({
      items: [sampleClassroom],
      total: 1,
      skip: 0,
      limit: 50,
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <VirtualClassroomsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(
        screen.getByText('Aulas Virtuales y Clases en Vivo')
      ).toBeInTheDocument()
    })

    expect(
      screen.getByText('Cálculo Diferencial: Límites y Continuidad')
    ).toBeInTheDocument()
    expect(screen.getByText('Programada')).toBeInTheDocument()
  })

  it('renders empty state when no classrooms exist', async () => {
    mockListClassrooms.mockResolvedValueOnce({
      items: [],
      total: 0,
      skip: 0,
      limit: 50,
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <VirtualClassroomsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(
        screen.getByText('No hay aulas virtuales disponibles')
      ).toBeInTheDocument()
    })
  })

  it('opens create modal and schedules new virtual classroom', async () => {
    const user = userEvent.setup()
    mockListClassrooms.mockResolvedValue({
      items: [],
      total: 0,
      skip: 0,
      limit: 50,
    })
    mockCreateClassroom.mockResolvedValueOnce(sampleClassroom)

    render(
      <MemoryRouter>
        <AuthProvider>
          <VirtualClassroomsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: /programar nueva aula virtual/i })
      ).toBeInTheDocument()
    })

    await user.click(
      screen.getByRole('button', { name: /programar nueva aula virtual/i })
    )

    expect(screen.getByText('Programar Nueva Aula Virtual')).toBeInTheDocument()

    const titleInput = screen.getByLabelText(/título de la sesión/i)
    await user.type(titleInput, 'Geometría Analítica')

    const submitBtn = screen.getByRole('button', { name: /crear aula/i })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(mockCreateClassroom).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Geometría Analítica',
          is_recording_enabled: true,
        })
      )
    })
  })

  it('launches scheduled classroom', async () => {
    const user = userEvent.setup()
    mockListClassrooms.mockResolvedValue({
      items: [sampleClassroom],
      total: 1,
      skip: 0,
      limit: 50,
    })
    mockLaunchClassroom.mockResolvedValueOnce({
      ...sampleClassroom,
      status: 'RUNNING',
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <VirtualClassroomsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /iniciar/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /iniciar/i }))

    await waitFor(() => {
      expect(mockLaunchClassroom).toHaveBeenCalledWith('vc-001')
    })
  })

  it('joins meeting and opens signed URL in a secure window', async () => {
    const user = userEvent.setup()
    mockListClassrooms.mockResolvedValue({
      items: [{ ...sampleClassroom, status: 'RUNNING' }],
      total: 1,
      skip: 0,
      limit: 50,
    })
    mockJoinClassroom.mockResolvedValueOnce({
      virtual_classroom_id: 'vc-001',
      join_url: 'https://bbb.pevn.gov.co/bigbluebutton/api/join?session=signed-123',
      role: 'MODERATOR',
      meeting_title: 'Cálculo Diferencial',
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <VirtualClassroomsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: /ingresar a clase/i })
      ).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /ingresar a clase/i }))

    await waitFor(() => {
      expect(mockJoinClassroom).toHaveBeenCalledWith('vc-001')
      expect(mockWindowOpen).toHaveBeenCalledWith(
        'https://bbb.pevn.gov.co/bigbluebutton/api/join?session=signed-123',
        '_blank',
        'noopener,noreferrer'
      )
    })
  })

  it('opens detail modal and displays attendances and recordings', async () => {
    const user = userEvent.setup()
    mockListClassrooms.mockResolvedValue({
      items: [sampleClassroom],
      total: 1,
      skip: 0,
      limit: 50,
    })
    mockListAttendances.mockResolvedValueOnce({
      items: [
        {
          id: 'att-001',
          virtual_classroom_id: 'vc-001',
          user_id: 'u-student-01',
          role: 'VIEWER',
          joined_at: '2026-08-25T08:05:00Z',
          left_at: '2026-08-25T09:55:00Z',
          duration_seconds: 6600,
          user_full_name: 'Isaac Newton',
          user_email: 'newton@pevn.edu.co',
        },
      ],
      total: 1,
    })
    mockListRecordings.mockResolvedValueOnce({
      items: [
        {
          id: 'rec-001',
          institution_id: 'inst-001',
          virtual_classroom_id: 'vc-001',
          bbb_record_id: 'rec-bbb-001',
          playback_url: 'https://bbb.pevn.gov.co/playback/rec-001',
          duration_seconds: 7200,
          file_size_bytes: 104857600,
          is_published: true,
          recorded_at: '2026-08-25T10:00:00Z',
          created_at: '2026-08-25T10:05:00Z',
        },
      ],
      total: 1,
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <VirtualClassroomsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /detalles/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /detalles/i }))

    await waitFor(() => {
      expect(
        screen.getByText('Detalles: Cálculo Diferencial: Límites y Continuidad')
      ).toBeInTheDocument()
    })

    // Click Attendances sub-tab
    const attTab = screen.getByRole('button', { name: /asistencias/i })
    await user.click(attTab)

    expect(screen.getByText('Isaac Newton')).toBeInTheDocument()
    expect(screen.getByText('110 min')).toBeInTheDocument()

    // Click Recordings sub-tab
    const recTab = screen.getByRole('button', { name: /grabaciones/i })
    await user.click(recTab)

    expect(screen.getByText('Grabación (120 min)')).toBeInTheDocument()
    expect(screen.getByText('Publicada')).toBeInTheDocument()
  })
})
