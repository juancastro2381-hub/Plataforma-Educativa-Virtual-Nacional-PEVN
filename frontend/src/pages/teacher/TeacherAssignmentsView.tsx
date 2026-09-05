/**
 * PEVN Frontend — Teacher My Academic Load View (Mi Carga Académica)
 *
 * Displays official pedagogical assignments allocated by Rector:
 * Teacher → Subject → Grade / Group → Enrolled Students Roster.
 */

import React, { useMemo, useState } from 'react'
import type {
  TeacherAssignmentItemResponse,
  TeacherGroupItemResponse,
  TeacherGroupRosterResponse,
} from '@/types/teacher'
import { teacherApi } from '@/services/teacher'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

interface Props {
  assignments: TeacherAssignmentItemResponse[]
  groups?: TeacherGroupItemResponse[]
  teacherName?: string
  totalUniqueStudents?: number
  loading: boolean
}

export const TeacherAssignmentsView: React.FC<Props> = ({
  assignments,
  groups = [],
  teacherName,
  totalUniqueStudents,
  loading,
}) => {
  // Map group_id -> TeacherGroupItemResponse for fast student count and metadata resolution
  const groupMap = useMemo(() => {
    const map = new Map<string, TeacherGroupItemResponse>()
    for (const g of groups) {
      map.set(g.group_id, g)
    }
    return map
  }, [groups])

  // Unique subjects and groups count
  const uniqueSubjectsCount = useMemo(() => {
    return new Set(assignments.map((a) => a.subject_id)).size
  }, [assignments])

  const uniqueGroupsCount = useMemo(() => {
    return new Set(assignments.map((a) => a.group_id)).size
  }, [assignments])

  const totalWeeklyHours = useMemo(() => {
    return assignments.reduce((sum, a) => sum + a.weekly_hours, 0)
  }, [assignments])

  // De-duplicated unique student count calculation fallback if not passed directly
  const calculatedUniqueStudents = useMemo(() => {
    if (totalUniqueStudents !== undefined) return totalUniqueStudents
    // Sum active enrolled counts of unique groups
    const seenGroups = new Set<string>()
    let count = 0
    for (const a of assignments) {
      if (!seenGroups.has(a.group_id)) {
        seenGroups.add(a.group_id)
        const g = groupMap.get(a.group_id)
        if (g) {
          count += g.active_enrolled_count
        }
      }
    }
    return count
  }, [assignments, groupMap, totalUniqueStudents])

  // Roster Modal state
  const [selectedAssignment, setSelectedAssignment] = useState<TeacherAssignmentItemResponse | null>(null)
  const [rosterData, setRosterData] = useState<TeacherGroupRosterResponse | null>(null)
  const [rosterLoading, setRosterLoading] = useState(false)
  const [rosterError, setRosterError] = useState<string | null>(null)

  const handleOpenRoster = async (assignment: TeacherAssignmentItemResponse) => {
    setSelectedAssignment(assignment)
    setRosterLoading(true)
    setRosterError(null)
    try {
      const data = await teacherApi.getGroupRoster(assignment.group_id)
      setRosterData(data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar la planilla de estudiantes del grupo.'
      setRosterError(msg)
    } finally {
      setRosterLoading(false)
    }
  }

  const handleCloseRosterModal = () => {
    setSelectedAssignment(null)
    setRosterData(null)
    setRosterError(null)
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: '#64748B' }}>
        <LoadingSpinner size="lg" />
        <p style={{ marginTop: '0.75rem', fontSize: '0.875rem' }}>Cargando asignaciones académicas...</p>
      </div>
    )
  }

  return (
    <div>
      {/* Educational Notice Banner */}
      <div
        style={{
          backgroundColor: '#EFF6FF',
          border: '1px solid #BFDBFE',
          borderRadius: '12px',
          padding: '1rem 1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
        }}
      >
        <span style={{ fontSize: '1.5rem' }}>ℹ️</span>
        <div style={{ fontSize: '0.875rem', color: '#1E40AF', lineHeight: 1.5 }}>
          <strong>Jerarquía Pedagógica Oficial:</strong> Su ámbito académico está delimitado por las materias y salones autorizados por la Rectoría: <code>Docente → Asignatura → Salón/Grupo → Estudiantes Matriculados</code>. La visibilidad de listas de estudiantes se restringe exclusivamente a los cursos que imparte.
        </div>
      </div>

      {/* Summary KPI Counters */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          marginBottom: '1.75rem',
        }}
      >
        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: '12px',
            padding: '1.25rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Asignaturas Asignadas
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#1E3A8A', marginTop: '0.25rem' }}>
            {uniqueSubjectsCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
            Materias en plan de estudios
          </div>
        </div>

        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: '12px',
            padding: '1.25rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Grupos / Salones
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F766E', marginTop: '0.25rem' }}>
            {uniqueGroupsCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
            Cursos con carga activa
          </div>
        </div>

        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: '12px',
            padding: '1.25rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Estudiantes Únicos
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#7C3AED', marginTop: '0.25rem' }}>
            {calculatedUniqueStudents}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
            Total alumnos a su cargo
          </div>
        </div>

        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: '12px',
            padding: '1.25rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Intensidad Horaria
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#EA580C', marginTop: '0.25rem' }}>
            {totalWeeklyHours} <span style={{ fontSize: '1rem', fontWeight: 600 }}>h/sem</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
            Horas lectivas semanales
          </div>
        </div>
      </div>

      {/* Main Workload Container */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          border: '1px solid #E2E8F0',
          padding: '1.75rem',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
              Mi Carga Académica Asignada
            </h3>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8125rem', color: '#64748B' }}>
              Planilla oficial de materias y salones autorizados para {teacherName || 'su perfil docente'}.
            </p>
          </div>
        </div>

        {assignments.length === 0 ? (
          /* High-Quality Empty State for Unassigned Teachers */
          <div
            style={{
              padding: '3.5rem 1.5rem',
              textAlign: 'center',
              backgroundColor: '#F8FAFC',
              borderRadius: '12px',
              border: '2px dashed #CBD5E1',
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📚</div>
            <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: 800, color: '#1E293B' }}>
              Sin carga académica asignada
            </h4>
            <p style={{ margin: '0 auto 1.5rem auto', maxWidth: '520px', fontSize: '0.875rem', color: '#64748B', lineHeight: 1.6 }}>
              Su cuenta y perfil docente se encuentran <strong>activos</strong>, pero aún no tiene materias ni salones asignados para el año lectivo en curso.
            </p>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '1.5rem',
                backgroundColor: '#FFFFFF',
                padding: '0.75rem 1.5rem',
                borderRadius: '9999px',
                border: '1px solid #E2E8F0',
                fontSize: '0.8125rem',
                color: '#475569',
                fontWeight: 600,
                marginBottom: '1.5rem',
              }}
            >
              <span>Asignaturas: <strong>0</strong></span>
              <span>•</span>
              <span>Grupos: <strong>0</strong></span>
              <span>•</span>
              <span>Estudiantes: <strong>0</strong></span>
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#475569' }}>
              📌 <em>Comuníquese con la Rectoría o Coordinación Académica de su institución educativa para la asignación oficial de sus asignaturas y salones.</em>
            </div>
          </div>
        ) : (
          /* Active Workload Table */
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569', backgroundColor: '#F8FAFC' }}>
                  <th style={{ padding: '0.875rem 1rem', borderRadius: '8px 0 0 0' }}>Asignatura / Área</th>
                  <th style={{ padding: '0.875rem 1rem' }}>Curso / Grado / Grupo</th>
                  <th style={{ padding: '0.875rem 1rem' }}>Sede & Jornada</th>
                  <th style={{ padding: '0.875rem 1rem', textAlign: 'center' }}>Estudiantes en Salón</th>
                  <th style={{ padding: '0.875rem 1rem', textAlign: 'center' }}>Horas / Sem</th>
                  <th style={{ padding: '0.875rem 1rem', textAlign: 'center' }}>Estado</th>
                  <th style={{ padding: '0.875rem 1rem', textAlign: 'right', borderRadius: '0 8px 0 0' }}>Acción</th>
                </tr>
              </thead>
              <tbody>
                {assignments.map((a) => {
                  const grp = groupMap.get(a.group_id)
                  const studentCount = grp ? grp.active_enrolled_count : '—'

                  return (
                    <tr
                      key={a.id}
                      style={{
                        borderBottom: '1px solid #F1F5F9',
                        transition: 'background-color 150ms',
                      }}
                    >
                      {/* Asignatura */}
                      <td style={{ padding: '1rem', fontWeight: 700, color: '#1E3A8A' }}>
                        <div style={{ fontSize: '0.9375rem' }}>{a.subject_name}</div>
                        {a.knowledge_area_name && (
                          <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 400, marginTop: '0.15rem' }}>
                            {a.knowledge_area_name}
                          </div>
                        )}
                      </td>

                      {/* Grupo / Salón */}
                      <td style={{ padding: '1rem', fontWeight: 700, color: '#0F172A' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <span style={{ fontSize: '1rem' }}>🏫</span>
                          <span>Grupo {a.group_name}</span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 400, marginTop: '0.15rem' }}>
                          {a.grade_name ? `Grado ${a.grade_name}` : 'Grado N/A'} • {a.academic_year_name}
                        </div>
                      </td>

                      {/* Sede y Jornada */}
                      <td style={{ padding: '1rem', color: '#475569' }}>
                        <div>{a.campus_name || 'Sede Principal'}</div>
                        <span
                          style={{
                            display: 'inline-block',
                            marginTop: '0.2rem',
                            padding: '0.15rem 0.5rem',
                            borderRadius: '9999px',
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            backgroundColor: '#F1F5F9',
                            color: '#475569',
                          }}
                        >
                          {a.shift || 'MAÑANA'}
                        </span>
                      </td>

                      {/* Estudiantes */}
                      <td style={{ padding: '1rem', textAlign: 'center' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            padding: '0.25rem 0.75rem',
                            borderRadius: '9999px',
                            fontSize: '0.8125rem',
                            fontWeight: 700,
                            backgroundColor: '#F3E8FF',
                            color: '#7E22CE',
                          }}
                        >
                          👥 {studentCount} {typeof studentCount === 'number' ? 'estudiantes' : ''}
                        </span>
                      </td>

                      {/* Horas */}
                      <td style={{ padding: '1rem', textAlign: 'center', fontWeight: 700, color: '#1E293B' }}>
                        {a.weekly_hours} h/sem
                      </td>

                      {/* Estado */}
                      <td style={{ padding: '1rem', textAlign: 'center' }}>
                        <span
                          style={{
                            display: 'inline-block',
                            padding: '0.2rem 0.6rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            backgroundColor: a.is_active ? '#DCFCE7' : '#F1F5F9',
                            color: a.is_active ? '#15803D' : '#64748B',
                          }}
                        >
                          {a.is_active ? 'ACTIVA' : 'INACTIVA'}
                        </span>
                      </td>

                      {/* Acción */}
                      <td style={{ padding: '1rem', textAlign: 'right' }}>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => void handleOpenRoster(a)}
                          style={{
                            fontSize: '0.8125rem',
                            fontWeight: 600,
                            whiteSpace: 'nowrap',
                          }}
                        >
                          👥 Ver Planilla
                        </Button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Contextual Roster Modal */}
      {selectedAssignment && (
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
            {/* Modal Header with Rich Academic Context */}
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
                  Grupo {selectedAssignment.group_name} — {selectedAssignment.subject_name}
                </h3>
                <div style={{ marginTop: '0.35rem', fontSize: '0.8125rem', color: '#94A3B8', display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
                  <span>👨‍🏫 <strong>Docente:</strong> {teacherName || 'Docente Titular'}</span>
                  <span>📖 <strong>Asignatura:</strong> {selectedAssignment.subject_name}</span>
                  <span>🏫 <strong>Grado:</strong> {selectedAssignment.grade_name || 'N/A'}</span>
                  <span>📅 <strong>Año:</strong> {selectedAssignment.academic_year_name}</span>
                </div>
              </div>
              <button
                onClick={handleCloseRosterModal}
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
                    Cargando nómina de estudiantes matriculados en el grupo...
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
                      Sede: {selectedAssignment.campus_name || 'Principal'} • Jornada: {selectedAssignment.shift || 'MAÑANA'}
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
              <Button variant="secondary" onClick={handleCloseRosterModal}>
                Cerrar Planilla
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TeacherAssignmentsView
