/**
 * PEVN Frontend — Guardian Child Card Component
 *
 * Rich student summary card for the "Mis Hijos" view with complete official context.
 */

import React from 'react'
import type { GuardianChildItemResponse } from '@/types/guardian'

interface Props {
  child: GuardianChildItemResponse
  isSelected: boolean
  onSelect: (studentId: string) => void
}

export const GuardianChildCard: React.FC<Props> = ({ child, isSelected, onSelect }) => {
  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '16px',
        border: isSelected ? '2px solid #0F172A' : '1px solid #E2E8F0',
        padding: '1.5rem',
        boxShadow: isSelected ? '0 10px 15px -3px rgba(15, 23, 42, 0.08)' : '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        transition: 'transform 150ms ease, box-shadow 150ms ease',
      }}
    >
      <div>
        {/* Card Header with Badges */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '14px',
                backgroundColor: isSelected ? '#0F172A' : '#EFF6FF',
                color: isSelected ? '#FFFFFF' : '#1D4ED8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: '1.125rem',
              }}
            >
              {child.first_name[0]}
              {child.last_name[0]}
            </div>

            <div>
              <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 800, color: '#0F172A' }}>
                {child.full_name}
              </h3>
              <div style={{ fontSize: '0.75rem', color: '#64748B', fontFamily: 'monospace', marginTop: '0.15rem' }}>
                SIMAT: <strong>{child.code_simat}</strong> • {child.document_type}: {child.document_number}
              </div>
            </div>
          </div>

          <span
            style={{
              padding: '0.2rem 0.6rem',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: 700,
              backgroundColor: '#DCFCE7',
              color: '#15803D',
            }}
          >
            {child.enrollment_status || 'MATRICULADO'}
          </span>
        </div>

        {/* Academic Details Grid */}
        <div
          style={{
            backgroundColor: '#F8FAFC',
            borderRadius: '10px',
            padding: '0.875rem 1rem',
            border: '1px solid #E2E8F0',
            fontSize: '0.8125rem',
            color: '#334155',
            marginBottom: '1.25rem',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '0.5rem',
          }}
        >
          <div>
            <span style={{ color: '#64748B' }}>Grado / Grupo:</span>
            <div style={{ fontWeight: 700, color: '#0F172A' }}>
              {child.grade_name || 'Grado N/A'} • Grupo {child.group_name || 'N/A'}
            </div>
          </div>

          <div>
            <span style={{ color: '#64748B' }}>Sede:</span>
            <div style={{ fontWeight: 700, color: '#0F172A' }}>
              {child.campus_name || 'Sede Principal'}
            </div>
          </div>

          <div>
            <span style={{ color: '#64748B' }}>Parentesco:</span>
            <div style={{ fontWeight: 700, color: '#7E22CE', textTransform: 'capitalize' }}>
              {child.relationship_type.toLowerCase()}
            </div>
          </div>

          <div>
            <span style={{ color: '#64748B' }}>Año Lectivo:</span>
            <div style={{ fontWeight: 700, color: '#0F172A' }}>
              {child.academic_year_name || '2026'}
            </div>
          </div>
        </div>

        {/* Contact Authorizations */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.25rem' }}>
          {child.is_primary_contact && (
            <span style={{ fontSize: '0.7rem', fontWeight: 700, backgroundColor: '#EFF6FF', color: '#1E40AF', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
              ⭐ Contacto Principal
            </span>
          )}
          {child.is_authorized_pickup && (
            <span style={{ fontSize: '0.7rem', fontWeight: 700, backgroundColor: '#F0FDF4', color: '#166534', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
              🛡️ Autorizado Retiro
            </span>
          )}
        </div>
      </div>

      {/* Select Action CTA */}
      <button
        type="button"
        onClick={() => onSelect(child.student_id)}
        style={{
          width: '100%',
          padding: '0.75rem 1rem',
          borderRadius: '8px',
          backgroundColor: isSelected ? '#0F172A' : '#1E293B',
          color: '#FFFFFF',
          border: 'none',
          fontSize: '0.875rem',
          fontWeight: 700,
          cursor: 'pointer',
          transition: 'background-color 150ms ease',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem',
        }}
      >
        <span>{isSelected ? '✓ Estudiante Activo' : `Monitorear a ${child.first_name}`}</span>
        <span>→</span>
      </button>
    </div>
  )
}
