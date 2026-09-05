/**
 * PEVN Frontend — Guardian Task Detail Modal Component
 *
 * Read-only modal displaying detailed assignment instructions, pedagogical resources,
 * due date, and qualitative educator feedback for parental supervision.
 */

import React from 'react'
import type { StudentActivityItemResponse } from '@/types/student'
import { StudentStatusBadge } from '@/components/student/StudentStatusBadge'

interface Props {
  activity: StudentActivityItemResponse | null
  onClose: () => void
}

export const GuardianTaskDetailModal: React.FC<Props> = ({ activity, onClose }) => {
  if (!activity) return null

  const formatFullDate = (dateStr: string | null) => {
    if (!dateStr) return 'Sin fecha programada'
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString('es-CO', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(3px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
        padding: '1rem',
      }}
    >
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          maxWidth: '680px',
          width: '100%',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          border: '1px solid #E2E8F0',
          overflow: 'hidden',
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '1.25rem 1.75rem',
            backgroundColor: '#0F172A',
            color: '#FFFFFF',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '1rem',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem', flexWrap: 'wrap' }}>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  backgroundColor: 'rgba(56, 189, 248, 0.2)',
                  color: '#38BDF8',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '9999px',
                }}
              >
                📖 {activity.subject_name}
              </span>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  backgroundColor: 'rgba(255, 255, 255, 0.15)',
                  color: '#FFFFFF',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '9999px',
                }}
              >
                {activity.activity_type}
              </span>
            </div>

            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#FFFFFF' }}>
              {activity.title}
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: '#94A3B8',
              lineHeight: 1,
              padding: '0.25rem',
            }}
          >
            ✕
          </button>
        </div>

        {/* Modal Scrollable Content */}
        <div style={{ padding: '1.5rem 1.75rem', overflowY: 'auto', flex: 1 }}>
          {/* Status & Deadline Card */}
          <div
            style={{
              backgroundColor: '#F8FAFC',
              borderRadius: '12px',
              padding: '1rem 1.25rem',
              border: '1px solid #E2E8F0',
              marginBottom: '1.25rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
            }}
          >
            <div>
              <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>
                ESTADO DE LA ENTREGA
              </div>
              <div style={{ marginTop: '0.25rem' }}>
                <StudentStatusBadge status={activity.submission_status} type="submission" />
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>
                FECHA LÍMITE DE ENTREGA
              </div>
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A', marginTop: '0.25rem' }}>
                {formatFullDate(activity.due_date)}
              </div>
            </div>

            {activity.teacher_name && (
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>
                  DOCENTE TITULAR
                </div>
                <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A', marginTop: '0.25rem' }}>
                  👨‍🏫 {activity.teacher_name}
                </div>
              </div>
            )}
          </div>

          {/* Description & Instructions */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9375rem', fontWeight: 800, color: '#0F172A' }}>
              📝 Descripción y Objetivos de la Actividad
            </h4>
            <div
              style={{
                fontSize: '0.875rem',
                color: '#334155',
                lineHeight: 1.6,
                backgroundColor: '#FFFFFF',
                padding: '0.875rem 1rem',
                borderRadius: '8px',
                border: '1px solid #E2E8F0',
                whiteSpace: 'pre-wrap',
              }}
            >
              {activity.description || 'Sin descripción general disponible.'}
            </div>
          </div>

          {activity.instructions && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9375rem', fontWeight: 800, color: '#0F172A' }}>
                📋 Instrucciones Pedagógicas
              </h4>
              <div
                style={{
                  fontSize: '0.875rem',
                  color: '#334155',
                  lineHeight: 1.6,
                  backgroundColor: '#F8FAFC',
                  padding: '0.875rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid #E2E8F0',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {activity.instructions}
              </div>
            </div>
          )}

          {/* Attached Resources */}
          {activity.resource_url && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9375rem', fontWeight: 800, color: '#0F172A' }}>
                📎 Recursos y Material de Apoyo
              </h4>
              <a
                href={activity.resource_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.625rem 1rem',
                  borderRadius: '8px',
                  backgroundColor: '#EFF6FF',
                  color: '#1D4ED8',
                  border: '1px solid #BFDBFE',
                  textDecoration: 'none',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                }}
              >
                <span>🔗</span>
                <span>Abrir Recurso / Guía Adjunta</span>
              </a>
            </div>
          )}

          {/* Grade & Teacher Feedback (If Graded) */}
          {activity.submission_status === 'GRADED' && activity.score !== null && (
            <div
              style={{
                backgroundColor: '#F0FDF4',
                border: '1px solid #86EFAC',
                borderRadius: '12px',
                padding: '1.25rem',
                marginBottom: '1.5rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 800, color: '#166534' }}>
                  🎯 Calificación Oficial Otorgada
                </span>
                <span style={{ fontSize: '1.375rem', fontWeight: 800, color: '#15803D' }}>
                  {Number(activity.score).toFixed(1)} / {Number(activity.max_score).toFixed(1)}
                </span>
              </div>

              {activity.feedback && (
                <div style={{ marginTop: '0.5rem', borderTop: '1px solid #BBF7D0', paddingTop: '0.5rem' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#166534', marginBottom: '0.25rem' }}>
                    💬 Observaciones y Retroalimentación Docente:
                  </div>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: '#14532D', fontStyle: 'italic', lineHeight: 1.5 }}>
                    "{activity.feedback}"
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Explicit Parental Supervision Notice */}
          <div
            style={{
              backgroundColor: '#F1F5F9',
              border: '1px solid #CBD5E1',
              borderRadius: '10px',
              padding: '0.875rem 1rem',
              fontSize: '0.8125rem',
              color: '#475569',
              lineHeight: 1.5,
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
            }}
          >
            <span style={{ fontSize: '1.25rem' }}>ℹ️</span>
            <div>
              <strong>Supervisión Familiar:</strong> Puedes consultar y acompañar el progreso de esta tarea. La entrega y desarrollo de actividades académicas corresponde exclusivamente al estudiante.
            </div>
          </div>
        </div>

        {/* Modal Footer (Read-Only) */}
        <div
          style={{
            padding: '1rem 1.75rem',
            borderTop: '1px solid #E2E8F0',
            backgroundColor: '#F8FAFC',
            display: 'flex',
            justifyContent: 'flex-end',
          }}
        >
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: '0.625rem 1.25rem',
              borderRadius: '8px',
              backgroundColor: '#0F172A',
              color: '#FFFFFF',
              border: 'none',
              fontSize: '0.875rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Cerrar Vista
          </button>
        </div>
      </div>
    </div>
  )
}
