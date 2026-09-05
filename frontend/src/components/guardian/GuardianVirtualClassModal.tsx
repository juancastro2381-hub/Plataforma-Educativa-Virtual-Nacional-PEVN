/**
 * PEVN Frontend — Guardian Virtual Classroom Modal Component
 *
 * Provides parental monitoring view for virtual classroom sessions and recordings.
 */

import React from 'react'
import type { StudentVirtualClassroomItemResponse } from '@/types/student'
import { StudentStatusBadge } from '@/components/student/StudentStatusBadge'

interface Props {
  classroom: StudentVirtualClassroomItemResponse | null
  onClose: () => void
}

export const GuardianVirtualClassModal: React.FC<Props> = ({ classroom, onClose }) => {
  if (!classroom) return null

  const formatFullDate = (dateStr: string | null) => {
    if (!dateStr) return 'Fecha por confirmar'
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString('es-CO', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr
    }
  }

  const isLive = classroom.status === 'RUNNING'

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(3px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
        padding: '1rem',
      }}
    >
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          maxWidth: '640px',
          width: '100%',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          border: '1px solid #E2E8F0',
          overflow: 'hidden',
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '1.25rem 1.75rem',
            backgroundColor: isLive ? '#1E3A8A' : '#0F172A',
            color: '#FFFFFF',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '1rem',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  backgroundColor: 'rgba(56, 189, 248, 0.2)',
                  color: '#38BDF8',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '9999px',
                }}
              >
                📖 {classroom.subject_name || 'Asignatura'}
              </span>
              <StudentStatusBadge status={classroom.status} type="classroom" />
            </div>

            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#FFFFFF' }}>
              {classroom.title}
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: '#94A3B8',
              lineHeight: 1,
              padding: '0.25rem',
            }}
          >
            ✕
          </button>
        </div>

        {/* Modal Scrollable Content */}
        <div style={{ padding: '1.5rem 1.75rem', overflowY: 'auto', flex: 1 }}>
          {/* Schedule Info */}
          <div
            style={{
              backgroundColor: '#F8FAFC',
              borderRadius: '12px',
              padding: '1rem 1.25rem',
              border: '1px solid #E2E8F0',
              marginBottom: '1.25rem',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
            }}
          >
            <div>
              <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>
                HORA DE INICIO PROGRAMADA
              </div>
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A', marginTop: '0.25rem' }}>
                🕒 {formatFullDate(classroom.scheduled_start_time)}
              </div>
            </div>

            {classroom.teacher_name && (
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>
                  DOCENTE ORGANIZADOR
                </div>
                <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A', marginTop: '0.25rem' }}>
                  👨‍🏫 {classroom.teacher_name}
                </div>
              </div>
            )}
          </div>

          {/* Description */}
          {classroom.description && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9375rem', fontWeight: 800, color: '#0F172A' }}>
                📋 Temas de la Sesión
              </h4>
              <p
                style={{
                  fontSize: '0.875rem',
                  color: '#334155',
                  lineHeight: 1.6,
                  backgroundColor: '#F8FAFC',
                  padding: '0.875rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid #E2E8F0',
                  margin: 0,
                }}
              >
                {classroom.description}
              </p>
            </div>
          )}

          {/* Room Name & Access Information */}
          {classroom.room_name && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9375rem', fontWeight: 800, color: '#0F172A' }}>
                💻 Identificador de Sala
              </h4>
              <div
                style={{
                  fontSize: '0.8125rem',
                  fontFamily: 'monospace',
                  color: '#1E293B',
                  backgroundColor: '#F1F5F9',
                  padding: '0.625rem 1rem',
                  borderRadius: '6px',
                  border: '1px solid #CBD5E1',
                }}
              >
                {classroom.room_name}
              </div>
            </div>
          )}

          {/* Parental Notice */}
          <div
            style={{
              backgroundColor: '#EFF6FF',
              border: '1px solid #BFDBFE',
              borderRadius: '10px',
              padding: '0.875rem 1rem',
              fontSize: '0.8125rem',
              color: '#1E40AF',
              lineHeight: 1.5,
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
            }}
          >
            <span style={{ fontSize: '1.25rem' }}>👁️</span>
            <div>
              <strong>Acompañamiento en Clase Virtual:</strong> Este espacio permite a padres y tutores supervisar las sesiones y el horario académico de sus hijos.
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: '1rem 1.75rem',
            borderTop: '1px solid #E2E8F0',
            backgroundColor: '#F8FAFC',
            display: 'flex',
            justifyContent: 'flex-end',
          }}
        >
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: '0.625rem 1.25rem',
              borderRadius: '8px',
              backgroundColor: '#0F172A',
              color: '#FFFFFF',
              border: 'none',
              fontSize: '0.875rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
