/**
 * PEVN Frontend — Teacher SIEE Period Evaluation Sheet View (Phase 16D)
 *
 * Dedicated teacher workspace to evaluate students on consolidated academic terms:
 * - Direct consumption of certified Phase 16C backend APIs
 * - Strictly data-driven SIEE rules (scale, thresholds, recovery caps from backend)
 * - Auto-calculated scores vs. Final grades with mandatory adjustment reason (DECISION-16-03)
 * - Recovery/remediation grade recording displaying institutional recovery cap
 * - Absolute immutability enforcement when period is closed/sealed
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { evaluationApi } from '@/services/evaluation'
import { useAuth } from '@/hooks/useAuth'
import type {
  AcademicPeriodResponse,
  GradeItemRequest,
  PeriodSheetResponse,
  SieePerformanceLevel,
  SieePolicyResponse,
  StudentGradeRow,
} from '@/types'
import type { TeacherAssignmentItemResponse } from '@/types/teacher'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

interface Props {
  assignments: TeacherAssignmentItemResponse[]
  initialSelectedAssignmentId?: string | null
}

interface LocalStudentGradeState {
  calculatedScore: number
  finalScore: string
  adjustmentReason: string
  totalAbsences: string
  unexcusedAbsences: string
  observations: string
  isDirty: boolean
}

export const TeacherSieeEvaluationView: React.FC<Props> = ({
  assignments,
  initialSelectedAssignmentId,
}) => {
  const { hasPermission } = useAuth()
  const canGrade = hasPermission('evaluations:grade')
  const canRecover = hasPermission('evaluations:recovery')

  // -------------------------------------------------------------------------
  // Selectors State
  // -------------------------------------------------------------------------
  const activeAssignments = useMemo(
    () => assignments.filter((a) => a.is_active),
    [assignments]
  )

  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string>(
    initialSelectedAssignmentId || (activeAssignments[0]?.id ?? '')
  )

  const selectedAssignment = useMemo(
    () => activeAssignments.find((a) => a.id === selectedAssignmentId) || activeAssignments[0],
    [activeAssignments, selectedAssignmentId]
  )

  const [periods, setPeriods] = useState<AcademicPeriodResponse[]>([])
  const [selectedPeriodId, setSelectedPeriodId] = useState<string>('')
  const [sieePolicy, setSieePolicy] = useState<SieePolicyResponse | null>(null)

  // -------------------------------------------------------------------------
  // Sheet Data & Form State
  // -------------------------------------------------------------------------
  const [sheet, setSheet] = useState<PeriodSheetResponse | null>(null)
  const [gradesState, setGradesState] = useState<Record<string, LocalStudentGradeState>>({})
  const [showPolicyInfo, setShowPolicyInfo] = useState(false)

  // Recovery Modal State
  const [recoveryModalStudent, setRecoveryModalStudent] = useState<{
    student: StudentGradeRow
    gradeId?: string
  } | null>(null)
  const [recoveryScoreInput, setRecoveryScoreInput] = useState<string>('')
  const [recoveryDateInput, setRecoveryDateInput] = useState<string>(
    new Date().toISOString().split('T')[0]
  )
  const [recoveryActInput, setRecoveryActInput] = useState<string>('')
  const [recoveryObsInput, setRecoveryObsInput] = useState<string>('')
  const [savingRecovery, setSavingRecovery] = useState(false)

  // UI Feedback State
  const [loadingPeriods, setLoadingPeriods] = useState(false)
  const [loadingSheet, setLoadingSheet] = useState(false)
  const [saving, setSaving] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{
    type: 'success' | 'error' | 'warning'
    text: string
  } | null>(null)

  // -------------------------------------------------------------------------
  // 1. Load Academic Periods & Active SIEE Policy
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!selectedAssignment?.academic_year_id) return

    let isMounted = true
    const loadPeriodsAndPolicy = async () => {
      setLoadingPeriods(true)
      setStatusMessage(null)
      try {
        const [periodsData, policyData] = await Promise.all([
          evaluationApi.listAcademicPeriods(selectedAssignment.academic_year_id),
          evaluationApi.getActiveSieePolicy(selectedAssignment.academic_year_id).catch(() => null),
        ])

        if (isMounted) {
          setPeriods(periodsData.items)
          setSieePolicy(policyData)
          if (periodsData.items.length > 0 && !selectedPeriodId) {
            // Pick first open period or fallback to first period
            const firstOpen = periodsData.items.find((p) => !p.is_closed) || periodsData.items[0]
            setSelectedPeriodId(firstOpen.id)
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg =
            err instanceof Error
              ? err.message
              : 'Error al consultar los períodos académicos de la institución.'
          setStatusMessage({ type: 'error', text: msg })
        }
      } finally {
        if (isMounted) setLoadingPeriods(false)
      }
    }

    void loadPeriodsAndPolicy()

    return () => {
      isMounted = false
    }
  }, [selectedAssignment?.academic_year_id])

  // -------------------------------------------------------------------------
  // 2. Load Period Sheet Matrix
  // -------------------------------------------------------------------------
  const loadPeriodSheet = useCallback(
    async (periodId: string, groupId: string, subjectId: string) => {
      if (!periodId || !groupId || !subjectId) {
        setSheet(null)
        setGradesState({})
        return
      }

      setLoadingSheet(true)
      setStatusMessage(null)

      try {
        const sheetData = await evaluationApi.getPeriodSheet({
          periodId,
          groupId,
          subjectId,
        })
        setSheet(sheetData)

        // Initialize local editable state
        const stateMap: Record<string, LocalStudentGradeState> = {}
        sheetData.students.forEach((s) => {
          stateMap[s.student_id] = {
            calculatedScore: s.calculated_score,
            finalScore: s.final_score !== null && s.final_score !== undefined ? String(s.final_score) : '',
            adjustmentReason: s.adjustment_reason || '',
            totalAbsences: String(s.total_absences ?? 0),
            unexcusedAbsences: String(s.unexcused_absences ?? 0),
            observations: s.observations || '',
            isDirty: false,
          }
        })
        setGradesState(stateMap)
      } catch (err: unknown) {
        const msg =
          err instanceof Error
            ? err.message
            : 'No fue posible cargar la sábana de notas del período seleccionado.'
        setStatusMessage({ type: 'error', text: msg })
        setSheet(null)
      } finally {
        setLoadingSheet(false)
      }
    },
    []
  )

  useEffect(() => {
    if (selectedPeriodId && selectedAssignment) {
      void loadPeriodSheet(
        selectedPeriodId,
        selectedAssignment.group_id,
        selectedAssignment.subject_id
      )
    }
  }, [selectedPeriodId, selectedAssignment, loadPeriodSheet])

  // -------------------------------------------------------------------------
  // 3. Computed Helpers
  // -------------------------------------------------------------------------
  const selectedPeriod = useMemo(
    () => periods.find((p) => p.id === selectedPeriodId) || sheet?.period,
    [periods, selectedPeriodId, sheet?.period]
  )

  const isPeriodClosed = Boolean(selectedPeriod?.is_closed)
  const isSheetLocked = Boolean(isPeriodClosed || !canGrade)

  const minScale = sheet?.policy?.scale_min ?? sieePolicy?.scale_min ?? 0.0
  const maxScale = sheet?.policy?.scale_max ?? sieePolicy?.scale_max ?? 5.0
  const passingScore = sheet?.policy?.min_passing_score ?? sieePolicy?.min_passing_score ?? 3.0
  const recoveryCap = sheet?.policy?.recovery_grade_cap ?? sieePolicy?.recovery_grade_cap ?? 3.0

  const dirtyCount = useMemo(() => {
    return Object.values(gradesState).filter((st) => st.isDirty).length
  }, [gradesState])

  // -------------------------------------------------------------------------
  // 4. Form Handlers
  // -------------------------------------------------------------------------
  const handleFinalScoreChange = (studentId: string, val: string) => {
    setGradesState((prev) => {
      const current = prev[studentId]
      if (!current) return prev
      return {
        ...prev,
        [studentId]: {
          ...current,
          finalScore: val,
          isDirty: true,
        },
      }
    })
  }

  const handleAdjustmentReasonChange = (studentId: string, val: string) => {
    setGradesState((prev) => {
      const current = prev[studentId]
      if (!current) return prev
      return {
        ...prev,
        [studentId]: {
          ...current,
          adjustmentReason: val,
          isDirty: true,
        },
      }
    })
  }

  const handleAbsencesChange = (
    studentId: string,
    field: 'totalAbsences' | 'unexcusedAbsences',
    val: string
  ) => {
    setGradesState((prev) => {
      const current = prev[studentId]
      if (!current) return prev
      return {
        ...prev,
        [studentId]: {
          ...current,
          [field]: val,
          isDirty: true,
        },
      }
    })
  }

  const handleObservationsChange = (studentId: string, val: string) => {
    setGradesState((prev) => {
      const current = prev[studentId]
      if (!current) return prev
      return {
        ...prev,
        [studentId]: {
          ...current,
          observations: val,
          isDirty: true,
        },
      }
    })
  }

  // Helper to determine performance badge color
  const getPerformanceBadge = (level: SieePerformanceLevel) => {
    switch (level) {
      case 'SUPERIOR':
        return { bg: '#EFF6FF', color: '#1E40AF', border: '#93C5FD', label: 'SUPERIOR' }
      case 'ALTO':
        return { bg: '#F0FDF4', color: '#166534', border: '#86EFAC', label: 'ALTO' }
      case 'BASICO':
        return { bg: '#FEFCE8', color: '#854D0E', border: '#FDE047', label: 'BÁSICO' }
      case 'BAJO':
        return { bg: '#FEF2F2', color: '#991B1B', border: '#FCA5A5', label: 'BAJO' }
      default:
        return { bg: '#F1F5F9', color: '#475569', border: '#CBD5E1', label: level }
    }
  }

  // -------------------------------------------------------------------------
  // 5. Batch Save Grades
  // -------------------------------------------------------------------------
  const handleSaveGrades = async () => {
    if (!sheet || !selectedAssignment || !selectedPeriodId) return
    setStatusMessage(null)

    // Validation pass
    const itemsToSave: GradeItemRequest[] = []

    for (const student of sheet.students) {
      const state = gradesState[student.student_id]
      if (!state) continue

      const scoreNum = parseFloat(state.finalScore)
      if (isNaN(scoreNum)) {
        setStatusMessage({
          type: 'error',
          text: `La nota definitiva de ${student.first_name} ${student.last_name} no es un número válido.`,
        })
        return
      }

      if (scoreNum < minScale || scoreNum > maxScale) {
        setStatusMessage({
          type: 'error',
          text: `La nota de ${student.first_name} ${student.last_name} (${scoreNum}) debe estar entre ${minScale.toFixed(2)} y ${maxScale.toFixed(2)}.`,
        })
        return
      }

      // DECISION-16-03: Mandatory adjustment reason if final differs from calculated
      const isAdjusted = Math.abs(scoreNum - state.calculatedScore) > 0.001
      if (isAdjusted && (!state.adjustmentReason || state.adjustmentReason.trim().length === 0)) {
        setStatusMessage({
          type: 'error',
          text: `Debe registrar un motivo pedagógico de ajuste para ${student.first_name} ${student.last_name}, ya que la nota final (${scoreNum.toFixed(2)}) difiere de la calculada (${state.calculatedScore.toFixed(2)}).`,
        })
        return
      }

      const totalAbs = parseInt(state.totalAbsences, 10) || 0
      const unexcusedAbs = parseInt(state.unexcusedAbsences, 10) || 0

      if (totalAbs < 0 || unexcusedAbs < 0) {
        setStatusMessage({
          type: 'error',
          text: `Las inasistencias de ${student.first_name} ${student.last_name} no pueden ser valores negativos.`,
        })
        return
      }

      if (unexcusedAbs > totalAbs) {
        setStatusMessage({
          type: 'error',
          text: `Las fallas injustificadas no pueden ser mayores que el total de inasistencias (${student.first_name} ${student.last_name}).`,
        })
        return
      }

      itemsToSave.push({
        student_id: student.student_id,
        enrollment_id: student.enrollment_id,
        calculated_score: state.calculatedScore,
        final_score: scoreNum,
        adjustment_reason: isAdjusted ? state.adjustmentReason.trim() : null,
        observations: state.observations.trim() || null,
        total_absences: totalAbs,
        unexcused_absences: unexcusedAbs,
      })
    }

    setSaving(true)
    try {
      await evaluationApi.savePeriodGrades({
        period_id: selectedPeriodId,
        group_id: selectedAssignment.group_id,
        subject_id: selectedAssignment.subject_id,
        items: itemsToSave,
      })

      setStatusMessage({
        type: 'success',
        text: '¡Calificaciones consolidadas del período guardadas exitosamente!',
      })

      // Reload fresh matrix from backend
      await loadPeriodSheet(
        selectedPeriodId,
        selectedAssignment.group_id,
        selectedAssignment.subject_id
      )
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Ocurrió un error al guardar las calificaciones del período.'
      setStatusMessage({ type: 'error', text: msg })
    } finally {
      setSaving(false)
    }
  }

  // -------------------------------------------------------------------------
  // 6. Recovery Registration
  // -------------------------------------------------------------------------
  const handleOpenRecoveryModal = (student: StudentGradeRow) => {
    setRecoveryModalStudent({ student })
    setRecoveryScoreInput('')
    setRecoveryDateInput(new Date().toISOString().split('T')[0])
    setRecoveryActInput('')
    setRecoveryObsInput('')
  }

  const handleSaveRecovery = async () => {
    if (!recoveryModalStudent || !sheet || !selectedPeriodId) return

    const parsedScore = parseFloat(recoveryScoreInput)
    if (isNaN(parsedScore) || parsedScore < minScale || parsedScore > maxScale) {
      alert(`La nota de nivelación debe ser un número entre ${minScale} y ${maxScale}.`)
      return
    }

    if (!recoveryDateInput) {
      alert('La fecha del examen o acta de nivelación es obligatoria.')
      return
    }

    setSavingRecovery(true)
    try {
      // Find grade id: from student row or fallback
      // Student has student_id; we call recordRecoveryGrade
      const gradeId =
        recoveryModalStudent.student.recoveries[0]?.id || recoveryModalStudent.student.enrollment_id

      await evaluationApi.recordRecoveryGrade(gradeId, {
        recovery_score: parsedScore,
        recovery_date: recoveryDateInput,
        act_number: recoveryActInput.trim() || null,
        observations: recoveryObsInput.trim() || null,
      })

      alert('¡Nivelación registrada exitosamente!')
      setRecoveryModalStudent(null)

      // Reload fresh matrix
      await loadPeriodSheet(
        selectedPeriodId,
        selectedAssignment.group_id,
        selectedAssignment.subject_id
      )
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'No fue posible registrar la nota de recuperación.'
      alert(`Error: ${msg}`)
    } finally {
      setSavingRecovery(false)
    }
  }

  return (
    <div>
      {/* Header Banner */}
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
        <div>
          <h2
            style={{
              fontSize: '1.25rem',
              fontWeight: 800,
              color: '#0F172A',
              margin: '0 0 0.25rem 0',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <span>📊</span>
            <span>Evaluación Periódica SIEE y Consolidación</span>
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
            Sábana de notas de período, cálculo ponderado de actividades, ajustes justificados y nivelaciones.
          </p>
        </div>

        {/* SIEE Policy Toggle */}
        {sieePolicy && (
          <button
            onClick={() => setShowPolicyInfo(!showPolicyInfo)}
            style={{
              backgroundColor: showPolicyInfo ? '#1E3A8A' : '#F1F5F9',
              color: showPolicyInfo ? '#FFFFFF' : '#1E3A8A',
              border: '1px solid #CBD5E1',
              borderRadius: '8px',
              padding: '0.5rem 0.875rem',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.375rem',
              transition: 'all 150ms ease-in-out',
            }}
          >
            <span>📜</span>
            <span>{showPolicyInfo ? 'Ocultar Parámetros SIEE' : 'Ver Parámetros SIEE'}</span>
          </button>
        )}
      </div>

      {/* SIEE Policy Details Drawer */}
      {showPolicyInfo && sieePolicy && (
        <div
          style={{
            backgroundColor: '#F8FAFC',
            border: '1px solid #E2E8F0',
            borderRadius: '12px',
            padding: '1.25rem',
            marginBottom: '1.5rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#1E293B', margin: 0 }}>
              Reglas Institucionales del SIEE ({sieePolicy.name} • Versión {sieePolicy.version})
            </h3>
            <span
              style={{
                fontSize: '0.75rem',
                backgroundColor: '#DCFCE7',
                color: '#15803D',
                fontWeight: 700,
                padding: '0.2rem 0.6rem',
                borderRadius: '9999px',
              }}
            >
              POLÍTICA VIGENTE
            </span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
              fontSize: '0.8125rem',
              color: '#334155',
            }}
          >
            <div style={{ backgroundColor: '#FFFFFF', padding: '0.75rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
              <div style={{ color: '#64748B', fontSize: '0.75rem' }}>Escala Numérica</div>
              <div style={{ fontWeight: 700, fontSize: '1rem', color: '#0F172A' }}>
                {sieePolicy.scale_min.toFixed(1)} – {sieePolicy.scale_max.toFixed(1)}
              </div>
              <div style={{ color: '#64748B', fontSize: '0.75rem', marginTop: '0.25rem' }}>
                Aprobación mínima: <strong>{sieePolicy.min_passing_score.toFixed(1)}</strong>
              </div>
            </div>

            <div style={{ backgroundColor: '#FFFFFF', padding: '0.75rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
              <div style={{ color: '#64748B', fontSize: '0.75rem' }}>Tope de Nivelación</div>
              <div style={{ fontWeight: 700, fontSize: '1rem', color: '#0F172A' }}>
                {sieePolicy.recovery_grade_cap.toFixed(1)} (Cap SIEE)
              </div>
              <div style={{ color: '#64748B', fontSize: '0.75rem', marginTop: '0.25rem' }}>
                Nivelaciones permitidas: {sieePolicy.allow_remedial_exams ? 'Sí' : 'No'}
              </div>
            </div>

            <div style={{ backgroundColor: '#FFFFFF', padding: '0.75rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
              <div style={{ color: '#64748B', fontSize: '0.75rem' }}>Niveles de Desempeño</div>
              <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', lineHeight: '1.4' }}>
                <div>🔴 <strong>Bajo:</strong> {sieePolicy.scale_min.toFixed(1)} - {sieePolicy.threshold_bajo_max.toFixed(1)}</div>
                <div>🟡 <strong>Básico:</strong> {(sieePolicy.threshold_bajo_max + 0.1).toFixed(1)} - {sieePolicy.threshold_basico_max.toFixed(1)}</div>
                <div>🟢 <strong>Alto:</strong> {(sieePolicy.threshold_basico_max + 0.1).toFixed(1)} - {sieePolicy.threshold_alto_max.toFixed(1)}</div>
                <div>🔵 <strong>Superior:</strong> {(sieePolicy.threshold_alto_max + 0.1).toFixed(1)} - {sieePolicy.threshold_superior_max.toFixed(1)}</div>
              </div>
            </div>

            <div style={{ backgroundColor: '#FFFFFF', padding: '0.75rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
              <div style={{ color: '#64748B', fontSize: '0.75rem' }}>Criterios de Promoción</div>
              <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', lineHeight: '1.4' }}>
                <div>Máx. Asignaturas Perdidas: <strong>{sieePolicy.max_failed_subjects_for_promotion}</strong></div>
                <div>Asistencia Mínima: <strong>{sieePolicy.min_attendance_percentage}%</strong></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Selectors Bar */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          padding: '1.25rem',
          border: '1px solid #E2E8F0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          marginBottom: '1.5rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
          alignItems: 'end',
        }}
      >
        {/* Assignment Selector */}
        <div>
          <label
            htmlFor="siee-assignment-select"
            style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.375rem' }}
          >
            Grupo y Asignatura Asignada:
          </label>
          <select
            id="siee-assignment-select"
            value={selectedAssignmentId}
            onChange={(e) => setSelectedAssignmentId(e.target.value)}
            disabled={activeAssignments.length === 0}
            style={{
              width: '100%',
              padding: '0.5rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              backgroundColor: '#FFFFFF',
              fontSize: '0.875rem',
              color: '#0F172A',
            }}
          >
            {activeAssignments.map((a) => (
              <option key={a.id} value={a.id}>
                {a.group_name} • {a.subject_name} ({a.grade_name || 'Salón'})
              </option>
            ))}
          </select>
        </div>

        {/* Academic Period Selector */}
        <div>
          <label
            htmlFor="siee-period-select"
            style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.375rem' }}
          >
            Período Académico:
          </label>
          <select
            id="siee-period-select"
            value={selectedPeriodId}
            onChange={(e) => setSelectedPeriodId(e.target.value)}
            disabled={loadingPeriods || periods.length === 0}
            style={{
              width: '100%',
              padding: '0.5rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              backgroundColor: '#FFFFFF',
              fontSize: '0.875rem',
              color: '#0F172A',
            }}
          >
            {periods.map((p) => (
              <option key={p.id} value={p.id}>
                Período {p.period_number}: {p.name} ({p.weight_percentage}% peso) {p.is_closed ? '🔒 [CERRADO]' : '🟢 [ABIERTO]'}
              </option>
            ))}
          </select>
        </div>

        {/* Period Status Indicator */}
        <div>
          <div style={{ fontSize: '0.75rem', color: '#64748B', marginBottom: '0.375rem', fontWeight: 600 }}>
            Estado del Período
          </div>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.45rem 0.85rem',
              borderRadius: '8px',
              fontSize: '0.8125rem',
              fontWeight: 700,
              backgroundColor: isPeriodClosed ? '#FEE2E2' : '#DCFCE7',
              color: isPeriodClosed ? '#991B1B' : '#166534',
              border: `1px solid ${isPeriodClosed ? '#FCA5A5' : '#86EFAC'}`,
            }}
          >
            <span>{isPeriodClosed ? '🔒' : '🟢'}</span>
            <span>{isPeriodClosed ? 'PERÍODO CERRADO (SELLADO)' : 'PERÍODO ABIERTO'}</span>
          </div>
        </div>
      </div>

      {/* Closed Period Alert Banner */}
      {isPeriodClosed && (
        <div
          style={{
            backgroundColor: '#FFF1F2',
            border: '1px solid #FDA4AF',
            borderRadius: '10px',
            padding: '1rem 1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.75rem',
            color: '#9F1239',
            fontSize: '0.875rem',
            lineHeight: 1.5,
          }}
        >
          <span style={{ fontSize: '1.25rem' }}>🔒</span>
          <div>
            <strong>Período Académico Sellado Institucionalmente:</strong>
            <br />
            Las calificaciones de este período se encuentran congeladas de forma inmutable. No se admiten adiciones ni modificaciones directas.
            Para realizar correcciones o aperturas extemporáneas, comuníquese con Coordinación Académica o Rectoría.
          </div>
        </div>
      )}

      {/* Status Feedback Message */}
      {statusMessage && (
        <div
          style={{
            backgroundColor:
              statusMessage.type === 'success'
                ? '#F0FDF4'
                : statusMessage.type === 'warning'
                ? '#FEFCE8'
                : '#FEF2F2',
            border: `1px solid ${
              statusMessage.type === 'success'
                ? '#86EFAC'
                : statusMessage.type === 'warning'
                ? '#FDE047'
                : '#FCA5A5'
            }`,
            borderRadius: '8px',
            padding: '0.875rem 1.25rem',
            marginBottom: '1.5rem',
            color:
              statusMessage.type === 'success'
                ? '#166534'
                : statusMessage.type === 'warning'
                ? '#854D0E'
                : '#991B1B',
            fontSize: '0.875rem',
            fontWeight: 500,
          }}
        >
          {statusMessage.text}
        </div>
      )}

      {/* Loading Spinner */}
      {loadingSheet && (
        <div style={{ padding: '3rem 0', textAlign: 'center' }}>
          <LoadingSpinner />
          <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
            Cargando la sábana de notas del período...
          </p>
        </div>
      )}

      {/* Main Grading Matrix Table */}
      {!loadingSheet && sheet && (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            border: '1px solid #E2E8F0',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            overflow: 'hidden',
          }}
        >
          {/* Table Header & Action Bar */}
          <div
            style={{
              padding: '1rem 1.25rem',
              borderBottom: '1px solid #E2E8F0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
              backgroundColor: '#FAFAFA',
            }}
          >
            <div>
              <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A' }}>
                Estudiantes Matriculados ({sheet.students.length})
              </span>
              <span style={{ fontSize: '0.8125rem', color: '#64748B', marginLeft: '0.5rem' }}>
                • {sheet.activities.length} actividad(es) ponderada(s)
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              {dirtyCount > 0 && (
                <span style={{ fontSize: '0.8125rem', color: '#D97706', fontWeight: 600 }}>
                  ⚠️ {dirtyCount} estudiante(s) con cambios pendientes
                </span>
              )}
              <Button
                variant="primary"
                onClick={handleSaveGrades}
                disabled={isSheetLocked || saving || dirtyCount === 0}
              >
                {saving ? 'Guardando...' : 'Guardar Calificaciones'}
              </Button>
            </div>
          </div>

          {/* Table Container */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.75rem 1rem', width: '40px' }}>#</th>
                  <th style={{ padding: '0.75rem 1rem', minWidth: '200px' }}>Estudiante</th>
                  <th style={{ padding: '0.75rem 0.5rem', textAlign: 'center', width: '95px' }}>
                    Calculada
                  </th>
                  <th style={{ padding: '0.75rem 0.5rem', textAlign: 'center', width: '110px' }}>
                    Definitiva *
                  </th>
                  <th style={{ padding: '0.75rem 0.5rem', textAlign: 'center', width: '110px' }}>
                    Desempeño
                  </th>
                  <th style={{ padding: '0.75rem 0.5rem', minWidth: '220px' }}>
                    Motivo de Ajuste Pedagógico
                  </th>
                  <th style={{ padding: '0.75rem 0.5rem', textAlign: 'center', width: '75px' }}>
                    Fallas
                  </th>
                  <th style={{ padding: '0.75rem 0.5rem', textAlign: 'center', width: '75px' }}>
                    Injust.
                  </th>
                  <th style={{ padding: '0.75rem 0.5rem', minWidth: '150px' }}>Nivelación</th>
                  <th style={{ padding: '0.75rem 1rem', minWidth: '160px' }}>Observaciones</th>
                </tr>
              </thead>
              <tbody>
                {sheet.students.length === 0 ? (
                  <tr>
                    <td colSpan={10} style={{ padding: '2rem', textAlign: 'center', color: '#64748B' }}>
                      No hay estudiantes matriculados en este grupo para el período actual.
                    </td>
                  </tr>
                ) : (
                  sheet.students.map((student, idx) => {
                    const state = gradesState[student.student_id] || {
                      calculatedScore: student.calculated_score,
                      finalScore: String(student.final_score),
                      adjustmentReason: student.adjustment_reason || '',
                      totalAbsences: String(student.total_absences),
                      unexcusedAbsences: String(student.unexcused_absences),
                      observations: student.observations || '',
                      isDirty: false,
                    }

                    const scoreNum = parseFloat(state.finalScore) || 0
                    const isAdjusted = Math.abs(scoreNum - state.calculatedScore) > 0.001
                    const hasRecoveries = student.recoveries && student.recoveries.length > 0
                    const isFailing = scoreNum < passingScore
                    const badge = getPerformanceBadge(student.performance_level)

                    return (
                      <tr
                        key={student.student_id}
                        style={{
                          borderBottom: '1px solid #E2E8F0',
                          backgroundColor: isAdjusted ? '#FFFBEB' : idx % 2 === 0 ? '#FFFFFF' : '#F9FAFB',
                        }}
                      >
                        {/* Index */}
                        <td style={{ padding: '0.625rem 1rem', color: '#94A3B8', fontWeight: 600 }}>
                          {idx + 1}
                        </td>

                        {/* Student Name & Document */}
                        <td style={{ padding: '0.625rem 1rem' }}>
                          <div style={{ fontWeight: 700, color: '#0F172A' }}>
                            {student.last_name}, {student.first_name}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                            {student.document_number ? `Doc: ${student.document_number}` : ''}
                            {student.simat_code ? ` • SIMAT: ${student.simat_code}` : ''}
                          </div>
                        </td>

                        {/* Calculated Score */}
                        <td style={{ padding: '0.625rem 0.5rem', textAlign: 'center' }}>
                          <span
                            style={{
                              display: 'inline-block',
                              padding: '0.2rem 0.5rem',
                              borderRadius: '6px',
                              backgroundColor: '#F1F5F9',
                              color: '#334155',
                              fontWeight: 700,
                            }}
                          >
                            {state.calculatedScore.toFixed(2)}
                          </span>
                        </td>

                        {/* Final Score Input */}
                        <td style={{ padding: '0.625rem 0.5rem', textAlign: 'center' }}>
                          <input
                            type="number"
                            step="0.1"
                            min={minScale}
                            max={maxScale}
                            value={state.finalScore}
                            onChange={(e) => handleFinalScoreChange(student.student_id, e.target.value)}
                            disabled={isSheetLocked}
                            style={{
                              width: '75px',
                              padding: '0.35rem 0.4rem',
                              textAlign: 'center',
                              fontWeight: 700,
                              fontSize: '0.875rem',
                              borderRadius: '6px',
                              border: isAdjusted ? '2px solid #F59E0B' : '1px solid #CBD5E1',
                              backgroundColor: isSheetLocked ? '#F1F5F9' : '#FFFFFF',
                              color: scoreNum < passingScore ? '#DC2626' : '#0F172A',
                            }}
                          />
                          {isAdjusted && (
                            <div style={{ fontSize: '0.6875rem', color: '#D97706', fontWeight: 700, marginTop: '0.15rem' }}>
                              Ajustada ⚠️
                            </div>
                          )}
                        </td>

                        {/* Performance Level */}
                        <td style={{ padding: '0.625rem 0.5rem', textAlign: 'center' }}>
                          <span
                            style={{
                              display: 'inline-block',
                              padding: '0.2rem 0.5rem',
                              borderRadius: '6px',
                              backgroundColor: badge.bg,
                              color: badge.color,
                              border: `1px solid ${badge.border}`,
                              fontWeight: 700,
                              fontSize: '0.6875rem',
                            }}
                          >
                            {badge.label}
                          </span>
                        </td>

                        {/* Adjustment Reason (Mandatory when adjusted) */}
                        <td style={{ padding: '0.625rem 0.5rem' }}>
                          <input
                            type="text"
                            placeholder={isAdjusted ? 'Explicación del ajuste *' : 'Opcional si no se ajusta'}
                            value={state.adjustmentReason}
                            onChange={(e) => handleAdjustmentReasonChange(student.student_id, e.target.value)}
                            disabled={isSheetLocked}
                            style={{
                              width: '100%',
                              padding: '0.35rem 0.5rem',
                              fontSize: '0.75rem',
                              borderRadius: '6px',
                              border: isAdjusted && !state.adjustmentReason.trim()
                                ? '1.5px solid #DC2626'
                                : '1px solid #CBD5E1',
                              backgroundColor: isSheetLocked ? '#F1F5F9' : '#FFFFFF',
                            }}
                          />
                        </td>

                        {/* Absences Total */}
                        <td style={{ padding: '0.625rem 0.5rem', textAlign: 'center' }}>
                          <input
                            type="number"
                            min="0"
                            value={state.totalAbsences}
                            onChange={(e) => handleAbsencesChange(student.student_id, 'totalAbsences', e.target.value)}
                            disabled={isSheetLocked}
                            style={{
                              width: '50px',
                              padding: '0.35rem 0.25rem',
                              textAlign: 'center',
                              fontSize: '0.75rem',
                              borderRadius: '6px',
                              border: '1px solid #CBD5E1',
                              backgroundColor: isSheetLocked ? '#F1F5F9' : '#FFFFFF',
                            }}
                          />
                        </td>

                        {/* Unexcused Absences */}
                        <td style={{ padding: '0.625rem 0.5rem', textAlign: 'center' }}>
                          <input
                            type="number"
                            min="0"
                            value={state.unexcusedAbsences}
                            onChange={(e) => handleAbsencesChange(student.student_id, 'unexcusedAbsences', e.target.value)}
                            disabled={isSheetLocked}
                            style={{
                              width: '50px',
                              padding: '0.35rem 0.25rem',
                              textAlign: 'center',
                              fontSize: '0.75rem',
                              borderRadius: '6px',
                              border: '1px solid #CBD5E1',
                              backgroundColor: isSheetLocked ? '#F1F5F9' : '#FFFFFF',
                            }}
                          />
                        </td>

                        {/* Recovery Action / History */}
                        <td style={{ padding: '0.625rem 0.5rem' }}>
                          {hasRecoveries ? (
                            <div>
                              <span
                                style={{
                                  display: 'inline-block',
                                  fontSize: '0.75rem',
                                  backgroundColor: '#EDE9FE',
                                  color: '#5B21B6',
                                  padding: '0.15rem 0.4rem',
                                  borderRadius: '4px',
                                  fontWeight: 600,
                                }}
                              >
                                Definitiva Nivelada: {student.recoveries[0].final_adjusted_score.toFixed(2)}
                              </span>
                              <div style={{ fontSize: '0.6875rem', color: '#64748B', marginTop: '0.15rem' }}>
                                Nota examen: {student.recoveries[0].recovery_score.toFixed(2)} (Cap: {student.recoveries[0].applied_cap.toFixed(2)})
                              </div>
                            </div>
                          ) : (
                            isFailing && canRecover && (
                              <button
                                onClick={() => handleOpenRecoveryModal(student)}
                                disabled={isPeriodClosed}
                                style={{
                                  backgroundColor: '#F3E8FF',
                                  color: '#6B21A8',
                                  border: '1px solid #D8B4FE',
                                  padding: '0.25rem 0.5rem',
                                  borderRadius: '6px',
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  cursor: isPeriodClosed ? 'not-allowed' : 'pointer',
                                }}
                              >
                                + Nivelar
                              </button>
                            )
                          )}
                        </td>

                        {/* Pedagogical Observations */}
                        <td style={{ padding: '0.625rem 1rem' }}>
                          <input
                            type="text"
                            placeholder="Comentarios..."
                            value={state.observations}
                            onChange={(e) => handleObservationsChange(student.student_id, e.target.value)}
                            disabled={isSheetLocked}
                            style={{
                              width: '100%',
                              padding: '0.35rem 0.5rem',
                              fontSize: '0.75rem',
                              borderRadius: '6px',
                              border: '1px solid #CBD5E1',
                              backgroundColor: isSheetLocked ? '#F1F5F9' : '#FFFFFF',
                            }}
                          />
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recovery Modal */}
      {recoveryModalStudent && (
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
                Registrar Nivelación / Recuperación
              </h3>
              <button
                onClick={() => setRecoveryModalStudent(null)}
                style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: '#64748B' }}
              >
                ✕
              </button>
            </div>

            <div style={{ backgroundColor: '#F8FAFC', padding: '0.875rem', borderRadius: '8px', marginBottom: '1rem' }}>
              <div style={{ fontWeight: 700, color: '#0F172A', fontSize: '0.875rem' }}>
                {recoveryModalStudent.student.last_name}, {recoveryModalStudent.student.first_name}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
                Nota inicial del período: <strong style={{ color: '#DC2626' }}>{recoveryModalStudent.student.final_score.toFixed(2)}</strong>
                {' • '}
                Tope máximo SIEE (Cap): <strong>{recoveryCap.toFixed(2)}</strong>
              </div>
            </div>

            <div style={{ display: 'grid', gap: '0.875rem', marginBottom: '1.25rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Nota obtenida en el examen de nivelación ({minScale} - {maxScale}) *
                </label>
                <input
                  type="number"
                  step="0.1"
                  min={minScale}
                  max={maxScale}
                  value={recoveryScoreInput}
                  onChange={(e) => setRecoveryScoreInput(e.target.value)}
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
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Fecha de Nivelación *
                </label>
                <input
                  type="date"
                  value={recoveryDateInput}
                  onChange={(e) => setRecoveryDateInput(e.target.value)}
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
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Número de Acta / Folio (Opcional)
                </label>
                <input
                  type="text"
                  placeholder="Ej: ACTA-REC-2026-001"
                  value={recoveryActInput}
                  onChange={(e) => setRecoveryActInput(e.target.value)}
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
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Observaciones Pedagógicas
                </label>
                <textarea
                  rows={2}
                  placeholder="Descripción de la actividad o logros superados..."
                  value={recoveryObsInput}
                  onChange={(e) => setRecoveryObsInput(e.target.value)}
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

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button variant="secondary" onClick={() => setRecoveryModalStudent(null)}>
                Cancelar
              </Button>
              <Button variant="primary" onClick={handleSaveRecovery} disabled={savingRecovery}>
                {savingRecovery ? 'Asentando...' : 'Asentar Nivelación'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TeacherSieeEvaluationView
