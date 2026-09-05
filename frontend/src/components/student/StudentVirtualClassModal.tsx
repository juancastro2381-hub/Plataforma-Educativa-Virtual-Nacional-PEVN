/**
 * PEVN Frontend — Student Virtual Classroom & Recordings Modal Component
 *
 * Provides:
 * - Direct classroom join instructions and room access
 * - Recordings archive player and list
 */

import React, { useEffect, useState } from 'react'
import type { StudentRecordingItemResponse, StudentVirtualClassroomItemResponse } from '@/types/student'
import { studentApi } from '@/services/student'
import { StudentStatusBadge } from './StudentStatusBadge'
import { formatDateTime } from '@/utils'

interface StudentVirtualClassModalProps {
  classroom: StudentVirtualClassroomItemResponse | null
  mode: 'join' | 'recordings'
  onClose: () => void
}

export const StudentVirtualClassModal: React.FC<StudentVirtualClassModalProps> = ({
  classroom,
  mode,
  onClose,
}) => {
  const [recordings, setRecordings] = useState<StudentRecordingItemResponse[]>([])
  const [loadingRecordings, setLoadingRecordings] = useState(false)
  const [selectedPlaybackUrl, setSelectedPlaybackUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (classroom && mode === 'recordings') {
      void fetchRecordings(classroom.id)
    }
  }, [classroom, mode])

  const fetchRecordings = async (classroomId: string) => {
    setLoadingRecordings(true)
    setError(null)
    try {
      const data = await studentApi.listRecordings(classroomId)
      setRecordings(data.items)
      if (data.items.length > 0 && data.items[0].playback_url) {
        setSelectedPlaybackUrl(data.items[0].playback_url)
      }
    } catch (err: unknown) {
      setError('No se pudieron cargar las grabaciones de la sesión.')
    } finally {
      setLoadingRecordings(false)
    }
  }

  if (!classroom) return null

  const isRunning = classroom.status === 'RUNNING'

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
          maxWidth: mode === 'recordings' ? '760px' : '600px',
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
              {classroom.subject_name && (
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
                  📖 {classroom.subject_name}
                </span>
              )}
              <StudentStatusBadge type="classroom" status={classroom.status} size="sm" />
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
              {classroom.title}
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
          {mode === 'join' ? (
            <>
              {/* Join Mode Content */}
              <div
                style={{
                  backgroundColor: isRunning ? '#DCFCE7' : '#EFF6FF',
                  border: isRunning ? '1px solid #86EFAC' : '1px solid #BFDBFE',
                  borderRadius: '12px',
                  padding: '1.25rem',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>
                  {isRunning ? '🟢' : '📅'}
                </div>
                <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.15rem', fontWeight: 800, color: isRunning ? '#15803D' : '#1D4ED8' }}>
                  {isRunning ? '¡La sesión está abierta y activa!' : 'Sesión Programada'}
                </h3>
                <p style={{ margin: 0, fontSize: '0.875rem', color: isRunning ? '#166534' : '#1E40AF', maxWidth: '440px', marginInline: 'auto' }}>
                  {isRunning
                    ? 'Tu docente y compañeros están en la sala. Haz clic en el botón inferior para conectarte de inmediato con audio y video.'
                    : 'La clase iniciará en el horario establecido. Podrás ingresar automáticamente cuando el docente inicie la sala.'}
                </p>
              </div>

              {/* Classroom metadata */}
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
                    DOCENTE MODERADOR
                  </span>
                  <strong style={{ color: '#1E293B' }}>{classroom.teacher_name || 'Docente Institucional'}</strong>
                </div>

                <div>
                  <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                    HORARIO PROGRAMADO
                  </span>
                  <strong style={{ color: '#1E293B' }}>
                    {classroom.scheduled_start_time ? formatDateTime(classroom.scheduled_start_time) : 'Sin horario fijado'}
                  </strong>
                </div>

                <div>
                  <span style={{ color: '#64748B', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>
                    SALA DE CONFERENCIA
                  </span>
                  <strong style={{ color: '#1E293B' }}>{classroom.room_name || 'Sala Virtual Segura'}</strong>
                </div>
              </div>

              {/* Join Checklist */}
              <div
                style={{
                  backgroundColor: '#FFFFFF',
                  border: '1px solid #E2E8F0',
                  borderRadius: '10px',
                  padding: '1rem',
                  fontSize: '0.85rem',
                  color: '#475569',
                }}
              >
                <strong style={{ color: '#0F172A', display: 'block', marginBottom: '0.4rem' }}>
                  💡 Recomendaciones antes de entrar:
                </strong>
                <ul style={{ margin: 0, paddingLeft: '1.25rem', lineHeight: 1.5 }}>
                  <li>Verifica que tu micrófono y cámara funcionen correctamente.</li>
                  <li>Usa audífonos para evitar eco y mejorar la calidad del audio.</li>
                  <li>Mantén el micrófono silenciado al ingresar hasta que el docente te dé la palabra.</li>
                </ul>
              </div>

              {/* Action */}
              <div style={{ marginTop: '0.5rem' }}>
                <a
                  href={`/virtual-classrooms`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    backgroundColor: isRunning ? '#16A34A' : '#1D4ED8',
                    color: '#FFFFFF',
                    textDecoration: 'none',
                    padding: '0.85rem 1.5rem',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    fontWeight: 800,
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    textAlign: 'center',
                  }}
                >
                  <span>{isRunning ? '🔴 ENTRAR A LA SALA AHORA' : '🚀 ABRIR SALA VIRTUAL'}</span>
                </a>
              </div>
            </>
          ) : (
            <>
              {/* Recordings Mode Content */}
              {loadingRecordings ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#64748B' }}>
                  <span>⏳ Cargando archivo de grabaciones...</span>
                </div>
              ) : error ? (
                <div style={{ padding: '1rem', backgroundColor: '#FEE2E2', color: '#991B1B', borderRadius: '8px' }}>
                  {error}
                </div>
              ) : recordings.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#64748B' }}>
                  <span>No hay grabaciones archivadas para esta clase virtual.</span>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {/* Selected Video Player or Link */}
                  {selectedPlaybackUrl && (
                    <div
                      style={{
                        backgroundColor: '#0F172A',
                        borderRadius: '12px',
                        padding: '1.5rem',
                        color: '#FFFFFF',
                        textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🎬</div>
                      <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', fontWeight: 700 }}>
                        Reproductor de Grabación de Clase
                      </h4>
                      <p style={{ margin: '0 0 1rem 0', fontSize: '0.85rem', color: '#94A3B8' }}>
                        Grabación oficial almacenada en el servidor seguro de PEVN.
                      </p>
                      <a
                        href={selectedPlaybackUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                          backgroundColor: '#2563EB',
                          color: '#FFFFFF',
                          textDecoration: 'none',
                          padding: '0.65rem 1.25rem',
                          borderRadius: '8px',
                          fontSize: '0.875rem',
                          fontWeight: 700,
                        }}
                      >
                        <span>▶ Ver Grabación en Pantalla Completa</span>
                        <span aria-hidden="true">↗</span>
                      </a>
                    </div>
                  )}

                  {/* Recordings List */}
                  <div>
                    <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', fontWeight: 700, color: '#1E293B' }}>
                      Grabaciones Disponibles ({recordings.length}):
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {recordings.map((rec) => (
                        <div
                          key={rec.id}
                          onClick={() => rec.playback_url && setSelectedPlaybackUrl(rec.playback_url)}
                          style={{
                            backgroundColor: selectedPlaybackUrl === rec.playback_url ? '#EFF6FF' : '#F8FAFC',
                            border:
                              selectedPlaybackUrl === rec.playback_url
                                ? '1px solid #3B82F6'
                                : '1px solid #E2E8F0',
                            borderRadius: '8px',
                            padding: '0.75rem 1rem',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            cursor: 'pointer',
                          }}
                        >
                          <div>
                            <strong style={{ display: 'block', fontSize: '0.875rem', color: '#0F172A' }}>
                              {rec.title}
                            </strong>
                            <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
                              Fecha: {formatDateTime(rec.created_at)}
                              {rec.duration_seconds && ` • Duración: ${Math.round(rec.duration_seconds / 60)} min`}
                            </span>
                          </div>

                          <span
                            style={{
                              fontSize: '0.8125rem',
                              fontWeight: 700,
                              color: '#1D4ED8',
                            }}
                          >
                            Reproducir ▶
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
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
