/**
 * PEVN Frontend — Guardian Virtual Class Card Component
 *
 * Displays scheduled virtual classroom agenda items with access and recording information.
 */

import React from 'react'
import type { StudentVirtualClassroomItemResponse } from '@/types/student'
import { StudentStatusBadge } from '@/components/student/StudentStatusBadge'

interface Props {
  classroom: StudentVirtualClassroomItemResponse
  onViewClassroom: (classroom: StudentVirtualClassroomItemResponse) => void
}

export const GuardianVirtualClassCard: React.FC<Props> = ({ classroom, onViewClassroom }) => {
  const formatTimeRange = (startStr: string | null, endStr: string | null) => {
    if (!startStr) return 'Horario por confirmar'
    try {
      const start = new Date(startStr)
      const end = endStr ? new Date(endStr) : null

      const datePart = start.toLocaleDateString('es-CO', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      })

      const timeStart = start.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
      const timeEnd = end ? end.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }) : ''

      return `${datePart} • ${timeStart} ${timeEnd ? `– ${timeEnd}` : ''}`
    } catch {
      return startStr
    }
  }

  const isLive = classroom.status === 'RUNNING'
  const isEnded = classroom.status === 'ENDED'

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '14px',
        border: isLive ? '2px solid #2563EB' : '1px solid #E2E8F0',
        padding: '1.25rem',
        boxShadow: isLive ? '0 4px 6px -1px rgba(37, 99, 235, 0.15)' : '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        transition: 'all 150ms ease',
      }}
    >
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <div>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: '#1E40AF',
                backgroundColor: '#EFF6FF',
                padding: '0.2rem 0.55rem',
                borderRadius: '6px',
                display: 'inline-block',
                marginBottom: '0.35rem',
              }}
            >
              📖 {classroom.subject_name || 'Asignatura Institucional'}
            </span>
            <h3 style={{ margin: 0, fontSize: '1.0625rem', fontWeight: 800, color: '#0F172A', lineHeight: 1.3 }}>
              {classroom.title}
            </h3>
          </div>

          <StudentStatusBadge status={classroom.status} type="classroom" />
        </div>

        {classroom.description && (
          <p
            style={{
              fontSize: '0.8125rem',
              color: '#475569',
              margin: '0 0 0.875rem 0',
              lineHeight: 1.4,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {classroom.description}
          </p>
        )}

        {/* Schedule & Teacher */}
        <div style={{ fontSize: '0.8125rem', color: '#64748B', display: 'flex', flexDirection: 'column', gap: '0.25rem', marginBottom: '1rem' }}>
          <div>
            🕒 <strong>Horario:</strong> <span style={{ color: '#0F172A', fontWeight: 600 }}>{formatTimeRange(classroom.scheduled_start_time, classroom.scheduled_end_time)}</span>
          </div>
          {classroom.teacher_name && (
            <div>
              👨‍🏫 <strong>Docente:</strong> {classroom.teacher_name}
            </div>
          )}
        </div>
      </div>

      {/* Action Button */}
      <button
        type="button"
        onClick={() => onViewClassroom(classroom)}
        style={{
          width: '100%',
          padding: '0.625rem 1rem',
          borderRadius: '8px',
          backgroundColor: isLive ? '#2563EB' : isEnded ? '#0F172A' : '#1E293B',
          color: '#FFFFFF',
          border: 'none',
          fontSize: '0.8125rem',
          fontWeight: 700,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.4rem',
        }}
      >
        <span>{isLive ? '🔴 Supervisar Sala en Vivo' : isEnded ? '📹 Ver Grabación y Detalles' : '📅 Consultar Agenda de Clase'}</span>
      </button>
    </div>
  )
}
