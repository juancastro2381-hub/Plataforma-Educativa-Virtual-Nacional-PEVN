/**
 * PEVN Frontend — Student Portal Header & Profile Banner
 *
 * Displays enriched student identity context:
 * - Full name and avatar initials
 * - SIMAT code badge
 * - Grade, Group, Campus & Institution
 * - Active Academic Year
 * - Refresh button
 */

import React from 'react'
import type { StudentProfileResponse } from '@/types/student'

interface StudentHeaderProps {
  profile: StudentProfileResponse | null
  onRefresh: () => void
  loading?: boolean
}

export const StudentHeader: React.FC<StudentHeaderProps> = ({
  profile,
  onRefresh,
  loading = false,
}) => {
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((part) => part[0])
      .slice(0, 2)
      .join('')
      .toUpperCase()
  }

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '16px',
        border: '1px solid #E2E8F0',
        padding: '1.5rem',
        boxShadow: '0 2px 4px rgba(0,0,0,0.03)',
        marginBottom: '1.5rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1.25rem',
        }}
      >
        {/* Left: Avatar & Identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div
            style={{
              width: '60px',
              height: '60px',
              borderRadius: '16px',
              backgroundColor: '#1E40AF',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.5rem',
              fontWeight: 800,
              boxShadow: '0 4px 6px -1px rgba(30, 64, 175, 0.25)',
              border: '2px solid #BFDBFE',
              flexShrink: 0,
            }}
          >
            {profile ? getInitials(profile.full_name) : 'ST'}
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
              <h1
                style={{
                  margin: 0,
                  fontSize: '1.35rem',
                  fontWeight: 800,
                  color: '#0F172A',
                  letterSpacing: '-0.01em',
                }}
              >
                {profile ? profile.full_name : 'Estudiante PEVN'}
              </h1>

              {profile?.code_simat && (
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    backgroundColor: '#F1F5F9',
                    color: '#475569',
                    padding: '0.2rem 0.6rem',
                    borderRadius: '6px',
                    border: '1px solid #CBD5E1',
                  }}
                  title="Código Único de Estudiante SIMAT"
                >
                  SIMAT: {profile.code_simat}
                </span>
              )}
            </div>

            {/* Academic Context Tags */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                flexWrap: 'wrap',
                marginTop: '0.4rem',
                fontSize: '0.875rem',
                color: '#64748B',
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontWeight: 600, color: '#1E293B' }}>
                🏫 {profile?.institution_name || 'Institución Educativa'}
              </span>

              {profile?.campus_name && (
                <>
                  <span style={{ color: '#CBD5E1' }}>•</span>
                  <span>Sede: {profile.campus_name}</span>
                </>
              )}

              {profile?.grade_name && (
                <>
                  <span style={{ color: '#CBD5E1' }}>•</span>
                  <span
                    style={{
                      fontWeight: 700,
                      color: '#1D4ED8',
                      backgroundColor: '#EFF6FF',
                      padding: '0.15rem 0.5rem',
                      borderRadius: '4px',
                    }}
                  >
                    Grado {profile.grade_name} {profile.group_name ? `— Grupo ${profile.group_name}` : ''}
                  </span>
                </>
              )}

              {profile?.academic_year_name && (
                <>
                  <span style={{ color: '#CBD5E1' }}>•</span>
                  <span style={{ color: '#059669', fontWeight: 600 }}>
                    Año Lectivo {profile.academic_year_name}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Right: Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={onRefresh}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              color: '#334155',
              padding: '0.55rem 1rem',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.15s ease',
            }}
            onMouseEnter={(e) => {
              if (!loading) e.currentTarget.style.backgroundColor = '#F1F5F9'
            }}
            onMouseLeave={(e) => {
              if (!loading) e.currentTarget.style.backgroundColor = '#F8FAFC'
            }}
            title="Actualizar datos académicos"
          >
            <span style={{ display: 'inline-block', transform: loading ? 'rotate(180deg)' : 'none', transition: 'transform 0.5s ease' }}>
              🔄
            </span>
            {loading ? 'Cargando...' : 'Actualizar'}
          </button>
        </div>
      </div>
    </div>
  )
}
