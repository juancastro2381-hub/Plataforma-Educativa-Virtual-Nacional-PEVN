/**
 * PEVN Frontend — Guardian Academic Performance View (Rendimiento Académico)
 *
 * Provides a comprehensive academic overview of the selected child's subjects,
 * evaluations, cumulative averages (0.0 – 5.0), and educator qualitative observations.
 */

import React, { useMemo } from 'react'
import type { GuardianChildGradesListResponse } from '@/types/guardian'
import type { StudentGradeItemResponse } from '@/types/student'
import { GuardianEmptyState } from '@/components/guardian/GuardianEmptyState'
import { GuardianLoadingSkeleton } from '@/components/guardian/GuardianLoadingSkeleton'

interface Props {
  gradesData: GuardianChildGradesListResponse | null
  loading: boolean
  childName?: string
}

export const GuardianAcademicView: React.FC<Props> = ({ gradesData, loading, childName }) => {
  if (loading) {
    return <GuardianLoadingSkeleton type="overview" />
  }

  if (!gradesData || gradesData.items.length === 0) {
    return (
      <GuardianEmptyState
        icon="📈"
        title="Sin registros de rendimiento académico"
        description={`Aún no se registran calificaciones oficiales para ${childName || 'el estudiante'}. Los docentes publicarán evaluaciones a lo largo del periodo lectivo.`}
      />
    )
  }

  // Group grades by subject
  const subjectsMap = useMemo(() => {
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
  }, [gradesData.items])

  const getPerformanceBadge = (avg: number | null) => {
    if (avg === null) return { text: 'Pendiente', bg: '#F1F5F9', color: '#64748B' }
    if (avg >= 4.6) return { text: 'Excelente (Superior)', bg: '#DCFCE7', color: '#15803D' }
    if (avg >= 4.0) return { text: 'Sobresaliente (Alto)', bg: '#EFF6FF', color: '#1D4ED8' }
    if (avg >= 3.0) return { text: 'Aceptable (Básico)', bg: '#FEF3C7', color: '#B45309' }
    return { text: 'En Riesgo (Bajo)', bg: '#FEE2E2', color: '#B91C1C' }
  }

  return (
    <div>
      {/* Header with Global Average */}
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
            Rendimiento Académico y Desempeño
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
            Seguimiento integral del progreso en las asignaturas cursadas por <strong>{gradesData.student_name}</strong>.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
              Promedio General Acumulado
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A' }}>
              {gradesData.average_score !== null ? Number(gradesData.average_score).toFixed(1) : '—'}
              <span style={{ fontSize: '0.875rem', color: '#94A3B8', fontWeight: 400 }}> / 5.0</span>
            </div>
          </div>
        </div>
      </div>

      {/* Subjects Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {subjectsMap.map((sub) => {
          const badge = getPerformanceBadge(sub.average)

          return (
            <div
              key={sub.subjectId}
              style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '14px',
                border: '1px solid #E2E8F0',
                padding: '1.5rem',
                boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
              }}
            >
              {/* Subject Title & Stats Header */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                  marginBottom: '1rem',
                  paddingBottom: '0.75rem',
                  borderBottom: '1px solid #F1F5F9',
                }}
              >
                <div>
                  <h3 style={{ margin: '0 0 0.2rem 0', fontSize: '1.125rem', fontWeight: 800, color: '#0F172A' }}>
                    📖 {sub.subjectName}
                  </h3>
                  {sub.teacherName && (
                    <div style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                      👨‍🏫 Docente Titular: <strong>{sub.teacherName}</strong>
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span
                    style={{
                      padding: '0.25rem 0.75rem',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      backgroundColor: badge.bg,
                      color: badge.color,
                    }}
                  >
                    {badge.text}
                  </span>

                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block' }}>Promedio</span>
                    <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
                      {sub.average !== null ? sub.average.toFixed(1) : '—'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Evaluations Table for Subject */}
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #E2E8F0', color: '#64748B' }}>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Actividad / Evaluación</th>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Tipo</th>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Retroalimentación del Educador</th>
                      <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right' }}>Nota Obtenida</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sub.items.map((it) => (
                      <tr key={it.activity_id} style={{ borderBottom: '1px solid #F8FAFC' }}>
                        <td style={{ padding: '0.625rem 0.75rem', fontWeight: 700, color: '#0F172A' }}>
                          {it.activity_title}
                        </td>
                        <td style={{ padding: '0.625rem 0.75rem' }}>
                          <span
                            style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              backgroundColor: '#F1F5F9',
                              color: '#475569',
                              padding: '0.15rem 0.45rem',
                              borderRadius: '4px',
                            }}
                          >
                            {it.activity_type}
                          </span>
                        </td>
                        <td style={{ padding: '0.625rem 0.75rem', color: '#475569', fontStyle: it.feedback ? 'italic' : 'normal' }}>
                          {it.feedback || <span style={{ color: '#94A3B8' }}>Sin observaciones registradas</span>}
                        </td>
                        <td style={{ padding: '0.625rem 0.75rem', textAlign: 'right', fontWeight: 800, color: it.score !== null && Number(it.score) >= 3.0 ? '#15803D' : '#BE123C' }}>
                          {it.score !== null ? `${Number(it.score).toFixed(1)} / ${Number(it.max_score).toFixed(1)}` : 'Sin Calificar'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
