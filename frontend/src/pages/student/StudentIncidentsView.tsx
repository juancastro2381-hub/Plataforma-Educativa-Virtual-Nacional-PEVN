/**
 * PEVN Frontend — Student Coexistence & Observador View (Phase 15)
 *
 * Personal Observador del Estudiante & Formative Coexistence Records.
 * Strict compliance with DECISION-15-01:
 * - Student only views their own records marked `is_visible_to_student = true`
 * - Clear formative emphasis: Pedagogical measures & commitments
 */

import React, { useEffect, useState } from 'react'
import { communicationApi } from '@/services/communication'
import type {
  CoexistenceSituationType,
  IncidentStatus,
  StudentIncidentItem,
} from '@/types/communication'

interface Props {
  onBackToDashboard?: () => void
}

const SITUATION_TYPE_META: Record<
  CoexistenceSituationType,
  { label: string; badge: string; bg: string; color: string; border: string; desc: string }
> = {
  TIPO_I: {
    label: 'Tipo I — Situación Leve / Cotidiana',
    badge: 'Tipo I',
    bg: '#FEF3C7',
    color: '#B45309',
    border: '#FDE68A',
    desc: 'Conflictos cotidianos manejados formativamente en el aula de clase.',
  },
  TIPO_II: {
    label: 'Tipo II — Situación Grave (Acoso / Agresión)',
    badge: 'Tipo II',
    bg: '#FFEDD5',
    color: '#C2410C',
    border: '#FED7AA',
    desc: 'Conductas de agresión o acoso que afectan la convivencia sin constituir delito.',
  },
  TIPO_III: {
    label: 'Tipo III — Situación Gravísima (Presunto Delito)',
    badge: 'Tipo III',
    bg: '#FEE2E2',
    color: '#B91C1C',
    border: '#FCA5A5',
    desc: 'Situaciones de presunta vulneración de derechos remitidas a comité de convivencia.',
  },
}

const STATUS_META: Record<IncidentStatus, { label: string; bg: string; color: string }> = {
  ABIERTO: { label: 'Abierto', bg: '#FEF2F2', color: '#DC2626' },
  EN_SEGUIMIENTO: { label: 'En Seguimiento Pedagógico', bg: '#EFF6FF', color: '#2563EB' },
  CERRADO: { label: 'Cerrado y Resuelto', bg: '#F0FDF4', color: '#16A34A' },
}

export const StudentIncidentsView: React.FC<Props> = ({ onBackToDashboard: _onBackToDashboard }) => {
  const [incidents, setIncidents] = useState<StudentIncidentItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const fetchIncidents = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await communicationApi.getStudentIncidents()
      setIncidents(res.items)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al consultar mi observador de convivencia.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchIncidents()
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Bar */}
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
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '1.5rem' }}>⚖️</span>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
              Mi Observador de Convivencia
            </h2>
          </div>
          <p style={{ margin: '0.35rem 0 0 0', color: '#64748B', fontSize: '0.875rem' }}>
            Registro formativo de acuerdos, compromisos pedagógicos y seguimiento al manual de convivencia.
          </p>
        </div>

        <button
          onClick={() => void fetchIncidents()}
          disabled={loading}
          style={{
            backgroundColor: '#F8FAFC',
            border: '1px solid #CBD5E1',
            borderRadius: '8px',
            padding: '0.5rem 1rem',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: '#334155',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}
        >
          <span>🔄</span> Actualizar
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div
          style={{
            backgroundColor: '#FEE2E2',
            border: '1px solid #FCA5A5',
            color: '#991B1B',
            borderRadius: '12px',
            padding: '1rem',
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#64748B' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>⏳</div>
          <p>Consultando el observador estudiantil...</p>
        </div>
      ) : incidents.length === 0 ? (
        /* Exemplary Student Empty State */
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '3.5rem 1.5rem',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>🌟</div>
          <h3 style={{ margin: '0 0 0.5rem 0', color: '#166534', fontWeight: 800 }}>
            ¡Excelente Historial de Convivencia!
          </h3>
          <p style={{ margin: 0, color: '#475569', fontSize: '0.9375rem', maxWidth: '520px', marginLeft: 'auto', marginRight: 'auto', lineHeight: 1.5 }}>
            No registras anotaciones de convivencia escolar ni llamados de atención disciplinarios. Mantienes un comportamiento ejemplar en tu comunidad educativa.
          </p>
        </div>
      ) : (
        /* Incidents List */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {incidents.map((incident) => {
            const typeMeta = SITUATION_TYPE_META[incident.situation_type] || SITUATION_TYPE_META.TIPO_I
            const statusMeta = STATUS_META[incident.status] || STATUS_META.ABIERTO

            return (
              <div
                key={incident.id}
                style={{
                  backgroundColor: '#FFFFFF',
                  borderRadius: '16px',
                  border: '1px solid #E2E8F0',
                  padding: '1.5rem',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span
                      style={{
                        backgroundColor: typeMeta.bg,
                        color: typeMeta.color,
                        border: `1px solid ${typeMeta.border}`,
                        fontSize: '0.75rem',
                        fontWeight: 800,
                        padding: '0.25rem 0.65rem',
                        borderRadius: '6px',
                      }}
                    >
                      {typeMeta.badge}
                    </span>

                    <span
                      style={{
                        backgroundColor: statusMeta.bg,
                        color: statusMeta.color,
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        padding: '0.25rem 0.6rem',
                        borderRadius: '6px',
                      }}
                    >
                      {statusMeta.label}
                    </span>
                  </div>

                  <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                    📅 {new Date(incident.incident_date).toLocaleDateString('es-CO')}
                  </span>
                </div>

                <div>
                  <h4 style={{ margin: '0 0 0.35rem 0', fontSize: '0.875rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
                    Descripción
                  </h4>
                  <p style={{ margin: 0, color: '#1E293B', fontSize: '0.9375rem', lineHeight: 1.6 }}>
                    {incident.description}
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '12px' }}>
                  <div>
                    <h5 style={{ margin: '0 0 0.25rem 0', fontSize: '0.8125rem', fontWeight: 700, color: '#1D4ED8' }}>
                      Medidas Pedagógicas Formativas
                    </h5>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: '#334155' }}>
                      {incident.pedagogical_measures}
                    </p>
                  </div>

                  {incident.commitments && (
                    <div>
                      <h5 style={{ margin: '0 0 0.25rem 0', fontSize: '0.8125rem', fontWeight: 700, color: '#047857' }}>
                        Mis Compromisos
                      </h5>
                      <p style={{ margin: 0, fontSize: '0.875rem', color: '#334155' }}>
                        {incident.commitments}
                      </p>
                    </div>
                  )}
                </div>

                {/* Follow-ups Timeline */}
                {incident.follow_ups && incident.follow_ups.length > 0 && (
                  <div>
                    <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '0.8125rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
                      Seguimientos y Acuerdos ({incident.follow_ups.length})
                    </h5>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {incident.follow_ups.map((f) => (
                        <div
                          key={f.id}
                          style={{
                            borderLeft: '3px solid #3B82F6',
                            paddingLeft: '0.75rem',
                            fontSize: '0.8125rem',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748B', marginBottom: '0.2rem' }}>
                            <span><strong>{f.author_name}</strong></span>
                            <span>{new Date(f.follow_up_date).toLocaleDateString('es-CO')}</span>
                          </div>
                          <p style={{ margin: 0, color: '#334155' }}>{f.notes}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div
                  style={{
                    borderTop: '1px solid #F1F5F9',
                    paddingTop: '0.75rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '0.75rem',
                    color: '#94A3B8',
                  }}
                >
                  <span>Docente / Directivo: {incident.reporter_name}</span>
                  {incident.closed_at && (
                    <span>Cerrado y Resuelto el {new Date(incident.closed_at).toLocaleDateString('es-CO')}</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
