/**
 * PEVN Frontend — Communications, News & School Life API Client Service (Phase 15)
 *
 * Encapsulates backend communication for:
 * - Institutional Communications & Circulars (Student & Guardian portals)
 * - Institutional News Bulletins
 * - School Coexistence & Observador del Estudiante (Student & Guardian monitoring)
 */

import apiClient from '@/services/api/client'
import type {
  CoexistenceSituationType,
  IncidentFollowUpItem,
  IncidentFollowUpPayload,
  IncidentStatus,
  InstitutionalCommunicationDetail,
  InstitutionalCommunicationItem,
  InstitutionalCommunicationListResponse,
  InstitutionalNewsItem,
  InstitutionalNewsListResponse,
  StudentIncidentCreateRequest,
  StudentIncidentItem,
  StudentIncidentListResponse,
  StudentIncidentUpdateRequest,
} from '@/types/communication'

export const communicationApi = {
  // -------------------------------------------------------------------------
  // Student Portal Feeds
  // -------------------------------------------------------------------------

  /**
   * List active institutional communications for the authenticated student.
   */
  getStudentCommunications: async (): Promise<InstitutionalCommunicationListResponse> => {
    const res = await apiClient.get<InstitutionalCommunicationListResponse>(
      '/api/v1/student/communications'
    )
    return res.data
  },

  /**
   * Acknowledge receipt of a mandatory communication (Student).
   */
  acknowledgeStudentCommunication: async (
    communicationId: string
  ): Promise<InstitutionalCommunicationItem> => {
    const res = await apiClient.post<InstitutionalCommunicationItem>(
      `/api/v1/student/communications/${communicationId}/acknowledge`
    )
    return res.data
  },

  /**
   * List institutional news for the student portal.
   */
  getStudentNews: async (params?: { category?: string }): Promise<InstitutionalNewsListResponse> => {
    const res = await apiClient.get<InstitutionalNewsListResponse>('/api/v1/student/news', {
      params,
    })
    return res.data
  },

  /**
   * List visible formative coexistence records for the authenticated student.
   */
  getStudentIncidents: async (): Promise<StudentIncidentListResponse> => {
    const res = await apiClient.get<StudentIncidentListResponse>('/api/v1/student/incidents')
    return res.data
  },

  // -------------------------------------------------------------------------
  // Guardian Portal Feeds
  // -------------------------------------------------------------------------

  /**
   * List active institutional communications for the authenticated guardian.
   */
  getGuardianCommunications: async (): Promise<InstitutionalCommunicationListResponse> => {
    const res = await apiClient.get<InstitutionalCommunicationListResponse>(
      '/api/v1/guardian/communications'
    )
    return res.data
  },

  /**
   * Acknowledge receipt of a mandatory communication (Guardian).
   */
  acknowledgeGuardianCommunication: async (
    communicationId: string
  ): Promise<InstitutionalCommunicationItem> => {
    const res = await apiClient.post<InstitutionalCommunicationItem>(
      `/api/v1/guardian/communications/${communicationId}/acknowledge`
    )
    return res.data
  },

  /**
   * List institutional news for the guardian portal.
   */
  getGuardianNews: async (params?: { category?: string }): Promise<InstitutionalNewsListResponse> => {
    const res = await apiClient.get<InstitutionalNewsListResponse>('/api/v1/guardian/news', {
      params,
    })
    return res.data
  },

  /**
   * List visible formative coexistence records for a specific linked child.
   */
  getChildIncidents: async (studentId: string): Promise<StudentIncidentListResponse> => {
    const res = await apiClient.get<StudentIncidentListResponse>(
      `/api/v1/guardian/students/${studentId}/incidents`
    )
    return res.data
  },

  // -------------------------------------------------------------------------
  // Teacher Portal Feeds (Phase B2)
  // -------------------------------------------------------------------------

  /**
   * List active institutional communications for the authenticated teacher.
   */
  getTeacherCommunications: async (): Promise<InstitutionalCommunicationListResponse> => {
    const res = await apiClient.get<InstitutionalCommunicationListResponse>(
      '/api/v1/teacher/communications'
    )
    return res.data
  },

  /**
   * Get single communication detail for teacher and register read receipt.
   */
  getTeacherCommunicationById: async (
    communicationId: string
  ): Promise<InstitutionalCommunicationItem> => {
    const res = await apiClient.get<InstitutionalCommunicationItem>(
      `/api/v1/teacher/communications/${communicationId}`
    )
    return res.data
  },

  /**
   * Acknowledge receipt of a mandatory communication (Teacher).
   */
  acknowledgeTeacherCommunication: async (
    communicationId: string
  ): Promise<InstitutionalCommunicationItem> => {
    const res = await apiClient.post<InstitutionalCommunicationItem>(
      `/api/v1/teacher/communications/${communicationId}/acknowledge`
    )
    return res.data
  },

  /**
   * List institutional news for teacher portal.
   */
  getTeacherNews: async (params?: { category?: string }): Promise<InstitutionalNewsListResponse> => {
    const res = await apiClient.get<InstitutionalNewsListResponse>('/api/v1/teacher/news', {
      params,
    })
    return res.data
  },

  /**
   * List institutional news from general endpoint.
   */
  listNews: async (params?: { category?: string }): Promise<InstitutionalNewsListResponse> => {
    const res = await apiClient.get<InstitutionalNewsListResponse>('/api/v1/news', {
      params,
    })
    return res.data
  },

  // -------------------------------------------------------------------------
  // Generic / Detail Endpoints
  // -------------------------------------------------------------------------

  /**
   * Get single communication detail by ID.
   */
  getCommunicationById: async (
    communicationId: string
  ): Promise<InstitutionalCommunicationDetail> => {
    const res = await apiClient.get<InstitutionalCommunicationDetail>(
      `/api/v1/communications/${communicationId}`
    )
    return res.data
  },

  /**
   * Get single news article by ID.
   */
  getNewsById: async (newsId: string): Promise<InstitutionalNewsItem> => {
    const res = await apiClient.get<InstitutionalNewsItem>(`/api/v1/news/${newsId}`)
    return res.data
  },

  /**
   * Get single incident detail by ID.
   */
  getIncidentById: async (incidentId: string): Promise<StudentIncidentItem> => {
    const res = await apiClient.get<StudentIncidentItem>(`/api/v1/incidents/${incidentId}`)
    return res.data
  },

  /**
   * List incidents scoped to institutional boundary and teacher assigned groups.
   */
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

  /**
   * Record a new school coexistence incident in Observador del Estudiante.
   */
  createIncident: async (
    payload: StudentIncidentCreateRequest
  ): Promise<StudentIncidentItem> => {
    const res = await apiClient.post<StudentIncidentItem>('/api/v1/incidents', payload)
    return res.data
  },

  /**
   * Modify an existing coexistence incident.
   */
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

  /**
   * Add a pedagogical follow-up note to an incident.
   */
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
