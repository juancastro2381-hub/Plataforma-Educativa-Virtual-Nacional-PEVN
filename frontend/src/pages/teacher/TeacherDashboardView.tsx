/**
 * PEVN Frontend — Teacher Dashboard Home View
 *
 * Displays teacher identity, institutional context, active academic year,
 * workload KPIs, pending tasks, and quick action navigation.
 */

import React from 'react'
import type { TeacherDashboardSummaryResponse } from '@/types/teacher'

interface Props {
  summary: TeacherDashboardSummaryResponse | null
  loading: boolean
  onTabChange: (tab: string) => void
}

export const TeacherDashboardView: React.FC<Props> = ({ summary, loading, onTabChange }) => {
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: '#64748B' }}>
        Cargando métricas del panel docente...
      </div>
    )
  }

  if (!summary) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: '#64748B' }}>
        No se pudo cargar la información del panel docente.
      </div>
    )
  }

  return (
    <div>
      {/* Welcome Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%)',
          color: '#FFFFFF',
          borderRadius: '16px',
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div
              style={{
                display: 'inline-block',
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                backgroundColor: 'rgba(252, 209, 22, 0.2)',
                color: '#FCD116',
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
                marginBottom: '0.75rem',
              }}
            >
              Espacio Operativo Docente
            </div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0 0 0.5rem 0' }}>
              ¡Bienvenido, {summary.teacher_name}!
            </h1>
            <p style={{ fontSize: '0.9375rem', color: '#E2E8F0', margin: 0 }}>
              {summary.institution_name} • {summary.specialty_area || 'Área Pedagógica'}
            </p>
          </div>
          <div
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              padding: '0.75rem 1.25rem',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              textAlign: 'right',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 600 }}>
              Año Escolar Vigente
            </div>
            <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#FCD116' }}>
              {summary.active_academic_year || '2026 (Activo)'}
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1.25rem',
          marginBottom: '2rem',
        }}
      >
        <div
          onClick={() => onTabChange('load')}
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            padding: '1.25rem',
            border: '1px solid #E2E8F0',
            cursor: 'pointer',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
            transition: 'transform 150ms, box-shadow 150ms',
          }}
        >
          <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>
            Asignaciones de Carga
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#1E3A8A', marginTop: '0.25rem' }}>
            {summary.total_active_assignments}
          </div>
          <div style={{ fontSize: '0.8125rem', color: '#3B82F6', marginTop: '0.25rem' }}>
            {summary.total_assigned_subjects} materias asignadas →
          </div>
        </div>

        <div
          onClick={() => onTabChange('groups')}
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            padding: '1.25rem',
            border: '1px solid #E2E8F0',
            cursor: 'pointer',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
            transition: 'transform 150ms, box-shadow 150ms',
          }}
        >
          <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>
            Grupos / Salones
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#0F766E', marginTop: '0.25rem' }}>
            {summary.total_assigned_groups}
          </div>
          <div style={{ fontSize: '0.8125rem', color: '#0D9488', marginTop: '0.25rem' }}>
            {summary.total_enrolled_students} estudiantes a cargo →
          </div>
        </div>

        <div
          onClick={() => onTabChange('activities')}
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            padding: '1.25rem',
            border: '1px solid #E2E8F0',
            cursor: 'pointer',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
            transition: 'transform 150ms, box-shadow 150ms',
          }}
        >
          <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>
            Actividades Publicadas
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#6D28D9', marginTop: '0.25rem' }}>
            {summary.total_active_activities}
          </div>
          <div style={{ fontSize: '0.8125rem', color: '#7C3AED', marginTop: '0.25rem' }}>
            Tareas y evaluaciones activas →
          </div>
        </div>

        <div
          onClick={() => onTabChange('grades')}
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            padding: '1.25rem',
            border: '1px solid #E2E8F0',
            cursor: 'pointer',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
            transition: 'transform 150ms, box-shadow 150ms',
          }}
        >
          <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>
            Pendientes por Calificar
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#C2410C', marginTop: '0.25rem' }}>
            {summary.total_pending_grades}
          </div>
          <div style={{ fontSize: '0.8125rem', color: '#EA580C', marginTop: '0.25rem' }}>
            Abrir planilla de notas →
          </div>
        </div>
      </div>

      {/* Quick Action Navigation Grid */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          padding: '1.5rem',
          border: '1px solid #E2E8F0',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
        }}
      >
        <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0F172A', margin: '0 0 1rem 0' }}>
          Acciones Rápidas del Docente
        </h3>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '1rem',
          }}
        >
          <div
            onClick={() => onTabChange('activities')}
            style={{
              padding: '1rem',
              backgroundColor: '#F8FAFC',
              borderRadius: '10px',
              border: '1px solid #E2E8F0',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>📝</div>
            <div style={{ fontWeight: 700, color: '#0F172A', fontSize: '0.9375rem' }}>Crear / Publicar Actividad</div>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8125rem', color: '#64748B' }}>
              Registrar tareas, talleres o exámenes para sus grupos asignados.
            </p>
          </div>

          <div
            onClick={() => onTabChange('attendance')}
            style={{
              padding: '1rem',
              backgroundColor: '#F8FAFC',
              borderRadius: '10px',
              border: '1px solid #E2E8F0',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>📋</div>
            <div style={{ fontWeight: 700, color: '#0F172A', fontSize: '0.9375rem' }}>Tomar Asistencia Diaria</div>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8125rem', color: '#64748B' }}>
              Marcar asistencia de la sesión escolar por grupo y fecha.
            </p>
          </div>

          <div
            onClick={() => onTabChange('grades')}
            style={{
              padding: '1rem',
              backgroundColor: '#F8FAFC',
              borderRadius: '10px',
              border: '1px solid #E2E8F0',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>📊</div>
            <div style={{ fontWeight: 700, color: '#0F172A', fontSize: '0.9375rem' }}>Planilla de Calificaciones</div>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8125rem', color: '#64748B' }}>
              Evaluar y asignar retroalimentación pedagógica a los estudiantes.
            </p>
          </div>

          <div
            onClick={() => onTabChange('planning')}
            style={{
              padding: '1rem',
              backgroundColor: '#F8FAFC',
              borderRadius: '10px',
              border: '1px solid #E2E8F0',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>🎯</div>
            <div style={{ fontWeight: 700, color: '#0F172A', fontSize: '0.9375rem' }}>Planeación Curricular</div>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8125rem', color: '#64748B' }}>
              Documentar unidades, competencias y evidencias de aprendizaje.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
