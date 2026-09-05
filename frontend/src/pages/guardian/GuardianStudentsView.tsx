/**
 * PEVN Frontend — Guardian Students View (Mis Hijos)
 *
 * Full directory of authorized children linked to the authenticated guardian.
 */

import React from 'react'
import type { GuardianChildItemResponse } from '@/types/guardian'
import { GuardianChildCard } from '@/components/guardian/GuardianChildCard'
import { GuardianEmptyState } from '@/components/guardian/GuardianEmptyState'
import { GuardianLoadingSkeleton } from '@/components/guardian/GuardianLoadingSkeleton'

interface Props {
  students: GuardianChildItemResponse[]
  selectedStudentId: string | null
  onSelectStudent: (studentId: string) => void
  loading: boolean
}

export const GuardianStudentsView: React.FC<Props> = ({
  students,
  selectedStudentId,
  onSelectStudent,
  loading,
}) => {
  if (loading) {
    return <GuardianLoadingSkeleton type="cards" />
  }

  if (students.length === 0) {
    return (
      <GuardianEmptyState
        icon="👨‍👧‍👦"
        title="Sin estudiantes vinculados"
        description="No se registran estudiantes legalmente vinculados a su cuenta de acudiente en esta institución. Comuníquese con la Rectoría o Secretaría Académica."
      />
    )
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
            Mis Hijos y Tutorados Registrados
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
            Estudiantes con matrícula activa bajo su responsabilidad parental y legal en la institución.
          </p>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1.25rem',
        }}
      >
        {students.map((st) => (
          <GuardianChildCard
            key={st.student_id}
            child={st}
            isSelected={selectedStudentId === st.student_id}
            onSelect={onSelectStudent}
          />
        ))}
      </div>
    </div>
  )
}
