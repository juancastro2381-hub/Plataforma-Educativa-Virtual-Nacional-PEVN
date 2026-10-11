/**
 * PEVN Frontend — Curricular Subjects View (Plan de Estudios / Asignaturas)
 *
 * Professional view displaying the institutional curricular plan of study,
 * statutory Colombian mandatory subjects, and weekly intensity allocations.
 * Protected by RBAC permission: 'subjects:read'.
 * Supports subject creation protected by 'subjects:create'.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { academicApi } from '@/services/academic'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Modal } from '@/components/ui/Modal'
import { useAuth } from '@/hooks/useAuth'
import type {
  GradeResponse,
  KnowledgeAreaResponse,
  SubjectCreateRequest,
  SubjectResponse,
} from '@/types'

export const SubjectsView: React.FC = () => {
  const { hasPermission } = useAuth()

  const [subjects, setSubjects] = useState<SubjectResponse[]>([])
  const [grades, setGrades] = useState<GradeResponse[]>([])
  const [knowledgeAreas, setKnowledgeAreas] = useState<KnowledgeAreaResponse[]>([])
  const [selectedGradeId, setSelectedGradeId] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Create Subject Modal State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [formError, setFormError] = useState<string | null>(null)

  const [createName, setCreateName] = useState<string>('')
  const [createGradeId, setCreateGradeId] = useState<string>('')
  const [createKnowledgeAreaId, setCreateKnowledgeAreaId] = useState<string>('')
  const [createWeeklyHours, setCreateWeeklyHours] = useState<number>(4)

  const loadData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [gradesRes, subjectsRes, kaRes] = await Promise.all([
        academicApi.listGrades().catch(() => ({ items: [], total: 0 })),
        academicApi.listSubjects(selectedGradeId ? { gradeId: selectedGradeId } : undefined),
        academicApi.listKnowledgeAreas().catch(() => ({ items: [], total: 0 })),
      ])
      setGrades(gradesRes.items)
      setSubjects(subjectsRes.items)
      setKnowledgeAreas(kaRes.items)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cargar asignaturas curriculares.')
    } finally {
      setIsLoading(false)
    }
  }, [selectedGradeId])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const handleOpenCreate = () => {
    setFormError(null)
    setCreateName('')
    setCreateGradeId(selectedGradeId || (grades[0]?.id ?? ''))
    setCreateKnowledgeAreaId(knowledgeAreas[0]?.id ?? '')
    setCreateWeeklyHours(4)
    setIsCreateOpen(true)
  }

  const handleCreateSubject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!createName.trim()) {
      setFormError('El nombre de la asignatura es obligatorio.')
      return
    }
    if (!createGradeId) {
      setFormError('Debe seleccionar el grado escolar curricular.')
      return
    }
    if (!createKnowledgeAreaId) {
      setFormError('Debe seleccionar el área fundamental de conocimiento.')
      return
    }
    if (createWeeklyHours < 1 || createWeeklyHours > 40) {
      setFormError('La intensidad horaria semanal debe estar entre 1 y 40 horas.')
      return
    }

    setIsSubmitting(true)
    setFormError(null)
    setError(null)
    setSuccessMsg(null)

    const payload: SubjectCreateRequest = {
      name: createName.trim(),
      grade_id: createGradeId,
      knowledge_area_id: createKnowledgeAreaId,
      weekly_hours: Number(createWeeklyHours),
    }

    try {
      await academicApi.createSubject(payload)
      setSuccessMsg(`Asignatura "${payload.name}" registrada exitosamente en el plan de estudios.`)
      setIsCreateOpen(false)
      await loadData()
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Error al registrar la asignatura curricular.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div id="subjects-catalog-view">
      {/* Global Alerts */}
      {error && <Alert error={new Error(error)} onClose={() => setError(null)} />}
      {successMsg && (
        <Alert variant="success" message={successMsg} onClose={() => setSuccessMsg(null)} />
      )}

      <Card
        title="Plan de Estudios y Asignaturas Curriculares"
        subtitle="Malla curricular obligatoria y optativa estandarizada según el MEN y el SIEE institucional."
        action={
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <Button variant="secondary" size="sm" onClick={() => void loadData()} id="btn-refresh-subjects">
              🔄 Refrescar
            </Button>
            {hasPermission('subjects:create') && (
              <Button
                variant="primary"
                size="sm"
                id="btn-new-subject"
                onClick={handleOpenCreate}
              >
                + Nueva Asignatura
              </Button>
            )}
          </div>
        }
      >
        {/* Filters */}
        <div style={{ marginBottom: '1.25rem', display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ width: '280px' }}>
            <label
              htmlFor="filter-grade-select"
              style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
            >
              Filtrar por Grado Escolar
            </label>
            <select
              id="filter-grade-select"
              value={selectedGradeId}
              onChange={(e) => setSelectedGradeId(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                color: '#0F172A',
              }}
            >
              <option value="">Todos los Grados</option>
              {grades.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name} ({g.level})
                </option>
              ))}
            </select>
          </div>
        </div>

        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando asignaturas y áreas de conocimiento...
            </p>
          </div>
        ) : subjects.length === 0 ? (
          <EmptyState
            icon="📚"
            title="No se encontraron asignaturas"
            description="No hay asignaturas registradas para el grado seleccionado en esta institución."
            actionLabel={hasPermission('subjects:create') ? '+ Crear Nueva Asignatura' : undefined}
            onAction={handleOpenCreate}
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table
              id="subjects-table"
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '0.875rem',
                textAlign: 'left',
              }}
            >
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Asignatura</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Área de Conocimiento</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Grado</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Intensidad Semanal</th>
                </tr>
              </thead>
              <tbody>
                {subjects.map((sub) => {
                  const matchedGrade = grades.find((g) => g.id === sub.grade_id)
                  const matchedArea = knowledgeAreas.find((k) => k.id === sub.knowledge_area_id)
                  return (
                    <tr
                      key={sub.id}
                      style={{
                        borderBottom: '1px solid #F1F5F9',
                        transition: 'background-color 150ms',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8FAFC')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                    >
                      <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                        {sub.name}
                      </td>
                      <td style={{ padding: '0.875rem 1rem', color: '#334155' }}>
                        {matchedArea ? matchedArea.name : 'Área Fundamental'}
                      </td>
                      <td style={{ padding: '0.875rem 1rem' }}>
                        <Badge variant="neutral">{matchedGrade ? matchedGrade.name : 'Grado Asignado'}</Badge>
                      </td>
                      <td style={{ padding: '0.875rem 1rem', textAlign: 'center' }}>
                        <span
                          style={{
                            backgroundColor: '#EFF6FF',
                            color: '#1D4ED8',
                            fontWeight: 700,
                            padding: '0.2rem 0.6rem',
                            borderRadius: '9999px',
                            fontSize: '0.8125rem',
                          }}
                        >
                          {sub.weekly_hours} {sub.weekly_hours === 1 ? 'hora' : 'horas'}/sem
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal: Crear Nueva Asignatura */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          if (!isSubmitting) setIsCreateOpen(false)
        }}
        title="Nueva Asignatura Curricular"
        subtitle="Agrega una nueva materia al plan de estudios institucional."
      >
        <form onSubmit={handleCreateSubject}>
          {formError && (
            <div style={{ marginBottom: '1rem' }}>
              <Alert error={new Error(formError)} onClose={() => setFormError(null)} />
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label
              htmlFor="subject-name-input"
              style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Nombre de la Asignatura *
            </label>
            <input
              id="subject-name-input"
              type="text"
              placeholder="Ej. Álgebra Lineal, Geometría Analítica, Filosofía"
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
              }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label
                htmlFor="subject-grade-input"
                style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
              >
                Grado Escolar *
              </label>
              <select
                id="subject-grade-input"
                value={createGradeId}
                onChange={(e) => setCreateGradeId(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '8px',
                  border: '1px solid #CBD5E1',
                  fontSize: '0.875rem',
                  backgroundColor: '#FFFFFF',
                }}
              >
                <option value="">Seleccione Grado...</option>
                {grades.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.name} ({g.level})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                htmlFor="subject-hours-input"
                style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
              >
                Intensidad Horaria Semanal *
              </label>
              <input
                id="subject-hours-input"
                type="number"
                min="1"
                max="40"
                value={createWeeklyHours}
                onChange={(e) => setCreateWeeklyHours(parseInt(e.target.value, 10) || 1)}
                required
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

          <div style={{ marginBottom: '1.5rem' }}>
            <label
              htmlFor="subject-ka-input"
              style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Área Fundamental de Conocimiento (Ley 115) *
            </label>
            <select
              id="subject-ka-input"
              value={createKnowledgeAreaId}
              onChange={(e) => setCreateKnowledgeAreaId(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
              }}
            >
              <option value="">Seleccione Área de Conocimiento...</option>
              {knowledgeAreas.map((ka) => (
                <option key={ka.id} value={ka.id}>
                  {ka.name}
                </option>
              ))}
            </select>
            <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block', marginTop: '0.25rem' }}>
              Asigna la materia al área correspondiente según los estándares del Ministerio de Educación Nacional.
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
            <Button
              variant="secondary"
              type="button"
              onClick={() => setIsCreateOpen(false)}
              disabled={isSubmitting}
              id="btn-cancel-create-subject"
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              type="submit"
              disabled={isSubmitting}
              id="btn-submit-create-subject"
            >
              {isSubmitting ? 'Guardando Asignatura...' : 'Guardar Asignatura'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default SubjectsView
