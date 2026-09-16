/**
 * PEVN Frontend — Teacher Coexistence & Observador del Estudiante View (Phase 15 / B1)
 *
 * Provides teacher interface for Colombian Ley 1620 de 2013:
 * - Query incidents for students in teacher's authorized groups
 * - Filter by group, student, situation type, and lifecycle status
 * - Register new coexistence situations with pedagogical measures and family visibility flags
 * - Consult full incident details, restorative commitments, and chronological follow-ups
 * - Add pedagogical follow-up encounters (formal closure reserved to directive roles)
 */

import React, { useEffect, useMemo, useState } from 'react'
import type { TeacherGroupItemResponse } from '@/types/teacher'
import type {
  CoexistenceSituationType,
  IncidentFollowUpItem,
  IncidentStatus,
  StudentIncidentCreateRequest,
  StudentIncidentItem,
} from '@/types/communication'
import { communicationApi } from '@/services/communication'
import { teacherApi } from '@/services/teacher'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

interface Props {
  groups: TeacherGroupItemResponse[]
  initialGroupId?: string | null
  teacherName?: string
}

interface StudentOption {
  id: string
  name: string
  document: string
  groupId: string
}

export const TeacherIncidentsView: React.FC<Props> = ({
  groups,
  initialGroupId = null,
  teacherName,
}) => {
  // Master list and loading states
  const [incidents, setIncidents] = useState<StudentIncidentItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [selectedGroupId, setSelectedGroupId] = useState<string>(initialGroupId || '')
  const [selectedStudentId, setSelectedStudentId] = useState<string>('')
  const [selectedSituationType, setSelectedSituationType] = useState<string>('')
  const [selectedStatus, setSelectedStatus] = useState<string>('')

  // Roster caching for student dropdowns: { [groupId]: StudentOption[] }
  const [groupRosters, setGroupRosters] = useState<Record<string, StudentOption[]>>({})
  const [loadingRoster, setLoadingRoster] = useState(false)

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedIncident, setSelectedIncident] = useState<StudentIncidentItem | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // Create incident form fields
  const [formGroupId, setFormGroupId] = useState<string>(initialGroupId || (groups[0]?.group_id || ''))
  const [formStudentId, setFormStudentId] = useState<string>('')
  const [formSituationType, setFormSituationType] = useState<CoexistenceSituationType>('TIPO_I')
  const [formIncidentDate, setFormIncidentDate] = useState<string>(
    new Date().toISOString().slice(0, 16)
  )
  const [formLocation, setFormLocation] = useState<string>('')
  const [formDescription, setFormDescription] = useState<string>('')
  const [formStudentVersion, setFormStudentVersion] = useState<string>('')
  const [formPedagogicalMeasures, setFormPedagogicalMeasures] = useState<string>('')
  const [formCommitments, setFormCommitments] = useState<string>('')
  const [formVisibleToStudent, setFormVisibleToStudent] = useState<boolean>(true)
  const [formVisibleToGuardian, setFormVisibleToGuardian] = useState<boolean>(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [formSuccess, setFormSuccess] = useState<string | null>(null)

  // Follow-up form inside detail modal
  const [followUpNotes, setFollowUpNotes] = useState('')
  const [isAddingFollowUp, setIsAddingFollowUp] = useState(false)
  const [followUpError, setFollowUpError] = useState<string | null>(null)

  // Load students for a specific group if not already cached
  const loadRosterForGroup = async (groupId: string): Promise<StudentOption[]> => {
    if (groupRosters[groupId]) {
      return groupRosters[groupId]
    }
    try {
      setLoadingRoster(true)
      const data = await teacherApi.getGroupRoster(groupId)
      const mapped: StudentOption[] = (data.students || []).map((st) => ({
        id: st.student_id,
        name: `${st.first_name} ${st.last_name}`.trim(),
        document: st.document_number,
        groupId: groupId,
      }))
      setGroupRosters((prev) => ({ ...prev, [groupId]: mapped }))
      return mapped
    } catch {
      return []
    } finally {
      setLoadingRoster(false)
    }
  }

  // Pre-load rosters for active groups
  useEffect(() => {
    if (groups.length > 0) {
      const targetGroup = formGroupId || groups[0].group_id
      void loadRosterForGroup(targetGroup)
    }
  }, [groups, formGroupId])

  // When form group changes, load its students and select first if needed
  const handleFormGroupChange = async (newGroupId: string) => {
    setFormGroupId(newGroupId)
    setFormStudentId('')
    const students = await loadRosterForGroup(newGroupId)
    if (students.length > 0) {
      setFormStudentId(students[0].id)
    }
  }

  // When filter group changes, load students for filter dropdown
  useEffect(() => {
    if (selectedGroupId) {
      void loadRosterForGroup(selectedGroupId)
    }
  }, [selectedGroupId])

  // Available students for filter dropdown
  const filterStudentsList = useMemo(() => {
    if (selectedGroupId && groupRosters[selectedGroupId]) {
      return groupRosters[selectedGroupId]
    }
    // Combine all cached students
    const all = Object.values(groupRosters).flat()
    const uniqueMap = new Map<string, StudentOption>()
    for (const s of all) {
      uniqueMap.set(s.id, s)
    }
    return Array.from(uniqueMap.values())
  }, [selectedGroupId, groupRosters])

  // Available students for create form
  const formStudentsList = useMemo(() => {
    return groupRosters[formGroupId] || []
  }, [formGroupId, groupRosters])

  // Fetch incidents list from backend
  const fetchIncidents = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: {
        student_id?: string
        situation_type?: CoexistenceSituationType
        status?: IncidentStatus
      } = {}

      if (selectedStudentId) {
        params.student_id = selectedStudentId
      }
      if (selectedSituationType) {
        params.situation_type = selectedSituationType as CoexistenceSituationType
      }
      if (selectedStatus) {
        params.status = selectedStatus as IncidentStatus
      }

      const res = await communicationApi.getIncidents(params)
      setIncidents(res.items || [])
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Error al consultar las situaciones de convivencia del observador.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchIncidents()
  }, [selectedStudentId, selectedSituationType, selectedStatus])

  // Filter incidents locally by group if selectedGroupId is present
  const filteredIncidents = useMemo(() => {
    if (!selectedGroupId) {
      return incidents
    }
    // Filter by matching students in the selected group's roster
    const rosterStudentIds = new Set((groupRosters[selectedGroupId] || []).map((s) => s.id))
    if (rosterStudentIds.size === 0) {
      return incidents
    }
    return incidents.filter((inc) => rosterStudentIds.has(inc.student_id))
  }, [incidents, selectedGroupId, groupRosters])

  // Reset all filters
  const handleResetFilters = () => {
    setSelectedGroupId('')
    setSelectedStudentId('')
    setSelectedSituationType('')
    setSelectedStatus('')
  }

  // Open Create Modal
  const handleOpenCreateModal = async () => {
    setFormError(null)
    setFormSuccess(null)
    const targetGroup = formGroupId || groups[0]?.group_id || ''
    setFormGroupId(targetGroup)
    if (targetGroup) {
      const students = await loadRosterForGroup(targetGroup)
      if (students.length > 0) {
        setFormStudentId(students[0].id)
      }
    }
    setFormSituationType('TIPO_I')
    setFormIncidentDate(new Date().toISOString().slice(0, 16))
    setFormLocation('')
    setFormDescription('')
    setFormStudentVersion('')
    setFormPedagogicalMeasures('')
    setFormCommitments('')
    setFormVisibleToStudent(true)
    setFormVisibleToGuardian(true)
    setShowCreateModal(true)
  }

  // Submit Create Incident
  const handleSubmitCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    setFormSuccess(null)

    if (!formStudentId) {
      setFormError('Debe seleccionar un estudiante matriculado.')
      return
    }
    if (!formDescription.trim() || formDescription.trim().length < 5) {
      setFormError('La descripción de los hechos debe tener al menos 5 caracteres.')
      return
    }
    if (!formPedagogicalMeasures.trim() || formPedagogicalMeasures.trim().length < 3) {
      setFormError('Las medidas formativas o pedagógicas son obligatorias (mínimo 3 caracteres).')
      return
    }

    setIsSubmitting(true)
    try {
      const payload: StudentIncidentCreateRequest = {
        student_id: formStudentId,
        situation_type: formSituationType,
        incident_date: formIncidentDate ? new Date(formIncidentDate).toISOString() : null,
        location: formLocation.trim() || null,
        description: formDescription.trim(),
        student_version: formStudentVersion.trim() || null,
        pedagogical_measures: formPedagogicalMeasures.trim(),
        commitments: formCommitments.trim() || null,
        is_visible_to_student: formVisibleToStudent,
        is_visible_to_guardian: formVisibleToGuardian,
      }

      await communicationApi.createIncident(payload)
      setFormSuccess('Situación registrada exitosamente en el Observador del Estudiante.')
      await fetchIncidents()
      setTimeout(() => {
        setShowCreateModal(false)
        setFormSuccess(null)
      }, 1200)
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'No fue posible registrar la situación. Verifique que el estudiante pertenezca a sus grupos asignados.'
      setFormError(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Open Incident Detail
  const handleOpenDetail = async (incident: StudentIncidentItem) => {
    setSelectedIncident(incident)
    setDetailLoading(true)
    setFollowUpNotes('')
    setFollowUpError(null)
    try {
      const detailed = await communicationApi.getIncidentById(incident.id)
      setSelectedIncident(detailed)
    } catch {
      setSelectedIncident(incident)
    } finally {
      setDetailLoading(false)
    }
  }

  // Submit Follow-up Note
  const handleAddFollowUp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedIncident) return
    if (!followUpNotes.trim() || followUpNotes.trim().length < 3) {
      setFollowUpError('La nota de seguimiento debe tener al menos 3 caracteres.')
      return
    }

    setIsAddingFollowUp(true)
    setFollowUpError(null)
    try {
      const newFollowUp: IncidentFollowUpItem = await communicationApi.addFollowUp(
        selectedIncident.id,
        {
          notes: followUpNotes.trim(),
          follow_up_date: new Date().toISOString(),
        }
      )

      setSelectedIncident((prev) => {
        if (!prev) return null
        return {
          ...prev,
          status: prev.status === 'ABIERTO' ? 'EN_SEGUIMIENTO' : prev.status,
          follow_ups: [...(prev.follow_ups || []), newFollowUp],
        }
      })
      setFollowUpNotes('')
      void fetchIncidents()
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Error al registrar la nota de seguimiento pedagógico.'
      setFollowUpError(msg)
    } finally {
      setIsAddingFollowUp(false)
    }
  }

  // Styling helper for Situation Type Badges
  const getSituationBadge = (type: CoexistenceSituationType) => {
    switch (type) {
      case 'TIPO_I':
        return {
          label: 'Tipo I — Pedagógico',
          bg: '#FEF3C7',
          color: '#92400E',
          border: '#FDE68A',
        }
      case 'TIPO_II':
        return {
          label: 'Tipo II — Conflicto / Bullying',
          bg: '#FFEDD5',
          color: '#C2410C',
          border: '#FDBA74',
        }
      case 'TIPO_III':
        return {
          label: 'Tipo III — Grave / Ley 1620',
          bg: '#FEE2E2',
          color: '#B91C1C',
          border: '#FCA5A5',
        }
      case 'OBSERVACION_POSITIVA':
        return {
          label: '⭐ Observación Positiva',
          bg: '#DCFCE7',
          color: '#15803D',
          border: '#86EFAC',
        }
      default:
        return {
          label: type,
          bg: '#F1F5F9',
          color: '#475569',
          border: '#CBD5E1',
        }
    }
  }

  // Styling helper for Incident Status Badges
  const getStatusBadge = (status: IncidentStatus) => {
    switch (status) {
      case 'ABIERTO':
        return {
          label: 'Abierto',
          bg: '#FEF9C3',
          color: '#854D0E',
        }
      case 'EN_SEGUIMIENTO':
        return {
          label: 'En Seguimiento',
          bg: '#DBEAFE',
          color: '#1E40AF',
        }
      case 'CERRADO':
        return {
          label: 'Cerrado / Resuelto',
          bg: '#F1F5F9',
          color: '#475569',
        }
      default:
        return {
          label: status,
          bg: '#F1F5F9',
          color: '#475569',
        }
    }
  }

  return (
    <div>
      {/* Header Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <span style={{ fontSize: '1.5rem' }}>🛡️</span>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
              Observador del Estudiante y Convivencia Escolar
            </h2>
          </div>
          <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0, maxWidth: '750px', lineHeight: 1.5 }}>
            Registro oficial de situaciones convivenciales y formativas conforme a la <strong>Ley 1620 de 2013</strong> y el Decreto 1965 de 2013.
            Consulte anotaciones, registre situaciones formativas y efectúe seguimientos pedagógicos a los estudiantes de su carga académica.
          </p>
        </div>

        <button
          type="button"
          data-testid="btn-new-incident"
          onClick={() => void handleOpenCreateModal()}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.625rem 1.25rem',
            backgroundColor: '#1E3A8A',
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 700,
            fontSize: '0.875rem',
            cursor: 'pointer',
            boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
            transition: 'background-color 150ms',
          }}
        >
          <span>➕</span>
          <span>Registrar Situación</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
          padding: '1.25rem',
          marginBottom: '1.5rem',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.03)',
        }}
      >
        <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#475569', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          🔍 Filtros de Búsqueda Convivencial
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            alignItems: 'flex-end',
          }}
        >
          {/* Group Filter */}
          <div>
            <label
              htmlFor="filter-group"
              style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748B', marginBottom: '0.35rem' }}
            >
              Grupo / Salón
            </label>
            <select
              id="filter-group"
              data-testid="filter-group-select"
              value={selectedGroupId}
              onChange={(e) => {
                setSelectedGroupId(e.target.value)
                setSelectedStudentId('')
              }}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                color: '#1E293B',
              }}
            >
              <option value="">Todos los grupos asignados</option>
              {groups.map((g) => (
                <option key={g.group_id} value={g.group_id}>
                  Grupo {g.group_name} ({g.grade_name || 'N/A'})
                </option>
              ))}
            </select>
          </div>

          {/* Student Filter */}
          <div>
            <label
              htmlFor="filter-student"
              style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748B', marginBottom: '0.35rem' }}
            >
              Estudiante {loadingRoster && ' (cargando...)'}
            </label>
            <select
              id="filter-student"
              data-testid="filter-student-select"
              value={selectedStudentId}
              onChange={(e) => setSelectedStudentId(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                color: '#1E293B',
              }}
            >
              <option value="">Todos los estudiantes</option>
              {filterStudentsList.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} (Doc. {s.document})
                </option>
              ))}
            </select>
          </div>

          {/* Situation Type Filter */}
          <div>
            <label
              htmlFor="filter-type"
              style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748B', marginBottom: '0.35rem' }}
            >
              Tipificación Ley 1620
            </label>
            <select
              id="filter-type"
              data-testid="filter-type-select"
              value={selectedSituationType}
              onChange={(e) => setSelectedSituationType(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                color: '#1E293B',
              }}
            >
              <option value="">Todas las tipificaciones</option>
              <option value="TIPO_I">Tipo I — Situaciones leves / formativas</option>
              <option value="TIPO_II">Tipo II — Acoso escolar / bullying</option>
              <option value="TIPO_III">Tipo III — Delitos / agresión grave</option>
              <option value="OBSERVACION_POSITIVA">Observación Positiva / Mérito</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label
              htmlFor="filter-status"
              style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748B', marginBottom: '0.35rem' }}
            >
              Estado del Caso
            </label>
            <select
              id="filter-status"
              data-testid="filter-status-select"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                color: '#1E293B',
              }}
            >
              <option value="">Todos los estados</option>
              <option value="ABIERTO">Abierto / En Atención</option>
              <option value="EN_SEGUIMIENTO">En Seguimiento</option>
              <option value="CERRADO">Cerrado / Resuelto</option>
            </select>
          </div>

          {/* Reset Filters Button */}
          <div>
            <button
              type="button"
              data-testid="btn-reset-filters"
              onClick={handleResetFilters}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                backgroundColor: '#F8FAFC',
                color: '#475569',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              🔄 Limpiar Filtros
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div
          data-testid="incidents-error-banner"
          style={{
            backgroundColor: '#FEF2F2',
            border: '1px solid #FCA5A5',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1.5rem',
            color: '#991B1B',
            fontSize: '0.875rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>⚠️ {error}</span>
          <button
            type="button"
            onClick={() => void fetchIncidents()}
            style={{
              padding: '0.25rem 0.75rem',
              borderRadius: '6px',
              backgroundColor: '#DC2626',
              color: '#FFFFFF',
              border: 'none',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Reintentar
          </button>
        </div>
      )}

      {/* Content Table / Cards */}
      {loading ? (
        <div data-testid="incidents-loading-state" style={{ textAlign: 'center', padding: '3rem', color: '#64748B' }}>
          <LoadingSpinner size="lg" />
          <p style={{ marginTop: '0.75rem', fontSize: '0.875rem' }}>
            Consultando registros del Observador del Estudiante...
          </p>
        </div>
      ) : filteredIncidents.length === 0 ? (
        <div
          data-testid="incidents-empty-state"
          style={{
            padding: '3.5rem 1.5rem',
            textAlign: 'center',
            backgroundColor: '#F8FAFC',
            borderRadius: '12px',
            border: '2px dashed #CBD5E1',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🛡️</div>
          <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: 800, color: '#1E293B' }}>
            No hay situaciones de convivencia registradas
          </h4>
          <p style={{ margin: '0 auto 1.5rem auto', maxWidth: '520px', fontSize: '0.875rem', color: '#64748B', lineHeight: 1.6 }}>
            {selectedGroupId || selectedStudentId || selectedSituationType || selectedStatus
              ? 'No se encontraron anotaciones que coincidan con los filtros aplicados. Intente restablecer los filtros para visualizar todo el historial.'
              : 'Su registro de Observador del Estudiante se encuentra al día. Puede utilizar el botón superior para registrar una nueva situación cuando sea pertinente.'}
          </p>
          <button
            type="button"
            onClick={() => void handleOpenCreateModal()}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '8px',
              backgroundColor: '#1E3A8A',
              color: '#FFFFFF',
              border: 'none',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: 'pointer',
            }}
          >
            ➕ Registrar Nueva Anotación
          </button>
        </div>
      ) : (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            border: '1px solid #E2E8F0',
            overflow: 'hidden',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.03)',
          }}
        >
          <div style={{ overflowX: 'auto' }}>
            <table
              data-testid="incidents-table"
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                textAlign: 'left',
                fontSize: '0.875rem',
              }}
            >
              <thead>
                <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#475569' }}>Fecha</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#475569' }}>Estudiante</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#475569' }}>Tipificación</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#475569' }}>Hechos / Resumen</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#475569' }}>Registrado por</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#475569' }}>Seguimiento</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#475569' }}>Estado</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#475569', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filteredIncidents.map((incident) => {
                  const typeBadge = getSituationBadge(incident.situation_type)
                  const statusBadge = getStatusBadge(incident.status)
                  const formattedDate = new Date(incident.incident_date).toLocaleDateString('es-CO', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })

                  return (
                    <tr
                      key={incident.id}
                      data-testid={`incident-row-${incident.id}`}
                      style={{
                        borderBottom: '1px solid #F1F5F9',
                        transition: 'background-color 120ms',
                      }}
                    >
                      {/* Date */}
                      <td style={{ padding: '0.875rem 1rem', whiteSpace: 'nowrap', color: '#64748B', fontSize: '0.8125rem' }}>
                        {formattedDate}
                      </td>

                      {/* Student */}
                      <td style={{ padding: '0.875rem 1rem' }}>
                        <div style={{ fontWeight: 700, color: '#0F172A' }}>{incident.student_name}</div>
                        <div style={{ fontSize: '0.75rem', color: '#64748B' }}>Doc: {incident.student_document}</div>
                      </td>

                      {/* Situation Type Badge */}
                      <td style={{ padding: '0.875rem 1rem', whiteSpace: 'nowrap' }}>
                        <span
                          style={{
                            display: 'inline-block',
                            padding: '0.2rem 0.6rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            backgroundColor: typeBadge.bg,
                            color: typeBadge.color,
                            border: `1px solid ${typeBadge.border}`,
                          }}
                        >
                          {typeBadge.label}
                        </span>
                      </td>

                      {/* Description Summary */}
                      <td style={{ padding: '0.875rem 1rem', maxWidth: '300px' }}>
                        <div
                          style={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            color: '#334155',
                          }}
                          title={incident.description}
                        >
                          {incident.description}
                        </div>
                        {incident.location && (
                          <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '0.15rem' }}>
                            📍 {incident.location}
                          </div>
                        )}
                      </td>

                      {/* Reporter */}
                      <td style={{ padding: '0.875rem 1rem', whiteSpace: 'nowrap', color: '#475569', fontSize: '0.8125rem' }}>
                        {incident.reporter_name || 'Docente'}
                      </td>

                      {/* Follow-ups count */}
                      <td style={{ padding: '0.875rem 1rem', whiteSpace: 'nowrap' }}>
                        <span
                          style={{
                            fontSize: '0.75rem',
                            padding: '0.15rem 0.5rem',
                            borderRadius: '6px',
                            backgroundColor: '#F8FAFC',
                            border: '1px solid #E2E8F0',
                            color: '#475569',
                            fontWeight: 600,
                          }}
                        >
                          💬 {(incident.follow_ups || []).length} notas
                        </span>
                      </td>

                      {/* Status Badge */}
                      <td style={{ padding: '0.875rem 1rem', whiteSpace: 'nowrap' }}>
                        <span
                          style={{
                            display: 'inline-block',
                            padding: '0.2rem 0.55rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            backgroundColor: statusBadge.bg,
                            color: statusBadge.color,
                          }}
                        >
                          {statusBadge.label}
                        </span>
                      </td>

                      {/* Actions */}
                      <td style={{ padding: '0.875rem 1rem', textAlign: 'right', whiteSpace: 'nowrap' }}>
                        <button
                          type="button"
                          data-testid={`btn-view-incident-${incident.id}`}
                          onClick={() => void handleOpenDetail(incident)}
                          style={{
                            padding: '0.35rem 0.75rem',
                            borderRadius: '6px',
                            backgroundColor: '#EFF6FF',
                            color: '#1D4ED8',
                            border: '1px solid #BFDBFE',
                            fontWeight: 600,
                            fontSize: '0.75rem',
                            cursor: 'pointer',
                            marginRight: '0.35rem',
                          }}
                        >
                          👁️ Ver Detalle
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <div
            style={{
              padding: '0.75rem 1rem',
              backgroundColor: '#F8FAFC',
              borderTop: '1px solid #E2E8F0',
              fontSize: '0.8125rem',
              color: '#64748B',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span>Total situaciones listadas: <strong>{filteredIncidents.length}</strong></span>
            <span>Ley 1620 de 2013 • Sistema Nacional de Convivencia Escolar</span>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 1: REGISTRAR NUEVA SITUACIÓN                                        */}
      {/* ========================================================================= */}
      {showCreateModal && (
        <div
          role="dialog"
          aria-modal="true"
          data-testid="modal-create-incident"
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.65)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '16px',
              maxWidth: '680px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
              padding: '1.75rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem', borderBottom: '1px solid #E2E8F0', paddingBottom: '0.75rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
                  Registrar Situación en Observador del Estudiante
                </h3>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8125rem', color: '#64748B' }}>
                  Diligencie los hechos objetivos y las medidas pedagógicas conforme al debido proceso.
                </p>
              </div>
              <button
                type="button"
                data-testid="btn-close-create-modal"
                onClick={() => setShowCreateModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.25rem',
                  cursor: 'pointer',
                  color: '#94A3B8',
                }}
              >
                ✕
              </button>
            </div>

            {formError && (
              <div
                data-testid="create-incident-error"
                style={{
                  backgroundColor: '#FEF2F2',
                  border: '1px solid #FCA5A5',
                  borderRadius: '8px',
                  padding: '0.75rem',
                  color: '#991B1B',
                  fontSize: '0.8125rem',
                  marginBottom: '1rem',
                }}
              >
                ⚠️ {formError}
              </div>
            )}

            {formSuccess && (
              <div
                data-testid="create-incident-success"
                style={{
                  backgroundColor: '#F0FDF4',
                  border: '1px solid #86EFAC',
                  borderRadius: '8px',
                  padding: '0.75rem',
                  color: '#166534',
                  fontSize: '0.8125rem',
                  marginBottom: '1rem',
                  fontWeight: 600,
                }}
              >
                ✅ {formSuccess}
              </div>
            )}

            <form onSubmit={handleSubmitCreate}>
              {/* Group & Student Selection */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label htmlFor="form-group-select" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#334155', marginBottom: '0.35rem' }}>
                    Grupo / Salón *
                  </label>
                  <select
                    id="form-group-select"
                    data-testid="form-group-select"
                    value={formGroupId}
                    onChange={(e) => void handleFormGroupChange(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '8px',
                      border: '1px solid #CBD5E1',
                      fontSize: '0.875rem',
                    }}
                  >
                    {groups.map((g) => (
                      <option key={g.group_id} value={g.group_id}>
                        Grupo {g.group_name} ({g.grade_name || 'N/A'})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="form-student-select" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#334155', marginBottom: '0.35rem' }}>
                    Estudiante Matriculado * {loadingRoster && ' (cargando...)'}
                  </label>
                  <select
                    id="form-student-select"
                    data-testid="form-student-select"
                    value={formStudentId}
                    onChange={(e) => setFormStudentId(e.target.value)}
                    required
                    style={{
                      width: '100%',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '8px',
                      border: '1px solid #CBD5E1',
                      fontSize: '0.875rem',
                    }}
                  >
                    {formStudentsList.length === 0 ? (
                      <option value="">No hay estudiantes disponibles en este grupo</option>
                    ) : (
                      formStudentsList.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name} ({s.document})
                        </option>
                      ))
                    )}
                  </select>
                </div>
              </div>

              {/* Tipificación & Date */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label htmlFor="form-situation-type" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#334155', marginBottom: '0.35rem' }}>
                    Tipificación Ley 1620 *
                  </label>
                  <select
                    id="form-situation-type"
                    data-testid="form-situation-type"
                    value={formSituationType}
                    onChange={(e) => setFormSituationType(e.target.value as CoexistenceSituationType)}
                    style={{
                      width: '100%',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '8px',
                      border: '1px solid #CBD5E1',
                      fontSize: '0.875rem',
                    }}
                  >
                    <option value="TIPO_I">Tipo I — Situaciones leves / formativas internas</option>
                    <option value="TIPO_II">Tipo II — Acoso escolar / bullying / agresión sin incapacidad</option>
                    <option value="TIPO_III">Tipo III — Presunto delito / agresión con armas o lesiones</option>
                    <option value="OBSERVACION_POSITIVA">Observación Positiva — Mérito convivencial y liderazgo</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="form-incident-date" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#334155', marginBottom: '0.35rem' }}>
                    Fecha y Hora de los Hechos
                  </label>
                  <input
                    id="form-incident-date"
                    data-testid="form-incident-date"
                    type="datetime-local"
                    value={formIncidentDate}
                    onChange={(e) => setFormIncidentDate(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '8px',
                      border: '1px solid #CBD5E1',
                      fontSize: '0.875rem',
                    }}
                  />
                </div>
              </div>

              {/* Location */}
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="form-location" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#334155', marginBottom: '0.35rem' }}>
                  Lugar del Suceso
                </label>
                <input
                  id="form-location"
                  data-testid="form-location"
                  type="text"
                  placeholder="Ej: Aula 204, Patio central, Cafetería, Entorno digital escolar"
                  value={formLocation}
                  onChange={(e) => setFormLocation(e.target.value)}
                  maxLength={150}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #CBD5E1',
                    fontSize: '0.875rem',
                  }}
                />
              </div>

              {/* Description */}
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="form-description" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#334155', marginBottom: '0.35rem' }}>
                  Descripción Objetiva de los Hechos * (Mínimo 5 caracteres)
                </label>
                <textarea
                  id="form-description"
                  data-testid="form-description"
                  rows={3}
                  required
                  placeholder="Relate de forma fáctica, neutral y precisa lo ocurrido sin emitir juicios de valor."
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #CBD5E1',
                    fontSize: '0.875rem',
                    fontFamily: 'inherit',
                  }}
                />
              </div>

              {/* Student Version */}
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="form-student-version" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#334155', marginBottom: '0.35rem' }}>
                  Versión o Descargos del Estudiante (Debido Proceso)
                </label>
                <textarea
                  id="form-student-version"
                  data-testid="form-student-version"
                  rows={2}
                  placeholder="Manifestación libre y respetuosa del estudiante sobre lo acontecido."
                  value={formStudentVersion}
                  onChange={(e) => setFormStudentVersion(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #CBD5E1',
                    fontSize: '0.875rem',
                    fontFamily: 'inherit',
                  }}
                />
              </div>

              {/* Pedagogical Measures */}
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="form-pedagogical-measures" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#334155', marginBottom: '0.35rem' }}>
                  Medidas Pedagógicas / Restaurativas Acordadas *
                </label>
                <textarea
                  id="form-pedagogical-measures"
                  data-testid="form-pedagogical-measures"
                  rows={2}
                  required
                  placeholder="Acciones formativas, diálogo mediado, reflexión pedagógica o restitución comunitaria."
                  value={formPedagogicalMeasures}
                  onChange={(e) => setFormPedagogicalMeasures(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #CBD5E1',
                    fontSize: '0.875rem',
                    fontFamily: 'inherit',
                  }}
                />
              </div>

              {/* Commitments */}
              <div style={{ marginBottom: '1.25rem' }}>
                <label htmlFor="form-commitments" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#334155', marginBottom: '0.35rem' }}>
                  Compromisos Adquiridos por las Partes
                </label>
                <textarea
                  id="form-commitments"
                  data-testid="form-commitments"
                  rows={2}
                  placeholder="Acuerdos convivenciales firmados y compromisos para el restablecimiento de la armonía escolar."
                  value={formCommitments}
                  onChange={(e) => setFormCommitments(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #CBD5E1',
                    fontSize: '0.875rem',
                    fontFamily: 'inherit',
                  }}
                />
              </div>

              {/* Family & Student Visibility Flags (CRITICAL) */}
              <div
                style={{
                  backgroundColor: '#F8FAFC',
                  borderRadius: '10px',
                  padding: '1rem',
                  border: '1px solid #E2E8F0',
                  marginBottom: '1.5rem',
                }}
              >
                <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#1E293B', marginBottom: '0.5rem' }}>
                  🔒 Configuración de Visibilidad en Portales Familiares
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      fontSize: '0.8125rem',
                      color: '#334155',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      data-testid="checkbox-visible-student"
                      checked={formVisibleToStudent}
                      onChange={(e) => setFormVisibleToStudent(e.target.checked)}
                    />
                    <span>Visible para el <strong>Estudiante</strong> en su Portal Estudiantil</span>
                  </label>

                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      fontSize: '0.8125rem',
                      color: '#334155',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      data-testid="checkbox-visible-guardian"
                      checked={formVisibleToGuardian}
                      onChange={(e) => setFormVisibleToGuardian(e.target.checked)}
                    />
                    <span>Visible para el <strong>Acudiente</strong> en su Portal Familiar</span>
                  </label>
                </div>
                <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.75rem', color: '#64748B' }}>
                  * Permite mantener la transparencia y co-responsabilidad formativa de los padres de familia conforme a la Ley de Infancia y Adolescencia.
                </p>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  disabled={isSubmitting}
                  style={{
                    padding: '0.625rem 1.25rem',
                    borderRadius: '8px',
                    border: '1px solid #CBD5E1',
                    backgroundColor: '#FFFFFF',
                    color: '#475569',
                    fontWeight: 600,
                    fontSize: '0.875rem',
                    cursor: 'pointer',
                  }}
                >
                  Cancelar
                </button>

                <button
                  type="submit"
                  data-testid="btn-submit-incident"
                  disabled={isSubmitting || formStudentsList.length === 0}
                  style={{
                    padding: '0.625rem 1.5rem',
                    borderRadius: '8px',
                    border: 'none',
                    backgroundColor: '#1E3A8A',
                    color: '#FFFFFF',
                    fontWeight: 700,
                    fontSize: '0.875rem',
                    cursor: isSubmitting || formStudentsList.length === 0 ? 'not-allowed' : 'pointer',
                    opacity: isSubmitting || formStudentsList.length === 0 ? 0.7 : 1,
                  }}
                >
                  {isSubmitting ? 'Registrando...' : 'Registrar en Observador'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 2: DETALLE DEL INCIDENTE Y SEGUIMIENTOS CRONOLÓGICOS                */}
      {/* ========================================================================= */}
      {selectedIncident && (
        <div
          role="dialog"
          aria-modal="true"
          data-testid="modal-incident-detail"
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.65)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '16px',
              maxWidth: '750px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
              padding: '1.75rem',
            }}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem', borderBottom: '1px solid #E2E8F0', paddingBottom: '0.75rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
                    Expediente Convivencial: {selectedIncident.student_name}
                  </h3>
                  <span
                    style={{
                      padding: '0.2rem 0.6rem',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      backgroundColor: getStatusBadge(selectedIncident.status).bg,
                      color: getStatusBadge(selectedIncident.status).color,
                    }}
                  >
                    {getStatusBadge(selectedIncident.status).label}
                  </span>
                </div>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8125rem', color: '#64748B' }}>
                  Documento: {selectedIncident.student_document} • Fecha de los hechos:{' '}
                  {new Date(selectedIncident.incident_date).toLocaleString('es-CO')}
                </p>
              </div>
              <button
                type="button"
                data-testid="btn-close-detail-modal"
                onClick={() => setSelectedIncident(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.25rem',
                  cursor: 'pointer',
                  color: '#94A3B8',
                }}
              >
                ✕
              </button>
            </div>

            {detailLoading ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#64748B' }}>
                <LoadingSpinner size="md" />
                <p style={{ marginTop: '0.5rem', fontSize: '0.8125rem' }}>Cargando expediente completo...</p>
              </div>
            ) : (
              <div>
                {/* Meta Information Cards */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '0.75rem',
                    marginBottom: '1.25rem',
                  }}
                >
                  <div style={{ backgroundColor: '#F8FAFC', padding: '0.75rem', borderRadius: '8px', border: '1px solid #F1F5F9' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>TIPIFICACIÓN</div>
                    <div style={{ marginTop: '0.25rem' }}>
                      <span
                        style={{
                          padding: '0.15rem 0.5rem',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          backgroundColor: getSituationBadge(selectedIncident.situation_type).bg,
                          color: getSituationBadge(selectedIncident.situation_type).color,
                          border: `1px solid ${getSituationBadge(selectedIncident.situation_type).border}`,
                        }}
                      >
                        {getSituationBadge(selectedIncident.situation_type).label}
                      </span>
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#F8FAFC', padding: '0.75rem', borderRadius: '8px', border: '1px solid #F1F5F9' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>LUGAR REGISTRADO</div>
                    <div style={{ fontSize: '0.875rem', color: '#1E293B', fontWeight: 600, marginTop: '0.25rem' }}>
                      {selectedIncident.location || 'Instalaciones de la Institución'}
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#F8FAFC', padding: '0.75rem', borderRadius: '8px', border: '1px solid #F1F5F9' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>DOCENTE REGISTRADOR</div>
                    <div style={{ fontSize: '0.875rem', color: '#1E293B', fontWeight: 600, marginTop: '0.25rem' }}>
                      {selectedIncident.reporter_name || teacherName || 'Docente'}
                    </div>
                  </div>
                </div>

                {/* Narrative Sections */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
                  <div>
                    <h4 style={{ margin: '0 0 0.35rem 0', fontSize: '0.875rem', fontWeight: 800, color: '#1E293B' }}>
                      1. Hechos Objetivos
                    </h4>
                    <div
                      data-testid="detail-description"
                      style={{
                        backgroundColor: '#F8FAFC',
                        borderRadius: '8px',
                        padding: '0.875rem',
                        fontSize: '0.875rem',
                        color: '#334155',
                        lineHeight: 1.6,
                        border: '1px solid #E2E8F0',
                      }}
                    >
                      {selectedIncident.description}
                    </div>
                  </div>

                  {selectedIncident.student_version && (
                    <div>
                      <h4 style={{ margin: '0 0 0.35rem 0', fontSize: '0.875rem', fontWeight: 800, color: '#1E293B' }}>
                        2. Versión del Estudiante (Descargos)
                      </h4>
                      <div
                        data-testid="detail-student-version"
                        style={{
                          backgroundColor: '#F8FAFC',
                          borderRadius: '8px',
                          padding: '0.875rem',
                          fontSize: '0.875rem',
                          color: '#334155',
                          lineHeight: 1.6,
                          border: '1px solid #E2E8F0',
                          fontStyle: 'italic',
                        }}
                      >
                        "{selectedIncident.student_version}"
                      </div>
                    </div>
                  )}

                  <div>
                    <h4 style={{ margin: '0 0 0.35rem 0', fontSize: '0.875rem', fontWeight: 800, color: '#1E293B' }}>
                      3. Medidas Pedagógicas y Restaurativas
                    </h4>
                    <div
                      data-testid="detail-pedagogical-measures"
                      style={{
                        backgroundColor: '#F8FAFC',
                        borderRadius: '8px',
                        padding: '0.875rem',
                        fontSize: '0.875rem',
                        color: '#334155',
                        lineHeight: 1.6,
                        border: '1px solid #E2E8F0',
                      }}
                    >
                      {selectedIncident.pedagogical_measures}
                    </div>
                  </div>

                  {selectedIncident.commitments && (
                    <div>
                      <h4 style={{ margin: '0 0 0.35rem 0', fontSize: '0.875rem', fontWeight: 800, color: '#1E293B' }}>
                        4. Compromisos Convivenciales
                      </h4>
                      <div
                        data-testid="detail-commitments"
                        style={{
                          backgroundColor: '#F0FDF4',
                          borderRadius: '8px',
                          padding: '0.875rem',
                          fontSize: '0.875rem',
                          color: '#166534',
                          lineHeight: 1.6,
                          border: '1px solid #BBF7D0',
                        }}
                      >
                        {selectedIncident.commitments}
                      </div>
                    </div>
                  )}

                  {/* Visibility Badges */}
                  <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                    <span
                      style={{
                        padding: '0.35rem 0.75rem',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        backgroundColor: selectedIncident.is_visible_to_student ? '#DCFCE7' : '#FEE2E2',
                        color: selectedIncident.is_visible_to_student ? '#166534' : '#991B1B',
                      }}
                    >
                      {selectedIncident.is_visible_to_student ? '👁️ Visible para Estudiante' : '🚫 No visible para Estudiante'}
                    </span>

                    <span
                      style={{
                        padding: '0.35rem 0.75rem',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        backgroundColor: selectedIncident.is_visible_to_guardian ? '#DCFCE7' : '#FEE2E2',
                        color: selectedIncident.is_visible_to_guardian ? '#166534' : '#991B1B',
                      }}
                    >
                      {selectedIncident.is_visible_to_guardian ? '👁️ Visible para Acudiente' : '🚫 No visible para Acudiente'}
                    </span>
                  </div>
                </div>

                {/* Follow-up Timeline Section */}
                <div style={{ borderTop: '2px solid #E2E8F0', paddingTop: '1.25rem', marginBottom: '1.25rem' }}>
                  <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', fontWeight: 800, color: '#0F172A' }}>
                    💬 Historial Cronológico de Seguimientos Pedagógicos
                  </h4>

                  {(selectedIncident.follow_ups || []).length === 0 ? (
                    <div style={{ padding: '1rem', backgroundColor: '#F8FAFC', borderRadius: '8px', fontSize: '0.8125rem', color: '#64748B', textAlign: 'center' }}>
                      No se han registrado notas de seguimiento para esta situación.
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
                      {selectedIncident.follow_ups.map((fu) => (
                        <div
                          key={fu.id}
                          data-testid={`follow-up-item-${fu.id}`}
                          style={{
                            backgroundColor: '#FFFFFF',
                            border: '1px solid #E2E8F0',
                            borderRadius: '8px',
                            padding: '0.875rem',
                            borderLeft: '4px solid #3B82F6',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.75rem', color: '#64748B' }}>
                            <span style={{ fontWeight: 700, color: '#1E40AF' }}>{fu.author_name || 'Docente / Orientador'}</span>
                            <span>{new Date(fu.follow_up_date || fu.created_at).toLocaleString('es-CO')}</span>
                          </div>
                          <div style={{ fontSize: '0.875rem', color: '#1E293B', lineHeight: 1.5 }}>
                            {fu.notes}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Add Follow-up Form (Only if incident is NOT closed) */}
                  {selectedIncident.status !== 'CERRADO' ? (
                    <form onSubmit={handleAddFollowUp} style={{ marginTop: '1rem' }}>
                      {followUpError && (
                        <div
                          style={{
                            backgroundColor: '#FEF2F2',
                            border: '1px solid #FCA5A5',
                            borderRadius: '6px',
                            padding: '0.5rem',
                            fontSize: '0.75rem',
                            color: '#991B1B',
                            marginBottom: '0.5rem',
                          }}
                        >
                          ⚠️ {followUpError}
                        </div>
                      )}

                      <label htmlFor="follow-up-notes" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#334155', marginBottom: '0.35rem' }}>
                        ➕ Agregar Nota de Seguimiento Formativo
                      </label>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <input
                          id="follow-up-notes"
                          data-testid="input-follow-up-notes"
                          type="text"
                          placeholder="Escriba la observación de evolución pedagógica o acuerdo cumplido..."
                          value={followUpNotes}
                          onChange={(e) => setFollowUpNotes(e.target.value)}
                          disabled={isAddingFollowUp}
                          style={{
                            flex: 1,
                            padding: '0.5rem 0.75rem',
                            borderRadius: '8px',
                            border: '1px solid #CBD5E1',
                            fontSize: '0.875rem',
                          }}
                        />
                        <button
                          type="submit"
                          data-testid="btn-submit-follow-up"
                          disabled={isAddingFollowUp || !followUpNotes.trim()}
                          style={{
                            padding: '0.5rem 1rem',
                            borderRadius: '8px',
                            backgroundColor: '#1E3A8A',
                            color: '#FFFFFF',
                            border: 'none',
                            fontWeight: 700,
                            fontSize: '0.8125rem',
                            cursor: isAddingFollowUp || !followUpNotes.trim() ? 'not-allowed' : 'pointer',
                            opacity: isAddingFollowUp || !followUpNotes.trim() ? 0.7 : 1,
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {isAddingFollowUp ? 'Guardando...' : 'Guardar Nota'}
                        </button>
                      </div>
                    </form>
                  ) : (
                    <div
                      style={{
                        padding: '0.75rem',
                        backgroundColor: '#F8FAFC',
                        borderRadius: '8px',
                        border: '1px solid #E2E8F0',
                        fontSize: '0.8125rem',
                        color: '#64748B',
                      }}
                    >
                      🔒 Esta situación se encuentra cerrada formalmente por {selectedIncident.closed_by_name || 'Rectoría / Comité de Convivencia'}. No admite nuevas notas de seguimiento.
                    </div>
                  )}
                </div>

                {/* Normative Notice about Closure Authority (NO CLOSE BUTTON FOR TEACHER) */}
                <div
                  style={{
                    backgroundColor: '#F8FAFC',
                    border: '1px solid #E2E8F0',
                    borderRadius: '8px',
                    padding: '0.75rem',
                    fontSize: '0.75rem',
                    color: '#64748B',
                    lineHeight: 1.5,
                  }}
                >
                  📌 <strong>Disposición Normativa (Ley 1620 / Decreto 1965):</strong> El cierre y resolución formal de situaciones de convivencia escolar está reservado por competencia legal a la Rectoría y al Comité Escolar de Convivencia Institucional. Los docentes registran los hechos y acompañan el seguimiento formativo continuo.
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default TeacherIncidentsView
