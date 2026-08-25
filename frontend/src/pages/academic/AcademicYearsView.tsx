/**
 * PEVN Frontend — Academic Years View
 *
 * Full lifecycle management for Academic Years (Años Lectivos):
 * Planning, Activation, Listing, Filtering, and Closing.
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
  AcademicYearCalendarType,
  AcademicYearCreateRequest,
  AcademicYearResponse,
  AcademicYearStatus,
  ApiError,
} from '@/types'

export const AcademicYearsView: React.FC = () => {
  const { hasPermission } = useAuth()

  const [years, setYears] = useState<AcademicYearResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [statusFilter, setStatusFilter] = useState<AcademicYearStatus | undefined>(undefined)
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Create Modal State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [createYear, setCreateYear] = useState<number>(new Date().getFullYear() + 1)
  const [createName, setCreateName] = useState<string>(`Año Escolar ${String(new Date().getFullYear() + 1)}`)
  const [createStartDate, setCreateStartDate] = useState<string>(`${String(new Date().getFullYear() + 1)}-02-01`)
  const [createEndDate, setCreateEndDate] = useState<string>(`${String(new Date().getFullYear() + 1)}-11-30`)
  const [createCalendar, setCreateCalendar] = useState<AcademicYearCalendarType>('CALENDAR_A')

  // Action Confirmation Modal
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean
    action: 'activate' | 'close' | null
    year: AcademicYearResponse | null
  }>({
    isOpen: false,
    action: null,
    year: null,
  })

  const loadYears = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await academicApi.listAcademicYears(statusFilter)
      setYears(data.items)
      setTotal(data.total)
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al cargar años lectivos'))
    } finally {
      setIsLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    void loadYears()
  }, [loadYears])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)

    const payload: AcademicYearCreateRequest = {
      year: createYear,
      name: createName.trim(),
      start_date: createStartDate,
      end_date: createEndDate,
      calendar_type: createCalendar,
      status: 'PLANNING',
    }

    try {
      await academicApi.createAcademicYear(payload)
      setSuccessMsg(`Año lectivo "${payload.name}" creado exitosamente.`)
      setIsCreateOpen(false)
      await loadYears()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al crear año lectivo'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleExecuteAction = async () => {
    if (!confirmModal.year || !confirmModal.action) return
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)

    try {
      if (confirmModal.action === 'activate') {
        await academicApi.activateAcademicYear(confirmModal.year.id)
        setSuccessMsg(`Año lectivo ${String(confirmModal.year.year)} activado exitosamente.`)
      } else {
        await academicApi.closeAcademicYear(confirmModal.year.id)
        setSuccessMsg(`Año lectivo ${String(confirmModal.year.year)} cerrado formalmente.`)
      }
      setConfirmModal({ isOpen: false, action: null, year: null })
      await loadYears()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al ejecutar transición de estado'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const getStatusBadge = (status: AcademicYearStatus) => {
    switch (status) {
      case 'ACTIVE':
        return <Badge variant="success">ACTIVO</Badge>
      case 'PLANNING':
        return <Badge variant="warning">PLANIFICACIÓN</Badge>
      case 'CLOSED':
        return <Badge variant="neutral">CERRADO</Badge>
      default:
        return <Badge>{status}</Badge>
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
              const val = e.target.value as AcademicYearStatus | ''
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
            <option value="PLANNING">Planificación (PLANNING)</option>
            <option value="ACTIVE">Activo (ACTIVE)</option>
            <option value="CLOSED">Cerrado (CLOSED)</option>
          </select>
        </div>

        {hasPermission('academic_years:create') && (
          <Button
            variant="primary"
            onClick={() => {
              setIsCreateOpen(true)
            }}
          >
            + Nuevo Año Lectivo
          </Button>
        )}
      </div>

      {/* Table Card */}
      <Card
        title="Años Lectivos Registrados"
        subtitle={`Total de períodos registrados: ${String(total)}`}
        action={
          <Button variant="secondary" size="sm" onClick={() => void loadYears()}>
            Refrescar
          </Button>
        }
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando calendario académico...
            </p>
          </div>
        ) : years.length === 0 ? (
          <EmptyState
            icon="📅"
            title="No se encontraron años lectivos"
            description="No hay años lectivos registrados para los filtros seleccionados."
            actionLabel={hasPermission('academic_years:create') ? '+ Crear Primer Año' : undefined}
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
                  <th style={{ padding: '0.75rem 1rem' }}>Año</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Nombre</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Calendario</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Vigencia</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Estado</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {years.map((y) => (
                  <tr
                    key={y.id}
                    style={{
                      borderBottom: '1px solid #F1F5F9',
                      transition: 'background-color 100ms',
                    }}
                  >
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                      {y.year}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#1E293B' }}>{y.name}</td>
                    <td style={{ padding: '0.875rem 1rem', color: '#64748B' }}>
                      {y.calendar_type === 'CALENDAR_A' ? 'Calendario A' : 'Calendario B'}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#475569', fontSize: '0.8125rem' }}>
                      {y.start_date} → {y.end_date}
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>{getStatusBadge(y.status)}</td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                        {y.status === 'PLANNING' && hasPermission('academic_years:update') && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => {
                              setConfirmModal({ isOpen: true, action: 'activate', year: y })
                            }}
                          >
                            Activar
                          </Button>
                        )}
                        {y.status === 'ACTIVE' && hasPermission('academic_years:close') && (
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => {
                              setConfirmModal({ isOpen: true, action: 'close', year: y })
                            }}
                          >
                            Cerrar Año
                          </Button>
                        )}
                        {y.status === 'CLOSED' && (
                          <span style={{ fontSize: '0.8125rem', color: '#94A3B8', fontStyle: 'italic' }}>
                            Concluido
                          </span>
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

      {/* Create Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false)
        }}
        title="Crear Nuevo Año Lectivo"
        subtitle="Configure los parámetros del calendario escolar institucional."
      >
        <form onSubmit={(e) => void handleCreate(e)}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Año Calendario (2000 - 2100) *
            </label>
            <input
              type="number"
              min={2000}
              max={2100}
              value={createYear}
              onChange={(e) => {
                const yr = Number(e.target.value)
                setCreateYear(yr)
                setCreateName(`Año Escolar ${String(yr)}`)
              }}
              required
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Nombre Descriptivo *
            </label>
            <input
              type="text"
              value={createName}
              onChange={(e) => {
                setCreateName(e.target.value)
              }}
              required
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Fecha de Inicio *
              </label>
              <input
                type="date"
                value={createStartDate}
                onChange={(e) => {
                  setCreateStartDate(e.target.value)
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Fecha de Finalización *
              </label>
              <input
                type="date"
                value={createEndDate}
                onChange={(e) => {
                  setCreateEndDate(e.target.value)
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Tipo de Calendario (MEN Colombia) *
            </label>
            <select
              value={createCalendar}
              onChange={(e) => {
                setCreateCalendar(e.target.value as AcademicYearCalendarType)
              }}
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            >
              <option value="CALENDAR_A">Calendario A (Febrero - Noviembre)</option>
              <option value="CALENDAR_B">Calendario B (Septiembre - Junio)</option>
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
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Guardar Año Lectivo'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* State Transition Confirmation Modal */}
      <Modal
        isOpen={confirmModal.isOpen}
        onClose={() => {
          setConfirmModal({ isOpen: false, action: null, year: null })
        }}
        title={
          confirmModal.action === 'activate'
            ? 'Confirmar Activación de Año Lectivo'
            : 'Confirmar Cierre de Año Lectivo'
        }
        maxWidth="sm"
      >
        <p style={{ fontSize: '0.9rem', color: '#475569', lineHeight: 1.5, marginBottom: '1.5rem' }}>
          {confirmModal.action === 'activate' ? (
            <>
              ¿Está seguro de que desea <strong>activar</strong> el año escolar{' '}
              <strong>{confirmModal.year?.name}</strong>? Esta acción habilitará matrículas y
              asignaciones académicas activas.
            </>
          ) : (
            <>
              ¿Está seguro de que desea <strong>cerrar</strong> el año escolar{' '}
              <strong>{confirmModal.year?.name}</strong>? Esta acción es irreversible y finalizará el
              ciclo académico formal.
            </>
          )}
        </p>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <Button
            variant="secondary"
            onClick={() => {
              setConfirmModal({ isOpen: false, action: null, year: null })
            }}
            disabled={isSubmitting}
          >
            Cancelar
          </Button>
          <Button
            variant={confirmModal.action === 'activate' ? 'primary' : 'danger'}
            onClick={() => void handleExecuteAction()}
            disabled={isSubmitting}
          >
            {isSubmitting ? <LoadingSpinner size="sm" /> : 'Confirmar Acción'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}

export default AcademicYearsView
