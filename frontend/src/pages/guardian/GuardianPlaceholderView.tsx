/**
 * PEVN Frontend — Guardian Placeholder View (Phase 14C / Phase 15 Preparation)
 *
 * Clean architectural placeholder for:
 * - Comunicados Institucionales (communications)
 * - Noticias y Boletines del Colegio (news)
 * - Convivencia Escolar y Registro de Incidentes (incidents)
 *
 * Strict Compliance: Zero fabricated data or fake institutional content.
 */

import React from 'react'

interface Props {
  moduleType: 'communications' | 'news' | 'incidents'
  onBackToDashboard?: () => void
}

const MODULE_META: Record<
  'communications' | 'news' | 'incidents',
  { title: string; icon: string; description: string; phaseInfo: string }
> = {
  communications: {
    title: 'Comunicados y Circulares Institucionales',
    icon: '📢',
    description:
      'Canal oficial de mensajería, circulares de rectoría y citaciones personalizadas dirigidas a los padres de familia.',
    phaseInfo:
      'El servicio de mensajería y notificaciones institucionales está programado para su integración oficial con el backend en la Fase 15.',
  },
  news: {
    title: 'Noticias y Eventos Escolares',
    icon: '📰',
    description:
      'Boletín informativo con eventos cívicos, culturales, deportivos y cronograma de actividades de la comunidad educativa.',
    phaseInfo:
      'El motor de noticias y publicaciones institucionales multi-tenant será habilitado junto con el CMS escolar en la Fase 15.',
  },
  incidents: {
    title: 'Convivencia Escolar y Seguimiento Disciplinario',
    icon: '⚖️',
    description:
      'Observaciones pedagógicas de convivencia, reconocimientos por mérito estudiantil y registro formativo del manual de convivencia.',
    phaseInfo:
      'El protocolo de convivencia y comité de mediación escolar se integrará en la Fase 15 con base en la Ley 1620 de Convivencia Escolar.',
  },
}

export const GuardianPlaceholderView: React.FC<Props> = ({
  moduleType,
  onBackToDashboard,
}) => {
  const meta = MODULE_META[moduleType]

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '16px',
        border: '1px solid #E2E8F0',
        padding: '3.5rem 2rem',
        textAlign: 'center',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
        maxWidth: '680px',
        margin: '2rem auto',
      }}
    >
      <div
        style={{
          width: '72px',
          height: '72px',
          borderRadius: '20px',
          backgroundColor: '#F8FAFC',
          border: '1px solid #E2E8F0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '2.5rem',
          margin: '0 auto 1.25rem auto',
        }}
      >
        {meta.icon}
      </div>

      <div
        style={{
          display: 'inline-block',
          fontSize: '0.75rem',
          fontWeight: 800,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          backgroundColor: '#EFF6FF',
          color: '#1D4ED8',
          padding: '0.25rem 0.75rem',
          borderRadius: '9999px',
          marginBottom: '0.75rem',
        }}
      >
        Próximamente • Fase 15
      </div>

      <h2 style={{ margin: '0 0 0.75rem 0', fontSize: '1.375rem', fontWeight: 800, color: '#0F172A' }}>
        {meta.title}
      </h2>

      <p style={{ margin: '0 auto 1.25rem auto', fontSize: '0.875rem', color: '#475569', lineHeight: 1.6 }}>
        {meta.description}
      </p>

      <div
        style={{
          backgroundColor: '#F8FAFC',
          border: '1px dashed #CBD5E1',
          borderRadius: '10px',
          padding: '0.875rem 1.25rem',
          fontSize: '0.8125rem',
          color: '#64748B',
          lineHeight: 1.5,
          marginBottom: '1.75rem',
        }}
      >
        📌 <strong>Arquitectura Preparada:</strong> {meta.phaseInfo}
      </div>

      {onBackToDashboard && (
        <button
          type="button"
          onClick={onBackToDashboard}
          style={{
            padding: '0.625rem 1.25rem',
            borderRadius: '8px',
            backgroundColor: '#0F172A',
            color: '#FFFFFF',
            border: 'none',
            fontSize: '0.875rem',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          ← Volver al Panel de Inicio
        </button>
      )}
    </div>
  )
}
