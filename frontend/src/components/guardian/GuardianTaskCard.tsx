/**
 * PEVN Frontend — Guardian Task Card Component
 *
 * Task observation card for parental monitoring and follow-up.
 * Includes explicit non-submission disclaimer pill.
 */

import React from 'react'
import type { StudentActivityItemResponse } from '@/types/student'
import { StudentStatusBadge } from '@/components/student/StudentStatusBadge'

interface Props {
  activity: StudentActivityItemResponse
  onViewDetails: (activity: StudentActivityItemResponse) => void
}

export const GuardianTaskCard: React.FC<Props> = ({ activity, onViewDetails }) => {
  const formatDueDate = (dateStr: string | null) => {
    if (!dateStr) return 'Sin fecha límite'
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString('es-CO', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr
    }
  }

  const isOverdue = activity.submission_status === 'OVERDUE'
  const isGraded = activity.submission_status === 'GRADED'

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '14px',
        border: isOverdue ? '1px solid #FECDD3' : '1px solid #E2E8F0',
        padding: '1.25rem',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        transition: 'transform 150ms ease, box-shadow 150ms ease',
      }}
    >
      <div>
        {/* Top Header with Subject and Status */}
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
              📖 {activity.subject_name}
            </span>
            <h3 style={{ margin: 0, fontSize: '1.0625rem', fontWeight: 800, color: '#0F172A', lineHeight: 1.3 }}>
              {activity.title}
            </h3>
          </div>

          <StudentStatusBadge status={activity.submission_status} type="submission" />
        </div>

        {/* Task description snippet */}
        {activity.description && (
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
            {activity.description}
          </p>
        )}

        {/* Supervision Context Pill */}
        <div
          style={{
            backgroundColor: '#F8FAFC',
            border: '1px dashed #CBD5E1',
            borderRadius: '8px',
            padding: '0.5rem 0.75rem',
            fontSize: '0.75rem',
            color: '#64748B',
            marginBottom: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}
        >
          <span>👁️</span>
          <span>Acompañamiento familiar • Entrega exclusiva del estudiante</span>
        </div>

        {/* Due date & Teacher */}
        <div style={{ fontSize: '0.8125rem', color: '#64748B', display: 'flex', flexDirection: 'column', gap: '0.25rem', marginBottom: '1rem' }}>
          <div>
            📅 <strong>Entrega:</strong> <span style={{ color: isOverdue ? '#BE123C' : '#0F172A', fontWeight: isOverdue ? 700 : 500 }}>{formatDueDate(activity.due_date)}</span>
          </div>
          {activity.teacher_name && (
            <div>
              👨‍🏫 <strong>Docente:</strong> {activity.teacher_name}
            </div>
          )}
        </div>

        {/* Evaluation score if graded */}
        {isGraded && activity.score !== null && (
          <div
            style={{
              backgroundColor: '#F0FDF4',
              border: '1px solid #BBF7D0',
              borderRadius: '8px',
              padding: '0.625rem 0.875rem',
              marginBottom: '1rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#166534' }}>
              Calificación Obtenida:
            </span>
            <span style={{ fontSize: '1.125rem', fontWeight: 800, color: '#15803D' }}>
              {Number(activity.score).toFixed(1)} / {Number(activity.max_score).toFixed(1)}
            </span>
          </div>
        )}
      </div>

      {/* View Details Action */}
      <button
        type="button"
        onClick={() => onViewDetails(activity)}
        style={{
          width: '100%',
          padding: '0.625rem 1rem',
          borderRadius: '8px',
          backgroundColor: '#0F172A',
          color: '#FFFFFF',
          border: 'none',
          fontSize: '0.8125rem',
          fontWeight: 700,
          cursor: 'pointer',
          transition: 'background-color 150ms ease',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.4rem',
        }}
      >
        <span>🔍 Ver Detalle e Instrucciones</span>
      </button>
    </div>
  )
}
