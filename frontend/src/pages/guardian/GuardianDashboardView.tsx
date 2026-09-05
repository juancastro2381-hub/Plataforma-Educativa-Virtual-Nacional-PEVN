/**
 * PEVN Frontend — Guardian Dashboard View (Phase 14C)
 *
 * Consolidated family overview:
 * - Alerts banner (overdue homework, live classes, attendance issues)
 * - 4 Key Performance Indicators (Subjects, Pending Tasks, Attendance %, Average Score)
 * - Urgent pending tasks list
 * - Recent evaluations and teacher feedback
 */

import React from 'react'
import type { GuardianChildOverviewResponse, GuardianTab } from '@/types/guardian'
import type { StudentActivityItemResponse } from '@/types/student'
import { GuardianMetricCard } from '@/components/guardian/GuardianMetricCard'
import { GuardianAlertBanner } from '@/components/guardian/GuardianAlertBanner'
import { GuardianTaskCard } from '@/components/guardian/GuardianTaskCard'
import { GuardianEmptyState } from '@/components/guardian/GuardianEmptyState'
import { GuardianLoadingSkeleton } from '@/components/guardian/GuardianLoadingSkeleton'

interface Props {
  overview: GuardianChildOverviewResponse | null
  loading: boolean
  onTabChange: (tab: GuardianTab) => void
  onSelectTask: (task: StudentActivityItemResponse) => void
}

export const GuardianDashboardView: React.FC<Props> = ({
  overview,
  loading,
  onTabChange,
  onSelectTask,
}) => {
  if (loading) {
    return <GuardianLoadingSkeleton type="overview" />
  }

  if (!overview) {
    return (
      <GuardianEmptyState
        icon="👶"
        title="Sin información de estudiante"
        description="Seleccione un hijo o tutorado para consultar su seguimiento académico institucional."
        actionLabel="Ver Mis Hijos"
        onAction={() => onTabChange('students')}
      />
    )
  }

  const { child, attendance_summary, pending_activities, recent_grades, upcoming_virtual_classrooms } = overview
  const nextClass = upcoming_virtual_classrooms[0]

  return (
    <div>
      {/* Alert Banner */}
      <GuardianAlertBanner
        overdueTasksCount={overview.overdue_tasks_count}
        nextLiveClassTitle={nextClass?.title}
        nextLiveClassTime={nextClass?.scheduled_start_time || undefined}
        absentCount={attendance_summary.absent_count}
        onViewTasks={() => onTabChange('tasks')}
        onViewVirtualClasses={() => onTabChange('virtual-classes')}
        onViewAttendance={() => onTabChange('attendance')}
      />

      {/* KPI Metrics Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
          marginBottom: '1.75rem',
        }}
      >
        <GuardianMetricCard
          title="Asignaturas Cursadas"
          value={overview.total_subjects}
          subtitle={`Grado ${child.grade_name || 'N/A'} • ${child.group_name || 'N/A'}`}
          icon="📚"
          accent="indigo"
          onClick={() => onTabChange('academic')}
        />

        <GuardianMetricCard
          title="Tareas Pendientes"
          value={overview.pending_tasks_count}
          subtitle={overview.overdue_tasks_count > 0 ? `${overview.overdue_tasks_count} vencidas` : 'Entregas al día'}
          icon="📝"
          accent={overview.overdue_tasks_count > 0 ? 'rose' : 'amber'}
          onClick={() => onTabChange('tasks')}
        />

        <GuardianMetricCard
          title="Asistencia Escolar"
          value={`${attendance_summary.attendance_rate}%`}
          subtitle={`${attendance_summary.present_count} de ${attendance_summary.total_sessions} sesiones`}
          icon="📋"
          accent="emerald"
          onClick={() => onTabChange('attendance')}
        />

        <GuardianMetricCard
          title="Promedio General"
          value={overview.average_score !== null ? Number(overview.average_score).toFixed(1) : '—'}
          subtitle="Escala nacional 0.0 – 5.0"
          icon="📊"
          accent="purple"
          onClick={() => onTabChange('grades')}
        />
      </div>

      {/* Two Column Layout: Urgent Tasks & Recent Evaluations */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '1.5rem',
        }}
      >
        {/* Urgent Tasks Section */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '1.5rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1.25rem',
            }}
          >
            <div>
              <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 800, color: '#0F172A' }}>
                📝 Deberes y Tareas Pendientes
              </h3>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.75rem', color: '#64748B' }}>
                Supervisión de entregas académicas asignadas a {child.first_name}
              </p>
            </div>

            <button
              type="button"
              onClick={() => onTabChange('tasks')}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#2563EB',
                fontSize: '0.8125rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Ver todas ({overview.pending_tasks_count}) →
            </button>
          </div>

          {pending_activities.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 1rem', color: '#64748B' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🎉</div>
              <div style={{ fontWeight: 700, color: '#0F172A' }}>¡Sin tareas pendientes!</div>
              <div style={{ fontSize: '0.8125rem', marginTop: '0.25rem' }}>
                {child.first_name} se encuentra al día con todas sus obligaciones escolares.
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {pending_activities.slice(0, 3).map((act) => (
                <GuardianTaskCard
                  key={act.id}
                  activity={act}
                  onViewDetails={onSelectTask}
                />
              ))}
            </div>
          )}
        </div>

        {/* Recent Evaluations Section */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '1.5rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1.25rem',
            }}
          >
            <div>
              <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 800, color: '#0F172A' }}>
                🎯 Últimas Evaluaciones Calificadas
              </h3>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.75rem', color: '#64748B' }}>
                Notas y comentarios emitidos recientemente por docentes
              </p>
            </div>

            <button
              type="button"
              onClick={() => onTabChange('grades')}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#2563EB',
                fontSize: '0.8125rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Ver calificaciones →
            </button>
          </div>

          {recent_grades.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 1rem', color: '#64748B' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📊</div>
              <div style={{ fontWeight: 700, color: '#0F172A' }}>Sin evaluaciones recientes</div>
              <div style={{ fontSize: '0.8125rem', marginTop: '0.25rem' }}>
                Las notas publicadas por los educadores aparecerán en este panel.
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {recent_grades.slice(0, 4).map((gr) => (
                <div
                  key={gr.activity_id}
                  style={{
                    padding: '0.875rem 1rem',
                    backgroundColor: '#F8FAFC',
                    borderRadius: '10px',
                    border: '1px solid #E2E8F0',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: '0.75rem',
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#1E40AF' }}>
                      {gr.subject_name}
                    </div>
                    <div style={{ fontWeight: 700, color: '#0F172A', fontSize: '0.875rem', marginTop: '0.1rem' }}>
                      {gr.activity_title}
                    </div>
                    {gr.feedback && (
                      <div style={{ fontSize: '0.75rem', color: '#15803D', fontStyle: 'italic', marginTop: '0.2rem' }}>
                        "{gr.feedback}"
                      </div>
                    )}
                  </div>

                  <div
                    style={{
                      padding: '0.35rem 0.75rem',
                      borderRadius: '8px',
                      backgroundColor: '#DCFCE7',
                      color: '#15803D',
                      fontWeight: 800,
                      fontSize: '1rem',
                      flexShrink: 0,
                    }}
                  >
                    {gr.score !== null ? Number(gr.score).toFixed(1) : '—'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
