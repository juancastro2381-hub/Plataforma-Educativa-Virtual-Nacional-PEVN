/**
 * PEVN Frontend — Group Transfers View (Traslados de Grupo)
 *
 * Atomic student classroom transfers with row-locked capacity validation
 * and immutable historical audit trail.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { academicApi } from '@/services/academic'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Alert } from '@/components/ui/Alert'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useAuth } from '@/hooks/useAuth'
import type {
  ApiError,
  EnrollmentResponse,
  GroupResponse,
  GroupTransferHistoryResponse,
  GroupTransferRequest,
  StudentResponse,
  TransferExecutionResponse,
} from '@/types'

export const TransfersView: React.FC = () => {
  const { hasPermission } = useAuth()

  // Form State
  const [enrollmentId, setEnrollmentId] = useState<string>('')
  const [targetGroupId, setTargetGroupId] = useState<string>('')
  const [reason, setReason] = useState<string>('')
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [executionResult, setExecutionResult] = useState<TransferExecutionResponse | null>(null)

  // History Query State
  const [queryEnrollmentId, setQueryEnrollmentId] = useState<string>('')
  const [historyItems, setHistoryItems] = useState<GroupTransferHistoryResponse[]>([])
  const [isQuerying, setIsQuerying] = useState<boolean>(false)
  const [hasQueried, setHasQueried] = useState<boolean>(false)

  // Reference Catalogs
  const [activeEnrollments, setActiveEnrollments] = useState<EnrollmentResponse[]>([])
  const [allEnrollments, setAllEnrollments] = useState<EnrollmentResponse[]>([])
  const [groups, setGroups] = useState<GroupResponse[]>([])
  const [students, setStudents] = useState<StudentResponse[]>([])
  const [isCatalogsLoading, setIsCatalogsLoading] = useState<boolean>(false)

  const loadCatalogs = useCallback(async () => {
    setIsCatalogsLoading(true)
    try {
      const [activeEnrData, allEnrData, groupsData, studentsData] = await Promise.all([
        academicApi.listEnrollments({ status: 'ACTIVE' }).catch(() => ({ items: [], total: 0 })),
        academicApi.listEnrollments().catch(() => ({ items: [], total: 0 })),
        academicApi.listGroups().catch(() => ({ items: [], total: 0 })),
        academicApi.listStudents().catch(() => ({ items: [], total: 0 })),
      ])

      if (activeEnrData?.items) setActiveEnrollments(activeEnrData.items)
      if (allEnrData?.items) setAllEnrollments(allEnrData.items)
      if (groupsData?.items) setGroups(groupsData.items)
      if (studentsData?.items) setStudents(studentsData.items)
    } catch {
      // Non-critical reference catalogs fallback
    } finally {
      setIsCatalogsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadCatalogs()
  }, [loadCatalogs])

  const getStudentLabel = (studentIdToFind: string) => {
    const s = students.find((item) => item.id === studentIdToFind)
    if (!s) return `Estudiante ${studentIdToFind.substring(0, 8)}...`
    if (s.user) {
      return `${s.user.first_name} ${s.user.last_name} (${s.user.document_type}: ${s.user.document_number})`
    }
    return `SIMAT: ${s.code_simat}`
  }

  const getGroupLabel = (groupIdToFind: string) => {
    const g = groups.find((item) => item.id === groupIdToFind)
    if (!g) return `Grupo ${groupIdToFind.substring(0, 8)}...`
    return `${g.name} (${g.shift})`
  }

  const selectedEnrollment = activeEnrollments.find((e) => e.id === enrollmentId)
  const candidateGroups = groups.filter((g) => {
    if (!selectedEnrollment) return true
    return g.id !== selectedEnrollment.group_id
  })

  const handleExecuteTransfer = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setExecutionResult(null)

    const payload: GroupTransferRequest = {
      enrollment_id: enrollmentId.trim(),
      target_group_id: targetGroupId.trim(),
      reason: reason.trim(),
    }

    try {
      const result = await academicApi.transferStudentGroup(payload)
      setExecutionResult(result)
      setEnrollmentId('')
      setTargetGroupId('')
      setReason('')
      await loadCatalogs()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al ejecutar traslado de grupo'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleQueryHistory = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!queryEnrollmentId.trim()) return
    setIsQuerying(true)
    setError(null)
    setHasQueried(true)

    try {
      const data = await academicApi.getTransferHistory(queryEnrollmentId.trim())
      setHistoryItems(data.items)
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al consultar historial de traslados'))
    } finally {
      setIsQuerying(false)
    }
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
      {/* Transfer Execution Form */}
      <div>
        <Card
          title="Trasladar Estudiante de Salón"
          subtitle="Transfiere atómicamente a un estudiante a otro grupo verificando cupos bloqueados."
        >
          {error && <Alert error={error} onClose={() => { setError(null) }} />}

          {executionResult && (
            <Alert
              variant="success"
              title="¡Traslado Ejecutado Exitosamente!"
              message={`Estudiante transferido al grupo ${getGroupLabel(executionResult.transfer_history.new_group_id)}`}
              onClose={() => { setExecutionResult(null) }}
            >
              <div style={{ marginTop: '0.5rem', fontSize: '0.8125rem' }}>
                <div>ID Matrícula: <code>{executionResult.enrollment.id}</code></div>
                <div>Nuevo Salón: <strong>{getGroupLabel(executionResult.enrollment.group_id)}</strong></div>
                <div>Fecha de Traslado: {executionResult.transfer_history.transfer_date}</div>
              </div>
            </Alert>
          )}

          {hasPermission('enrollments:transfer') ? (
            <form onSubmit={(e) => void handleExecuteTransfer(e)}>
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="transfer-enrollment-select" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Matrícula Activa *
                </label>
                {activeEnrollments.length > 0 ? (
                  <select
                    id="transfer-enrollment-select"
                    value={enrollmentId}
                    onChange={(e) => {
                      setEnrollmentId(e.target.value)
                      setTargetGroupId('')
                    }}
                    required
                    disabled={isCatalogsLoading || isSubmitting}
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', backgroundColor: '#FFFFFF' }}
                  >
                    <option value="">-- Seleccione una matrícula activa --</option>
                    {activeEnrollments.map((enr) => (
                      <option key={enr.id} value={enr.id}>
                        {getStudentLabel(enr.student_id)} — Grupo: {getGroupLabel(enr.group_id)} ({enr.enrollment_date})
                      </option>
                    ))}
                  </select>
                ) : (
                  <p style={{ fontSize: '0.8125rem', color: '#EF4444', margin: '0.25rem 0 0 0' }}>
                    {isCatalogsLoading ? 'Cargando matrículas activas...' : 'No hay matrículas activas en la institución para trasladar.'}
                  </p>
                )}
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="transfer-target-group-select" style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Salón / Grupo Destino *
                </label>
                {candidateGroups.length > 0 ? (
                  <select
                    id="transfer-target-group-select"
                    value={targetGroupId}
                    onChange={(e) => {
                      setTargetGroupId(e.target.value)
                    }}
                    required
                    disabled={isCatalogsLoading || isSubmitting || !enrollmentId}
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', backgroundColor: '#FFFFFF' }}
                  >
                    <option value="">-- Seleccione el grupo destino --</option>
                    {candidateGroups.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.name} — Jornada {g.shift} (Cupo: {g.capacity_limit})
                      </option>
                    ))}
                  </select>
                ) : (
                  <p style={{ fontSize: '0.8125rem', color: '#64748B', margin: '0.25rem 0 0 0' }}>
                    {isCatalogsLoading
                      ? 'Cargando salones destino...'
                      : !enrollmentId
                        ? 'Seleccione primero una matrícula activa.'
                        : 'No hay otros salones disponibles.'}
                  </p>
                )}
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Motivo Administrativo o Académico *
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => {
                    setReason(e.target.value)
                  }}
                  required
                  rows={3}
                  placeholder="Justificación del traslado escolar (ej: solicitud de acudiente, reubicación de cupo)..."
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                style={{ width: '100%' }}
                disabled={isSubmitting || !enrollmentId || !targetGroupId}
              >
                {isSubmitting ? <LoadingSpinner size="sm" /> : 'Ejecutar Traslado Atómico'}
              </Button>
            </form>
          ) : (
            <Alert
              variant="warning"
              message="No cuenta con el permiso 'enrollments:transfer' para ejecutar traslados de grupo."
            />
          )}
        </Card>
      </div>

      {/* History Inspector Card */}
      <div>
        <Card
          title="Historial de Traslados por Matrícula"
          subtitle="Consulte el registro de auditoría inmutable de traslados de salón."
        >
          <form onSubmit={(e) => void handleQueryHistory(e)} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
            {allEnrollments.length > 0 ? (
              <select
                value={queryEnrollmentId}
                onChange={(e) => {
                  setQueryEnrollmentId(e.target.value)
                }}
                required
                style={{ flex: 1, padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem', backgroundColor: '#FFFFFF' }}
              >
                <option value="">-- Seleccione una matrícula para auditar historial --</option>
                {allEnrollments.map((enr) => (
                  <option key={enr.id} value={enr.id}>
                    {getStudentLabel(enr.student_id)} — {getGroupLabel(enr.group_id)} ({enr.status})
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                placeholder="UUID de la matrícula..."
                value={queryEnrollmentId}
                onChange={(e) => {
                  setQueryEnrollmentId(e.target.value)
                }}
                required
                style={{ flex: 1, padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
              />
            )}
            <Button type="submit" variant="secondary" size="sm" disabled={isQuerying || !queryEnrollmentId}>
              {isQuerying ? <LoadingSpinner size="sm" /> : 'Consultar'}
            </Button>
          </form>

          {isQuerying ? (
            <div style={{ padding: '2rem', textAlign: 'center' }}>
              <LoadingSpinner size="md" />
              <p style={{ color: '#64748B', fontSize: '0.875rem', marginTop: '0.5rem' }}>
                Consultando registros históricos...
              </p>
            </div>
          ) : hasQueried && historyItems.length === 0 ? (
            <EmptyState
              icon="🔄"
              title="Sin traslados registrados"
              description="Esta matrícula no presenta traslados de salón históricos."
            />
          ) : historyItems.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '420px', overflowY: 'auto' }}>
              {historyItems.map((h) => (
                <div
                  key={h.id}
                  style={{
                    padding: '1rem',
                    backgroundColor: '#F8FAFC',
                    borderRadius: '8px',
                    border: '1px solid #E2E8F0',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <Badge variant="info" size="sm">Traslado</Badge>
                    <span style={{ fontSize: '0.75rem', color: '#64748B' }}>{h.transfer_date}</span>
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: '#1E293B', marginBottom: '0.25rem' }}>
                    <strong>Origen:</strong> <code>{h.previous_group_id.substring(0, 8)}...</code> →{' '}
                    <strong>Destino:</strong> <code>{h.new_group_id.substring(0, 8)}...</code>
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: '#475569', fontStyle: 'italic' }}>
                    &ldquo;{h.reason}&rdquo;
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '0.35rem' }}>
                    Operador: <code>{h.transferred_by_user_id.substring(0, 8)}...</code>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </Card>
      </div>
    </div>
  )
}

export default TransfersView
