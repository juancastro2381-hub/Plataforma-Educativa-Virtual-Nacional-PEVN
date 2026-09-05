/**
 * PEVN Frontend — Student Dashboard View (Phase 14B)
 *
 * Actionable home workspace for the authenticated student:
 * - High-priority next/live class alert banner with instant "INGRESAR A CLASE" CTA
 * - KPI metric cards (Pending Tasks, Overdue Tasks, Enrolled Subjects, Attendance Rate)
 * - Priority urgent task list with status badges and due dates
 * - Upcoming scheduled virtual classes
 * - Recent evaluations and educator feedback
 */

import React from 'react'
import type {
  StudentActivityItemResponse,
  StudentDashboardResponse,
  StudentTab,
  StudentVirtualClassroomItemResponse,
} from '@/types/student'
import { StudentMetricCard } from '@/components/student/StudentMetricCard'
import { StudentTaskCard } from '@/components/student/StudentTaskCard'
import { StudentVirtualClassCard } from '@/components/student/StudentVirtualClassCard'
import { StudentEmptyState } from '@/components/student/StudentEmptyState'
import { formatDateTime } from '@/utils'

interface StudentDashboardViewProps {
  data: StudentDashboardResponse
  onNavigateTab: (tab: StudentTab) => void
  onViewTaskDetails: (activity: StudentActivityItemResponse) => void
  onJoinClass: (classroom: StudentVirtualClassroomItemResponse) => void
  onViewRecordings: (classroom: StudentVirtualClassroomItemResponse) => void
}

export const StudentDashboardView: React.FC<StudentDashboardViewProps> = ({
  data,
  onNavigateTab,
  onViewTaskDetails,
  onJoinClass,
  onViewRecordings,
}) => {
  const {
    total_subjects,
    pending_activities_count,
    overdue_activities_count,
    graded_activities_count,
    attendance_summary,
    upcoming_virtual_classrooms,
    upcoming_activities,
    recent_grades,
  } = data

  // Check if there is an active running class or next class within the next 3 hours
  const liveClass = upcoming_virtual_classrooms.find((c) => c.status === 'RUNNING')
  const nextScheduledClass = !liveClass ? upcoming_virtual_classrooms.find((c) => c.status === 'SCHEDULED') : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* 1. HIGH-PRIORITY ACTION BANNER: LIVE / UPCOMING VIRTUAL CLASS */}
      {liveClass ? (
        <div
          style={{
            backgroundColor: '#DCFCE7',
            border: '2px solid #22C55E',
            borderRadius: '16px',
            padding: '1.5rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1.25rem',
            boxShadow: '0 10px 15px -3px rgba(34, 197, 94, 0.15)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div
              style={{
                width: '52px',
                height: '52px',
                borderRadius: '50%',
                backgroundColor: '#16A34A',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.75rem',
                flexShrink: 0,
              }}
            >
              🔴
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, backgroundColor: '#22C55E', color: '#FFFFFF', padding: '0.15rem 0.55rem', borderRadius: '9999px' }}>
                  CLASE EN VIVO
                </span>
                <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#166534' }}>
                  {liveClass.subject_name || 'Clase Virtual'}
                </span>
              </div>

              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
                {liveClass.title}
              </h2>

              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: '#166534' }}>
                Docente: <strong>{liveClass.teacher_name || 'Docente Institucional'}</strong> • Sala activa ahora
              </p>
            </div>
          </div>

          <button
            onClick={() => onJoinClass(liveClass)}
            style={{
              backgroundColor: '#16A34A',
              color: '#FFFFFF',
              border: 'none',
              padding: '0.85rem 1.75rem',
              borderRadius: '10px',
              fontSize: '1.05rem',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
              boxShadow: '0 4px 6px -1px rgba(22, 163, 74, 0.35)',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#15803D')}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#16A34A')}
          >
            <span>INGRESAR A CLASE AHORA</span>
            <span aria-hidden="true">→</span>
          </button>
        </div>
      ) : nextScheduledClass ? (
        <div
          style={{
            backgroundColor: '#EFF6FF',
            border: '1px solid #BFDBFE',
            borderRadius: '16px',
            padding: '1.25rem 1.5rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <span style={{ fontSize: '1.8rem' }}>📅</span>
            <div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#1E40AF', textTransform: 'uppercase' }}>
                Próxima Clase Virtual Programada
              </span>
              <h3 style={{ margin: '0.15rem 0', fontSize: '1.1rem', fontWeight: 800, color: '#0F172A' }}>
                {nextScheduledClass.title} ({nextScheduledClass.subject_name})
              </h3>
              <span style={{ fontSize: '0.8125rem', color: '#475569' }}>
                {nextScheduledClass.scheduled_start_time ? formatDateTime(nextScheduledClass.scheduled_start_time) : ''} • Docente: {nextScheduledClass.teacher_name}
              </span>
            </div>
          </div>

          <button
            onClick={() => onJoinClass(nextScheduledClass)}
            style={{
              backgroundColor: '#1D4ED8',
              color: '#FFFFFF',
              border: 'none',
              padding: '0.65rem 1.25rem',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Ver Detalles y Sala
          </button>
        </div>
      ) : null}

      {/* 2. KPI METRIC CARDS */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
        }}
      >
        <StudentMetricCard
          icon="📝"
          label="Tareas Pendientes"
          value={pending_activities_count}
          subtext="Por entregar"
          accentColor="#3B82F6"
          onClick={() => onNavigateTab('tasks')}
          badge={pending_activities_count > 0 ? { text: `${pending_activities_count} activas`, variant: 'info' } : undefined}
        />

        <StudentMetricCard
          icon="⚠️"
          label="Tareas Vencidas"
          value={overdue_activities_count}
          subtext="Requieren atención"
          accentColor="#EF4444"
          onClick={() => onNavigateTab('tasks')}
          badge={overdue_activities_count > 0 ? { text: '¡Urgente!', variant: 'danger' } : undefined}
        />

        <StudentMetricCard
          icon="📚"
          label="Asignaturas"
          value={total_subjects}
          subtext="Plan de estudios activo"
          accentColor="#8B5CF6"
          onClick={() => onNavigateTab('subjects')}
        />

        <StudentMetricCard
          icon="📋"
          label="Asistencia Global"
          value={`${attendance_summary.attendance_rate.toFixed(1)}%`}
          subtext={`${attendance_summary.present_count} de ${attendance_summary.total_sessions} sesiones`}
          accentColor="#10B981"
          onClick={() => onNavigateTab('attendance')}
          badge={{
            text: attendance_summary.attendance_rate >= 80 ? 'Excelente' : 'Alerta',
            variant: attendance_summary.attendance_rate >= 80 ? 'success' : 'warning',
          }}
        />
      </div>

      {/* 3. TWO COLUMNS: URGENT TASKS & UPCOMING CLASSES */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
        {/* Left: Mis Tareas Inmediatas */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.3rem' }}>📝</span>
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: '#0F172A' }}>
                Mis Tareas Prioritarias
              </h3>
            </div>

            <button
              onClick={() => onNavigateTab('tasks')}
              style={{
                background: 'none',
                border: 'none',
                color: '#1D4ED8',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Ver todas ({upcoming_activities.length}) →
            </button>
          </div>

          {upcoming_activities.length === 0 ? (
            <StudentEmptyState
              icon="🎉"
              title="¡Estás al día!"
              description="No tienes tareas pendientes ni evaluaciones próximas por entregar."
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {upcoming_activities.slice(0, 3).map((act) => (
                <StudentTaskCard
                  key={act.id}
                  activity={act}
                  onViewDetails={onViewTaskDetails}
                />
              ))}
            </div>
          )}
        </div>

        {/* Right: Próximas Clases Virtuales */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.3rem' }}>💻</span>
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: '#0F172A' }}>
                Clases Virtuales del Grupo
              </h3>
            </div>

            <button
              onClick={() => onNavigateTab('virtual-classes')}
              style={{
                background: 'none',
                border: 'none',
                color: '#1D4ED8',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Ver todas ({upcoming_virtual_classrooms.length}) →
            </button>
          </div>

          {upcoming_virtual_classrooms.length === 0 ? (
            <StudentEmptyState
              icon="💻"
              title="Sin clases virtuales programadas"
              description="No hay sesiones de videoconferencia agendadas para el grupo en este momento."
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {upcoming_virtual_classrooms.slice(0, 2).map((classroom) => (
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
      </div>

      {/* 4. RECENT GRADES & EVALUATIONS */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          border: '1px solid #E2E8F0',
          padding: '1.5rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.3rem' }}>📊</span>
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: '#0F172A' }}>
              Últimas Calificaciones y Retroalimentación
            </h3>
          </div>

          <button
            onClick={() => onNavigateTab('grades')}
            style={{
              background: 'none',
              border: 'none',
              color: '#1D4ED8',
              fontSize: '0.85rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Ver reporte de notas ({graded_activities_count}) →
          </button>
        </div>

        {recent_grades.length === 0 ? (
          <StudentEmptyState
            icon="📊"
            title="Sin calificaciones recientes"
            description="Las calificaciones y observaciones pedagógicas de tus docentes aparecerán aquí una vez evaluadas."
          />
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '1rem',
            }}
          >
            {recent_grades.slice(0, 4).map((gr, index) => (
              <div
                key={gr.grade_id || gr.activity_id || index}
                style={{
                  backgroundColor: '#F8FAFC',
                  borderRadius: '10px',
                  border: '1px solid #E2E8F0',
                  padding: '1rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#1E40AF' }}>
                      {gr.subject_name}
                    </span>
                    {gr.score !== null && (
                      <span
                        style={{
                          fontSize: '1rem',
                          fontWeight: 800,
                          color: '#15803D',
                          backgroundColor: '#DCFCE7',
                          padding: '0.15rem 0.5rem',
                          borderRadius: '6px',
                        }}
                      >
                        {Number(gr.score).toFixed(1)} / {Number(gr.max_score).toFixed(1)}
                      </span>
                    )}
                  </div>

                  <strong style={{ display: 'block', fontSize: '0.9rem', color: '#0F172A', marginBottom: '0.4rem' }}>
                    {gr.activity_title}
                  </strong>

                  {gr.feedback && (
                    <p style={{ margin: 0, fontSize: '0.8125rem', color: '#475569', fontStyle: 'italic', lineHeight: 1.4 }}>
                      "{gr.feedback}"
                    </p>
                  )}
                </div>

                {gr.graded_at && (
                  <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '0.5rem' }}>
                    Evaluado: {formatDateTime(gr.graded_at)}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
