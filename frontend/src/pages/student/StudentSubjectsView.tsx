/**
 * PEVN Frontend — Student Subjects View (Phase 14B)
 *
 * Displays all enrolled subjects for the active group:
 * - Subject name and knowledge area
 * - Weekly intensity hours
 * - Assigned educator and contact email
 * - Quick action to filter activities for that subject
 */

import React, { useState } from 'react'
import type { StudentSubjectItemResponse } from '@/types/student'
import { StudentEmptyState } from '@/components/student/StudentEmptyState'

interface StudentSubjectsViewProps {
  subjects: StudentSubjectItemResponse[]
  onSelectSubjectForTasks?: (subjectId: string) => void
}

export const StudentSubjectsView: React.FC<StudentSubjectsViewProps> = ({
  subjects,
  onSelectSubjectForTasks,
}) => {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredSubjects = subjects.filter((s) => {
    const q = searchTerm.toLowerCase()
    return (
      s.name.toLowerCase().includes(q) ||
      (s.teacher_name && s.teacher_name.toLowerCase().includes(q)) ||
      (s.knowledge_area_name && s.knowledge_area_name.toLowerCase().includes(q))
    )
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Search and Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
          padding: '1.25rem',
        }}
      >
        <div>
          <h2 style={{ margin: '0 0 0.25rem 0', fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
            Plan de Estudios y Asignaturas Matriculadas
          </h2>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748B' }}>
            Materias curriculares correspondientes a tu matrícula activa para el año lectivo en curso ({subjects.length} asignaturas).
          </p>
        </div>

        <div style={{ position: 'relative', width: '100%', maxWidth: '300px' }}>
          <input
            type="text"
            placeholder="Buscar por asignatura o docente..."
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
      </div>

      {/* Grid of Subjects */}
      {filteredSubjects.length === 0 ? (
        <StudentEmptyState
          icon="📚"
          title="No se encontraron asignaturas"
          description={
            searchTerm
              ? 'No hay materias que coincidan con el término de búsqueda.'
              : 'No tienes asignaturas registradas en tu grupo actual.'
          }
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '1.25rem',
          }}
        >
          {filteredSubjects.map((subj) => (
            <div
              key={subj.subject_id}
              style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '14px',
                border: '1px solid #E2E8F0',
                padding: '1.5rem',
                boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'transform 0.15s ease, box-shadow 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)'
                e.currentTarget.style.boxShadow = '0 6px 14px rgba(0,0,0,0.08)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.04)'
              }}
            >
              <div>
                {/* Area badge */}
                {subj.knowledge_area_name && (
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      color: '#6366F1',
                      backgroundColor: '#EEF2FF',
                      padding: '0.2rem 0.55rem',
                      borderRadius: '6px',
                      display: 'inline-block',
                      marginBottom: '0.5rem',
                    }}
                  >
                    Área: {subj.knowledge_area_name}
                  </span>
                )}

                <h3
                  style={{
                    margin: '0 0 0.75rem 0',
                    fontSize: '1.2rem',
                    fontWeight: 800,
                    color: '#0F172A',
                  }}
                >
                  {subj.name}
                </h3>

                {/* Info Card */}
                <div
                  style={{
                    backgroundColor: '#F8FAFC',
                    borderRadius: '10px',
                    padding: '1rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.6rem',
                    fontSize: '0.85rem',
                    marginBottom: '1rem',
                    border: '1px solid #F1F5F9',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>👨‍🏫</span>
                    <div>
                      <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem' }}>DOCENTE</span>
                      <strong style={{ color: '#1E293B' }}>{subj.teacher_name || 'Docente no asignado'}</strong>
                    </div>
                  </div>

                  {subj.teacher_email && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span>✉️</span>
                      <span style={{ color: '#3B82F6', fontSize: '0.8125rem' }}>{subj.teacher_email}</span>
                    </div>
                  )}

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>⏰</span>
                    <span style={{ color: '#475569' }}>
                      Intensidad horaria: <strong>{subj.weekly_hours} hora(s) semanales</strong>
                    </span>
                  </div>
                </div>
              </div>

              {/* Action */}
              {onSelectSubjectForTasks && (
                <button
                  onClick={() => onSelectSubjectForTasks(subj.subject_id)}
                  style={{
                    backgroundColor: '#EFF6FF',
                    color: '#1D4ED8',
                    border: '1px solid #BFDBFE',
                    padding: '0.65rem 1rem',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.4rem',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#1D4ED8'
                    e.currentTarget.style.color = '#FFFFFF'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#EFF6FF'
                    e.currentTarget.style.color = '#1D4ED8'
                  }}
                >
                  <span>Ver Tareas de {subj.name}</span>
                  <span aria-hidden="true">→</span>
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
