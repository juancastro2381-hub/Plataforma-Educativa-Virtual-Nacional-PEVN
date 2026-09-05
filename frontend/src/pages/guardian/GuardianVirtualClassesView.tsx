/**
 * PEVN Frontend — Guardian Virtual Classes View (Clases Virtuales)
 *
 * Virtual classroom agenda monitoring and lecture recordings viewer for the selected child.
 */

import React, { useState } from 'react'
import type { StudentVirtualClassroomItemResponse } from '@/types/student'
import type { GuardianChildVirtualClassroomsListResponse } from '@/types/guardian'
import { GuardianVirtualClassCard } from '@/components/guardian/GuardianVirtualClassCard'
import { GuardianVirtualClassModal } from '@/components/guardian/GuardianVirtualClassModal'
import { GuardianEmptyState } from '@/components/guardian/GuardianEmptyState'
import { GuardianLoadingSkeleton } from '@/components/guardian/GuardianLoadingSkeleton'

interface Props {
  classroomsData: GuardianChildVirtualClassroomsListResponse | null
  loading: boolean
  childName?: string
}

export const GuardianVirtualClassesView: React.FC<Props> = ({
  classroomsData,
  loading,
  childName,
}) => {
  const [selectedClassroom, setSelectedClassroom] = useState<StudentVirtualClassroomItemResponse | null>(null)

  if (loading) {
    return <GuardianLoadingSkeleton type="cards" />
  }

  const items = classroomsData?.items || []
  const upcomingAndLive = items.filter((c) => c.status === 'RUNNING' || c.status === 'SCHEDULED')
  const pastSessions = items.filter((c) => c.status === 'ENDED' || c.status === 'CANCELLED')

  if (items.length === 0) {
    return (
      <GuardianEmptyState
        icon="💻"
        title="Sin clases virtuales programadas"
        description={`No hay sesiones virtuales agendadas para el grupo de ${childName || 'el estudiante'} en este momento.`}
      />
    )
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
            Agenda de Clases Virtuales — {classroomsData?.student_name}
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
            Supervise los horarios de conexión sincrónica y el repositorio de grabaciones del curso.
          </p>
        </div>
      </div>

      {/* Live & Upcoming Sessions Section */}
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.0625rem', fontWeight: 800, color: '#0F172A', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>🔴</span>
          <span>Sesiones en Vivo y Próximas Clases ({upcomingAndLive.length})</span>
        </h3>

        {upcomingAndLive.length === 0 ? (
          <div
            style={{
              padding: '2rem',
              backgroundColor: '#FFFFFF',
              borderRadius: '12px',
              border: '1px solid #E2E8F0',
              textAlign: 'center',
              color: '#64748B',
              fontSize: '0.875rem',
            }}
          >
            No hay clases virtuales en vivo ni programadas para las próximas horas.
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '1.25rem',
            }}
          >
            {upcomingAndLive.map((c) => (
              <GuardianVirtualClassCard
                key={c.id}
                classroom={c}
                onViewClassroom={setSelectedClassroom}
              />
            ))}
          </div>
        )}
      </div>

      {/* Past Sessions / Recordings Section */}
      {pastSessions.length > 0 && (
        <div>
          <h3 style={{ fontSize: '1.0625rem', fontWeight: 800, color: '#0F172A', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>📹</span>
            <span>Historial y Grabaciones de Sesiones Anteriores ({pastSessions.length})</span>
          </h3>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '1.25rem',
            }}
          >
            {pastSessions.map((c) => (
              <GuardianVirtualClassCard
                key={c.id}
                classroom={c}
                onViewClassroom={setSelectedClassroom}
              />
            ))}
          </div>
        </div>
      )}

      {/* Virtual Classroom Modal */}
      {selectedClassroom && (
        <GuardianVirtualClassModal
          classroom={selectedClassroom}
          onClose={() => setSelectedClassroom(null)}
        />
      )}
    </div>
  )
}
