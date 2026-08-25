/**
 * PEVN Frontend — Groups / Classrooms View
 *
 * Classroom management, capacity inspections, and director appointments.
 */

import React, { useCallback, useEffect, useState } from 'react'
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
  ApiError,
  AssignGroupDirectorRequest,
  GroupCapacityResponse,
  GroupCreateRequest,
  GroupResponse,
  ShiftEnum,
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

  // Capacity Inspector Modal
  const [capacityModal, setCapacityModal] = useState<{
    isOpen: boolean
    group: GroupResponse | null
    capacity: GroupCapacityResponse | null
    isLoading: boolean
  }>({
    isOpen: false,
    group: null,
    capacity: null,
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

  useEffect(() => {
    void loadGroups()
    void loadTeachers()
  }, [loadGroups, loadTeachers])

  const handleInspectCapacity = async (group: GroupResponse) => {
    setCapacityModal({
      isOpen: true,
      group,
      capacity: null,
      isLoading: true,
    })
    try {
      const cap = await academicApi.getGroupCapacity(group.id)
      setCapacityModal({
        isOpen: true,
        group,
        capacity: cap,
        isLoading: false,
      })
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al consultar cupos'))
      setCapacityModal({ isOpen: false, group: null, capacity: null, isLoading: false })
    }
  }

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)

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
          setCapacityModal({ isOpen: false, group: null, capacity: null, isLoading: false })
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

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="secondary"
                onClick={() => {
                  setCapacityModal({ isOpen: false, group: null, capacity: null, isLoading: false })
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
              ID Sede Educativa (Campus UUID) *
            </label>
            <input
              type="text"
              value={campusId}
              onChange={(e) => {
                setCampusId(e.target.value)
              }}
              required
              placeholder="UUID de la sede"
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              ID Año Lectivo (Academic Year UUID) *
            </label>
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
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              ID Grado Catálogo MEN (Grade UUID) *
            </label>
            <input
              type="text"
              value={gradeId}
              onChange={(e) => {
                setGradeId(e.target.value)
              }}
              required
              placeholder="UUID del grado"
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
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
