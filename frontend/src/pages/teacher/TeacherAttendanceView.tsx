/**
 * PEVN Frontend — Teacher Daily Attendance View
 *
 * Provides daily attendance logging for assigned groups and subjects:
 * Present, Absent, Excused, Late with quick bulk actions and remarks.
 */

import React, { useEffect, useState } from 'react'
import type {
  AttendanceStatusEnum,
  DailyAttendanceBatchRequest,
  DailyAttendanceEntry,
  DailyAttendanceListResponse,
  TeacherAssignmentItemResponse,
} from '@/types/teacher'
import { teacherApi } from '@/services/teacher'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

interface Props {
  assignments: TeacherAssignmentItemResponse[]
}

export const TeacherAttendanceView: React.FC<Props> = ({ assignments }) => {
  // Extract unique groups
  const uniqueGroups = Array.from(
    new Map(assignments.map((a) => [a.group_id, { id: a.group_id, name: a.group_name }])).values()
  )

  const [selectedGroupId, setSelectedGroupId] = useState<string>(uniqueGroups[0]?.id || '')
  const [attendanceDate, setAttendanceDate] = useState<string>(new Date().toISOString().split('T')[0])
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('')

  const [sheet, setSheet] = useState<DailyAttendanceListResponse | null>(null)
  const [localStatuses, setLocalStatuses] = useState<Record<string, AttendanceStatusEnum>>({})
  const [localRemarks, setLocalRemarks] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // Subjects for the selected group
  const subjectsInGroup = assignments.filter((a) => a.group_id === selectedGroupId)

  const loadAttendance = async (grpId: string, attDate: string, subId?: string) => {
    if (!grpId || !attDate) return
    setLoading(true)
    setStatusMessage(null)
    try {
      const data = await teacherApi.getDailyAttendance(grpId, attDate, subId || undefined)
      setSheet(data)
      const stMap: Record<string, AttendanceStatusEnum> = {}
      const remMap: Record<string, string> = {}
      data.items.forEach((item) => {
        stMap[item.student_id] = item.status
        remMap[item.student_id] = item.remarks || ''
      })
      setLocalStatuses(stMap)
      setLocalRemarks(remMap)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar la planilla de asistencia.'
      setStatusMessage({ type: 'error', text: msg })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!selectedGroupId && uniqueGroups.length > 0) {
      setSelectedGroupId(uniqueGroups[0].id)
    }
  }, [uniqueGroups, selectedGroupId])

  useEffect(() => {
    if (selectedGroupId && attendanceDate) {
      void loadAttendance(selectedGroupId, attendanceDate, selectedSubjectId)
    }
  }, [selectedGroupId, attendanceDate, selectedSubjectId])

  const handleMarkAllPresent = () => {
    if (!sheet) return
    const updated: Record<string, AttendanceStatusEnum> = {}
    sheet.items.forEach((item) => {
      updated[item.student_id] = 'PRESENT'
    })
    setLocalStatuses(updated)
  }

  const handleStatusChange = (studentId: string, status: AttendanceStatusEnum) => {
    setLocalStatuses((prev) => ({ ...prev, [studentId]: status }))
  }

  const handleRemarkChange = (studentId: string, remark: string) => {
    setLocalRemarks((prev) => ({ ...prev, [studentId]: remark }))
  }

  const handleSaveAttendance = async () => {
    if (!sheet) return
    setStatusMessage(null)

    const records: DailyAttendanceEntry[] = sheet.items.map((item) => ({
      student_id: item.student_id,
      status: localStatuses[item.student_id] || 'PRESENT',
      remarks: localRemarks[item.student_id]?.trim() || null,
    }))

    const payload: DailyAttendanceBatchRequest = {
      subject_id: selectedSubjectId || null,
      attendance_date: attendanceDate,
      records,
    }

    setSaving(true)
    try {
      const updated = await teacherApi.recordDailyAttendance(sheet.group_id, payload)
      setSheet(updated)
      setStatusMessage({ type: 'success', text: '¡Asistencia escolar registrada y guardada exitosamente!' })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al registrar asistencia.'
      setStatusMessage({ type: 'error', text: msg })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
          Control Diario de Asistencia Escolar
        </h2>
        <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
          Registre y actualice la asistencia diaria de los estudiantes por grupo y fecha escolar.
        </p>
      </div>

      {/* Control Filters Bar */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          padding: '1.25rem',
          border: '1px solid #E2E8F0',
          marginBottom: '1.5rem',
          display: 'flex',
          gap: '1rem',
          flexWrap: 'wrap',
          alignItems: 'flex-end',
        }}
      >
        <div style={{ minWidth: '200px' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
            Grupo / Salón: *
          </label>
          <select
            value={selectedGroupId}
            onChange={(e) => setSelectedGroupId(e.target.value)}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
          >
            {uniqueGroups.map((g) => (
              <option key={g.id} value={g.id}>Grupo {g.name}</option>
            ))}
          </select>
        </div>

        <div style={{ minWidth: '180px' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
            Fecha de la Sesión: *
          </label>
          <input
            type="date"
            value={attendanceDate}
            onChange={(e) => setAttendanceDate(e.target.value)}
            style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem', boxSizing: 'border-box' }}
          />
        </div>

        <div style={{ minWidth: '200px' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
            Materia (Opcional):
          </label>
          <select
            value={selectedSubjectId}
            onChange={(e) => setSelectedSubjectId(e.target.value)}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
          >
            <option value="">Todas / Sesión General</option>
            {subjectsInGroup.map((s) => (
              <option key={s.subject_id} value={s.subject_id}>{s.subject_name}</option>
            ))}
          </select>
        </div>

        {sheet && sheet.items.length > 0 && (
          <div style={{ display: 'flex', gap: '0.5rem', marginLeft: 'auto' }}>
            <Button variant="secondary" onClick={handleMarkAllPresent}>
              ✅ Marcar Todos Presentes
            </Button>
            <Button variant="primary" onClick={handleSaveAttendance} disabled={saving || loading}>
              {saving ? 'Guardando...' : '💾 Guardar Asistencia'}
            </Button>
          </div>
        )}
      </div>

      {statusMessage && (
        <div
          style={{
            padding: '0.875rem 1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            fontSize: '0.875rem',
            backgroundColor: statusMessage.type === 'success' ? '#F0FDF4' : '#FEF2F2',
            border: `1px solid ${statusMessage.type === 'success' ? '#86EFAC' : '#FCA5A5'}`,
            color: statusMessage.type === 'success' ? '#166534' : '#991B1B',
          }}
        >
          {statusMessage.text}
        </div>
      )}

      {/* Attendance Sheet Table */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
          padding: '1.5rem',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
        }}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <LoadingSpinner />
            <p style={{ marginTop: '0.5rem', color: '#64748B', fontSize: '0.875rem' }}>Cargando planilla de asistencia...</p>
          </div>
        ) : !sheet || sheet.items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#64748B' }}>
            No hay estudiantes activos matriculados en este grupo.
          </div>
        ) : (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', paddingBottom: '0.75rem', borderBottom: '1px solid #F1F5F9' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 800, color: '#0F172A' }}>
                  Planilla de Asistencia — Grupo {sheet.group_name} ({attendanceDate})
                </h3>
                {sheet.subject_name && (
                  <div style={{ fontSize: '0.8125rem', color: '#1E40AF', marginTop: '0.2rem' }}>
                    Asignatura: {sheet.subject_name}
                  </div>
                )}
              </div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#475569' }}>
                Total Estudiantes: {sheet.total_students}
              </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                    <th style={{ padding: '0.625rem 0.75rem' }}>#</th>
                    <th style={{ padding: '0.625rem 0.75rem' }}>Estudiante</th>
                    <th style={{ padding: '0.625rem 0.75rem' }}>Documento</th>
                    <th style={{ padding: '0.625rem 0.75rem', width: '320px' }}>Estado de Asistencia</th>
                    <th style={{ padding: '0.625rem 0.75rem' }}>Observaciones</th>
                  </tr>
                </thead>
                <tbody>
                  {sheet.items.map((item, idx) => (
                    <tr key={item.student_id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                      <td style={{ padding: '0.625rem 0.75rem', color: '#94A3B8', fontWeight: 600 }}>
                        {idx + 1}
                      </td>
                      <td style={{ padding: '0.625rem 0.75rem', fontWeight: 600, color: '#0F172A' }}>
                        {item.student_name}
                      </td>
                      <td style={{ padding: '0.625rem 0.75rem', color: '#64748B', fontSize: '0.8125rem' }}>
                        {item.document_number}
                      </td>
                      <td style={{ padding: '0.625rem 0.75rem' }}>
                        <div style={{ display: 'flex', gap: '0.4rem' }}>
                          {(['PRESENT', 'ABSENT', 'EXCUSED', 'LATE'] as AttendanceStatusEnum[]).map((st) => {
                            const isSelected = (localStatuses[item.student_id] || 'PRESENT') === st
                            let bg = '#F1F5F9'
                            let color = '#475569'
                            let label = 'Presente'

                            if (st === 'PRESENT') {
                              label = 'Presente'
                              if (isSelected) { bg = '#DCFCE7'; color = '#15803D' }
                            } else if (st === 'ABSENT') {
                              label = 'Ausente'
                              if (isSelected) { bg = '#FEE2E2'; color = '#B91C1C' }
                            } else if (st === 'EXCUSED') {
                              label = 'Excusa'
                              if (isSelected) { bg = '#FEF3C7'; color = '#B45309' }
                            } else if (st === 'LATE') {
                              label = 'Tardanza'
                              if (isSelected) { bg = '#E0E7FF'; color = '#4338CA' }
                            }

                            return (
                              <button
                                key={st}
                                type="button"
                                onClick={() => handleStatusChange(item.student_id, st)}
                                style={{
                                  padding: '0.25rem 0.5rem',
                                  borderRadius: '6px',
                                  fontSize: '0.75rem',
                                  fontWeight: 700,
                                  border: isSelected ? `2px solid ${color}` : '1px solid #CBD5E1',
                                  backgroundColor: bg,
                                  color,
                                  cursor: 'pointer',
                                }}
                              >
                                {label}
                              </button>
                            )
                          })}
                        </div>
                      </td>
                      <td style={{ padding: '0.625rem 0.75rem' }}>
                        <input
                          type="text"
                          value={localRemarks[item.student_id] ?? ''}
                          onChange={(e) => handleRemarkChange(item.student_id, e.target.value)}
                          placeholder="Nota u observación..."
                          style={{
                            width: '100%',
                            padding: '0.35rem 0.5rem',
                            borderRadius: '6px',
                            border: '1px solid #CBD5E1',
                            fontSize: '0.8125rem',
                            boxSizing: 'border-box',
                          }}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="primary" onClick={handleSaveAttendance} disabled={saving || loading}>
                {saving ? 'Guardando...' : '💾 Guardar Asistencia'}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
