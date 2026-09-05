/**
 * PEVN Frontend — Student Task Card Component
 *
 * Rich card representing an academic task or evaluation:
 * - Activity title and subject
 * - Activity type badge (Taller, Tarea, Evaluación, etc.)
 * - Dynamic submission status badge (PENDING, OVERDUE, SUBMITTED, GRADED)
 * - Due date with urgent countdown highlight
 * - Max score / graded score
 * - Action button to open instructions and feedback
 */

import React from 'react'
import type { StudentActivityItemResponse } from '@/types/student'
import { StudentStatusBadge } from './StudentStatusBadge'
import { formatDateTime } from '@/utils'

interface StudentTaskCardProps {
  activity: StudentActivityItemResponse
  onViewDetails: (activity: StudentActivityItemResponse) => void
}

export const StudentTaskCard: React.FC<StudentTaskCardProps> = ({
  activity,
  onViewDetails,
}) => {
  const isOverdue = activity.submission_status === 'OVERDUE'
  const isPending = activity.submission_status === 'PENDING'
  const isGraded = activity.submission_status === 'GRADED'

  const activityTypeLabels: Record<string, string> = {
    HOMEWORK: 'Tarea',
    WORKSHOP: 'Taller',
    EXAM: 'Examen',
    QUIZ: 'Quiz',
    PROJECT: 'Proyecto',
    CLASS_PARTICIPATION: 'Participación',
  }

  // Calculate days/hours remaining if pending
  const getDeadlineText = () => {
    if (!activity.due_date) return null
    const due = new Date(activity.due_date)
    const now = new Date()
    const diffMs = due.getTime() - now.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)

    if (diffMs < 0) {
      return { text: `Venció el ${formatDateTime(activity.due_date)}`, isUrgent: true }
    }
    if (diffHours < 24) {
      return { text: `¡Vence hoy en ${diffHours} hora(s)!`, isUrgent: true }
    }
    if (diffDays === 1) {
      return { text: `Vence mañana (${formatDateTime(activity.due_date)})`, isUrgent: true }
    }
    return { text: `Entrega: ${formatDateTime(activity.due_date)}`, isUrgent: false }
  }

  const deadlineInfo = getDeadlineText()

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '12px',
        border: isOverdue ? '1px solid #FECACA' : '1px solid #E2E8F0',
        boxShadow: isOverdue ? '0 2px 4px rgba(239, 68, 68, 0.05)' : '0 1px 3px rgba(0,0,0,0.04)',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative',
        transition: 'transform 0.15s ease, box-shadow 0.15s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)'
        e.currentTarget.style.boxShadow = '0 6px 14px rgba(0,0,0,0.08)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = isOverdue
          ? '0 2px 4px rgba(239, 68, 68, 0.05)'
          : '0 1px 3px rgba(0,0,0,0.04)'
      }}
    >
      {/* Card Header: Subject & Status */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem', flexWrap: 'wrap', gap: '0.4rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
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
              📖 {activity.subject_name}
            </span>

            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                color: '#64748B',
                backgroundColor: '#F8FAFC',
                padding: '0.2rem 0.5rem',
                borderRadius: '6px',
              }}
            >
              {activityTypeLabels[activity.activity_type] || activity.activity_type}
            </span>
          </div>

          <StudentStatusBadge type="submission" status={activity.submission_status} size="sm" />
        </div>

        {/* Title */}
        <h4
          style={{
            margin: '0 0 0.4rem 0',
            fontSize: '1.05rem',
            fontWeight: 700,
            color: '#0F172A',
            lineHeight: 1.3,
          }}
        >
          {activity.title}
        </h4>

        {/* Educator & Description snippet */}
        {activity.teacher_name && (
          <div style={{ fontSize: '0.8125rem', color: '#64748B', marginBottom: '0.5rem' }}>
            Docente: <strong style={{ color: '#334155' }}>{activity.teacher_name}</strong>
          </div>
        )}

        {activity.description && (
          <p
            style={{
              margin: '0 0 0.75rem 0',
              fontSize: '0.85rem',
              color: '#475569',
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
      </div>

      {/* Card Footer: Deadline & Score & Action */}
      <div style={{ borderTop: '1px solid #F1F5F9', paddingTop: '0.85rem', marginTop: '0.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            {deadlineInfo && (
              <div
                style={{
                  fontSize: '0.75rem',
                  fontWeight: deadlineInfo.isUrgent ? 700 : 500,
                  color: deadlineInfo.isUrgent ? '#DC2626' : '#64748B',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                }}
              >
                {deadlineInfo.isUrgent ? '⏰' : '📅'} {deadlineInfo.text}
              </div>
            )}

            {isGraded && activity.score !== null && (
              <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#15803D', marginTop: '0.2rem' }}>
                Nota: {Number(activity.score).toFixed(1)} / {Number(activity.max_score).toFixed(1)}
              </div>
            )}
          </div>

          <button
            onClick={() => onViewDetails(activity)}
            style={{
              backgroundColor: isPending || isOverdue ? '#1E40AF' : '#F1F5F9',
              color: isPending || isOverdue ? '#FFFFFF' : '#334155',
              border: 'none',
              padding: '0.45rem 0.9rem',
              borderRadius: '6px',
              fontSize: '0.8125rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
              if (isPending || isOverdue) {
                e.currentTarget.style.backgroundColor = '#1D4ED8'
              } else {
                e.currentTarget.style.backgroundColor = '#E2E8F0'
              }
            }}
            onMouseLeave={(e) => {
              if (isPending || isOverdue) {
                e.currentTarget.style.backgroundColor = '#1E40AF'
              } else {
                e.currentTarget.style.backgroundColor = '#F1F5F9'
              }
            }}
          >
            <span>Ver Instrucciones</span>
            <span aria-hidden="true">→</span>
          </button>
        </div>
      </div>
    </div>
  )
}
