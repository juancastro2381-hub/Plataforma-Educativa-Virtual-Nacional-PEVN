/**
 * PEVN Frontend — Teacher Academic Activities View
 *
 * Full lifecycle management for teacher tasks, workshops, quizzes, and exams:
 * creation, draft editing, publication, closure, and grading shortcut.
 */

import React, { useEffect, useState } from 'react'
import type {
  AcademicActivityCreateRequest,
  AcademicActivityResponse,
  AcademicActivityUpdateRequest,
  ActivityDeliveryType,
  ActivityResourceResponse,
  ActivityResourceType,
  ActivityStatus,
  ActivityType,
  TeacherAssignmentItemResponse,
} from '@/types/teacher'
import { teacherApi } from '@/services/teacher'
import { Button } from '@/components/ui/Button'
import { TeacherSubmissionsModal } from '@/components/teacher/TeacherSubmissionsModal'

interface Props {
  activities: AcademicActivityResponse[]
  assignments: TeacherAssignmentItemResponse[]
  loading: boolean
  onRefresh: () => Promise<void>
  onSelectActivityForGrading: (activityId: string) => void
  initialGroupId?: string
  initialStatus?: string
}

export const TeacherActivitiesView: React.FC<Props> = ({
  activities,
  assignments,
  loading,
  onRefresh,
  onSelectActivityForGrading,
  initialGroupId,
  initialStatus,
}) => {
  // Filters
  const [filterGroup, setFilterGroup] = useState<string>(initialGroupId || '')
  const [filterStatus, setFilterStatus] = useState<string>(initialStatus || '')

  useEffect(() => {
    if (initialGroupId) {
      setFilterGroup(initialGroupId)
    }
  }, [initialGroupId])

  useEffect(() => {
    if (initialStatus) {
      setFilterStatus(initialStatus)
    }
  }, [initialStatus])

  // Create modal state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string>('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [activityType, setActivityType] = useState<ActivityType>('TASK')
  const [deliveryType, setDeliveryType] = useState<ActivityDeliveryType>('FILE')
  const [dueDate, setDueDate] = useState('')
  const [maxScore, setMaxScore] = useState<number>(5.0)
  const [instructions, setInstructions] = useState('')
  const [resourceUrl, setResourceUrl] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [formSuccess, setFormSuccess] = useState<string | null>(null)

  // Edit DRAFT modal state
  const [editingActivity, setEditingActivity] = useState<AcademicActivityResponse | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editActivityType, setEditActivityType] = useState<ActivityType>('TASK')
  const [editDeliveryType, setEditDeliveryType] = useState<ActivityDeliveryType>('FILE')
  const [editDueDate, setEditDueDate] = useState('')
  const [editMaxScore, setEditMaxScore] = useState<number>(5.0)
  const [editInstructions, setEditInstructions] = useState('')
  const [editResourceUrl, setEditResourceUrl] = useState('')
  const [isSavingEdit, setIsSavingEdit] = useState(false)
  const [editFormError, setEditFormError] = useState<string | null>(null)
  const [editFormSuccess, setEditFormSuccess] = useState<string | null>(null)

  // Submissions review modal state
  const [reviewingSubmissionsActivity, setReviewingSubmissionsActivity] = useState<AcademicActivityResponse | null>(null)

  const handleOpenEditModal = (act: AcademicActivityResponse) => {
    if (act.status !== 'DRAFT') return
    setEditingActivity(act)
    setEditTitle(act.title)
    setEditDescription(act.description || '')
    setEditActivityType(act.activity_type)
    setEditDeliveryType(act.delivery_type || 'FILE')
    setEditDueDate(act.due_date ? new Date(act.due_date).toISOString().slice(0, 16) : '')
    setEditMaxScore(typeof act.max_score === 'number' ? act.max_score : parseFloat(String(act.max_score)) || 5.0)
    setEditInstructions(act.instructions || '')
    setEditResourceUrl(act.resource_url || '')
    setEditFormError(null)
    setEditFormSuccess(null)
  }

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingActivity) return
    setEditFormError(null)
    setEditFormSuccess(null)

    if (!editTitle.trim()) {
      setEditFormError('El título de la actividad es obligatorio.')
      return
    }

    setIsSavingEdit(true)
    try {
      const payload: AcademicActivityUpdateRequest = {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
        activity_type: editActivityType,
        delivery_type: editDeliveryType,
        due_date: editDueDate ? new Date(editDueDate).toISOString() : null,
        max_score: editMaxScore,
        instructions: editInstructions.trim() || null,
        resource_url: editResourceUrl.trim() || null,
      }

      await teacherApi.updateActivity(editingActivity.id, payload)
      setEditFormSuccess('¡Actividad en borrador actualizada exitosamente!')
      await onRefresh()
      setTimeout(() => {
        setEditingActivity(null)
      }, 1000)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al actualizar actividad.'
      setEditFormError(msg)
    } finally {
      setIsSavingEdit(false)
    }
  }

  // Details modal state
  const [selectedActivity, setSelectedActivity] = useState<AcademicActivityResponse | null>(null)

  // Resources Manager Modal State (B3-H11)
  const [managingResourcesActivity, setManagingResourcesActivity] = useState<AcademicActivityResponse | null>(null)
  const [activityResources, setActivityResources] = useState<ActivityResourceResponse[]>([])
  const [loadingResources, setLoadingResources] = useState(false)
  const [resourceType, setResourceType] = useState<ActivityResourceType>('FILE')
  const [resourceTitle, setResourceTitle] = useState('')
  const [resourceDescription, setResourceDescription] = useState('')
  const [resourceUrlInput, setResourceUrlInput] = useState('')
  const [resourceFile, setResourceFile] = useState<File | null>(null)
  const [isSubmittingResource, setIsSubmittingResource] = useState(false)
  const [resourceError, setResourceError] = useState<string | null>(null)
  const [resourceSuccess, setResourceSuccess] = useState<string | null>(null)
  const [downloadingResourceId, setDownloadingResourceId] = useState<string | null>(null)

  const handleOpenResourcesModal = async (act: AcademicActivityResponse) => {
    setManagingResourcesActivity(act)
    setResourceTitle('')
    setResourceDescription('')
    setResourceUrlInput('')
    setResourceFile(null)
    setResourceError(null)
    setResourceSuccess(null)
    setLoadingResources(true)
    try {
      const res = await teacherApi.listActivityResources(act.id)
      setActivityResources(res.items)
    } catch (err: unknown) {
      setResourceError(err instanceof Error ? err.message : 'Error al cargar recursos pedagógicos.')
    } finally {
      setLoadingResources(false)
    }
  }

  const handleCreateResource = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!managingResourcesActivity) return
    setResourceError(null)
    setResourceSuccess(null)

    if (!resourceTitle.trim()) {
      setResourceError('El título del material / recurso es obligatorio.')
      return
    }

    setIsSubmittingResource(true)
    try {
      if (resourceType === 'FILE') {
        if (!resourceFile) {
          setResourceError('Debe seleccionar un archivo para adjuntar.')
          setIsSubmittingResource(false)
          return
        }
        await teacherApi.uploadFileResource(managingResourcesActivity.id, {
          title: resourceTitle.trim(),
          file: resourceFile,
          description: resourceDescription.trim() || null,
        })
      } else {
        if (!resourceUrlInput.trim()) {
          setResourceError('Debe ingresar una URL válida para el recurso.')
          setIsSubmittingResource(false)
          return
        }
        await teacherApi.createUrlResource(managingResourcesActivity.id, {
          title: resourceTitle.trim(),
          url: resourceUrlInput.trim(),
          description: resourceDescription.trim() || null,
        })
      }

      setResourceTitle('')
      setResourceDescription('')
      setResourceUrlInput('')
      setResourceFile(null)
      setResourceSuccess('¡Material pedagógico adjuntado exitosamente!')

      const refreshed = await teacherApi.listActivityResources(managingResourcesActivity.id)
      setActivityResources(refreshed.items)
      await onRefresh()
    } catch (err: unknown) {
      setResourceError(err instanceof Error ? err.message : 'Error al adjuntar material.')
    } finally {
      setIsSubmittingResource(false)
    }
  }

  const handleDeleteResource = async (resourceId: string, resTitle: string) => {
    if (!managingResourcesActivity) return
    if (!window.confirm(`¿Desea eliminar el recurso "${resTitle}"?`)) return
    try {
      await teacherApi.deleteResource(managingResourcesActivity.id, resourceId)
      const refreshed = await teacherApi.listActivityResources(managingResourcesActivity.id)
      setActivityResources(refreshed.items)
      await onRefresh()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Error al eliminar recurso.')
    }
  }

  const handleDownloadResource = async (resourceId: string, fileName: string | null) => {
    if (!managingResourcesActivity) return
    try {
      setDownloadingResourceId(resourceId)
      const { data, filename } = await teacherApi.downloadActivityResource(managingResourcesActivity.id, resourceId)
      const blobUrl = window.URL.createObjectURL(data)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = filename || fileName || 'recurso'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(blobUrl)
      document.body.removeChild(a)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Error al descargar archivo adjunto.')
    } finally {
      setDownloadingResourceId(null)
    }
  }

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
    setDeliveryType('FILE')
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
        delivery_type: deliveryType,
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
            onChange={(e) => { setFilterGroup(e.target.value); }}
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
            onChange={(e) => { setFilterStatus(e.target.value); }}
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
                  <th style={{ padding: '0.75rem 1rem' }}>Título / Tipo / Modalidad</th>
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
                      <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center', marginTop: '0.2rem', flexWrap: 'wrap' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6D28D9', fontWeight: 600 }}>
                          {getTypeLabel(act.activity_type)}
                        </span>
                        <span style={{ fontSize: '0.7rem', color: '#475569', backgroundColor: '#F1F5F9', padding: '0.1rem 0.35rem', borderRadius: '4px', border: '1px solid #E2E8F0' }}>
                          {act.delivery_type === 'TEXT' ? '📝 Solo Texto' : act.delivery_type === 'FILE' ? '📎 Archivo(s)' : '📝+📎 Texto y Archivo'}
                        </span>
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
                          onClick={() => { setSelectedActivity(act); }}
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
                        <button
                          onClick={() => { void handleOpenResourcesModal(act); }}
                          style={{
                            padding: '0.3rem 0.6rem',
                            borderRadius: '6px',
                            border: '1px solid #CBD5E1',
                            backgroundColor: '#F8FAFC',
                            color: '#0F172A',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          📎 Materiales
                        </button>

                        {act.status === 'DRAFT' && (
                          <>
                            <button
                              onClick={() => { handleOpenEditModal(act); }}
                              style={{
                                padding: '0.3rem 0.6rem',
                                borderRadius: '6px',
                                border: '1px solid #CBD5E1',
                                backgroundColor: '#F8FAFC',
                                color: '#1E293B',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                cursor: 'pointer',
                              }}
                            >
                              ✏️ Editar
                            </button>
                            <button
                              onClick={() => { void handlePublish(act); }}
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
                          </>
                        )}

                        {act.status === 'PUBLISHED' && (
                          <>
                            <button
                              onClick={() => { setReviewingSubmissionsActivity(act); }}
                              style={{
                                padding: '0.3rem 0.6rem',
                                borderRadius: '6px',
                                border: '1px solid #C7D2FE',
                                backgroundColor: '#EEF2FF',
                                color: '#4338CA',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                cursor: 'pointer',
                              }}
                            >
                              📥 Entregas ({act.total_submissions})
                            </button>
                            <button
                              onClick={() => { onSelectActivityForGrading(act.id); }}
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
                              onClick={() => { void handleClose(act); }}
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

                        {act.status === 'CLOSED' && (
                          <button
                            onClick={() => { setReviewingSubmissionsActivity(act); }}
                            style={{
                              padding: '0.3rem 0.6rem',
                              borderRadius: '6px',
                              border: '1px solid #C7D2FE',
                              backgroundColor: '#EEF2FF',
                              color: '#4338CA',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              cursor: 'pointer',
                            }}
                          >
                            📥 Entregas ({act.total_submissions})
                          </button>
                        )}

                        {act.status === 'DRAFT' && (
                          <button
                            onClick={() => { void handleDelete(act); }}
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
                onClick={() => { setShowCreateModal(false); }}
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

            <form onSubmit={(e) => { void handleCreateSubmit(e); }}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Asignación Académica (Materia y Grupo): *
                </label>
                <select
                  value={selectedAssignmentId}
                  onChange={(e) => { setSelectedAssignmentId(e.target.value); }}
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
                  onChange={(e) => { setTitle(e.target.value); }}
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
                    onChange={(e) => { setActivityType(e.target.value as ActivityType); }}
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
                    onChange={(e) => { setMaxScore(parseFloat(e.target.value)); }}
                    required
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Modalidad de Entrega del Estudiante: *
                </label>
                <select
                  value={deliveryType}
                  onChange={(e) => { setDeliveryType(e.target.value as ActivityDeliveryType); }}
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
                >
                  <option value="FILE">📎 Archivo(s) adjunto(s) (1 a 3 archivos: PDF, Word, Excel, fotos, etc.)</option>
                  <option value="TEXT">📝 Respuesta solo texto (Directamente en la plataforma)</option>
                  <option value="TEXT_AND_FILE">📝 + 📎 Texto y Archivo(s) (Respuesta escrita con soporte de archivos)</option>
                </select>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Fecha y Hora Límite de Entrega:
                </label>
                <input
                  type="datetime-local"
                  value={dueDate}
                  onChange={(e) => { setDueDate(e.target.value); }}
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
                  onChange={(e) => { setInstructions(e.target.value); }}
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
                  onChange={(e) => { setResourceUrl(e.target.value); }}
                  placeholder="https://ejemplo.edu.co/guia-matematicas.pdf"
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <Button variant="secondary" type="button" onClick={() => { setShowCreateModal(false); }}>
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
                onClick={() => { setSelectedActivity(null); }}
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

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', flexWrap: 'wrap' }}>
              <Button
                variant="secondary"
                onClick={() => {
                  const act = selectedActivity
                  setSelectedActivity(null)
                  void handleOpenResourcesModal(act)
                }}
              >
                📎 Materiales ({selectedActivity.resources?.length || 0})
              </Button>
              {selectedActivity.status === 'DRAFT' && (
                <Button
                  variant="primary"
                  onClick={() => {
                    const actToEdit = selectedActivity
                    setSelectedActivity(null)
                    handleOpenEditModal(actToEdit)
                  }}
                >
                  ✏️ Editar Borrador
                </Button>
              )}
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
              <Button variant="secondary" onClick={() => { setSelectedActivity(null); }}>
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit DRAFT Activity Modal */}
      {editingActivity && (
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
              maxWidth: '680px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '1.5rem',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
                  Editar Actividad Académica (Borrador)
                </h3>
                <div style={{ fontSize: '0.8125rem', color: '#6D28D9', fontWeight: 600, marginTop: '0.2rem' }}>
                  {editingActivity.subject_name} • Grupo {editingActivity.group_name} • {getStatusBadge(editingActivity.status)}
                </div>
              </div>
              <button
                onClick={() => { setEditingActivity(null); }}
                style={{ background: 'transparent', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: '#94A3B8' }}
              >
                ✕
              </button>
            </div>

            {editFormError && (
              <div style={{ backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', color: '#991B1B', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.875rem' }}>
                {editFormError}
              </div>
            )}

            {editFormSuccess && (
              <div style={{ backgroundColor: '#F0FDF4', border: '1px solid #86EFAC', color: '#166534', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.875rem' }}>
                {editFormSuccess}
              </div>
            )}

            <form onSubmit={(e) => { void handleEditSubmit(e); }}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Título de la Actividad: *
                </label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => { setEditTitle(e.target.value); }}
                  placeholder="Ej: Taller Práctico de Leyes de Newton"
                  required
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Descripción Pedagógica:
                </label>
                <textarea
                  rows={2}
                  value={editDescription}
                  onChange={(e) => { setEditDescription(e.target.value); }}
                  placeholder="Breve resumen de la actividad..."
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Tipo de Actividad: *
                  </label>
                  <select
                    value={editActivityType}
                    onChange={(e) => { setEditActivityType(e.target.value as ActivityType); }}
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
                    value={editMaxScore}
                    onChange={(e) => { setEditMaxScore(parseFloat(e.target.value)); }}
                    required
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Modalidad de Entrega del Estudiante: *
                </label>
                <select
                  value={editDeliveryType}
                  onChange={(e) => { setEditDeliveryType(e.target.value as ActivityDeliveryType); }}
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
                >
                  <option value="FILE">📎 Archivo(s) adjunto(s) (1 a 3 archivos: PDF, Word, Excel, fotos, etc.)</option>
                  <option value="TEXT">📝 Respuesta solo texto (Directamente en la plataforma)</option>
                  <option value="TEXT_AND_FILE">📝 + 📎 Texto y Archivo(s) (Respuesta escrita con soporte de archivos)</option>
                </select>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Fecha y Hora Límite de Entrega:
                </label>
                <input
                  type="datetime-local"
                  value={editDueDate}
                  onChange={(e) => { setEditDueDate(e.target.value); }}
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Instrucciones para los Estudiantes:
                </label>
                <textarea
                  rows={3}
                  value={editInstructions}
                  onChange={(e) => { setEditInstructions(e.target.value); }}
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
                  value={editResourceUrl}
                  onChange={(e) => { setEditResourceUrl(e.target.value); }}
                  placeholder="https://ejemplo.edu.co/guia-matematicas.pdf"
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <Button variant="secondary" type="button" onClick={() => { setEditingActivity(null); }}>
                  Cancelar
                </Button>
                <Button variant="primary" type="submit" disabled={isSavingEdit}>
                  {isSavingEdit ? 'Guardando Cambios...' : '💾 Guardar Cambios (Borrador)'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Resources Manager Modal (B3-H11) */}
      {managingResourcesActivity && (
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
            zIndex: 60,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '16px',
              maxWidth: '720px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '1.5rem',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
                  Gestión de Materiales y Recursos Pedagógicos
                </h3>
                <div style={{ fontSize: '0.8125rem', color: '#6D28D9', fontWeight: 600, marginTop: '0.2rem' }}>
                  {managingResourcesActivity.title} • {managingResourcesActivity.subject_name} • Grupo {managingResourcesActivity.group_name}
                </div>
              </div>
              <button
                onClick={() => { setManagingResourcesActivity(null); }}
                style={{ background: 'transparent', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: '#94A3B8' }}
              >
                ✕
              </button>
            </div>

            {resourceError && (
              <div style={{ backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', color: '#991B1B', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.875rem' }}>
                {resourceError}
              </div>
            )}

            {resourceSuccess && (
              <div style={{ backgroundColor: '#F0FDF4', border: '1px solid #86EFAC', color: '#166534', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.875rem' }}>
                {resourceSuccess}
              </div>
            )}

            {/* List of Current Resources */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                Materiales Adjuntos ({activityResources.length})
              </h4>

              {loadingResources ? (
                <div style={{ textAlign: 'center', padding: '1.5rem', color: '#64748B', fontSize: '0.875rem' }}>
                  Cargando materiales...
                </div>
              ) : activityResources.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '1.5rem', color: '#94A3B8', fontSize: '0.875rem', backgroundColor: '#F8FAFC', borderRadius: '8px', border: '1px dashed #CBD5E1' }}>
                  No hay materiales pedagógicos adjuntos para esta actividad. Utilice el formulario inferior para agregar archivos o enlaces.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  {activityResources.map((res) => (
                    <div
                      key={res.id}
                      style={{
                        backgroundColor: '#F8FAFC',
                        border: '1px solid #E2E8F0',
                        borderRadius: '8px',
                        padding: '0.75rem 1rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '0.75rem',
                        flexWrap: 'wrap',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', minWidth: 0, flex: 1 }}>
                        <span style={{ fontSize: '1.25rem' }}>
                          {res.resource_type === 'FILE' ? '📄' : '🔗'}
                        </span>
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontWeight: 700, fontSize: '0.875rem', color: '#0F172A', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {res.title}
                          </div>
                          {res.description && (
                            <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                              {res.description}
                            </div>
                          )}
                          {res.resource_type === 'FILE' && res.file_size_bytes && (
                            <div style={{ fontSize: '0.7rem', color: '#94A3B8' }}>
                              {res.file_name} • {(res.file_size_bytes / 1024 / 1024).toFixed(2)} MB
                            </div>
                          )}
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                        {res.resource_type === 'FILE' ? (
                          <button
                            onClick={() => { void handleDownloadResource(res.id, res.file_name); }}
                            disabled={downloadingResourceId === res.id}
                            style={{
                              backgroundColor: '#1E40AF',
                              color: '#FFFFFF',
                              border: 'none',
                              padding: '0.35rem 0.75rem',
                              borderRadius: '6px',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              cursor: downloadingResourceId === res.id ? 'not-allowed' : 'pointer',
                            }}
                          >
                            {downloadingResourceId === res.id ? 'Descargando...' : '⬇ Descargar'}
                          </button>
                        ) : res.url ? (
                          <a
                            href={res.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              backgroundColor: '#059669',
                              color: '#FFFFFF',
                              textDecoration: 'none',
                              padding: '0.35rem 0.75rem',
                              borderRadius: '6px',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                            }}
                          >
                            ↗ Abrir
                          </a>
                        ) : null}

                        <button
                          onClick={() => { void handleDeleteResource(res.id, res.title); }}
                          style={{
                            backgroundColor: '#FEE2E2',
                            color: '#991B1B',
                            border: '1px solid #FCA5A5',
                            padding: '0.35rem 0.6rem',
                            borderRadius: '6px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            cursor: 'pointer',
                          }}
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Add New Resource Form */}
            <div style={{ backgroundColor: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '12px', padding: '1.25rem' }}>
              <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                + Adjuntar Nuevo Material Pedagógico
              </h4>

              {/* Type Switcher */}
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                <button
                  type="button"
                  onClick={() => { setResourceType('FILE'); }}
                  style={{
                    flex: 1,
                    padding: '0.5rem',
                    borderRadius: '8px',
                    border: resourceType === 'FILE' ? '2px solid #2563EB' : '1px solid #CBD5E1',
                    backgroundColor: resourceType === 'FILE' ? '#EFF6FF' : '#FFFFFF',
                    color: resourceType === 'FILE' ? '#1D4ED8' : '#475569',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  📄 Subir Archivo (Guía, PDF, Taller)
                </button>
                <button
                  type="button"
                  onClick={() => { setResourceType('URL'); }}
                  style={{
                    flex: 1,
                    padding: '0.5rem',
                    borderRadius: '8px',
                    border: resourceType === 'URL' ? '2px solid #2563EB' : '1px solid #CBD5E1',
                    backgroundColor: resourceType === 'URL' ? '#EFF6FF' : '#FFFFFF',
                    color: resourceType === 'URL' ? '#1D4ED8' : '#475569',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  🔗 Enlace Web (URL Externa)
                </button>
              </div>

              <form onSubmit={(e) => { void handleCreateResource(e); }}>
                <div style={{ marginBottom: '0.75rem' }}>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Título / Nombre del Recurso: *
                  </label>
                  <input
                    type="text"
                    value={resourceTitle}
                    onChange={(e) => { setResourceTitle(e.target.value); }}
                    placeholder={resourceType === 'FILE' ? 'Ej: Guía de Ejercicios N° 3' : 'Ej: Video Explicativo en YouTube'}
                    required
                    style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', fontSize: '0.875rem' }}
                  />
                </div>

                <div style={{ marginBottom: '0.75rem' }}>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Descripción / Observaciones (Opcional):
                  </label>
                  <input
                    type="text"
                    value={resourceDescription}
                    onChange={(e) => { setResourceDescription(e.target.value); }}
                    placeholder="Instrucciones breves sobre cómo usar este material..."
                    style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', fontSize: '0.875rem' }}
                  />
                </div>

                {resourceType === 'FILE' ? (
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                      Seleccionar Archivo (Máx. 20 MB): *
                    </label>
                    <input
                      type="file"
                      accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.odt,.ods,.odp,.txt,.rtf,.csv,.zip,.rar,.tar,.gz,.7z,.jpg,.jpeg,.png,.gif,.webp,.svg,.mp3,.wav,.ogg,.mp4,.webm,.ogv"
                      onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          setResourceFile(e.target.files[0])
                        } else {
                          setResourceFile(null)
                        }
                      }}
                      required
                      style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid #CBD5E1', backgroundColor: '#FFFFFF', boxSizing: 'border-box', fontSize: '0.875rem' }}
                    />
                    <div style={{ fontSize: '0.725rem', color: '#64748B', marginTop: '0.25rem' }}>
                      Formatos permitidos: PDF, Office (Word, Excel, PowerPoint), Imágenes, Archivos Comprimidos (.zip), Audio y Video.
                    </div>
                  </div>
                ) : (
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                      URL del Recurso: *
                    </label>
                    <input
                      type="url"
                      value={resourceUrlInput}
                      onChange={(e) => { setResourceUrlInput(e.target.value); }}
                      placeholder="https://ejemplo.edu.co/recurso"
                      required
                      style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', fontSize: '0.875rem' }}
                    />
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                  <Button variant="primary" type="submit" disabled={isSubmittingResource}>
                    {isSubmittingResource ? 'Adjuntando...' : '➕ Adjuntar Recurso'}
                  </Button>
                </div>
              </form>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.25rem' }}>
              <Button variant="secondary" onClick={() => { setManagingResourcesActivity(null); }}>
                Cerrar Ventana
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Submissions Review Modal (B3-H13) */}
      {reviewingSubmissionsActivity && (
        <TeacherSubmissionsModal
          activityId={reviewingSubmissionsActivity.id}
          activityTitle={reviewingSubmissionsActivity.title}
          onClose={() => {
            setReviewingSubmissionsActivity(null);
            void onRefresh();
          }}
          onGradingShortcut={(actId) => {
            setReviewingSubmissionsActivity(null);
            onSelectActivityForGrading(actId);
          }}
        />
      )}
    </div>
  )
}
