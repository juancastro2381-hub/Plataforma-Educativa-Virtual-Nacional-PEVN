/**
 * PEVN Frontend — Guardians View
 *
 * Legal guardians (Acudientes), decoupled civil identities,
 * account provisioning, lifecycle management, and bidirectional student associations.
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
  DocumentType,
  GuardianAccountStatus,
  GuardianCreateRequest,
  GuardianRelationshipType,
  GuardianResponse,
  StudentGuardianResponse,
  StudentResponse,
  UserResponse,
} from '@/types'

export const GuardiansView: React.FC = () => {
  const { user, hasPermission } = useAuth()

  const [guardians, setGuardians] = useState<GuardianResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [docSearch, setDocSearch] = useState<string>('')
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Reference Catalogs
  const [students, setStudents] = useState<StudentResponse[]>([])

  // Create Guardian Modal
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [accountMode, setAccountMode] = useState<'civil_only' | 'new_account' | 'existing_user'>('new_account')

  // Form fields
  const [firstName, setFirstName] = useState<string>('')
  const [lastName, setLastName] = useState<string>('')
  const [docType, setDocType] = useState<DocumentType>('CC')
  const [docNumber, setDocNumber] = useState<string>('')
  const [phone, setPhone] = useState<string>('')
  const [email, setEmail] = useState<string>('')
  const [address, setAddress] = useState<string>('')
  const [relationshipType, setRelationshipType] = useState<GuardianRelationshipType>('MADRE')

  // Existing User Search
  const [userSearchQuery, setUserSearchQuery] = useState<string>('')
  const [userSearchResults, setUserSearchResults] = useState<UserResponse[]>([])
  const [isSearchingUsers, setIsSearchingUsers] = useState<boolean>(false)
  const [selectedUser, setSelectedUser] = useState<UserResponse | null>(null)

  // Token Delivery Modal
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

  // Action in progress state
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null)

  // Associate to Student Modal
  const [linkModal, setLinkModal] = useState<{
    isOpen: boolean
    guardian: GuardianResponse | null
    studentId: string
    relType: GuardianRelationshipType
    isPrimary: boolean
    isAuthorizedPickup: boolean
    isSubmitting: boolean
  }>({
    isOpen: false,
    guardian: null,
    studentId: '',
    relType: 'MADRE',
    isPrimary: false,
    isAuthorizedPickup: true,
    isSubmitting: false,
  })

  // View / Unlink Students Modal
  const [viewStudentsModal, setViewStudentsModal] = useState<{
    isOpen: boolean
    guardian: GuardianResponse | null
    linkedStudents: StudentGuardianResponse[]
    isLoading: boolean
  }>({
    isOpen: false,
    guardian: null,
    linkedStudents: [],
    isLoading: false,
  })

  // Unlink Confirmation Dialog
  const [unlinkDialog, setUnlinkDialog] = useState<{
    isOpen: boolean
    guardianId: string
    studentId: string
    studentName: string
    isSubmitting: boolean
  }>({
    isOpen: false,
    guardianId: '',
    studentId: '',
    studentName: '',
    isSubmitting: false,
  })

  const loadGuardians = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await academicApi.listGuardians(docSearch.trim() || undefined)
      setGuardians(data.items)
      setTotal(data.total)
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al cargar acudientes'))
    } finally {
      setIsLoading(false)
    }
  }, [docSearch])

  const loadStudents = useCallback(async () => {
    try {
      const data = await academicApi.listStudents()
      if (data?.items) {
        setStudents(data.items)
      }
    } catch {
      // Non-critical reference catalog fallback
    }
  }, [])

  useEffect(() => {
    setGuardians([])
    setStudents([])
    void loadGuardians()
    void loadStudents()
  }, [user?.institution_id, loadGuardians, loadStudents])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    void loadGuardians()
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
    setFirstName('')
    setLastName('')
    setDocNumber('')
    setPhone('')
    setEmail('')
    setAddress('')
    setSelectedUser(null)
    setUserSearchQuery('')
    setUserSearchResults([])
    setAccountMode('new_account')
  }

  const handleCreateGuardian = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)

    const payload: GuardianCreateRequest = {
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      document_type: docType,
      document_number: docNumber.trim(),
      phone: phone.trim(),
      email: email.trim() || null,
      address: address.trim() || null,
      relationship_type: relationshipType,
      user_id: accountMode === 'existing_user' && selectedUser ? selectedUser.id : null,
      new_user:
        accountMode === 'new_account'
          ? {
              first_name: firstName.trim(),
              last_name: lastName.trim(),
              document_type: docType,
              document_number: docNumber.trim(),
              email: email.trim(),
              phone: phone.trim() || null,
            }
          : null,
      provision_account: accountMode === 'new_account',
    }

    try {
      const created = await academicApi.createGuardian(payload)
      setSuccessMsg(`Acudiente ${created.first_name} ${created.last_name} registrado exitosamente.`)
      setIsCreateOpen(false)
      resetCreateForm()
      await loadGuardians()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al registrar acudiente'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleProvisionAccount = async (g: GuardianResponse) => {
    setActionLoadingId(g.id)
    setError(null)
    setSuccessMsg(null)
    try {
      const res = await academicApi.provisionGuardianAccount(g.id, { email: g.email || undefined })
      setSuccessMsg(`Cuenta de acceso aprovisionada para ${g.first_name} ${g.last_name}.`)
      await loadGuardians()
      if (res.reset_token) {
        setTokenModal({
          isOpen: true,
          title: 'Credencial de Acceso Aprovisionada',
          recipientName: `${g.first_name} ${g.last_name}`,
          recipientEmail: g.email || g.account_email || 'Sin correo',
          token: res.reset_token,
          isCopied: false,
        })
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al aprovisionar cuenta de acudiente'))
    } finally {
      setActionLoadingId(null)
    }
  }

  const handleToggleAccountStatus = async (g: GuardianResponse) => {
    const isCurrentlyActive = g.account_status === 'ACTIVA'
    const targetState = !isCurrentlyActive
    setActionLoadingId(g.id)
    setError(null)
    setSuccessMsg(null)
    try {
      await academicApi.updateGuardianAccountStatus(g.id, targetState)
      setSuccessMsg(
        `Cuenta de acudiente ${targetState ? 'habilitada' : 'deshabilitada'} exitosamente para ${g.first_name} ${g.last_name}.`
      )
      await loadGuardians()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al modificar estado de la cuenta'))
    } finally {
      setActionLoadingId(null)
    }
  }

  const handleResetPassword = async (g: GuardianResponse) => {
    setActionLoadingId(g.id)
    setError(null)
    setSuccessMsg(null)
    try {
      const res = await academicApi.resetGuardianPassword(g.id)
      setSuccessMsg(`Token de restablecimiento generado para ${g.first_name} ${g.last_name}.`)
      if (res.reset_token) {
        setTokenModal({
          isOpen: true,
          title: 'Restablecimiento de Contraseña',
          recipientName: `${g.first_name} ${g.last_name}`,
          recipientEmail: g.email || g.account_email || 'Sin correo',
          token: res.reset_token,
          isCopied: false,
        })
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al restablecer contraseña'))
    } finally {
      setActionLoadingId(null)
    }
  }

  const handleAssociateStudent = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!linkModal.guardian || !linkModal.studentId) return

    setLinkModal((prev) => ({ ...prev, isSubmitting: true }))
    setError(null)
    setSuccessMsg(null)

    const payload: AssociateGuardianRequest = {
      relationship_type: linkModal.relType,
      is_primary_contact: linkModal.isPrimary,
      is_authorized_pickup: linkModal.isAuthorizedPickup,
    }

    try {
      await academicApi.associateGuardianToStudent(
        linkModal.guardian.id,
        linkModal.studentId,
        payload
      )
      setSuccessMsg('Acudiente vinculado al estudiante exitosamente.')
      setLinkModal({
        isOpen: false,
        guardian: null,
        studentId: '',
        relType: 'MADRE',
        isPrimary: false,
        isAuthorizedPickup: true,
        isSubmitting: false,
      })
      await loadGuardians()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al asociar acudiente con estudiante'))
    } finally {
      setLinkModal((prev) => ({ ...prev, isSubmitting: false }))
    }
  }

  const handleOpenViewStudents = async (g: GuardianResponse) => {
    setViewStudentsModal({
      isOpen: true,
      guardian: g,
      linkedStudents: [],
      isLoading: true,
    })
    try {
      const data = await academicApi.getGuardianStudents(g.id)
      setViewStudentsModal((prev) => ({
        ...prev,
        linkedStudents: data,
        isLoading: false,
      }))
    } catch {
      setViewStudentsModal((prev) => ({ ...prev, isLoading: false }))
    }
  }

  const handleConfirmUnlink = async () => {
    if (!unlinkDialog.guardianId || !unlinkDialog.studentId) return
    setUnlinkDialog((prev) => ({ ...prev, isSubmitting: true }))
    setError(null)
    setSuccessMsg(null)

    try {
      await academicApi.dissociateGuardian(unlinkDialog.guardianId, unlinkDialog.studentId)
      setSuccessMsg(`Estudiante desvinculado exitosamente del acudiente.`)
      setUnlinkDialog({
        isOpen: false,
        guardianId: '',
        studentId: '',
        studentName: '',
        isSubmitting: false,
      })
      if (viewStudentsModal.guardian) {
        void handleOpenViewStudents(viewStudentsModal.guardian)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al desvincular estudiante'))
    } finally {
      setUnlinkDialog((prev) => ({ ...prev, isSubmitting: false }))
    }
  }

  const getStatusBadge = (status?: GuardianAccountStatus) => {
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
          Directorio Familiar & Acudientes
        </h1>
        <p style={{ color: '#64748B', fontSize: '0.875rem', marginTop: '0.25rem' }}>
          Gestión civil de acudientes, aprovisionamiento de cuentas de acceso y vinculación familiar.
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
            placeholder="Buscar por cédula / documento..."
            value={docSearch}
            onChange={(e) => {
              setDocSearch(e.target.value)
            }}
            style={{
              padding: '0.45rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              fontSize: '0.875rem',
              width: '260px',
            }}
          />
          <Button type="submit" variant="secondary" size="sm">
            Buscar
          </Button>
          {docSearch && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => {
                setDocSearch('')
              }}
            >
              Limpiar
            </Button>
          )}
        </form>

        {hasPermission('guardians:create') && (
          <Button
            variant="primary"
            onClick={() => {
              setIsCreateOpen(true)
            }}
          >
            + Registrar Acudiente
          </Button>
        )}
      </div>

      {/* Table Card */}
      <Card
        title="Registro Civil y Cuentas de Acudientes"
        subtitle={`Total registrados: ${String(total)}`}
        action={
          <Button variant="secondary" size="sm" onClick={() => void loadGuardians()}>
            Refrescar
          </Button>
        }
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando acudientes...
            </p>
          </div>
        ) : guardians.length === 0 ? (
          <EmptyState
            icon="👪"
            title="No se encontraron acudientes"
            description="No hay acudientes registrados con los criterios de búsqueda especificados."
            actionLabel={hasPermission('guardians:create') ? '+ Registrar Primer Acudiente' : undefined}
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
                  <th style={{ padding: '0.75rem 1rem' }}>Nombre Completo</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Documento</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Teléfono</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Correo / Usuario</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Estado de Cuenta</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {guardians.map((g) => (
                  <tr key={g.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                      {g.first_name} {g.last_name}
                      <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 400 }}>
                        Parentesco: {g.relationship_type}
                      </div>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#1E40AF' }}>
                      <code>{g.document_type} {g.document_number}</code>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#475569' }}>{g.phone}</td>
                    <td style={{ padding: '0.875rem 1rem', color: '#64748B' }}>
                      {g.email || <span style={{ fontStyle: 'italic', color: '#94A3B8' }}>Sin correo</span>}
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      {getStatusBadge(g.account_status)}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                        {/* Link to Student */}
                        {hasPermission('guardians:link_student') && (
                          <Button
                            variant="secondary"
                            size="sm"
                            title="Vincular a estudiante"
                            onClick={() => {
                              setLinkModal({
                                isOpen: true,
                                guardian: g,
                                studentId: '',
                                relType: g.relationship_type,
                                isPrimary: false,
                                isAuthorizedPickup: true,
                                isSubmitting: false,
                              })
                            }}
                          >
                            🔗 Vincular
                          </Button>
                        )}

                        {/* View linked children */}
                        <Button
                          variant="secondary"
                          size="sm"
                          title="Ver hijos / acudidos"
                          onClick={() => void handleOpenViewStudents(g)}
                        >
                          👥 Hijos
                        </Button>

                        {/* Account Lifecycle Actions */}
                        {g.account_status === 'SIN_CUENTA' && hasPermission('guardians:create') && (
                          <Button
                            variant="primary"
                            size="sm"
                            disabled={actionLoadingId === g.id}
                            onClick={() => void handleProvisionAccount(g)}
                          >
                            + Aprovisionar Acceso
                          </Button>
                        )}

                        {g.account_status !== 'SIN_CUENTA' && hasPermission('guardians:update') && (
                          <>
                            <Button
                              variant="secondary"
                              size="sm"
                              disabled={actionLoadingId === g.id}
                              onClick={() => void handleToggleAccountStatus(g)}
                            >
                              {g.account_status === 'ACTIVA' ? 'Desactivar' : 'Activar'}
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              disabled={actionLoadingId === g.id || g.account_status === 'INACTIVA'}
                              onClick={() => void handleResetPassword(g)}
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

      {/* CREATE GUARDIAN MODAL */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false)
          resetCreateForm()
        }}
        title="Registrar Acudiente / Familiar"
        subtitle="Complete los datos del acudiente y seleccione el tipo de aprovisionamiento de acceso."
      >
        <form onSubmit={(e) => void handleCreateGuardian(e)} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Account Mode Selection */}
          <div style={{ backgroundColor: '#F8FAFC', padding: '0.875rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.5rem' }}>
              Modalidad de Cuenta de Acceso:
            </label>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8125rem', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="accountMode"
                  checked={accountMode === 'new_account'}
                  onChange={() => setAccountMode('new_account')}
                />
                <strong>Crear cuenta de acceso</strong> (Recomendado)
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8125rem', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="accountMode"
                  checked={accountMode === 'civil_only'}
                  onChange={() => setAccountMode('civil_only')}
                />
                Solo registro civil (Sin acceso)
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8125rem', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="accountMode"
                  checked={accountMode === 'existing_user'}
                  onChange={() => setAccountMode('existing_user')}
                />
                Vincular usuario existente
              </label>
            </div>
          </div>

          {/* Existing User Search if selected */}
          {accountMode === 'existing_user' && (
            <div style={{ backgroundColor: '#EFF6FF', padding: '0.75rem', borderRadius: '8px', border: '1px solid #BFDBFE' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#1E40AF', marginBottom: '0.25rem' }}>
                Buscar usuario existente de la institución:
              </label>
              <input
                type="text"
                value={userSearchQuery}
                onChange={(e) => void handleSearchUsers(e.target.value)}
                placeholder="Escriba nombre o correo..."
                style={{ width: '100%', padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid #93C5FD' }}
              />
              {isSearchingUsers && <span style={{ fontSize: '0.75rem', color: '#6B7280' }}>Buscando...</span>}
              {userSearchResults.length > 0 && (
                <div style={{ marginTop: '0.5rem', maxHeight: '120px', overflowY: 'auto' }}>
                  {userSearchResults.map((u) => (
                    <div
                      key={u.id}
                      onClick={() => {
                        setSelectedUser(u)
                        setFirstName(u.first_name)
                        setLastName(u.last_name)
                        setDocNumber(u.document_number || '')
                        setEmail(u.email)
                      }}
                      style={{
                        padding: '0.35rem 0.5rem',
                        cursor: 'pointer',
                        fontSize: '0.8125rem',
                        backgroundColor: selectedUser?.id === u.id ? '#DBEAFE' : 'white',
                        borderBottom: '1px solid #E5E7EB',
                      }}
                    >
                      {u.first_name} {u.last_name} ({u.email})
                    </div>
                  ))}
                </div>
              )}
              {selectedUser && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.8125rem', color: '#1E40AF' }}>
                  Usuario seleccionado: <strong>{selectedUser.first_name} {selectedUser.last_name}</strong>
                </div>
              )}
            </div>
          )}

          {/* Civil Information */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Nombres *
              </label>
              <input
                type="text"
                required
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
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
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Tipo Doc. *
              </label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value as DocumentType)}
                style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              >
                <option value="CC">CC</option>
                <option value="TI">TI</option>
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
                value={docNumber}
                onChange={(e) => setDocNumber(e.target.value)}
                style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Teléfono de Contacto *
              </label>
              <input
                type="tel"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Correo Electrónico {accountMode === 'new_account' ? '*' : '(Opcional)'}
              </label>
              <input
                type="email"
                required={accountMode === 'new_account'}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="acudiente@ejemplo.com"
                style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Parentesco por Defecto
              </label>
              <select
                value={relationshipType}
                onChange={(e) => setRelationshipType(e.target.value as GuardianRelationshipType)}
                style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
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
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Dirección Residencial
              </label>
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="Dirección o barrio"
                style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
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
              {isSubmitting ? 'Registrando...' : 'Registrar Acudiente'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* LINK TO STUDENT MODAL */}
      <Modal
        isOpen={linkModal.isOpen}
        onClose={() => {
          setLinkModal((prev) => ({ ...prev, isOpen: false }))
        }}
        title={`Vincular a Estudiante — ${linkModal.guardian?.first_name ?? ''} ${linkModal.guardian?.last_name ?? ''}`}
        subtitle="Seleccione el estudiante y configure las autorizaciones familiares."
      >
        <form onSubmit={(e) => void handleAssociateStudent(e)} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Seleccione el Estudiante *
            </label>
            <select
              required
              value={linkModal.studentId}
              onChange={(e) => setLinkModal((prev) => ({ ...prev, studentId: e.target.value }))}
              style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
            >
              <option value="">-- Seleccionar estudiante --</option>
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.user ? `${s.user.first_name} ${s.user.last_name}` : s.code_simat} (SIMAT: {s.code_simat})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Parentesco específico con este estudiante *
            </label>
            <select
              value={linkModal.relType}
              onChange={(e) => setLinkModal((prev) => ({ ...prev, relType: e.target.value as GuardianRelationshipType }))}
              style={{ width: '100%', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
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

          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8125rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={linkModal.isPrimary}
                onChange={(e) => setLinkModal((prev) => ({ ...prev, isPrimary: e.target.checked }))}
              />
              Contacto Principal de Emergencia
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8125rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={linkModal.isAuthorizedPickup}
                onChange={(e) => setLinkModal((prev) => ({ ...prev, isAuthorizedPickup: e.target.checked }))}
              />
              Autorizado para Retiro
            </label>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setLinkModal((prev) => ({ ...prev, isOpen: false }))}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={linkModal.isSubmitting || !linkModal.studentId}>
              {linkModal.isSubmitting ? 'Vinculando...' : 'Confirmar Vinculación'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* VIEW LINKED STUDENTS MODAL */}
      <Modal
        isOpen={viewStudentsModal.isOpen}
        onClose={() => {
          setViewStudentsModal({ isOpen: false, guardian: null, linkedStudents: [], isLoading: false })
        }}
        title={`Estudiantes Vinculados — ${viewStudentsModal.guardian?.first_name ?? ''} ${viewStudentsModal.guardian?.last_name ?? ''}`}
        subtitle="Hijos o acudidos bajo la tutela de este acudiente en la institución."
      >
        {viewStudentsModal.isLoading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <LoadingSpinner size="md" />
            <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '0.5rem' }}>
              Consultando estudiantes vinculados...
            </p>
          </div>
        ) : viewStudentsModal.linkedStudents.length === 0 ? (
          <EmptyState
            icon="👨‍👧"
            title="Sin estudiantes vinculados"
            description="Este acudiente aún no se encuentra vinculado a ningún estudiante."
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {viewStudentsModal.linkedStudents.map((sg) => {
              const matchedStudent = sg.student || students.find((s) => s.id === sg.student_id)
              const studentName = matchedStudent?.user
                ? `${matchedStudent.user.first_name} ${matchedStudent.user.last_name}`
                : matchedStudent?.code_simat || sg.student_id

              return (
                <div
                  key={sg.id}
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
                      {studentName}
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                      Parentesco: <strong>{sg.relationship_type}</strong>
                      {sg.is_primary_contact && ' • Contacto Principal'}
                      {sg.is_authorized_pickup && ' • Retiro Autorizado'}
                    </div>
                  </div>

                  {hasPermission('guardians:link_student') && (
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => {
                        setUnlinkDialog({
                          isOpen: true,
                          guardianId: viewStudentsModal.guardian?.id || '',
                          studentId: sg.student_id,
                          studentName,
                          isSubmitting: false,
                        })
                      }}
                    >
                      Desvincular
                    </Button>
                  )}
                </div>
              )
            })}
          </div>
        )}
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
              ¿Está seguro de desvincular al estudiante <strong>{unlinkDialog.studentName}</strong> de este acudiente?
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

      {/* TOKEN DELIVERY MODAL */}
      <Modal
        isOpen={tokenModal.isOpen}
        onClose={() => {
          setTokenModal((prev) => ({ ...prev, isOpen: false }))
        }}
        title={tokenModal.title}
        subtitle="Entregue este enlace seguro al acudiente para que establezca su contraseña."
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ backgroundColor: '#F0FDF4', padding: '0.875rem', borderRadius: '8px', border: '1px solid #BBF7D0' }}>
            <div style={{ fontSize: '0.8125rem', color: '#166534', fontWeight: 600 }}>
              Acudiente: {tokenModal.recipientName} ({tokenModal.recipientEmail})
            </div>
            <p style={{ fontSize: '0.75rem', color: '#15803D', marginTop: '0.25rem' }}>
              El token es de un solo uso y cuenta con expiración segura.
            </p>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Enlace Directo de Activación:
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                readOnly
                value={`${window.location.origin}/auth/reset-password?token=${encodeURIComponent(tokenModal.token)}`}
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
                  const url = `${window.location.origin}/auth/reset-password?token=${encodeURIComponent(tokenModal.token)}`
                  void navigator.clipboard.writeText(url)
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
    </div>
  )
}

export default GuardiansView
