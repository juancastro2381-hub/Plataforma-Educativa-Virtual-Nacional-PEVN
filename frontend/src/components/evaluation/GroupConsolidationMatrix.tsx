/**
 * PEVN Frontend — Group Consolidation Matrix Component (Phase 16E)
 *
 * Official institutional Grade Sheet (Sábana de Notas y Ranking de Grupo):
 * - Displays complete matrix of students x subjects for evaluation commissions
 * - Group ranking (Puesto) and student averages computed authoritatively by backend
 * - Clean CSV Export strictly formatted from the authorized backend payload
 * - Print-to-PDF presentation with landscape formatting
 */

import React from 'react'
import type { GroupConsolidationMatrixResponse, SieePerformanceLevel } from '@/types/evaluation'
import './ReportCardPrint.css'

interface Props {
  matrix: GroupConsolidationMatrixResponse
  onPrint?: () => void
  showActions?: boolean
}

export const GroupConsolidationMatrix: React.FC<Props> = ({
  matrix,
  onPrint,
  showActions = true,
}) => {
  const { group, period, subjects, students, total_students } = matrix

  const handlePrint = () => {
    if (onPrint) {
      onPrint()
    } else {
      window.print()
    }
  }

  const exportToCSV = () => {
    // 1. Build CSV Header
    const subjectHeaders = subjects.map((s) => `"${s.name.replace(/"/g, '""')}"`).join(',')
    const headerRow = `"Puesto","Estudiante","Código SIMAT",${subjectHeaders},"Promedio","Inasistencias"`

    // 2. Build Student Rows
    const dataRows = students.map((st) => {
      const subjectScores = subjects
        .map((s) => {
          const scoreObj = st.subjects[s.id]
          return scoreObj && scoreObj.score !== null ? scoreObj.score.toFixed(2) : '—'
        })
        .join(',')

      return `"${st.rank}","${st.student_name.replace(/"/g, '""')}","${st.simat_code || ''}",${subjectScores},"${st.average.toFixed(2)}","${st.total_absences}"`
    })

    const csvContent = '\uFEFF' + [headerRow, ...dataRows].join('\r\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.setAttribute('href', url)
    link.setAttribute(
      'download',
      `Sabana_Notas_${group.name.replace(/\s+/g, '_')}_Periodo_${period.period_number}.csv`
    )
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const getScoreColor = (level: SieePerformanceLevel | null) => {
    switch (level) {
      case 'SUPERIOR':
        return '#1D4ED8'
      case 'ALTO':
        return '#15803D'
      case 'BASICO':
        return '#854D0E'
      case 'BAJO':
        return '#B91C1C'
      default:
        return '#64748B'
    }
  }

  return (
    <div className="official-report-document" style={{ width: '100%', margin: '0 auto' }}>
      {/* 1. Actions Toolbar (Screen only) */}
      {showActions && (
        <div
          className="no-print"
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#F8FAFC',
            border: '1px solid #E2E8F0',
            borderRadius: '12px',
            padding: '0.875rem 1.25rem',
            marginBottom: '1.5rem',
            flexWrap: 'wrap',
            gap: '0.75rem',
          }}
        >
          <div>
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: '#0F172A' }}>
              Sábana de Notas Consolidada — {group.name} ({period.name})
            </h3>
            <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
              {total_students} estudiantes registrados • {subjects.length} asignaturas evaluadas
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="button"
              onClick={exportToCSV}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
                backgroundColor: '#059669',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '8px',
                padding: '0.5rem 0.875rem',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <span>📥</span> Exportar a CSV
            </button>
            <button
              type="button"
              onClick={handlePrint}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
                backgroundColor: '#1E40AF',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '8px',
                padding: '0.5rem 0.875rem',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <span>🖨️</span> Imprimir / PDF
            </button>
          </div>
        </div>
      )}

      {/* 2. Sábana Frame */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderRadius: '12px',
          padding: '1.5rem',
          boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
        }}
      >
        {/* Document Header */}
        <div style={{ textAlign: 'center', borderBottom: '2px solid #0F172A', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0F172A', margin: '0 0 0.2rem 0', textTransform: 'uppercase' }}>
            SÁBANA CONSOLIDADA DE EVALUACIÓN Y RANKING DEL GRUPO
          </h2>
          <div style={{ fontSize: '0.8125rem', color: '#475569', fontWeight: 600 }}>
            {group.grade_name ? `${group.grade_name} — ` : ''}GRUPO {group.name} • {period.name.toUpperCase()}
          </div>
        </div>

        {/* Matrix Table */}
        <div style={{ overflowX: 'auto' }}>
          <table className="report-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
            <thead>
              <tr style={{ backgroundColor: '#F1F5F9', borderBottom: '2px solid #CBD5E1', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem 0.35rem', width: '35px', textAlign: 'center' }}>#</th>
                <th style={{ padding: '0.5rem 0.75rem', minWidth: '160px' }}>Estudiante</th>
                <th style={{ padding: '0.5rem 0.5rem', width: '80px' }}>SIMAT</th>
                {subjects.map((sub) => (
                  <th key={sub.id} style={{ padding: '0.5rem 0.35rem', minWidth: '55px', textAlign: 'center' }} title={sub.name}>
                    {sub.name.length > 8 ? `${sub.name.slice(0, 7)}.` : sub.name}
                  </th>
                ))}
                <th style={{ padding: '0.5rem 0.5rem', width: '65px', textAlign: 'center', backgroundColor: '#E2E8F0', fontWeight: 800 }}>
                  Prom.
                </th>
                <th style={{ padding: '0.5rem 0.35rem', width: '45px', textAlign: 'center' }}>
                  Fall.
                </th>
                <th style={{ padding: '0.5rem 0.35rem', width: '45px', textAlign: 'center', fontWeight: 800 }}>
                  Pto.
                </th>
              </tr>
            </thead>
            <tbody>
              {students.length === 0 ? (
                <tr>
                  <td colSpan={6 + subjects.length} style={{ padding: '1.5rem', textAlign: 'center', color: '#64748B' }}>
                    No se registran notas de estudiantes en este salón para el período seleccionado.
                  </td>
                </tr>
              ) : (
                students.map((st) => (
                  <tr key={st.student_id} className="avoid-break" style={{ borderBottom: '1px solid #E2E8F0' }}>
                    <td style={{ padding: '0.4rem 0.35rem', textAlign: 'center', color: '#64748B' }}>
                      {st.rank}
                    </td>
                    <td style={{ padding: '0.4rem 0.75rem', fontWeight: 600, color: '#0F172A' }}>
                      {st.student_name}
                    </td>
                    <td style={{ padding: '0.4rem 0.5rem', color: '#64748B', fontSize: '0.7rem' }}>
                      {st.simat_code || '—'}
                    </td>
                    {subjects.map((sub) => {
                      const scoreData = st.subjects[sub.id]
                      const scoreVal = scoreData && scoreData.score !== null ? scoreData.score.toFixed(1) : '—'
                      const scoreColor = scoreData ? getScoreColor(scoreData.level) : '#64748B'
                      return (
                        <td
                          key={sub.id}
                          style={{
                            padding: '0.4rem 0.35rem',
                            textAlign: 'center',
                            fontWeight: scoreData && scoreData.score !== null ? 700 : 400,
                            color: scoreColor,
                          }}
                        >
                          {scoreVal}
                        </td>
                      )
                    })}
                    <td
                      style={{
                        padding: '0.4rem 0.5rem',
                        textAlign: 'center',
                        fontWeight: 800,
                        backgroundColor: '#F8FAFC',
                        color: '#0F172A',
                      }}
                    >
                      {st.average.toFixed(2)}
                    </td>
                    <td style={{ padding: '0.4rem 0.35rem', textAlign: 'center', color: '#64748B' }}>
                      {st.total_absences}
                    </td>
                    <td style={{ padding: '0.4rem 0.35rem', textAlign: 'center', fontWeight: 800, color: '#1E3A8A' }}>
                      {st.rank}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
