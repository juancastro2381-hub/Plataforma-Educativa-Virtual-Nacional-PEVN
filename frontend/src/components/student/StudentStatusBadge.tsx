/**
 * PEVN Frontend — Student Portal Status Badge Component
 *
 * Provides accessible, color-coded and labeled badges for:
 * - Activity submission statuses: PENDING, OVERDUE, SUBMITTED, GRADED
 * - Attendance statuses: PRESENT, ABSENT, EXCUSED, LATE
 * - Virtual classroom statuses: SCHEDULED, RUNNING, ENDED, CANCELLED
 */

import React from 'react'
import type {
  ActivitySubmissionStatus,
  AttendanceStatus,
  VirtualClassroomStatus,
} from '@/types/student'

interface StudentStatusBadgeProps {
  type: 'submission' | 'attendance' | 'classroom'
  status: ActivitySubmissionStatus | AttendanceStatus | VirtualClassroomStatus | string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export const StudentStatusBadge: React.FC<StudentStatusBadgeProps> = ({
  type,
  status,
  size = 'md',
  className = '',
}) => {
  let label = status
  let bg = '#F1F5F9'
  let color = '#475569'
  let border = '#CBD5E1'
  let icon = '•'

  if (type === 'submission') {
    switch (status) {
      case 'PENDING':
        label = 'Pendiente'
        bg = '#FEF3C7'
        color = '#92400E'
        border = '#FCD34D'
        icon = '⏳'
        break
      case 'OVERDUE':
        label = 'Vencida'
        bg = '#FEE2E2'
        color = '#991B1B'
        border = '#FCA5A5'
        icon = '⚠️'
        break
      case 'SUBMITTED':
        label = 'Entregada'
        bg = '#E0F2FE'
        color = '#0369A1'
        border = '#BAE6FD'
        icon = '📥'
        break
      case 'GRADED':
        label = 'Calificada'
        bg = '#DCFCE7'
        color = '#15803D'
        border = '#86EFAC'
        icon = '✅'
        break
      default:
        label = status
    }
  } else if (type === 'attendance') {
    switch (status) {
      case 'PRESENT':
        label = 'Presente'
        bg = '#DCFCE7'
        color = '#15803D'
        border = '#86EFAC'
        icon = '✅'
        break
      case 'ABSENT':
        label = 'Falla'
        bg = '#FEE2E2'
        color = '#991B1B'
        border = '#FCA5A5'
        icon = '❌'
        break
      case 'EXCUSED':
        label = 'Excusa Justificada'
        bg = '#FEF3C7'
        color = '#92400E'
        border = '#FCD34D'
        icon = '📝'
        break
      case 'LATE':
        label = 'Tardanza'
        bg = '#FFEDD5'
        color = '#C2410C'
        border = '#FDBA74'
        icon = '⏰'
        break
      default:
        label = status
    }
  } else if (type === 'classroom') {
    switch (status) {
      case 'RUNNING':
        label = 'En Vivo Ahora'
        bg = '#DCFCE7'
        color = '#15803D'
        border = '#86EFAC'
        icon = '🔴'
        break
      case 'SCHEDULED':
        label = 'Programada'
        bg = '#EFF6FF'
        color = '#1D4ED8'
        border = '#BFDBFE'
        icon = '📅'
        break
      case 'ENDED':
        label = 'Finalizada'
        bg = '#F1F5F9'
        color = '#475569'
        border = '#E2E8F0'
        icon = '⏹️'
        break
      case 'CANCELLED':
        label = 'Cancelada'
        bg = '#FEE2E2'
        color = '#991B1B'
        border = '#FCA5A5'
        icon = '🚫'
        break
      default:
        label = status
    }
  }

  const fontSizes = {
    sm: '0.75rem',
    md: '0.8125rem',
    lg: '0.875rem',
  }

  const paddings = {
    sm: '0.15rem 0.45rem',
    md: '0.25rem 0.65rem',
    lg: '0.35rem 0.85rem',
  }

  return (
    <span
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        backgroundColor: bg,
        color,
        border: `1px solid ${border}`,
        borderRadius: '9999px',
        padding: paddings[size],
        fontSize: fontSizes[size],
        fontWeight: 600,
        lineHeight: 1,
        whiteSpace: 'nowrap',
      }}
    >
      <span aria-hidden="true" style={{ fontSize: '0.8em' }}>{icon}</span>
      <span>{label}</span>
    </span>
  )
}
