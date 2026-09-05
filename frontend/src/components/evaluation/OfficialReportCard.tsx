/**
 * PEVN Frontend — Official Period Report Card Component (Phase 16E)
 *
 * Authoritative periodic academic report card (Boletín de Calificaciones):
 * - Displays institutional headers, DANE code, and campus metadata
 * - Explicit visual distinction: SEALED/OFFICIAL (🟢) vs. OPEN/PROVISIONAL (🟡)
 * - Subject breakdown with calculated vs. final scores, SIEE level, achievements, and absences
 * - Displays remedial recovery history with initial failing score and institutional SIEE cap
 * - Group academic ranking and summary metrics
 * - Zero-binary native print/PDF presentation with signature placeholders
 */

import React from 'react'
import type { StudentReportCardResponse, SieePerformanceLevel } from '@/types/evaluation'
import './ReportCardPrint.css'

interface Props {
  reportCard: StudentReportCardResponse
  onPrint?: () => void
  showActions?: boolean
}

export const OfficialReportCard: React.FC<Props> = ({
  reportCard,
  onPrint,
  showActions = true,
}) => {
  const { institution, campus, student, academic_year, period, group, summary, subjects } =
    reportCard

  const handlePrint = () => {
    if (onPrint) {
      onPrint()
    } else {
      window.print()
    }
  }

  const getLevelBadge = (level: SieePerformanceLevel) => {
    switch (level) {
      case 'SUPERIOR':
        return { bg: '#EFF6FF', border: '#93C5FD', text: '#1D4ED8', label: 'SUPERIOR' }
      case 'ALTO':
        return { bg: '#F0FDF4', border: '#86EFAC', text: '#15803D', label: 'ALTO' }
      case 'BASICO':
        return { bg: '#FEFCE8', border: '#FDE047', text: '#854D0E', label: 'BÁSICO' }
      case 'BAJO':
        return { bg: '#FEF2F2', border: '#FCA5A5', text: '#B91C1C', label: 'BAJO' }
      default:
        return { bg: '#F8FAFC', border: '#CBD5E1', text: '#475569', label: level }
    }
  }

  const summaryLevelStyle = getLevelBadge(summary.performance_level)

  return (
    <div className="official-report-document" style={{ width: '100%', maxWidth: '960px', margin: '0 auto' }}>
      {/* 1. Print & Action Toolbar (Screen only) */}
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
          }}
        >
          <div>
            <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A' }}>
              Boletín Oficial de Calificaciones — Período {period.period_number}
            </span>
            <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
              Año Lectivo {academic_year.year} • {group.name}
            </div>
          </div>
          <button
            type="button"
            onClick={handlePrint}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              backgroundColor: '#1E40AF',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '8px',
              padding: '0.5rem 1rem',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            }}
          >
            <span>🖨️</span> Imprimir / Guardar PDF
          </button>
        </div>
      )}

      {/* 2. Official Document Frame */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderRadius: '12px',
          padding: '2rem',
          boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
        }}
      >
        {/* Header Block */}
        <div
          style={{
            borderBottom: '2px solid #0F172A',
            paddingBottom: '1rem',
            marginBottom: '1.25rem',
            textAlign: 'center',
          }}
        >
          <h1
            style={{
              fontSize: '1.35rem',
              fontWeight: 800,
              color: '#0F172A',
              margin: '0 0 0.25rem 0',
              textTransform: 'uppercase',
              letterSpacing: '0.02em',
            }}
          >
            {institution.name}
          </h1>
          <div style={{ fontSize: '0.8125rem', color: '#475569', fontWeight: 500 }}>
            {institution.dane_code && `CÓDIGO DANE: ${institution.dane_code} • `}
            {campus.name} • AÑO LECTIVO {academic_year.year}
          </div>
          <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#1E3A8A', marginTop: '0.35rem' }}>
            INFORME DE EVALUACIÓN PERIÓDICA — {period.name.toUpperCase()} (Ponderación: {period.weight_percentage}%)
          </div>

          {/* Official Sealed vs Provisional Badge */}
          <div style={{ marginTop: '0.75rem', display: 'flex', justifyContent: 'center' }}>
            {period.is_closed ? (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  backgroundColor: '#ECFDF5',
                  color: '#065F46',
                  border: '1px solid #6EE7B7',
                  borderRadius: '9999px',
                  padding: '0.25rem 0.875rem',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  letterSpacing: '0.04em',
                }}
              >
                🟢 BOLETÍN OFICIAL SELLADO INSTITUCIONALMENTE
              </span>
            ) : (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  backgroundColor: '#FFFBEB',
                  color: '#92400E',
                  border: '1px solid #FCD34D',
                  borderRadius: '9999px',
                  padding: '0.25rem 0.875rem',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  letterSpacing: '0.04em',
                }}
              >
                🟡 INFORME PROVISIONAL (PERÍODO EN CURSO)
              </span>
            )}
          </div>
        </div>

        {/* Student Identification Info Card */}
        <div
          style={{
            backgroundColor: '#F8FAFC',
            border: '1px solid #E2E8F0',
            borderRadius: '8px',
            padding: '0.875rem 1.25rem',
            marginBottom: '1.5rem',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '0.75rem 1.25rem',
            fontSize: '0.8125rem',
          }}
        >
          <div>
            <span style={{ color: '#64748B', display: 'block', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Estudiante
            </span>
            <strong style={{ color: '#0F172A', fontSize: '0.9375rem' }}>{student.full_name}</strong>
          </div>
          <div>
            <span style={{ color: '#64748B', display: 'block', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Documento / SIMAT
            </span>
            <span style={{ color: '#1E293B', fontWeight: 600 }}>
              {student.document_type ? `${student.document_type} ` : ''}{student.document_number || '—'}
              {student.simat_code && ` • SIMAT: ${student.simat_code}`}
            </span>
          </div>
          <div>
            <span style={{ color: '#64748B', display: 'block', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Grado y Grupo
            </span>
            <span style={{ color: '#1E293B', fontWeight: 600 }}>
              {group.grade_name ? `${group.grade_name} — ` : ''}{group.name}
            </span>
          </div>
          <div>
            <span style={{ color: '#64748B', display: 'block', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Sede Educativa
            </span>
            <span style={{ color: '#1E293B', fontWeight: 600 }}>{campus.name}</span>
          </div>
        </div>

        {/* Academic Summary KPIs */}
        <div
          className="report-summary-card"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
            gap: '0.75rem',
            marginBottom: '1.5rem',
          }}
        >
          <div
            style={{
              backgroundColor: summaryLevelStyle.bg,
              border: `1px solid ${summaryLevelStyle.border}`,
              borderRadius: '8px',
              padding: '0.75rem',
              textAlign: 'center',
            }}
          >
            <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: summaryLevelStyle.text, textTransform: 'uppercase', display: 'block' }}>
              Promedio Período
            </span>
            <strong style={{ fontSize: '1.35rem', fontWeight: 800, color: summaryLevelStyle.text }}>
              {summary.average_score.toFixed(2)}
            </strong>
          </div>

          <div
            style={{
              backgroundColor: summaryLevelStyle.bg,
              border: `1px solid ${summaryLevelStyle.border}`,
              borderRadius: '8px',
              padding: '0.75rem',
              textAlign: 'center',
            }}
          >
            <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: summaryLevelStyle.text, textTransform: 'uppercase', display: 'block' }}>
              Desempeño SIEE
            </span>
            <strong style={{ fontSize: '1.1rem', fontWeight: 800, color: summaryLevelStyle.text }}>
              {summaryLevelStyle.label}
            </strong>
          </div>

          <div
            style={{
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              borderRadius: '8px',
              padding: '0.75rem',
              textAlign: 'center',
            }}
          >
            <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', display: 'block' }}>
              Puesto en el Grupo
            </span>
            <strong style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
              {summary.rank} <span style={{ fontSize: '0.75rem', fontWeight: 500, color: '#64748B' }}>de {summary.total_students}</span>
            </strong>
          </div>

          <div
            style={{
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              borderRadius: '8px',
              padding: '0.75rem',
              textAlign: 'center',
            }}
          >
            <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', display: 'block' }}>
              Aprobadas / Reprobadas
            </span>
            <strong style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0F172A' }}>
              <span style={{ color: '#15803D' }}>{summary.passed_subjects}</span> /{' '}
              <span style={{ color: summary.failed_subjects > 0 ? '#B91C1C' : '#64748B' }}>
                {summary.failed_subjects}
              </span>
            </strong>
          </div>

          <div
            style={{
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              borderRadius: '8px',
              padding: '0.75rem',
              textAlign: 'center',
            }}
          >
            <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', display: 'block' }}>
              Inasistencias
            </span>
            <strong style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0F172A' }}>
              {summary.total_absences}{' '}
              <span style={{ fontSize: '0.7rem', fontWeight: 500, color: '#64748B' }}>
                ({summary.unexcused_absences} inj.)
              </span>
            </strong>
          </div>
        </div>

        {/* 3. Detailed Subject Grades Table */}
        <div style={{ overflowX: 'auto', marginBottom: '2rem' }}>
          <table className="report-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
            <thead>
              <tr style={{ backgroundColor: '#F1F5F9', borderBottom: '2px solid #CBD5E1', textAlign: 'left' }}>
                <th style={{ padding: '0.625rem 0.75rem', width: '30%' }}>Área / Asignatura</th>
                <th style={{ padding: '0.625rem 0.5rem', width: '6%', textAlign: 'center' }}>I.H.</th>
                <th style={{ padding: '0.625rem 0.5rem', width: '10%', textAlign: 'center' }}>Calculada</th>
                <th style={{ padding: '0.625rem 0.5rem', width: '10%', textAlign: 'center' }}>Definitiva</th>
                <th style={{ padding: '0.625rem 0.75rem', width: '14%', textAlign: 'center' }}>Desempeño</th>
                <th style={{ padding: '0.625rem 0.5rem', width: '8%', textAlign: 'center' }}>Fallas</th>
                <th style={{ padding: '0.625rem 0.75rem', width: '22%' }}>Docente Asignado</th>
              </tr>
            </thead>
            <tbody>
              {subjects.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '1.5rem', textAlign: 'center', color: '#64748B' }}>
                    No se registran calificaciones asentadas para este período.
                  </td>
                </tr>
              ) : (
                subjects.map((sub) => {
                  const badge = getLevelBadge(sub.performance_level)
                  return (
                    <React.Fragment key={sub.subject_id}>
                      <tr className="avoid-break" style={{ borderBottom: '1px solid #E2E8F0', backgroundColor: '#FFFFFF' }}>
                        <td style={{ padding: '0.625rem 0.75rem', verticalAlign: 'top' }}>
                          <div style={{ fontWeight: 700, color: '#0F172A' }}>{sub.subject_name}</div>
                          <div style={{ fontSize: '0.725rem', color: '#64748B' }}>{sub.area_name}</div>
                        </td>
                        <td style={{ padding: '0.625rem 0.5rem', textAlign: 'center', color: '#475569', verticalAlign: 'top' }}>
                          {sub.weekly_hours}h
                        </td>
                        <td style={{ padding: '0.625rem 0.5rem', textAlign: 'center', color: '#64748B', verticalAlign: 'top' }}>
                          {sub.calculated_score.toFixed(2)}
                        </td>
                        <td
                          style={{
                            padding: '0.625rem 0.5rem',
                            textAlign: 'center',
                            fontWeight: 800,
                            fontSize: '0.9375rem',
                            color: sub.is_passed ? '#0F172A' : '#B91C1C',
                            verticalAlign: 'top',
                          }}
                        >
                          {sub.final_score.toFixed(2)}
                        </td>
                        <td style={{ padding: '0.625rem 0.75rem', textAlign: 'center', verticalAlign: 'top' }}>
                          <span
                            style={{
                              display: 'inline-block',
                              padding: '0.15rem 0.5rem',
                              borderRadius: '4px',
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              backgroundColor: badge.bg,
                              color: badge.text,
                              border: `1px solid ${badge.border}`,
                            }}
                          >
                            {badge.label}
                          </span>
                        </td>
                        <td style={{ padding: '0.625rem 0.5rem', textAlign: 'center', color: '#475569', verticalAlign: 'top' }}>
                          {sub.total_absences > 0 ? (
                            <span>
                              {sub.total_absences}
                              {sub.unexcused_absences > 0 && ` (${sub.unexcused_absences}i)`}
                            </span>
                          ) : (
                            '0'
                          )}
                        </td>
                        <td style={{ padding: '0.625rem 0.75rem', fontSize: '0.75rem', color: '#334155', verticalAlign: 'top' }}>
                          {sub.teacher_name || 'No asignado'}
                        </td>
                      </tr>

                      {/* Pedagogical Observations & Adjustment Reason (if any) */}
                      {(sub.adjustment_reason || sub.observations || sub.achievements.length > 0 || sub.recoveries.length > 0) && (
                        <tr className="avoid-break" style={{ borderBottom: '2px solid #CBD5E1', backgroundColor: '#F8FAFC' }}>
                          <td colSpan={7} style={{ padding: '0.5rem 0.75rem', fontSize: '0.75rem', color: '#475569' }}>
                            {/* Adjustment Reason */}
                            {sub.adjustment_reason && (
                              <div style={{ marginBottom: '0.25rem' }}>
                                <strong style={{ color: '#B45309' }}>Motivo de Ajuste Pedagógico:</strong> {sub.adjustment_reason}
                              </div>
                            )}

                            {/* Qualitative Achievements */}
                            {sub.achievements.length > 0 && (
                              <div style={{ marginBottom: '0.25rem' }}>
                                <strong style={{ color: '#1E3A8A' }}>Logros / Descriptores:</strong>
                                <ul style={{ margin: '0.15rem 0 0.25rem 1.25rem', padding: 0 }}>
                                  {sub.achievements.map((ach, idx) => (
                                    <li key={idx}>
                                      {ach.code ? `[${ach.code}] ` : ''}{ach.description}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* Remedial Recovery Records */}
                            {sub.recoveries.length > 0 && (
                              <div style={{ marginBottom: '0.25rem', color: '#15803D' }}>
                                <strong>Historial de Nivelación / Recuperación:</strong>
                                {sub.recoveries.map((rec, rIdx) => (
                                  <div key={rIdx} style={{ marginLeft: '0.5rem' }}>
                                    • Nota inicial: <strong>{rec.initial_score.toFixed(2)}</strong> | Examen: <strong>{rec.recovery_score.toFixed(2)}</strong> | Tope SIEE: <strong>{rec.applied_cap.toFixed(2)}</strong> → Nota Asentada: <strong>{rec.final_adjusted_score.toFixed(2)}</strong> ({rec.recovery_date}{rec.act_number ? ` - Acta: ${rec.act_number}` : ''})
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* Teacher observations */}
                            {sub.observations && (
                              <div>
                                <strong>Observaciones:</strong> {sub.observations}
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* 4. Institutional Signatures Area (Legal validity for print) */}
        <div
          className="signature-block avoid-break"
          style={{
            marginTop: '3rem',
            paddingTop: '1.5rem',
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '2rem',
            textAlign: 'center',
            fontSize: '0.75rem',
          }}
        >
          <div>
            <div style={{ borderTop: '1px solid #0F172A', paddingTop: '0.35rem', fontWeight: 700, color: '#0F172A' }}>
              RECTOR(A) / DIRECTOR(A)
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748B' }}>Firma Autorizada</div>
          </div>
          <div>
            <div style={{ borderTop: '1px solid #0F172A', paddingTop: '0.35rem', fontWeight: 700, color: '#0F172A' }}>
              DIRECTOR(A) DE GRUPO
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748B' }}>{group.name}</div>
          </div>
          <div>
            <div style={{ borderTop: '1px solid #0F172A', paddingTop: '0.35rem', fontWeight: 700, color: '#0F172A' }}>
              SECRETARÍA ACADÉMICA
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748B' }}>Sello Institucional</div>
          </div>
        </div>
      </div>
    </div>
  )
}
