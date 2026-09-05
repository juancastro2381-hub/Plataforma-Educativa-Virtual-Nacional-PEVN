/**
 * PEVN Frontend — Guardian Attendance View (Asistencia)
 *
 * Daily attendance follow-up, absence statistics, and chronological logs for the active child.
 */

import React, { useMemo, useState } from 'react'
import type { AttendanceStatus } from '@/types/student'
import type { GuardianChildAttendanceListResponse } from '@/types/guardian'
import { StudentStatusBadge } from '@/components/student/StudentStatusBadge'
import { GuardianMetricCard } from '@/components/guardian/GuardianMetricCard'
import { GuardianEmptyState } from '@/components/guardian/GuardianEmptyState'
import { GuardianLoadingSkeleton } from '@/components/guardian/GuardianLoadingSkeleton'

interface Props {
  attendanceData: GuardianChildAttendanceListResponse | null
  loading: boolean
  childName?: string
}

type FilterAttendance = 'ALL' | AttendanceStatus

export const GuardianAttendanceView: React.FC<Props> = ({
  attendanceData,
  loading,
  childName,
}) => {
  const [filterStatus, setFilterStatus] = useState<FilterAttendance>('ALL')

  const summary = attendanceData?.summary
  const items = attendanceData?.items || []

  const filteredItems = useMemo(() => {
    if (filterStatus === 'ALL') return items
    return items.filter((i) => i.status === filterStatus)
  }, [items, filterStatus])

  if (loading) {
    return <GuardianLoadingSkeleton type="overview" />
  }

  if (!attendanceData || items.length === 0) {
    return (
      <GuardianEmptyState
        icon="📋"
        title="Sin registros de asistencia escolar"
        description={`Aún no se registran llamadas a lista oficiales para ${childName || 'el estudiante'} en el sistema institucional.`}
      />
    )
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
            Control de Asistencia Escolar — {attendanceData.student_name}
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
            Historial de puntualidad, inasistencias justificadas y reportes diarios docentes.
          </p>
        </div>
      </div>

      {/* KPI Metrics Summary */}
      {summary && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '1rem',
            marginBottom: '1.75rem',
          }}
        >
          <GuardianMetricCard
            title="Porcentaje Asistencia"
            value={`${summary.attendance_rate}%`}
            subtitle="Tasa de permanencia"
            icon="📊"
            accent="emerald"
          />

          <GuardianMetricCard
            title="Asistencias"
            value={summary.present_count}
            subtitle={`de ${summary.total_sessions} sesiones`}
            icon="✅"
            accent="indigo"
          />

          <GuardianMetricCard
            title="Inasistencias"
            value={summary.absent_count}
            subtitle={summary.absent_count > 0 ? 'Fallas reportadas' : 'Sin fallas'}
            icon="❌"
            accent={summary.absent_count > 0 ? 'rose' : 'emerald'}
          />

          <GuardianMetricCard
            title="Retardos"
            value={summary.late_count}
            subtitle="Llegadas tarde"
            icon="⏰"
            accent="amber"
          />

          <GuardianMetricCard
            title="Excusas"
            value={summary.excused_count}
            subtitle="Fallas justificadas"
            icon="📝"
            accent="purple"
          />
        </div>
      )}

      {/* Filter Tabs */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '14px',
          border: '1px solid #E2E8F0',
          padding: '1rem 1.25rem',
          marginBottom: '1.5rem',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.5rem',
        }}
      >
        {[
          { id: 'ALL', label: 'Todos los Registros', count: items.length },
          { id: 'PRESENT', label: 'Asistió', count: summary?.present_count || 0 },
          { id: 'ABSENT', label: 'Inasistencias', count: summary?.absent_count || 0 },
          { id: 'LATE', label: 'Retardos', count: summary?.late_count || 0 },
          { id: 'EXCUSED', label: 'Excusas', count: summary?.excused_count || 0 },
        ].map((tab) => {
          const isSelected = filterStatus === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setFilterStatus(tab.id as FilterAttendance)}
              style={{
                padding: '0.45rem 0.875rem',
                borderRadius: '8px',
                border: isSelected ? '1px solid #0F172A' : '1px solid #E2E8F0',
                backgroundColor: isSelected ? '#0F172A' : '#F8FAFC',
                color: isSelected ? '#FFFFFF' : '#475569',
                fontWeight: isSelected ? 700 : 500,
                fontSize: '0.8125rem',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}
            >
              <span>{tab.label}</span>
              <span
                style={{
                  backgroundColor: isSelected ? 'rgba(255,255,255,0.2)' : '#E2E8F0',
                  color: isSelected ? '#FFFFFF' : '#64748B',
                  padding: '0.1rem 0.45rem',
                  borderRadius: '9999px',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                }}
              >
                {tab.count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Attendance Table */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '14px',
          border: '1px solid #E2E8F0',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
          overflow: 'hidden',
        }}
      >
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #E2E8F0', backgroundColor: '#F8FAFC', color: '#475569' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Fecha</th>
                <th style={{ padding: '0.75rem 1rem' }}>Estado de Asistencia</th>
                <th style={{ padding: '0.75rem 1rem' }}>Asignatura</th>
                <th style={{ padding: '0.75rem 1rem' }}>Docente</th>
                <th style={{ padding: '0.75rem 1rem' }}>Observaciones del Educador</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((rec) => (
                <tr key={rec.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                  <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                    {rec.attendance_date}
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <StudentStatusBadge status={rec.status} type="attendance" />
                  </td>
                  <td style={{ padding: '0.75rem 1rem', color: '#1E40AF', fontWeight: 600 }}>
                    {rec.subject_name || 'Jornada Institucional'}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', color: '#475569' }}>
                    {rec.teacher_name || 'Docente Titular'}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', color: '#64748B', fontStyle: rec.remarks ? 'italic' : 'normal' }}>
                    {rec.remarks || 'Sin observaciones'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
