/**
 * PEVN Frontend — Teachers View
 *
 * Educator profiles, statutory appointments, and assignment eligibility checks.
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
  TeacherAccountStatus,
  TeacherContractType,
  TeacherCreateRequest,
  TeacherEligibilityResponse,
  TeacherResponse,
  UserResponse,
} from '@/types'

export const TeachersView: React.FC = () => {
  const { hasPermission } = useAuth()

  const [teachers, setTeachers] = useState<TeacherResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [contractFilter, setContractFilter] = useState<TeacherContractType | undefined>(undefined)
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Create Teacher Modal & User Search / Provisioning
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
  const [newDocType, setNewDocType] = useState<string>('CC')
  const [newDocNumber, setNewDocNumber] = useState<string>('')
  const [newEmail, setNewEmail] = useState<string>('')
  const [newPhone, setNewPhone] = useState<string>('')
  const [specialtyArea, setSpecialtyArea] = useState<string>('Licenciatura en Ciencias Básicas')
  const [contractType, setContractType] = useState<TeacherContractType>('PROPIEDAD')
  const [escalafonGrade, setEscalafonGrade] = useState<string>('14')
  const [provisionAccountNow, setProvisionAccountNow] = useState<boolean>(true)

  // Onboarding / Credential Delivery Modal
  const [onboardingModal, setOnboardingModal] = useState<{
    isOpen: boolean
    title: string
    teacherName: string
    teacherEmail: string
    setupUrl: string | null
    portalUrl: string
    copiedSetup: boolean
    copiedPortal: boolean
  }>({
    isOpen: false,
    title: '',
    teacherName: '',
    teacherEmail: '',
    setupUrl: null,
    portalUrl: '',
    copiedSetup: false,
    copiedPortal: false,
  })

  // Provision Account Modal
  const [provisionModal, setProvisionModal] = useState<{
    isOpen: boolean
    teacher: TeacherResponse | null
    email: string
    isSubmitting: boolean
    error: string | null
  }>({
    isOpen: false,
    teacher: null,
    email: '',
    isSubmitting: false,
    error: null,
  })

  // Eligibility Modal
  const [eligibilityModal, setEligibilityModal] = useState<{
    isOpen: boolean
    teacher: TeacherResponse | null
    eligibility: TeacherEligibilityResponse | null
    isLoading: boolean
  }>({
    isOpen: false,
    teacher: null,
    eligibility: null,
    isLoading: false,
  })

  const loadTeachers = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await academicApi.listTeachers(contractFilter)
      setTeachers(data.items)
      setTotal(data.total)
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al cargar docentes'))
    } finally {
      setIsLoading(false)
    }
  }, [contractFilter])

  useEffect(() => {
    void loadTeachers()
  }, [loadTeachers])

  const handleSearchUsers = async (query: string) => {
    setUserSearchQuery(query)
    const trimmed = query.trim()
    if (!trimmed) {
      setUserSearchResults([])
      return
    }
    setIsSearchingUsers(true)
    try {
      const data = await usersApi.searchUsers({ search: trimmed, page_size: 10 })
      setUserSearchResults(data.items)
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
    setNewDocType('CC')
    setNewDocNumber('')
    setNewEmail('')
    setNewPhone('')
    setSpecialtyArea('Licenciatura en Ciencias Básicas')
    setContractType('PROPIEDAD')
    setEscalafonGrade('14')
    setProvisionAccountNow(true)
    setModalError(null)
  }

  const handleCreateTeacher = async (e: React.FormEvent) => {
    e.preventDefault()
    setModalError(null)
    setError(null)
    setSuccessMsg(null)

    let payload: TeacherCreateRequest

    if (isRegisteringNewUser) {
      if (!newFirstName.trim() || !newLastName.trim() || !newDocNumber.trim() || !newEmail.trim()) {
        setModalError(
          new Error('Por favor complete todos los campos obligatorios del nuevo docente.')
        )
        return
      }
      payload = {
        new_user: {
          first_name: newFirstName.trim(),
          last_name: newLastName.trim(),
          document_type: newDocType,
          document_number: newDocNumber.trim(),
          email: newEmail.trim().toLowerCase(),
          phone: newPhone.trim() || null,
        },
        specialty_area: specialtyArea.trim() || null,
        contract_type: contractType,
        escalafon_grade: escalafonGrade.trim() || null,
        provision_account: provisionAccountNow,
      }
    } else {
      if (!selectedUser) {
        setModalError(
          new Error('Debe buscar y seleccionar una cuenta de usuario institucional o registrar a un nuevo docente.')
        )
        return
      }
      payload = {
        user_id: selectedUser.id,
        specialty_area: specialtyArea.trim() || null,
        contract_type: contractType,
        escalafon_grade: escalafonGrade.trim() || null,
        provision_account: provisionAccountNow,
      }
    }

    setIsSubmitting(true)
    try {
      const createdTeacher = await academicApi.createTeacher(payload)
      const docName = isRegisteringNewUser
        ? `${newFirstName.trim()} ${newLastName.trim()}`
        : `${selectedUser?.first_name} ${selectedUser?.last_name}`
      const teacherEmail = isRegisteringNewUser
        ? newEmail.trim().toLowerCase()
        : (selectedUser?.email || '')

      if (createdTeacher && createdTeacher.account_status === 'ACTIVA') {
        setSuccessMsg(
          `Perfil docente para ${docName} creado exitosamente con cuenta de acceso activa (ACTIVA). El educador puede iniciar sesión en /teacher.`
        )
        if (createdTeacher.reset_token) {
          const origin = window.location.origin
          setOnboardingModal({
            isOpen: true,
            title: 'Docente Creado y Cuenta Activada',
            teacherName: docName,
            teacherEmail,
            setupUrl: `${origin}/auth/reset-password?token=${encodeURIComponent(createdTeacher.reset_token)}`,
            portalUrl: `${origin}/teacher`,
            copiedSetup: false,
            copiedPortal: false,
          })
        }
      } else {
        setSuccessMsg(
          `Perfil docente para ${docName} creado exitosamente (Estado: SIN CUENTA). Podrá aprovisionar el acceso institucional usando '+ Crear Cuenta' en la tabla.`
        )
      }
      setIsCreateOpen(false)
      resetCreateForm()
      await loadTeachers()
    } catch (err: unknown) {
      setModalError(err instanceof Error ? err : new Error('Error al crear docente'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCheckEligibility = async (teacher: TeacherResponse) => {
    setEligibilityModal({
      isOpen: true,
      teacher,
      eligibility: null,
      isLoading: true,
    })
    try {
      const el = await academicApi.validateTeacherEligibility(teacher.id)
      setEligibilityModal({
        isOpen: true,
        teacher,
        eligibility: el,
        isLoading: false,
      })
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al verificar aptitud docente'))
      setEligibilityModal({ isOpen: false, teacher: null, eligibility: null, isLoading: false })
    }
  }

  const handleOpenProvision = (t: TeacherResponse) => {
    setProvisionModal({
      isOpen: true,
      teacher: t,
      email: t.user?.email || '',
      isSubmitting: false,
      error: null,
    })
  }

  const handleExecuteProvision = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!provisionModal.teacher) return
    setProvisionModal((prev) => ({ ...prev, isSubmitting: true, error: null }))
    try {
      const res = await academicApi.provisionTeacherAccount(provisionModal.teacher.id, {
        email: provisionModal.email.trim() || undefined,
      })
      setSuccessMsg(res.message)
      const docName = provisionModal.teacher.user
        ? `${provisionModal.teacher.user.first_name} ${provisionModal.teacher.user.last_name}`
        : 'Docente'
      const teacherEmail = provisionModal.email.trim() || provisionModal.teacher.user?.email || ''
      setProvisionModal({ isOpen: false, teacher: null, email: '', isSubmitting: false, error: null })
      if (res.reset_token) {
        const origin = window.location.origin
        setOnboardingModal({
          isOpen: true,
          title: 'Cuenta Docente Aprovisionada',
          teacherName: docName,
          teacherEmail,
          setupUrl: `${origin}/auth/reset-password?token=${encodeURIComponent(res.reset_token)}`,
          portalUrl: `${origin}/teacher`,
          copiedSetup: false,
          copiedPortal: false,
        })
      }
      await loadTeachers()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al aprovisionar cuenta de acceso.'
      setProvisionModal((prev) => ({ ...prev, isSubmitting: false, error: msg }))
    }
  }

  const handleToggleStatus = async (t: TeacherResponse, targetActive: boolean) => {
    setError(null)
    try {
      const res = await academicApi.updateTeacherAccountStatus(t.id, targetActive)
      setSuccessMsg(res.message)
      await loadTeachers()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al actualizar estado de cuenta docente.'))
    }
  }

  const handleResetPassword = async (t: TeacherResponse) => {
    setError(null)
    try {
      const res = await academicApi.resetTeacherPassword(t.id)
      setSuccessMsg(res.message)
      const docName = t.user ? `${t.user.first_name} ${t.user.last_name}` : 'Docente'
      const teacherEmail = t.user?.email || ''
      if (res.reset_token) {
        const origin = window.location.origin
        setOnboardingModal({
          isOpen: true,
          title: 'Enlace de Restablecimiento de Clave Generado',
          teacherName: docName,
          teacherEmail,
          setupUrl: `${origin}/auth/reset-password?token=${encodeURIComponent(res.reset_token)}`,
          portalUrl: `${origin}/teacher`,
          copiedSetup: false,
          copiedPortal: false,
        })
      }
      await loadTeachers()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al solicitar restablecimiento de clave.'))
    }
  }

  const getContractBadge = (ct: TeacherContractType) => {
    switch (ct) {
      case 'PROPIEDAD':
        return <Badge variant="success">PROPIEDAD</Badge>
      case 'PERIODO_PRUEBA':
        return <Badge variant="warning">PERIODO PRUEBA</Badge>
      case 'PROVISIONAL':
        return <Badge variant="info">PROVISIONAL</Badge>
      default:
        return <Badge variant="neutral">{ct}</Badge>
    }
  }

  const getAccountStatusBadge = (status?: TeacherAccountStatus) => {
    switch (status) {
      case 'ACTIVA':
        return <Badge variant="success">ACTIVA</Badge>
      case 'INACTIVA':
        return <Badge variant="danger">INACTIVA</Badge>
      case 'SIN_CUENTA':
      default:
        return <Badge variant="neutral">SIN CUENTA</Badge>
    }
  }

  return (
    <div>
      {/* Notifications */}
      {error && <Alert error={error} onClose={() => { setError(null) }} />}
      {successMsg && (
        <Alert variant="success" message={successMsg} onClose={() => { setSuccessMsg(null) }} />
      )}

      {/* Action Bar */}
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
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <label style={{ fontSize: '0.875rem', fontWeight: 600, color: '#475569' }}>
            Filtrar por Vinculación:
          </label>
          <select
            value={contractFilter ?? ''}
            onChange={(e) => {
              const val = e.target.value as TeacherContractType | ''
              setContractFilter(val ? val : undefined)
            }}
            style={{
              padding: '0.45rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              backgroundColor: '#FFFFFF',
              fontSize: '0.875rem',
              color: '#0F172A',
            }}
          >
            <option value="">Todos los Tipos de Vinculación</option>
            <option value="PROPIEDAD">Carrera Docente (Propiedad)</option>
            <option value="PERIODO_PRUEBA">Período de Prueba</option>
            <option value="PROVISIONAL">Provisional</option>
            <option value="TEMPORAL">Temporal</option>
            <option value="HORA_CATEDRA">Hora Cátedra</option>
          </select>
        </div>

        {hasPermission('teachers:create') && (
          <Button
            variant="primary"
            onClick={() => {
              setIsCreateOpen(true)
            }}
          >
            + Registrar Perfil Docente
          </Button>
        )}
      </div>

      {/* Table Card */}
      <Card
        title="Planta Docente Institucional"
        subtitle={`Total de docentes registrados: ${String(total)}`}
        action={
          <Button variant="secondary" size="sm" onClick={() => void loadTeachers()}>
            Refrescar
          </Button>
        }
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando planta docente...
            </p>
          </div>
        ) : teachers.length === 0 ? (
          <EmptyState
            icon="👩‍🏫"
            title="No hay docentes registrados"
            description="No se encontraron perfiles docentes para los criterios seleccionados."
            actionLabel={hasPermission('teachers:create') ? '+ Registrar Primer Docente' : undefined}
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
                  <th style={{ padding: '0.75rem 1rem' }}>Docente</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Especialidad</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Vinculación</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Escalafón</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Estado de Cuenta</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {teachers.map((t) => (
                  <tr key={t.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                      {t.user ? `${t.user.first_name} ${t.user.last_name}` : t.user_id}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#1E293B' }}>
                      {t.specialty_area || 'Área General'}
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>{getContractBadge(t.contract_type)}</td>
                    <td style={{ padding: '0.875rem 1rem', color: '#64748B' }}>
                      Grado {t.escalafon_grade || 'N/A'}
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      {getAccountStatusBadge(t.account_status)}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                        {t.account_status === 'SIN_CUENTA' && hasPermission('teachers:create') && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => { handleOpenProvision(t) }}
                          >
                            + Crear Cuenta
                          </Button>
                        )}
                        {t.account_status === 'ACTIVA' && hasPermission('teachers:update') && (
                          <>
                            <Button
                              variant="danger"
                              size="sm"
                              onClick={() => void handleToggleStatus(t, false)}
                            >
                              Desactivar
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => void handleResetPassword(t)}
                            >
                              Restablecer Clave
                            </Button>
                          </>
                        )}
                        {t.account_status === 'INACTIVA' && hasPermission('teachers:update') && (
                          <>
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => void handleToggleStatus(t, true)}
                            >
                              Activar
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => void handleResetPassword(t)}
                            >
                              Restablecer Clave
                            </Button>
                          </>
                        )}
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => void handleCheckEligibility(t)}
                        >
                          Verificar Aptitud
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Eligibility Modal */}
      <Modal
        isOpen={eligibilityModal.isOpen}
        onClose={() => {
          setEligibilityModal({ isOpen: false, teacher: null, eligibility: null, isLoading: false })
        }}
        title={`Aptitud y Estado de Asignación Docente`}
        subtitle={
          eligibilityModal.teacher?.user
            ? `${eligibilityModal.teacher.user.first_name} ${eligibilityModal.teacher.user.last_name}`
            : ''
        }
        maxWidth="sm"
      >
        {eligibilityModal.isLoading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <LoadingSpinner size="md" />
            <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '0.5rem' }}>
              Validando habilitación académica...
            </p>
          </div>
        ) : eligibilityModal.eligibility ? (
          <div>
            <div
              style={{
                padding: '1.5rem',
                backgroundColor: eligibilityModal.eligibility.is_eligible ? '#ECFDF5' : '#FEF2F2',
                border: `1px solid ${eligibilityModal.eligibility.is_eligible ? '#A7F3D0' : '#FECACA'}`,
                borderRadius: '12px',
                textAlign: 'center',
                marginBottom: '1.5rem',
              }}
            >
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
                {eligibilityModal.eligibility.is_eligible ? '✅' : '❌'}
              </div>
              <h4
                style={{
                  margin: '0 0 0.5rem 0',
                  color: eligibilityModal.eligibility.is_eligible ? '#065F46' : '#991B1B',
                  fontSize: '1.125rem',
                  fontWeight: 700,
                }}
              >
                {eligibilityModal.eligibility.is_eligible
                  ? 'Docente Apto y Habilitado'
                  : 'Docente No Habilitado'}
              </h4>
              <p
                style={{
                  margin: 0,
                  fontSize: '0.875rem',
                  color: eligibilityModal.eligibility.is_eligible ? '#047857' : '#B91C1C',
                }}
              >
                {eligibilityModal.eligibility.message}
              </p>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="secondary"
                onClick={() => {
                  setEligibilityModal({ isOpen: false, teacher: null, eligibility: null, isLoading: false })
                }}
              >
                Cerrar
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>

      {/* Create Teacher Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false)
          resetCreateForm()
        }}
        title="Registrar Perfil Docente"
        subtitle={
          isRegisteringNewUser
            ? "Aprovisionamiento de nuevo docente institucional."
            : "Vincule una cuenta de usuario existente o aprovisione un nuevo docente institucional."
        }
      >
        <form onSubmit={(e) => void handleCreateTeacher(e)}>
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
            /* Mode B: Inline Civil Identity Provisioning */
            <div style={{ marginBottom: '1.25rem' }}>
              <div
                style={{
                  padding: '0.75rem 1rem',
                  backgroundColor: '#EFF6FF',
                  border: '1px solid #BFDBFE',
                  borderRadius: '8px',
                  marginBottom: '1rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ fontWeight: 700, color: '#1E40AF', fontSize: '0.875rem' }}>
                    🆕 Nuevo Docente Institucional
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#3B82F6', marginTop: '0.1rem' }}>
                    Se creará la cuenta institucional y se asignará automáticamente el rol de Docente.
                  </div>
                </div>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setIsRegisteringNewUser(false)
                  }}
                >
                  ← Buscar Existente
                </Button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Nombres del Docente *
                  </label>
                  <input
                    type="text"
                    value={newFirstName}
                    onChange={(e) => setNewFirstName(e.target.value)}
                    required
                    placeholder="Ej. Carlos Alberto"
                    style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', fontSize: '0.875rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Apellidos del Docente *
                  </label>
                  <input
                    type="text"
                    value={newLastName}
                    onChange={(e) => setNewLastName(e.target.value)}
                    required
                    placeholder="Ej. Gómez Restrepo"
                    style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', fontSize: '0.875rem' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '130px 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Tipo Doc. *
                  </label>
                  <select
                    value={newDocType}
                    onChange={(e) => setNewDocType(e.target.value)}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', fontSize: '0.875rem' }}
                  >
                    <option value="CC">CC - Cédula</option>
                    <option value="CE">CE - Extranjería</option>
                    <option value="TI">TI - Tarjeta Id</option>
                    <option value="PEP">PEP</option>
                    <option value="PPT">PPT</option>
                    <option value="PASSPORT">Pasaporte</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Número de Documento *
                  </label>
                  <input
                    type="text"
                    value={newDocNumber}
                    onChange={(e) => setNewDocNumber(e.target.value)}
                    required
                    placeholder="Ej. 20202020"
                    style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', fontSize: '0.875rem' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Correo Electrónico Institucional *
                  </label>
                  <input
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    required
                    placeholder="carlos.gomez@colegio.edu.co"
                    style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', fontSize: '0.875rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Teléfono (Opcional)
                  </label>
                  <input
                    type="tel"
                    value={newPhone}
                    onChange={(e) => setNewPhone(e.target.value)}
                    placeholder="Ej. 3001234567"
                    style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box', fontSize: '0.875rem' }}
                  />
                </div>
              </div>
            </div>
          ) : (
            /* Mode A: Search and Link Existing Institutional User */
            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                Usuario Institucional *
              </label>

              {selectedUser ? (
                <div
                  style={{
                    padding: '0.875rem 1rem',
                    backgroundColor: '#F0FDF4',
                    border: '1px solid #86EFAC',
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, color: '#166534', fontSize: '0.9375rem' }}>
                      ✓ {selectedUser.first_name} {selectedUser.last_name}
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: '#15803D', marginTop: '0.15rem' }}>
                      Documento: {selectedUser.document_type} {selectedUser.document_number} | Correo: {selectedUser.email}
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setSelectedUser(null)
                      setUserSearchQuery('')
                      setUserSearchResults([])
                    }}
                  >
                    Cambiar
                  </Button>
                </div>
              ) : (
                <div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <input
                      type="text"
                      value={userSearchQuery}
                      onChange={(e) => void handleSearchUsers(e.target.value)}
                      placeholder="Buscar por documento (ej. 8788), nombre o correo..."
                      style={{
                        width: '100%',
                        padding: '0.625rem',
                        borderRadius: '6px',
                        border: '1px solid #CBD5E1',
                        boxSizing: 'border-box',
                        fontSize: '0.875rem',
                      }}
                    />
                    {isSearchingUsers && (
                      <div style={{ display: 'flex', alignItems: 'center', padding: '0 0.5rem' }}>
                        <LoadingSpinner size="sm" />
                      </div>
                    )}
                  </div>

                  {userSearchResults.length > 0 && (
                    <div
                      style={{
                        marginTop: '0.5rem',
                        maxHeight: '180px',
                        overflowY: 'auto',
                        border: '1px solid #E2E8F0',
                        borderRadius: '6px',
                        backgroundColor: '#FFFFFF',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
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
                            padding: '0.6rem 0.85rem',
                            borderBottom: '1px solid #F1F5F9',
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            transition: 'background-color 0.15s ease',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = '#F8FAFC'
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = '#FFFFFF'
                          }}
                        >
                          <div>
                            <div style={{ fontWeight: 600, fontSize: '0.875rem', color: '#0F172A' }}>
                              {u.first_name} {u.last_name}
                            </div>
                            <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                              {u.document_type} {u.document_number} · {u.email}
                            </div>
                          </div>
                          <Button type="button" variant="primary" size="sm">
                            Seleccionar
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}

                  {userSearchQuery.trim().length > 0 && (
                    <div
                      style={{
                        marginTop: '0.75rem',
                        padding: '0.75rem 1rem',
                        backgroundColor: '#F8FAFC',
                        border: '1px dashed #CBD5E1',
                        borderRadius: '8px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: '0.5rem',
                        flexWrap: 'wrap',
                      }}
                    >
                      <div style={{ fontSize: '0.8125rem', color: '#475569' }}>
                        {userSearchResults.length === 0 && !isSearchingUsers ? (
                          <span>No existe una cuenta institucional para <strong>"{userSearchQuery}"</strong>.</span>
                        ) : (
                          <span>¿El docente aún no tiene cuenta de usuario?</span>
                        )}
                      </div>
                      <Button
                        type="button"
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          setIsRegisteringNewUser(true)
                          if (/^\d+$/.test(userSearchQuery.trim())) {
                            setNewDocNumber(userSearchQuery.trim())
                          }
                        }}
                      >
                        + Registrar como nuevo docente en la institución
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Professional Appointment Details */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Área de Especialidad / Título Profesional *
            </label>
            <input
              type="text"
              value={specialtyArea}
              onChange={(e) => {
                setSpecialtyArea(e.target.value)
              }}
              required
              placeholder="Licenciatura en Matemáticas, Física, etc."
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Tipo de Nombramiento / Vinculación *
              </label>
              <select
                value={contractType}
                onChange={(e) => {
                  setContractType(e.target.value as TeacherContractType)
                }}
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              >
                <option value="PROPIEDAD">Propiedad (Carrera Docente)</option>
                <option value="PERIODO_PRUEBA">Período de Prueba</option>
                <option value="PROVISIONAL">Provisional</option>
                <option value="TEMPORAL">Temporal</option>
                <option value="HORA_CATEDRA">Hora Cátedra</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Grado Escalafón Docente (Decreto 1278 / 2277)
              </label>
              <input
                type="text"
                value={escalafonGrade}
                onChange={(e) => {
                  setEscalafonGrade(e.target.value)
                }}
                placeholder="14, 2A, 3D, etc."
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
          </div>

          {/* Account Provisioning Option */}
          <div
            style={{
              marginBottom: '1.5rem',
              padding: '0.875rem 1rem',
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              borderRadius: '8px',
            }}
          >
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.625rem',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: 600,
                color: '#1E293B',
              }}
            >
              <input
                type="checkbox"
                checked={provisionAccountNow}
                onChange={(e) => setProvisionAccountNow(e.target.checked)}
                style={{ width: '1.1rem', height: '1.1rem', accentColor: '#2563EB', cursor: 'pointer' }}
              />
              <span>Aprovisionar y activar credenciales de acceso docente inmediatamente</span>
            </label>
            <p style={{ margin: '0.35rem 0 0 1.75rem', fontSize: '0.75rem', color: '#64748B' }}>
              {provisionAccountNow
                ? 'Se asignará el rol docente, se activará la cuenta y se habilitará el ingreso al Portal Docente (/teacher).'
                : 'El perfil docente se registrará en estado "SIN CUENTA". Podrá aprovisionar el acceso más adelante desde la tabla.'}
            </p>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setIsCreateOpen(false)
                resetCreateForm()
              }}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Guardar Docente'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Provision Teacher Account Modal */}
      <Modal
        isOpen={provisionModal.isOpen}
        onClose={() => {
          setProvisionModal({ isOpen: false, teacher: null, email: '', isSubmitting: false, error: null })
        }}
        title="Crear Cuenta de Acceso Docente"
        subtitle="Aprovisionamiento de credenciales institucionales para el educador."
        maxWidth="sm"
      >
        <form onSubmit={(e) => void handleExecuteProvision(e)}>
          {provisionModal.error && (
            <div style={{ marginBottom: '1rem' }}>
              <Alert
                variant="error"
                message={provisionModal.error}
                onClose={() => { setProvisionModal((prev) => ({ ...prev, error: null })) }}
              />
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
            <div
              style={{
                padding: '1rem',
                backgroundColor: '#F8FAFC',
                border: '1px solid #E2E8F0',
                borderRadius: '8px',
              }}
            >
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.25rem' }}>
                {provisionModal.teacher?.user
                  ? `${provisionModal.teacher.user.first_name} ${provisionModal.teacher.user.last_name}`
                  : 'Docente Institucional'}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                Documento: {provisionModal.teacher?.user?.document_type ?? 'CC'} {provisionModal.teacher?.user?.document_number ?? 'N/A'} • Especialidad: {provisionModal.teacher?.specialty_area ?? 'General'}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Correo Electrónico Institucional *
              </label>
              <input
                type="email"
                required
                value={provisionModal.email}
                onChange={(e) => {
                  setProvisionModal((prev) => ({ ...prev, email: e.target.value }))
                }}
                placeholder="docente@colegio.edu.co"
                style={{
                  width: '100%',
                  padding: '0.625rem',
                  borderRadius: '6px',
                  border: '1px solid #CBD5E1',
                  boxSizing: 'border-box',
                }}
              />
              <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block', marginTop: '0.25rem' }}>
                Se enviará o configurará la clave temporal para el primer inicio de sesión del educador.
              </span>
            </div>

            <div
              style={{
                padding: '0.75rem',
                backgroundColor: '#EFF6FF',
                border: '1px solid #BFDBFE',
                borderRadius: '8px',
                fontSize: '0.8125rem',
                color: '#1E40AF',
              }}
            >
              ℹ️ Al confirmar, se asignará el rol canónico <strong>DOCENTE</strong> y se habilitará el acceso al <strong>Portal Docente (/teacher)</strong>. El docente deberá actualizar su clave en el primer acceso.
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setProvisionModal({ isOpen: false, teacher: null, email: '', isSubmitting: false, error: null })
              }}
              disabled={provisionModal.isSubmitting}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={provisionModal.isSubmitting}>
              {provisionModal.isSubmitting ? <LoadingSpinner size="sm" /> : 'Crear Cuenta'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Onboarding Credentials Delivery Modal */}
      <Modal
        isOpen={onboardingModal.isOpen}
        onClose={() => {
          setOnboardingModal({
            isOpen: false,
            title: '',
            teacherName: '',
            teacherEmail: '',
            setupUrl: null,
            portalUrl: '',
            copiedSetup: false,
            copiedPortal: false,
          })
        }}
        title={onboardingModal.title || "Credenciales de Acceso Docente"}
        subtitle="Enlace seguro para configuración de contraseña y acceso al portal."
        maxWidth="md"
      >
        <div>
          {/* Header Summary Box */}
          <div
            style={{
              padding: '1.25rem',
              backgroundColor: '#F0FDF4',
              border: '1px solid #BBF7D0',
              borderRadius: '10px',
              marginBottom: '1.25rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: '#DCFCE7',
                  color: '#166534',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  fontSize: '1.125rem',
                  flexShrink: 0,
                }}
              >
                ✓
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#14532D' }}>
                  {onboardingModal.teacherName}
                </h4>
                <div style={{ fontSize: '0.8125rem', color: '#166534' }}>
                  Correo Institucional: <strong>{onboardingModal.teacherEmail || 'No especificado'}</strong> · Estado: <Badge variant="success">ACTIVA</Badge>
                </div>
              </div>
            </div>
            <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.8125rem', color: '#15803D', lineHeight: 1.45 }}>
              La cuenta institucional ha sido habilitada exitosamente. El docente debe ingresar al enlace de configuración para establecer su propia contraseña antes de iniciar sesión.
            </p>
          </div>

          {/* Setup Link Section */}
          {onboardingModal.setupUrl && (
            <div
              style={{
                padding: '1.25rem',
                backgroundColor: '#FFFFFF',
                border: '1px solid #E2E8F0',
                borderRadius: '10px',
                marginBottom: '1rem',
                boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <label style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#1E293B', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  🔑 Enlace de Configuración de Contraseña
                </label>
                <span style={{ fontSize: '0.75rem', color: '#64748B', backgroundColor: '#F1F5F9', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
                  Uso Único · 1 Hora
                </span>
              </div>

              <div
                style={{
                  padding: '0.625rem 0.875rem',
                  backgroundColor: '#F8FAFC',
                  border: '1px solid #CBD5E1',
                  borderRadius: '6px',
                  fontSize: '0.8125rem',
                  color: '#334155',
                  fontFamily: 'monospace',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  marginBottom: '0.75rem',
                }}
                title={onboardingModal.setupUrl}
              >
                {onboardingModal.setupUrl.length > 55
                  ? `${onboardingModal.setupUrl.substring(0, 48)}...`
                  : onboardingModal.setupUrl}
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <Button
                  type="button"
                  variant="primary"
                  size="sm"
                  onClick={async () => {
                    if (onboardingModal.setupUrl) {
                      try {
                        await navigator.clipboard.writeText(onboardingModal.setupUrl)
                        setOnboardingModal((prev) => ({ ...prev, copiedSetup: true, copiedPortal: false }))
                      } catch {
                        // fallback
                      }
                    }
                  }}
                >
                  {onboardingModal.copiedSetup ? '✓ Enlace Copiado' : 'Copiar Enlace de Configuración'}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    if (onboardingModal.setupUrl) {
                      window.open(onboardingModal.setupUrl, '_blank')
                    }
                  }}
                >
                  Abrir Enlace ↗
                </Button>
              </div>
            </div>
          )}

          {/* Teacher Portal Link Section */}
          <div
            style={{
              padding: '1.25rem',
              backgroundColor: '#FFFFFF',
              border: '1px solid #E2E8F0',
              borderRadius: '10px',
              marginBottom: '1.25rem',
              boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
            }}
          >
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#1E293B', marginBottom: '0.5rem' }}>
              🌐 Acceso al Portal Docente
            </label>
            <div
              style={{
                padding: '0.625rem 0.875rem',
                backgroundColor: '#F8FAFC',
                border: '1px solid #CBD5E1',
                borderRadius: '6px',
                fontSize: '0.8125rem',
                color: '#334155',
                fontFamily: 'monospace',
                marginBottom: '0.75rem',
              }}
            >
              {onboardingModal.portalUrl}
            </div>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(onboardingModal.portalUrl)
                  setOnboardingModal((prev) => ({ ...prev, copiedPortal: true, copiedSetup: false }))
                } catch {
                  // fallback
                }
              }}
            >
              {onboardingModal.copiedPortal ? '✓ Acceso Copiado' : 'Copiar Acceso al Portal'}
            </Button>
          </div>

          {/* Security Notice */}
          <p style={{ fontSize: '0.75rem', color: '#64748B', lineHeight: 1.4, margin: '0 0 1.25rem 0' }}>
            ℹ️ <strong>Seguridad Institucional:</strong> El enlace de configuración es personal y confidencial. Permite al docente establecer su clave sin intermediarios. Nunca almacene ni envíe contraseñas en texto claro.
          </p>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              type="button"
              variant="primary"
              onClick={() => {
                setOnboardingModal({
                  isOpen: false,
                  title: '',
                  teacherName: '',
                  teacherEmail: '',
                  setupUrl: null,
                  portalUrl: '',
                  copiedSetup: false,
                  copiedPortal: false,
                })
              }}
            >
              Entendido / Cerrar
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default TeachersView
