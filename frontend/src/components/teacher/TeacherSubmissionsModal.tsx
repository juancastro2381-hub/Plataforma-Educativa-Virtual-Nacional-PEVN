/**
 * PEVN Frontend — Teacher Submissions Review Modal Component (Phase B3-H13)
 *
 * Dedicated educator interface to review student submissions:
 * - Summary metrics (Enrolled, Submitted, Late, Returned, Graded)
 * - Student roster table with submission status and attempt details
 * - Inspect individual student attempt (answers, attached files, history)
 * - Download student submission attachments safely (anti-IDOR)
 * - Return submission for pedagogical correction with qualitative feedback
 * - Shortcut to grade entry
 */

import React, { useEffect, useState } from 'react'
import type {
  TeacherSubmissionDetailResponse,
  TeacherSubmissionItemResponse,
  TeacherSubmissionsListResponse,
} from '@/types/teacher'
import { teacherApi } from '@/services/teacher'
import { formatDateTime } from '@/utils'
import { Button } from '@/components/ui/Button'

interface TeacherSubmissionsModalProps {
  activityId: string
  activityTitle: string
  onClose: () => void
  onGradingShortcut?: (activityId: string) => void
  initialStudentId?: string
}

export const TeacherSubmissionsModal: React.FC<TeacherSubmissionsModalProps> = ({
  activityId,
  activityTitle,
  onClose,
  onGradingShortcut,
  initialStudentId,
}) => {
  const [loadingList, setLoadingList] = useState<boolean>(true)
  const [submissionsList, setSubmissionsList] = useState<TeacherSubmissionsListResponse | null>(null)
  const [listError, setListError] = useState<string | null>(null)

  // Filter state
  const [filterStatus, setFilterStatus] = useState<string>('ALL')
  const [searchQuery, setSearchQuery] = useState<string>('')

  // Inspected student state
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(initialStudentId || null)
  const [studentDetail, setStudentDetail] = useState<TeacherSubmissionDetailResponse | null>(null)
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false)
  const [detailError, setDetailError] = useState<string | null>(null)

  // Return submission state
  const [showReturnDialog, setShowReturnDialog] = useState<boolean>(false)
  const [returnFeedback, setReturnFeedback] = useState<string>('')
  const [submittingReturn, setSubmittingReturn] = useState<boolean>(false)
  const [returnError, setReturnError] = useState<string | null>(null)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)

  // Download state
  const [downloadingAttachmentId, setDownloadingAttachmentId] = useState<string | null>(null)

  // Fetch submissions list
  const loadSubmissions = async () => {
    setLoadingList(true)
    setListError(null)
    try {
      const data = await teacherApi.getActivitySubmissions(activityId)
      setSubmissionsList(data)
    } catch (err: unknown) {
      setListError(err instanceof Error ? err.message : 'Error al cargar las entregas.')
    } finally {
      setLoadingList(false)
    }
  }

  // Fetch inspected student detail
  const loadStudentDetail = async (studentId: string) => {
    setSelectedStudentId(studentId)
    setLoadingDetail(true)
    setDetailError(null)
    setShowReturnDialog(false)
    setReturnFeedback('')
    try {
      const data = await teacherApi.getStudentSubmissionDetail(activityId, studentId)
      setStudentDetail(data)
    } catch (err: unknown) {
      setDetailError(err instanceof Error ? err.message : 'Error al cargar el detalle del estudiante.')
    } finally {
      setLoadingDetail(false)
    }
  }

  useEffect(() => {
    void loadSubmissions()
  }, [activityId])

  useEffect(() => {
    if (initialStudentId) {
      void loadStudentDetail(initialStudentId)
    }
  }, [initialStudentId])

  // Download attachment
  const handleDownload = async (attachmentId: string, fileName: string) => {
    if (!selectedStudentId) return
    try {
      setDownloadingAttachmentId(attachmentId)
      const { data, filename } = await teacherApi.downloadStudentSubmissionAttachment(
        activityId,
        selectedStudentId,
        attachmentId
      )
      const blobUrl = window.URL.createObjectURL(data)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = filename || fileName || 'entrega_estudiante'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(blobUrl)
      document.body.removeChild(a)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Error al descargar el archivo de la entrega.')
    } finally {
      setDownloadingAttachmentId(null)
    }
  }

  // Confirm return
  const handleReturnSubmission = async () => {
    if (!selectedStudentId || !returnFeedback.trim()) {
      setReturnError('Debe ingresar una justificación o retroalimentación para la devolución.')
      return
    }

    setSubmittingReturn(true)
    setReturnError(null)
    try {
      const updated = await teacherApi.returnStudentSubmission(
        activityId,
        selectedStudentId,
        returnFeedback.trim()
      )
      setStudentDetail(updated)
      setShowReturnDialog(false)
      setReturnFeedback('')
      setActionSuccess('Entrega devuelta al estudiante para corrección pedagógica.')
      setTimeout(() => setActionSuccess(null), 4000)
      // Refresh list in background
      void loadSubmissions()
    } catch (err: unknown) {
      setReturnError(err instanceof Error ? err.message : 'Error al devolver la entrega.')
    } finally {
      setSubmittingReturn(false)
    }
  }

  // Filter items
  const filteredItems = (submissionsList?.items || []).filter((item: TeacherSubmissionItemResponse) => {
    if (filterStatus !== 'ALL') {
      if (filterStatus === 'PENDING' && item.status !== null && item.status !== 'DRAFT') return false
      if (filterStatus === 'SUBMITTED' && item.status !== 'SUBMITTED') return false
      if (filterStatus === 'LATE' && item.status !== 'LATE') return false
      if (filterStatus === 'RETURNED' && item.status !== 'RETURNED') return false
      if (filterStatus === 'GRADED' && item.status !== 'GRADED' && item.grade_status !== 'GRADED') return false
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      const matchName = item.student_name.toLowerCase().includes(q)
      const matchDoc = (item.student_document || '').toLowerCase().includes(q)
      return matchName || matchDoc
    }
    return true
  })

  // Counters
  const totalEnrolled = submissionsList?.total || 0
  const totalSubmitted = (submissionsList?.items || []).filter(
    (i) => i.status === 'SUBMITTED' || i.status === 'LATE' || i.status === 'RETURNED' || i.status === 'GRADED'
  ).length
  const totalLate = (submissionsList?.items || []).filter((i) => i.status === 'LATE').length
  const totalReturned = (submissionsList?.items || []).filter((i) => i.status === 'RETURNED').length

  const getStatusBadge = (status: string | null, isLate: boolean) => {
    if (!status || status === 'DRAFT') {
      return (
        <span style={{ backgroundColor: '#F1F5F9', color: '#64748B', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>
          Sin Entregar
        </span>
      )
    }
    if (status === 'LATE' || isLate) {
      return (
        <span style={{ backgroundColor: '#FEE2E2', color: '#991B1B', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700 }}>
          ⚠️ Tardía
        </span>
      )
    }
    if (status === 'SUBMITTED') {
      return (
        <span style={{ backgroundColor: '#DCFCE7', color: '#166534', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700 }}>
          ✓ Entregado
        </span>
      )
    }
    if (status === 'RETURNED') {
      return (
        <span style={{ backgroundColor: '#FED7AA', color: '#9A3412', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700 }}>
          ↩ Devuelto
        </span>
      )
    }
    if (status === 'GRADED') {
      return (
        <span style={{ backgroundColor: '#DCFCE7', color: '#15803D', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700 }}>
          ✓ Calificado
        </span>
      )
    }
    return null
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '1rem',
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          maxWidth: selectedStudentId ? '920px' : '980px',
          width: '100%',
          maxHeight: '92vh',
          overflowY: 'auto',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          border: '1px solid #E2E8F0',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid #E2E8F0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '1rem',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  color: '#4338CA',
                  backgroundColor: '#EEF2FF',
                  padding: '0.2rem 0.55rem',
                  borderRadius: '6px',
                  border: '1px solid #C7D2FE',
                }}
              >
                📥 Control de Entregas
              </span>
              {submissionsList && (
                <span style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>
                  Modalidad: {submissionsList.delivery_type}
                </span>
              )}
            </div>

            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
              {activityTitle}
            </h2>
          </div>

          <button
            onClick={onClose}
            aria-label="Cerrar modal"
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              color: '#94A3B8',
              cursor: 'pointer',
              padding: '0.2rem',
              lineHeight: 1,
            }}
          >
            ✕
          </button>
        </div>

        {/* Global Notifications */}
        {actionSuccess && (
          <div style={{ backgroundColor: '#F0FDF4', borderBottom: '1px solid #BBF7D0', padding: '0.75rem 1.5rem', color: '#166534', fontSize: '0.875rem', fontWeight: 600 }}>
            {actionSuccess}
          </div>
        )}

        {listError && (
          <div style={{ backgroundColor: '#FEF2F2', borderBottom: '1px solid #FECACA', padding: '0.75rem 1.5rem', color: '#991B1B', fontSize: '0.875rem', fontWeight: 600 }}>
            {listError}
          </div>
        )}

        {/* Body Content */}
        <div style={{ padding: '1.5rem', flex: 1, overflowY: 'auto' }}>
          {/* ============================================================== */}
          {/* VIEW 1: STUDENT DETAIL VIEW (When student selected)           */}
          {/* ============================================================== */}
          {selectedStudentId ? (
            <div>
              {/* Back Button */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <button
                  onClick={() => {
                    setSelectedStudentId(null)
                    setStudentDetail(null)
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#2563EB',
                    fontSize: '0.875rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                    padding: 0,
                  }}
                >
                  ← Volver a la lista de estudiantes
                </button>

                {onGradingShortcut && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      onGradingShortcut(activityId)
                      onClose()
                    }}
                  >
                    📊 Ir a Calificar en Planilla
                  </Button>
                )}
              </div>

              {loadingDetail && (
                <div style={{ textAlign: 'center', padding: '3rem', color: '#64748B' }}>
                  Cargando entrega del estudiante...
                </div>
              )}

              {detailError && (
                <div style={{ backgroundColor: '#FEF2F2', border: '1px solid #FECACA', padding: '1rem', borderRadius: '8px', color: '#991B1B', fontSize: '0.875rem' }}>
                  {detailError}
                </div>
              )}

              {!loadingDetail && studentDetail && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {/* Student Header Card */}
                  <div
                    style={{
                      backgroundColor: '#F8FAFC',
                      border: '1px solid #E2E8F0',
                      borderRadius: '12px',
                      padding: '1rem 1.25rem',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: '0.75rem',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0F172A' }}>
                        {studentDetail.student_name}
                      </div>
                      <div style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                        {studentDetail.current_attempt
                          ? `Intento #${studentDetail.current_attempt.attempt_number} • ${formatDateTime(studentDetail.current_attempt.submitted_at)}`
                          : 'Sin intentos presentados'}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      {studentDetail.current_attempt &&
                        getStatusBadge(studentDetail.current_attempt.status, studentDetail.current_attempt.is_late)}

                      {studentDetail.grade_score !== null && (
                        <span
                          style={{
                            fontSize: '1rem',
                            fontWeight: 800,
                            color: '#15803D',
                            backgroundColor: '#DCFCE7',
                            padding: '0.25rem 0.65rem',
                            borderRadius: '8px',
                            border: '1px solid #86EFAC',
                          }}
                        >
                          Nota: {Number(studentDetail.grade_score).toFixed(1)}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Return Modal / Confirmation Dialog */}
                  {showReturnDialog && (
                    <div
                      style={{
                        backgroundColor: '#FFF7ED',
                        border: '1px solid #FDBA74',
                        borderRadius: '12px',
                        padding: '1.25rem',
                      }}
                    >
                      <h4 style={{ margin: '0 0 0.5rem 0', color: '#9A3412', fontSize: '0.95rem', fontWeight: 800 }}>
                        ↩ Devolver Entrega para Corrección Pedagógica
                      </h4>
                      <p style={{ margin: '0 0 0.75rem 0', fontSize: '0.8125rem', color: '#C2410C', lineHeight: 1.5 }}>
                        Al devolver la entrega, el estudiante podrá corregir su trabajo y presentar un nuevo intento (Intento #{((studentDetail.current_attempt?.attempt_number || 1) + 1)}).
                        La nota en la planilla se restablecerá a <strong>PENDIENTE</strong>.
                      </p>

                      {returnError && (
                        <div style={{ backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', color: '#991B1B', padding: '0.5rem', borderRadius: '6px', marginBottom: '0.5rem', fontSize: '0.8125rem' }}>
                          {returnError}
                        </div>
                      )}

                      <textarea
                        rows={3}
                        value={returnFeedback}
                        onChange={(e) => setReturnFeedback(e.target.value)}
                        placeholder="Escribe las observaciones y recomendaciones pedagógicas para que el estudiante corrija su entrega..."
                        style={{
                          width: '100%',
                          padding: '0.65rem',
                          borderRadius: '8px',
                          border: '1px solid #CBD5E1',
                          fontSize: '0.875rem',
                          boxSizing: 'border-box',
                          fontFamily: 'inherit',
                          marginBottom: '0.75rem',
                        }}
                      />

                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                        <button
                          onClick={() => {
                            setShowReturnDialog(false)
                            setReturnError(null)
                          }}
                          style={{
                            padding: '0.45rem 0.9rem',
                            borderRadius: '6px',
                            border: '1px solid #94A3B8',
                            backgroundColor: '#FFFFFF',
                            fontSize: '0.8125rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          Cancelar
                        </button>
                        <button
                          onClick={() => void handleReturnSubmission()}
                          disabled={submittingReturn || !returnFeedback.trim()}
                          style={{
                            padding: '0.45rem 1rem',
                            borderRadius: '6px',
                            border: 'none',
                            backgroundColor: '#EA580C',
                            color: '#FFFFFF',
                            fontSize: '0.8125rem',
                            fontWeight: 700,
                            cursor: submittingReturn || !returnFeedback.trim() ? 'not-allowed' : 'pointer',
                          }}
                        >
                          {submittingReturn ? 'Devolviendo...' : 'Confirmar Devolución'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Current Attempt Content */}
                  {studentDetail.current_attempt ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      {/* Text Answer */}
                      <div>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 700, color: '#334155' }}>
                          Respuesta de Texto del Estudiante:
                        </h4>
                        <div
                          style={{
                            backgroundColor: '#FFFFFF',
                            border: '1px solid #E2E8F0',
                            borderRadius: '8px',
                            padding: '1rem',
                            fontSize: '0.875rem',
                            color: studentDetail.current_attempt.student_response ? '#0F172A' : '#94A3B8',
                            lineHeight: 1.6,
                            whiteSpace: 'pre-wrap',
                            minHeight: '80px',
                          }}
                        >
                          {studentDetail.current_attempt.student_response || '(El estudiante no ingresó respuesta de texto)'}
                        </div>
                      </div>

                      {/* Attachments */}
                      <div>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 700, color: '#334155' }}>
                          Archivos Adjuntos ({studentDetail.current_attempt.attachments.length}):
                        </h4>

                        {studentDetail.current_attempt.attachments.length > 0 ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {studentDetail.current_attempt.attachments.map((att) => (
                              <div
                                key={att.id}
                                style={{
                                  backgroundColor: '#F8FAFC',
                                  border: '1px solid #E2E8F0',
                                  borderRadius: '8px',
                                  padding: '0.75rem 1rem',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                  gap: '0.5rem',
                                }}
                              >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflow: 'hidden' }}>
                                  <span>📄</span>
                                  <div>
                                    <div style={{ fontWeight: 600, fontSize: '0.875rem', color: '#0F172A' }}>
                                      {att.original_filename}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                                      {(att.file_size_bytes / 1024 / 1024).toFixed(2)} MB • {formatDateTime(att.created_at)}
                                    </div>
                                  </div>
                                </div>

                                <button
                                  onClick={() => void handleDownload(att.id, att.original_filename)}
                                  disabled={downloadingAttachmentId === att.id}
                                  style={{
                                    backgroundColor: '#1E40AF',
                                    color: '#FFFFFF',
                                    border: 'none',
                                    padding: '0.4rem 0.85rem',
                                    borderRadius: '6px',
                                    fontSize: '0.75rem',
                                    fontWeight: 700,
                                    cursor: downloadingAttachmentId === att.id ? 'not-allowed' : 'pointer',
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: '0.3rem',
                                  }}
                                >
                                  <span>{downloadingAttachmentId === att.id ? 'Descargando...' : 'Descargar'}</span>
                                  <span aria-hidden="true">⬇</span>
                                </button>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ backgroundColor: '#F8FAFC', padding: '0.75rem 1rem', borderRadius: '8px', color: '#94A3B8', fontSize: '0.8125rem' }}>
                            No se adjuntaron archivos en este intento.
                          </div>
                        )}
                      </div>

                      {/* Action buttons on current attempt */}
                      {!showReturnDialog &&
                        (studentDetail.current_attempt.status === 'SUBMITTED' ||
                          studentDetail.current_attempt.status === 'LATE') && (
                          <div style={{ display: 'flex', justifyContent: 'flex-start', marginTop: '0.5rem' }}>
                            <button
                              onClick={() => setShowReturnDialog(true)}
                              style={{
                                backgroundColor: '#FFF7ED',
                                color: '#C2410C',
                                border: '1px solid #FDBA74',
                                borderRadius: '8px',
                                padding: '0.5rem 1rem',
                                fontSize: '0.8125rem',
                                fontWeight: 700,
                                cursor: 'pointer',
                              }}
                            >
                              ↩ Devolver Entrega para Corrección Pedagógica
                            </button>
                          </div>
                        )}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '2rem', color: '#64748B', backgroundColor: '#F8FAFC', borderRadius: '12px' }}>
                      Este estudiante aún no ha presentado ninguna entrega.
                    </div>
                  )}

                  {/* Past Attempts History */}
                  {studentDetail.history.length > 1 && (
                    <div style={{ marginTop: '1rem', borderTop: '1px solid #E2E8F0', paddingTop: '1rem' }}>
                      <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.875rem', fontWeight: 800, color: '#0F172A' }}>
                        📜 Historial de Intentos ({studentDetail.history.length})
                      </h4>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {studentDetail.history.map((att) => (
                          <div
                            key={att.id}
                            style={{
                              backgroundColor: '#F8FAFC',
                              border: '1px solid #E2E8F0',
                              borderRadius: '8px',
                              padding: '0.75rem 1rem',
                              fontSize: '0.8125rem',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                              <strong style={{ color: '#0F172A' }}>Intento #{att.attempt_number}</strong>
                              {getStatusBadge(att.status, att.is_late)}
                            </div>

                            {att.submitted_at && (
                              <div style={{ color: '#64748B', fontSize: '0.75rem', marginBottom: '0.3rem' }}>
                                Entregado: {formatDateTime(att.submitted_at)}
                              </div>
                            )}

                            {att.return_feedback && (
                              <div style={{ color: '#9A3412', fontStyle: 'italic', marginBottom: '0.4rem', backgroundColor: '#FFF7ED', padding: '0.4rem 0.6rem', borderRadius: '4px' }}>
                                Observación docente: "{att.return_feedback}"
                              </div>
                            )}

                            {att.attachments.length > 0 && (
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                                {att.attachments.map((a) => (
                                  <button
                                    key={a.id}
                                    onClick={() => void handleDownload(a.id, a.original_filename)}
                                    style={{
                                      backgroundColor: '#FFFFFF',
                                      border: '1px solid #CBD5E1',
                                      borderRadius: '4px',
                                      padding: '0.2rem 0.5rem',
                                      fontSize: '0.75rem',
                                      cursor: 'pointer',
                                    }}
                                  >
                                    📎 {a.original_filename} ⬇
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            /* ============================================================== */
            /* VIEW 2: ALL STUDENTS ROSTER & SUBMISSIONS TABLE               */
            /* ============================================================== */
            <div>
              {/* Summary KPIs */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                  gap: '0.75rem',
                  marginBottom: '1.25rem',
                }}
              >
                <div style={{ backgroundColor: '#F8FAFC', padding: '0.75rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                  <span style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>Matriculados</span>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>{totalEnrolled}</div>
                </div>

                <div style={{ backgroundColor: '#F0FDF4', padding: '0.75rem', borderRadius: '8px', border: '1px solid #BBF7D0' }}>
                  <span style={{ fontSize: '0.75rem', color: '#166534', fontWeight: 600 }}>Con Entrega</span>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#15803D' }}>{totalSubmitted}</div>
                </div>

                <div style={{ backgroundColor: '#FEF2F2', padding: '0.75rem', borderRadius: '8px', border: '1px solid #FECACA' }}>
                  <span style={{ fontSize: '0.75rem', color: '#991B1B', fontWeight: 600 }}>Entregas Tardías</span>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#DC2626' }}>{totalLate}</div>
                </div>

                <div style={{ backgroundColor: '#FFF7ED', padding: '0.75rem', borderRadius: '8px', border: '1px solid #FED7AA' }}>
                  <span style={{ fontSize: '0.75rem', color: '#9A3412', fontWeight: 600 }}>Devueltas</span>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#EA580C' }}>{totalReturned}</div>
                </div>

                <div style={{ backgroundColor: '#F1F5F9', padding: '0.75rem', borderRadius: '8px', border: '1px solid #CBD5E1' }}>
                  <span style={{ fontSize: '0.75rem', color: '#475569', fontWeight: 600 }}>Pendientes</span>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#334155' }}>
                    {Math.max(0, totalEnrolled - totalSubmitted)}
                  </div>
                </div>
              </div>

              {/* Filters & Search */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                <input
                  type="text"
                  placeholder="Buscar estudiante por nombre o documento..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    padding: '0.5rem 0.75rem',
                    borderRadius: '6px',
                    border: '1px solid #CBD5E1',
                    fontSize: '0.875rem',
                    minWidth: '260px',
                    flex: 1,
                  }}
                />

                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  style={{
                    padding: '0.5rem 0.75rem',
                    borderRadius: '6px',
                    border: '1px solid #CBD5E1',
                    fontSize: '0.875rem',
                  }}
                >
                  <option value="ALL">Todos los estados</option>
                  <option value="SUBMITTED">Entregados</option>
                  <option value="LATE">Entregas Tardías</option>
                  <option value="RETURNED">Devueltos</option>
                  <option value="PENDING">Sin entregar</option>
                  <option value="GRADED">Calificados</option>
                </select>
              </div>

              {/* Students Submissions Table */}
              {loadingList ? (
                <div style={{ textAlign: 'center', padding: '3rem', color: '#64748B' }}>
                  Cargando planilla de entregas...
                </div>
              ) : filteredItems.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2.5rem', color: '#64748B', backgroundColor: '#F8FAFC', borderRadius: '8px' }}>
                  No se encontraron estudiantes con los filtros seleccionados.
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569', textAlign: 'left', backgroundColor: '#F8FAFC' }}>
                        <th style={{ padding: '0.75rem' }}>Estudiante</th>
                        <th style={{ padding: '0.75rem' }}>Documento</th>
                        <th style={{ padding: '0.75rem' }}>Estado Entrega</th>
                        <th style={{ padding: '0.75rem' }}>Intento</th>
                        <th style={{ padding: '0.75rem' }}>Adjuntos</th>
                        <th style={{ padding: '0.75rem' }}>Nota</th>
                        <th style={{ padding: '0.75rem', textAlign: 'right' }}>Acción</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredItems.map((item) => (
                        <tr key={item.student_id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                          <td style={{ padding: '0.75rem', fontWeight: 600, color: '#0F172A' }}>
                            {item.student_name}
                          </td>
                          <td style={{ padding: '0.75rem', color: '#64748B', fontSize: '0.8125rem' }}>
                            {item.student_document}
                          </td>
                          <td style={{ padding: '0.75rem' }}>
                            {getStatusBadge(item.status, item.is_late)}
                          </td>
                          <td style={{ padding: '0.75rem', color: '#475569' }}>
                            {item.attempt_number ? `#${item.attempt_number}` : '—'}
                          </td>
                          <td style={{ padding: '0.75rem', color: '#475569' }}>
                            {item.attachments_count > 0 ? `📎 ${item.attachments_count}` : '—'}
                          </td>
                          <td style={{ padding: '0.75rem', fontWeight: 700, color: item.grade_score !== null ? '#15803D' : '#94A3B8' }}>
                            {item.grade_score !== null ? Number(item.grade_score).toFixed(1) : '—'}
                          </td>
                          <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                            <button
                              onClick={() => void loadStudentDetail(item.student_id)}
                              style={{
                                padding: '0.35rem 0.75rem',
                                borderRadius: '6px',
                                border: '1px solid #CBD5E1',
                                backgroundColor: '#FFFFFF',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                color: '#1E40AF',
                                cursor: 'pointer',
                              }}
                            >
                              👁️ Revisar
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderTop: '1px solid #E2E8F0',
            backgroundColor: '#F8FAFC',
            borderRadius: '0 0 16px 16px',
            display: 'flex',
            justifyContent: 'flex-end',
          }}
        >
          <button
            onClick={onClose}
            style={{
              backgroundColor: '#0F172A',
              color: '#FFFFFF',
              border: 'none',
              padding: '0.55rem 1.25rem',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
