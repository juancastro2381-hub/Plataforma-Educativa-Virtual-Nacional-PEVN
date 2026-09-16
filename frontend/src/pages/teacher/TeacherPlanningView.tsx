/**
 * PEVN Frontend — Teacher Curricular Planning View
 *
 * Full management of lesson plans, unit competencies, learning objectives,
 * pedagogical methodologies, evaluation criteria, and educational resources.
 */

import React, { useEffect, useState } from 'react'
import type {
  AcademicPlanCreateRequest,
  AcademicPlanResponse,
  AcademicPlanStatus,
  AcademicPlanUpdateRequest,
  TeacherAssignmentItemResponse,
} from '@/types/teacher'
import { teacherApi } from '@/services/teacher'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

interface Props {
  assignments: TeacherAssignmentItemResponse[]
  initialGroupId?: string
}

export const TeacherPlanningView: React.FC<Props> = ({ assignments, initialGroupId }) => {
  const [plans, setPlans] = useState<AcademicPlanResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [filterGroup, setFilterGroup] = useState<string>(initialGroupId || '')

  useEffect(() => {
    if (initialGroupId) {
      setFilterGroup(initialGroupId)
    }
  }, [initialGroupId])

  // Create Modal
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string>(assignments[0]?.id || '')
  const [unitName, setUnitName] = useState('')
  const [competencies, setCompetencies] = useState('')
  const [learningObjectives, setLearningObjectives] = useState('')
  const [methodology, setMethodology] = useState('')
  const [evaluationCriteria, setEvaluationCriteria] = useState('')
  const [resources, setResources] = useState('')
  const [status, setStatus] = useState<AcademicPlanStatus>('DRAFT')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [formSuccess, setFormSuccess] = useState<string | null>(null)

  // Edit Modal
  const [editingPlan, setEditingPlan] = useState<AcademicPlanResponse | null>(null)
  const [editUnitName, setEditUnitName] = useState('')
  const [editCompetencies, setEditCompetencies] = useState('')
  const [editLearningObjectives, setEditLearningObjectives] = useState('')
  const [editMethodology, setEditMethodology] = useState('')
  const [editEvaluationCriteria, setEditEvaluationCriteria] = useState('')
  const [editResources, setEditResources] = useState('')
  const [editStatus, setEditStatus] = useState<AcademicPlanStatus>('DRAFT')
  const [editStartDate, setEditStartDate] = useState('')
  const [editEndDate, setEditEndDate] = useState('')
  const [isSavingEdit, setIsSavingEdit] = useState(false)
  const [editFormError, setEditFormError] = useState<string | null>(null)
  const [editFormSuccess, setEditFormSuccess] = useState<string | null>(null)

  const handleOpenEditModal = (plan: AcademicPlanResponse) => {
    setEditingPlan(plan)
    setEditUnitName(plan.unit_name)
    setEditCompetencies(plan.competencies || '')
    setEditLearningObjectives(plan.learning_objectives || '')
    setEditMethodology(plan.methodology || '')
    setEditEvaluationCriteria(plan.evaluation_criteria || '')
    setEditResources(plan.resources || '')
    setEditStatus(plan.status)
    setEditStartDate(plan.start_date || '')
    setEditEndDate(plan.end_date || '')
    setEditFormError(null)
    setEditFormSuccess(null)
  }

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingPlan) return
    setEditFormError(null)
    setEditFormSuccess(null)

    if (!editUnitName.trim()) {
      setEditFormError('El nombre de la unidad temática es obligatorio.')
      return
    }

    setIsSavingEdit(true)
    try {
      const payload: AcademicPlanUpdateRequest = {
        unit_name: editUnitName.trim(),
        competencies: editCompetencies.trim() || null,
        learning_objectives: editLearningObjectives.trim() || null,
        methodology: editMethodology.trim() || null,
        evaluation_criteria: editEvaluationCriteria.trim() || null,
        resources: editResources.trim() || null,
        status: editStatus,
        start_date: editStartDate || null,
        end_date: editEndDate || null,
      }

      await teacherApi.updatePlanning(editingPlan.id, payload)
      setEditFormSuccess('¡Planeación curricular actualizada exitosamente!')
      await loadPlans()
      setTimeout(() => {
        setEditingPlan(null)
      }, 1000)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al actualizar la planeación.'
      setEditFormError(msg)
    } finally {
      setIsSavingEdit(false)
    }
  }

  // Details Modal
  const [selectedPlan, setSelectedPlan] = useState<AcademicPlanResponse | null>(null)

  const uniqueGroups = Array.from(
    new Map(assignments.map((a) => [a.group_id, { id: a.group_id, name: a.group_name }])).values()
  )

  const loadPlans = async () => {
    setLoading(true)
    try {
      const data = await teacherApi.listPlanning({
        group_id: filterGroup || undefined,
      })
      setPlans(data.items)
    } catch (err: unknown) {
      console.error('Error loading plans:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadPlans()
  }, [filterGroup])

  const handleOpenCreateModal = () => {
    if (assignments.length > 0) {
      setSelectedAssignmentId(assignments[0].id)
    }
    setUnitName('')
    setCompetencies('')
    setLearningObjectives('')
    setMethodology('')
    setEvaluationCriteria('')
    setResources('')
    setStatus('DRAFT')
    setStartDate('')
    setEndDate('')
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

    if (!unitName.trim()) {
      setFormError('El nombre de la unidad temática es obligatorio.')
      return
    }

    setIsSubmitting(true)
    try {
      const payload: AcademicPlanCreateRequest = {
        subject_id: assignment.subject_id,
        group_id: assignment.group_id,
        academic_year_id: assignment.academic_year_id,
        unit_name: unitName.trim(),
        competencies: competencies.trim() || null,
        learning_objectives: learningObjectives.trim() || null,
        methodology: methodology.trim() || null,
        evaluation_criteria: evaluationCriteria.trim() || null,
        resources: resources.trim() || null,
        status,
        start_date: startDate || null,
        end_date: endDate || null,
      }

      await teacherApi.createPlanning(payload)
      setFormSuccess('¡Planeación curricular registrada exitosamente!')
      await loadPlans()
      setTimeout(() => {
        setShowCreateModal(false)
      }, 1200)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al guardar la planeación.'
      setFormError(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeletePlan = async (plan: AcademicPlanResponse) => {
    if (!window.confirm(`¿Está seguro de eliminar la planeación "${plan.unit_name}"?`)) {
      return
    }
    try {
      await teacherApi.deletePlanning(plan.id)
      await loadPlans()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Error al eliminar planeación.')
    }
  }

  const getStatusBadge = (st: AcademicPlanStatus) => {
    switch (st) {
      case 'DRAFT':
        return <span style={{ backgroundColor: '#F1F5F9', color: '#475569', padding: '0.2rem 0.6rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 700 }}>BORRADOR</span>
      case 'APPROVED':
        return <span style={{ backgroundColor: '#DCFCE7', color: '#15803D', padding: '0.2rem 0.6rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 700 }}>APROBADA</span>
      case 'IN_PROGRESS':
        return <span style={{ backgroundColor: '#EFF6FF', color: '#2563EB', padding: '0.2rem 0.6rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 700 }}>EN EJECUCIÓN</span>
      case 'COMPLETED':
        return <span style={{ backgroundColor: '#F3E8FF', color: '#7E22CE', padding: '0.2rem 0.6rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 700 }}>COMPLETADA</span>
    }
  }

  return (
    <div>
      {/* Header & Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
            Planeación Curricular y Unidades Didácticas
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
            Eructure y documente las competencias, metodologías y criterios de evaluación de sus cursos.
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreateModal}>
          + Nueva Planeación Curricular
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
          alignItems: 'center',
        }}
      >
        <label style={{ fontSize: '0.875rem', fontWeight: 600, color: '#475569' }}>Filtrar por Grupo:</label>
        <select
          value={filterGroup}
          onChange={(e) => setFilterGroup(e.target.value)}
          style={{ padding: '0.4rem 0.75rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
        >
          <option value="">Todos los grupos</option>
          {uniqueGroups.map((g) => (
            <option key={g.id} value={g.id}>Grupo {g.name}</option>
          ))}
        </select>
      </div>

      {/* Plans List */}
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
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <LoadingSpinner />
            <p style={{ marginTop: '0.5rem', color: '#64748B', fontSize: '0.875rem' }}>Cargando planeaciones curriculares...</p>
          </div>
        ) : plans.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#64748B' }}>
            No tiene planeaciones registradas para el criterio seleccionado.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Unidad Temática</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Materia</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Grupo</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Fechas Estimadas</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Estado</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {plans.map((p) => (
                  <tr key={p.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                      {p.unit_name}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#1E40AF', fontWeight: 600 }}>
                      {p.subject_name}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 600, color: '#0F172A' }}>
                      {p.group_name}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#475569', fontSize: '0.8125rem' }}>
                      {p.start_date || 'N/A'} — {p.end_date || 'N/A'}
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      {getStatusBadge(p.status)}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                        <button
                          onClick={() => setSelectedPlan(p)}
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
                          👁️ Ver Detalle
                        </button>
                        <button
                          onClick={() => handleOpenEditModal(p)}
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
                          onClick={() => handleDeletePlan(p)}
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
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Plan Modal */}
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
              maxWidth: '680px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '1.5rem',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
                Registrar Unidad de Planeación Curricular
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
                  Nombre de la Unidad Didáctica / Temática: *
                </label>
                <input
                  type="text"
                  value={unitName}
                  onChange={(e) => setUnitName(e.target.value)}
                  placeholder="Ej: Unidad 2: Cinemática y Leyes de Newton"
                  required
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Fecha de Inicio:
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Fecha de Finalización:
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Competencias a Desarrollar (MEN):
                </label>
                <textarea
                  rows={2}
                  value={competencies}
                  onChange={(e) => setCompetencies(e.target.value)}
                  placeholder="Formulación de hipótesis, modelamiento matemático y razonamiento cuantitativo..."
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Objetivos de Aprendizaje (DBA):
                </label>
                <textarea
                  rows={2}
                  value={learningObjectives}
                  onChange={(e) => setLearningObjectives(e.target.value)}
                  placeholder="El estudiante interpreta situaciones físicas aplicando principios de dinámica..."
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Metodología Pedagógica:
                </label>
                <textarea
                  rows={2}
                  value={methodology}
                  onChange={(e) => setMethodology(e.target.value)}
                  placeholder="Aprendizaje basado en problemas (ABP), laboratorios virtuales y talleres colaborativos..."
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Criterios e Instrumentos de Evaluación:
                </label>
                <textarea
                  rows={2}
                  value={evaluationCriteria}
                  onChange={(e) => setEvaluationCriteria(e.target.value)}
                  placeholder="Rúbrica de evaluación continua, quices formativos y sustentación final..."
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <Button variant="secondary" type="button" onClick={() => setShowCreateModal(false)}>
                  Cancelar
                </Button>
                <Button variant="primary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Guardando...' : '💾 Guardar Planeación'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Plan Details Modal */}
      {selectedPlan && (
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
                  {selectedPlan.unit_name}
                </h3>
                <div style={{ fontSize: '0.8125rem', color: '#1E40AF', fontWeight: 600, marginTop: '0.2rem' }}>
                  {selectedPlan.subject_name} • Grupo {selectedPlan.group_name} • {selectedPlan.academic_year_name}
                </div>
              </div>
              <button
                onClick={() => setSelectedPlan(null)}
                style={{ background: 'transparent', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: '#94A3B8' }}
              >
                ✕
              </button>
            </div>

            <div style={{ backgroundColor: '#F8FAFC', borderRadius: '8px', padding: '1rem', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Estado:</strong> {getStatusBadge(selectedPlan.status)}
              </div>
              <div style={{ marginBottom: '0.75rem' }}>
                <strong>Periodo Estimado:</strong> {selectedPlan.start_date || 'Sin definir'} al {selectedPlan.end_date || 'Sin definir'}
              </div>

              {selectedPlan.competencies && (
                <div style={{ marginTop: '0.75rem' }}>
                  <strong>Competencias:</strong>
                  <p style={{ margin: '0.25rem 0 0 0', color: '#334155', whiteSpace: 'pre-wrap' }}>
                    {selectedPlan.competencies}
                  </p>
                </div>
              )}

              {selectedPlan.learning_objectives && (
                <div style={{ marginTop: '0.75rem' }}>
                  <strong>Objetivos de Aprendizaje:</strong>
                  <p style={{ margin: '0.25rem 0 0 0', color: '#334155', whiteSpace: 'pre-wrap' }}>
                    {selectedPlan.learning_objectives}
                  </p>
                </div>
              )}

              {selectedPlan.methodology && (
                <div style={{ marginTop: '0.75rem' }}>
                  <strong>Metodología Pedagógica:</strong>
                  <p style={{ margin: '0.25rem 0 0 0', color: '#334155', whiteSpace: 'pre-wrap' }}>
                    {selectedPlan.methodology}
                  </p>
                </div>
              )}

              {selectedPlan.evaluation_criteria && (
                <div style={{ marginTop: '0.75rem' }}>
                  <strong>Criterios de Evaluación:</strong>
                  <p style={{ margin: '0.25rem 0 0 0', color: '#334155', whiteSpace: 'pre-wrap' }}>
                    {selectedPlan.evaluation_criteria}
                  </p>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button
                variant="primary"
                onClick={() => {
                  const planToEdit = selectedPlan
                  setSelectedPlan(null)
                  handleOpenEditModal(planToEdit)
                }}
              >
                ✏️ Editar Planeación
              </Button>
              <Button variant="secondary" onClick={() => setSelectedPlan(null)}>
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Plan Modal */}
      {editingPlan && (
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
                  Editar Unidad de Planeación Curricular
                </h3>
                <div style={{ fontSize: '0.8125rem', color: '#1E40AF', fontWeight: 600, marginTop: '0.2rem' }}>
                  {editingPlan.subject_name} • Grupo {editingPlan.group_name} • {editingPlan.academic_year_name}
                </div>
              </div>
              <button
                onClick={() => setEditingPlan(null)}
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

            <form onSubmit={handleEditSubmit}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Nombre de la Unidad Didáctica / Temática: *
                </label>
                <input
                  type="text"
                  value={editUnitName}
                  onChange={(e) => setEditUnitName(e.target.value)}
                  placeholder="Ej: Unidad 2: Cinemática y Leyes de Newton"
                  required
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Estado: *
                  </label>
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value as AcademicPlanStatus)}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
                  >
                    <option value="DRAFT">Borrador</option>
                    <option value="APPROVED">Aprobada</option>
                    <option value="IN_PROGRESS">En Ejecución</option>
                    <option value="COMPLETED">Completada</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Fecha de Inicio:
                  </label>
                  <input
                    type="date"
                    value={editStartDate}
                    onChange={(e) => setEditStartDate(e.target.value)}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Fecha de Finalización:
                  </label>
                  <input
                    type="date"
                    value={editEndDate}
                    onChange={(e) => setEditEndDate(e.target.value)}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Competencias a Desarrollar (MEN):
                </label>
                <textarea
                  rows={2}
                  value={editCompetencies}
                  onChange={(e) => setEditCompetencies(e.target.value)}
                  placeholder="Formulación de hipótesis, modelamiento matemático y razonamiento cuantitativo..."
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Objetivos de Aprendizaje (DBA):
                </label>
                <textarea
                  rows={2}
                  value={editLearningObjectives}
                  onChange={(e) => setEditLearningObjectives(e.target.value)}
                  placeholder="El estudiante interpreta situaciones físicas aplicando principios de dinámica..."
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Metodología Pedagógica:
                </label>
                <textarea
                  rows={2}
                  value={editMethodology}
                  onChange={(e) => setEditMethodology(e.target.value)}
                  placeholder="Aprendizaje basado en problemas (ABP), laboratorios virtuales y talleres colaborativos..."
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Criterios e Instrumentos de Evaluación:
                </label>
                <textarea
                  rows={2}
                  value={editEvaluationCriteria}
                  onChange={(e) => setEditEvaluationCriteria(e.target.value)}
                  placeholder="Rúbrica de evaluación continua, quices formativos y sustentación final..."
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <Button variant="secondary" type="button" onClick={() => setEditingPlan(null)}>
                  Cancelar
                </Button>
                <Button variant="primary" type="submit" disabled={isSavingEdit}>
                  {isSavingEdit ? 'Guardando Cambios...' : '💾 Guardar Cambios'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
