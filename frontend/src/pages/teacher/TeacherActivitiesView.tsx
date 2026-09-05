/**
 * PEVN Frontend — Teacher Academic Activities View
 *
 * Full lifecycle management for teacher tasks, workshops, quizzes, and exams:
 * creation, draft editing, publication, closure, and grading shortcut.
 */

import React, { useState } from 'react'
import type {
  AcademicActivityCreateRequest,
  AcademicActivityResponse,
  ActivityStatus,
  ActivityType,
  TeacherAssignmentItemResponse,
} from '@/types/teacher'
import { teacherApi } from '@/services/teacher'
import { Button } from '@/components/ui/Button'

interface Props {
  activities: AcademicActivityResponse[]
  assignments: TeacherAssignmentItemResponse[]
  loading: boolean
  onRefresh: () => Promise<void>
  onSelectActivityForGrading: (activityId: string) => void
}

export const TeacherActivitiesView: React.FC<Props> = ({
  activities,
  assignments,
  loading,
  onRefresh,
  onSelectActivityForGrading,
}) => {
  // Filters
  const [filterGroup, setFilterGroup] = useState<string>('')
  const [filterStatus, setFilterStatus] = useState<string>('')

  // Create modal state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string>('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [activityType, setActivityType] = useState<ActivityType>('TASK')
  const [dueDate, setDueDate] = useState('')
  const [maxScore, setMaxScore] = useState<number>(5.0)
  const [instructions, setInstructions] = useState('')
  const [resourceUrl, setResourceUrl] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [formSuccess, setFormSuccess] = useState<string | null>(null)

  // Details modal state
  const [selectedActivity, setSelectedActivity] = useState<AcademicActivityResponse | null>(null)

  // Unique groups for filter
  const uniqueGroups = Array.from(
    new Map(assignments.map((a) => [a.group_id, { id: a.group_id, name: a.group_name }])).values()
  )

  const filteredActivities = activities.filter((act) => {
    if (filterGroup && act.group_id !== filterGroup) return false
    if (filterStatus && act.status !== filterStatus) return false
    return true
  })

  const handleOpenCreateModal = () => {
    if (assignments.length > 0) {
      setSelectedAssignmentId(assignments[0].id)
    }
    setTitle('')
    setDescription('')
    setActivityType('TASK')
    setDueDate('')
    setMaxScore(5.0)
    setInstructions('')
    setResourceUrl('')
    setFormError(null)
    setFormSuccess(null)
    setShowCreateModal(true)
  }

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    setFormSuccess(null)

    const assignment = assignments.find((a) => a.id === selectedAssignmentId)
    if (!assignment) {
      setFormError('Debe seleccionar una asignación académica válida.')
      return
    }

    if (!title.trim()) {
      setFormError('El título de la actividad es obligatorio.')
      return
    }

    setIsSubmitting(true)
    try {
      const payload: AcademicActivityCreateRequest = {
        subject_id: assignment.subject_id,
        group_id: assignment.group_id,
        academic_year_id: assignment.academic_year_id,
        title: title.trim(),
        description: description.trim() || null,
        activity_type: activityType,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        max_score: maxScore,
        instructions: instructions.trim() || null,
        resource_url: resourceUrl.trim() || null,
      }

      await teacherApi.createActivity(payload)
      setFormSuccess('¡Actividad académica creada exitosamente en modo BORRADOR!')
      await onRefresh()
      setTimeout(() => {
        setShowCreateModal(false)
      }, 1200)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al registrar actividad.'
      setFormError(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handlePublish = async (act: AcademicActivityResponse) => {
    if (!window.confirm(`¿Desea publicar la actividad "${act.title}"? Estará disponible para los estudiantes y se habilitará la planilla de evaluación.`)) {
      return
    }
    try {
      await teacherApi.publishActivity(act.id)
      await onRefresh()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Error al publicar actividad.')
    }
  }

  const handleClose = async (act: AcademicActivityResponse) => {
    if (!window.confirm(`¿Desea cerrar la actividad "${act.title}"? No se permitirán nuevas entregas de estudiantes.`)) {
      return
    }
    try {
      await teacherApi.closeActivity(act.id)
      await onRefresh()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Error al cerrar actividad.')
    }
  }

  const handleDelete = async (act: AcademicActivityResponse) => {
    if (!window.confirm(`¿Está seguro de eliminar permanentemente la actividad "${act.title}"?`)) {
      return
    }
    try {
      await teacherApi.deleteActivity(act.id)
      await onRefresh()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Error al eliminar actividad.')
    }
  }

  const getStatusBadge = (status: ActivityStatus) => {
    switch (status) {
      case 'DRAFT':
        return <span style={{ backgroundColor: '#F1F5F9', color: '#475569', padding: '0.2rem 0.6rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 700 }}>BORRADOR</span>
      case 'PUBLISHED':
        return <span style={{ backgroundColor: '#DCFCE7', color: '#15803D', padding: '0.2rem 0.6rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 700 }}>PUBLICADA</span>
      case 'CLOSED':
        return <span style={{ backgroundColor: '#FEE2E2', color: '#B91C1C', padding: '0.2rem 0.6rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 700 }}>CERRADA</span>
    }
  }

  const getTypeLabel = (type: ActivityType) => {
    switch (type) {
      case 'TASK': return 'Tarea'
      case 'WORKSHOP': return 'Taller'
      case 'QUIZ': return 'Quiz / Prueba Corta'
      case 'EXAM': return 'Examen / Evaluación'
      case 'PROJECT': return 'Proyecto'
      case 'CLASS_ACTIVITY': return 'Actividad en Clase'
    }
  }

  return (
    <div>
      {/* Header & Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
            Actividades Académicas y Evaluaciones
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
            Gestione tareas, talleres, quizzes y proyectos asociados a sus asignaciones curriculares.
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreateModal}>
          + Nueva Actividad Académica
        </Button>
      </div>

      {/* Filter Bar */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          padding: '1rem 1.25rem',
          border: '1px solid #E2E8F0',
          marginBottom: '1.5rem',
          display: 'flex',
          gap: '1rem',
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.875rem', fontWeight: 600, color: '#475569' }}>Filtrar por Grupo:</label>
          <select
            value={filterGroup}
            onChange={(e) => setFilterGroup(e.target.value)}
            style={{
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid #CBD5E1',
              fontSize: '0.875rem',
              color: '#0F172A',
            }}
          >
            <option value="">Todos los grupos</option>
            {uniqueGroups.map((g) => (
              <option key={g.id} value={g.id}>Grupo {g.name}</option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.875rem', fontWeight: 600, color: '#475569' }}>Estado:</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            style={{
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid #CBD5E1',
              fontSize: '0.875rem',
              color: '#0F172A',
            }}
          >
            <option value="">Todos los estados</option>
            <option value="DRAFT">Borrador</option>
            <option value="PUBLISHED">Publicada</option>
            <option value="CLOSED">Cerrada</option>
          </select>
        </div>
      </div>

      {/* Activities Table */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
          padding: '1.5rem',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
        }}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#64748B' }}>Cargando actividades...</div>
        ) : filteredActivities.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#64748B' }}>
            No se encontraron actividades con los filtros seleccionados.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Título / Tipo</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Asignatura</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Grupo</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Fecha Límite</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Nota Máx</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Estado</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filteredActivities.map((act) => (
                  <tr key={act.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      <div style={{ fontWeight: 700, color: '#0F172A' }}>{act.title}</div>
                      <div style={{ fontSize: '0.75rem', color: '#6D28D9', fontWeight: 600 }}>
                        {getTypeLabel(act.activity_type)}
                      </div>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#1E40AF', fontWeight: 600 }}>
                      {act.subject_name}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 600, color: '#0F172A' }}>
                      {act.group_name}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#475569' }}>
                      {act.due_date ? new Date(act.due_date).toLocaleDateString() : 'Sin fecha límite'}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#0F766E' }}>
                      {act.max_score} pts
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      {getStatusBadge(act.status)}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                        <button
                          onClick={() => setSelectedActivity(act)}
                          style={{
                            padding: '0.3rem 0.6rem',
                            borderRadius: '6px',
                            border: '1px solid #CBD5E1',
                            backgroundColor: '#FFFFFF',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          👁️ Ver
                        </button>

                        {act.status === 'DRAFT' && (
                          <button
                            onClick={() => handlePublish(act)}
                            style={{
                              padding: '0.3rem 0.6rem',
                              borderRadius: '6px',
                              border: '1px solid #86EFAC',
                              backgroundColor: '#F0FDF4',
                              color: '#15803D',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              cursor: 'pointer',
                            }}
                          >
                            🚀 Publicar
                          </button>
                        )}

                        {act.status === 'PUBLISHED' && (
                          <>
                            <button
                              onClick={() => onSelectActivityForGrading(act.id)}
                              style={{
                                padding: '0.3rem 0.6rem',
                                borderRadius: '6px',
                                border: '1px solid #93C5FD',
                                backgroundColor: '#EFF6FF',
                                color: '#1D4ED8',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                cursor: 'pointer',
                              }}
                            >
                              📊 Calificar
                            </button>
                            <button
                              onClick={() => handleClose(act)}
                              style={{
                                padding: '0.3rem 0.6rem',
                                borderRadius: '6px',
                                border: '1px solid #FCA5A5',
                                backgroundColor: '#FEF2F2',
                                color: '#991B1B',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                cursor: 'pointer',
                              }}
                            >
                              🔒 Cerrar
                            </button>
                          </>
                        )}

                        {act.status === 'DRAFT' && (
                          <button
                            onClick={() => handleDelete(act)}
                            style={{
                              padding: '0.3rem 0.6rem',
                              borderRadius: '6px',
                              border: '1px solid #FECDD3',
                              backgroundColor: '#FFF1F2',
                              color: '#BE123C',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            🗑️
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Activity Modal */}
      {showCreateModal && (
        <div
          role="dialog"
          aria-modal="true"
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
              maxWidth: '640px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '1.5rem',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
                Registrar Nueva Actividad Académica
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{ background: 'transparent', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: '#94A3B8' }}
              >
                ✕
              </button>
            </div>

            {formError && (
              <div style={{ backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', color: '#991B1B', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.875rem' }}>
                {formError}
              </div>
            )}

            {formSuccess && (
              <div style={{ backgroundColor: '#F0FDF4', border: '1px solid #86EFAC', color: '#166534', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.875rem' }}>
                {formSuccess}
              </div>
            )}

            <form onSubmit={handleCreateSubmit}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Asignación Académica (Materia y Grupo): *
                </label>
                <select
                  value={selectedAssignmentId}
                  onChange={(e) => setSelectedAssignmentId(e.target.value)}
                  required
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
                >
                  {assignments.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.subject_name} — Grupo {a.group_name} ({a.academic_year_name})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Título de la Actividad / Evaluación: *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ej: Taller 1: Ecuaciones Cuadráticas y Gráficas"
                  required
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Tipo de Actividad: *
                  </label>
                  <select
                    value={activityType}
                    onChange={(e) => setActivityType(e.target.value as ActivityType)}
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                  >
                    <option value="TASK">Tarea</option>
                    <option value="WORKSHOP">Taller</option>
                    <option value="QUIZ">Quiz / Prueba Corta</option>
                    <option value="EXAM">Examen / Evaluación</option>
                    <option value="PROJECT">Proyecto</option>
                    <option value="CLASS_ACTIVITY">Actividad en Clase</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Calificación Máxima: *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="1.0"
                    max="100.0"
                    value={maxScore}
                    onChange={(e) => setMaxScore(parseFloat(e.target.value))}
                    required
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Fecha y Hora Límite de Entrega:
                </label>
                <input
                  type="datetime-local"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Instrucciones para los Estudiantes:
                </label>
                <textarea
                  rows={3}
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="Especifique los pasos, criterios de entrega y materiales requeridos..."
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Enlace de Recurso / Material de Apoyo (URL):
                </label>
                <input
                  type="url"
                  value={resourceUrl}
                  onChange={(e) => setResourceUrl(e.target.value)}
                  placeholder="https://ejemplo.edu.co/guia-matematicas.pdf"
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <Button variant="secondary" type="button" onClick={() => setShowCreateModal(false)}>
                  Cancelar
                </Button>
                <Button variant="primary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Guardando...' : '💾 Guardar Actividad (Borrador)'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Activity Details Modal */}
      {selectedActivity && (
        <div
          role="dialog"
          aria-modal="true"
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
              maxWidth: '600px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '1.5rem',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
                  {selectedActivity.title}
                </h3>
                <div style={{ fontSize: '0.8125rem', color: '#6D28D9', fontWeight: 600, marginTop: '0.2rem' }}>
                  {getTypeLabel(selectedActivity.activity_type)} • {selectedActivity.subject_name} • Grupo {selectedActivity.group_name}
                </div>
              </div>
              <button
                onClick={() => setSelectedActivity(null)}
                style={{ background: 'transparent', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: '#94A3B8' }}
              >
                ✕
              </button>
            </div>

            <div style={{ backgroundColor: '#F8FAFC', borderRadius: '8px', padding: '1rem', marginBottom: '1rem', fontSize: '0.875rem' }}>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Estado:</strong> {getStatusBadge(selectedActivity.status)}
              </div>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Puntaje Máximo:</strong> {selectedActivity.max_score} puntos
              </div>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Fecha Límite:</strong> {selectedActivity.due_date ? new Date(selectedActivity.due_date).toLocaleString() : 'Sin fecha límite'}
              </div>
              {selectedActivity.instructions && (
                <div style={{ marginTop: '0.75rem' }}>
                  <strong>Instrucciones:</strong>
                  <p style={{ margin: '0.25rem 0 0 0', whiteSpace: 'pre-wrap', color: '#334155' }}>
                    {selectedActivity.instructions}
                  </p>
                </div>
              )}
              {selectedActivity.resource_url && (
                <div style={{ marginTop: '0.75rem' }}>
                  <strong>Material de Apoyo:</strong>{' '}
                  <a href={selectedActivity.resource_url} target="_blank" rel="noreferrer" style={{ color: '#2563EB' }}>
                    {selectedActivity.resource_url}
                  </a>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              {selectedActivity.status === 'PUBLISHED' && (
                <Button
                  variant="primary"
                  onClick={() => {
                    const id = selectedActivity.id
                    setSelectedActivity(null)
                    onSelectActivityForGrading(id)
                  }}
                >
                  📊 Abrir Planilla de Calificaciones
                </Button>
              )}
              <Button variant="secondary" onClick={() => setSelectedActivity(null)}>
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
