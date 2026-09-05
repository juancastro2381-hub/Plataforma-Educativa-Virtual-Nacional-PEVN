/**
 * PEVN Frontend — Academic Assignments View (Carga Académica Docente)
 *
 * Subject teacher allocations, single-active instructor invariant,
 * and atomic teacher replacements with canonical reference resolution.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { academicApi } from '@/services/academic'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { Alert } from '@/components/ui/Alert'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useAuth } from '@/hooks/useAuth'
import type {
  AcademicAssignmentCreateRequest,
  AcademicAssignmentResponse,
  AcademicYearResponse,
  ApiError,
  GroupResponse,
  SubjectResponse,
  TeacherReplacementRequest,
  TeacherResponse,
} from '@/types'

export const AcademicAssignmentsView: React.FC = () => {
  const { hasPermission } = useAuth()

  const [assignments, setAssignments] = useState<AcademicAssignmentResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(true)
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Catalogs for reference resolution
  const [teachers, setTeachers] = useState<TeacherResponse[]>([])
  const [subjects, setSubjects] = useState<SubjectResponse[]>([])
  const [groups, setGroups] = useState<GroupResponse[]>([])
  const [academicYears, setAcademicYears] = useState<AcademicYearResponse[]>([])

  // Create Modal
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [teacherId, setTeacherId] = useState<string>('')
  const [subjectId, setSubjectId] = useState<string>('')
  const [groupId, setGroupId] = useState<string>('')
  const [academicYearId, setAcademicYearId] = useState<string>('')
  const [weeklyHours, setWeeklyHours] = useState<number>(4)

  // Teacher Replacement Modal
  const [replaceModal, setReplaceModal] = useState<{
    isOpen: boolean
    assignment: AcademicAssignmentResponse | null
    newTeacherId: string
  }>({
    isOpen: false,
    assignment: null,
    newTeacherId: '',
  })

  // Lookup maps for table rendering
  const teacherMap = useMemo(() => {
    const map = new Map<string, string>()
    for (const t of teachers) {
      const name = t.user?.full_name || (t.user ? `${t.user.first_name} ${t.user.last_name}` : '') || t.specialty_area || t.id
      map.set(t.id, name)
    }
    return map
  }, [teachers])

  const subjectMap = useMemo(() => {
    const map = new Map<string, string>()
    for (const s of subjects) {
      map.set(s.id, s.name)
    }
    return map
  }, [subjects])

  const groupMap = useMemo(() => {
    const map = new Map<string, string>()
    for (const g of groups) {
      map.set(g.id, `${g.name} (${g.shift})`)
    }
    return map
  }, [groups])

  const yearMap = useMemo(() => {
    const map = new Map<string, string>()
    for (const y of academicYears) {
      map.set(y.id, `${y.name} (${y.year})`)
    }
    return map
  }, [academicYears])

  const loadAssignments = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await academicApi.listAssignments({ isActive: activeFilter })
      setAssignments(data.items)
      setTotal(data.total)
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al cargar asignaciones académicas'))
    } finally {
      setIsLoading(false)
    }
  }, [activeFilter])

  const loadCatalogs = useCallback(async () => {
    try {
      const [tRes, sRes, gRes, yRes] = await Promise.all([
        academicApi.listTeachers(),
        academicApi.listSubjects(),
        academicApi.listGroups(),
        academicApi.listAcademicYears(),
      ])
      setTeachers(tRes.items)
      setSubjects(sRes.items)
      setGroups(gRes.items)
      setAcademicYears(yRes.items)

      // Set default active academic year if not yet selected
      const activeYear = yRes.items.find((y) => y.status === 'ACTIVE') || yRes.items[0]
      if (activeYear && !academicYearId) {
        setAcademicYearId(activeYear.id)
      }
    } catch {
      // Non-critical fallback
    }
  }, [academicYearId])

  useEffect(() => {
    void loadAssignments()
  }, [loadAssignments])

  useEffect(() => {
    void loadCatalogs()
  }, [loadCatalogs])

  // Filter groups according to selected academic year
  const availableGroups = useMemo(() => {
    if (!academicYearId) return groups
    return groups.filter((g) => g.academic_year_id === academicYearId)
  }, [groups, academicYearId])

  // Filter subjects according to selected group's grade (if group selected)
  const availableSubjects = useMemo(() => {
    if (!groupId) return subjects
    const selectedGroup = groups.find((g) => g.id === groupId)
    if (!selectedGroup || !selectedGroup.grade_id) return subjects
    const filtered = subjects.filter((s) => s.grade_id === selectedGroup.grade_id)
    return filtered.length > 0 ? filtered : subjects
  }, [subjects, groupId, groups])

  const handleSubjectChange = (newSubjectId: string) => {
    setSubjectId(newSubjectId)
    const selected = subjects.find((s) => s.id === newSubjectId)
    if (selected && selected.weekly_hours) {
      setWeeklyHours(selected.weekly_hours)
    }
  }

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)

    const payload: AcademicAssignmentCreateRequest = {
      teacher_id: teacherId.trim(),
      subject_id: subjectId.trim(),
      group_id: groupId.trim(),
      academic_year_id: academicYearId.trim(),
      weekly_hours: weeklyHours,
      is_active: true,
    }

    try {
      await academicApi.createAssignment(payload)
      setSuccessMsg(`Asignación académica registrada exitosamente.`)
      setIsCreateOpen(false)
      setTeacherId('')
      setSubjectId('')
      setGroupId('')
      await loadAssignments()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al crear asignación académica'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeactivate = async (assignmentId: string) => {
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)
    try {
      await academicApi.deactivateAssignment(assignmentId)
      setSuccessMsg('Asignación académica desactivada.')
      await loadAssignments()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al desactivar asignación'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleReplaceTeacher = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!replaceModal.assignment || !replaceModal.newTeacherId) return
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)

    const payload: TeacherReplacementRequest = {
      new_teacher_id: replaceModal.newTeacherId.trim(),
    }

    try {
      await academicApi.replaceTeacher(replaceModal.assignment.id, payload)
      setSuccessMsg('Sustitución docente ejecutada atómicamente con éxito.')
      setReplaceModal({ isOpen: false, assignment: null, newTeacherId: '' })
      await loadAssignments()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al sustituir docente'))
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
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <label style={{ fontSize: '0.875rem', fontWeight: 600, color: '#475569' }}>
            Filtrar por Estado:
          </label>
          <select
            value={activeFilter === undefined ? '' : activeFilter ? 'true' : 'false'}
            onChange={(e) => {
              const val = e.target.value
              if (val === '') setActiveFilter(undefined)
              else setActiveFilter(val === 'true')
            }}
            style={{
              padding: '0.45rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              backgroundColor: '#FFFFFF',
              fontSize: '0.875rem',
              color: '#0F172A',
            }}
          >
            <option value="true">Solo Asignaciones Activas</option>
            <option value="false">Solo Asignaciones Inactivas</option>
            <option value="">Todas</option>
          </select>
        </div>

        {hasPermission('academic_assignments:create') && (
          <Button
            variant="primary"
            onClick={() => {
              setIsCreateOpen(true)
            }}
          >
            + Asignar Carga Académica
          </Button>
        )}
      </div>

      {/* Table Card */}
      <Card
        title="Distribución Institucional de Carga Académica (Docente → Asignatura → Grupo)"
        subtitle={`Mapeo oficial de asignaciones académicas institucional: ${String(total)} registros.`}
        action={
          <Button variant="secondary" size="sm" onClick={() => void loadAssignments()}>
            Refrescar
          </Button>
        }
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando asignaciones académicas...
            </p>
          </div>
        ) : assignments.length === 0 ? (
          <EmptyState
            icon="📚"
            title="Sin asignaciones académicas"
            description="No se encontraron cargas académicas para los filtros seleccionados."
            actionLabel={hasPermission('academic_assignments:create') ? '+ Crear Primera Asignación' : undefined}
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
                <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569', backgroundColor: '#F8FAFC' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Docente Titular</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Asignatura</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Grupo / Salón</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Año Lectivo</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Cupo Salón</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Horas / Sem</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Estado</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {assignments.map((a) => {
                  const resolvedTeacher = teacherMap.get(a.teacher_id) || `${a.teacher_id.substring(0, 8)}...`
                  const resolvedSubject = subjectMap.get(a.subject_id) || `${a.subject_id.substring(0, 8)}...`
                  const resolvedGroup = groupMap.get(a.group_id) || `${a.group_id.substring(0, 8)}...`
                  const resolvedYear = yearMap.get(a.academic_year_id) || `${a.academic_year_id.substring(0, 8)}...`
                  const groupObj = groups.find((g) => g.id === a.group_id)

                  return (
                    <tr key={a.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                      <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#1E40AF' }}>
                        {resolvedTeacher}
                      </td>
                      <td style={{ padding: '0.875rem 1rem', fontWeight: 600, color: '#0F172A' }}>
                        {resolvedSubject}
                      </td>
                      <td style={{ padding: '0.875rem 1rem', color: '#475569' }}>
                        {resolvedGroup}
                      </td>
                      <td style={{ padding: '0.875rem 1rem', color: '#64748B' }}>
                        {resolvedYear}
                      </td>
                      <td style={{ padding: '0.875rem 1rem', textAlign: 'center', color: '#475569' }}>
                        {groupObj ? `${groupObj.capacity_limit} cupos` : '—'}
                      </td>
                      <td style={{ padding: '0.875rem 1rem', textAlign: 'center', color: '#1E293B', fontWeight: 600 }}>
                        {a.weekly_hours} h/sem
                      </td>
                      <td style={{ padding: '0.875rem 1rem', textAlign: 'center' }}>
                        {a.is_active ? (
                          <Badge variant="success" size="sm">ACTIVA</Badge>
                        ) : (
                          <Badge variant="neutral" size="sm">INACTIVA</Badge>
                        )}
                      </td>
                      <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                        {a.is_active && hasPermission('academic_assignments:update') && (
                          <div style={{ display: 'flex', gap: '0.35rem', justifyContent: 'flex-end' }}>
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => {
                                setReplaceModal({
                                  isOpen: true,
                                  assignment: a,
                                  newTeacherId: '',
                                })
                              }}
                            >
                              Sustituir
                            </Button>
                            <Button
                              variant="danger"
                              size="sm"
                              onClick={() => void handleDeactivate(a.id)}
                              disabled={isSubmitting}
                            >
                              Desactivar
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Teacher Replacement Modal */}
      <Modal
        isOpen={replaceModal.isOpen}
        onClose={() => {
          setReplaceModal({ isOpen: false, assignment: null, newTeacherId: '' })
        }}
        title="Sustituir Docente en Asignación Académica"
        subtitle="Desactiva atómicamente la asignación previa y crea una nueva activa con el nuevo docente."
      >
        <form onSubmit={(e) => void handleReplaceTeacher(e)}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Nuevo Docente Titular *
            </label>
            {teachers.length > 0 ? (
              <select
                value={replaceModal.newTeacherId}
                onChange={(e) => {
                  setReplaceModal({ ...replaceModal, newTeacherId: e.target.value })
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              >
                <option value="">-- Seleccione el docente reemplazante --</option>
                {teachers
                  .filter((t) => t.id !== replaceModal.assignment?.teacher_id)
                  .map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.user?.full_name || (t.user ? `${t.user.first_name} ${t.user.last_name}` : '') || t.specialty_area || t.id} ({t.contract_type})
                    </option>
                  ))}
              </select>
            ) : (
              <input
                type="text"
                placeholder="UUID del nuevo docente"
                value={replaceModal.newTeacherId}
                onChange={(e) => {
                  setReplaceModal({ ...replaceModal, newTeacherId: e.target.value })
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
                setReplaceModal({ isOpen: false, assignment: null, newTeacherId: '' })
              }}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Confirmar Sustitución'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Create Assignment Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false)
        }}
        title="Asignar Carga Académica Docente"
        subtitle="Vincule a un docente con una asignatura y grupo específico."
      >
        <form onSubmit={(e) => void handleCreateAssignment(e)}>
          {/* Docente Selector */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Docente Titular *
            </label>
            {teachers.length > 0 ? (
              <select
                value={teacherId}
                onChange={(e) => {
                  setTeacherId(e.target.value)
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              >
                <option value="">-- Seleccione un docente titular --</option>
                {teachers.map((t) => {
                  const label = t.user?.full_name || (t.user ? `${t.user.first_name} ${t.user.last_name}` : '') || t.id
                  return (
                    <option key={t.id} value={t.id}>
                      {label} — {t.specialty_area || 'Docente'} ({t.contract_type})
                    </option>
                  )
                })}
              </select>
            ) : (
              <input
                type="text"
                value={teacherId}
                onChange={(e) => {
                  setTeacherId(e.target.value)
                }}
                required
                placeholder="UUID del docente"
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            )}
          </div>

          {/* Año Lectivo Selector */}
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
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              >
                <option value="">-- Seleccione el año lectivo --</option>
                {academicYears.map((ay) => (
                  <option key={ay.id} value={ay.id}>
                    {ay.name} ({ay.year}) {ay.status === 'ACTIVE' ? '— ACTIVO' : `— ${ay.status}`}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={academicYearId}
                onChange={(e) => {
                  setAcademicYearId(e.target.value)
                }}
                required
                placeholder="UUID del año escolar"
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            )}
          </div>

          {/* Grupo / Salón Selector */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Grupo / Salón *
            </label>
            {availableGroups.length > 0 ? (
              <select
                value={groupId}
                onChange={(e) => {
                  setGroupId(e.target.value)
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              >
                <option value="">-- Seleccione el grupo / salón --</option>
                {availableGroups.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.name} — Jornada {g.shift} (Cupo: {g.capacity_limit})
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={groupId}
                onChange={(e) => {
                  setGroupId(e.target.value)
                }}
                required
                placeholder="UUID del grupo"
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            )}
          </div>

          {/* Asignatura Selector & Horas Semanales */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Asignatura Curricular *
              </label>
              {availableSubjects.length > 0 ? (
                <select
                  value={subjectId}
                  onChange={(e) => {
                    handleSubjectChange(e.target.value)
                  }}
                  required
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                >
                  <option value="">-- Seleccione la asignatura --</option>
                  {availableSubjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.weekly_hours}h/sem)
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  value={subjectId}
                  onChange={(e) => {
                    setSubjectId(e.target.value)
                  }}
                  required
                  placeholder="UUID de la asignatura"
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              )}
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Horas / Sem *
              </label>
              <input
                type="number"
                min={1}
                max={40}
                value={weeklyHours}
                onChange={(e) => {
                  setWeeklyHours(Number(e.target.value))
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
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
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Guardar Asignación'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default AcademicAssignmentsView
