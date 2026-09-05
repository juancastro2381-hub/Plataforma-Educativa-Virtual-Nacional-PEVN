/**
 * PEVN Frontend — Groups / Classrooms View
 *
 * Classroom management, capacity inspections, and director appointments.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { academicApi } from '@/services/academic'
import { institutionApi } from '@/services/institution'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { Alert } from '@/components/ui/Alert'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useAuth } from '@/hooks/useAuth'
import type {
  AcademicAssignmentResponse,
  AcademicYearResponse,
  ApiError,
  AssignGroupDirectorRequest,
  CampusResponse,
  GradeResponse,
  GroupCapacityResponse,
  GroupCreateRequest,
  GroupResponse,
  ShiftEnum,
  SubjectResponse,
  TeacherResponse,
} from '@/types'

export const GroupsView: React.FC = () => {
  const { hasPermission } = useAuth()

  const [groups, setGroups] = useState<GroupResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Teachers for director assignment selection
  const [teachers, setTeachers] = useState<TeacherResponse[]>([])

  // Catalogs for group creation
  const [campuses, setCampuses] = useState<CampusResponse[]>([])
  const [academicYears, setAcademicYears] = useState<AcademicYearResponse[]>([])
  const [grades, setGrades] = useState<GradeResponse[]>([])
  const [isCatalogsLoading, setIsCatalogsLoading] = useState<boolean>(false)

  // Capacity & Teachers Inspector Modal
  const [capacityModal, setCapacityModal] = useState<{
    isOpen: boolean
    group: GroupResponse | null
    capacity: GroupCapacityResponse | null
    assignments: AcademicAssignmentResponse[]
    subjects: SubjectResponse[]
    isLoading: boolean
  }>({
    isOpen: false,
    group: null,
    capacity: null,
    assignments: [],
    subjects: [],
    isLoading: false,
  })

  // Create Group Modal
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [campusId, setCampusId] = useState<string>('')
  const [academicYearId, setAcademicYearId] = useState<string>('')
  const [gradeId, setGradeId] = useState<string>('')
  const [name, setName] = useState<string>('')
  const [shift, setShift] = useState<ShiftEnum>('MANANA')
  const [capacityLimit, setCapacityLimit] = useState<number>(35)

  // Assign Director Modal
  const [directorModal, setDirectorModal] = useState<{
    isOpen: boolean
    group: GroupResponse | null
    selectedTeacherId: string
  }>({
    isOpen: false,
    group: null,
    selectedTeacherId: '',
  })

  const loadGroups = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await academicApi.listGroups()
      setGroups(data.items)
      setTotal(data.total)
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al cargar grupos de clase'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  const loadTeachers = useCallback(async () => {
    try {
      const data = await academicApi.listTeachers()
      setTeachers(data.items)
    } catch {
      // Non-critical, teacher selection will fallback
    }
  }, [])

  const loadCatalogs = useCallback(async () => {
    setIsCatalogsLoading(true)
    try {
      const [instData, ayData, gradesData] = await Promise.all([
        institutionApi.getMyInstitution().catch(() => null),
        academicApi.listAcademicYears().catch(() => ({ items: [], total: 0 })),
        academicApi.listGrades().catch(() => ({ items: [], total: 0 })),
      ])

      if (instData?.campuses) {
        setCampuses(instData.campuses)
        if (instData.campuses.length === 1) {
          setCampusId((prev) => prev || instData.campuses[0].id)
        }
      }

      if (ayData?.items) {
        setAcademicYears(ayData.items)
        const activeYear = ayData.items.find((y) => y.status === 'ACTIVE')
        if (activeYear) {
          setAcademicYearId((prev) => prev || activeYear.id)
        } else if (ayData.items.length === 1) {
          setAcademicYearId((prev) => prev || ayData.items[0].id)
        }
      }

      if (gradesData?.items) {
        setGrades(gradesData.items)
      }
    } catch {
      // Reference catalogs non-fatal fallback
    } finally {
      setIsCatalogsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadGroups()
    void loadTeachers()
    void loadCatalogs()
  }, [loadGroups, loadTeachers, loadCatalogs])

  const handleInspectCapacity = async (group: GroupResponse) => {
    setCapacityModal({
      isOpen: true,
      group,
      capacity: null,
      assignments: [],
      subjects: [],
      isLoading: true,
    })
    try {
      const [cap, asgRes, subRes] = await Promise.all([
        academicApi.getGroupCapacity(group.id),
        academicApi.listAssignments({ isActive: true }).catch(() => ({ items: [], total: 0 })),
        academicApi.listSubjects().catch(() => ({ items: [], total: 0 })),
      ])
      const groupAssignments = asgRes.items.filter((a) => a.group_id === group.id)
      setCapacityModal({
        isOpen: true,
        group,
        capacity: cap,
        assignments: groupAssignments,
        subjects: subRes.items,
        isLoading: false,
      })
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al consultar cupos'))
      setCapacityModal({ isOpen: false, group: null, capacity: null, assignments: [], subjects: [], isLoading: false })
    }
  }

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)

    if (!campusId.trim()) {
      setError(new Error('Debe seleccionar una sede educativa válida.'))
      setIsSubmitting(false)
      return
    }
    if (!academicYearId.trim()) {
      setError(new Error('Debe seleccionar un año lectivo válido.'))
      setIsSubmitting(false)
      return
    }
    if (!gradeId.trim()) {
      setError(new Error('Debe seleccionar un grado del catálogo nacional MEN.'))
      setIsSubmitting(false)
      return
    }

    const payload: GroupCreateRequest = {
      campus_id: campusId.trim(),
      academic_year_id: academicYearId.trim(),
      grade_id: gradeId.trim(),
      name: name.trim(),
      shift,
      capacity_limit: capacityLimit,
    }

    try {
      await academicApi.createGroup(payload)
      setSuccessMsg(`Grupo "${payload.name}" creado exitosamente.`)
      setIsCreateOpen(false)
      setName('')
      await loadGroups()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al crear grupo'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleAssignDirector = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!directorModal.group || !directorModal.selectedTeacherId) return
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)

    const payload: AssignGroupDirectorRequest = {
      teacher_id: directorModal.selectedTeacherId,
    }

    try {
      await academicApi.assignGroupDirector(directorModal.group.id, payload)
      setSuccessMsg(`Director de grupo asignado exitosamente.`)
      setDirectorModal({ isOpen: false, group: null, selectedTeacherId: '' })
      await loadGroups()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al asignar director de grupo'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div>
      {/* Notifications */}
      {error && <Alert error={error} onClose={() => { setError(null) }} />}
      {successMsg && (
        <Alert variant="success" message={successMsg} onClose={() => { setSuccessMsg(null) }} />
      )}

      {/* Action Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <p style={{ margin: 0, fontSize: '0.875rem', color: '#64748B' }}>
          Gestión de salones de clase, cupos y directores de grupo.
        </p>

        {hasPermission('groups:create') && (
          <Button
            variant="primary"
            onClick={() => {
              setIsCreateOpen(true)
            }}
          >
            + Nuevo Grupo
          </Button>
        )}
      </div>

      {/* Table Card */}
      <Card
        title="Grupos y Salones de Clase"
        subtitle={`Total de salones configurados: ${String(total)}`}
        action={
          <Button variant="secondary" size="sm" onClick={() => void loadGroups()}>
            Refrescar
          </Button>
        }
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando salones de clase...
            </p>
          </div>
        ) : groups.length === 0 ? (
          <EmptyState
            icon="🏫"
            title="No hay grupos registrados"
            description="Cree salones de clase para habilitar la asignación de matrículas."
            actionLabel={hasPermission('groups:create') ? '+ Crear Primer Grupo' : undefined}
            onAction={() => {
              setIsCreateOpen(true)
            }}
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '0.875rem',
                textAlign: 'left',
              }}
            >
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Grupo</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Jornada</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Cupo Máximo</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Director</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {groups.map((g) => (
                  <tr key={g.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                      {g.name}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#475569' }}>
                      <Badge variant="info" size="sm">
                        {g.shift}
                      </Badge>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#1E293B', fontWeight: 600 }}>
                      {g.capacity_limit} estudiantes
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#64748B' }}>
                      {g.group_director_teacher_id ? (
                        <span style={{ color: '#059669', fontWeight: 600 }}>✓ Asignado</span>
                      ) : (
                        <span style={{ color: '#94A3B8', fontStyle: 'italic' }}>Sin Director</span>
                      )}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => void handleInspectCapacity(g)}
                        >
                          Ver Cupos
                        </Button>
                        {hasPermission('groups:assign_director') && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              setDirectorModal({
                                isOpen: true,
                                group: g,
                                selectedTeacherId: g.group_director_teacher_id ?? '',
                              })
                            }}
                          >
                            Director
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Capacity Modal */}
      <Modal
        isOpen={capacityModal.isOpen}
        onClose={() => {
          setCapacityModal({ isOpen: false, group: null, capacity: null, assignments: [], subjects: [], isLoading: false })
        }}
        title={`Disponibilidad y Cupos — Grupo ${capacityModal.group?.name ?? ''}`}
        subtitle="Cálculo en tiempo real contra la base de datos institucional."
        maxWidth="sm"
      >
        {capacityModal.isLoading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <LoadingSpinner size="md" />
            <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '0.5rem' }}>
              Consultando cupos bloqueados...
            </p>
          </div>
        ) : capacityModal.capacity ? (
          <div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '1rem',
                textAlign: 'center',
                marginBottom: '1.5rem',
              }}
            >
              <div style={{ padding: '1rem', backgroundColor: '#F8FAFC', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>LÍMITE</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0F172A' }}>
                  {capacityModal.capacity.capacity_limit}
                </div>
              </div>
              <div style={{ padding: '1rem', backgroundColor: '#EFF6FF', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: '#1E40AF', fontWeight: 600 }}>MATRICULADOS</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1E40AF' }}>
                  {capacityModal.capacity.active_enrolled_count}
                </div>
              </div>
              <div style={{ padding: '1rem', backgroundColor: '#ECFDF5', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: '#065F46', fontWeight: 600 }}>DISPONIBLES</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#059669' }}>
                  {capacityModal.capacity.available_slots}
                </div>
              </div>
            </div>

            {capacityModal.capacity.available_slots === 0 && (
              <Alert
                variant="warning"
                message="El grupo ha alcanzado su capacidad máxima permitida. No se admiten nuevas matrículas sin ampliación de cupos."
              />
            )}

            {/* Assigned Teachers & Subjects for this Group */}
            <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem', borderTop: '1px solid #E2E8F0', paddingTop: '1rem' }}>
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.5rem' }}>
                👨‍🏫 Docentes y Asignaturas Asignadas ({capacityModal.assignments.length})
              </div>
              {capacityModal.assignments.length === 0 ? (
                <p style={{ fontSize: '0.8125rem', color: '#64748B', margin: 0, fontStyle: 'italic' }}>
                  No hay docentes ni materias asignadas a este grupo todavía.
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {capacityModal.assignments.map((a) => {
                    const teacher = teachers.find((t) => t.id === a.teacher_id)
                    const teacherName = teacher?.user?.full_name || (teacher?.user ? `${teacher.user.first_name} ${teacher.user.last_name}` : null) || teacher?.specialty_area || 'Docente'
                    const subject = capacityModal.subjects.find((s) => s.id === a.subject_id)
                    const subjectName = subject?.name || 'Materia'

                    return (
                      <div
                        key={a.id}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          backgroundColor: '#F8FAFC',
                          padding: '0.5rem 0.75rem',
                          borderRadius: '6px',
                          border: '1px solid #E2E8F0',
                          fontSize: '0.8125rem',
                        }}
                      >
                        <div>
                          <strong style={{ color: '#1E40AF' }}>{teacherName}</strong> — <span style={{ color: '#0F172A' }}>{subjectName}</span>
                        </div>
                        <span style={{ color: '#64748B', fontWeight: 600 }}>
                          {a.weekly_hours} h/sem
                        </span>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="secondary"
                onClick={() => {
                  setCapacityModal({ isOpen: false, group: null, capacity: null, assignments: [], subjects: [], isLoading: false })
                }}
              >
                Cerrar
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>

      {/* Create Group Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false)
        }}
        title="Crear Nuevo Grupo / Salón"
        subtitle="Defina los identificadores y capacidad del salón de clase."
      >
        <form onSubmit={(e) => void handleCreateGroup(e)}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Nombre del Salón (ej: 10-01, 6-B) *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value)
              }}
              required
              placeholder="10-01"
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Jornada Escolar *
              </label>
              <select
                value={shift}
                onChange={(e) => {
                  setShift(e.target.value as ShiftEnum)
                }}
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              >
                <option value="MANANA">Mañana</option>
                <option value="TARDE">Tarde</option>
                <option value="NOCHE">Noche</option>
                <option value="UNICA">Jornada Única</option>
                <option value="SABATINA">Sabatina</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Límite de Capacidad (1 - 100) *
              </label>
              <input
                type="number"
                min={1}
                max={100}
                value={capacityLimit}
                onChange={(e) => {
                  setCapacityLimit(Number(e.target.value))
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Sede Educativa *
            </label>
            {campuses.length > 0 ? (
              <select
                value={campusId}
                onChange={(e) => {
                  setCampusId(e.target.value)
                }}
                required
                disabled={isCatalogsLoading || isSubmitting}
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', backgroundColor: '#FFFFFF' }}
              >
                <option value="">-- Seleccione una sede --</option>
                {campuses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} — DANE {c.dane_sede_code}
                  </option>
                ))}
              </select>
            ) : (
              <p style={{ fontSize: '0.8125rem', color: '#EF4444', margin: '0.25rem 0 0 0' }}>
                {isCatalogsLoading ? 'Cargando sedes educativas...' : 'No hay sedes educativas disponibles para esta institución.'}
              </p>
            )}
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Año Lectivo *
            </label>
            {academicYears.length > 0 ? (
              <select
                value={academicYearId}
                onChange={(e) => {
                  setAcademicYearId(e.target.value)
                }}
                required
                disabled={isCatalogsLoading || isSubmitting}
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', backgroundColor: '#FFFFFF' }}
              >
                <option value="">-- Seleccione un año lectivo --</option>
                {academicYears.map((ay) => (
                  <option key={ay.id} value={ay.id}>
                    {ay.name} ({ay.status})
                  </option>
                ))}
              </select>
            ) : (
              <p style={{ fontSize: '0.8125rem', color: '#EF4444', margin: '0.25rem 0 0 0' }}>
                {isCatalogsLoading ? 'Cargando años escolares...' : 'No hay años lectivos disponibles para esta institución.'}
              </p>
            )}
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Grado *
            </label>
            {grades.length > 0 ? (
              <select
                value={gradeId}
                onChange={(e) => {
                  setGradeId(e.target.value)
                }}
                required
                disabled={isCatalogsLoading || isSubmitting}
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', backgroundColor: '#FFFFFF' }}
              >
                <option value="">-- Seleccione un grado --</option>
                {grades.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.name} ({g.code})
                  </option>
                ))}
              </select>
            ) : (
              <p style={{ fontSize: '0.8125rem', color: '#EF4444', margin: '0.25rem 0 0 0' }}>
                {isCatalogsLoading ? 'Cargando catálogo de grados...' : 'No se pudo cargar el catálogo de grados.'}
              </p>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setIsCreateOpen(false)
              }}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Guardar Grupo'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Assign Director Modal */}
      <Modal
        isOpen={directorModal.isOpen}
        onClose={() => {
          setDirectorModal({ isOpen: false, group: null, selectedTeacherId: '' })
        }}
        title={`Asignar Director de Grupo — ${directorModal.group?.name ?? ''}`}
        subtitle="Seleccione el docente institucional que actuará como director titular."
        maxWidth="sm"
      >
        <form onSubmit={(e) => void handleAssignDirector(e)}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Docente Titular *
            </label>
            {teachers.length > 0 ? (
              <select
                value={directorModal.selectedTeacherId}
                onChange={(e) => {
                  setDirectorModal({ ...directorModal, selectedTeacherId: e.target.value })
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              >
                <option value="">-- Seleccione un docente --</option>
                {teachers.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.user?.full_name || t.specialty_area || t.id} ({t.contract_type})
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                placeholder="UUID del perfil docente"
                value={directorModal.selectedTeacherId}
                onChange={(e) => {
                  setDirectorModal({ ...directorModal, selectedTeacherId: e.target.value })
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setDirectorModal({ isOpen: false, group: null, selectedTeacherId: '' })
              }}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Confirmar Director'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default GroupsView
