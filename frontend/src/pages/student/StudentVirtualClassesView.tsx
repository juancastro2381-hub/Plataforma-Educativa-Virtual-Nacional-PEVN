/**
 * PEVN Frontend — Student Virtual Classes & Recordings View (Phase 14B)
 *
 * Dedicated hub for virtual classes and lecture recordings:
 * - Tabs: Clases Programadas y en Vivo | Archivo de Grabaciones
 * - Live sessions highlighted with pulsating live badge and prominent "INGRESAR A CLASE" CTA
 * - Recordings archive with "VER GRABACIÓN" action
 */

import React, { useMemo, useState } from 'react'
import type { StudentVirtualClassroomItemResponse } from '@/types/student'
import { StudentVirtualClassCard } from '@/components/student/StudentVirtualClassCard'
import { StudentEmptyState } from '@/components/student/StudentEmptyState'

interface StudentVirtualClassesViewProps {
  classrooms: StudentVirtualClassroomItemResponse[]
  onJoinClass: (classroom: StudentVirtualClassroomItemResponse) => void
  onViewRecordings: (classroom: StudentVirtualClassroomItemResponse) => void
}

type ClassViewFilter = 'ACTIVE' | 'RECORDINGS' | 'ALL'

export const StudentVirtualClassesView: React.FC<StudentVirtualClassesViewProps> = ({
  classrooms,
  onJoinClass,
  onViewRecordings,
}) => {
  const [filter, setFilter] = useState<ClassViewFilter>('ACTIVE')

  const liveOrUpcoming = useMemo(() => {
    return classrooms.filter((c) => c.status === 'RUNNING' || c.status === 'SCHEDULED')
  }, [classrooms])

  const withRecordings = useMemo(() => {
    return classrooms.filter((c) => c.has_recordings)
  }, [classrooms])

  const displayedClassrooms = useMemo(() => {
    if (filter === 'ACTIVE') return liveOrUpcoming
    if (filter === 'RECORDINGS') return withRecordings
    return classrooms
  }, [filter, liveOrUpcoming, withRecordings, classrooms])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 1. Header Banner */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          border: '1px solid #E2E8F0',
          padding: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
        }}
      >
        <div>
          <h2 style={{ margin: '0 0 0.35rem 0', fontSize: '1.3rem', fontWeight: 800, color: '#0F172A' }}>
            Aulas Virtuales y Clases Sincrónicas
          </h2>
          <p style={{ margin: 0, fontSize: '0.875rem', color: '#64748B' }}>
            Salas de videoconferencia interactivas y repositorio de clases grabadas para tu grupo académico.
          </p>
        </div>

        {liveOrUpcoming.length > 0 && (
          <div
            style={{
              backgroundColor: '#DCFCE7',
              border: '2px solid #86EFAC',
              borderRadius: '12px',
              padding: '0.65rem 1.15rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
            }}
          >
            <span style={{ fontSize: '1.4rem' }}>🔴</span>
            <div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#166534', display: 'block' }}>
                SESIONES ACTIVAS / PROGRAMADAS
              </span>
              <strong style={{ fontSize: '1.15rem', fontWeight: 800, color: '#15803D' }}>
                {liveOrUpcoming.length} {liveOrUpcoming.length === 1 ? 'Clase' : 'Clases'}
              </strong>
            </div>
          </div>
        )}
      </div>

      {/* 2. View Filter Pills */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          flexWrap: 'wrap',
          backgroundColor: '#FFFFFF',
          padding: '0.75rem',
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
        }}
      >
        <button
          onClick={() => setFilter('ACTIVE')}
          style={{
            padding: '0.55rem 1rem',
            borderRadius: '8px',
            border: filter === 'ACTIVE' ? '1px solid #1D4ED8' : '1px solid transparent',
            backgroundColor: filter === 'ACTIVE' ? '#EFF6FF' : 'transparent',
            color: filter === 'ACTIVE' ? '#1D4ED8' : '#64748B',
            fontSize: '0.875rem',
            fontWeight: filter === 'ACTIVE' ? 700 : 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}
        >
          <span>🔴 En Vivo y Programadas</span>
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              backgroundColor: filter === 'ACTIVE' ? '#1D4ED8' : '#94A3B8',
              color: '#FFFFFF',
              borderRadius: '9999px',
              padding: '0.1rem 0.45rem',
            }}
          >
            {liveOrUpcoming.length}
          </span>
        </button>

        <button
          onClick={() => setFilter('RECORDINGS')}
          style={{
            padding: '0.55rem 1rem',
            borderRadius: '8px',
            border: filter === 'RECORDINGS' ? '1px solid #1D4ED8' : '1px solid transparent',
            backgroundColor: filter === 'RECORDINGS' ? '#EFF6FF' : 'transparent',
            color: filter === 'RECORDINGS' ? '#1D4ED8' : '#64748B',
            fontSize: '0.875rem',
            fontWeight: filter === 'RECORDINGS' ? 700 : 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}
        >
          <span>📹 Grabaciones Disponibles</span>
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              backgroundColor: filter === 'RECORDINGS' ? '#1D4ED8' : '#94A3B8',
              color: '#FFFFFF',
              borderRadius: '9999px',
              padding: '0.1rem 0.45rem',
            }}
          >
            {withRecordings.length}
          </span>
        </button>

        <button
          onClick={() => setFilter('ALL')}
          style={{
            padding: '0.55rem 1rem',
            borderRadius: '8px',
            border: filter === 'ALL' ? '1px solid #1D4ED8' : '1px solid transparent',
            backgroundColor: filter === 'ALL' ? '#EFF6FF' : 'transparent',
            color: filter === 'ALL' ? '#1D4ED8' : '#64748B',
            fontSize: '0.875rem',
            fontWeight: filter === 'ALL' ? 700 : 600,
            cursor: 'pointer',
          }}
        >
          Todas las Clases ({classrooms.length})
        </button>
      </div>

      {/* 3. Grid of Virtual Classes */}
      {displayedClassrooms.length === 0 ? (
        <StudentEmptyState
          icon="💻"
          title={
            filter === 'ACTIVE'
              ? 'No tienes clases virtuales programadas'
              : filter === 'RECORDINGS'
                ? 'No hay grabaciones archivadas'
                : 'No se encontraron clases virtuales'
          }
          description={
            filter === 'ACTIVE'
              ? 'Cuando tus docentes programen o inicien una clase en vivo para tu grupo, aparecerá aquí con el botón para ingresar.'
              : 'Las grabaciones de clases finalizadas estarán disponibles tan pronto sean procesadas y publicadas por tus docentes.'
          }
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: '1.25rem',
          }}
        >
          {displayedClassrooms.map((classroom) => (
            <StudentVirtualClassCard
              key={classroom.id}
              classroom={classroom}
              onJoinClass={onJoinClass}
              onViewRecordings={onViewRecordings}
            />
          ))}
        </div>
      )}
    </div>
  )
}
