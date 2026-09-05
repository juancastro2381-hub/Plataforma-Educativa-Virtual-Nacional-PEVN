/**
 * PEVN Frontend — Student Attendance View (Phase 14B)
 *
 * Displays daily attendance logs, percentages, and attendance status:
 * - Summary KPI cards (Attendance Rate, Total Sessions, Presentes, Fallas, Excusas, Tardanzas)
 * - Canonical status filters (PRESENT, ABSENT, EXCUSED, LATE)
 * - Historical attendance log table
 */

import React, { useMemo, useState } from 'react'
import type {
  AttendanceStatus,
  StudentAttendanceItemResponse,
  StudentAttendanceSummary,
} from '@/types/student'
import { StudentStatusBadge } from '@/components/student/StudentStatusBadge'
import { StudentEmptyState } from '@/components/student/StudentEmptyState'
import { formatDate } from '@/utils'

interface StudentAttendanceViewProps {
  attendanceItems: StudentAttendanceItemResponse[]
  summary: StudentAttendanceSummary
}

type AttendanceFilter = 'ALL' | AttendanceStatus

export const StudentAttendanceView: React.FC<StudentAttendanceViewProps> = ({
  attendanceItems,
  summary,
}) => {
  const [filter, setFilter] = useState<AttendanceFilter>('ALL')

  const filteredItems = useMemo(() => {
    if (filter === 'ALL') return attendanceItems
    return attendanceItems.filter((item) => item.status === filter)
  }, [attendanceItems, filter])

  const rate = summary.attendance_rate || 100.0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 1. Attendance Summary Overview */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          border: '1px solid #E2E8F0',
          padding: '1.5rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.25rem', marginBottom: '1.5rem' }}>
          <div>
            <h2 style={{ margin: '0 0 0.25rem 0', fontSize: '1.3rem', fontWeight: 800, color: '#0F172A' }}>
              Control y Registro de Asistencia Escolar
            </h2>
            <p style={{ margin: 0, fontSize: '0.875rem', color: '#64748B' }}>
              Historial de asistencia a clases y jornadas académicas del año lectivo vigente.
            </p>
          </div>

          {/* Rate Badge */}
          <div
            style={{
              backgroundColor: rate >= 80 ? '#F0FDF4' : '#FEF2F2',
              border: `2px solid ${rate >= 80 ? '#86EFAC' : '#FECACA'}`,
              borderRadius: '12px',
              padding: '0.75rem 1.25rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
            }}
          >
            <span style={{ fontSize: '1.75rem' }}>{rate >= 80 ? '✅' : '⚠️'}</span>
            <div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: rate >= 80 ? '#166534' : '#991B1B', display: 'block', textTransform: 'uppercase' }}>
                Porcentaje de Asistencia
              </span>
              <strong style={{ fontSize: '1.5rem', fontWeight: 800, color: rate >= 80 ? '#15803D' : '#DC2626' }}>
                {rate.toFixed(1)}%
              </strong>
            </div>
          </div>
        </div>

        {/* Breakdown Metric Blocks */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '0.75rem',
          }}
        >
          <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '10px', border: '1px solid #E2E8F0', textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B', display: 'block' }}>TOTAL SESIONES</span>
            <strong style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0F172A' }}>{summary.total_sessions}</strong>
          </div>

          <div style={{ backgroundColor: '#DCFCE7', padding: '1rem', borderRadius: '10px', border: '1px solid #86EFAC', textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#166534', display: 'block' }}>ASISTENCIAS</span>
            <strong style={{ fontSize: '1.4rem', fontWeight: 800, color: '#15803D' }}>{summary.present_count}</strong>
          </div>

          <div style={{ backgroundColor: '#FEE2E2', padding: '1rem', borderRadius: '10px', border: '1px solid #FCA5A5', textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#991B1B', display: 'block' }}>FALLAS (INASISTENCIAS)</span>
            <strong style={{ fontSize: '1.4rem', fontWeight: 800, color: '#DC2626' }}>{summary.absent_count}</strong>
          </div>

          <div style={{ backgroundColor: '#FEF3C7', padding: '1rem', borderRadius: '10px', border: '1px solid #FCD34D', textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#92400E', display: 'block' }}>EXCUSAS JUSTIFICADAS</span>
            <strong style={{ fontSize: '1.4rem', fontWeight: 800, color: '#D97706' }}>{summary.excused_count}</strong>
          </div>

          <div style={{ backgroundColor: '#FFEDD5', padding: '1rem', borderRadius: '10px', border: '1px solid #FDBA74', textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#9A3412', display: 'block' }}>TARDANZAS</span>
            <strong style={{ fontSize: '1.4rem', fontWeight: 800, color: '#EA580C' }}>{summary.late_count}</strong>
          </div>
        </div>
      </div>

      {/* 2. Filter Pills */}
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
          onClick={() => setFilter('ALL')}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            border: filter === 'ALL' ? '1px solid #1D4ED8' : '1px solid transparent',
            backgroundColor: filter === 'ALL' ? '#EFF6FF' : 'transparent',
            color: filter === 'ALL' ? '#1D4ED8' : '#64748B',
            fontSize: '0.85rem',
            fontWeight: filter === 'ALL' ? 700 : 600,
            cursor: 'pointer',
          }}
        >
          Todos los registros ({attendanceItems.length})
        </button>

        <button
          onClick={() => setFilter('PRESENT')}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            border: filter === 'PRESENT' ? '1px solid #15803D' : '1px solid transparent',
            backgroundColor: filter === 'PRESENT' ? '#DCFCE7' : 'transparent',
            color: filter === 'PRESENT' ? '#15803D' : '#64748B',
            fontSize: '0.85rem',
            fontWeight: filter === 'PRESENT' ? 700 : 600,
            cursor: 'pointer',
          }}
        >
          Presentes ({summary.present_count})
        </button>

        <button
          onClick={() => setFilter('ABSENT')}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            border: filter === 'ABSENT' ? '1px solid #DC2626' : '1px solid transparent',
            backgroundColor: filter === 'ABSENT' ? '#FEE2E2' : 'transparent',
            color: filter === 'ABSENT' ? '#DC2626' : '#64748B',
            fontSize: '0.85rem',
            fontWeight: filter === 'ABSENT' ? 700 : 600,
            cursor: 'pointer',
          }}
        >
          Fallas ({summary.absent_count})
        </button>

        <button
          onClick={() => setFilter('EXCUSED')}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            border: filter === 'EXCUSED' ? '1px solid #D97706' : '1px solid transparent',
            backgroundColor: filter === 'EXCUSED' ? '#FEF3C7' : 'transparent',
            color: filter === 'EXCUSED' ? '#D97706' : '#64748B',
            fontSize: '0.85rem',
            fontWeight: filter === 'EXCUSED' ? 700 : 600,
            cursor: 'pointer',
          }}
        >
          Excusas ({summary.excused_count})
        </button>

        <button
          onClick={() => setFilter('LATE')}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            border: filter === 'LATE' ? '1px solid #EA580C' : '1px solid transparent',
            backgroundColor: filter === 'LATE' ? '#FFEDD5' : 'transparent',
            color: filter === 'LATE' ? '#EA580C' : '#64748B',
            fontSize: '0.85rem',
            fontWeight: filter === 'LATE' ? 700 : 600,
            cursor: 'pointer',
          }}
        >
          Tardanzas ({summary.late_count})
        </button>
      </div>

      {/* 3. Attendance Table */}
      {filteredItems.length === 0 ? (
        <StudentEmptyState
          icon="📋"
          title="No hay registros de asistencia"
          description={
            filter !== 'ALL'
              ? 'No se encontraron registros para el filtro de estado seleccionado.'
              : 'Aún no se han tomado listas de asistencia en el periodo actual.'
          }
        />
      ) : (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            overflow: 'hidden',
            boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
          }}
        >
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>FECHA</th>
                  <th style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>ESTADO</th>
                  <th style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>MATERIA / SESIÓN</th>
                  <th style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>DOCENTE</th>
                  <th style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>OBSERVACIÓN / JUSTIFICACIÓN</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr
                    key={item.id}
                    style={{
                      borderBottom: '1px solid #F1F5F9',
                      transition: 'background-color 0.15s ease',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8FAFC')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <td style={{ padding: '1rem 1.25rem', fontWeight: 700, color: '#0F172A' }}>
                      {formatDate(item.attendance_date)}
                    </td>
                    <td style={{ padding: '1rem 1.25rem' }}>
                      <StudentStatusBadge type="attendance" status={item.status} size="sm" />
                    </td>
                    <td style={{ padding: '1rem 1.25rem', color: '#334155', fontWeight: 600 }}>
                      {item.subject_name || 'Jornada Académica General'}
                    </td>
                    <td style={{ padding: '1rem 1.25rem', color: '#64748B' }}>
                      {item.teacher_name || 'Docente Titular'}
                    </td>
                    <td style={{ padding: '1rem 1.25rem', color: '#475569', fontStyle: item.remarks ? 'normal' : 'italic' }}>
                      {item.remarks || 'Sin observaciones registradas.'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
