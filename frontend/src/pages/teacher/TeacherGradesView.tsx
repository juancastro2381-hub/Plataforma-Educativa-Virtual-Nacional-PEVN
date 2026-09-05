/**
 * PEVN Frontend — Teacher Grades & Evaluation View
 *
 * Provides both:
 * 1. SIEE Period Consolidation Sheet (TeacherSieeEvaluationView - Phase 16D)
 * 2. Activity-level grading sheet (Phase 13)
 */

import React, { useEffect, useState } from 'react'
import type {
  AcademicActivityResponse,
  ActivityGradeEntry,
  ActivityGradesListResponse,
  TeacherAssignmentItemResponse,
} from '@/types/teacher'
import { teacherApi } from '@/services/teacher'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { TeacherSieeEvaluationView } from './TeacherSieeEvaluationView'

interface Props {
  activities: AcademicActivityResponse[]
  assignments?: TeacherAssignmentItemResponse[]
  initialSelectedActivityId?: string | null
}

export const TeacherGradesView: React.FC<Props> = ({
  activities,
  assignments = [],
  initialSelectedActivityId,
}) => {
  const [evaluationMode, setEvaluationMode] = useState<'siee' | 'activities'>(
    initialSelectedActivityId ? 'activities' : 'siee'
  )

  const publishedActivities = activities.filter((a) => a.status === 'PUBLISHED' || a.status === 'CLOSED')
  const [selectedActivityId, setSelectedActivityId] = useState<string>(
    initialSelectedActivityId || (publishedActivities[0]?.id ?? '')
  )

  const [gradesheet, setGradesheet] = useState<ActivityGradesListResponse | null>(null)
  const [localScores, setLocalScores] = useState<Record<string, string>>({})
  const [localFeedbacks, setLocalFeedbacks] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const loadGradesheet = async (actId: string) => {
    if (!actId) {
      setGradesheet(null)
      return
    }
    setLoading(true)
    setStatusMessage(null)
    try {
      const data = await teacherApi.getActivityGrades(actId)
      setGradesheet(data)
      const scoresMap: Record<string, string> = {}
      const feedbacksMap: Record<string, string> = {}
      data.items.forEach((item) => {
        scoresMap[item.student_id] = item.score !== null ? String(item.score) : ''
        feedbacksMap[item.student_id] = item.feedback || ''
      })
      setLocalScores(scoresMap)
      setLocalFeedbacks(feedbacksMap)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar la planilla de notas.'
      setStatusMessage({ type: 'error', text: msg })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (initialSelectedActivityId) {
      setSelectedActivityId(initialSelectedActivityId)
      setEvaluationMode('activities')
      void loadGradesheet(initialSelectedActivityId)
    } else if (publishedActivities.length > 0 && !selectedActivityId) {
      const firstId = publishedActivities[0].id
      setSelectedActivityId(firstId)
      void loadGradesheet(firstId)
    } else if (selectedActivityId) {
      void loadGradesheet(selectedActivityId)
    }
  }, [initialSelectedActivityId, publishedActivities.length, selectedActivityId])

  const handleActivityChange = (actId: string) => {
    setSelectedActivityId(actId)
    void loadGradesheet(actId)
  }

  const handleScoreChange = (studentId: string, val: string) => {
    setLocalScores((prev) => ({ ...prev, [studentId]: val }))
  }

  const handleFeedbackChange = (studentId: string, val: string) => {
    setLocalFeedbacks((prev) => ({ ...prev, [studentId]: val }))
  }

  const handleSaveGrades = async () => {
    if (!gradesheet) return
    setStatusMessage(null)

    // Validation
    const entries: ActivityGradeEntry[] = []
    for (const item of gradesheet.items) {
      const scoreStr = localScores[item.student_id]
      const feedbackStr = localFeedbacks[item.student_id]

      let numScore: number | null = null
      if (scoreStr !== undefined && scoreStr.trim() !== '') {
        const parsed = parseFloat(scoreStr)
        if (isNaN(parsed) || parsed < 0 || parsed > gradesheet.max_score) {
          setStatusMessage({
            type: 'error',
            text: `La calificación de ${item.student_name} (${scoreStr}) está fuera del rango permitido (0.0 a ${gradesheet.max_score}).`,
          })
          return
        }
        numScore = parsed
      }

      entries.push({
        student_id: item.student_id,
        score: numScore,
        feedback: feedbackStr?.trim() || null,
      })
    }

    setSaving(true)
    try {
      const updated = await teacherApi.batchUpdateActivityGrades(gradesheet.activity_id, {
        grades: entries,
      })
      setGradesheet(updated)
      setStatusMessage({ type: 'success', text: '¡Calificaciones y retroalimentaciones guardadas exitosamente!' })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al guardar calificaciones.'
      setStatusMessage({ type: 'error', text: msg })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      {/* Mode Subtabs Bar */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          backgroundColor: '#F1F5F9',
          padding: '0.375rem',
          borderRadius: '10px',
          marginBottom: '1.5rem',
          width: 'fit-content',
        }}
      >
        <button
          onClick={() => setEvaluationMode('siee')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            border: 'none',
            backgroundColor: evaluationMode === 'siee' ? '#1E3A8A' : 'transparent',
            color: evaluationMode === 'siee' ? '#FFFFFF' : '#475569',
            fontWeight: evaluationMode === 'siee' ? 700 : 500,
            fontSize: '0.875rem',
            cursor: 'pointer',
            transition: 'all 150ms ease-in-out',
          }}
        >
          <span>📊</span>
          <span>Consolidado de Período SIEE</span>
        </button>

        <button
          onClick={() => setEvaluationMode('activities')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            border: 'none',
            backgroundColor: evaluationMode === 'activities' ? '#1E3A8A' : 'transparent',
            color: evaluationMode === 'activities' ? '#FFFFFF' : '#475569',
            fontWeight: evaluationMode === 'activities' ? 700 : 500,
            fontSize: '0.875rem',
            cursor: 'pointer',
            transition: 'all 150ms ease-in-out',
          }}
        >
          <span>📝</span>
          <span>Calificar por Actividad</span>
        </button>
      </div>

      {evaluationMode === 'siee' ? (
        <TeacherSieeEvaluationView assignments={assignments} />
      ) : (
        <div>
          <div style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
              Planilla de Calificaciones y Retroalimentación
            </h2>
            <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
              Ingrese y actualice las notas obtenidas por los estudiantes en las actividades académicas publicadas.
            </p>
          </div>

          {/* Activity Selector Card */}
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '12px',
              padding: '1.25rem',
              border: '1px solid #E2E8F0',
              marginBottom: '1.5rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
            }}
          >
            <div style={{ flex: 1, minWidth: '280px' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                Seleccionar Actividad Publicada:
              </label>
              <select
                value={selectedActivityId}
                onChange={(e) => handleActivityChange(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
              >
                {publishedActivities.length === 0 && (
                  <option value="">No hay actividades publicadas para calificar</option>
                )}
                {publishedActivities.map((act) => (
                  <option key={act.id} value={act.id}>
                    {act.title} — {act.subject_name} (Grupo {act.group_name}) [{act.status}]
                  </option>
                ))}
              </select>
            </div>

            {gradesheet && (
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <Button variant="primary" onClick={handleSaveGrades} disabled={saving || loading}>
                  {saving ? 'Guardando...' : '💾 Guardar Calificaciones'}
                </Button>
              </div>
            )}
          </div>

          {statusMessage && (
            <div
              style={{
                padding: '0.875rem 1rem',
                borderRadius: '8px',
                marginBottom: '1.5rem',
                fontSize: '0.875rem',
                backgroundColor: statusMessage.type === 'success' ? '#F0FDF4' : '#FEF2F2',
                border: `1px solid ${statusMessage.type === 'success' ? '#86EFAC' : '#FCA5A5'}`,
                color: statusMessage.type === 'success' ? '#166534' : '#991B1B',
              }}
            >
              {statusMessage.text}
            </div>
          )}

          {/* Gradesheet Table */}
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
                <p style={{ marginTop: '0.5rem', color: '#64748B', fontSize: '0.875rem' }}>Cargando planilla de notas...</p>
              </div>
            ) : !gradesheet ? (
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#64748B' }}>
                Seleccione una actividad publicada para abrir la planilla de notas.
              </div>
            ) : (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', paddingBottom: '0.75rem', borderBottom: '1px solid #F1F5F9' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 800, color: '#0F172A' }}>
                      {gradesheet.activity_title}
                    </h3>
                    <div style={{ fontSize: '0.8125rem', color: '#64748B', marginTop: '0.2rem' }}>
                      Puntaje Máximo: <strong>{gradesheet.max_score}</strong> | Registros: <strong>{gradesheet.items.length}</strong>
                    </div>
                  </div>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '2px solid #E2E8F0', textAlign: 'left' }}>
                        <th style={{ padding: '0.75rem', width: '50px' }}>#</th>
                        <th style={{ padding: '0.75rem', minWidth: '180px' }}>Estudiante</th>
                        <th style={{ padding: '0.75rem', minWidth: '100px' }}>Documento</th>
                        <th style={{ padding: '0.75rem', width: '120px' }}>Nota (0 - {gradesheet.max_score})</th>
                        <th style={{ padding: '0.75rem', minWidth: '220px' }}>Retroalimentación Pedagógica</th>
                        <th style={{ padding: '0.75rem', width: '120px' }}>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {gradesheet.items.map((item, idx) => (
                        <tr key={item.student_id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                          <td style={{ padding: '0.625rem 0.75rem', color: '#64748B' }}>{idx + 1}</td>
                          <td style={{ padding: '0.625rem 0.75rem', fontWeight: 600, color: '#0F172A' }}>
                            {item.student_name}
                          </td>
                          <td style={{ padding: '0.625rem 0.75rem', color: '#64748B' }}>
                            {item.student_document || '—'}
                          </td>
                          <td style={{ padding: '0.625rem 0.75rem' }}>
                            <input
                              type="number"
                              step="0.1"
                              min={0}
                              max={gradesheet.max_score}
                              value={localScores[item.student_id] ?? ''}
                              onChange={(e) => handleScoreChange(item.student_id, e.target.value)}
                              placeholder="0.0"
                              style={{
                                width: '80px',
                                padding: '0.45rem',
                                borderRadius: '6px',
                                border: '1px solid #CBD5E1',
                                textAlign: 'center',
                                fontWeight: 700,
                              }}
                            />
                          </td>
                          <td style={{ padding: '0.625rem 0.75rem' }}>
                            <input
                              type="text"
                              value={localFeedbacks[item.student_id] ?? ''}
                              onChange={(e) => handleFeedbackChange(item.student_id, e.target.value)}
                              placeholder="Observaciones pedagógicas..."
                              style={{
                                width: '100%',
                                padding: '0.45rem',
                                borderRadius: '6px',
                                border: '1px solid #CBD5E1',
                                boxSizing: 'border-box',
                              }}
                            />
                          </td>
                          <td style={{ padding: '0.625rem 0.75rem' }}>
                            <span
                              style={{
                                padding: '0.2rem 0.5rem',
                                borderRadius: '9999px',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                backgroundColor: localScores[item.student_id] ? '#DCFCE7' : '#F1F5F9',
                                color: localScores[item.student_id] ? '#15803D' : '#64748B',
                              }}
                            >
                              {localScores[item.student_id] ? 'EVALUADO' : 'PENDIENTE'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {gradesheet && gradesheet.items.length > 0 && (
              <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
                <Button variant="primary" onClick={handleSaveGrades} disabled={saving || loading}>
                  {saving ? 'Guardando...' : '💾 Guardar Calificaciones'}
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default TeacherGradesView
