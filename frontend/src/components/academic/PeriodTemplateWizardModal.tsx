/**
 * PEVN Frontend — Period Template Wizard Modal (NTA-10-R7)
 *
 * Guided workflow allowing educational administrators (Rector) to select,
 * review, customize, and provision legally aligned academic period templates
 * complying with Decreto 1290 de 2009, Ley 115 de 1994, institutional SIEE,
 * and applicable territorial school calendars.
 */

import React, { useEffect, useMemo, useState } from 'react'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Modal } from '@/components/ui/Modal'
import { academicApi } from '@/services/academic'
import type {
  AcademicPeriodTemplateType,
  AcademicYearResponse,
  DraftPeriodItem,
  PeriodTemplatePreviewResponse,
  SieeComplianceMetadata,
} from '@/types'

export interface PeriodTemplateWizardModalProps {
  isOpen: boolean
  onClose: () => void
  academicYear: AcademicYearResponse | null
  onSuccess: () => Promise<void>
}

interface TemplateOption {
  type: AcademicPeriodTemplateType
  title: string
  subtitle: string
  weightsSummary: string
  description: string
  isRecommended?: boolean
}

const TEMPLATE_OPTIONS: TemplateOption[] = [
  {
    type: 'PERIODS_4',
    title: '4 Períodos — Cuatro Períodos de Evaluación',
    subtitle: 'Distribución trimestral estándar',
    weightsSummary: '25% cada período (25%, 25%, 25%, 25%)',
    description:
      'Estructura tradicional ampliamente implementada en instituciones colombianas para cuatro entregas periódicas de boletines.',
    isRecommended: true,
  },
  {
    type: 'SEMESTRAL_2',
    title: '2 Períodos — Semestral',
    subtitle: 'Dos términos evaluativos',
    weightsSummary: '50%, 50%',
    description:
      'Organización semestral para instituciones con esquemas semestralizados o ciclos lectivos integrados de dos cortes.',
  },
  {
    type: 'TRIMESTRAL_3',
    title: '3 Períodos — Tres Períodos de Evaluación',
    subtitle: 'Tres términos evaluativos',
    weightsSummary: '33.33%, 33.33%, 33.34%',
    description:
      'Distribución en tres términos regulares con ajuste matemático decimal para alcanzar con exactitud el 100.00%.',
  },
  {
    type: 'PERIODS_5',
    title: '5 Períodos — Cinco Períodos de Evaluación',
    subtitle: 'Cinco términos bimestrales',
    weightsSummary: '20% cada período (20% x 5)',
    description:
      'Esquema de evaluación continua y seguimiento estrecho con cinco informes periódicos durante el año lectivo.',
  },
  {
    type: 'CUSTOM',
    title: 'Configuración Personalizada',
    subtitle: 'Estructura definida por la institución',
    weightsSummary: 'Ponderación configurable',
    description:
      'Defina libremente la cantidad de períodos, nombres, fechas y pesos porcentuales según el SIEE específico de su institución.',
  },
]

export const PeriodTemplateWizardModal: React.FC<PeriodTemplateWizardModalProps> = ({
  isOpen,
  onClose,
  academicYear,
  onSuccess,
}) => {
  // Wizard Steps: 1 = Template selection, 2 = Preview & reconciliation, 3 = Review & edit, 4 = SIEE Compliance & Activation
  const [currentStep, setCurrentStep] = useState<number>(1)
  const [selectedTemplate, setSelectedTemplate] = useState<AcademicPeriodTemplateType>('PERIODS_4')
  const [customPeriodCount, setCustomPeriodCount] = useState<number>(4)

  // Data states
  const [previewData, setPreviewData] = useState<PeriodTemplatePreviewResponse | null>(null)
  const [editedPeriods, setEditedPeriods] = useState<DraftPeriodItem[]>([])

  // Compliance state
  const [compliance, setCompliance] = useState<SieeComplianceMetadata>({
    siee_version: '',
    approval_act: '',
    approval_date: undefined,
    calendar_source: '',
    calendar_source_url: '',
    reviewed_at: new Date().toISOString().split('T')[0],
    confirmed_by_rector: false,
  })

  // Status states
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [draftNotice, setDraftNotice] = useState<string | null>(null)

  // Local storage draft key
  const draftStorageKey = useMemo(() => {
    return academicYear ? `pevn_period_template_draft_${academicYear.id}` : null
  }, [academicYear])

  // Reset or load saved draft on open
  useEffect(() => {
    if (isOpen && academicYear) {
      setCurrentStep(1)
      setSelectedTemplate('PERIODS_4')
      setErrorMsg(null)
      setDraftNotice(null)

      if (draftStorageKey) {
        const savedDraft = localStorage.getItem(draftStorageKey)
        if (savedDraft) {
          try {
            const parsed = JSON.parse(savedDraft)
            if (parsed.template_type) setSelectedTemplate(parsed.template_type)
            if (parsed.periods && Array.isArray(parsed.periods)) setEditedPeriods(parsed.periods)
            if (parsed.compliance) setCompliance(parsed.compliance)
            setDraftNotice('Se detectó un borrador guardado en este navegador. Puede continuar su configuración.')
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  }, [isOpen, academicYear, draftStorageKey])

  // Calculate live cumulative weight
  const totalWeight = useMemo(() => {
    return editedPeriods.reduce((acc, p) => acc + (Number(p.weight_percentage) || 0), 0)
  }, [editedPeriods])

  const isWeightValid = useMemo(() => {
    return Math.abs(totalWeight - 100.0) <= 0.01
  }, [totalWeight])

  // Step 1 -> Step 2: Fetch Preview from Backend
  const handleFetchPreview = async () => {
    if (!academicYear) return
    setIsLoading(true)
    setErrorMsg(null)

    try {
      const res = await academicApi.previewPeriodTemplate(academicYear.id, {
        template_type: selectedTemplate,
        custom_period_count: selectedTemplate === 'CUSTOM' ? customPeriodCount : undefined,
      })
      setPreviewData(res)
      setEditedPeriods(res.proposed_periods)
      setCurrentStep(2)
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error al generar la propuesta de períodos.')
    } finally {
      setIsLoading(false)
    }
  }

  // Handle live inline edits in Step 3
  const handlePeriodFieldChange = (
    index: number,
    field: keyof DraftPeriodItem,
    value: string | number
  ) => {
    setEditedPeriods((prev) => {
      const updated = [...prev]
      updated[index] = {
        ...updated[index],
        [field]: value,
      }
      return updated
    })
  }

  // Save draft locally
  const handleSaveDraft = () => {
    if (!draftStorageKey) return
    const draftPayload = {
      template_type: selectedTemplate,
      periods: editedPeriods,
      compliance,
      savedAt: new Date().toISOString(),
    }
    localStorage.setItem(draftStorageKey, JSON.stringify(draftPayload))
    setDraftNotice('Borrador guardado localmente de forma segura. Puede continuar en cualquier momento.')
  }

  // Provisioning Action (Step 4)
  const handleProvision = async (activateImmediately: boolean) => {
    if (!academicYear) return
    if (!isWeightValid) {
      setErrorMsg(`La suma de ponderaciones debe ser exactamente 100.00% (actual: ${totalWeight.toFixed(2)}%).`)
      return
    }
    if (activateImmediately && !compliance.confirmed_by_rector) {
      setErrorMsg('Debe confirmar formalmente la declaración de conformidad institucional con el SIEE para activar.')
      return
    }

    setIsSubmitting(true)
    setErrorMsg(null)

    try {
      await academicApi.provisionPeriodTemplate(academicYear.id, {
        template_type: selectedTemplate,
        periods: editedPeriods,
        compliance,
        activate_immediately: activateImmediately,
      })

      // Clean local draft
      if (draftStorageKey) {
        localStorage.removeItem(draftStorageKey)
      }

      await onSuccess()
      onClose()
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error al aprovisionar los períodos académicos.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen || !academicYear) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        if (!isSubmitting) onClose()
      }}
      title="Configuración de Períodos Académicos y SIEE"
      subtitle={`Año Lectivo: ${academicYear.name} (${academicYear.year}) — Vigencia: ${academicYear.start_date} al ${academicYear.end_date}`}
      maxWidth="xl"
    >
      <div id="period-template-wizard">
        {/* Step Indicator Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '1.25rem',
            paddingBottom: '0.75rem',
            borderBottom: '1px solid #E2E8F0',
          }}
        >
          {[
            { num: 1, label: 'Plantilla' },
            { num: 2, label: 'Vista Previa' },
            { num: 3, label: 'Ajuste SIEE' },
            { num: 4, label: 'Conformidad' },
          ].map((s) => (
            <div
              key={s.num}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                opacity: currentStep === s.num ? 1 : 0.6,
                fontWeight: currentStep === s.num ? 700 : 500,
                color: currentStep === s.num ? '#1E40AF' : '#64748B',
                fontSize: '0.8125rem',
              }}
            >
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  backgroundColor: currentStep === s.num ? '#2563EB' : '#CBD5E1',
                  color: '#FFFFFF',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                }}
              >
                {s.num}
              </span>
              <span>{s.label}</span>
            </div>
          ))}
        </div>

        {/* Global Notifications */}
        {errorMsg && (
          <div style={{ marginBottom: '1rem' }}>
            <Alert error={new Error(errorMsg)} onClose={() => setErrorMsg(null)} />
          </div>
        )}
        {draftNotice && (
          <div style={{ marginBottom: '1rem' }}>
            <Alert variant="info" message={draftNotice} onClose={() => setDraftNotice(null)} />
          </div>
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Consultando propuesta no destructiva con el servidor...
            </p>
          </div>
        )}

        {/* =================================================================== */}
        {/* PASO 1: SELECCIÓN DE PLANTILLA */}
        {/* =================================================================== */}
        {!isLoading && currentStep === 1 && (
          <div>
            <div
              style={{
                backgroundColor: '#EFF6FF',
                border: '1px solid #BFDBFE',
                borderRadius: '8px',
                padding: '0.875rem 1rem',
                marginBottom: '1.25rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '1rem' }}>⚖️</span>
                <span style={{ fontWeight: 700, fontSize: '0.875rem', color: '#1E3A8A' }}>
                  Principios Legales y Autonomía Institucional (Decreto 1290 de 2009 / Ley 115 de 1994, Art. 77)
                </span>
              </div>
              <p style={{ margin: 0, fontSize: '0.8125rem', color: '#1E40AF', lineHeight: '1.4' }}>
                Las siguientes plantillas son <strong>propuestas operativas de referencia</strong>. El Ministerio de Educación
                Nacional (MEN) no impone un número fijo de períodos ni porcentajes universales. Cada institución define
                autónomamente la periodicidad y ponderaciones en su <strong>SIEE</strong>, articulado con el calendario
                escolar territorial.
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
              {TEMPLATE_OPTIONS.map((tmpl) => (
                <div
                  key={tmpl.type}
                  id={`template-card-${tmpl.type}`}
                  onClick={() => setSelectedTemplate(tmpl.type)}
                  style={{
                    border: selectedTemplate === tmpl.type ? '2px solid #2563EB' : '1px solid #E2E8F0',
                    backgroundColor: selectedTemplate === tmpl.type ? '#F8FAFC' : '#FFFFFF',
                    borderRadius: '8px',
                    padding: '1rem',
                    cursor: 'pointer',
                    transition: 'all 150ms ease',
                    boxShadow: selectedTemplate === tmpl.type ? '0 2px 4px rgba(37,99,235,0.1)' : 'none',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: '#0F172A' }}>
                          {tmpl.title}
                        </span>
                        {tmpl.isRecommended && (
                          <Badge variant="info">
                            Plantilla de referencia institucional — no obligatoria por el MEN
                          </Badge>
                        )}
                      </div>
                      <p style={{ margin: 0, fontSize: '0.8125rem', color: '#64748B' }}>
                        {tmpl.description}
                      </p>
                    </div>
                    <div style={{ textAlign: 'right', whiteSpace: 'nowrap', marginLeft: '1rem' }}>
                      <span
                        style={{
                          backgroundColor: '#E0E7FF',
                          color: '#3730A3',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '0.2rem 0.5rem',
                          borderRadius: '6px',
                        }}
                      >
                        {tmpl.weightsSummary}
                      </span>
                    </div>
                  </div>

                  {tmpl.type === 'CUSTOM' && selectedTemplate === 'CUSTOM' && (
                    <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid #E2E8F0' }}>
                      <label
                        htmlFor="custom-period-count"
                        style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
                      >
                        Número de Períodos a Generar (1 a 10):
                      </label>
                      <input
                        id="custom-period-count"
                        type="number"
                        min={1}
                        max={10}
                        value={customPeriodCount}
                        onChange={(e) => setCustomPeriodCount(Math.max(1, Math.min(10, Number(e.target.value))))}
                        style={{
                          width: '120px',
                          padding: '0.4rem 0.6rem',
                          border: '1px solid #CBD5E1',
                          borderRadius: '6px',
                          fontSize: '0.875rem',
                        }}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button variant="secondary" onClick={onClose} id="btn-cancel-step-1">
                Cancelar
              </Button>
              <Button variant="primary" onClick={handleFetchPreview} id="btn-next-to-preview">
                Generar Propuesta no Destructiva →
              </Button>
            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* PASO 2: VISTA PREVIA Y DETECCIÓN NO DESTRUCTIVA */}
        {/* =================================================================== */}
        {!isLoading && currentStep === 2 && previewData && (
          <div>
            <div
              style={{
                backgroundColor: '#F1F5F9',
                borderRadius: '8px',
                padding: '0.75rem 1rem',
                marginBottom: '1rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '0.5rem',
              }}
            >
              <div>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#334155' }}>
                  Plantilla seleccionada:
                </span>{' '}
                <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A' }}>
                  {previewData.template_label}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                  Períodos en base de datos: <strong>{previewData.existing_periods.length}</strong>
                </span>
                <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>|</span>
                <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                  Nuevos a crear: <strong>{previewData.proposed_periods.filter((p) => !p.is_existing).length}</strong>
                </span>
              </div>
            </div>

            {/* Existing periods preservation guarantee */}
            {previewData.existing_periods.length > 0 && (
              <div
                style={{
                  backgroundColor: '#ECFDF5',
                  border: '1px solid #A7F3D0',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                  marginBottom: '1rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>🛡️</span>
                  <span style={{ fontWeight: 700, fontSize: '0.8125rem', color: '#065F46' }}>
                    Garantía de Preservación de Datos Existentes
                  </span>
                </div>
                <p style={{ margin: '0.25rem 0 0', fontSize: '0.75rem', color: '#047857' }}>
                  Se detectaron períodos ya registrados en este año lectivo. La propuesta conserva íntegramente sus
                  registros y propone únicamente los períodos complementarios necesarios sin eliminar datos.
                </p>
              </div>
            )}

            {/* Conflict Warnings */}
            {previewData.has_conflicts && (
              <div
                style={{
                  backgroundColor: '#FFFBEB',
                  border: '1px solid #FDE68A',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                  marginBottom: '1rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <span>⚠️</span>
                  <span style={{ fontWeight: 700, fontSize: '0.8125rem', color: '#92400E' }}>
                    Aspectos Relevantes para Revisión Institucional
                  </span>
                </div>
                <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.75rem', color: '#B45309' }}>
                  {previewData.conflict_messages.map((msg, i) => (
                    <li key={i}>{msg}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Preview Table */}
            <div style={{ overflowX: 'auto', marginBottom: '1.25rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                    <th style={{ padding: '0.5rem' }}>Período</th>
                    <th style={{ padding: '0.5rem' }}>Nombre</th>
                    <th style={{ padding: '0.5rem' }}>Rango de Fechas</th>
                    <th style={{ padding: '0.5rem', textAlign: 'center' }}>Ponderación</th>
                    <th style={{ padding: '0.5rem', textAlign: 'center' }}>Origen</th>
                  </tr>
                </thead>
                <tbody>
                  {editedPeriods.map((p) => (
                    <tr key={p.period_number} style={{ borderBottom: '1px solid #F1F5F9' }}>
                      <td style={{ padding: '0.5rem', fontWeight: 700 }}>#{p.period_number}</td>
                      <td style={{ padding: '0.5rem', fontWeight: 600 }}>{p.name}</td>
                      <td style={{ padding: '0.5rem', color: '#475569' }}>
                        {p.start_date} → {p.end_date}
                      </td>
                      <td style={{ padding: '0.5rem', textAlign: 'center', fontWeight: 700 }}>
                        {p.weight_percentage}%
                      </td>
                      <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                        {p.is_existing ? (
                          <Badge variant="success">Existente (Conservado)</Badge>
                        ) : (
                          <Badge variant="warning">Propuesto (Provisional)</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Button variant="secondary" onClick={() => setCurrentStep(1)} id="btn-back-to-step-1">
                ← Cambiar Plantilla
              </Button>
              <Button variant="primary" onClick={() => setCurrentStep(3)} id="btn-proceed-to-customize">
                Personalizar y Ajustar Fechas/Pesos →
              </Button>
            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* PASO 3: REVISIÓN Y PERSONALIZACIÓN EN VIVO */}
        {/* =================================================================== */}
        {!isLoading && currentStep === 3 && (
          <div>
            <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 700, color: '#0F172A' }}>
                  Ajuste de Ponderaciones y Fechas
                </h4>
                <p style={{ margin: '0.2rem 0 0', fontSize: '0.75rem', color: '#64748B' }}>
                  Modifique los cortes de evaluación según los acuerdos del Consejo Directivo de su institución.
                </p>
              </div>

              {/* Weight Indicator Pill */}
              <div
                style={{
                  padding: '0.4rem 0.8rem',
                  borderRadius: '9999px',
                  backgroundColor: isWeightValid ? '#ECFDF5' : '#FEF2F2',
                  border: isWeightValid ? '1px solid #10B981' : '1px solid #EF4444',
                  color: isWeightValid ? '#065F46' : '#991B1B',
                  fontWeight: 700,
                  fontSize: '0.8125rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                }}
              >
                <span>{isWeightValid ? '✅' : '⚠️'}</span>
                <span>Ponderación Total: {totalWeight.toFixed(2)}% / 100%</span>
              </div>
            </div>

            {/* Editable Grid Table */}
            <div style={{ overflowX: 'auto', marginBottom: '1rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569', textAlign: 'left' }}>
                    <th style={{ padding: '0.5rem', width: '60px' }}>#</th>
                    <th style={{ padding: '0.5rem', width: '180px' }}>Nombre del Período</th>
                    <th style={{ padding: '0.5rem', width: '140px' }}>Fecha Inicio</th>
                    <th style={{ padding: '0.5rem', width: '140px' }}>Fecha Fin</th>
                    <th style={{ padding: '0.5rem', width: '100px', textAlign: 'center' }}>Peso (%)</th>
                    <th style={{ padding: '0.5rem', textAlign: 'center', width: '100px' }}>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {editedPeriods.map((p, idx) => (
                    <tr key={p.period_number} style={{ borderBottom: '1px solid #F1F5F9' }}>
                      <td style={{ padding: '0.5rem', fontWeight: 700 }}>#{p.period_number}</td>
                      <td style={{ padding: '0.5rem' }}>
                        <input
                          type="text"
                          value={p.name}
                          onChange={(e) => handlePeriodFieldChange(idx, 'name', e.target.value)}
                          style={{
                            width: '100%',
                            padding: '0.35rem 0.5rem',
                            border: '1px solid #CBD5E1',
                            borderRadius: '6px',
                            fontSize: '0.8125rem',
                          }}
                        />
                      </td>
                      <td style={{ padding: '0.5rem' }}>
                        <input
                          type="date"
                          value={p.start_date}
                          onChange={(e) => handlePeriodFieldChange(idx, 'start_date', e.target.value)}
                          min={academicYear.start_date}
                          max={academicYear.end_date}
                          style={{
                            width: '100%',
                            padding: '0.35rem 0.5rem',
                            border: '1px solid #CBD5E1',
                            borderRadius: '6px',
                            fontSize: '0.8125rem',
                          }}
                        />
                      </td>
                      <td style={{ padding: '0.5rem' }}>
                        <input
                          type="date"
                          value={p.end_date}
                          onChange={(e) => handlePeriodFieldChange(idx, 'end_date', e.target.value)}
                          min={academicYear.start_date}
                          max={academicYear.end_date}
                          style={{
                            width: '100%',
                            padding: '0.35rem 0.5rem',
                            border: '1px solid #CBD5E1',
                            borderRadius: '6px',
                            fontSize: '0.8125rem',
                          }}
                        />
                      </td>
                      <td style={{ padding: '0.5rem' }}>
                        <input
                          type="number"
                          step="0.01"
                          min="1"
                          max="100"
                          value={p.weight_percentage}
                          onChange={(e) => handlePeriodFieldChange(idx, 'weight_percentage', Number(e.target.value))}
                          style={{
                            width: '100%',
                            padding: '0.35rem 0.5rem',
                            border: '1px solid #CBD5E1',
                            borderRadius: '6px',
                            fontSize: '0.8125rem',
                            textAlign: 'center',
                            fontWeight: 700,
                          }}
                        />
                      </td>
                      <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                        {p.is_existing ? (
                          <Badge variant="success">Existente</Badge>
                        ) : (
                          <Badge variant="warning">Nuevo</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button variant="secondary" onClick={() => setCurrentStep(2)} id="btn-back-to-step-2">
                  ← Vista Previa
                </Button>
                <Button variant="secondary" onClick={handleSaveDraft} id="btn-save-draft">
                  💾 Guardar Borrador
                </Button>
              </div>
              <Button
                variant="primary"
                onClick={() => setCurrentStep(4)}
                disabled={!isWeightValid}
                id="btn-proceed-to-compliance"
              >
                Conformidad SIEE y Activación →
              </Button>
            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* PASO 4: CONFORMIDAD SIEE Y ACTIVACIÓN */}
        {/* =================================================================== */}
        {!isLoading && currentStep === 4 && (
          <div>
            <div
              style={{
                backgroundColor: '#F8FAFC',
                border: '1px solid #E2E8F0',
                borderRadius: '8px',
                padding: '1rem',
                marginBottom: '1.25rem',
              }}
            >
              <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.875rem', fontWeight: 700, color: '#0F172A' }}>
                Resumen de la Configuración a Registrar
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', fontSize: '0.8125rem' }}>
                <div>
                  <span style={{ color: '#64748B' }}>Año Lectivo:</span>{' '}
                  <strong>{academicYear.year}</strong>
                </div>
                <div>
                  <span style={{ color: '#64748B' }}>Total Períodos:</span>{' '}
                  <strong>{editedPeriods.length}</strong>
                </div>
                <div>
                  <span style={{ color: '#64748B' }}>Ponderación Acumulada:</span>{' '}
                  <strong style={{ color: '#059669' }}>{totalWeight.toFixed(2)}%</strong>
                </div>
              </div>
            </div>

            {/* Mandatory Compliance Checkbox */}
            <div
              style={{
                backgroundColor: compliance.confirmed_by_rector ? '#ECFDF5' : '#FEF2F2',
                border: compliance.confirmed_by_rector ? '1px solid #10B981' : '1px solid #EF4444',
                borderRadius: '8px',
                padding: '1rem',
                marginBottom: '1.25rem',
              }}
            >
              <label
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.75rem',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: compliance.confirmed_by_rector ? '#065F46' : '#991B1B',
                  lineHeight: '1.4',
                }}
              >
                <input
                  type="checkbox"
                  id="rector-siee-compliance-checkbox"
                  checked={compliance.confirmed_by_rector}
                  onChange={(e) => setCompliance((prev) => ({ ...prev, confirmed_by_rector: e.target.checked }))}
                  style={{ marginTop: '0.2rem', width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <span>
                  Declaro que esta configuración de períodos evaluativos y porcentajes ha sido revisada y concertada
                  conforme al Sistema Institucional de Evaluación de los Estudiantes (SIEE) de la institución y a la
                  resolución de calendario escolar territorial aplicable expedida por la Secretaría de Educación
                  competente.
                </span>
              </label>
            </div>

            {/* Optional Metadata Fields */}
            <div style={{ border: '1px solid #E2E8F0', borderRadius: '8px', padding: '1rem', marginBottom: '1.5rem' }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <span style={{ fontWeight: 700, fontSize: '0.8125rem', color: '#334155' }}>
                  Metadatos Opcionales de Respaldo Institucional (Consejo Directivo y Calendario):
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.8125rem' }}>
                <div>
                  <label htmlFor="input-siee-version" style={{ display: 'block', fontWeight: 600, color: '#475569', marginBottom: '0.2rem' }}>
                    Versión o Referencia del SIEE:
                  </label>
                  <input
                    id="input-siee-version"
                    type="text"
                    placeholder="Ej. SIEE 2027 v2.0"
                    value={compliance.siee_version || ''}
                    onChange={(e) => setCompliance((prev) => ({ ...prev, siee_version: e.target.value }))}
                    style={{ width: '100%', padding: '0.35rem 0.5rem', border: '1px solid #CBD5E1', borderRadius: '6px' }}
                  />
                </div>
                <div>
                  <label htmlFor="input-approval-act" style={{ display: 'block', fontWeight: 600, color: '#475569', marginBottom: '0.2rem' }}>
                    Acto / Acuerdo de Consejo Directivo:
                  </label>
                  <input
                    id="input-approval-act"
                    type="text"
                    placeholder="Ej. Acuerdo CD N° 004 de 2026"
                    value={compliance.approval_act || ''}
                    onChange={(e) => setCompliance((prev) => ({ ...prev, approval_act: e.target.value }))}
                    style={{ width: '100%', padding: '0.35rem 0.5rem', border: '1px solid #CBD5E1', borderRadius: '6px' }}
                  />
                </div>
                <div>
                  <label htmlFor="input-calendar-source" style={{ display: 'block', fontWeight: 600, color: '#475569', marginBottom: '0.2rem' }}>
                    Resolución de Calendario Territorial:
                  </label>
                  <input
                    id="input-calendar-source"
                    type="text"
                    placeholder="Ej. Res. SED Antioquia 2026-098"
                    value={compliance.calendar_source || ''}
                    onChange={(e) => setCompliance((prev) => ({ ...prev, calendar_source: e.target.value }))}
                    style={{ width: '100%', padding: '0.35rem 0.5rem', border: '1px solid #CBD5E1', borderRadius: '6px' }}
                  />
                </div>
                <div>
                  <label htmlFor="input-reviewed-at" style={{ display: 'block', fontWeight: 600, color: '#475569', marginBottom: '0.2rem' }}>
                    Fecha de Revisión Institucional:
                  </label>
                  <input
                    id="input-reviewed-at"
                    type="date"
                    value={compliance.reviewed_at || ''}
                    onChange={(e) => setCompliance((prev) => ({ ...prev, reviewed_at: e.target.value }))}
                    style={{ width: '100%', padding: '0.35rem 0.5rem', border: '1px solid #CBD5E1', borderRadius: '6px' }}
                  />
                </div>
              </div>
            </div>

            {/* Final Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
              <Button variant="secondary" onClick={() => setCurrentStep(3)} id="btn-back-to-step-3" disabled={isSubmitting}>
                ← Regresar a Ajustes
              </Button>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <Button
                  variant="secondary"
                  onClick={() => handleProvision(false)}
                  disabled={isSubmitting || !isWeightValid}
                  id="btn-provision-only"
                >
                  {isSubmitting ? 'Guardando...' : 'Aprovisionar sin Activar'}
                </Button>
                <Button
                  variant="primary"
                  onClick={() => handleProvision(true)}
                  disabled={isSubmitting || !isWeightValid || !compliance.confirmed_by_rector}
                  id="btn-provision-and-activate"
                >
                  {isSubmitting ? 'Procesando...' : '✨ Aprovisionar y Activar Configuración'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}
