/**
 * PEVN Frontend — Guardian Profile View (Mi Perfil)
 *
 * Displays the verified identity, institutional affiliation, contact records,
 * and family representation records for the authenticated guardian.
 */

import React from 'react'
import type { GuardianProfileResponse } from '@/types/guardian'
import { GuardianEmptyState } from '@/components/guardian/GuardianEmptyState'
import { GuardianLoadingSkeleton } from '@/components/guardian/GuardianLoadingSkeleton'

interface Props {
  profile: GuardianProfileResponse | null
  loading: boolean
}

export const GuardianProfileView: React.FC<Props> = ({ profile, loading }) => {
  if (loading) {
    return <GuardianLoadingSkeleton type="overview" />
  }

  if (!profile) {
    return (
      <GuardianEmptyState
        icon="👤"
        title="Perfil no disponible"
        description="No fue posible cargar la información de acudiente asociada a su cuenta de usuario."
      />
    )
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      {/* Profile Card */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          border: '1px solid #E2E8F0',
          padding: '2rem',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
        }}
      >
        {/* Profile Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1.25rem',
            paddingBottom: '1.5rem',
            borderBottom: '1px solid #E2E8F0',
            marginBottom: '1.5rem',
            flexWrap: 'wrap',
          }}
        >
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '16px',
              backgroundColor: '#0F172A',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '1.5rem',
            }}
          >
            {profile.first_name[0]}
            {profile.last_name[0]}
          </div>

          <div style={{ flex: 1, minWidth: '240px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.375rem', fontWeight: 800, color: '#0F172A' }}>
                {profile.full_name}
              </h2>
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  backgroundColor: '#DCFCE7',
                  color: '#15803D',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '9999px',
                }}
              >
                Acudiente Verificado
              </span>
            </div>
            <div style={{ fontSize: '0.875rem', color: '#64748B' }}>
              🏫 {profile.institution_name}
            </div>
          </div>
        </div>

        {/* Official Information Details Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '1.25rem',
            marginBottom: '1.5rem',
          }}
        >
          <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '10px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
              Documento de Identidad
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 800, color: '#0F172A', marginTop: '0.25rem' }}>
              {profile.document_type} {profile.document_number}
            </div>
          </div>

          <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '10px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
              Teléfono de Contacto
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 800, color: '#0F172A', marginTop: '0.25rem' }}>
              📞 {profile.phone}
            </div>
          </div>

          <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '10px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
              Correo Electrónico
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 800, color: '#0F172A', marginTop: '0.25rem' }}>
              ✉️ {profile.email || 'No registrado'}
            </div>
          </div>

          <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '10px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
              Dirección de Residencia
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 800, color: '#0F172A', marginTop: '0.25rem' }}>
              🏠 {profile.address || 'No registrada'}
            </div>
          </div>
        </div>

        {/* Linked Children Metric */}
        <div
          style={{
            backgroundColor: '#EFF6FF',
            borderRadius: '12px',
            border: '1px solid #BFDBFE',
            padding: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div>
            <div style={{ fontSize: '0.9375rem', fontWeight: 800, color: '#1E40AF' }}>
              👨‍👩‍👧 Vinculación Familiar Institucional
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#2563EB', marginTop: '0.2rem' }}>
              Total de estudiantes bajo su patria potestad o tutoría legal en el sistema
            </div>
          </div>

          <div
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#1E40AF',
              color: '#FFFFFF',
              borderRadius: '8px',
              fontWeight: 800,
              fontSize: '1.125rem',
            }}
          >
            {profile.total_linked_students} {profile.total_linked_students === 1 ? 'Estudiante' : 'Estudiantes'}
          </div>
        </div>
      </div>
    </div>
  )
}
