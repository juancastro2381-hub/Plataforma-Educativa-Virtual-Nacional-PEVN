/**
 * PEVN Frontend — Student Task Detail Modal Component
 *
 * Displays full academic activity instructions, due dates, grading details,
 * teacher feedback, and attached resources.
 */

import React from 'react'
import type { StudentActivityItemResponse } from '@/types/student'
import { StudentStatusBadge } from './StudentStatusBadge'
import { formatDateTime } from '@/utils'

interface StudentTaskDetailModalProps {
  activity: StudentActivityItemResponse | null
  onClose: () => void
}

export const StudentTaskDetailModal: React.FC<StudentTaskDetailModalProps> = ({
  activity,
  onClose,
}) => {
  if (!activity) return null

  const isGraded = activity.submission_status === 'GRADED'

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '1rem',
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          maxWidth: '680px',
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
          border: '1px solid #E2E8F0',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '1.5rem',
            borderBottom: '1px solid #E2E8F0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '1rem',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  color: '#1E40AF',
                  backgroundColor: '#EFF6FF',
                  padding: '0.2rem 0.55rem',
                  borderRadius: '6px',
                  border: '1px solid #DBEAFE',
                }}
              >
                📖 {activity.subject_name}
              </span>
              <StudentStatusBadge type="submission" status={activity.submission_status} size="sm" />
            </div>

            <h2
              style={{
                margin: 0,
                fontSize: '1.25rem',
                fontWeight: 800,
                color: '#0F172A',
                lineHeight: 1.3,
              }}
            >
              {activity.title}
            </h2>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              color: '#94A3B8',
              cursor: 'pointer',
              padding: '0.2rem 0.5rem',
              borderRadius: '6px',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#0F172A')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#94A3B8')}
            aria-label="Cerrar modal"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Metadata Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '0.75rem',
              backgroundColor: '#F8FAFC',
              padding: '1rem',
              borderRadius: '10px',
              border: '1px solid #E2E8F0',
              fontSize: '0.85rem',
            }}
          >
            <div>
              <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                DOCENTE RESPONSABLE
              </span>
              <strong style={{ color: '#1E293B' }}>{activity.teacher_name || 'No especificado'}</strong>
            </div>

            <div>
              <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                FECHA DE ENTREGA
              </span>
              <strong style={{ color: '#1E293B' }}>
                {activity.due_date ? formatDateTime(activity.due_date) : 'Sin fecha límite'}
              </strong>
            </div>

            <div>
              <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                PUNTAJE MÁXIMO
              </span>
              <strong style={{ color: '#1E293B' }}>{Number(activity.max_score).toFixed(1)} Puntos</strong>
            </div>
          </div>

          {/* Instructions / Description */}
          <div>
            <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
              📝 Instrucciones de la Actividad
            </h4>
            <div
              style={{
                backgroundColor: '#FFFFFF',
                border: '1px solid #E2E8F0',
                borderRadius: '8px',
                padding: '1rem',
                fontSize: '0.875rem',
                color: '#334155',
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
              }}
            >
              {activity.instructions || activity.description || 'No se registraron instrucciones adicionales para esta actividad.'}
            </div>
          </div>

          {/* Attached Resource / External URL */}
          {activity.resource_url && (
            <div
              style={{
                backgroundColor: '#EFF6FF',
                border: '1px solid #BFDBFE',
                borderRadius: '8px',
                padding: '1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '0.75rem',
              }}
            >
              <div>
                <span style={{ fontWeight: 700, color: '#1E40AF', display: 'block', fontSize: '0.875rem' }}>
                  📎 Material de Apoyo / Recurso Adjunto
                </span>
                <span style={{ fontSize: '0.75rem', color: '#3B82F6', wordBreak: 'break-all' }}>
                  {activity.resource_url}
                </span>
              </div>

              <a
                href={activity.resource_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  backgroundColor: '#1D4ED8',
                  color: '#FFFFFF',
                  textDecoration: 'none',
                  padding: '0.45rem 0.9rem',
                  borderRadius: '6px',
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                }}
              >
                <span>Abrir Recurso</span>
                <span aria-hidden="true">↗</span>
              </a>
            </div>
          )}

          {/* Graded Feedback Section */}
          {isGraded && (
            <div
              style={{
                backgroundColor: '#F0FDF4',
                border: '1px solid #BBF7D0',
                borderRadius: '10px',
                padding: '1.25rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 800, color: '#15803D' }}>
                  🎯 Evaluación y Retroalimentación Pedagógica
                </h4>
                {activity.score !== null && (
                  <span
                    style={{
                      fontSize: '1.15rem',
                      fontWeight: 800,
                      color: '#15803D',
                      backgroundColor: '#DCFCE7',
                      padding: '0.2rem 0.6rem',
                      borderRadius: '8px',
                      border: '1px solid #86EFAC',
                    }}
                  >
                    Nota: {Number(activity.score).toFixed(1)} / {Number(activity.max_score).toFixed(1)}
                  </span>
                )}
              </div>

              {activity.feedback ? (
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#166534', lineHeight: 1.5 }}>
                  "{activity.feedback}"
                </p>
              ) : (
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#166534', fontStyle: 'italic' }}>
                  Actividad calificada sin observaciones adicionales.
                </p>
              )}

              {activity.graded_at && (
                <div style={{ fontSize: '0.75rem', color: '#4ADE80', marginTop: '0.5rem' }}>
                  Calificado el: {formatDateTime(activity.graded_at)}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderTop: '1px solid #E2E8F0',
            backgroundColor: '#F8FAFC',
            borderRadius: '0 0 16px 16px',
            display: 'flex',
            justifyContent: 'flex-end',
          }}
        >
          <button
            onClick={onClose}
            style={{
              backgroundColor: '#0F172A',
              color: '#FFFFFF',
              border: 'none',
              padding: '0.6rem 1.25rem',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
