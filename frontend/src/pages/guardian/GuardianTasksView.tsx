/**
 * PEVN Frontend — Guardian Tasks View (Tareas / Trabajos en Casa)
 *
 * Homework and task supervision module for the active child.
 * Strictly read-only for parental accompaniment.
 */

import React, { useMemo, useState } from 'react'
import type { ActivitySubmissionStatus, StudentActivityItemResponse } from '@/types/student'
import type { GuardianChildActivitiesListResponse } from '@/types/guardian'
import { GuardianTaskCard } from '@/components/guardian/GuardianTaskCard'
import { GuardianTaskDetailModal } from '@/components/guardian/GuardianTaskDetailModal'
import { GuardianEmptyState } from '@/components/guardian/GuardianEmptyState'
import { GuardianLoadingSkeleton } from '@/components/guardian/GuardianLoadingSkeleton'

interface Props {
  activitiesData: GuardianChildActivitiesListResponse | null
  loading: boolean
  childName?: string
}

type FilterStatus = 'ALL' | ActivitySubmissionStatus

export const GuardianTasksView: React.FC<Props> = ({
  activitiesData,
  loading,
  childName,
}) => {
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('ALL')
  const [filterSubject, setFilterSubject] = useState<string>('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTask, setSelectedTask] = useState<StudentActivityItemResponse | null>(null)

  const rawActivities = activitiesData?.items || []

  // Extract unique subjects
  const uniqueSubjects = useMemo(() => {
    const map = new Map<string, string>()
    for (const act of rawActivities) {
      map.set(act.subject_id, act.subject_name)
    }
    return Array.from(map.entries()).map(([id, name]) => ({ id, name }))
  }, [rawActivities])

  // Filter activities
  const filteredActivities = useMemo(() => {
    return rawActivities.filter((act) => {
      // Status filter
      if (filterStatus !== 'ALL' && act.submission_status !== filterStatus) {
        return false
      }

      // Subject filter
      if (filterSubject !== 'ALL' && act.subject_id !== filterSubject) {
        return false
      }

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        const matchesTitle = act.title.toLowerCase().includes(q)
        const matchesDesc = (act.description || '').toLowerCase().includes(q)
        const matchesSub = act.subject_name.toLowerCase().includes(q)
        if (!matchesTitle && !matchesDesc && !matchesSub) {
          return false
        }
      }

      return true
    })
  }, [rawActivities, filterStatus, filterSubject, searchQuery])

  if (loading) {
    return <GuardianLoadingSkeleton type="cards" />
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
            Tareas y Trabajos Escolares — {childName || 'Estudiante'}
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
            Supervise deberes escolares, fechas límite, calificaciones y observaciones emitidas por los educadores.
          </p>
        </div>
      </div>

      {/* Parental Supervisory Disclaimer */}
      <div
        style={{
          backgroundColor: '#EFF6FF',
          border: '1px solid #BFDBFE',
          borderRadius: '12px',
          padding: '0.875rem 1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.8125rem',
          color: '#1E40AF',
        }}
      >
        <span style={{ fontSize: '1.25rem' }}>ℹ️</span>
        <div>
          <strong>Modalidad de Acompañamiento Parental:</strong> La entrega y desarrollo de actividades académicas corresponde al estudiante. Desde este portal puede monitorear las tareas programadas y su respectivo estado de cumplimiento.
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderRadius: '14px',
          padding: '1.25rem',
          marginBottom: '1.5rem',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}
      >
        {/* Status Pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {[
            { id: 'ALL', label: 'Todas las Tareas', count: rawActivities.length },
            { id: 'PENDING', label: 'Pendientes', count: rawActivities.filter((a) => a.submission_status === 'PENDING').length },
            { id: 'OVERDUE', label: 'Vencidas', count: rawActivities.filter((a) => a.submission_status === 'OVERDUE').length },
            { id: 'SUBMITTED', label: 'Entregadas', count: rawActivities.filter((a) => a.submission_status === 'SUBMITTED').length },
            { id: 'GRADED', label: 'Calificadas', count: rawActivities.filter((a) => a.submission_status === 'GRADED').length },
          ].map((pill) => {
            const isSelected = filterStatus === pill.id
            return (
              <button
                key={pill.id}
                type="button"
                onClick={() => setFilterStatus(pill.id as FilterStatus)}
                style={{
                  padding: '0.45rem 0.875rem',
                  borderRadius: '9999px',
                  border: isSelected ? '1px solid #0F172A' : '1px solid #E2E8F0',
                  backgroundColor: isSelected ? '#0F172A' : '#F8FAFC',
                  color: isSelected ? '#FFFFFF' : '#475569',
                  fontWeight: isSelected ? 700 : 500,
                  fontSize: '0.8125rem',
                  cursor: 'pointer',
                  transition: 'all 150ms ease',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                }}
              >
                <span>{pill.label}</span>
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
                  {pill.count}
                </span>
              </button>
            )
          })}
        </div>

        {/* Search & Subject Selector Row */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ flex: 1, minWidth: '220px' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="🔍 Buscar por título o tema de la actividad..."
              style={{
                width: '100%',
                padding: '0.625rem 0.875rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                color: '#0F172A',
                boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ minWidth: '200px' }}>
            <select
              value={filterSubject}
              onChange={(e) => setFilterSubject(e.target.value)}
              style={{
                width: '100%',
                padding: '0.625rem 0.875rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                color: '#0F172A',
                backgroundColor: '#FFFFFF',
                boxSizing: 'border-box',
              }}
            >
              <option value="ALL">Todas las asignaturas</option>
              {uniqueSubjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Task Cards Grid */}
      {filteredActivities.length === 0 ? (
        <GuardianEmptyState
          icon="📝"
          title="No se encontraron actividades"
          description="No hay tareas que coincidan con los filtros seleccionados."
          actionLabel="Ver todas las tareas"
          onAction={() => {
            setFilterStatus('ALL')
            setFilterSubject('ALL')
            setSearchQuery('')
          }}
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '1.25rem',
          }}
        >
          {filteredActivities.map((act) => (
            <GuardianTaskCard
              key={act.id}
              activity={act}
              onViewDetails={setSelectedTask}
            />
          ))}
        </div>
      )}

      {/* Task Details Modal */}
      {selectedTask && (
        <GuardianTaskDetailModal
          activity={selectedTask}
          onClose={() => setSelectedTask(null)}
        />
      )}
    </div>
  )
}
