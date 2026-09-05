/**
 * PEVN Frontend — Official Year-End Cumulative Report Card Component (Phase 16E)
 *
 * Authoritative annual cumulative report card (Informe Final de Evaluación y Promoción):
 * - Displays multi-period grade breakdown matrix (P1, P2, P3, P4)
 * - Annual weighted cumulative averages and SIEE performance level
 * - Official Promotion / Graduation Dictamen from Evaluation Commission
 * - Strict semantic preservation: PROMOVIDO != GRADUADO (DECISION-16-04)
 * - Official Commission Act reference (Acta de Evaluación y Promoción)
 * - Zero-binary native print/PDF presentation with signature placeholders
 */

import React from 'react'
import type { YearEndReportCardResponse, SieePerformanceLevel } from '@/types/evaluation'
import './ReportCardPrint.css'

interface Props {
  reportCard: YearEndReportCardResponse
  onPrint?: () => void
  showActions?: boolean
}

export const OfficialYearEndReportCard: React.FC<Props> = ({
  reportCard,
  onPrint,
  showActions = true,
}) => {
  const { institution, campus, student, academic_year, group, summary, promotion, subjects } =
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

  const getPromotionBadge = (status: string) => {
    switch (status) {
      case 'GRADUADO':
        return {
          bg: '#FAF5FF',
          border: '#D8B4FE',
          text: '#6B21A8',
          icon: '🎓',
          title: 'GRADUADO — BACHILLER ACADÉMICO',
          description: 'Cumplió a cabalidad con todos los requisitos académicos del ciclo de Educación Media.',
        }
      case 'PROMOVIDO':
        return {
          bg: '#ECFDF5',
          border: '#6EE7B7',
          text: '#065F46',
          icon: '🟢',
          title: 'PROMOVIDO AL SIGUIENTE GRADO',
          description: 'Aprobó satisfactoriamente las áreas fundamentales según los criterios del SIEE institucional.',
        }
      case 'NO_PROMOVIDO':
        return {
          bg: '#FEF2F2',
          border: '#FCA5A5',
          text: '#991B1B',
          icon: '🔴',
          title: 'NO PROMOVIDO / REINICIA GRADO',
          description: 'No superó los criterios mínimos de promoción establecidos en el reglamento del SIEE.',
        }
      case 'PENDIENTE_NIVELACION':
        return {
          bg: '#FFFBEB',
          border: '#FCD34D',
          text: '#92400E',
          icon: '🟠',
          title: 'PENDIENTE DE NIVELACIÓN EXTRAORDINARIA',
          description: 'Habilitado para presentar evaluaciones de recuperación de fin de año.',
        }
      default:
        return {
          bg: '#F8FAFC',
          border: '#E2E8F0',
          text: '#334155',
          icon: '🔵',
          title: 'EVALUACIÓN ORDINARIA EN CURSO',
          description: 'Pendiente de sesión de la Comisión de Evaluación y Promoción.',
        }
    }
  }

  const promoBadge = getPromotionBadge(promotion.status)
  const summaryLevelStyle = getLevelBadge(summary.performance_level)

  // Extract all distinct period numbers from subjects
  const allPeriodNumbers = Array.from(
    new Set(
      subjects.flatMap((s) => Object.keys(s.period_grades).map((k) => Number(k)))
    )
  ).sort((a, b) => a - b)

  return (
    <div className="official-report-document" style={{ width: '100%', maxWidth: '960px', margin: '0 auto' }}>
      {/* 1. Action Toolbar (Screen only) */}
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
              Informe Final Acumulado y Dictamen de Promoción — Año Lectivo {academic_year.year}
            </span>
            <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
              {student.full_name} • {group.name}
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

      {/* 2. Document Body */}
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
          <div style={{ fontSize: '0.875rem', fontWeight: 800, color: '#1E3A8A', marginTop: '0.35rem' }}>
            INFORME FINAL DE EVALUACIÓN ACADÉMICA Y DICTAMEN DE PROMOCIÓN ANUAL
          </div>
        </div>

        {/* Student Identification Block */}
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
              {student.document_number || '—'}
              {student.simat_code && ` • SIMAT: ${student.simat_code}`}
            </span>
          </div>
          <div>
            <span style={{ color: '#64748B', display: 'block', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Grado y Salón
            </span>
            <span style={{ color: '#1E293B', fontWeight: 600 }}>
              {group.grade_name ? `${group.grade_name} — ` : ''}{group.name}
            </span>
          </div>
          <div>
            <span style={{ color: '#64748B', display: 'block', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Año Escolar
            </span>
            <span style={{ color: '#1E293B', fontWeight: 600 }}>{academic_year.year} ({academic_year.status || 'Activo'})</span>
          </div>
        </div>

        {/* 3. Official Promotion / Graduation Dictamen Banner */}
        <div
          className="report-summary-card avoid-break"
          style={{
            backgroundColor: promoBadge.bg,
            border: `2px solid ${promoBadge.border}`,
            borderRadius: '10px',
            padding: '1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '1rem',
          }}
        >
          <span style={{ fontSize: '2rem', lineHeight: 1 }}>{promoBadge.icon}</span>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 800, color: promoBadge.text }}>
                {promoBadge.title}
              </h2>
              {promotion.acta_number && (
                <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: promoBadge.text, backgroundColor: '#FFFFFF', padding: '0.2rem 0.6rem', borderRadius: '6px', border: `1px solid ${promoBadge.border}` }}>
                  Acta Comisión: #{promotion.acta_number}
                </span>
              )}
            </div>
            <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.8125rem', color: '#334155' }}>
              {promoBadge.description}
            </p>
            {(promotion.decision_date || promotion.observations) && (
              <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#475569', borderTop: `1px solid ${promoBadge.border}`, paddingTop: '0.35rem' }}>
                {promotion.decision_date && <span><strong>Fecha de Dictamen:</strong> {promotion.decision_date} • </span>}
                {promotion.observations && <span><strong>Observaciones de Comisión:</strong> {promotion.observations}</span>}
              </div>
            )}
          </div>
        </div>

        {/* 4. Annual Cumulative KPIs */}
        <div
          className="report-summary-card"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
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
              Promedio Acumulado Anual
            </span>
            <strong style={{ fontSize: '1.35rem', fontWeight: 800, color: summaryLevelStyle.text }}>
              {summary.cumulative_average.toFixed(2)}
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
              Desempeño Anual SIEE
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
              Asignaturas Reprobadas
            </span>
            <strong style={{ fontSize: '1.25rem', fontWeight: 800, color: summary.failed_subjects_count > 0 ? '#B91C1C' : '#15803D' }}>
              {summary.failed_subjects_count}
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
              Total Asignaturas
            </span>
            <strong style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
              {subjects.length}
            </strong>
          </div>
        </div>

        {/* 5. Multi-Period Grades Breakdown Matrix */}
        <div style={{ overflowX: 'auto', marginBottom: '2rem' }}>
          <table className="report-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
            <thead>
              <tr style={{ backgroundColor: '#F1F5F9', borderBottom: '2px solid #CBD5E1', textAlign: 'left' }}>
                <th style={{ padding: '0.625rem 0.75rem', minWidth: '220px' }}>Área / Asignatura</th>
                {allPeriodNumbers.map((pNum) => (
                  <th key={pNum} style={{ padding: '0.625rem 0.5rem', width: '70px', textAlign: 'center' }}>
                    P{pNum}
                  </th>
                ))}
                <th style={{ padding: '0.625rem 0.5rem', width: '85px', textAlign: 'center', backgroundColor: '#E2E8F0' }}>
                  Definitiva
                </th>
                <th style={{ padding: '0.625rem 0.75rem', width: '110px', textAlign: 'center' }}>
                  Desempeño
                </th>
                <th style={{ padding: '0.625rem 0.5rem', width: '65px', textAlign: 'center' }}>
                  Fallas
                </th>
              </tr>
            </thead>
            <tbody>
              {subjects.length === 0 ? (
                <tr>
                  <td colSpan={4 + allPeriodNumbers.length} style={{ padding: '1.5rem', textAlign: 'center', color: '#64748B' }}>
                    No se registran notas de período para este año escolar.
                  </td>
                </tr>
              ) : (
                subjects.map((sub) => {
                  const badge = getLevelBadge(sub.performance_level)
                  return (
                    <tr key={sub.subject_id} className="avoid-break" style={{ borderBottom: '1px solid #E2E8F0', backgroundColor: '#FFFFFF' }}>
                      <td style={{ padding: '0.625rem 0.75rem' }}>
                        <div style={{ fontWeight: 700, color: '#0F172A' }}>{sub.subject_name}</div>
                        <div style={{ fontSize: '0.725rem', color: '#64748B' }}>{sub.area_name}</div>
                      </td>

                      {/* Period columns */}
                      {allPeriodNumbers.map((pNum) => {
                        const pGrade = sub.period_grades[pNum]
                        return (
                          <td key={pNum} style={{ padding: '0.625rem 0.5rem', textAlign: 'center', color: '#334155' }}>
                            {pGrade ? Number(pGrade.score).toFixed(2) : '—'}
                          </td>
                        )
                      })}

                      {/* Final Annual Score */}
                      <td
                        style={{
                          padding: '0.625rem 0.5rem',
                          textAlign: 'center',
                          fontWeight: 800,
                          fontSize: '0.9375rem',
                          backgroundColor: '#F8FAFC',
                          color: '#0F172A',
                        }}
                      >
                        {sub.final_annual_score.toFixed(2)}
                      </td>

                      {/* Performance Level */}
                      <td style={{ padding: '0.625rem 0.75rem', textAlign: 'center' }}>
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

                      {/* Absences */}
                      <td style={{ padding: '0.625rem 0.5rem', textAlign: 'center', color: '#475569' }}>
                        {sub.total_absences}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* 6. Institutional Signatures Area */}
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
              RECTOR(A) INSTITUCIONAL
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748B' }}>Firma y Sello Oficial</div>
          </div>
          <div>
            <div style={{ borderTop: '1px solid #0F172A', paddingTop: '0.35rem', fontWeight: 700, color: '#0F172A' }}>
              COMISIÓN DE EVALUACIÓN
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748B' }}>Presidente de Comisión</div>
          </div>
          <div>
            <div style={{ borderTop: '1px solid #0F172A', paddingTop: '0.35rem', fontWeight: 700, color: '#0F172A' }}>
              SECRETARÍA ACADÉMICA
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748B' }}>Libro de Calificaciones</div>
          </div>
        </div>
      </div>
    </div>
  )
}
