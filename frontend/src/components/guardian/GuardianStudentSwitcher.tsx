/**
 * PEVN Frontend — Guardian Student Context Switcher (Phase 14C)
 *
 * Allows guardians linked to one or multiple students to switch the active child context.
 * Strict Anti-IDOR: only students returned by /guardian/students are displayed.
 */

import React from 'react'
import type { GuardianChildItemResponse } from '@/types/guardian'

interface Props {
  students: GuardianChildItemResponse[]
  selectedStudentId: string | null
  onSelectStudent: (studentId: string) => void
  loading?: boolean
}

export const GuardianStudentSwitcher: React.FC<Props> = ({
  students,
  selectedStudentId,
  onSelectStudent,
  loading = false,
}) => {
  if (students.length === 0) {
    return null
  }

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: '14px',
        padding: '1rem 1.25rem',
        marginBottom: '1.5rem',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.75rem',
          marginBottom: '0.75rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.125rem' }}>👧👦</span>
          <span style={{ fontSize: '0.875rem', fontWeight: 800, color: '#0F172A' }}>
            Seleccionar Estudiante / Hijo a Monitorear:
          </span>
        </div>
        <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
          {students.length} {students.length === 1 ? 'estudiante vinculado' : 'estudiantes vinculados'}
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '0.75rem',
        }}
      >
        {students.map((st) => {
          const isSelected = selectedStudentId === st.student_id

          return (
            <button
              key={st.student_id}
              type="button"
              data-testid={`student-switcher-${st.student_id}`}
              aria-label={st.full_name}
              disabled={loading}
              onClick={() => onSelectStudent(st.student_id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.75rem 1rem',
                borderRadius: '10px',
                border: isSelected ? '2px solid #0F172A' : '1px solid #CBD5E1',
                backgroundColor: isSelected ? '#F8FAFC' : '#FFFFFF',
                cursor: loading ? 'not-allowed' : 'pointer',
                textAlign: 'left',
                transition: 'all 150ms ease',
                boxShadow: isSelected ? '0 4px 6px -1px rgba(15, 23, 42, 0.08)' : 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div
                  style={{
                    width: '38px',
                    height: '38px',
                    borderRadius: '50%',
                    backgroundColor: isSelected ? '#0F172A' : '#E2E8F0',
                    color: isSelected ? '#FFFFFF' : '#475569',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 800,
                    fontSize: '0.875rem',
                  }}
                >
                  {st.first_name[0]}
                  {st.last_name[0]}
                </div>

                <div>
                  <div style={{ fontWeight: 800, color: '#0F172A', fontSize: '0.9375rem' }}>
                    {st.full_name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.15rem' }}>
                    {st.grade_name ? `${st.grade_name}` : 'Grado N/A'} • Grupo {st.group_name || 'N/A'}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem' }}>
                <span
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    backgroundColor: '#F1F5F9',
                    color: '#475569',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '9999px',
                    textTransform: 'capitalize',
                  }}
                >
                  {st.relationship_type.toLowerCase()}
                </span>
                {isSelected && (
                  <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#0F172A' }}>
                    ✓ Activo
                  </span>
                )}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
