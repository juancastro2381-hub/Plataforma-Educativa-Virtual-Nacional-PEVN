/**
 * PEVN Frontend — Teachers View
 *
 * Educator profiles, statutory appointments, and assignment eligibility checks.
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
  TeacherContractType,
  TeacherCreateRequest,
  TeacherEligibilityResponse,
  TeacherResponse,
} from '@/types'

export const TeachersView: React.FC = () => {
  const { hasPermission } = useAuth()

  const [teachers, setTeachers] = useState<TeacherResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [contractFilter, setContractFilter] = useState<TeacherContractType | undefined>(undefined)
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Create Teacher Modal
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [userId, setUserId] = useState<string>('')
  const [specialtyArea, setSpecialtyArea] = useState<string>('Licenciatura en Ciencias Básicas')
  const [contractType, setContractType] = useState<TeacherContractType>('PROPIEDAD')
  const [escalafonGrade, setEscalafonGrade] = useState<string>('14')

  // Eligibility Modal
  const [eligibilityModal, setEligibilityModal] = useState<{
    isOpen: boolean
    teacher: TeacherResponse | null
    eligibility: TeacherEligibilityResponse | null
    isLoading: boolean
  }>({
    isOpen: false,
    teacher: null,
    eligibility: null,
    isLoading: false,
  })

  const loadTeachers = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await academicApi.listTeachers(contractFilter)
      setTeachers(data.items)
      setTotal(data.total)
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al cargar docentes'))
    } finally {
      setIsLoading(false)
    }
  }, [contractFilter])

  useEffect(() => {
    void loadTeachers()
  }, [loadTeachers])

  const handleCreateTeacher = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)

    const payload: TeacherCreateRequest = {
      user_id: userId.trim(),
      specialty_area: specialtyArea.trim() || null,
      contract_type: contractType,
      escalafon_grade: escalafonGrade.trim() || null,
    }

    try {
      await academicApi.createTeacher(payload)
      setSuccessMsg(`Perfil docente creado exitosamente.`)
      setIsCreateOpen(false)
      setUserId('')
      await loadTeachers()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al crear docente'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCheckEligibility = async (teacher: TeacherResponse) => {
    setEligibilityModal({
      isOpen: true,
      teacher,
      eligibility: null,
      isLoading: true,
    })
    try {
      const el = await academicApi.validateTeacherEligibility(teacher.id)
      setEligibilityModal({
        isOpen: true,
        teacher,
        eligibility: el,
        isLoading: false,
      })
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al verificar aptitud docente'))
      setEligibilityModal({ isOpen: false, teacher: null, eligibility: null, isLoading: false })
    }
  }

  const getContractBadge = (ct: TeacherContractType) => {
    switch (ct) {
      case 'PROPIEDAD':
        return <Badge variant="success">PROPIEDAD</Badge>
      case 'PERIODO_PRUEBA':
        return <Badge variant="warning">PERIODO PRUEBA</Badge>
      case 'PROVISIONAL':
        return <Badge variant="info">PROVISIONAL</Badge>
      default:
        return <Badge variant="neutral">{ct}</Badge>
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
            Filtrar por Vinculación:
          </label>
          <select
            value={contractFilter ?? ''}
            onChange={(e) => {
              const val = e.target.value as TeacherContractType | ''
              setContractFilter(val ? val : undefined)
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
            <option value="">Todos los Tipos de Vinculación</option>
            <option value="PROPIEDAD">Carrera Docente (Propiedad)</option>
            <option value="PERIODO_PRUEBA">Período de Prueba</option>
            <option value="PROVISIONAL">Provisional</option>
            <option value="TEMPORAL">Temporal</option>
            <option value="HORA_CATEDRA">Hora Cátedra</option>
          </select>
        </div>

        {hasPermission('teachers:create') && (
          <Button
            variant="primary"
            onClick={() => {
              setIsCreateOpen(true)
            }}
          >
            + Registrar Perfil Docente
          </Button>
        )}
      </div>

      {/* Table Card */}
      <Card
        title="Planta Docente Institucional"
        subtitle={`Total de docentes registrados: ${String(total)}`}
        action={
          <Button variant="secondary" size="sm" onClick={() => void loadTeachers()}>
            Refrescar
          </Button>
        }
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando planta docente...
            </p>
          </div>
        ) : teachers.length === 0 ? (
          <EmptyState
            icon="👩‍🏫"
            title="No hay docentes registrados"
            description="No se encontraron perfiles docentes para los criterios seleccionados."
            actionLabel={hasPermission('teachers:create') ? '+ Registrar Primer Docente' : undefined}
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
                  <th style={{ padding: '0.75rem 1rem' }}>Docente</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Especialidad</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Vinculación</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Escalafón</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {teachers.map((t) => (
                  <tr key={t.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                      {t.user ? `${t.user.first_name} ${t.user.last_name}` : t.user_id}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#1E293B' }}>
                      {t.specialty_area || 'Área General'}
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>{getContractBadge(t.contract_type)}</td>
                    <td style={{ padding: '0.875rem 1rem', color: '#64748B' }}>
                      Grado {t.escalafon_grade || 'N/A'}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => void handleCheckEligibility(t)}
                      >
                        Verificar Aptitud
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Eligibility Modal */}
      <Modal
        isOpen={eligibilityModal.isOpen}
        onClose={() => {
          setEligibilityModal({ isOpen: false, teacher: null, eligibility: null, isLoading: false })
        }}
        title={`Aptitud y Estado de Asignación Docente`}
        subtitle={
          eligibilityModal.teacher?.user
            ? `${eligibilityModal.teacher.user.first_name} ${eligibilityModal.teacher.user.last_name}`
            : ''
        }
        maxWidth="sm"
      >
        {eligibilityModal.isLoading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <LoadingSpinner size="md" />
            <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '0.5rem' }}>
              Validando habilitación académica...
            </p>
          </div>
        ) : eligibilityModal.eligibility ? (
          <div>
            <div
              style={{
                padding: '1.5rem',
                backgroundColor: eligibilityModal.eligibility.is_eligible ? '#ECFDF5' : '#FEF2F2',
                border: `1px solid ${eligibilityModal.eligibility.is_eligible ? '#A7F3D0' : '#FECACA'}`,
                borderRadius: '12px',
                textAlign: 'center',
                marginBottom: '1.5rem',
              }}
            >
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
                {eligibilityModal.eligibility.is_eligible ? '✅' : '❌'}
              </div>
              <h4
                style={{
                  margin: '0 0 0.5rem 0',
                  color: eligibilityModal.eligibility.is_eligible ? '#065F46' : '#991B1B',
                  fontSize: '1.125rem',
                  fontWeight: 700,
                }}
              >
                {eligibilityModal.eligibility.is_eligible
                  ? 'Docente Apto y Habilitado'
                  : 'Docente No Habilitado'}
              </h4>
              <p
                style={{
                  margin: 0,
                  fontSize: '0.875rem',
                  color: eligibilityModal.eligibility.is_eligible ? '#047857' : '#B91C1C',
                }}
              >
                {eligibilityModal.eligibility.message}
              </p>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="secondary"
                onClick={() => {
                  setEligibilityModal({ isOpen: false, teacher: null, eligibility: null, isLoading: false })
                }}
              >
                Cerrar
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>

      {/* Create Teacher Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false)
        }}
        title="Registrar Perfil Docente"
        subtitle="Vincule una cuenta de usuario existente con su nombramiento profesional."
      >
        <form onSubmit={(e) => void handleCreateTeacher(e)}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              ID de Usuario Institucional (User UUID) *
            </label>
            <input
              type="text"
              value={userId}
              onChange={(e) => {
                setUserId(e.target.value)
              }}
              required
              placeholder="UUID de la cuenta de usuario"
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Área de Especialidad / Título Profesional *
            </label>
            <input
              type="text"
              value={specialtyArea}
              onChange={(e) => {
                setSpecialtyArea(e.target.value)
              }}
              required
              placeholder="Licenciatura en Matemáticas, Física, etc."
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Tipo de Nombramiento / Vinculación *
              </label>
              <select
                value={contractType}
                onChange={(e) => {
                  setContractType(e.target.value as TeacherContractType)
                }}
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              >
                <option value="PROPIEDAD">Propiedad (Carrera Docente)</option>
                <option value="PERIODO_PRUEBA">Período de Prueba</option>
                <option value="PROVISIONAL">Provisional</option>
                <option value="TEMPORAL">Temporal</option>
                <option value="HORA_CATEDRA">Hora Cátedra</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Grado Escalafón Docente (Decreto 1278 / 2277)
              </label>
              <input
                type="text"
                value={escalafonGrade}
                onChange={(e) => {
                  setEscalafonGrade(e.target.value)
                }}
                placeholder="14, 2A, 3D, etc."
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
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Guardar Docente'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default TeachersView
