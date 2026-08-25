/**
 * PEVN Frontend — Students View
 *
 * Student profiles, SIMAT identification, inclusion metadata,
 * and linked guardian relationships.
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
  StudentCreateRequest,
  StudentGender,
  StudentGuardianResponse,
  StudentResponse,
} from '@/types'

export const StudentsView: React.FC = () => {
  const { hasPermission } = useAuth()

  const [students, setStudents] = useState<StudentResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [simatSearch, setSimatSearch] = useState<string>('')
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Create Student Modal
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [userId, setUserId] = useState<string>('')
  const [codeSimat, setCodeSimat] = useState<string>('')
  const [birthDate, setBirthDate] = useState<string>('2010-01-01')
  const [gender, setGender] = useState<StudentGender>('M')
  const [bloodType, setBloodType] = useState<string>('O+')
  const [stratum, setStratum] = useState<number>(2)
  const [eps, setEps] = useState<string>('Nueva EPS')
  const [hasDisability, setHasDisability] = useState<boolean>(false)
  const [disabilityType, setDisabilityType] = useState<string>('')

  // View Guardians Modal
  const [guardiansModal, setGuardiansModal] = useState<{
    isOpen: boolean
    student: StudentResponse | null
    guardians: StudentGuardianResponse[]
    isLoading: boolean
  }>({
    isOpen: false,
    student: null,
    guardians: [],
    isLoading: false,
  })

  const loadStudents = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await academicApi.listStudents(simatSearch.trim() || undefined)
      setStudents(data.items)
      setTotal(data.total)
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al cargar lista de estudiantes'))
    } finally {
      setIsLoading(false)
    }
  }, [simatSearch])

  useEffect(() => {
    void loadStudents()
  }, [loadStudents])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    void loadStudents()
  }

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)

    const payload: StudentCreateRequest = {
      user_id: userId.trim(),
      code_simat: codeSimat.trim(),
      birth_date: birthDate,
      gender,
      blood_type: bloodType.trim() || null,
      stratum: stratum || null,
      eps_health_provider: eps.trim() || null,
      has_disability: hasDisability,
      disability_type: hasDisability ? disabilityType.trim() || null : null,
    }

    try {
      await academicApi.createStudent(payload)
      setSuccessMsg(`Perfil estudiantil con código SIMAT ${payload.code_simat} creado exitosamente.`)
      setIsCreateOpen(false)
      setUserId('')
      setCodeSimat('')
      await loadStudents()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al crear perfil de estudiante'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleViewGuardians = async (student: StudentResponse) => {
    setGuardiansModal({
      isOpen: true,
      student,
      guardians: [],
      isLoading: true,
    })
    try {
      const list = await academicApi.getStudentGuardians(student.id)
      setGuardiansModal({
        isOpen: true,
        student,
        guardians: list,
        isLoading: false,
      })
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al consultar acudientes'))
      setGuardiansModal({ isOpen: false, student: null, guardians: [], isLoading: false })
    }
  }

  return (
    <div>
      {/* Notifications */}
      {error && <Alert error={error} onClose={() => { setError(null) }} />}
      {successMsg && (
        <Alert variant="success" message={successMsg} onClose={() => { setSuccessMsg(null) }} />
      )}

      {/* Action Bar & Search */}
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
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Buscar por código SIMAT..."
            value={simatSearch}
            onChange={(e) => {
              setSimatSearch(e.target.value)
            }}
            style={{
              padding: '0.45rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              fontSize: '0.875rem',
              width: '240px',
            }}
          />
          <Button type="submit" variant="secondary" size="sm">
            Buscar
          </Button>
          {simatSearch && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => {
                setSimatSearch('')
              }}
            >
              Limpiar
            </Button>
          )}
        </form>

        {hasPermission('students:create') && (
          <Button
            variant="primary"
            onClick={() => {
              setIsCreateOpen(true)
            }}
          >
            + Registrar Estudiante
          </Button>
        )}
      </div>

      {/* Table Card */}
      <Card
        title="Estudiantes Matriculados y Registrados"
        subtitle={`Total de estudiantes: ${String(total)}`}
        action={
          <Button variant="secondary" size="sm" onClick={() => void loadStudents()}>
            Refrescar
          </Button>
        }
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando estudiantes...
            </p>
          </div>
        ) : students.length === 0 ? (
          <EmptyState
            icon="🎓"
            title="No se encontraron estudiantes"
            description="No hay estudiantes registrados que coincidan con la búsqueda."
            actionLabel={hasPermission('students:create') ? '+ Registrar Primer Estudiante' : undefined}
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
                  <th style={{ padding: '0.75rem 1rem' }}>Código SIMAT</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Nombre / Usuario</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Nacimiento</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Género / RH</th>
                  <th style={{ padding: '0.75rem 1rem' }}>EPS / Estrato</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {students.map((s) => (
                  <tr key={s.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#1E40AF' }}>
                      <code>{s.code_simat}</code>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#0F172A', fontWeight: 500 }}>
                      {s.user ? `${s.user.first_name} ${s.user.last_name}` : s.user_id}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#475569' }}>{s.birth_date}</td>
                    <td style={{ padding: '0.875rem 1rem', color: '#475569' }}>
                      <Badge variant="neutral" size="sm">
                        {s.gender}
                      </Badge>{' '}
                      {s.blood_type && (
                        <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>({s.blood_type})</span>
                      )}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#64748B' }}>
                      {s.eps_health_provider || 'Sin EPS'} (Est. {s.stratum ?? 'N/A'})
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => void handleViewGuardians(s)}
                      >
                        Acudientes
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Linked Guardians Modal */}
      <Modal
        isOpen={guardiansModal.isOpen}
        onClose={() => {
          setGuardiansModal({ isOpen: false, student: null, guardians: [], isLoading: false })
        }}
        title={`Acudientes — Estudiante ${guardiansModal.student?.code_simat ?? ''}`}
        subtitle="Contactos autorizados y responsables civiles del estudiante."
      >
        {guardiansModal.isLoading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <LoadingSpinner size="md" />
            <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '0.5rem' }}>
              Consultando vínculos familiares...
            </p>
          </div>
        ) : guardiansModal.guardians.length === 0 ? (
          <EmptyState
            icon="👨‍👩‍👧"
            title="Sin acudientes vinculados"
            description="El estudiante no tiene acudientes registrados en la institución."
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {guardiansModal.guardians.map((g) => (
              <div
                key={g.id}
                style={{
                  padding: '1rem',
                  backgroundColor: '#F8FAFC',
                  borderRadius: '8px',
                  border: '1px solid #E2E8F0',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ fontWeight: 700, color: '#0F172A', marginBottom: '0.25rem' }}>
                    {g.guardian ? `${g.guardian.first_name} ${g.guardian.last_name}` : g.guardian_id}
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                    Parentesco: <strong>{g.relationship_type}</strong> • Tel:{' '}
                    {g.guardian?.phone || 'N/A'}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.35rem' }}>
                  {g.is_primary_contact && <Badge variant="primary" size="sm">Principal</Badge>}
                  {g.is_authorized_pickup && <Badge variant="success" size="sm">Retiro Autorizado</Badge>}
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>

      {/* Create Student Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false)
        }}
        title="Registrar Perfil de Estudiante"
        subtitle="Vincule una cuenta de usuario existente con su información escolar SIMAT."
      >
        <form onSubmit={(e) => void handleCreateStudent(e)}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              ID de Usuario Institucional (User Account UUID) *
            </label>
            <input
              type="text"
              value={userId}
              onChange={(e) => {
                setUserId(e.target.value)
              }}
              required
              placeholder="UUID del usuario asignado como estudiante"
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Código Nacional SIMAT *
              </label>
              <input
                type="text"
                value={codeSimat}
                onChange={(e) => {
                  setCodeSimat(e.target.value)
                }}
                required
                placeholder="SIMAT-2026-XXXX"
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Fecha de Nacimiento *
              </label>
              <input
                type="date"
                value={birthDate}
                onChange={(e) => {
                  setBirthDate(e.target.value)
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Género *
              </label>
              <select
                value={gender}
                onChange={(e) => {
                  setGender(e.target.value as StudentGender)
                }}
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              >
                <option value="M">Masculino</option>
                <option value="F">Femenino</option>
                <option value="OTHER">Otro</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Grupo RH
              </label>
              <input
                type="text"
                value={bloodType}
                onChange={(e) => {
                  setBloodType(e.target.value)
                }}
                placeholder="O+, A+, etc."
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Estrato (1 - 6)
              </label>
              <input
                type="number"
                min={1}
                max={6}
                value={stratum}
                onChange={(e) => {
                  setStratum(Number(e.target.value))
                }}
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Entidad Prestadora de Salud (EPS)
            </label>
            <input
              type="text"
              value={eps}
              onChange={(e) => {
                setEps(e.target.value)
              }}
              placeholder="Nueva EPS, Sura, etc."
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: '#334155', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={hasDisability}
                onChange={(e) => {
                  setHasDisability(e.target.checked)
                }}
              />
              <strong>Estudiante con condición de inclusión / discapacidad</strong>
            </label>
            {hasDisability && (
              <input
                type="text"
                value={disabilityType}
                onChange={(e) => {
                  setDisabilityType(e.target.value)
                }}
                placeholder="Describa la condición de inclusión"
                style={{ marginTop: '0.5rem', width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            )}
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
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Guardar Estudiante'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default StudentsView
