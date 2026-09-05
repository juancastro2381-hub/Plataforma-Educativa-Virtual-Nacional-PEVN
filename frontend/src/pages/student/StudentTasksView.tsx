/**
 * PEVN Frontend — Student Tasks & Assignments View (Phase 14B)
 *
 * Comprehensive task management module for the student:
 * - Status tabs: Todas | Pendientes | Vencidas | Entregadas | Calificadas
 * - Subject selector filter
 * - Activity type selector filter
 * - Search bar and sorting by due date, subject, or score
 * - Detailed task cards with urgent deadline indicators
 */

import React, { useMemo, useState } from 'react'
import type {
  ActivitySubmissionStatus,
  StudentActivityItemResponse,
  StudentSubjectItemResponse,
} from '@/types/student'
import { StudentTaskCard } from '@/components/student/StudentTaskCard'
import { StudentEmptyState } from '@/components/student/StudentEmptyState'

interface StudentTasksViewProps {
  activities: StudentActivityItemResponse[]
  subjects: StudentSubjectItemResponse[]
  selectedSubjectId?: string | null
  onViewTaskDetails: (activity: StudentActivityItemResponse) => void
}

type StatusFilter = 'ALL' | ActivitySubmissionStatus

export const StudentTasksView: React.FC<StudentTasksViewProps> = ({
  activities,
  subjects,
  selectedSubjectId = null,
  onViewTaskDetails,
}) => {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL')
  const [subjectFilter, setSubjectFilter] = useState<string>(selectedSubjectId || 'ALL')
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<'due_date_asc' | 'due_date_desc' | 'subject' | 'title'>('due_date_asc')

  // Counts for tabs
  const counts = useMemo(() => {
    return {
      ALL: activities.length,
      PENDING: activities.filter((a) => a.submission_status === 'PENDING').length,
      OVERDUE: activities.filter((a) => a.submission_status === 'OVERDUE').length,
      SUBMITTED: activities.filter((a) => a.submission_status === 'SUBMITTED').length,
      GRADED: activities.filter((a) => a.submission_status === 'GRADED').length,
    }
  }, [activities])

  // Filter and sort activities
  const filteredActivities = useMemo(() => {
    return activities
      .filter((a) => {
        // Status filter
        if (statusFilter !== 'ALL' && a.submission_status !== statusFilter) return false

        // Subject filter
        if (subjectFilter !== 'ALL' && a.subject_id !== subjectFilter) return false

        // Search text
        if (searchTerm.trim()) {
          const q = searchTerm.toLowerCase()
          const matchTitle = a.title.toLowerCase().includes(q)
          const matchSubject = a.subject_name.toLowerCase().includes(q)
          const matchTeacher = a.teacher_name?.toLowerCase().includes(q) || false
          if (!matchTitle && !matchSubject && !matchTeacher) return false
        }

        return true
      })
      .sort((a, b) => {
        if (sortBy === 'due_date_asc') {
          if (!a.due_date) return 1
          if (!b.due_date) return -1
          return new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
        }
        if (sortBy === 'due_date_desc') {
          if (!a.due_date) return 1
          if (!b.due_date) return -1
          return new Date(b.due_date).getTime() - new Date(a.due_date).getTime()
        }
        if (sortBy === 'subject') {
          return a.subject_name.localeCompare(b.subject_name)
        }
        if (sortBy === 'title') {
          return a.title.localeCompare(b.title)
        }
        return 0
      })
  }, [activities, statusFilter, subjectFilter, searchTerm, sortBy])

  const statusTabs: { id: StatusFilter; label: string; count: number; color?: string }[] = [
    { id: 'ALL', label: 'Todas las Tareas', count: counts.ALL },
    { id: 'PENDING', label: 'Pendientes', count: counts.PENDING, color: '#F59E0B' },
    { id: 'OVERDUE', label: 'Vencidas', count: counts.OVERDUE, color: '#EF4444' },
    { id: 'SUBMITTED', label: 'Entregadas', count: counts.SUBMITTED, color: '#3B82F6' },
    { id: 'GRADED', label: 'Calificadas', count: counts.GRADED, color: '#10B981' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 1. Status Filter Pills */}
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
        {statusTabs.map((tab) => {
          const isSelected = statusFilter === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                padding: '0.55rem 1rem',
                borderRadius: '8px',
                border: isSelected ? '1px solid #1D4ED8' : '1px solid transparent',
                backgroundColor: isSelected ? '#EFF6FF' : 'transparent',
                color: isSelected ? '#1D4ED8' : '#64748B',
                fontSize: '0.875rem',
                fontWeight: isSelected ? 700 : 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <span>{tab.label}</span>
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  backgroundColor: isSelected ? '#1D4ED8' : tab.color || '#94A3B8',
                  color: '#FFFFFF',
                  borderRadius: '9999px',
                  padding: '0.1rem 0.45rem',
                  minWidth: '18px',
                  textAlign: 'center',
                }}
              >
                {tab.count}
              </span>
            </button>
          )
        })}
      </div>

      {/* 2. Secondary Filters and Search Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          backgroundColor: '#FFFFFF',
          padding: '1.25rem',
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
        }}
      >
        {/* Search */}
        <div style={{ position: 'relative', width: '100%', maxWidth: '320px' }}>
          <input
            type="text"
            placeholder="Buscar por título, materia o docente..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '0.6rem 1rem 0.6rem 2.25rem',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              fontSize: '0.875rem',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
          <span style={{ position: 'absolute', left: '0.75rem', top: '0.65rem', color: '#94A3B8' }}>
            🔍
          </span>
        </div>

        {/* Dropdowns */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Subject Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#64748B' }}>
              Materia:
            </label>
            <select
              value={subjectFilter}
              onChange={(e) => setSubjectFilter(e.target.value)}
              style={{
                padding: '0.55rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                color: '#334155',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="ALL">Todas las Materias ({subjects.length})</option>
              {subjects.map((s) => (
                <option key={s.subject_id} value={s.subject_id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          {/* Sort By */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#64748B' }}>
              Ordenar por:
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              style={{
                padding: '0.55rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                color: '#334155',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="due_date_asc">Fecha límite (Próximas primero)</option>
              <option value="due_date_desc">Fecha límite (Más lejanas)</option>
              <option value="subject">Materia (A-Z)</option>
              <option value="title">Título de la Tarea (A-Z)</option>
            </select>
          </div>
        </div>
      </div>

      {/* 3. Task Cards Grid */}
      {filteredActivities.length === 0 ? (
        <StudentEmptyState
          icon="📝"
          title="No se encontraron tareas"
          description={
            statusFilter !== 'ALL' || subjectFilter !== 'ALL' || searchTerm
              ? 'No hay actividades que coincidan con los filtros seleccionados.'
              : 'No tienes actividades académicas asignadas en este momento.'
          }
          actionLabel={
            statusFilter !== 'ALL' || subjectFilter !== 'ALL' || searchTerm
              ? 'Limpiar filtros'
              : undefined
          }
          onAction={() => {
            setStatusFilter('ALL')
            setSubjectFilter('ALL')
            setSearchTerm('')
          }}
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: '1.25rem',
          }}
        >
          {filteredActivities.map((activity) => (
            <StudentTaskCard
              key={activity.id}
              activity={activity}
              onViewDetails={onViewTaskDetails}
            />
          ))}
        </div>
      )}
    </div>
  )
}
