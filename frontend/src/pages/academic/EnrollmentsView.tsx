/**
 * PEVN Frontend — Enrollments View
 *
 * Student enrollment lifecycle: PRE_ENROLLED, ACTIVE, WITHDRAWN, GRADUATED.
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
  EnrollmentCreateRequest,
  EnrollmentResponse,
  EnrollmentStatus,
} from '@/types'

export const EnrollmentsView: React.FC = () => {
  const { hasPermission } = useAuth()

  const [enrollments, setEnrollments] = useState<EnrollmentResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [statusFilter, setStatusFilter] = useState<EnrollmentStatus | undefined>(undefined)
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Create Modal
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [studentId, setStudentId] = useState<string>('')
  const [groupId, setGroupId] = useState<string>('')
  const [academicYearId, setAcademicYearId] = useState<string>('')
  const [status, setStatus] = useState<EnrollmentStatus>('ACTIVE')

  // Action Modals (Withdraw / Graduate)
  const [lifecycleModal, setLifecycleModal] = useState<{
    isOpen: boolean
    action: 'activate' | 'withdraw' | 'graduate' | null
    enrollment: EnrollmentResponse | null
    reason: string
  }>({
    isOpen: false,
    action: null,
    enrollment: null,
    reason: '',
  })

  const loadEnrollments = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await academicApi.listEnrollments({ status: statusFilter })
      setEnrollments(data.items)
      setTotal(data.total)
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al cargar matrículas'))
    } finally {
      setIsLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    void loadEnrollments()
  }, [loadEnrollments])

  const handleCreateEnrollment = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)

    const payload: EnrollmentCreateRequest = {
      student_id: studentId.trim(),
      group_id: groupId.trim(),
      academic_year_id: academicYearId.trim(),
      status,
    }

    try {
      await academicApi.createEnrollment(payload)
      setSuccessMsg(`Matrícula registrada exitosamente.`)
      setIsCreateOpen(false)
      setStudentId('')
      setGroupId('')
      await loadEnrollments()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al formalizar matrícula'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleExecuteLifecycleAction = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!lifecycleModal.enrollment || !lifecycleModal.action) return
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)

    try {
      if (lifecycleModal.action === 'activate') {
        await academicApi.activateEnrollment(lifecycleModal.enrollment.id)
        setSuccessMsg('Prematrícula activada formalmente.')
      } else if (lifecycleModal.action === 'withdraw') {
        await academicApi.withdrawEnrollment(lifecycleModal.enrollment.id, {
          reason: lifecycleModal.reason.trim() || 'Retiro institucional solicitado',
        })
        setSuccessMsg('Matrícula retirada exitosamente.')
      } else {
        await academicApi.graduateEnrollment(lifecycleModal.enrollment.id, {
          reason: lifecycleModal.reason.trim() || 'Culminación exitosa del año lectivo',
        })
        setSuccessMsg('Estudiante graduado del año escolar.')
      }
      setLifecycleModal({ isOpen: false, action: null, enrollment: null, reason: '' })
      await loadEnrollments()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error en la transición de matrícula'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const getStatusBadge = (st: EnrollmentStatus) => {
    switch (st) {
      case 'ACTIVE':
        return <Badge variant="success">ACTIVA</Badge>
      case 'PRE_ENROLLED':
        return <Badge variant="warning">PRE-MATRÍCULA</Badge>
      case 'WITHDRAWN':
        return <Badge variant="danger">RETIRADA</Badge>
      case 'GRADUATED':
        return <Badge variant="primary">GRADUADO</Badge>
      default:
        return <Badge>{st}</Badge>
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
            value={statusFilter ?? ''}
            onChange={(e) => {
              const val = e.target.value as EnrollmentStatus | ''
              setStatusFilter(val ? val : undefined)
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
            <option value="">Todos los Estados</option>
            <option value="ACTIVE">Activa (ACTIVE)</option>
            <option value="PRE_ENROLLED">Pre-Matrícula (PRE_ENROLLED)</option>
            <option value="WITHDRAWN">Retirada (WITHDRAWN)</option>
            <option value="GRADUATED">Graduado (GRADUATED)</option>
          </select>
        </div>

        {hasPermission('enrollments:create') && (
          <Button
            variant="primary"
            onClick={() => {
              setIsCreateOpen(true)
            }}
          >
            + Formalizar Matrícula
          </Button>
        )}
      </div>

      {/* Table Card */}
      <Card
        title="Libro de Matrículas Institucional"
        subtitle={`Total de contratos de matrícula: ${String(total)}`}
        action={
          <Button variant="secondary" size="sm" onClick={() => void loadEnrollments()}>
            Refrescar
          </Button>
        }
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando libro de matrículas...
            </p>
          </div>
        ) : enrollments.length === 0 ? (
          <EmptyState
            icon="📑"
            title="No se encontraron matrículas"
            description="No hay registros de matrícula que coincidan con los filtros seleccionados."
            actionLabel={hasPermission('enrollments:create') ? '+ Registrar Primera Matrícula' : undefined}
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
                  <th style={{ padding: '0.75rem 1rem' }}>ID Matrícula</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Estudiante UUID</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Grupo UUID</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Fecha</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Estado</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {enrollments.map((enr) => (
                  <tr key={enr.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 600, color: '#1E40AF' }}>
                      <code>{enr.id.substring(0, 8)}...</code>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#0F172A' }}>
                      <code>{enr.student_id.substring(0, 8)}...</code>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#475569' }}>
                      <code>{enr.group_id.substring(0, 8)}...</code>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#64748B' }}>{enr.enrollment_date}</td>
                    <td style={{ padding: '0.875rem 1rem' }}>{getStatusBadge(enr.status)}</td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.35rem', justifyContent: 'flex-end' }}>
                        {enr.status === 'PRE_ENROLLED' && hasPermission('enrollments:create') && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => {
                              setLifecycleModal({
                                isOpen: true,
                                action: 'activate',
                                enrollment: enr,
                                reason: '',
                              })
                            }}
                          >
                            Activar
                          </Button>
                        )}
                        {enr.status === 'ACTIVE' && hasPermission('enrollments:withdraw') && (
                          <>
                            <Button
                              variant="danger"
                              size="sm"
                              onClick={() => {
                                setLifecycleModal({
                                  isOpen: true,
                                  action: 'withdraw',
                                  enrollment: enr,
                                  reason: '',
                                })
                              }}
                            >
                              Retirar
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => {
                                setLifecycleModal({
                                  isOpen: true,
                                  action: 'graduate',
                                  enrollment: enr,
                                  reason: 'Graduación exitosa del año lectivo',
                                })
                              }}
                            >
                              Graduar
                            </Button>
                          </>
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

      {/* Create Enrollment Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false)
        }}
        title="Formalizar Nueva Matrícula"
        subtitle="Asigne al estudiante a un salón de clase y año escolar garantizando invariantes de cupo."
      >
        <form onSubmit={(e) => void handleCreateEnrollment(e)}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              ID de Estudiante (Student UUID) *
            </label>
            <input
              type="text"
              value={studentId}
              onChange={(e) => {
                setStudentId(e.target.value)
              }}
              required
              placeholder="UUID del estudiante"
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              ID de Salón / Grupo (Group UUID) *
            </label>
            <input
              type="text"
              value={groupId}
              onChange={(e) => {
                setGroupId(e.target.value)
              }}
              required
              placeholder="UUID del grupo destino"
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              ID de Año Lectivo (Academic Year UUID) *
            </label>
            <input
              type="text"
              value={academicYearId}
              onChange={(e) => {
                setAcademicYearId(e.target.value)
              }}
              required
              placeholder="UUID del año escolar vigente"
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Estado Inicial de la Matrícula *
            </label>
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value as EnrollmentStatus)
              }}
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            >
              <option value="ACTIVE">Activa (ACTIVE - Ocupa cupo de inmediato)</option>
              <option value="PRE_ENROLLED">Pre-Matrícula (PRE_ENROLLED)</option>
            </select>
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
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Registrar Matrícula'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Lifecycle Action Modal */}
      <Modal
        isOpen={lifecycleModal.isOpen}
        onClose={() => {
          setLifecycleModal({ isOpen: false, action: null, enrollment: null, reason: '' })
        }}
        title={
          lifecycleModal.action === 'activate'
            ? 'Activar Prematrícula'
            : lifecycleModal.action === 'withdraw'
              ? 'Retirar Matrícula Estudiantil'
              : 'Graduar Estudiante'
        }
        maxWidth="sm"
      >
        <form onSubmit={(e) => void handleExecuteLifecycleAction(e)}>
          {lifecycleModal.action === 'activate' ? (
            <p style={{ fontSize: '0.875rem', color: '#475569', lineHeight: 1.5, marginBottom: '1.5rem' }}>
              ¿Desea formalizar la prematrícula en estado <strong>ACTIVO</strong>? Se validará el cupo disponible en el salón.
            </p>
          ) : (
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Motivo / Justificación Legal *
              </label>
              <textarea
                value={lifecycleModal.reason}
                onChange={(e) => {
                  setLifecycleModal({ ...lifecycleModal, reason: e.target.value })
                }}
                required
                rows={3}
                placeholder="Indique el motivo administrativo o académico..."
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setLifecycleModal({ isOpen: false, action: null, enrollment: null, reason: '' })
              }}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant={lifecycleModal.action === 'withdraw' ? 'danger' : 'primary'}
              disabled={isSubmitting}
            >
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Confirmar Transición'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default EnrollmentsView
