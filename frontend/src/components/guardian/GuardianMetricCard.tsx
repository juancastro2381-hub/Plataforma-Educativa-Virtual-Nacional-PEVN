/**
 * PEVN Frontend — Guardian Metric Card Component
 *
 * KPI summary card tailored for family monitoring with curated color tokens.
 */

import React from 'react'

export type MetricAccent = 'indigo' | 'emerald' | 'amber' | 'rose' | 'sky' | 'purple'

interface Props {
  title: string
  value: string | number
  subtitle?: string
  icon: string
  accent?: MetricAccent
  onClick?: () => void
}

const ACCENT_STYLES: Record<MetricAccent, { bg: string; text: string; border: string }> = {
  indigo: { bg: '#EEF2FF', text: '#4338CA', border: '#C7D2FE' },
  emerald: { bg: '#ECFDF5', text: '#047857', border: '#A7F3D0' },
  amber: { bg: '#FFFBEB', text: '#B45309', border: '#FDE68A' },
  rose: { bg: '#FFF1F2', text: '#BE123C', border: '#FECDD3' },
  sky: { bg: '#F0F9FF', text: '#0369A1', border: '#BAE6FD' },
  purple: { bg: '#FAF5FF', text: '#6B21A8', border: '#E9D5FF' },
}

export const GuardianMetricCard: React.FC<Props> = ({
  title,
  value,
  subtitle,
  icon,
  accent = 'indigo',
  onClick,
}) => {
  const styles = ACCENT_STYLES[accent]

  return (
    <div
      onClick={onClick}
      style={{
        backgroundColor: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: '14px',
        padding: '1.25rem',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 150ms ease, box-shadow 150ms ease',
      }}
    >
      <div
        style={{
          width: '52px',
          height: '52px',
          borderRadius: '12px',
          backgroundColor: styles.bg,
          border: `1px solid ${styles.border}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.5rem',
          flexShrink: 0,
        }}
      >
        {icon}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          {title}
        </div>
        <div style={{ fontSize: '1.625rem', fontWeight: 800, color: '#0F172A', lineHeight: 1.2, margin: '0.2rem 0' }}>
          {value}
        </div>
        {subtitle && (
          <div style={{ fontSize: '0.75rem', color: '#64748B', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {subtitle}
          </div>
        )}
      </div>
    </div>
  )
}
