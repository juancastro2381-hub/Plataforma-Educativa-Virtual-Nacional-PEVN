/**
 * PEVN Frontend — Students View
 *
 * Student profiles, SIMAT identification, inclusion metadata,
 * login account lifecycle, and bidirectional guardian relationship management.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { academicApi } from '@/services/academic'
import { usersApi } from '@/services/users'
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
  AssociateGuardianRequest,
  GuardianRelationshipType,
  GuardianResponse,
  StudentAccountStatus,
  StudentCreateRequest,
  StudentGender,
  StudentGuardianResponse,
  StudentResponse,
  UserResponse,
} from '@/types'

export const StudentsView: React.FC = () => {
  const { hasPermission } = useAuth()

  const [students, setStudents] = useState<StudentResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [simatSearch, setSimatSearch] = useState<string>('')
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Catalogs
  const [guardiansCatalog, setGuardiansCatalog] = useState<GuardianResponse[]>([])

  // Action Loading ID
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null)

  // Create Student Modal & User Search / Provisioning
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [modalError, setModalError] = useState<ApiError | Error | null>(null)
  const [userSearchQuery, setUserSearchQuery] = useState<string>('')
  const [userSearchResults, setUserSearchResults] = useState<UserResponse[]>([])
  const [isSearchingUsers, setIsSearchingUsers] = useState<boolean>(false)
  const [selectedUser, setSelectedUser] = useState<UserResponse | null>(null)
  const [isRegisteringNewUser, setIsRegisteringNewUser] = useState<boolean>(false)
  const [newFirstName, setNewFirstName] = useState<string>('')
  const [newLastName, setNewLastName] = useState<string>('')
  const [newDocType, setNewDocType] = useState<string>('TI')
  const [newDocNumber, setNewDocNumber] = useState<string>('')
  const [newEmail, setNewEmail] = useState<string>('')
  const [newPhone, setNewPhone] = useState<string>('')
  const [codeSimat, setCodeSimat] = useState<string>('')
  const [birthDate, setBirthDate] = useState<string>('2010-01-01')
  const [gender, setGender] = useState<StudentGender>('M')
  const [bloodType, setBloodType] = useState<string>('O+')
  const [stratum, setStratum] = useState<number>(2)
  const [eps, setEps] = useState<string>('Nueva EPS')
  const [hasDisability, setHasDisability] = useState<boolean>(false)
  const [disabilityType, setDisabilityType] = useState<string>('')

  // View / Manage Guardians Modal
  const [guardiansModal, setGuardiansModal] = useState<{
    isOpen: boolean
    student: StudentResponse | null
    guardians: StudentGuardianResponse[]
    isLoading: boolean
    isLinkingNew: boolean
    selectedGuardianId: string
    relType: GuardianRelationshipType
    isPrimary: boolean
    isAuthorizedPickup: boolean
    isLinkingSubmitting: boolean
  }>({
    isOpen: false,
    student: null,
    guardians: [],
    isLoading: false,
    isLinkingNew: false,
    selectedGuardianId: '',
    relType: 'MADRE',
    isPrimary: false,
    isAuthorizedPickup: true,
    isLinkingSubmitting: false,
  })

  // Unlink Confirmation Dialog
  const [unlinkDialog, setUnlinkDialog] = useState<{
    isOpen: boolean
    studentId: string
    guardianId: string
    guardianName: string
    isSubmitting: boolean
  }>({
    isOpen: false,
    studentId: '',
    guardianId: '',
    guardianName: '',
    isSubmitting: false,
  })

  // Setup / Reset Token Delivery Modal
  const [tokenModal, setTokenModal] = useState<{
    isOpen: boolean
    title: string
    recipientName: string
    recipientEmail: string
    token: string
    isCopied: boolean
  }>({
    isOpen: false,
    title: '',
    recipientName: '',
    recipientEmail: '',
    token: '',
    isCopied: false,
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

  const loadGuardiansCatalog = useCallback(async () => {
    try {
      const res = await academicApi.listGuardians()
      setGuardiansCatalog(res.items || [])
    } catch {
      // Non-critical catalog fallback
    }
  }, [])

  useEffect(() => {
    void loadStudents()
    void loadGuardiansCatalog()
  }, [loadStudents, loadGuardiansCatalog])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    void loadStudents()
  }

  const handleSearchUsers = async (query: string) => {
    setUserSearchQuery(query)
    const trimmed = query.trim()
    if (trimmed.length < 2) {
      setUserSearchResults([])
      return
    }
    setIsSearchingUsers(true)
    try {
      const res = await usersApi.searchUsers({ search: trimmed, page_size: 6 })
      setUserSearchResults(res.items || [])
    } catch {
      setUserSearchResults([])
    } finally {
      setIsSearchingUsers(false)
    }
  }

  const resetCreateForm = () => {
    setSelectedUser(null)
    setUserSearchQuery('')
    setUserSearchResults([])
    setIsRegisteringNewUser(false)
    setNewFirstName('')
    setNewLastName('')
    setNewDocNumber('')
    setNewEmail('')
    setNewPhone('')
    setCodeSimat('')
    setBirthDate('2010-01-01')
    setGender('M')
    setBloodType('O+')
    setStratum(2)
    setEps('Nueva EPS')
    setHasDisability(false)
    setDisabilityType('')
    setModalError(null)
  }

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setModalError(null)
    setError(null)
    setSuccessMsg(null)

    if (!isRegisteringNewUser && !selectedUser) {
      setModalError(new Error('Debe seleccionar una cuenta de usuario existente o aprovisionar una nueva.'))
      setIsSubmitting(false)
      return
    }

    const payload: StudentCreateRequest = {
      code_simat: codeSimat.trim(),
      birth_date: birthDate,
      gender,
      blood_type: bloodType,
      stratum,
      eps_health_provider: eps.trim() || null,
      has_disability: hasDisability,
      disability_type: hasDisability ? disabilityType.trim() : null,
    }

    if (isRegisteringNewUser) {
      payload.new_user = {
        first_name: newFirstName.trim(),
        last_name: newLastName.trim(),
        document_type: newDocType,
        document_number: newDocNumber.trim(),
        email: newEmail.trim(),
        phone: newPhone.trim() || null,
      }
    } else if (selectedUser) {
      payload.user_id = selectedUser.id
    }

    try {
      const created = await academicApi.createStudent(payload)
      setSuccessMsg(`Estudiante ${created.code_simat} registrado exitosamente.`)
      setIsCreateOpen(false)
      resetCreateForm()
      await loadStudents()
    } catch (err: unknown) {
      setModalError(err instanceof Error ? err : new Error('Error al registrar estudiante'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleProvisionAccount = async (s: StudentResponse) => {
    setActionLoadingId(s.id)
    setError(null)
    setSuccessMsg(null)
    try {
      const res = await academicApi.provisionStudentAccount(s.id)
      setSuccessMsg(`Cuenta de acceso aprovisionada exitosamente para el estudiante SIMAT ${s.code_simat}.`)
      if (res.reset_token) {
        setTokenModal({
          isOpen: true,
          title: 'Configuración Inicial de Cuenta de Estudiante',
          recipientName: s.user ? `${s.user.first_name} ${s.user.last_name}` : s.code_simat,
          recipientEmail: s.user?.email || s.account_email || 'Sin correo institucional',
          token: res.reset_token,
          isCopied: false,
        })
      }
      await loadStudents()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al aprovisionar cuenta de estudiante'))
    } finally {
      setActionLoadingId(null)
    }
  }

  const handleToggleAccountStatus = async (s: StudentResponse) => {
    const isCurrentlyActive = s.account_status === 'ACTIVA'
    const targetState = !isCurrentlyActive
    setActionLoadingId(s.id)
    setError(null)
    setSuccessMsg(null)
    try {
      await academicApi.updateStudentAccountStatus(s.id, targetState)
      setSuccessMsg(
        `Cuenta de acceso ${targetState ? 'habilitada' : 'deshabilitada'} para el estudiante SIMAT ${s.code_simat}.`
      )
      await loadStudents()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al actualizar estado de la cuenta'))
    } finally {
      setActionLoadingId(null)
    }
  }

  const handleResetPassword = async (s: StudentResponse) => {
    setActionLoadingId(s.id)
    setError(null)
    setSuccessMsg(null)
    try {
      const res = await academicApi.resetStudentPassword(s.id)
      setSuccessMsg(`Token de restablecimiento generado para el estudiante SIMAT ${s.code_simat}.`)
      if (res.reset_token) {
        setTokenModal({
          isOpen: true,
          title: 'Restablecimiento de Contraseña de Estudiante',
          recipientName: s.user ? `${s.user.first_name} ${s.user.last_name}` : s.code_simat,
          recipientEmail: s.user?.email || s.account_email || 'Sin correo institucional',
          token: res.reset_token,
          isCopied: false,
        })
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al restablecer contraseña de estudiante'))
    } finally {
      setActionLoadingId(null)
    }
  }

  const handleViewGuardians = async (student: StudentResponse) => {
    setGuardiansModal({
      isOpen: true,
      student,
      guardians: [],
      isLoading: true,
      isLinkingNew: false,
      selectedGuardianId: '',
      relType: 'MADRE',
      isPrimary: false,
      isAuthorizedPickup: true,
      isLinkingSubmitting: false,
    })
    try {
      const data = await academicApi.getStudentGuardians(student.id)
      setGuardiansModal((prev) => ({
        ...prev,
        guardians: data,
        isLoading: false,
      }))
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al consultar acudientes'))
      setGuardiansModal((prev) => ({ ...prev, isLoading: false }))
    }
  }

  const handleLinkGuardianSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!guardiansModal.student || !guardiansModal.selectedGuardianId) return

    setGuardiansModal((prev) => ({ ...prev, isLinkingSubmitting: true }))
    setError(null)
    setSuccessMsg(null)

    const payload: AssociateGuardianRequest = {
      relationship_type: guardiansModal.relType,
      is_primary_contact: guardiansModal.isPrimary,
      is_authorized_pickup: guardiansModal.isAuthorizedPickup,
    }

    try {
      await academicApi.associateGuardianFromStudent(
        guardiansModal.student.id,
        guardiansModal.selectedGuardianId,
        payload
      )
      setSuccessMsg('Acudiente vinculado exitosamente al estudiante.')
      const refreshed = await academicApi.getStudentGuardians(guardiansModal.student.id)
      setGuardiansModal((prev) => ({
        ...prev,
        guardians: refreshed,
        isLinkingNew: false,
        selectedGuardianId: '',
        isLinkingSubmitting: false,
      }))
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al vincular acudiente'))
      setGuardiansModal((prev) => ({ ...prev, isLinkingSubmitting: false }))
    }
  }

  const handleConfirmUnlink = async () => {
    if (!unlinkDialog.studentId || !unlinkDialog.guardianId) return
    setUnlinkDialog((prev) => ({ ...prev, isSubmitting: true }))
    setError(null)
    setSuccessMsg(null)

    try {
      await academicApi.dissociateGuardianFromStudent(unlinkDialog.studentId, unlinkDialog.guardianId)
      setSuccessMsg('Acudiente desvinculado exitosamente.')
      setUnlinkDialog({
        isOpen: false,
        studentId: '',
        guardianId: '',
        guardianName: '',
        isSubmitting: false,
      })
      if (guardiansModal.student) {
        const refreshed = await academicApi.getStudentGuardians(guardiansModal.student.id)
        setGuardiansModal((prev) => ({ ...prev, guardians: refreshed }))
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al desvincular acudiente'))
    } finally {
      setUnlinkDialog((prev) => ({ ...prev, isSubmitting: false }))
    }
  }

  const getStatusBadge = (status?: StudentAccountStatus) => {
    switch (status) {
      case 'ACTIVA':
        return <Badge variant="success" size="sm">Cuenta Activa</Badge>
      case 'INACTIVA':
        return <Badge variant="danger" size="sm">Cuenta Inactiva</Badge>
      default:
        return <Badge variant="neutral" size="sm">Sin Cuenta</Badge>
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header & Feedback */}
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
          Padrón de Estudiantes & Cuentas de Acceso
        </h1>
        <p style={{ color: '#64748B', fontSize: '0.875rem', marginTop: '0.25rem' }}>
          Matrícula oficial SIMAT, ciclo de vida de cuentas de acceso y vinculación familiar simétrica.
        </p>
      </div>

      {error && (
        <Alert
          error={error}
          onClose={() => {
            setError(null)
          }}
        />
      )}

      {successMsg && (
        <Alert
          variant="success"
          onClose={() => {
            setSuccessMsg(null)
          }}
        >
          {successMsg}
        </Alert>
      )}

      {/* Action Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
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
        title="Censo Institucional de Estudiantes (Rectoría / SIMAT)"
        subtitle={`Padrón escolar oficial de la institución: ${String(total)} estudiantes registrados.`}
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
                  <th style={{ padding: '0.75rem 1rem' }}>Nombre Completo</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Correo Institucional</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Estado de Cuenta</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Datos Demográficos</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {students.map((s) => (
                  <tr key={s.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#1E40AF' }}>
                      <code>{s.code_simat}</code>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#0F172A', fontWeight: 600 }}>
                      {s.user ? `${s.user.first_name} ${s.user.last_name}` : s.user_id}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#64748B' }}>
                      {s.user?.email || s.account_email || 'Sin correo asignado'}
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      {getStatusBadge(s.account_status)}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#475569' }}>
                      <Badge variant="neutral" size="sm">{s.gender}</Badge>{' '}
                      {s.blood_type && <strong>({s.blood_type})</strong>} • Est. {s.stratum ?? 'N/A'}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                        {/* Guardians Modal Button */}
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => void handleViewGuardians(s)}
                        >
                          👥 Acudientes
                        </Button>

                        {/* Account Lifecycle Actions */}
                        {(!s.account_status || s.account_status === 'SIN_CUENTA') && hasPermission('students:update') && (
                          <Button
                            variant="primary"
                            size="sm"
                            disabled={actionLoadingId === s.id}
                            onClick={() => void handleProvisionAccount(s)}
                          >
                            + Aprovisionar Acceso
                          </Button>
                        )}

                        {s.account_status && s.account_status !== 'SIN_CUENTA' && hasPermission('students:update') && (
                          <>
                            <Button
                              variant="secondary"
                              size="sm"
                              disabled={actionLoadingId === s.id}
                              onClick={() => void handleToggleAccountStatus(s)}
                            >
                              {s.account_status === 'ACTIVA' ? 'Desactivar' : 'Activar'}
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              disabled={actionLoadingId === s.id || s.account_status === 'INACTIVA'}
                              onClick={() => void handleResetPassword(s)}
                            >
                              🔑 Restablecer
                            </Button>
                          </>
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

      {/* VIEW & LINK GUARDIANS MODAL */}
      <Modal
        isOpen={guardiansModal.isOpen}
        onClose={() => {
          setGuardiansModal({
            isOpen: false,
            student: null,
            guardians: [],
            isLoading: false,
            isLinkingNew: false,
            selectedGuardianId: '',
            relType: 'MADRE',
            isPrimary: false,
            isAuthorizedPickup: true,
            isLinkingSubmitting: false,
          })
        }}
        title={`Acudientes del Estudiante — SIMAT ${guardiansModal.student?.code_simat ?? ''}`}
        subtitle="Contactos familiares autorizados y responsables civiles."
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Action Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8125rem', color: '#64748B', fontWeight: 600 }}>
              Acudientes Vinculados ({guardiansModal.guardians.length})
            </span>
            {hasPermission('guardians:link_student') && !guardiansModal.isLinkingNew && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setGuardiansModal((prev) => ({ ...prev, isLinkingNew: true }))}
              >
                + Vincular Acudiente
              </Button>
            )}
          </div>

          {/* Form to link a new guardian */}
          {guardiansModal.isLinkingNew && (
            <form
              onSubmit={(e) => void handleLinkGuardianSubmit(e)}
              style={{
                backgroundColor: '#EFF6FF',
                padding: '0.875rem',
                borderRadius: '8px',
                border: '1px solid #BFDBFE',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
              }}
            >
              <div style={{ fontWeight: 700, fontSize: '0.875rem', color: '#1E40AF' }}>
                Vincular Acudiente a este Estudiante
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#334155', marginBottom: '0.2rem' }}>
                  Seleccione el Acudiente Registrado *
                </label>
                <select
                  required
                  value={guardiansModal.selectedGuardianId}
                  onChange={(e) => setGuardiansModal((prev) => ({ ...prev, selectedGuardianId: e.target.value }))}
                  style={{ width: '100%', padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid #93C5FD' }}
                >
                  <option value="">-- Seleccione un acudiente --</option>
                  {guardiansCatalog.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.first_name} {g.last_name} ({g.document_type} {g.document_number}) - Tel: {g.phone}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#334155', marginBottom: '0.2rem' }}>
                  Parentesco con este estudiante *
                </label>
                <select
                  value={guardiansModal.relType}
                  onChange={(e) => setGuardiansModal((prev) => ({ ...prev, relType: e.target.value as GuardianRelationshipType }))}
                  style={{ width: '100%', padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid #93C5FD' }}
                >
                  <option value="MADRE">Madre</option>
                  <option value="PADRE">Padre</option>
                  <option value="TUTOR_LEGAL">Tutor Legal</option>
                  <option value="ABUELO_A">Abuelo / Abuela</option>
                  <option value="TIO_A">Tío / Tía</option>
                  <option value="HERMANO_A">Hermano / Hermana</option>
                  <option value="OTRO">Otro</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={guardiansModal.isPrimary}
                    onChange={(e) => setGuardiansModal((prev) => ({ ...prev, isPrimary: e.target.checked }))}
                  />
                  Contacto Principal
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={guardiansModal.isAuthorizedPickup}
                    onChange={(e) => setGuardiansModal((prev) => ({ ...prev, isAuthorizedPickup: e.target.checked }))}
                  />
                  Retiro Autorizado
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.25rem' }}>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setGuardiansModal((prev) => ({ ...prev, isLinkingNew: false }))}
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={guardiansModal.isLinkingSubmitting || !guardiansModal.selectedGuardianId}
                >
                  {guardiansModal.isLinkingSubmitting ? 'Vinculando...' : 'Confirmar'}
                </Button>
              </div>
            </form>
          )}

          {/* List of Guardians */}
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
                    padding: '0.875rem 1rem',
                    backgroundColor: '#F8FAFC',
                    borderRadius: '8px',
                    border: '1px solid #E2E8F0',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, color: '#0F172A', marginBottom: '0.2rem' }}>
                      {g.guardian ? `${g.guardian.first_name} ${g.guardian.last_name}` : g.guardian_id}
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                      Parentesco: <strong>{g.relationship_type}</strong> • Tel:{' '}
                      {g.guardian?.phone || 'N/A'}
                      {g.is_primary_contact && ' • Contacto Principal'}
                      {g.is_authorized_pickup && ' • Retiro Autorizado'}
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    {hasPermission('guardians:link_student') && (
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => {
                          setUnlinkDialog({
                            isOpen: true,
                            studentId: guardiansModal.student?.id || '',
                            guardianId: g.guardian_id,
                            guardianName: g.guardian ? `${g.guardian.first_name} ${g.guardian.last_name}` : g.guardian_id,
                            isSubmitting: false,
                          })
                        }}
                      >
                        Desvincular
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Modal>

      {/* UNLINK CONFIRMATION DIALOG */}
      <Modal
        isOpen={unlinkDialog.isOpen}
        onClose={() => {
          setUnlinkDialog((prev) => ({ ...prev, isOpen: false }))
        }}
        title="Confirmar Desvinculación"
        subtitle="Esta acción elimina la relación familiar sin alterar los registros civiles ni académicos."
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#991B1B' }}>
            <span style={{ fontSize: '1.25rem' }}>⚠️</span>
            <span style={{ fontSize: '0.875rem' }}>
              ¿Está seguro de desvincular al acudiente <strong>{unlinkDialog.guardianName}</strong> de este estudiante?
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setUnlinkDialog((prev) => ({ ...prev, isOpen: false }))}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              variant="danger"
              disabled={unlinkDialog.isSubmitting}
              onClick={() => void handleConfirmUnlink()}
            >
              {unlinkDialog.isSubmitting ? 'Desvinculando...' : 'Sí, Desvincular'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* RESET TOKEN DELIVERY MODAL */}
      <Modal
        isOpen={tokenModal.isOpen}
        onClose={() => {
          setTokenModal((prev) => ({ ...prev, isOpen: false }))
        }}
        title={tokenModal.title}
        subtitle="Entregue este token seguro al estudiante o acudiente para restablecer credenciales."
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ backgroundColor: '#F0FDF4', padding: '0.875rem', borderRadius: '8px', border: '1px solid #BBF7D0' }}>
            <div style={{ fontSize: '0.8125rem', color: '#166534', fontWeight: 600 }}>
              Estudiante: {tokenModal.recipientName} ({tokenModal.recipientEmail})
            </div>
            <p style={{ fontSize: '0.75rem', color: '#15803D', marginTop: '0.25rem' }}>
              El token es de un solo uso y cuenta con expiración segura de acuerdo con la política institucional.
            </p>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Token de Restablecimiento:
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                readOnly
                value={tokenModal.token}
                style={{
                  width: '100%',
                  padding: '0.45rem 0.6rem',
                  borderRadius: '6px',
                  border: '1px solid #CBD5E1',
                  backgroundColor: '#F8FAFC',
                  fontSize: '0.8125rem',
                  fontFamily: 'monospace',
                }}
              />
              <Button
                type="button"
                variant="primary"
                size="sm"
                onClick={() => {
                  void navigator.clipboard.writeText(tokenModal.token)
                  setTokenModal((prev) => ({ ...prev, isCopied: true }))
                }}
              >
                {tokenModal.isCopied ? '✓ Copiado' : 'Copiar'}
              </Button>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setTokenModal((prev) => ({ ...prev, isOpen: false }))}
            >
              Cerrar
            </Button>
          </div>
        </div>
      </Modal>

      {/* CREATE STUDENT MODAL */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false)
          resetCreateForm()
        }}
        title="Registrar Perfil de Estudiante"
        subtitle={
          isRegisteringNewUser
            ? "Aprovisionamiento de nuevo estudiante institucional."
            : "Vincule una cuenta de usuario existente o aprovisione un nuevo estudiante institucional."
        }
      >
        <form onSubmit={(e) => void handleCreateStudent(e)}>
          {modalError && (
            <div style={{ marginBottom: '1rem' }}>
              <Alert
                error={modalError}
                onClose={() => {
                  setModalError(null)
                }}
              />
            </div>
          )}

          {isRegisteringNewUser ? (
            /* Inline Civil Identity Provisioning */
            <div style={{ marginBottom: '1.25rem' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.75rem',
                }}
              >
                <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#1E293B' }}>
                  Datos de la Nueva Cuenta
                </span>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setIsRegisteringNewUser(false)
                  }}
                >
                  ← Vincular Usuario Existente
                </Button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Nombres *
                  </label>
                  <input
                    type="text"
                    required
                    value={newFirstName}
                    onChange={(e) => {
                      setNewFirstName(e.target.value)
                    }}
                    style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Apellidos *
                  </label>
                  <input
                    type="text"
                    required
                    value={newLastName}
                    onChange={(e) => {
                      setNewLastName(e.target.value)
                    }}
                    style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Tipo Doc. *
                  </label>
                  <select
                    value={newDocType}
                    onChange={(e) => {
                      setNewDocType(e.target.value)
                    }}
                    style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                  >
                    <option value="TI">TI</option>
                    <option value="CC">CC</option>
                    <option value="RC">RC</option>
                    <option value="CE">CE</option>
                    <option value="PASSPORT">Pasaporte</option>
                    <option value="PEP">PEP</option>
                    <option value="PPT">PPT</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Número de Documento *
                  </label>
                  <input
                    type="text"
                    required
                    value={newDocNumber}
                    onChange={(e) => {
                      setNewDocNumber(e.target.value)
                    }}
                    style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Correo Electrónico *
                  </label>
                  <input
                    type="email"
                    required
                    value={newEmail}
                    onChange={(e) => {
                      setNewEmail(e.target.value)
                    }}
                    style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Teléfono
                  </label>
                  <input
                    type="tel"
                    value={newPhone}
                    onChange={(e) => {
                      setNewPhone(e.target.value)
                    }}
                    style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                  />
                </div>
              </div>
            </div>
          ) : (
            /* User Autocomplete Selection */
            <div style={{ marginBottom: '1.25rem' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.5rem',
                }}
              >
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#334155' }}>
                  Cuenta de Usuario *
                </label>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setIsRegisteringNewUser(true)
                    setSelectedUser(null)
                  }}
                >
                  + Aprovisionar Nuevo Usuario
                </Button>
              </div>

              {selectedUser ? (
                <div
                  style={{
                    padding: '0.75rem',
                    backgroundColor: '#EFF6FF',
                    borderRadius: '8px',
                    border: '1px solid #BFDBFE',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, color: '#1E40AF' }}>
                      {selectedUser.first_name} {selectedUser.last_name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#3B82F6' }}>
                      {selectedUser.email} • {selectedUser.document_type} {selectedUser.document_number}
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setSelectedUser(null)
                    }}
                  >
                    Cambiar
                  </Button>
                </div>
              ) : (
                <div>
                  <input
                    type="text"
                    placeholder="Escriba nombre o correo del estudiante..."
                    value={userSearchQuery}
                    onChange={(e) => {
                      void handleSearchUsers(e.target.value)
                    }}
                    style={{
                      width: '100%',
                      padding: '0.45rem 0.75rem',
                      borderRadius: '8px',
                      border: '1px solid #CBD5E1',
                      fontSize: '0.875rem',
                    }}
                  />
                  {isSearchingUsers && (
                    <p style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
                      Buscando cuentas institucionales...
                    </p>
                  )}
                  {userSearchResults.length > 0 && (
                    <div
                      style={{
                        marginTop: '0.5rem',
                        border: '1px solid #E2E8F0',
                        borderRadius: '8px',
                        maxHeight: '140px',
                        overflowY: 'auto',
                      }}
                    >
                      {userSearchResults.map((u) => (
                        <div
                          key={u.id}
                          onClick={() => {
                            setSelectedUser(u)
                            setUserSearchResults([])
                          }}
                          style={{
                            padding: '0.5rem 0.75rem',
                            borderBottom: '1px solid #F1F5F9',
                            cursor: 'pointer',
                            fontSize: '0.8125rem',
                          }}
                        >
                          <strong>{u.first_name} {u.last_name}</strong> — {u.email}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Academic & SIMAT Data */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Código SIMAT *
              </label>
              <input
                type="text"
                required
                placeholder="Ej: SIMAT-2026-001"
                value={codeSimat}
                onChange={(e) => {
                  setCodeSimat(e.target.value)
                }}
                style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Fecha de Nacimiento *
              </label>
              <input
                type="date"
                required
                value={birthDate}
                onChange={(e) => {
                  setBirthDate(e.target.value)
                }}
                style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Género
              </label>
              <select
                value={gender}
                onChange={(e) => {
                  setGender(e.target.value as StudentGender)
                }}
                style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              >
                <option value="M">Masculino</option>
                <option value="F">Femenino</option>
                <option value="OTHER">Otro</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Tipo de Sangre / RH
              </label>
              <select
                value={bloodType}
                onChange={(e) => {
                  setBloodType(e.target.value)
                }}
                style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              >
                <option value="O+">O+</option>
                <option value="O-">O-</option>
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Estrato (1-6)
              </label>
              <input
                type="number"
                min={1}
                max={6}
                value={stratum}
                onChange={(e) => {
                  setStratum(Number(e.target.value))
                }}
                style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Entidad de Salud (EPS)
            </label>
            <input
              type="text"
              value={eps}
              onChange={(e) => {
                setEps(e.target.value)
              }}
              style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
            />
          </div>

          {/* Inclusion metadata */}
          <div style={{ padding: '0.75rem', backgroundColor: '#F8FAFC', borderRadius: '8px', border: '1px solid #E2E8F0', marginBottom: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.8125rem' }}>
              <input
                type="checkbox"
                checked={hasDisability}
                onChange={(e) => {
                  setHasDisability(e.target.checked)
                }}
              />
              <strong>Estudiante con Inclusión / Discapacidad</strong>
            </label>

            {hasDisability && (
              <div style={{ marginTop: '0.5rem' }}>
                <input
                  type="text"
                  placeholder="Detalle el tipo de discapacidad..."
                  value={disabilityType}
                  onChange={(e) => {
                    setDisabilityType(e.target.value)
                  }}
                  style={{ width: '100%', padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.8125rem' }}
                />
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setIsCreateOpen(false)
                resetCreateForm()
              }}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? 'Registrando...' : 'Registrar Estudiante'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default StudentsView
