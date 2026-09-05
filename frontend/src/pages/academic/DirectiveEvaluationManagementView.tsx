/**
 * PEVN Frontend — Directive SIEE Evaluation & Period Management View (Phase 16D)
 *
 * Dedicated console for Academic Directives (Rector, Coordinador Académico):
 * - Direct consumption of certified Phase 16C backend APIs
 * - Period Lifecycle: Close/Seal periods (evaluations:close_period) with confirmation
 * - Period Reopening (evaluations:reopen_period) with mandatory audit justification
 * - SIEE Active Institutional Policy inspection
 * - Institutional classroom evaluation matrix inspection
 */

import React, { useCallback, useEffect, useState } from 'react'
import { academicApi } from '@/services/academic'
import { evaluationApi } from '@/services/evaluation'
import { useAuth } from '@/hooks/useAuth'
import type {
  AcademicPeriodResponse,
  AcademicYearResponse,
  GroupConsolidationMatrixResponse,
  GroupResponse,
  PeriodSheetResponse,
  SieePolicyResponse,
  StudentReportCardResponse,
  SubjectResponse,
} from '@/types'
import { GroupConsolidationMatrix } from '@/components/evaluation/GroupConsolidationMatrix'
import { OfficialReportCard } from '@/components/evaluation/OfficialReportCard'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

export const DirectiveEvaluationManagementView: React.FC = () => {
  const { hasPermission } = useAuth()
  const canClosePeriod = hasPermission('evaluations:close_period')
  const canReopenPeriod = hasPermission('evaluations:reopen_period')

  // -------------------------------------------------------------------------
  // State: Academic Years & SIEE Policy
  // -------------------------------------------------------------------------
  const [academicYears, setAcademicYears] = useState<AcademicYearResponse[]>([])
  const [selectedYearId, setSelectedYearId] = useState<string>('')
  const [periods, setPeriods] = useState<AcademicPeriodResponse[]>([])
  const [sieePolicy, setSieePolicy] = useState<SieePolicyResponse | null>(null)

  // -------------------------------------------------------------------------
  // State: Oversight Inspection
  // -------------------------------------------------------------------------
  const [groups, setGroups] = useState<GroupResponse[]>([])
  const [selectedGroupId, setSelectedGroupId] = useState<string>('')
  const [subjects, setSubjects] = useState<SubjectResponse[]>([])
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('')
  const [inspectPeriodId, setInspectPeriodId] = useState<string>('')
  const [inspectedSheet, setInspectedSheet] = useState<PeriodSheetResponse | null>(null)
  const [loadingSheet, setLoadingSheet] = useState(false)
  const [groupMatrix, setGroupMatrix] = useState<GroupConsolidationMatrixResponse | null>(null)
  const [loadingMatrix, setLoadingMatrix] = useState(false)
  const [selectedStudentCard, setSelectedStudentCard] = useState<StudentReportCardResponse | null>(null)
  const [loadingStudentCard, setLoadingStudentCard] = useState(false)
  const [studentCardModalOpen, setStudentCardModalOpen] = useState(false)

  // -------------------------------------------------------------------------
  // Modals State
  // -------------------------------------------------------------------------
  const [closeModalPeriod, setCloseModalPeriod] = useState<AcademicPeriodResponse | null>(null)
  const [unlockModalPeriod, setUnlockModalPeriod] = useState<AcademicPeriodResponse | null>(null)
  const [unlockReason, setUnlockReason] = useState<string>('')
  const [modalActionLoading, setModalActionLoading] = useState(false)

  // Feedback State
  const [loading, setLoading] = useState(true)
  const [statusMessage, setStatusMessage] = useState<{
    type: 'success' | 'error' | 'warning'
    text: string
  } | null>(null)

  // -------------------------------------------------------------------------
  // 1. Initial Load: Years & Policy
  // -------------------------------------------------------------------------
  const loadInitialData = useCallback(async () => {
    setLoading(true)
    setStatusMessage(null)
    try {
      const [yearsData, policyData, groupsData] = await Promise.all([
        academicApi.listAcademicYears(),
        evaluationApi.getActiveSieePolicy().catch(() => null),
        academicApi.listGroups(),
      ])

      setAcademicYears(yearsData.items)
      setSieePolicy(policyData)
      setGroups(groupsData.items)

      const activeYear = yearsData.items.find((y) => y.status === 'ACTIVE') || yearsData.items[0]
      if (activeYear) {
        setSelectedYearId(activeYear.id)
      }
      if (groupsData.items.length > 0) {
        setSelectedGroupId(groupsData.items[0].id)
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Error al cargar la información de años lectivos y política SIEE.'
      setStatusMessage({ type: 'error', text: msg })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadInitialData()
  }, [loadInitialData])

  // -------------------------------------------------------------------------
  // 2. Load Periods for Selected Year
  // -------------------------------------------------------------------------
  const loadPeriods = useCallback(async (yearId: string) => {
    if (!yearId) {
      setPeriods([])
      return
    }
    try {
      const data = await evaluationApi.listAcademicPeriods(yearId)
      setPeriods(data.items)
      if (data.items.length > 0 && !inspectPeriodId) {
        setInspectPeriodId(data.items[0].id)
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Error al consultar los períodos del año escolar.'
      setStatusMessage({ type: 'error', text: msg })
    }
  }, [inspectPeriodId])

  useEffect(() => {
    if (selectedYearId) {
      void loadPeriods(selectedYearId)
    }
  }, [selectedYearId, loadPeriods])

  // -------------------------------------------------------------------------
  // 3. Load Subjects for Selected Group
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!selectedGroupId) return
    const group = groups.find((g) => g.id === selectedGroupId)
    if (!group) return

    const loadSubjects = async () => {
      try {
        const data = await academicApi.listSubjects({ gradeId: group.grade_id })
        setSubjects(data.items)
        if (data.items.length > 0) {
          setSelectedSubjectId(data.items[0].id)
        }
      } catch {
        setSubjects([])
      }
    }
    void loadSubjects()
  }, [selectedGroupId, groups])

  // -------------------------------------------------------------------------
  // 4. Inspect Period Sheet (Institutional Directorial Scope)
  // -------------------------------------------------------------------------
  const handleInspectSheet = async () => {
    if (!inspectPeriodId || !selectedGroupId || !selectedSubjectId) return
    setLoadingSheet(true)
    setStatusMessage(null)
    try {
      const data = await evaluationApi.getPeriodSheet({
        periodId: inspectPeriodId,
        groupId: selectedGroupId,
        subjectId: selectedSubjectId,
      })
      setInspectedSheet(data)
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'No se pudo consultar la sábana de notas del grupo.'
      setStatusMessage({ type: 'error', text: msg })
      setInspectedSheet(null)
    } finally {
      setLoadingSheet(false)
    }
  }

  const handleInspectGroupMatrix = async () => {
    if (!selectedGroupId || !inspectPeriodId) return
    setLoadingMatrix(true)
    setInspectedSheet(null)
    try {
      const data = await evaluationApi.getGroupConsolidationMatrix(selectedGroupId, inspectPeriodId)
      setGroupMatrix(data)
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Error al consultar la sábana consolidada del grupo.'
      setStatusMessage({ type: 'error', text: msg })
      setGroupMatrix(null)
    } finally {
      setLoadingMatrix(false)
    }
  }

  const handleInspectStudentCard = async (studentId: string) => {
    if (!inspectPeriodId) return
    setLoadingStudentCard(true)
    setStudentCardModalOpen(true)
    try {
      const data = await evaluationApi.getStudentReportCard(studentId, inspectPeriodId)
      setSelectedStudentCard(data)
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Error al consultar el boletín oficial del estudiante.'
      alert(`Error: ${msg}`)
      setStudentCardModalOpen(false)
    } finally {
      setLoadingStudentCard(false)
    }
  }

  // -------------------------------------------------------------------------
  // 5. Period Close Action (evaluations:close_period)
  // -------------------------------------------------------------------------
  const handleConfirmClosePeriod = async () => {
    if (!closeModalPeriod) return
    setModalActionLoading(true)
    try {
      await evaluationApi.closePeriod(closeModalPeriod.id)
      setStatusMessage({
        type: 'success',
        text: `El período "${closeModalPeriod.name}" ha sido cerrado y sus calificaciones han sido selladas exitosamente.`,
      })
      setCloseModalPeriod(null)
      if (selectedYearId) void loadPeriods(selectedYearId)
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Ocurrió un error al intentar cerrar el período académico.'
      alert(`Error: ${msg}`)
    } finally {
      setModalActionLoading(false)
    }
  }

  // -------------------------------------------------------------------------
  // 6. Period Reopening Action (evaluations:reopen_period)
  // -------------------------------------------------------------------------
  const handleConfirmUnlockPeriod = async () => {
    if (!unlockModalPeriod) return

    if (!unlockReason.trim() || unlockReason.trim().length < 10) {
      alert('La justificación formal de reapertura debe contener al menos 10 caracteres.')
      return
    }

    setModalActionLoading(true)
    try {
      await evaluationApi.unlockPeriod(unlockModalPeriod.id, {
        reason: unlockReason.trim(),
      })
      setStatusMessage({
        type: 'success',
        text: `El período "${unlockModalPeriod.name}" ha sido reabierto con éxito para modificaciones.`,
      })
      setUnlockModalPeriod(null)
      setUnlockReason('')
      if (selectedYearId) void loadPeriods(selectedYearId)
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Ocurrió un error al intentar reabrir el período académico.'
      alert(`Error: ${msg}`)
    } finally {
      setModalActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ padding: '3rem 0', textAlign: 'center' }}>
        <LoadingSpinner />
        <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
          Cargando consola directiva de evaluación...
        </p>
      </div>
    )
  }

  return (
    <div>
      {/* Header Banner */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.5rem' }}>⚖️</span>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
            Gestión Institucional de Evaluación y Períodos Académicos
          </h2>
        </div>
        <p style={{ fontSize: '0.875rem', color: '#64748B', margin: '0.25rem 0 0 0' }}>
          Control de ciclo de vida de períodos (Cierre / Reapertura auditada), supervisión de sábanas de calificaciones y parámetros SIEE.
        </p>
      </div>

      {/* Status Message */}
      {statusMessage && (
        <div
          style={{
            backgroundColor: statusMessage.type === 'success' ? '#F0FDF4' : '#FEF2F2',
            border: `1px solid ${statusMessage.type === 'success' ? '#86EFAC' : '#FCA5A5'}`,
            borderRadius: '8px',
            padding: '0.875rem 1.25rem',
            marginBottom: '1.5rem',
            color: statusMessage.type === 'success' ? '#166534' : '#991B1B',
            fontSize: '0.875rem',
            fontWeight: 500,
          }}
        >
          {statusMessage.text}
        </div>
      )}

      {/* Academic Year Selector */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          padding: '1.25rem',
          border: '1px solid #E2E8F0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          marginBottom: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <label
            htmlFor="directive-year-select"
            style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
          >
            Año Lectivo Escolar:
          </label>
          <select
            id="directive-year-select"
            value={selectedYearId}
            onChange={(e) => setSelectedYearId(e.target.value)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              backgroundColor: '#FFFFFF',
              fontSize: '0.875rem',
              fontWeight: 600,
              color: '#0F172A',
              minWidth: '220px',
            }}
          >
            {academicYears.map((y) => (
              <option key={y.id} value={y.id}>
                {y.name} ({y.year}) — {y.status}
              </option>
            ))}
          </select>
        </div>

        {sieePolicy && (
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', color: '#64748B' }}>Política SIEE Activa</div>
            <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A' }}>
              {sieePolicy.name} (v{sieePolicy.version})
            </div>
            <div style={{ fontSize: '0.75rem', color: '#166534', fontWeight: 600 }}>
              Escala: {sieePolicy.scale_min.toFixed(1)}–{sieePolicy.scale_max.toFixed(1)} • Min Aprobatorio: {sieePolicy.min_passing_score.toFixed(1)}
            </div>
          </div>
        )}
      </div>

      {/* 1. Periods Lifecycle Console */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          overflow: 'hidden',
          marginBottom: '2rem',
        }}
      >
        <div
          style={{
            padding: '1rem 1.25rem',
            borderBottom: '1px solid #E2E8F0',
            backgroundColor: '#FAFAFA',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#0F172A', margin: 0 }}>
            Períodos Académicos del Año Lectivo
          </h3>
          <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>
            {periods.length} período(s) configurado(s)
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Período</th>
                <th style={{ padding: '0.75rem 1rem' }}>Nombre</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Peso %</th>
                <th style={{ padding: '0.75rem 1rem' }}>Rango de Fechas</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Estado</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones Directivas</th>
              </tr>
            </thead>
            <tbody>
              {periods.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '2rem', textAlign: 'center', color: '#64748B' }}>
                    No hay períodos académicos registrados para este año escolar.
                  </td>
                </tr>
              ) : (
                periods.map((period) => (
                  <tr key={period.id} style={{ borderBottom: '1px solid #E2E8F0' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                      Período {period.period_number}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: '#334155' }}>
                      {period.name}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'center', fontWeight: 700, color: '#0F172A' }}>
                      {period.weight_percentage}%
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: '#64748B' }}>
                      {period.start_date} a {period.end_date}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '0.25rem 0.6rem',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          backgroundColor: period.is_closed ? '#FEE2E2' : '#DCFCE7',
                          color: period.is_closed ? '#991B1B' : '#166534',
                        }}
                      >
                        {period.is_closed ? '🔒 CERRADO / SELLADO' : '🟢 ABIERTO'}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                      {period.is_closed ? (
                        canReopenPeriod ? (
                          <Button
                            variant="secondary"
                            onClick={() => {
                              setUnlockModalPeriod(period)
                              setUnlockReason('')
                            }}
                          >
                            🔓 Reabrir Período
                          </Button>
                        ) : (
                          <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>Sellado</span>
                        )
                      ) : (
                        canClosePeriod ? (
                          <Button
                            variant="danger"
                            onClick={() => setCloseModalPeriod(period)}
                          >
                            🔒 Cerrar y Sellar
                          </Button>
                        ) : (
                          <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>En curso</span>
                        )
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. SIEE Institutional Parameters Card */}
      {sieePolicy && (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            border: '1px solid #E2E8F0',
            padding: '1.25rem',
            marginBottom: '2rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#0F172A', margin: 0 }}>
              Reglamento de Evaluación Institucional SIEE ({sieePolicy.name})
            </h3>
            <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Versión {sieePolicy.version}</span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '1rem',
              fontSize: '0.8125rem',
            }}
          >
            <div style={{ padding: '0.75rem', backgroundColor: '#F8FAFC', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
              <div style={{ color: '#64748B', fontSize: '0.75rem' }}>Escala y Decimales</div>
              <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: '#0F172A', marginTop: '0.25rem' }}>
                {sieePolicy.scale_min.toFixed(1)} – {sieePolicy.scale_max.toFixed(1)} ({sieePolicy.scale_decimals} decimales)
              </div>
              <div style={{ color: '#64748B', fontSize: '0.75rem', marginTop: '0.25rem' }}>
                Redondeo: {sieePolicy.rounding_mode}
              </div>
            </div>

            <div style={{ padding: '0.75rem', backgroundColor: '#F8FAFC', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
              <div style={{ color: '#64748B', fontSize: '0.75rem' }}>Aprobación y Nivelaciones</div>
              <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: '#0F172A', marginTop: '0.25rem' }}>
                Mínimo aprobatorio: {sieePolicy.min_passing_score.toFixed(1)}
              </div>
              <div style={{ color: '#64748B', fontSize: '0.75rem', marginTop: '0.25rem' }}>
                Tope máximo nivelación: {sieePolicy.recovery_grade_cap.toFixed(1)}
              </div>
            </div>

            <div style={{ padding: '0.75rem', backgroundColor: '#F8FAFC', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
              <div style={{ color: '#64748B', fontSize: '0.75rem' }}>Desempeños SIEE</div>
              <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', lineHeight: '1.4' }}>
                <div>🔴 <strong>Bajo:</strong> {sieePolicy.scale_min.toFixed(1)} - {sieePolicy.threshold_bajo_max.toFixed(1)}</div>
                <div>🟡 <strong>Básico:</strong> {(sieePolicy.threshold_bajo_max + 0.1).toFixed(1)} - {sieePolicy.threshold_basico_max.toFixed(1)}</div>
                <div>🟢 <strong>Alto:</strong> {(sieePolicy.threshold_basico_max + 0.1).toFixed(1)} - {sieePolicy.threshold_alto_max.toFixed(1)}</div>
                <div>🔵 <strong>Superior:</strong> {(sieePolicy.threshold_alto_max + 0.1).toFixed(1)} - {sieePolicy.threshold_superior_max.toFixed(1)}</div>
              </div>
            </div>

            <div style={{ padding: '0.75rem', backgroundColor: '#F8FAFC', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
              <div style={{ color: '#64748B', fontSize: '0.75rem' }}>Promoción de Grado</div>
              <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', lineHeight: '1.4' }}>
                <div>Máx. Asignaturas no superadas: <strong>{sieePolicy.max_failed_subjects_for_promotion}</strong></div>
                <div>Asistencia mínima requerida: <strong>{sieePolicy.min_attendance_percentage}%</strong></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3. Institutional Oversight: Group Inspection */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
          padding: '1.25rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#0F172A', margin: '0 0 1rem 0' }}>
          Supervisión de Sábanas de Calificaciones por Grupo
        </h3>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            alignItems: 'end',
            marginBottom: '1.25rem',
          }}
        >
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Grupo:
            </label>
            <select
              value={selectedGroupId}
              onChange={(e) => setSelectedGroupId(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
            >
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name} (Cupos: {g.capacity_limit})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Asignatura:
            </label>
            <select
              value={selectedSubjectId}
              onChange={(e) => setSelectedSubjectId(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
            >
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.weekly_hours}h/sem)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Período:
            </label>
            <select
              value={inspectPeriodId}
              onChange={(e) => setInspectPeriodId(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
            >
              {periods.map((p) => (
                <option key={p.id} value={p.id}>
                  Período {p.period_number} ({p.is_closed ? 'Cerrado' : 'Abierto'})
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <Button
              variant="secondary"
              onClick={handleInspectSheet}
              disabled={loadingSheet || !inspectPeriodId || !selectedGroupId || !selectedSubjectId}
            >
              {loadingSheet ? 'Consultando...' : 'Consultar Sábana'}
            </Button>
            <Button
              variant="primary"
              onClick={handleInspectGroupMatrix}
              disabled={loadingMatrix || !inspectPeriodId || !selectedGroupId}
            >
              {loadingMatrix ? 'Generando Sábana...' : '📊 Sábana Consolidada Grupo'}
            </Button>
          </div>
        </div>

        {/* Group Consolidation Matrix Display (Phase 16E) */}
        {groupMatrix && (
          <div style={{ marginTop: '1.5rem', borderTop: '2px solid #CBD5E1', paddingTop: '1.5rem' }}>
            <GroupConsolidationMatrix matrix={groupMatrix} />
          </div>
        )}

        {/* Inspected Single-Subject Sheet Table */}
        {inspectedSheet && (
          <div style={{ marginTop: '1rem', borderTop: '1px solid #E2E8F0', paddingTop: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A' }}>
                Estudiantes ({inspectedSheet.students.length}) • {inspectedSheet.group.name} • {inspectedSheet.subject.name}
              </div>
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '0.2rem 0.5rem',
                  borderRadius: '4px',
                  backgroundColor: inspectedSheet.period.is_closed ? '#FEE2E2' : '#DCFCE7',
                  color: inspectedSheet.period.is_closed ? '#991B1B' : '#166534',
                }}
              >
                {inspectedSheet.period.is_closed ? '🔒 CERRADO' : '🟢 ABIERTO'}
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
                <thead>
                  <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0', color: '#475569' }}>
                    <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left' }}>Estudiante</th>
                    <th style={{ padding: '0.5rem 0.75rem', textAlign: 'center' }}>Calculada</th>
                    <th style={{ padding: '0.5rem 0.75rem', textAlign: 'center' }}>Definitiva</th>
                    <th style={{ padding: '0.5rem 0.75rem', textAlign: 'center' }}>Desempeño</th>
                    <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left' }}>Ajuste / Observación</th>
                    <th style={{ padding: '0.5rem 0.75rem', textAlign: 'center' }}>Fallas</th>
                    <th style={{ padding: '0.5rem 0.75rem', textAlign: 'center' }}>Boletín</th>
                  </tr>
                </thead>
                <tbody>
                  {inspectedSheet.students.map((st) => (
                    <tr key={st.student_id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                      <td style={{ padding: '0.5rem 0.75rem', fontWeight: 600, color: '#0F172A' }}>
                        {st.last_name}, {st.first_name}
                      </td>
                      <td style={{ padding: '0.5rem 0.75rem', textAlign: 'center', color: '#64748B' }}>
                        {st.calculated_score.toFixed(2)}
                      </td>
                      <td
                        style={{
                          padding: '0.5rem 0.75rem',
                          textAlign: 'center',
                          fontWeight: 700,
                          color: st.final_score < (sieePolicy?.min_passing_score ?? 3.0) ? '#DC2626' : '#0F172A',
                        }}
                      >
                        {st.final_score.toFixed(2)}
                      </td>
                      <td style={{ padding: '0.5rem 0.75rem', textAlign: 'center' }}>
                        <span
                          style={{
                            padding: '0.15rem 0.4rem',
                            borderRadius: '4px',
                            fontSize: '0.6875rem',
                            fontWeight: 700,
                            backgroundColor:
                              st.performance_level === 'SUPERIOR'
                                ? '#EFF6FF'
                                : st.performance_level === 'ALTO'
                                ? '#F0FDF4'
                                : st.performance_level === 'BASICO'
                                ? '#FEFCE8'
                                : '#FEF2F2',
                            color:
                              st.performance_level === 'SUPERIOR'
                                ? '#1E40AF'
                                : st.performance_level === 'ALTO'
                                ? '#166534'
                                : st.performance_level === 'BASICO'
                                ? '#854D0E'
                                : '#991B1B',
                          }}
                        >
                          {st.performance_level}
                        </span>
                      </td>
                      <td style={{ padding: '0.5rem 0.75rem', color: '#475569', fontSize: '0.75rem' }}>
                        {st.adjustment_reason ? `Ajuste: ${st.adjustment_reason}` : st.observations || '—'}
                      </td>
                      <td style={{ padding: '0.5rem 0.75rem', textAlign: 'center', color: '#64748B' }}>
                        {st.total_absences}
                      </td>
                      <td style={{ padding: '0.5rem 0.75rem', textAlign: 'center' }}>
                        <button
                          type="button"
                          onClick={() => handleInspectStudentCard(st.student_id)}
                          style={{
                            backgroundColor: '#EFF6FF',
                            border: '1px solid #BFDBFE',
                            color: '#1D4ED8',
                            borderRadius: '6px',
                            padding: '0.2rem 0.5rem',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          👁️ Boletín
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Student Report Card Inspection Modal (Phase 16E) */}
      {studentCardModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.65)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1100,
            padding: '1.5rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '16px',
              maxWidth: '1000px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
              padding: '1.5rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: '#0F172A' }}>
                Vista Previa de Boletín Oficial del Estudiante
              </h3>
              <button
                type="button"
                onClick={() => {
                  setStudentCardModalOpen(false)
                  setSelectedStudentCard(null)
                }}
                style={{
                  backgroundColor: '#F1F5F9',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0.4rem 0.75rem',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#475569',
                  cursor: 'pointer',
                }}
              >
                ✕ Cerrar
              </button>
            </div>

            {loadingStudentCard ? (
              <div style={{ padding: '3rem 0', textAlign: 'center' }}>
                <LoadingSpinner size="lg" />
                <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
                  Cargando boletín oficial...
                </p>
              </div>
            ) : selectedStudentCard ? (
              <OfficialReportCard reportCard={selectedStudentCard} />
            ) : (
              <p style={{ color: '#64748B', textAlign: 'center' }}>No se pudo cargar el boletín.</p>
            )}
          </div>
        </div>
      )}

      {/* Close Period Confirmation Modal */}
      {closeModalPeriod && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '16px',
              maxWidth: '480px',
              width: '100%',
              padding: '1.5rem',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <span style={{ fontSize: '1.75rem' }}>⚠️</span>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 800, color: '#991B1B', margin: 0 }}>
                Confirmación de Cierre y Sellado
              </h3>
            </div>

            <p style={{ fontSize: '0.875rem', color: '#334155', lineHeight: 1.5, margin: '0 0 1rem 0' }}>
              ¿Está seguro de que desea cerrar y sellar el <strong>Período {closeModalPeriod.period_number}: {closeModalPeriod.name}</strong>?
            </p>

            <div
              style={{
                backgroundColor: '#FEF2F2',
                border: '1px solid #FCA5A5',
                borderRadius: '8px',
                padding: '0.875rem',
                fontSize: '0.8125rem',
                color: '#991B1B',
                marginBottom: '1.25rem',
              }}
            >
              <strong>Consecuencia institucional:</strong>
              <br />
              Una vez sellado, ningún docente podrá asentar o modificar notas para este período. Solo Rectoría o Coordinación podrán reabrirlo con justificación formal en auditoría.
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button variant="secondary" onClick={() => setCloseModalPeriod(null)}>
                Cancelar
              </Button>
              <Button variant="danger" onClick={handleConfirmClosePeriod} disabled={modalActionLoading}>
                {modalActionLoading ? 'Sellando...' : 'Sí, Cerrar y Sellar'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Reopen Period Justification Modal */}
      {unlockModalPeriod && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '16px',
              maxWidth: '520px',
              width: '100%',
              padding: '1.5rem',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <span style={{ fontSize: '1.75rem' }}>🔓</span>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
                Reapertura de Período Académico
              </h3>
            </div>

            <p style={{ fontSize: '0.875rem', color: '#334155', lineHeight: 1.5, margin: '0 0 0.75rem 0' }}>
              Reapertura de: <strong>Período {unlockModalPeriod.period_number}: {unlockModalPeriod.name}</strong>
            </p>

            <div style={{ marginBottom: '1.25rem' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  color: '#334155',
                  marginBottom: '0.375rem',
                }}
              >
                Justificación Pedagógica / Administrativa Formal (Obligatoria, mín. 10 caracteres) *
              </label>
              <textarea
                rows={3}
                placeholder="Indique el motivo institucional, acta o solicitud por la cual se reabre el período..."
                value={unlockReason}
                onChange={(e) => setUnlockReason(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '8px',
                  border: '1px solid #CBD5E1',
                  fontSize: '0.875rem',
                }}
              />
              <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
                Este evento quedará asentado con su firma digital y dirección IP en la bitácora de auditoría institucional.
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button variant="secondary" onClick={() => setUnlockModalPeriod(null)}>
                Cancelar
              </Button>
              <Button
                variant="primary"
                onClick={handleConfirmUnlockPeriod}
                disabled={modalActionLoading || unlockReason.trim().length < 10}
              >
                {modalActionLoading ? 'Reabriendo...' : 'Reabrir Período'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DirectiveEvaluationManagementView
