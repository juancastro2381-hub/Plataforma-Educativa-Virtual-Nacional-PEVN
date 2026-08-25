/**
 * PEVN Frontend — Virtual Classrooms View (Aulas Virtuales)
 *
 * Master management and participation view for synchronous classes,
 * real-time BigBlueButton meeting sessions, attendance logs, and recordings.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { virtualClassroomApi } from '@/services/virtualClassroom'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { Alert } from '@/components/ui/Alert'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useAuth } from '@/hooks/useAuth'
import type {
  ApiError,
  MeetingAttendanceResponse,
  MeetingRecordingResponse,
  VirtualClassroomCreateRequest,
  VirtualClassroomResponse,
  VirtualClassroomStatus,
} from '@/types'

export const VirtualClassroomsView: React.FC = () => {
  const { user } = useAuth()

  const [classrooms, setClassrooms] = useState<VirtualClassroomResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [statusFilter, setStatusFilter] = useState<VirtualClassroomStatus | 'ALL'>('ALL')
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Creation Modal State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [title, setTitle] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [maxParticipants, setMaxParticipants] = useState<number>(50)
  const [isRecordingEnabled, setIsRecordingEnabled] = useState<boolean>(true)

  // Join Action State
  const [joiningId, setJoiningId] = useState<string | null>(null)

  // Detail / Manage Modal State
  const [selectedClassroom, setSelectedClassroom] = useState<VirtualClassroomResponse | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState<boolean>(false)
  const [detailTab, setDetailTab] = useState<'info' | 'attendances' | 'recordings'>('info')
  const [attendances, setAttendances] = useState<MeetingAttendanceResponse[]>([])
  const [recordings, setRecordings] = useState<MeetingRecordingResponse[]>([])
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false)
  const [isSyncingRecordings, setIsSyncingRecordings] = useState<boolean>(false)

  const isStaff = Boolean(
    user?.roles.some(r =>
      ['rector', 'academic_coordinator', 'teacher', 'superadmin'].includes(r)
    )
  )

  const loadClassrooms = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const filter = statusFilter === 'ALL' ? undefined : statusFilter
      const res = await virtualClassroomApi.listVirtualClassrooms({
        status: filter,
        limit: 50,
      })
      setClassrooms(res.items)
      setTotal(res.total)
    } catch (err: unknown) {
      setError(err as ApiError)
    } finally {
      setIsLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    void loadClassrooms()
  }, [loadClassrooms])

  // =========================================================================
  // Actions
  // =========================================================================

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    try {
      const payload: VirtualClassroomCreateRequest = {
        title: title.trim(),
        description: description.trim() || undefined,
        max_participants: maxParticipants,
        is_recording_enabled: isRecordingEnabled,
      }
      await virtualClassroomApi.createVirtualClassroom(payload)
      setSuccessMsg('Aula virtual programada exitosamente.')
      setIsCreateOpen(false)
      setTitle('')
      setDescription('')
      void loadClassrooms()
    } catch (err: unknown) {
      setError(err as ApiError)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleLaunch = async (classroomId: string) => {
    setError(null)
    try {
      await virtualClassroomApi.launchVirtualClassroom(classroomId)
      setSuccessMsg('Sesión iniciada en el servidor.')
      void loadClassrooms()
    } catch (err: unknown) {
      setError(err as ApiError)
    }
  }

  const handleJoin = async (classroom: VirtualClassroomResponse) => {
    setJoiningId(classroom.id)
    setError(null)
    try {
      const res = await virtualClassroomApi.joinVirtualClassroom(classroom.id)
      setSuccessMsg(`Ingresando a "${res.meeting_title}" como ${res.role}...`)
      // Open signed meeting in a new secure window tab
      window.open(res.join_url, '_blank', 'noopener,noreferrer')
      void loadClassrooms()
    } catch (err: unknown) {
      setError(err as ApiError)
    } finally {
      setJoiningId(null)
    }
  }

  const handleEnd = async (classroomId: string) => {
    if (!window.confirm('¿Está seguro de finalizar la clase para todos los participantes?')) {
      return
    }
    setError(null)
    try {
      await virtualClassroomApi.endVirtualClassroom(classroomId)
      setSuccessMsg('Aula virtual finalizada correctamente.')
      void loadClassrooms()
      if (selectedClassroom?.id === classroomId) {
        setIsDetailOpen(false)
      }
    } catch (err: unknown) {
      setError(err as ApiError)
    }
  }

  const openDetail = async (classroom: VirtualClassroomResponse) => {
    setSelectedClassroom(classroom)
    setIsDetailOpen(true)
    setDetailTab('info')
    setIsLoadingDetail(true)
    try {
      const [attRes, recRes] = await Promise.all([
        virtualClassroomApi.listAttendances(classroom.id),
        virtualClassroomApi.listRecordings(classroom.id),
      ])
      setAttendances(attRes.items)
      setRecordings(recRes.items)
    } catch (err: unknown) {
      setError(err as ApiError)
    } finally {
      setIsLoadingDetail(false)
    }
  }

  const handleSyncRecordings = async () => {
    if (!selectedClassroom) return
    setIsSyncingRecordings(true)
    try {
      const res = await virtualClassroomApi.syncRecordings(selectedClassroom.id)
      setRecordings(res.items)
      setSuccessMsg('Grabaciones sincronizadas con el servidor.')
    } catch (err: unknown) {
      setError(err as ApiError)
    } finally {
      setIsSyncingRecordings(false)
    }
  }

  const handleTogglePublish = async (recording: MeetingRecordingResponse) => {
    try {
      const updated = await virtualClassroomApi.publishRecording(
        recording.id,
        !recording.is_published
      )
      setRecordings(prev =>
        prev.map(r => (r.id === updated.id ? updated : r))
      )
      setSuccessMsg(
        updated.is_published
          ? 'Grabación publicada para estudiantes.'
          : 'Grabación ocultada para estudiantes.'
      )
    } catch (err: unknown) {
      setError(err as ApiError)
    }
  }

  const handleDeleteRecording = async (recordingId: string) => {
    if (!window.confirm('¿Está seguro de eliminar esta grabación?')) return
    try {
      await virtualClassroomApi.deleteRecording(recordingId)
      setRecordings(prev => prev.filter(r => r.id !== recordingId))
      setSuccessMsg('Grabación eliminada.')
    } catch (err: unknown) {
      setError(err as ApiError)
    }
  }

  // =========================================================================
  // Helpers & Rendering
  // =========================================================================

  const getStatusBadge = (status: VirtualClassroomStatus) => {
    switch (status) {
      case 'RUNNING':
        return <Badge variant="success">● En Vivo</Badge>
      case 'SCHEDULED':
        return <Badge variant="warning">Programada</Badge>
      case 'ENDED':
        return <Badge variant="neutral">Finalizada</Badge>
      case 'CANCELLED':
        return <Badge variant="danger">Cancelada</Badge>
      default:
        return <Badge variant="neutral">{status}</Badge>
    }
  }

  return (
    <div style={{ padding: '1.5rem', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1.5rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
            Aulas Virtuales y Clases en Vivo
          </h1>
          <p style={{ color: '#64748B', margin: '0.25rem 0 0 0', fontSize: '0.875rem' }}>
            Videoconferencias interactivas, control de asistencia y grabaciones de clase.
          </p>
        </div>

        {isStaff && (
          <Button
            variant="primary"
            onClick={() => {
              setIsCreateOpen(true)
            }}
            aria-label="Programar nueva aula virtual"
          >
            ➕ Programar Clase
          </Button>
        )}
      </div>

      {/* Alerts */}
      {error && (
        <div style={{ marginBottom: '1rem' }}>
          <Alert
            variant="error"
            title="Error en Aulas Virtuales"
            message={'message' in error ? error.message : 'Error inesperado.'}
            onClose={() => {
              setError(null)
            }}
          />
        </div>
      )}

      {successMsg && (
        <div style={{ marginBottom: '1rem' }}>
          <Alert
            variant="success"
            title="Operación Exitosa"
            message={successMsg}
            onClose={() => {
              setSuccessMsg(null)
            }}
          />
        </div>
      )}

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {(['ALL', 'RUNNING', 'SCHEDULED', 'ENDED'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => {
              setStatusFilter(tab)
            }}
            style={{
              padding: '0.4rem 0.85rem',
              borderRadius: '6px',
              fontSize: '0.8125rem',
              fontWeight: 600,
              border: 'none',
              cursor: 'pointer',
              backgroundColor: statusFilter === tab ? '#2563EB' : '#E2E8F0',
              color: statusFilter === tab ? '#FFFFFF' : '#475569',
              transition: 'all 0.15s ease-in-out',
            }}
          >
            {tab === 'ALL'
              ? `Todas (${String(total)})`
              : tab === 'RUNNING'
              ? '● En Vivo'
              : tab === 'SCHEDULED'
              ? 'Programadas'
              : 'Finalizadas'}
          </button>
        ))}
      </div>

      {/* Content List */}
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '4rem 0' }}>
          <LoadingSpinner />
          <p style={{ color: '#64748B', marginTop: '0.75rem', fontSize: '0.875rem' }}>
            Cargando aulas virtuales...
          </p>
        </div>
      ) : classrooms.length === 0 ? (
        <EmptyState
          title="No hay aulas virtuales disponibles"
          description="No se encontraron sesiones programadas o activas con el filtro actual."
          actionLabel={isStaff ? 'Programar Clase' : undefined}
          onAction={
            isStaff
              ? () => {
                  setIsCreateOpen(true)
                }
              : undefined
          }
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: '1.25rem',
          }}
        >
          {classrooms.map(classroom => (
            <Card key={classroom.id}>
              <div style={{ padding: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0F172A', margin: 0, lineHeight: 1.3 }}>
                    {classroom.title}
                  </h3>
                  {getStatusBadge(classroom.status)}
                </div>

                {classroom.description && (
                  <p style={{ color: '#64748B', fontSize: '0.8125rem', marginTop: '0.5rem', marginBottom: '0.75rem' }}>
                    {classroom.description}
                  </p>
                )}

                <div
                  style={{
                    backgroundColor: '#F8FAFC',
                    padding: '0.75rem',
                    borderRadius: '6px',
                    margin: '0.75rem 0',
                    fontSize: '0.75rem',
                    color: '#475569',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.25rem',
                  }}
                >
                  <div>
                    <strong>Capacidad:</strong> Hasta {String(classroom.max_participants)} participantes
                  </div>
                  <div>
                    <strong>Grabación:</strong> {classroom.is_recording_enabled ? 'Activada' : 'Desactivada'}
                  </div>
                  {classroom.actual_start_time && (
                    <div>
                      <strong>Iniciada:</strong> {new Date(classroom.actual_start_time).toLocaleTimeString()}
                    </div>
                  )}
                </div>

                {/* Card Actions */}
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                  {/* Join Button */}
                  {classroom.status !== 'ENDED' && classroom.status !== 'CANCELLED' && (
                    <Button
                      variant="primary"
                      size="sm"
                      isLoading={joiningId === classroom.id}
                      onClick={() => {
                        void handleJoin(classroom)
                      }}
                    >
                      🚀 Ingresar a Clase
                    </Button>
                  )}

                  {/* Launch Button (for staff if scheduled) */}
                  {isStaff && classroom.status === 'SCHEDULED' && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        void handleLaunch(classroom.id)
                      }}
                    >
                      ▶ Iniciar
                    </Button>
                  )}

                  {/* End Button (for staff if running) */}
                  {isStaff && classroom.status === 'RUNNING' && (
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => {
                        void handleEnd(classroom.id)
                      }}
                    >
                      ⏹ Finalizar
                    </Button>
                  )}

                  {/* Details Button */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      void openDetail(classroom)
                    }}
                  >
                    Detalles
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 1. Schedule Classroom Modal */}
      {/* ========================================================================= */}
      <Modal
        isOpen={isCreateOpen}
        title="Programar Nueva Aula Virtual"
        onClose={() => {
          setIsCreateOpen(false)
        }}
      >
        <form
          onSubmit={e => {
            void handleCreate(e)
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label htmlFor="create-title" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Título de la Sesión *
              </label>
              <input
                id="create-title"
                type="text"
                required
                value={title}
                onChange={e => {
                  setTitle(e.target.value)
                }}
                placeholder="Ej. Clase de Matemáticas: Geometría Analítica"
                style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              />
            </div>

            <div>
              <label htmlFor="create-desc" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Descripción o Agenda
              </label>
              <textarea
                id="create-desc"
                rows={3}
                value={description}
                onChange={e => {
                  setDescription(e.target.value)
                }}
                placeholder="Objetivos de aprendizaje o instrucciones de la clase..."
                style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label htmlFor="create-max-participants" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Cupo Máximo
                </label>
                <input
                  id="create-max-participants"
                  type="number"
                  min={1}
                  max={200}
                  value={maxParticipants}
                  onChange={e => {
                    setMaxParticipants(Number(e.target.value))
                  }}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', paddingTop: '1.25rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.8125rem', fontWeight: 600, color: '#334155' }}>
                  <input
                    type="checkbox"
                    checked={isRecordingEnabled}
                    onChange={e => {
                      setIsRecordingEnabled(e.target.checked)
                    }}
                  />
                  Habilitar Grabación
                </label>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setIsCreateOpen(false)
                }}
              >
                Cancelar
              </Button>
              <Button type="submit" variant="primary" isLoading={isSubmitting}>
                Crear Aula
              </Button>
            </div>
          </div>
        </form>
      </Modal>

      {/* ========================================================================= */}
      {/* 2. Classroom Detail & Management Modal */}
      {/* ========================================================================= */}
      {selectedClassroom && (
        <Modal
          isOpen={isDetailOpen}
          title={`Detalles: ${selectedClassroom.title}`}
          onClose={() => {
            setIsDetailOpen(false)
          }}
        >
          <div>
            {/* Sub Tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid #E2E8F0', marginBottom: '1rem' }}>
              {(['info', 'attendances', 'recordings'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => {
                    setDetailTab(tab)
                  }}
                  style={{
                    padding: '0.5rem 1rem',
                    border: 'none',
                    borderBottom: detailTab === tab ? '2px solid #2563EB' : 'none',
                    backgroundColor: 'transparent',
                    color: detailTab === tab ? '#2563EB' : '#64748B',
                    fontWeight: 600,
                    fontSize: '0.8125rem',
                    cursor: 'pointer',
                  }}
                >
                  {tab === 'info'
                    ? 'Información'
                    : tab === 'attendances'
                    ? `Asistencias (${String(attendances.length)})`
                    : `Grabaciones (${String(recordings.length)})`}
                </button>
              ))}
            </div>

            {isLoadingDetail ? (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <LoadingSpinner />
              </div>
            ) : detailTab === 'info' ? (
              <div style={{ fontSize: '0.8125rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div><strong>Estado:</strong> {getStatusBadge(selectedClassroom.status)}</div>
                <div><strong>ID de Sala:</strong> {selectedClassroom.bbb_meeting_id}</div>
                {selectedClassroom.description && (
                  <div><strong>Descripción:</strong> {selectedClassroom.description}</div>
                )}
                <div><strong>Grabación:</strong> {selectedClassroom.is_recording_enabled ? 'Sí' : 'No'}</div>
                <div><strong>Cupo Máximo:</strong> {String(selectedClassroom.max_participants)}</div>
                <div><strong>Fecha de Creación:</strong> {new Date(selectedClassroom.created_at).toLocaleString()}</div>
              </div>
            ) : detailTab === 'attendances' ? (
              <div>
                {attendances.length === 0 ? (
                  <p style={{ color: '#64748B', fontSize: '0.8125rem', textAlign: 'center', padding: '1rem' }}>
                    No hay registros de asistencia aún.
                  </p>
                ) : (
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
                        <th style={{ textAlign: 'left', padding: '0.5rem' }}>Participante</th>
                        <th style={{ textAlign: 'left', padding: '0.5rem' }}>Rol</th>
                        <th style={{ textAlign: 'left', padding: '0.5rem' }}>Ingreso</th>
                        <th style={{ textAlign: 'left', padding: '0.5rem' }}>Duración</th>
                      </tr>
                    </thead>
                    <tbody>
                      {attendances.map(a => (
                        <tr key={a.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                          <td style={{ padding: '0.5rem' }}>{a.user_full_name || a.user_email || a.user_id}</td>
                          <td style={{ padding: '0.5rem' }}>
                            <Badge variant={a.role === 'MODERATOR' ? 'primary' : 'neutral'}>
                              {a.role}
                            </Badge>
                          </td>
                          <td style={{ padding: '0.5rem' }}>{new Date(a.joined_at).toLocaleTimeString()}</td>
                          <td style={{ padding: '0.5rem' }}>
                            {a.duration_seconds !== null && a.duration_seconds !== undefined
                              ? `${String(Math.round(a.duration_seconds / 60))} min`
                              : 'En sesión'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            ) : (
              <div>
                {isStaff && (
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.75rem' }}>
                    <Button
                      variant="secondary"
                      size="sm"
                      isLoading={isSyncingRecordings}
                      onClick={() => {
                        void handleSyncRecordings()
                      }}
                    >
                      🔄 Sincronizar Grabaciones
                    </Button>
                  </div>
                )}

                {recordings.length === 0 ? (
                  <p style={{ color: '#64748B', fontSize: '0.8125rem', textAlign: 'center', padding: '1rem' }}>
                    No hay grabaciones disponibles para esta sesión.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {recordings.map(rec => (
                      <div
                        key={rec.id}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '0.75rem',
                          backgroundColor: '#F8FAFC',
                          borderRadius: '6px',
                          border: '1px solid #E2E8F0',
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 600, fontSize: '0.8125rem' }}>
                            Grabación ({String(Math.round(rec.duration_seconds / 60))} min)
                          </div>
                          <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                            {new Date(rec.recorded_at).toLocaleString()}
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <Badge variant={rec.is_published ? 'success' : 'warning'}>
                            {rec.is_published ? 'Publicada' : 'Oculta'}
                          </Badge>

                          <a
                            href={rec.playback_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              padding: '0.25rem 0.5rem',
                              backgroundColor: '#2563EB',
                              color: '#FFFFFF',
                              borderRadius: '4px',
                              textDecoration: 'none',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                            }}
                          >
                            Ver ▶
                          </a>

                          {isStaff && (
                            <>
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => {
                                  void handleTogglePublish(rec)
                                }}
                              >
                                {rec.is_published ? 'Ocultar' : 'Publicar'}
                              </Button>
                              <Button
                                variant="danger"
                                size="sm"
                                onClick={() => {
                                  void handleDeleteRecording(rec.id)
                                }}
                              >
                                🗑
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  )
}

export default VirtualClassroomsView
