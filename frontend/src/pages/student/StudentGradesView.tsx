/**
 * PEVN Frontend — Student Grades & Official Academic Reports View (Phase 16E)
 *
 * Comprehensive academic performance and official evaluation portal for students:
 * - Tab 1: Boletín Oficial de Período (Phase 16E — Authoritative SIEE periodic report card)
 * - Tab 2: Informe Final y Promoción (Phase 16E — Annual cumulative report and promotion outcome)
 * - Tab 3: Calificaciones por Actividad (Phase 14 — Granular homework, workshop and exam feedback)
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import type { StudentGradeItemResponse, StudentSubjectItemResponse } from '@/types/student'
import type {
  AcademicPeriodResponse,
  StudentReportCardResponse,
  YearEndReportCardResponse,
} from '@/types/evaluation'
import { evaluationApi } from '@/services/evaluation'
import { studentApi } from '@/services/student'
import { OfficialReportCard } from '@/components/evaluation/OfficialReportCard'
import { OfficialYearEndReportCard } from '@/components/evaluation/OfficialYearEndReportCard'
import { StudentEmptyState } from '@/components/student/StudentEmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { formatDateTime } from '@/utils'

export type GradesSubMode = 'period_report' | 'year_end_report' | 'activity_grades'

interface StudentGradesViewProps {
  grades: StudentGradeItemResponse[]
  averageScore?: number | string | null
  subjects: StudentSubjectItemResponse[]
  studentId?: string
  academicYearId?: string
  initialSubMode?: GradesSubMode
}

export const StudentGradesView: React.FC<StudentGradesViewProps> = ({
  grades,
  averageScore,
  subjects,
  studentId: propStudentId,
  academicYearId: propAcademicYearId,
  initialSubMode,
}) => {
  const [subMode, setSubMode] = useState<GradesSubMode>(
    initialSubMode || (propAcademicYearId ? 'period_report' : 'activity_grades')
  )

  // Resolved student and academic year IDs
  const [studentId, setStudentId] = useState<string | null>(propStudentId || null)
  const [academicYearId, setAcademicYearId] = useState<string | null>(propAcademicYearId || null)

  // Period report card states
  const [periods, setPeriods] = useState<AcademicPeriodResponse[]>([])
  const [selectedPeriodId, setSelectedPeriodId] = useState<string>('')
  const [periodReportCard, setPeriodReportCard] = useState<StudentReportCardResponse | null>(null)
  const [periodLoading, setPeriodLoading] = useState<boolean>(false)
  const [periodError, setPeriodError] = useState<string | null>(null)

  // Year-end report card states
  const [yearEndReportCard, setYearEndReportCard] = useState<YearEndReportCardResponse | null>(null)
  const [yearEndLoading, setYearEndLoading] = useState<boolean>(false)
  const [yearEndError, setYearEndError] = useState<string | null>(null)

  // Activity filter state
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('ALL')

  // Resolve profile if studentId is not provided
  useEffect(() => {
    if (!studentId || !academicYearId) {
      if (typeof studentApi?.getProfile === 'function') {
        const promise = studentApi.getProfile()
        if (promise && typeof promise.then === 'function') {
          promise
            .then((prof) => {
              if (prof?.student_id) setStudentId(prof.student_id)
              if (prof?.academic_year_id) setAcademicYearId(prof.academic_year_id)
            })
            .catch(() => {
              // Keep current state
            })
        }
      }
    }
  }, [studentId, academicYearId])

  // Fetch periods when academicYearId is available
  useEffect(() => {
    if (!academicYearId) return
    if (typeof evaluationApi?.listAcademicPeriods === 'function') {
      const promise = evaluationApi.listAcademicPeriods(academicYearId)
      if (promise && typeof promise.then === 'function') {
        promise
          .then((res) => {
            if (res?.items) {
              setPeriods(res.items)
              if (res.items.length > 0 && !selectedPeriodId) {
                // Select first open period or first period
                const openPeriod = res.items.find((p) => !p.is_closed) || res.items[0]
                setSelectedPeriodId(openPeriod.id)
              }
            }
          })
          .catch(() => {
            // Handle error silently
          })
      }
    }
  }, [academicYearId, selectedPeriodId, initialSubMode])

  // Fetch periodic report card
  const loadPeriodReportCard = useCallback(async (stId: string, pId: string) => {
    if (typeof evaluationApi?.getStudentReportCard !== 'function') return
    setPeriodLoading(true)
    setPeriodError(null)
    try {
      const data = await evaluationApi.getStudentReportCard(stId, pId)
      setPeriodReportCard(data)
    } catch (err: any) {
      setPeriodError(
        err.response?.data?.detail ||
          'No se pudo cargar el boletín de calificaciones para este período académico.'
      )
      setPeriodReportCard(null)
    } finally {
      setPeriodLoading(false)
    }
  }, [])

  // Fetch year-end report card
  const loadYearEndReportCard = useCallback(async (stId: string, yId: string) => {
    if (typeof evaluationApi?.getStudentYearEndReportCard !== 'function') return
    setYearEndLoading(true)
    setYearEndError(null)
    try {
      const data = await evaluationApi.getStudentYearEndReportCard(stId, yId)
      setYearEndReportCard(data)
    } catch (err: any) {
      setYearEndError(
        err.response?.data?.detail ||
          'No se pudo cargar el informe final acumulado de fin de año.'
      )
      setYearEndReportCard(null)
    } finally {
      setYearEndLoading(false)
    }
  }, [])

  // Trigger loads when subMode or selections change
  useEffect(() => {
    if (subMode === 'period_report' && studentId && selectedPeriodId) {
      loadPeriodReportCard(studentId, selectedPeriodId)
    } else if (subMode === 'year_end_report' && studentId && academicYearId) {
      loadYearEndReportCard(studentId, academicYearId)
    }
  }, [subMode, studentId, selectedPeriodId, academicYearId, loadPeriodReportCard, loadYearEndReportCard])

  // Group activity grades by subject for Tab 3
  const gradesBySubject = useMemo(() => {
    const map = new Map<string, StudentGradeItemResponse[]>()

    grades.forEach((g) => {
      if (selectedSubjectId !== 'ALL' && g.subject_id !== selectedSubjectId) return
      const list = map.get(g.subject_name) || []
      list.push(g)
      map.set(g.subject_name, list)
    })

    return map
  }, [grades, selectedSubjectId])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 1. Sub-Mode Navigation Bar */}
      <div
        className="no-print"
        style={{
          display: 'flex',
          gap: '0.5rem',
          backgroundColor: '#F1F5F9',
          padding: '0.35rem',
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
          flexWrap: 'wrap',
        }}
      >
        <button
          type="button"
          onClick={() => setSubMode('period_report')}
          style={{
            flex: '1 1 auto',
            padding: '0.625rem 1rem',
            borderRadius: '8px',
            border: 'none',
            fontSize: '0.875rem',
            fontWeight: subMode === 'period_report' ? 700 : 500,
            backgroundColor: subMode === 'period_report' ? '#FFFFFF' : 'transparent',
            color: subMode === 'period_report' ? '#1E40AF' : '#64748B',
            boxShadow: subMode === 'period_report' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          📄 Boletín Oficial de Período
        </button>

        <button
          type="button"
          onClick={() => setSubMode('year_end_report')}
          style={{
            flex: '1 1 auto',
            padding: '0.625rem 1rem',
            borderRadius: '8px',
            border: 'none',
            fontSize: '0.875rem',
            fontWeight: subMode === 'year_end_report' ? 700 : 500,
            backgroundColor: subMode === 'year_end_report' ? '#FFFFFF' : 'transparent',
            color: subMode === 'year_end_report' ? '#1E40AF' : '#64748B',
            boxShadow: subMode === 'year_end_report' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          🎓 Informe Final y Promoción
        </button>

        <button
          type="button"
          onClick={() => setSubMode('activity_grades')}
          style={{
            flex: '1 1 auto',
            padding: '0.625rem 1rem',
            borderRadius: '8px',
            border: 'none',
            fontSize: '0.875rem',
            fontWeight: subMode === 'activity_grades' ? 700 : 500,
            backgroundColor: subMode === 'activity_grades' ? '#FFFFFF' : 'transparent',
            color: subMode === 'activity_grades' ? '#1E40AF' : '#64748B',
            boxShadow: subMode === 'activity_grades' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          📝 Calificaciones por Actividad
        </button>
      </div>

      {/* 2. MODE: Official Period Report Card */}
      {subMode === 'period_report' && (
        <div>
          {/* Period Selector Controls (Screen only) */}
          <div
            className="no-print"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: '#FFFFFF',
              border: '1px solid #E2E8F0',
              borderRadius: '12px',
              padding: '1rem 1.25rem',
              marginBottom: '1.25rem',
              flexWrap: 'wrap',
              gap: '0.75rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <label htmlFor="student-period-select" style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#334155' }}>
                Período Académico:
              </label>
              <select
                id="student-period-select"
                value={selectedPeriodId}
                onChange={(e) => setSelectedPeriodId(e.target.value)}
                style={{
                  padding: '0.45rem 0.75rem',
                  borderRadius: '8px',
                  border: '1px solid #CBD5E1',
                  backgroundColor: '#FFFFFF',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  color: '#0F172A',
                }}
              >
                {periods.map((p) => (
                  <option key={p.id} value={p.id}>
                    Período {p.period_number} — {p.name} ({p.weight_percentage}%){p.is_closed ? ' [🔒 SELLADO]' : ' [🟢 ABIERTO]'}
                  </option>
                ))}
              </select>
            </div>

            {selectedPeriodId && (
              <button
                type="button"
                onClick={() => studentId && loadPeriodReportCard(studentId, selectedPeriodId)}
                style={{
                  backgroundColor: '#F1F5F9',
                  border: '1px solid #CBD5E1',
                  borderRadius: '8px',
                  padding: '0.4rem 0.75rem',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: '#334155',
                  cursor: 'pointer',
                }}
              >
                🔄 Actualizar Boletín
              </button>
            )}
          </div>

          {periodLoading ? (
            <div style={{ padding: '3rem 0', textAlign: 'center' }}>
              <LoadingSpinner size="lg" />
              <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
                Cargando boletín oficial de calificaciones...
              </p>
            </div>
          ) : periodError ? (
            <StudentEmptyState
              icon="⚠️"
              title="No se pudo cargar el boletín"
              description={periodError}
            />
          ) : periodReportCard ? (
            <OfficialReportCard reportCard={periodReportCard} />
          ) : (
            <StudentEmptyState
              icon="📊"
              title="Seleccione un período académico"
              description="Seleccione un período en el selector superior para consultar el boletín oficial de calificaciones."
            />
          )}
        </div>
      )}

      {/* 3. MODE: Year-End Cumulative Report Card & Promotion */}
      {subMode === 'year_end_report' && (
        <div>
          {yearEndLoading ? (
            <div style={{ padding: '3rem 0', textAlign: 'center' }}>
              <LoadingSpinner size="lg" />
              <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
                Cargando informe final acumulado y dictamen de promoción...
              </p>
            </div>
          ) : yearEndError ? (
            <StudentEmptyState
              icon="⚠️"
              title="Informe final no disponible"
              description={yearEndError}
            />
          ) : yearEndReportCard ? (
            <OfficialYearEndReportCard reportCard={yearEndReportCard} />
          ) : (
            <StudentEmptyState
              icon="🎓"
              title="Informe final en proceso"
              description="El informe final acumulado estará disponible una vez concluyan los períodos académicos del año lectivo."
            />
          )}
        </div>
      )}

      {/* 4. MODE: Granular Activity Grades (Phase 14 Legacy Mode) */}
      {subMode === 'activity_grades' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Header Banner with Average Score */}
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '16px',
              border: '1px solid #E2E8F0',
              padding: '1.5rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
              boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
            }}
          >
            <div>
              <h2 style={{ margin: '0 0 0.35rem 0', fontSize: '1.3rem', fontWeight: 800, color: '#0F172A' }}>
                Libreta de Calificaciones y Evaluaciones
              </h2>
              <p style={{ margin: 0, fontSize: '0.875rem', color: '#64748B' }}>
                Registro detallado de tareas, talleres, quizzes y retroalimentaciones pedagógicas emitidas por los docentes.
              </p>
            </div>

            {averageScore !== undefined && averageScore !== null && (
              <div
                style={{
                  backgroundColor: '#F0FDF4',
                  border: '2px solid #86EFAC',
                  borderRadius: '12px',
                  padding: '0.75rem 1.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                }}
              >
                <span style={{ fontSize: '1.75rem' }}>🎯</span>
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#166534', display: 'block', textTransform: 'uppercase' }}>
                    Promedio Actividades
                  </span>
                  <strong style={{ fontSize: '1.5rem', fontWeight: 800, color: '#15803D' }}>
                    {Number(averageScore).toFixed(2)}
                  </strong>
                </div>
              </div>
            )}
          </div>

          {/* Subject Filter Bar */}
          <div
            style={{
              display: 'flex',
              gap: '0.5rem',
              overflowX: 'auto',
              paddingBottom: '0.5rem',
            }}
          >
            <button
              type="button"
              onClick={() => setSelectedSubjectId('ALL')}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                border: '1px solid',
                borderColor: selectedSubjectId === 'ALL' ? '#1E40AF' : '#CBD5E1',
                backgroundColor: selectedSubjectId === 'ALL' ? '#EFF6FF' : '#FFFFFF',
                color: selectedSubjectId === 'ALL' ? '#1E40AF' : '#475569',
                fontSize: '0.8125rem',
                fontWeight: selectedSubjectId === 'ALL' ? 700 : 500,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              Todas las Asignaturas ({grades.length})
            </button>
            {subjects.map((s) => (
              <button
                key={s.subject_id}
                type="button"
                onClick={() => setSelectedSubjectId(s.subject_id)}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid',
                  borderColor: selectedSubjectId === s.subject_id ? '#1E40AF' : '#CBD5E1',
                  backgroundColor: selectedSubjectId === s.subject_id ? '#EFF6FF' : '#FFFFFF',
                  color: selectedSubjectId === s.subject_id ? '#1E40AF' : '#475569',
                  fontSize: '0.8125rem',
                  fontWeight: selectedSubjectId === s.subject_id ? 700 : 500,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                }}
              >
                {s.name}
              </button>
            ))}
          </div>

          {/* Grades Grouped List */}
          {gradesBySubject.size === 0 ? (
            <StudentEmptyState
              icon="📊"
              title="Sin calificaciones de actividades"
              description="Aún no se registran calificaciones de tareas o exámenes en esta asignatura."
            />
          ) : (
            Array.from(gradesBySubject.entries()).map(([subjName, items]) => (
              <div
                key={subjName}
                style={{
                  backgroundColor: '#FFFFFF',
                  borderRadius: '12px',
                  border: '1px solid #E2E8F0',
                  overflow: 'hidden',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
                }}
              >
                <div
                  style={{
                    backgroundColor: '#F8FAFC',
                    padding: '0.875rem 1.25rem',
                    borderBottom: '1px solid #E2E8F0',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: '#0F172A' }}>
                    {subjName}
                  </h3>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B' }}>
                    {items.length} actividad(es) calificada(s)
                  </span>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#FAFAFA', borderBottom: '1px solid #E2E8F0', textAlign: 'left' }}>
                        <th style={{ padding: '0.625rem 1rem', width: '35%' }}>Actividad</th>
                        <th style={{ padding: '0.625rem 0.75rem', width: '15%', textAlign: 'center' }}>Nota</th>
                        <th style={{ padding: '0.625rem 0.75rem', width: '15%', textAlign: 'center' }}>Puntaje Máx</th>
                        <th style={{ padding: '0.625rem 1rem', width: '35%' }}>Retroalimentación Docente</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((g, idx) => (
                        <tr key={g.grade_id || g.activity_id || idx} style={{ borderBottom: '1px solid #F1F5F9' }}>
                          <td style={{ padding: '0.625rem 1rem', verticalAlign: 'top' }}>
                            <div style={{ fontWeight: 600, color: '#0F172A' }}>{g.activity_title}</div>
                            {g.graded_at && (
                              <div style={{ fontSize: '0.7rem', color: '#64748B' }}>
                                Calificado: {formatDateTime(g.graded_at)}
                              </div>
                            )}
                          </td>
                          <td
                            style={{
                              padding: '0.625rem 0.75rem',
                              textAlign: 'center',
                              fontWeight: 800,
                              fontSize: '0.9375rem',
                              color: g.score !== null && Number(g.score) >= 3.0 ? '#15803D' : '#B91C1C',
                              verticalAlign: 'top',
                            }}
                          >
                            {g.score !== null ? Number(g.score).toFixed(1) : '—'}
                          </td>
                          <td style={{ padding: '0.625rem 0.75rem', textAlign: 'center', color: '#64748B', verticalAlign: 'top' }}>
                            {g.max_score}
                          </td>
                          <td style={{ padding: '0.625rem 1rem', color: '#334155', verticalAlign: 'top' }}>
                            {g.feedback ? (
                              <div style={{ fontStyle: 'italic', backgroundColor: '#F8FAFC', padding: '0.35rem 0.6rem', borderRadius: '6px' }}>
                                "{g.feedback}"
                              </div>
                            ) : (
                              <span style={{ color: '#94A3B8' }}>Sin retroalimentación adicional.</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
