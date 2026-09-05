/**
 * PEVN Frontend — Guardian Alert Banner Component
 *
 * Highlights pressing academic events requiring parental attention:
 * - Overdue homework tasks
 * - Imminent / Live virtual classes
 * - High absence counts
 */

import React from 'react'

interface Props {
  overdueTasksCount: number
  nextLiveClassTitle?: string
  nextLiveClassTime?: string
  absentCount: number
  onViewTasks?: () => void
  onViewVirtualClasses?: () => void
  onViewAttendance?: () => void
}

export const GuardianAlertBanner: React.FC<Props> = ({
  overdueTasksCount,
  nextLiveClassTitle,
  nextLiveClassTime,
  absentCount,
  onViewTasks,
  onViewVirtualClasses,
  onViewAttendance,
}) => {
  const hasAlerts = overdueTasksCount > 0 || nextLiveClassTitle || absentCount > 0

  if (!hasAlerts) {
    return (
      <div
        style={{
          backgroundColor: '#ECFDF5',
          border: '1px solid #A7F3D0',
          borderRadius: '12px',
          padding: '1rem 1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          color: '#065F46',
          fontSize: '0.875rem',
        }}
      >
        <span style={{ fontSize: '1.25rem' }}>✅</span>
        <div>
          <strong>¡Todo al día!</strong> No hay tareas vencidas ni alertas críticas de asistencia para el estudiante seleccionado.
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
      {/* Overdue Tasks Alert */}
      {overdueTasksCount > 0 && (
        <div
          style={{
            backgroundColor: '#FFF1F2',
            border: '1px solid #FECDD3',
            borderRadius: '12px',
            padding: '1rem 1.25rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '0.75rem',
            color: '#9F1239',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '1.5rem' }}>⚠️</span>
            <div>
              <div style={{ fontWeight: 800, fontSize: '0.9375rem' }}>
                Atención requerida: {overdueTasksCount} {overdueTasksCount === 1 ? 'tarea vencida' : 'tareas vencidas'}
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#BE123C', marginTop: '0.15rem' }}>
                El estudiante tiene entregas académicas que han superado la fecha límite sin registro de entrega.
              </div>
            </div>
          </div>

          {onViewTasks && (
            <button
              type="button"
              onClick={onViewTasks}
              style={{
                padding: '0.45rem 0.875rem',
                borderRadius: '8px',
                backgroundColor: '#BE123C',
                color: '#FFFFFF',
                border: 'none',
                fontSize: '0.8125rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Ver Tareas Vencidas →
            </button>
          )}
        </div>
      )}

      {/* Live / Upcoming Class Alert */}
      {nextLiveClassTitle && (
        <div
          style={{
            backgroundColor: '#EFF6FF',
            border: '1px solid #BFDBFE',
            borderRadius: '12px',
            padding: '1rem 1.25rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '0.75rem',
            color: '#1E40AF',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '1.5rem' }}>💻</span>
            <div>
              <div style={{ fontWeight: 800, fontSize: '0.9375rem' }}>
                Próxima Clase Virtual: {nextLiveClassTitle}
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#2563EB', marginTop: '0.15rem' }}>
                Horario programado: {nextLiveClassTime || 'Hoy'}
              </div>
            </div>
          </div>

          {onViewVirtualClasses && (
            <button
              type="button"
              onClick={onViewVirtualClasses}
              style={{
                padding: '0.45rem 0.875rem',
                borderRadius: '8px',
                backgroundColor: '#1E40AF',
                color: '#FFFFFF',
                border: 'none',
                fontSize: '0.8125rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Consultar Agenda →
            </button>
          )}
        </div>
      )}

      {/* Attendance Alert */}
      {absentCount > 2 && (
        <div
          style={{
            backgroundColor: '#FFFBEB',
            border: '1px solid #FDE68A',
            borderRadius: '12px',
            padding: '1rem 1.25rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '0.75rem',
            color: '#92400E',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '1.5rem' }}>📋</span>
            <div>
              <div style={{ fontWeight: 800, fontSize: '0.9375rem' }}>
                Alerta de Asistencia: {absentCount} inasistencias registradas
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#B45309', marginTop: '0.15rem' }}>
                Revise el historial para verificar si hay fallas pendientes de justificación institucional.
              </div>
            </div>
          </div>

          {onViewAttendance && (
            <button
              type="button"
              onClick={onViewAttendance}
              style={{
                padding: '0.45rem 0.875rem',
                borderRadius: '8px',
                backgroundColor: '#D97706',
                color: '#FFFFFF',
                border: 'none',
                fontSize: '0.8125rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Revisar Asistencia →
            </button>
          )}
        </div>
      )}
    </div>
  )
}
