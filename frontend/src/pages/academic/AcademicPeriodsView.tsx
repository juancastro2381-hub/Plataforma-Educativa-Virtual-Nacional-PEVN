/**
 * PEVN Frontend — Academic Periods View (Períodos Académicos)
 *
 * Professional view displaying the term subdivisions, start/end dates,
 * evaluation weight percentages, and closure status of academic years.
 * Protected by RBAC permission: 'academic_periods:read'.
 * Supports period creation protected by 'academic_periods:create'.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { academicApi } from '@/services/academic'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Modal } from '@/components/ui/Modal'
import { PeriodTemplateWizardModal } from '@/components/academic/PeriodTemplateWizardModal'
import { useAuth } from '@/hooks/useAuth'
import type {
  AcademicPeriodCreateRequest,
  AcademicPeriodResponse,
  AcademicYearResponse,
} from '@/types'

export const AcademicPeriodsView: React.FC = () => {
  const { hasPermission } = useAuth()

  const [years, setYears] = useState<AcademicYearResponse[]>([])
  const [selectedYearId, setSelectedYearId] = useState<string>('')
  const [periods, setPeriods] = useState<AcademicPeriodResponse[]>([])
  const [isLoadingYears, setIsLoadingYears] = useState<boolean>(true)
  const [isLoadingPeriods, setIsLoadingPeriods] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Guided Template Wizard Modal State
  const [isTemplateWizardOpen, setIsTemplateWizardOpen] = useState<boolean>(false)

  // Create Period Modal State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [formError, setFormError] = useState<string | null>(null)

  const [createPeriodNumber, setCreatePeriodNumber] = useState<number>(1)
  const [createName, setCreateName] = useState<string>('Primer Período')
  const [createWeight, setCreateWeight] = useState<number>(25)
  const [createStartDate, setCreateStartDate] = useState<string>('')
  const [createEndDate, setCreateEndDate] = useState<string>('')

  const loadYears = useCallback(async () => {
    setIsLoadingYears(true)
    setError(null)
    try {
      const res = await academicApi.listAcademicYears()
      setYears(res.items)
      if (res.items.length > 0) {
        // Default to active year or the latest one
        const active = res.items.find((y) => y.status === 'ACTIVE') || res.items[0]
        setSelectedYearId(active.id)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cargar años lectivos.')
    } finally {
      setIsLoadingYears(false)
    }
  }, [])

  const loadPeriods = useCallback(async (yearId: string) => {
    if (!yearId) {
      setPeriods([])
      return
    }
    setIsLoadingPeriods(true)
    setError(null)
    try {
      const res = await academicApi.listAcademicPeriods(yearId)
      setPeriods(res.items)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cargar períodos del año lectivo.')
    } finally {
      setIsLoadingPeriods(false)
    }
  }, [])

  useEffect(() => {
    void loadYears()
  }, [loadYears])

  useEffect(() => {
    if (selectedYearId) {
      void loadPeriods(selectedYearId)
    }
  }, [selectedYearId, loadPeriods])

  const selectedYear = years.find((y) => y.id === selectedYearId)

  // Open modal with smart defaults based on existing periods and selected year
  const handleOpenCreate = () => {
    setFormError(null)
    const nextNumber = periods.length > 0
      ? Math.max(...periods.map((p) => p.period_number)) + 1
      : 1
    setCreatePeriodNumber(nextNumber)

    const periodNames = ['Primer Período', 'Segundo Período', 'Tercer Período', 'Cuarto Período', 'Quinto Período']
    setCreateName(periodNames[nextNumber - 1] || `Período ${nextNumber}`)

    // Remaining weight percentage
    const existingWeight = periods.reduce((sum, p) => sum + Number(p.weight_percentage), 0)
    const remainingWeight = Math.max(0, 100 - existingWeight)
    setCreateWeight(remainingWeight > 0 ? (remainingWeight >= 25 ? 25 : remainingWeight) : 25)

    if (selectedYear) {
      setCreateStartDate(selectedYear.start_date)
      setCreateEndDate(selectedYear.end_date)
    } else {
      setCreateStartDate('')
      setCreateEndDate('')
    }

    setIsCreateOpen(true)
  }

  const handleCreatePeriod = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedYearId) {
      setFormError('Debe seleccionar un año lectivo válido.')
      return
    }
    if (createPeriodNumber < 1) {
      setFormError('El número del período debe ser mayor o igual a 1.')
      return
    }
    if (!createName.trim()) {
      setFormError('El nombre del período es obligatorio.')
      return
    }
    if (createWeight <= 0 || createWeight > 100) {
      setFormError('La ponderación debe ser mayor a 0% y menor o igual a 100%.')
      return
    }
    if (!createStartDate || !createEndDate) {
      setFormError('Debe ingresar las fechas de inicio y finalización.')
      return
    }
    if (createStartDate >= createEndDate) {
      setFormError('La fecha de inicio debe ser anterior a la fecha de finalización.')
      return
    }
    if (selectedYear) {
      if (createStartDate < selectedYear.start_date || createEndDate > selectedYear.end_date) {
        setFormError(
          `Las fechas deben estar dentro de la vigencia del año escolar (${selectedYear.start_date} a ${selectedYear.end_date}).`
        )
        return
      }
    }

    setIsSubmitting(true)
    setFormError(null)
    setError(null)
    setSuccessMsg(null)

    const payload: AcademicPeriodCreateRequest = {
      period_number: Number(createPeriodNumber),
      name: createName.trim(),
      weight_percentage: Number(createWeight),
      start_date: createStartDate,
      end_date: createEndDate,
    }

    try {
      await academicApi.createAcademicPeriod(selectedYearId, payload)
      setSuccessMsg(`Período "${payload.name}" (#${payload.period_number}) creado exitosamente.`)
      setIsCreateOpen(false)
      await loadPeriods(selectedYearId)
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Error al registrar el período académico.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div id="academic-periods-view">
      {/* Global Alerts */}
      {error && <Alert error={new Error(error)} onClose={() => setError(null)} />}
      {successMsg && (
        <Alert variant="success" message={successMsg} onClose={() => setSuccessMsg(null)} />
      )}

      <Card
        title="Períodos de Evaluación y Calendario Escolar"
        subtitle="Subdivisiones periódicas del año lectivo para el registro y ponderación de calificaciones."
        action={
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                if (selectedYearId) void loadPeriods(selectedYearId)
              }}
              id="btn-refresh-periods"
            >
              🔄 Refrescar
            </Button>
            {hasPermission('academic_periods:create') && (
              <>
                <Button
                  variant="primary"
                  size="sm"
                  id="btn-configure-period-template"
                  onClick={() => setIsTemplateWizardOpen(true)}
                  disabled={!selectedYearId || selectedYear?.status === 'CLOSED'}
                >
                  ✨ Configurar períodos académicos
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  id="btn-new-period"
                  onClick={handleOpenCreate}
                  disabled={!selectedYearId || selectedYear?.status === 'CLOSED'}
                >
                  + Nuevo Período
                </Button>
              </>
            )}
          </div>
        }
      >
        {/* Year Selector */}
        <div style={{ marginBottom: '1.25rem', display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ width: '280px' }}>
            <label
              htmlFor="period-year-select"
              style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
            >
              Año Lectivo
            </label>
            <select
              id="period-year-select"
              value={selectedYearId}
              onChange={(e) => setSelectedYearId(e.target.value)}
              disabled={isLoadingYears || years.length === 0}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                color: '#0F172A',
              }}
            >
              {years.map((y) => (
                <option key={y.id} value={y.id}>
                  {y.name} ({y.year}) — {y.status}
                </option>
              ))}
            </select>
          </div>

          {selectedYear && (
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '1.2rem' }}>
              <Badge variant={selectedYear.status === 'ACTIVE' ? 'success' : selectedYear.status === 'CLOSED' ? 'danger' : 'warning'}>
                {selectedYear.status}
              </Badge>
              <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                Vigencia: {selectedYear.start_date} → {selectedYear.end_date}
              </span>
            </div>
          )}
        </div>

        {isLoadingYears || isLoadingPeriods ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando períodos académicos del año lectivo...
            </p>
          </div>
        ) : periods.length === 0 ? (
          <EmptyState
            icon="📅"
            title="No se encontraron períodos"
            description="Este año lectivo no tiene períodos académicos configurados todavía. Utilice el asistente de plantillas legales o agregue períodos individuales."
            actionLabel={
              hasPermission('academic_periods:create') && selectedYear?.status !== 'CLOSED'
                ? '✨ Configurar períodos académicos'
                : undefined
            }
            onAction={() => setIsTemplateWizardOpen(true)}
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table
              id="periods-table"
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '0.875rem',
                textAlign: 'left',
              }}
            >
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Período</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Nombre</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Rango de Fechas</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Ponderación</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Estado</th>
                </tr>
              </thead>
              <tbody>
                {periods.map((p) => (
                  <tr
                    key={p.id}
                    style={{
                      borderBottom: '1px solid #F1F5F9',
                      transition: 'background-color 150ms',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8FAFC')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                      #{p.period_number}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 600, color: '#1E293B' }}>
                      {p.name}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#475569', fontSize: '0.8125rem' }}>
                      {p.start_date} → {p.end_date}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'center' }}>
                      <span
                        style={{
                          backgroundColor: '#FEF3C7',
                          color: '#92400E',
                          fontWeight: 700,
                          padding: '0.2rem 0.6rem',
                          borderRadius: '9999px',
                          fontSize: '0.8125rem',
                        }}
                      >
                        {p.weight_percentage}%
                      </span>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'center' }}>
                      <Badge variant={p.is_closed ? 'danger' : 'success'}>
                        {p.is_closed ? 'Cerrado' : 'Abierto'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal: Crear Período Académico */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          if (!isSubmitting) setIsCreateOpen(false)
        }}
        title="Nuevo Período Académico"
        subtitle={
          selectedYear
            ? `Asociado al año lectivo ${selectedYear.name} (${selectedYear.year})`
            : undefined
        }
      >
        <form onSubmit={handleCreatePeriod}>
          {formError && (
            <div style={{ marginBottom: '1rem' }}>
              <Alert error={new Error(formError)} onClose={() => setFormError(null)} />
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label
                htmlFor="period-number-input"
                style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
              >
                Número de Período *
              </label>
              <input
                id="period-number-input"
                type="number"
                min="1"
                max="10"
                value={createPeriodNumber}
                onChange={(e) => setCreatePeriodNumber(parseInt(e.target.value, 10) || 1)}
                required
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '8px',
                  border: '1px solid #CBD5E1',
                  fontSize: '0.875rem',
                }}
              />
            </div>

            <div>
              <label
                htmlFor="period-name-input"
                style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
              >
                Nombre del Período *
              </label>
              <input
                id="period-name-input"
                type="text"
                placeholder="Ej. Primer Período"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '8px',
                  border: '1px solid #CBD5E1',
                  fontSize: '0.875rem',
                }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label
              htmlFor="period-weight-input"
              style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Ponderación de Calificación (%) *
            </label>
            <input
              id="period-weight-input"
              type="number"
              step="0.01"
              min="0.01"
              max="100"
              value={createWeight}
              onChange={(e) => setCreateWeight(parseFloat(e.target.value) || 0)}
              required
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
              }}
            />
            <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block', marginTop: '0.25rem' }}>
              Porcentaje que aporta a la calificación final del año escolar (la suma anual debe ser 100%).
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <label
                htmlFor="period-start-date-input"
                style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
              >
                Fecha de Inicio *
              </label>
              <input
                id="period-start-date-input"
                type="date"
                value={createStartDate}
                onChange={(e) => setCreateStartDate(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '8px',
                  border: '1px solid #CBD5E1',
                  fontSize: '0.875rem',
                }}
              />
            </div>

            <div>
              <label
                htmlFor="period-end-date-input"
                style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
              >
                Fecha de Finalización *
              </label>
              <input
                id="period-end-date-input"
                type="date"
                value={createEndDate}
                onChange={(e) => setCreateEndDate(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '8px',
                  border: '1px solid #CBD5E1',
                  fontSize: '0.875rem',
                }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
            <Button
              variant="secondary"
              type="button"
              onClick={() => setIsCreateOpen(false)}
              disabled={isSubmitting}
              id="btn-cancel-create-period"
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              type="submit"
              disabled={isSubmitting}
              id="btn-submit-create-period"
            >
              {isSubmitting ? 'Guardando Período...' : 'Guardar Período'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Guided Period Template Configuration Wizard Modal */}
      <PeriodTemplateWizardModal
        isOpen={isTemplateWizardOpen}
        onClose={() => setIsTemplateWizardOpen(false)}
        academicYear={selectedYear || null}
        onSuccess={async () => {
          if (selectedYearId) {
            await loadPeriods(selectedYearId)
            setSuccessMsg('Configuración de períodos académicos aplicada exitosamente según el SIEE institucional.')
          }
        }}
      />
    </div>
  )
}

export default AcademicPeriodsView
