/**
 * PEVN Frontend — Guardian Header Component
 *
 * Displays the authenticated guardian's identity, contact information,
 * institutional affiliation, and total linked children count.
 */

import React from 'react'
import type { GuardianProfileResponse } from '@/types/guardian'

interface Props {
  profile: GuardianProfileResponse | null
  loading?: boolean
  onRefresh?: () => void
}

export const GuardianHeader: React.FC<Props> = ({ profile, loading, onRefresh }) => {
  return (
    <div
      style={{
        backgroundColor: '#0F172A',
        color: '#FFFFFF',
        borderRadius: '16px',
        padding: '1.75rem 2rem',
        marginBottom: '1.75rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1.25rem',
        boxShadow: '0 10px 25px -5px rgba(15, 23, 42, 0.2)',
        border: '1px solid #1E293B',
      }}
    >
      <div style={{ flex: 1, minWidth: '280px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              backgroundColor: 'rgba(244, 114, 182, 0.2)',
              color: '#F472B6',
              padding: '0.25rem 0.75rem',
              borderRadius: '9999px',
              border: '1px solid rgba(244, 114, 182, 0.3)',
            }}
          >
            Portal de Acudientes y Familias
          </span>

          {profile && (
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                backgroundColor: 'rgba(56, 189, 248, 0.15)',
                color: '#38BDF8',
                padding: '0.25rem 0.65rem',
                borderRadius: '9999px',
                border: '1px solid rgba(56, 189, 248, 0.25)',
              }}
            >
              👨‍👩‍👧 {profile.total_linked_students} {profile.total_linked_students === 1 ? 'Hijo / Tutorado' : 'Hijos / Tutorados'}
            </span>
          )}
        </div>

        <h1
          style={{
            margin: '0.25rem 0 0.5rem 0',
            fontSize: '1.625rem',
            fontWeight: 800,
            color: '#FFFFFF',
            lineHeight: 1.25,
          }}
        >
          {profile ? `¡Bienvenido(a), ${profile.full_name}!` : 'Portal de Acudientes y Familias'}
        </h1>

        <div
          style={{
            fontSize: '0.875rem',
            color: '#94A3B8',
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: '1rem',
          }}
        >
          {profile ? (
            <>
              <span>🏫 <strong>{profile.institution_name}</strong></span>
              <span>📄 <strong>Doc:</strong> {profile.document_type} {profile.document_number}</span>
              <span>📞 <strong>Tel:</strong> {profile.phone}</span>
              {profile.email && <span>✉️ {profile.email}</span>}
            </>
          ) : (
            <span>Seguimiento académico y acompañamiento familiar integral • PEVN</span>
          )}
        </div>
      </div>

      {onRefresh && (
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            color: '#FFFFFF',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            fontSize: '0.8125rem',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'background-color 150ms',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}
        >
          <span>🔄</span>
          <span>{loading ? 'Actualizando...' : 'Actualizar'}</span>
        </button>
      )}
    </div>
  )
}
