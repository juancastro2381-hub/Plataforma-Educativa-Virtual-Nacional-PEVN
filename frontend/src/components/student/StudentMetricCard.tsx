/**
 * PEVN Frontend — Student Metric Card Component
 *
 * Displays a concise KPI metric with icon, value, label, and contextual accent.
 */

import React from 'react'

interface StudentMetricCardProps {
  icon: string
  label: string
  value: string | number
  subtext?: string
  accentColor?: string
  onClick?: () => void
  badge?: {
    text: string
    variant: 'danger' | 'warning' | 'success' | 'info'
  }
}

export const StudentMetricCard: React.FC<StudentMetricCardProps> = ({
  icon,
  label,
  value,
  subtext,
  accentColor = '#3B82F6',
  onClick,
  badge,
}) => {
  const badgeStyles = {
    danger: { bg: '#FEE2E2', color: '#991B1B' },
    warning: { bg: '#FEF3C7', color: '#92400E' },
    success: { bg: '#DCFCE7', color: '#15803D' },
    info: { bg: '#EFF6FF', color: '#1D4ED8' },
  }

  return (
    <div
      onClick={onClick}
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '12px',
        border: '1px solid #E2E8F0',
        padding: '1.25rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease',
        position: 'relative',
        overflow: 'hidden',
      }}
      onMouseEnter={(e) => {
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(-2px)'
          e.currentTarget.style.boxShadow = '0 6px 12px rgba(0,0,0,0.08)'
          e.currentTarget.style.borderColor = accentColor
        }
      }}
      onMouseLeave={(e) => {
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(0)'
          e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.05)'
          e.currentTarget.style.borderColor = '#E2E8F0'
        }
      }}
    >
      {/* Top Color Accent Line */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          backgroundColor: accentColor,
        }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
        <div
          style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            backgroundColor: `${accentColor}15`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.35rem',
          }}
        >
          {icon}
        </div>

        {badge && (
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '0.2rem 0.5rem',
              borderRadius: '9999px',
              backgroundColor: badgeStyles[badge.variant].bg,
              color: badgeStyles[badge.variant].color,
            }}
          >
            {badge.text}
          </span>
        )}
      </div>

      <div>
        <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', lineHeight: 1.1 }}>
          {value}
        </div>
        <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#64748B', marginTop: '0.25rem' }}>
          {label}
        </div>
        {subtext && (
          <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '0.25rem' }}>
            {subtext}
          </div>
        )}
      </div>
    </div>
  )
}
