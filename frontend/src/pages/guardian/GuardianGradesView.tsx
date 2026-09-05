/**
 * PEVN Frontend — Guardian Grades & Official Academic Reports View (Phase 16E)
 *
 * Official academic reports and evaluations view for the selected child:
 * - Subtab 1: Boletín Oficial de Período (Phase 16E — Authoritative periodic SIEE report card)
 * - Subtab 2: Informe Final y Promoción (Phase 16E — Annual cumulative report & promotion outcome)
 * - Subtab 3: Calificaciones por Actividad (Phase 14 — Detailed activity grades and educator notes)
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import type { GuardianChildGradesListResponse } from '@/types/guardian'
import type { StudentGradeItemResponse } from '@/types/student'
import type {
  AcademicPeriodResponse,
  StudentReportCardResponse,
  YearEndReportCardResponse,
} from '@/types/evaluation'
import { evaluationApi } from '@/services/evaluation'
import { academicApi } from '@/services/academic'
import { OfficialReportCard } from '@/components/evaluation/OfficialReportCard'
import { OfficialYearEndReportCard } from '@/components/evaluation/OfficialYearEndReportCard'
import { GuardianEmptyState } from '@/components/guardian/GuardianEmptyState'
import { GuardianLoadingSkeleton } from '@/components/guardian/GuardianLoadingSkeleton'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

export type GuardianGradesSubMode = 'period_report' | 'year_end_report' | 'activity_grades'

interface Props {
  gradesData: GuardianChildGradesListResponse | null
  loading: boolean
  childName?: string
  studentId?: string
  academicYearId?: string
  initialSubMode?: GuardianGradesSubMode
}

export const GuardianGradesView: React.FC<Props> = ({
  gradesData,
  loading,
  childName,
  studentId: propStudentId,
  academicYearId: propAcademicYearId,
  initialSubMode,
}) => {
  const [subMode, setSubMode] = useState<GuardianGradesSubMode>(
    initialSubMode || (propAcademicYearId ? 'period_report' : 'activity_grades')
  )

  const studentId = propStudentId || (gradesData as any)?.student_id || null
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

  // Discover active academic year if not provided
  useEffect(() => {
    if (!academicYearId) {
      if (typeof academicApi?.listAcademicYears === 'function') {
        const promise = academicApi.listAcademicYears()
        if (promise && typeof promise.then === 'function') {
          promise
            .then((res) => {
              if (res?.items && res.items.length > 0) {
                const activeY = res.items.find((y) => y.status === 'ACTIVE') || res.items[0]
                setAcademicYearId(activeY.id)
              }
            })
            .catch(() => {
              // Keep state
            })
        }
      }
    }
  }, [academicYearId])

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
                const openPeriod = res.items.find((p) => !p.is_closed) || res.items[0]
                setSelectedPeriodId(openPeriod.id)
              }
            }
          })
          .catch(() => {
            // Keep state
          })
      }
    }
  }, [academicYearId, selectedPeriodId, initialSubMode])

  // Load period report card for child
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
          `No se pudo cargar el boletín oficial de calificaciones para ${childName || 'el estudiante'}.`
      )
      setPeriodReportCard(null)
    } finally {
      setPeriodLoading(false)
    }
  }, [childName])

  // Load year-end report card for child
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
          `No se pudo cargar el informe final acumulado para ${childName || 'el estudiante'}.`
      )
      setYearEndReportCard(null)
    } finally {
      setYearEndLoading(false)
    }
  }, [childName])

  // Fetch when subMode or selections change
  useEffect(() => {
    if (subMode === 'period_report' && studentId && selectedPeriodId) {
      loadPeriodReportCard(studentId, selectedPeriodId)
    } else if (subMode === 'year_end_report' && studentId && academicYearId) {
      loadYearEndReportCard(studentId, academicYearId)
    }
  }, [subMode, studentId, selectedPeriodId, academicYearId, loadPeriodReportCard, loadYearEndReportCard])

  // Group activity evaluations by subject for Tab 3
  const subjectsMap = useMemo(() => {
    if (!gradesData || !gradesData.items) return []
    const map = new Map<string, { subjectName: string; teacherName: string | null; items: StudentGradeItemResponse[] }>()

    for (const g of gradesData.items) {
      if (!map.has(g.subject_id)) {
        map.set(g.subject_id, {
          subjectName: g.subject_name,
          teacherName: g.teacher_name,
          items: [],
        })
      }
      map.get(g.subject_id)!.items.push(g)
    }

    return Array.from(map.entries()).map(([subId, data]) => {
      const scoredItems = data.items.filter((i) => i.score !== null)
      const avg = scoredItems.length > 0
        ? scoredItems.reduce((acc, curr) => acc + Number(curr.score), 0) / scoredItems.length
        : null

      return {
        subjectId: subId,
        subjectName: data.subjectName,
        teacherName: data.teacherName,
        items: data.items,
        average: avg,
      }
    })
  }, [gradesData])

  if (loading) {
    return <GuardianLoadingSkeleton type="overview" />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 1. Sub-Mode Toggle Bar */}
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
              <label htmlFor="guardian-period-select" style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#334155' }}>
                Período Académico:
              </label>
              <select
                id="guardian-period-select"
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

            {selectedPeriodId && studentId && (
              <button
                type="button"
                onClick={() => loadPeriodReportCard(studentId, selectedPeriodId)}
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
                Cargando boletín oficial para {childName || 'el estudiante'}...
              </p>
            </div>
          ) : periodError ? (
            <GuardianEmptyState
              icon="⚠️"
              title="No se pudo cargar el boletín"
              description={periodError}
            />
          ) : periodReportCard ? (
            <OfficialReportCard reportCard={periodReportCard} />
          ) : (
            <GuardianEmptyState
              icon="📊"
              title="Seleccione un período académico"
              description={`Seleccione un período para consultar el boletín oficial de calificaciones de ${childName || 'su acudido'}.`}
            />
          )}
        </div>
      )}

      {/* 3. MODE: Year-End Cumulative Report Card */}
      {subMode === 'year_end_report' && (
        <div>
          {yearEndLoading ? (
            <div style={{ padding: '3rem 0', textAlign: 'center' }}>
              <LoadingSpinner size="lg" />
              <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
                Cargando informe final acumulado de {childName || 'el estudiante'}...
              </p>
            </div>
          ) : yearEndError ? (
            <GuardianEmptyState
              icon="⚠️"
              title="Informe final no disponible"
              description={yearEndError}
            />
          ) : yearEndReportCard ? (
            <OfficialYearEndReportCard reportCard={yearEndReportCard} />
          ) : (
            <GuardianEmptyState
              icon="🎓"
              title="Informe final en proceso"
              description={`El informe final y dictamen de promoción de ${childName || 'el estudiante'} estará disponible al finalizar el año lectivo.`}
            />
          )}
        </div>
      )}

      {/* 4. MODE: Activity Grades (Phase 14 Legacy Mode) */}
      {subMode === 'activity_grades' && (
        <div>
          {/* Header */}
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '16px',
              border: '1px solid #E2E8F0',
              padding: '1.5rem',
              marginBottom: '1.75rem',
              boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
            }}
          >
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
                Libreta Oficial de Calificaciones — {childName || 'Estudiante'}
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
                Registro detallado de tareas, talleres y retroalimentaciones pedagógicas emitidas por los docentes.
              </p>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
                Promedio Ponderado General
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A' }}>
                {gradesData?.average_score !== null && gradesData?.average_score !== undefined
                  ? `${Number(gradesData.average_score).toFixed(1)} / 5.0`
                  : '— / 5.0'}
              </div>
            </div>
          </div>

          {/* Subjects Grouping */}
          {!gradesData || gradesData.items.length === 0 ? (
            <GuardianEmptyState
              icon="📊"
              title="Sin calificaciones registradas"
              description={`No se registran notas de actividades para ${childName || 'el estudiante'} en este período.`}
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {subjectsMap.map((sub) => (
                <div
                  key={sub.subjectId}
                  style={{
                    backgroundColor: '#FFFFFF',
                    borderRadius: '16px',
                    border: '1px solid #E2E8F0',
                    overflow: 'hidden',
                    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
                  }}
                >
                  <div
                    style={{
                      padding: '1.25rem 1.5rem',
                      backgroundColor: '#F8FAFC',
                      borderBottom: '1px solid #E2E8F0',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
                        {sub.subjectName}
                      </h3>
                      {sub.teacherName && (
                        <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                          Docente: {sub.teacherName}
                        </span>
                      )}
                    </div>
                    {sub.average !== null && (
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', display: 'block' }}>
                          Promedio
                        </span>
                        <strong style={{ fontSize: '1.25rem', fontWeight: 800, color: sub.average >= 3.0 ? '#15803D' : '#B91C1C' }}>
                          {sub.average.toFixed(1)}
                        </strong>
                      </div>
                    )}
                  </div>

                  <div style={{ padding: '1rem 1.5rem' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {sub.items.map((item, idx) => (
                        <div
                          key={item.grade_id || item.activity_id || idx}
                          style={{
                            padding: '0.875rem',
                            borderRadius: '8px',
                            backgroundColor: '#FAFAFA',
                            border: '1px solid #F1F5F9',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'flex-start',
                            gap: '1rem',
                          }}
                        >
                          <div style={{ flex: 1 }}>
                            <div style={{ fontWeight: 700, fontSize: '0.875rem', color: '#0F172A' }}>
                              {item.activity_title}
                            </div>
                            {item.feedback && (
                              <div style={{ marginTop: '0.25rem', fontSize: '0.8125rem', color: '#475569', fontStyle: 'italic' }}>
                                "{item.feedback}"
                              </div>
                            )}
                          </div>
                          <div style={{ textAlign: 'right', minWidth: '80px' }}>
                            <div style={{ fontSize: '1.125rem', fontWeight: 800, color: item.score !== null && Number(item.score) >= 3.0 ? '#15803D' : '#B91C1C' }}>
                              {item.score !== null ? Number(item.score).toFixed(1) : '—'}
                              <span style={{ fontSize: '0.75rem', fontWeight: 400, color: '#94A3B8' }}> / {item.max_score}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
