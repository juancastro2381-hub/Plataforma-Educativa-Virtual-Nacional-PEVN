/**
 * PEVN Frontend — Student Virtual Class Card Component
 *
 * Prominent card representing an authorized virtual classroom:
 * - Session title and enrolled subject
 * - Teacher and scheduled start/end times
 * - Live status badge (RUNNING, SCHEDULED, ENDED)
 * - Primary CTA: "INGRESAR A CLASE" (enabled when can_join is true)
 * - Secondary CTA: "VER GRABACIÓN" (when recordings are available)
 */

import React from 'react'
import type { StudentVirtualClassroomItemResponse } from '@/types/student'
import { StudentStatusBadge } from './StudentStatusBadge'
import { formatDateTime } from '@/utils'

interface StudentVirtualClassCardProps {
  classroom: StudentVirtualClassroomItemResponse
  onJoinClass?: (classroom: StudentVirtualClassroomItemResponse) => void
  onViewRecordings?: (classroom: StudentVirtualClassroomItemResponse) => void
}

export const StudentVirtualClassCard: React.FC<StudentVirtualClassCardProps> = ({
  classroom,
  onJoinClass,
  onViewRecordings,
}) => {
  const isRunning = classroom.status === 'RUNNING'
  const isEnded = classroom.status === 'ENDED'

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '14px',
        border: isRunning ? '2px solid #22C55E' : '1px solid #E2E8F0',
        boxShadow: isRunning ? '0 4px 12px rgba(34, 197, 94, 0.15)' : '0 1px 3px rgba(0,0,0,0.04)',
        padding: '1.35rem',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Live Pulsing Banner for Running Classes */}
      {isRunning && (
        <div
          style={{
            backgroundColor: '#DCFCE7',
            color: '#15803D',
            padding: '0.35rem 0.75rem',
            margin: '-1.35rem -1.35rem 1rem -1.35rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.8125rem',
            fontWeight: 800,
            borderBottom: '1px solid #86EFAC',
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: '#22C55E',
                display: 'inline-block',
                boxShadow: '0 0 0 2px rgba(34, 197, 94, 0.4)',
              }}
            />
            ¡CLASE EN VIVO EN ESTE MOMENTO!
          </span>
          <span>SALA ABIERTA</span>
        </div>
      )}

      {/* Header Info */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.5rem' }}>
          {classroom.subject_name && (
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: '#1E40AF',
                backgroundColor: '#EFF6FF',
                padding: '0.2rem 0.55rem',
                borderRadius: '6px',
                border: '1px solid #DBEAFE',
              }}
            >
              📖 {classroom.subject_name}
            </span>
          )}

          <StudentStatusBadge type="classroom" status={classroom.status} size="sm" />
        </div>

        <h3
          style={{
            margin: '0 0 0.5rem 0',
            fontSize: '1.125rem',
            fontWeight: 800,
            color: '#0F172A',
            lineHeight: 1.3,
          }}
        >
          {classroom.title}
        </h3>

        {classroom.teacher_name && (
          <div style={{ fontSize: '0.85rem', color: '#475569', marginBottom: '0.4rem' }}>
            👨‍🏫 Docente: <strong style={{ color: '#1E293B' }}>{classroom.teacher_name}</strong>
          </div>
        )}

        {classroom.scheduled_start_time && (
          <div style={{ fontSize: '0.8125rem', color: '#64748B', display: 'flex', alignItems: 'center', gap: '0.35rem', marginBottom: '0.5rem' }}>
            <span>🕒 Horario:</span>
            <strong>
              {formatDateTime(classroom.scheduled_start_time)}
              {classroom.scheduled_end_time && ` — ${new Date(classroom.scheduled_end_time).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}`}
            </strong>
          </div>
        )}

        {classroom.description && (
          <p
            style={{
              margin: '0.4rem 0 0.75rem 0',
              fontSize: '0.85rem',
              color: '#475569',
              lineHeight: 1.4,
            }}
          >
            {classroom.description}
          </p>
        )}
      </div>

      {/* CTA Buttons */}
      <div style={{ borderTop: '1px solid #F1F5F9', paddingTop: '1rem', marginTop: '0.75rem', display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
        {classroom.can_join && (
          <button
            onClick={() => onJoinClass?.(classroom)}
            style={{
              flex: 1,
              backgroundColor: isRunning ? '#16A34A' : '#1D4ED8',
              color: '#FFFFFF',
              border: 'none',
              padding: '0.75rem 1.25rem',
              borderRadius: '8px',
              fontSize: '0.925rem',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              boxShadow: isRunning
                ? '0 4px 6px -1px rgba(22, 163, 74, 0.3)'
                : '0 4px 6px -1px rgba(29, 78, 216, 0.25)',
              transition: 'background-color 0.15s ease, transform 0.1s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = isRunning ? '#15803D' : '#1E40AF'
              e.currentTarget.style.transform = 'translateY(-1px)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = isRunning ? '#16A34A' : '#1D4ED8'
              e.currentTarget.style.transform = 'translateY(0)'
            }}
          >
            <span aria-hidden="true" style={{ fontSize: '1.1rem' }}>
              {isRunning ? '🔴' : '🚀'}
            </span>
            <span>INGRESAR A CLASE</span>
          </button>
        )}

        {classroom.has_recordings && (
          <button
            onClick={() => onViewRecordings?.(classroom)}
            style={{
              backgroundColor: '#F8FAFC',
              color: '#0F172A',
              border: '1px solid #CBD5E1',
              padding: '0.65rem 1rem',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.4rem',
              transition: 'background-color 0.15s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#F1F5F9'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#F8FAFC'
            }}
          >
            <span>📹</span>
            <span>VER GRABACIÓN</span>
          </button>
        )}

        {!classroom.can_join && !classroom.has_recordings && isEnded && (
          <div style={{ fontSize: '0.8125rem', color: '#94A3B8', fontStyle: 'italic', padding: '0.4rem 0' }}>
            Esta sesión finalizó y no cuenta con grabaciones archivadas.
          </div>
        )}
      </div>
    </div>
  )
}
