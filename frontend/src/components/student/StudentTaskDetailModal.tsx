/**
 * PEVN Frontend — Student Task Detail & Submission Modal Component (Phase B3-H13)
 *
 * Displays full academic activity instructions, due dates, grading details,
 * teacher feedback, pedagogical resources, and interactive submission workflow:
 * - Multi-modality submission (TEXT, FILE, TEXT_AND_FILE)
 * - Server-side deadline evaluation and late delivery badge
 * - Draft auto-creation and updates
 * - File upload and deletion (max 3 files, 10MB)
 * - Multi-attempt submission lifecycle with teacher return feedback
 * - Past attempts history view
 */

import React, { useEffect, useState } from 'react'
import type {
  StudentActivityItemResponse,
  StudentSubmissionAttempt,
  StudentSubmissionDetailResponse,
} from '@/types/student'
import { studentApi } from '@/services/student'
import { StudentStatusBadge } from './StudentStatusBadge'
import { formatDateTime } from '@/utils'

interface StudentTaskDetailModalProps {
  activity: StudentActivityItemResponse | null
  onClose: () => void
  onSubmitted?: () => void
}

export const StudentTaskDetailModal: React.FC<StudentTaskDetailModalProps> = ({
  activity,
  onClose,
  onSubmitted,
}) => {
  const [downloadingResourceId, setDownloadingResourceId] = useState<string | null>(null)
  const [downloadingAttachmentId, setDownloadingAttachmentId] = useState<string | null>(null)

  // Submission state
  const [submission, setSubmission] = useState<StudentSubmissionDetailResponse | null>(null)
  const [loadingSubmission, setLoadingSubmission] = useState<boolean>(true)
  const [submissionError, setSubmissionError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Draft form state
  const [studentResponseText, setStudentResponseText] = useState<string>('')
  const [savingDraft, setSavingDraft] = useState<boolean>(false)
  const [uploadingFile, setUploadingFile] = useState<boolean>(false)
  const [deletingAttachmentId, setDeletingAttachmentId] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState<boolean>(false)

  // History accordion
  const [showHistory, setShowHistory] = useState<boolean>(false)

  // Load submission detail on mount or activity change
  useEffect(() => {
    if (!activity) return

    let isMounted = true
    setLoadingSubmission(true)
    setSubmissionError(null)

    studentApi
      .getSubmissionDetail(activity.id)
      .then((detail) => {
        if (!isMounted) return
        setSubmission(detail)
        if (detail.current_attempt?.student_response) {
          setStudentResponseText(detail.current_attempt.student_response)
        } else {
          setStudentResponseText('')
        }
      })
      .catch((err: unknown) => {
        if (!isMounted) return
        setSubmissionError(err instanceof Error ? err.message : 'Error al cargar el estado de entrega.')
      })
      .finally(() => {
        if (isMounted) setLoadingSubmission(false)
      })

    return () => {
      isMounted = false
    }
  }, [activity])

  if (!activity) return null

  const isGraded = activity.submission_status === 'GRADED'
  const deliveryType = submission?.delivery_type || activity.delivery_type || 'FILE'
  const currentAttempt = submission?.current_attempt
  const isDraft = currentAttempt?.status === 'DRAFT'
  const canEdit = Boolean(submission?.can_edit_draft && isDraft)

  // Check if past deadline
  const isPastDeadline = Boolean(
    activity.due_date && new Date() > new Date(activity.due_date)
  )

  // Pedagogical resource download
  const handleDownloadResource = async (resourceId: string, fileName: string | null) => {
    try {
      setDownloadingResourceId(resourceId)
      const { data, filename } = await studentApi.downloadActivityResource(activity.id, resourceId)
      const blobUrl = window.URL.createObjectURL(data)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = filename || fileName || 'recurso'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(blobUrl)
      document.body.removeChild(a)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Error al descargar el archivo adjunto.')
    } finally {
      setDownloadingResourceId(null)
    }
  }

  // Student submission attachment download
  const handleDownloadAttachment = async (attachmentId: string, fileName: string) => {
    try {
      setDownloadingAttachmentId(attachmentId)
      const { data, filename } = await studentApi.downloadSubmissionAttachment(activity.id, attachmentId)
      const blobUrl = window.URL.createObjectURL(data)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = filename || fileName || 'archivo_entrega'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(blobUrl)
      document.body.removeChild(a)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Error al descargar el archivo de entrega.')
    } finally {
      setDownloadingAttachmentId(null)
    }
  }

  // Save Draft (text response)
  const handleSaveDraft = async () => {
    try {
      setSavingDraft(true)
      setSubmissionError(null)
      const updated = await studentApi.saveSubmissionDraft(activity.id, {
        student_response: studentResponseText,
      })
      if (submission) {
        setSubmission({
          ...submission,
          current_attempt: updated,
        })
      }
      setSuccessMessage('Borrador guardado exitosamente.')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err: unknown) {
      setSubmissionError(err instanceof Error ? err.message : 'Error al guardar el borrador.')
    } finally {
      setSavingDraft(false)
    }
  }

  // Upload File to Draft
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    const file = files[0]
    if (file.size > 10 * 1024 * 1024) {
      setSubmissionError('El archivo excede el tamaño máximo permitido de 10 MB.')
      e.target.value = ''
      return
    }

    try {
      setUploadingFile(true)
      setSubmissionError(null)
      await studentApi.uploadSubmissionFile(activity.id, file)
      // Refresh submission detail to get updated attachment list
      const updated = await studentApi.getSubmissionDetail(activity.id)
      setSubmission(updated)
      setSuccessMessage('Archivo adjuntado correctamente.')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err: unknown) {
      setSubmissionError(err instanceof Error ? err.message : 'Error al subir el archivo adjunto.')
    } finally {
      setUploadingFile(false)
      e.target.value = ''
    }
  }

  // Delete Attachment from Draft
  const handleDeleteAttachment = async (attachmentId: string) => {
    if (!window.confirm('¿Seguro que deseas eliminar este archivo adjunto?')) return

    try {
      setDeletingAttachmentId(attachmentId)
      setSubmissionError(null)
      await studentApi.deleteSubmissionFile(activity.id, attachmentId)
      // Refresh submission detail
      const updated = await studentApi.getSubmissionDetail(activity.id)
      setSubmission(updated)
      setSuccessMessage('Archivo eliminado del borrador.')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err: unknown) {
      setSubmissionError(err instanceof Error ? err.message : 'Error al eliminar el archivo.')
    } finally {
      setDeletingAttachmentId(null)
    }
  }

  // Submit Activity Formally
  const handleSubmitActivity = async () => {
    // Client-side quick checks according to delivery_type
    const hasText = Boolean(studentResponseText.trim())
    const attCount = currentAttempt?.attachments.length || 0

    if (deliveryType === 'TEXT' && !hasText) {
      setSubmissionError('Debe escribir una respuesta de texto antes de entregar.')
      return
    }
    if (deliveryType === 'FILE' && attCount < 1) {
      setSubmissionError('Debe adjuntar al menos un archivo para realizar la entrega.')
      return
    }
    if (deliveryType === 'TEXT_AND_FILE') {
      if (!hasText) {
        setSubmissionError('Debe escribir una respuesta de texto para esta entrega.')
        return
      }
      if (attCount < 1) {
        setSubmissionError('Debe adjuntar al menos un archivo para esta entrega.')
        return
      }
    }

    const confirmMsg = isPastDeadline
      ? '⚠️ ATENCIÓN: La fecha límite ha vencido. Tu entrega quedará registrada como TARDÍA.\n\n¿Deseas confirmar la entrega ahora?'
      : '¿Confirmas que deseas enviar tu entrega? Una vez enviada, no podrás modificarla salvo que el docente la devuelva para corrección.'

    if (!window.confirm(confirmMsg)) return

    try {
      setSubmitting(true)
      setSubmissionError(null)

      // Save draft text first if modified
      if (hasText && studentResponseText !== (currentAttempt?.student_response || '')) {
        await studentApi.saveSubmissionDraft(activity.id, {
          student_response: studentResponseText,
        })
      }

      const finalDetail = await studentApi.submitActivity(activity.id)
      setSubmission(finalDetail)
      setSuccessMessage('🎉 ¡Actividad entregada exitosamente!')
      if (onSubmitted) {
        onSubmitted()
      }
    } catch (err: unknown) {
      setSubmissionError(err instanceof Error ? err.message : 'Error al enviar la entrega.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
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
          maxWidth: '740px',
          width: '100%',
          maxHeight: '92vh',
          overflowY: 'auto',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
          border: '1px solid #E2E8F0',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => {
          e.stopPropagation()
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '1.5rem',
            borderBottom: '1px solid #E2E8F0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '1rem',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  color: '#1E40AF',
                  backgroundColor: '#EFF6FF',
                  padding: '0.2rem 0.55rem',
                  borderRadius: '6px',
                  border: '1px solid #DBEAFE',
                }}
              >
                📖 {activity.subject_name}
              </span>
              <StudentStatusBadge type="submission" status={activity.submission_status} size="sm" />
              {deliveryType && (
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    color: '#475569',
                    backgroundColor: '#F1F5F9',
                    padding: '0.2rem 0.55rem',
                    borderRadius: '6px',
                    border: '1px solid #E2E8F0',
                  }}
                >
                  {deliveryType === 'TEXT' && '📝 Solo Texto'}
                  {deliveryType === 'FILE' && '📎 Archivo(s)'}
                  {deliveryType === 'TEXT_AND_FILE' && '📝 + 📎 Texto y Archivo'}
                </span>
              )}
            </div>

            <h2
              style={{
                margin: 0,
                fontSize: '1.25rem',
                fontWeight: 800,
                color: '#0F172A',
                lineHeight: 1.3,
              }}
            >
              {activity.title}
            </h2>

            {activity.teacher_name && (
              <div style={{ fontSize: '0.8125rem', color: '#64748B', marginTop: '0.25rem' }}>
                Docente: <strong style={{ color: '#334155' }}>{activity.teacher_name}</strong>
              </div>
            )}
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

        {/* Modal Body */}
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Metadata Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
              gap: '0.75rem',
              backgroundColor: '#F8FAFC',
              padding: '1rem',
              borderRadius: '12px',
              border: '1px solid #E2E8F0',
            }}
          >
            <div>
              <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block', fontWeight: 600 }}>
                Tipo de Actividad
              </span>
              <strong style={{ fontSize: '0.875rem', color: '#0F172A' }}>{activity.activity_type}</strong>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block', fontWeight: 600 }}>
                Fecha Límite
              </span>
              <strong style={{ fontSize: '0.875rem', color: isPastDeadline ? '#DC2626' : '#0F172A' }}>
                {formatDateTime(activity.due_date)}
              </strong>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block', fontWeight: 600 }}>
                Puntaje Máximo
              </span>
              <strong style={{ fontSize: '0.875rem', color: '#0F172A' }}>
                {Number(activity.max_score).toFixed(1)} pts
              </strong>
            </div>

            {activity.score !== null && (
              <div>
                <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block', fontWeight: 600 }}>
                  Calificación Obtenida
                </span>
                <strong style={{ fontSize: '1rem', color: '#15803D' }}>
                  {Number(activity.score).toFixed(1)} / {Number(activity.max_score).toFixed(1)}
                </strong>
              </div>
            )}
          </div>

          {/* Activity Description */}
          {activity.description && (
            <div>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 700, color: '#334155' }}>
                Descripción
              </h4>
              <p style={{ margin: 0, fontSize: '0.875rem', color: '#475569', lineHeight: 1.5 }}>
                {activity.description}
              </p>
            </div>
          )}

          {/* Activity Instructions */}
          {activity.instructions && (
            <div>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 700, color: '#334155' }}>
                Instrucciones Detalladas
              </h4>
              <div
                style={{
                  backgroundColor: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  borderRadius: '8px',
                  padding: '1rem',
                  fontSize: '0.875rem',
                  color: '#1E293B',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {activity.instructions}
              </div>
            </div>
          )}

          {/* Teacher Materials / Resources */}
          {activity.resources && activity.resources.length > 0 && (
            <div>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 700, color: '#334155' }}>
                📁 Materiales y Recursos Adjuntos por el Docente ({activity.resources.length})
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {activity.resources.map((res) => (
                  <div
                    key={res.id}
                    style={{
                      backgroundColor: '#F8FAFC',
                      border: '1px solid #E2E8F0',
                      borderRadius: '8px',
                      padding: '0.75rem 1rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '0.75rem',
                      flexWrap: 'wrap',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <span style={{ fontSize: '1.25rem' }}>{res.resource_type === 'FILE' ? '📄' : '🔗'}</span>
                      <div>
                        <div style={{ fontWeight: 600, color: '#0F172A', fontSize: '0.875rem' }}>
                          {res.title}
                        </div>
                        {res.file_size_bytes && (
                          <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                            {res.file_name} • {(res.file_size_bytes / 1024 / 1024).toFixed(2)} MB
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      {res.resource_type === 'FILE' ? (
                        <button
                          onClick={() => {
                            void handleDownloadResource(res.id, res.file_name)
                          }}
                          disabled={downloadingResourceId === res.id}
                          style={{
                            backgroundColor: '#1E40AF',
                            color: '#FFFFFF',
                            border: 'none',
                            padding: '0.45rem 0.9rem',
                            borderRadius: '6px',
                            fontSize: '0.8125rem',
                            fontWeight: 700,
                            cursor: downloadingResourceId === res.id ? 'not-allowed' : 'pointer',
                          }}
                        >
                          {downloadingResourceId === res.id ? 'Descargando...' : 'Descargar Archivo ⬇'}
                        </button>
                      ) : res.url ? (
                        <a
                          href={res.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            backgroundColor: '#059669',
                            color: '#FFFFFF',
                            textDecoration: 'none',
                            padding: '0.45rem 0.9rem',
                            borderRadius: '6px',
                            fontSize: '0.8125rem',
                            fontWeight: 700,
                          }}
                        >
                          Abrir Enlace ↗
                        </a>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Feedback & Graded Section (if already graded) */}
          {isGraded && (
            <div
              style={{
                backgroundColor: '#F0FDF4',
                border: '1px solid #BBF7D0',
                borderRadius: '10px',
                padding: '1.25rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 800, color: '#15803D' }}>
                  🎯 Evaluación y Calificación Oficial
                </h4>
                {activity.score !== null && (
                  <span
                    style={{
                      fontSize: '1.15rem',
                      fontWeight: 800,
                      color: '#15803D',
                      backgroundColor: '#DCFCE7',
                      padding: '0.2rem 0.6rem',
                      borderRadius: '8px',
                      border: '1px solid #86EFAC',
                    }}
                  >
                    Nota: {Number(activity.score).toFixed(1)} / {Number(activity.max_score).toFixed(1)}
                  </span>
                )}
              </div>

              {activity.feedback ? (
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#166534', lineHeight: 1.5 }}>
                  "{activity.feedback}"
                </p>
              ) : (
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#166534', fontStyle: 'italic' }}>
                  Actividad calificada sin observaciones adicionales.
                </p>
              )}

              {activity.graded_at && (
                <div style={{ fontSize: '0.75rem', color: '#16A34A', marginTop: '0.5rem' }}>
                  Calificado el: {formatDateTime(activity.graded_at)}
                </div>
              )}
            </div>
          )}

          {/* ============================================================= */}
          {/* SECTION: MI ENTREGA (Phase B3-H13)                           */}
          {/* ============================================================= */}
          <div
            style={{
              backgroundColor: '#FAFAFA',
              border: '1px solid #CBD5E1',
              borderRadius: '12px',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '1.25rem' }}>📥</span>
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800, color: '#0F172A' }}>
                  Mi Entrega
                </h3>
                {currentAttempt && (
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      backgroundColor: '#E2E8F0',
                      color: '#334155',
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                    }}
                  >
                    Intento #{currentAttempt.attempt_number}
                  </span>
                )}
              </div>

              {/* Status Badge */}
              {currentAttempt && (
                <div>
                  {currentAttempt.status === 'DRAFT' && (
                    <span style={{ backgroundColor: '#FEF3C7', color: '#92400E', padding: '0.25rem 0.6rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 700 }}>
                      Borrador en edición
                    </span>
                  )}
                  {currentAttempt.status === 'SUBMITTED' && (
                    <span style={{ backgroundColor: '#DCFCE7', color: '#166534', padding: '0.25rem 0.6rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 700 }}>
                      ✓ Entregado
                    </span>
                  )}
                  {currentAttempt.status === 'LATE' && (
                    <span style={{ backgroundColor: '#FEE2E2', color: '#991B1B', padding: '0.25rem 0.6rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 700 }}>
                      ⚠️ Entrega Tardía
                    </span>
                  )}
                  {currentAttempt.status === 'RETURNED' && (
                    <span style={{ backgroundColor: '#FED7AA', color: '#9A3412', padding: '0.25rem 0.6rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 700 }}>
                      ↩ Devuelto para corrección
                    </span>
                  )}
                  {currentAttempt.status === 'GRADED' && (
                    <span style={{ backgroundColor: '#DCFCE7', color: '#15803D', padding: '0.25rem 0.6rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 700 }}>
                      ✓ Calificado
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Error or Success alerts */}
            {submissionError && (
              <div
                style={{
                  backgroundColor: '#FEF2F2',
                  border: '1px solid #F87171',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                  color: '#991B1B',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                }}
              >
                {submissionError}
              </div>
            )}

            {successMessage && (
              <div
                style={{
                  backgroundColor: '#F0FDF4',
                  border: '1px solid #4ADE80',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                  color: '#166534',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                }}
              >
                {successMessage}
              </div>
            )}

            {/* Loading submission state */}
            {loadingSubmission && (
              <div style={{ textAlign: 'center', padding: '1rem', color: '#64748B', fontSize: '0.875rem' }}>
                Cargando estado de entrega...
              </div>
            )}

            {/* Return feedback notification if previous attempt was returned */}
            {submission?.history && submission.history.some((h) => h.status === 'RETURNED') && isDraft && (
              <div
                style={{
                  backgroundColor: '#FFF7ED',
                  border: '1px solid #FDBA74',
                  borderRadius: '8px',
                  padding: '1rem',
                  color: '#9A3412',
                  fontSize: '0.875rem',
                }}
              >
                <strong style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.9rem' }}>
                  ⚠️ Retroalimentación del Docente al Devolver la Entrega:
                </strong>
                <p style={{ margin: '0 0 0.5rem 0', fontStyle: 'italic', lineHeight: 1.5 }}>
                  "{submission.history.slice().reverse().find((h) => h.status === 'RETURNED')?.return_feedback}"
                </p>
                <div style={{ fontSize: '0.75rem', color: '#C2410C' }}>
                  Corrige los puntos señalados por el docente y vuelve a presionar "Entregar Actividad".
                </div>
              </div>
            )}

            {/* Late Delivery Notice if past deadline */}
            {isPastDeadline && isDraft && (
              <div
                style={{
                  backgroundColor: '#FEF3C7',
                  border: '1px solid #FCD34D',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                  color: '#92400E',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                }}
              >
                ⚠️ La fecha límite ha vencido ({formatDateTime(activity.due_date)}). Si realizas la entrega ahora, quedará registrada como <strong>TARDÍA</strong>.
              </div>
            )}

            {!loadingSubmission && currentAttempt && (
              <>
                {/* 1. TEXT MODALITY: Textarea */}
                {(deliveryType === 'TEXT' || deliveryType === 'TEXT_AND_FILE') && (
                  <div>
                    <label
                      style={{
                        display: 'block',
                        fontWeight: 700,
                        color: '#334155',
                        fontSize: '0.875rem',
                        marginBottom: '0.35rem',
                      }}
                    >
                      {deliveryType === 'TEXT' ? 'Respuesta de Texto (Obligatoria):' : 'Respuesta o Comentario de Texto:'}
                    </label>

                    {canEdit ? (
                      <textarea
                        value={studentResponseText}
                        onChange={(e) => setStudentResponseText(e.target.value)}
                        placeholder="Escribe tu respuesta, solución o comentarios sobre la actividad aquí..."
                        rows={5}
                        maxLength={10000}
                        style={{
                          width: '100%',
                          padding: '0.75rem',
                          borderRadius: '8px',
                          border: '1px solid #CBD5E1',
                          fontSize: '0.875rem',
                          fontFamily: 'inherit',
                          lineHeight: 1.5,
                          boxSizing: 'border-box',
                          resize: 'vertical',
                        }}
                      />
                    ) : (
                      <div
                        style={{
                          backgroundColor: '#FFFFFF',
                          border: '1px solid #E2E8F0',
                          borderRadius: '8px',
                          padding: '0.75rem 1rem',
                          fontSize: '0.875rem',
                          color: currentAttempt.student_response ? '#0F172A' : '#94A3B8',
                          whiteSpace: 'pre-wrap',
                          lineHeight: 1.5,
                        }}
                      >
                        {currentAttempt.student_response || '(Sin respuesta de texto registrada)'}
                      </div>
                    )}
                  </div>
                )}

                {/* 2. FILE MODALITY: Attachments list & uploader */}
                {(deliveryType === 'FILE' || deliveryType === 'TEXT_AND_FILE') && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                      <label style={{ fontWeight: 700, color: '#334155', fontSize: '0.875rem' }}>
                        Archivos Adjuntos ({currentAttempt.attachments.length} / 3 máx):
                      </label>
                      <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
                        PDF, DOCX, XLSX, PPTX, TXT, ZIP, Imágenes (máx 10 MB)
                      </span>
                    </div>

                    {/* Uploaded Attachments List */}
                    {currentAttempt.attachments.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '0.75rem' }}>
                        {currentAttempt.attachments.map((att) => (
                          <div
                            key={att.id}
                            style={{
                              backgroundColor: '#FFFFFF',
                              border: '1px solid #E2E8F0',
                              borderRadius: '8px',
                              padding: '0.6rem 0.9rem',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              gap: '0.5rem',
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflow: 'hidden' }}>
                              <span>📄</span>
                              <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#0F172A' }}>
                                  {att.original_filename}
                                </span>
                                <span style={{ fontSize: '0.75rem', color: '#64748B', marginLeft: '0.5rem' }}>
                                  ({(att.file_size_bytes / 1024 / 1024).toFixed(2)} MB)
                                </span>
                              </div>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexShrink: 0 }}>
                              <button
                                onClick={() => {
                                  void handleDownloadAttachment(att.id, att.original_filename)
                                }}
                                disabled={downloadingAttachmentId === att.id}
                                style={{
                                  backgroundColor: '#EFF6FF',
                                  color: '#1D4ED8',
                                  border: '1px solid #BFDBFE',
                                  borderRadius: '6px',
                                  padding: '0.35rem 0.65rem',
                                  fontSize: '0.75rem',
                                  fontWeight: 700,
                                  cursor: downloadingAttachmentId === att.id ? 'not-allowed' : 'pointer',
                                }}
                              >
                                {downloadingAttachmentId === att.id ? 'Descargando...' : 'Descargar ⬇'}
                              </button>

                              {canEdit && (
                                <button
                                  onClick={() => {
                                    void handleDeleteAttachment(att.id)
                                  }}
                                  disabled={deletingAttachmentId === att.id}
                                  title="Eliminar archivo"
                                  style={{
                                    backgroundColor: '#FEF2F2',
                                    color: '#DC2626',
                                    border: '1px solid #FECACA',
                                    borderRadius: '6px',
                                    padding: '0.35rem 0.65rem',
                                    fontSize: '0.75rem',
                                    fontWeight: 700,
                                    cursor: deletingAttachmentId === att.id ? 'not-allowed' : 'pointer',
                                  }}
                                >
                                  {deletingAttachmentId === att.id ? '...' : 'Eliminar 🗑'}
                                </button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div
                        style={{
                          backgroundColor: '#F8FAFC',
                          border: '1px dashed #CBD5E1',
                          borderRadius: '8px',
                          padding: '1rem',
                          textAlign: 'center',
                          color: '#64748B',
                          fontSize: '0.8125rem',
                          marginBottom: '0.75rem',
                        }}
                      >
                        {canEdit
                          ? 'No has adjuntado archivos aún. Selecciona un archivo abajo para adjuntarlo.'
                          : 'No se adjuntaron archivos en esta entrega.'}
                      </div>
                    )}

                    {/* Upload file input (only when draft is editable and < 3 files) */}
                    {canEdit && currentAttempt.attachments.length < 3 && (
                      <div>
                        <label
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            backgroundColor: '#FFFFFF',
                            border: '1px solid #3B82F6',
                            color: '#1D4ED8',
                            padding: '0.45rem 0.9rem',
                            borderRadius: '6px',
                            fontSize: '0.8125rem',
                            fontWeight: 700,
                            cursor: uploadingFile ? 'not-allowed' : 'pointer',
                          }}
                        >
                          <span>{uploadingFile ? 'Subiendo archivo...' : '+ Adjuntar Archivo'}</span>
                          <input
                            type="file"
                            onChange={(e) => {
                              void handleFileUpload(e)
                            }}
                            disabled={uploadingFile}
                            style={{ display: 'none' }}
                            accept=".pdf,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.txt,.zip,.png,.jpg,.jpeg"
                          />
                        </label>
                      </div>
                    )}
                  </div>
                )}

                {/* 3. Action Buttons (Draft mode) */}
                {canEdit ? (
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                    <button
                      onClick={() => {
                        void handleSaveDraft()
                      }}
                      disabled={savingDraft || submitting}
                      style={{
                        backgroundColor: '#FFFFFF',
                        border: '1px solid #94A3B8',
                        color: '#334155',
                        padding: '0.55rem 1.1rem',
                        borderRadius: '8px',
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        cursor: savingDraft || submitting ? 'not-allowed' : 'pointer',
                      }}
                    >
                      {savingDraft ? 'Guardando...' : '💾 Guardar Borrador'}
                    </button>

                    <button
                      onClick={() => {
                        void handleSubmitActivity()
                      }}
                      disabled={submitting || savingDraft || uploadingFile}
                      style={{
                        backgroundColor: '#059669',
                        border: 'none',
                        color: '#FFFFFF',
                        padding: '0.55rem 1.25rem',
                        borderRadius: '8px',
                        fontSize: '0.875rem',
                        fontWeight: 700,
                        cursor: submitting || savingDraft || uploadingFile ? 'not-allowed' : 'pointer',
                        boxShadow: '0 2px 4px rgba(5, 150, 105, 0.25)',
                      }}
                    >
                      {submitting ? 'Enviando entrega...' : '🚀 Entregar Actividad'}
                    </button>
                  </div>
                ) : (
                  <div style={{ fontSize: '0.8125rem', color: '#64748B', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span>🔒</span>
                    <span>
                      {currentAttempt.submitted_at
                        ? `Entrega enviada el ${formatDateTime(currentAttempt.submitted_at)}. En espera de evaluación docente.`
                        : 'La actividad se encuentra cerrada o no admite modificaciones.'}
                    </span>
                  </div>
                )}
              </>
            )}

            {/* Past Attempts History (if multi-attempt exists) */}
            {submission && submission.history.length > 1 && (
              <div style={{ marginTop: '0.5rem', borderTop: '1px solid #E2E8F0', paddingTop: '0.75rem' }}>
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#2563EB',
                    fontSize: '0.8125rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    padding: 0,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                  }}
                >
                  <span>{showHistory ? '▼ Ocultar' : '▶ Ver'} historial de intentos anteriores ({submission.history.length})</span>
                </button>

                {showHistory && (
                  <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {submission.history.map((att: StudentSubmissionAttempt) => (
                      <div
                        key={att.id}
                        style={{
                          backgroundColor: '#FFFFFF',
                          border: '1px solid #E2E8F0',
                          borderRadius: '8px',
                          padding: '0.75rem 1rem',
                          fontSize: '0.8125rem',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                          <strong style={{ color: '#0F172A' }}>
                            Intento #{att.attempt_number}
                          </strong>
                          <span
                            style={{
                              backgroundColor: att.status === 'RETURNED' ? '#FED7AA' : '#DCFCE7',
                              color: att.status === 'RETURNED' ? '#9A3412' : '#166534',
                              padding: '0.15rem 0.5rem',
                              borderRadius: '4px',
                              fontWeight: 700,
                              fontSize: '0.75rem',
                            }}
                          >
                            {att.status}
                          </span>
                        </div>

                        {att.submitted_at && (
                          <div style={{ color: '#64748B', marginBottom: '0.3rem' }}>
                            Enviado: {formatDateTime(att.submitted_at)} {att.is_late && '⚠️ (Tardía)'}
                          </div>
                        )}

                        {att.student_response && (
                          <div style={{ backgroundColor: '#F8FAFC', padding: '0.5rem', borderRadius: '6px', marginBottom: '0.4rem' }}>
                            "{att.student_response}"
                          </div>
                        )}

                        {att.return_feedback && (
                          <div style={{ color: '#C2410C', fontStyle: 'italic', marginBottom: '0.4rem' }}>
                            Devolución del docente: "{att.return_feedback}"
                          </div>
                        )}

                        {att.attachments.length > 0 && (
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                            {att.attachments.map((a) => (
                              <button
                                key={a.id}
                                onClick={() => {
                                  void handleDownloadAttachment(a.id, a.original_filename)
                                }}
                                style={{
                                  backgroundColor: '#F1F5F9',
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
                )}
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
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
              padding: '0.6rem 1.25rem',
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
