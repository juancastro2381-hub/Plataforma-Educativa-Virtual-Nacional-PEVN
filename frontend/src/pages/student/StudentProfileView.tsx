/**
 * PEVN Frontend — Student Profile & Institutional Context View (Phase 14B)
 *
 * Displays the authenticated student's profile and enrollment registry:
 * - Personal and identity document information
 * - SIMAT unique national student code
 * - Enrolled grade, group, campus, and institution
 * - Active enrollment status
 */

import React from 'react'
import type { StudentProfileResponse } from '@/types/student'
import { formatDate } from '@/utils'

interface StudentProfileViewProps {
  profile: StudentProfileResponse
}

export const StudentProfileView: React.FC<StudentProfileViewProps> = ({ profile }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '900px', margin: '0 auto' }}>
      {/* 1. Header Profile Summary */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          border: '1px solid #E2E8F0',
          padding: '1.75rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1.5rem',
          flexWrap: 'wrap',
          boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
        }}
      >
        <div
          style={{
            width: '72px',
            height: '72px',
            borderRadius: '20px',
            backgroundColor: '#1E40AF',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.75rem',
            fontWeight: 800,
            boxShadow: '0 4px 6px -1px rgba(30, 64, 175, 0.25)',
          }}
        >
          {profile.first_name[0]}
          {profile.last_name[0]}
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', flexWrap: 'wrap' }}>
            <h2 style={{ margin: 0, fontSize: '1.35rem', fontWeight: 800, color: '#0F172A' }}>
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
                border: '1px solid #86EFAC',
              }}
            >
              Matrícula {profile.enrollment_status || 'ACTIVA'}
            </span>
          </div>

          <div style={{ fontSize: '0.875rem', color: '#64748B' }}>
            {profile.email} • Código SIMAT: <strong style={{ color: '#1E293B' }}>{profile.code_simat}</strong>
          </div>
        </div>
      </div>

      {/* 2. Personal & Academic Context Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
        {/* Personal Details */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem', borderBottom: '1px solid #F1F5F9', paddingBottom: '0.75rem' }}>
            <span style={{ fontSize: '1.25rem' }}>👤</span>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: '#0F172A' }}>
              Información de Identidad
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.875rem' }}>
            <div>
              <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                NOMBRES COMPLETOS
              </span>
              <strong style={{ color: '#1E293B' }}>{profile.first_name} {profile.last_name}</strong>
            </div>

            <div>
              <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                TIPO Y NÚMERO DE DOCUMENTO
              </span>
              <strong style={{ color: '#1E293B' }}>
                {profile.document_type}: {profile.document_number}
              </strong>
            </div>

            <div>
              <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                CÓDIGO NACIONAL SIMAT
              </span>
              <strong style={{ color: '#1E40AF' }}>{profile.code_simat}</strong>
            </div>

            <div>
              <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                FECHA DE NACIMIENTO
              </span>
              <strong style={{ color: '#1E293B' }}>{formatDate(profile.birth_date)}</strong>
            </div>

            <div>
              <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                CORREO ELECTRÓNICO INSTITUCIONAL
              </span>
              <strong style={{ color: '#1E293B' }}>{profile.email}</strong>
            </div>
          </div>
        </div>

        {/* Academic & Institutional Details */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem', borderBottom: '1px solid #F1F5F9', paddingBottom: '0.75rem' }}>
            <span style={{ fontSize: '1.25rem' }}>🏫</span>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: '#0F172A' }}>
              Matrícula Institucional Activa
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.875rem' }}>
            <div>
              <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                INSTITUCIÓN EDUCATIVA
              </span>
              <strong style={{ color: '#1E293B' }}>{profile.institution_name}</strong>
            </div>

            {profile.campus_name && (
              <div>
                <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                  SEDE EDUCATIVA
                </span>
                <strong style={{ color: '#1E293B' }}>{profile.campus_name}</strong>
              </div>
            )}

            <div>
              <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                GRADO ESCOLAR
              </span>
              <strong style={{ color: '#1E40AF' }}>{profile.grade_name || 'Grado no especificado'}</strong>
            </div>

            <div>
              <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                GRUPO ASIGNADO
              </span>
              <strong style={{ color: '#1E40AF' }}>{profile.group_name || 'Sin grupo'}</strong>
            </div>

            <div>
              <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                AÑO LECTIVO VIGENTE
              </span>
              <strong style={{ color: '#059669' }}>{profile.academic_year_name || 'Vigente'}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
