/**
 * PEVN Frontend — Teacher My Groups View (Mis Grupos y Salones)
 *
 * Displays cards of groups assigned to the teacher and an interactive modal
 * to view the official student roster (Planilla Pedagógica de Estudiantes).
 */

import React, { useState } from 'react'
import type { TeacherGroupItemResponse, TeacherGroupRosterResponse } from '@/types/teacher'
import { teacherApi } from '@/services/teacher'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

interface Props {
  groups: TeacherGroupItemResponse[]
  teacherName?: string
  loading: boolean
  onNavigateToTab?: (tab: string, context?: { groupId?: string }) => void
}

export const TeacherGroupsView: React.FC<Props> = ({ groups, teacherName, loading, onNavigateToTab }) => {
  const [selectedGroup, setSelectedGroup] = useState<TeacherGroupItemResponse | null>(null)
  const [rosterData, setRosterData] = useState<TeacherGroupRosterResponse | null>(null)
  const [rosterLoading, setRosterLoading] = useState(false)
  const [rosterError, setRosterError] = useState<string | null>(null)

  const handleOpenRoster = async (group: TeacherGroupItemResponse) => {
    setSelectedGroup(group)
    setRosterLoading(true)
    setRosterError(null)
    try {
      const data = await teacherApi.getGroupRoster(group.group_id)
      setRosterData(data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar la planilla del grupo.'
      setRosterError(msg)
    } finally {
      setRosterLoading(false)
    }
  }

  const handleCloseModal = () => {
    setSelectedGroup(null)
    setRosterData(null)
    setRosterError(null)
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: '#64748B' }}>
        <LoadingSpinner size="lg" />
        <p style={{ marginTop: '0.75rem', fontSize: '0.875rem' }}>Cargando grupos y salones asignados...</p>
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
            Mis Grupos y Salones de Clase
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
            Salones académicos autorizados con matrícula activa. Seleccione un grupo para consultar su planilla pedagógica oficial.
          </p>
        </div>
      </div>

      {groups.length === 0 ? (
        <div
          style={{
            padding: '3.5rem 1.5rem',
            textAlign: 'center',
            backgroundColor: '#F8FAFC',
            borderRadius: '12px',
            border: '2px dashed #CBD5E1',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏫</div>
          <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: 800, color: '#1E293B' }}>
            No tiene grupos o salones asignados
          </h4>
          <p style={{ margin: '0 auto 1.5rem auto', maxWidth: '520px', fontSize: '0.875rem', color: '#64748B', lineHeight: 1.6 }}>
            Su usuario no posee asignaciones activas de materias ni dirección de grupo en el año lectivo vigente.
          </p>
          <div style={{ fontSize: '0.8125rem', color: '#475569' }}>
            📌 <em>Solicite a la Rectoría de su establecimiento educativo la vinculación de su carga académica para acceder a las listas de estudiantes.</em>
          </div>
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr)))',
            gap: '1.25rem',
          }}
        >
          {groups.map((grp) => (
            <div
              key={grp.group_id}
              style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '14px',
                border: '1px solid #E2E8F0',
                padding: '1.5rem',
                boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'transform 150ms, box-shadow 150ms',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
                      Grupo {grp.group_name}
                    </h3>
                    <div style={{ fontSize: '0.8125rem', color: '#64748B', marginTop: '0.2rem' }}>
                      {grp.grade_name || 'N/A'} • {grp.campus_name || 'Sede Principal'}
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.35rem' }}>
                    <span
                      style={{
                        padding: '0.25rem 0.6rem',
                        borderRadius: '9999px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        backgroundColor: '#EFF6FF',
                        color: '#2563EB',
                      }}
                    >
                      {grp.shift || 'MAÑANA'}
                    </span>
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: '#F8FAFC',
                    borderRadius: '8px',
                    padding: '0.875rem',
                    marginBottom: '1.25rem',
                    fontSize: '0.8125rem',
                    border: '1px solid #F1F5F9',
                  }}
                >
                  <div style={{ color: '#475569', marginBottom: '0.35rem' }}>
                    <strong>Año Lectivo:</strong> {grp.academic_year_name}
                  </div>
                  <div style={{ color: '#475569', marginBottom: '0.35rem' }}>
                    <strong>Estudiantes Matriculados:</strong> <span style={{ fontWeight: 700, color: '#7E22CE' }}>{grp.active_enrolled_count}</span> / {grp.capacity_limit} cupos
                  </div>
                  <div style={{ color: '#475569' }}>
                    <strong>Materias que Imparte:</strong> {grp.subjects_taught.length > 0 ? grp.subjects_taught.join(', ') : 'Asignación Institucional'}
                  </div>
                </div>

                {/* Contextual Actions Bar */}
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                    Navegación Contextual del Salón:
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.4rem', marginBottom: '0.4rem' }}>
                    <button
                      type="button"
                      data-testid={`btn-context-activities-${grp.group_id}`}
                      onClick={() => onNavigateToTab?.('activities', { groupId: grp.group_id })}
                      style={{
                        padding: '0.45rem 0.5rem',
                        borderRadius: '6px',
                        border: '1px solid #CBD5E1',
                        backgroundColor: '#F8FAFC',
                        color: '#334155',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        justifyContent: 'center',
                      }}
                    >
                      <span>📝</span> Actividades
                    </button>
                    <button
                      type="button"
                      data-testid={`btn-context-grades-${grp.group_id}`}
                      onClick={() => onNavigateToTab?.('grades', { groupId: grp.group_id })}
                      style={{
                        padding: '0.45rem 0.5rem',
                        borderRadius: '6px',
                        border: '1px solid #CBD5E1',
                        backgroundColor: '#F8FAFC',
                        color: '#334155',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        justifyContent: 'center',
                      }}
                    >
                      <span>📊</span> Calificaciones
                    </button>
                    <button
                      type="button"
                      data-testid={`btn-context-attendance-${grp.group_id}`}
                      onClick={() => onNavigateToTab?.('attendance', { groupId: grp.group_id })}
                      style={{
                        padding: '0.45rem 0.5rem',
                        borderRadius: '6px',
                        border: '1px solid #CBD5E1',
                        backgroundColor: '#F8FAFC',
                        color: '#334155',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        justifyContent: 'center',
                      }}
                    >
                      <span>📋</span> Asistencia
                    </button>
                    <button
                      type="button"
                      data-testid={`btn-context-planning-${grp.group_id}`}
                      onClick={() => onNavigateToTab?.('planning', { groupId: grp.group_id })}
                      style={{
                        padding: '0.45rem 0.5rem',
                        borderRadius: '6px',
                        border: '1px solid #CBD5E1',
                        backgroundColor: '#F8FAFC',
                        color: '#334155',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        justifyContent: 'center',
                      }}
                    >
                      <span>🎯</span> Planeación
                    </button>
                  </div>
                  <button
                    type="button"
                    data-testid={`btn-context-coexistence-${grp.group_id}`}
                    onClick={() => onNavigateToTab?.('coexistence', { groupId: grp.group_id })}
                    style={{
                      width: '100%',
                      padding: '0.45rem 0.5rem',
                      borderRadius: '6px',
                      border: '1px solid #CBD5E1',
                      backgroundColor: '#F8FAFC',
                      color: '#334155',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      justifyContent: 'center',
                    }}
                  >
                    <span>🛡️</span> Observador / Convivencia
                  </button>
                </div>
              </div>

              <button
                type="button"
                data-testid="btn-open-roster"
                onClick={() => void handleOpenRoster(grp)}
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  backgroundColor: '#1E3A8A',
                  color: '#FFFFFF',
                  border: 'none',
                  fontWeight: 700,
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                }}
              >
                👥 Ver Planilla de Estudiantes
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Group Roster Modal */}
      {selectedGroup && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.65)',
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
              maxWidth: '850px',
              width: '100%',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            }}
          >
            {/* Modal Header with Full Context */}
            <div
              style={{
                padding: '1.25rem 1.75rem',
                borderBottom: '1px solid #E2E8F0',
                backgroundColor: '#0F172A',
                color: '#FFFFFF',
                borderRadius: '16px 16px 0 0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
              }}
            >
              <div>
                <div
                  style={{
                    display: 'inline-block',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    backgroundColor: 'rgba(56, 189, 248, 0.2)',
                    color: '#38BDF8',
                    padding: '0.2rem 0.6rem',
                    borderRadius: '9999px',
                    marginBottom: '0.35rem',
                  }}
                >
                  Planilla Pedagógica Oficial
                </div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#FFFFFF' }}>
                  Grupo {selectedGroup.group_name} — {selectedGroup.grade_name || 'Grado'}
                </h3>
                <div style={{ marginTop: '0.35rem', fontSize: '0.8125rem', color: '#94A3B8', display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
                  <span>👨‍🏫 <strong>Docente:</strong> {teacherName || 'Docente Titular'}</span>
                  <span>📖 <strong>Materias:</strong> {selectedGroup.subjects_taught?.join(', ') || 'Carga Institucional'}</span>
                  <span>🏫 <strong>Sede:</strong> {selectedGroup.campus_name || 'Principal'}</span>
                  <span>📅 <strong>Año:</strong> {selectedGroup.academic_year_name}</span>
                </div>
              </div>
              <button
                onClick={handleCloseModal}
                style={{
                  background: 'transparent',
                  border: 'none',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  color: '#94A3B8',
                  lineHeight: 1,
                  padding: '0.25rem',
                }}
                aria-label="Cerrar modal"
              >
                ✕
              </button>
            </div>

            {/* Modal Content */}
            <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>
              {rosterLoading && (
                <div style={{ textAlign: 'center', padding: '3rem' }}>
                  <LoadingSpinner size="lg" />
                  <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
                    Cargando nómina de estudiantes matriculados...
                  </p>
                </div>
              )}

              {rosterError && (
                <div
                  style={{
                    backgroundColor: '#FEF2F2',
                    border: '1px solid #FCA5A5',
                    borderRadius: '8px',
                    padding: '1rem',
                    color: '#991B1B',
                    fontSize: '0.875rem',
                  }}
                >
                  {rosterError}
                </div>
              )}

              {rosterData && (
                <div>
                  <div
                    style={{
                      marginBottom: '1.25rem',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      backgroundColor: '#F8FAFC',
                      padding: '0.75rem 1rem',
                      borderRadius: '8px',
                      border: '1px solid #E2E8F0',
                    }}
                  >
                    <span style={{ fontSize: '0.875rem', color: '#334155', fontWeight: 700 }}>
                      👥 Total Estudiantes con Matrícula Activa: {rosterData.total_students}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
                      Capacidad del Salón: {selectedGroup.capacity_limit} cupos
                    </span>
                  </div>

                  {rosterData.students.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '2.5rem', color: '#64748B' }}>
                      No hay estudiantes con matrícula activa en este salón.
                    </div>
                  ) : (
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', textAlign: 'left' }}>
                        <thead>
                          <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569', backgroundColor: '#F8FAFC' }}>
                            <th style={{ padding: '0.625rem 0.75rem' }}>#</th>
                            <th style={{ padding: '0.625rem 0.75rem' }}>Estudiante</th>
                            <th style={{ padding: '0.625rem 0.75rem' }}>Documento</th>
                            <th style={{ padding: '0.625rem 0.75rem' }}>Código SIMAT</th>
                            <th style={{ padding: '0.625rem 0.75rem', textAlign: 'center' }}>Estado Matrícula</th>
                          </tr>
                        </thead>
                        <tbody>
                          {rosterData.students.map((st, idx) => (
                            <tr key={st.student_id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                              <td style={{ padding: '0.75rem', color: '#94A3B8', fontWeight: 700 }}>
                                {idx + 1}
                              </td>
                              <td style={{ padding: '0.75rem', fontWeight: 700, color: '#0F172A' }}>
                                {st.full_name}
                              </td>
                              <td style={{ padding: '0.75rem', color: '#475569' }}>
                                {st.document_type}: {st.document_number}
                              </td>
                              <td style={{ padding: '0.75rem', color: '#64748B', fontFamily: 'monospace' }}>
                                {st.simat_code || 'SIN SIMAT'}
                              </td>
                              <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                                <span
                                  style={{
                                    padding: '0.2rem 0.6rem',
                                    borderRadius: '9999px',
                                    fontSize: '0.75rem',
                                    fontWeight: 700,
                                    backgroundColor: '#DCFCE7',
                                    color: '#15803D',
                                  }}
                                >
                                  {st.enrollment_status}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
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
                display: 'flex',
                justifyContent: 'flex-end',
                backgroundColor: '#F8FAFC',
                borderRadius: '0 0 16px 16px',
              }}
            >
              <Button variant="secondary" onClick={handleCloseModal}>
                Cerrar Planilla
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TeacherGroupsView
