/**
 * PEVN Frontend — Municipality Administrators & Territorial Provisioning View
 *
 * Professional administrative interface for managing and provisioning MUNICIPALITY_ADMIN users.
 * Supports:
 *   - DEPARTMENT_ADMIN: normal provisioning authority for municipalities in their assigned department
 *   - NATIONAL_ADMIN & SUPERADMIN: supervisory escalation across canonical departments
 *   - Live municipality selector with active-administrator detection to prevent duplicate assignments
 *   - Status management (activate/deactivate) with automatic session invalidation
 *   - Controlled municipality reassignment with automatic session invalidation
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Modal } from '@/components/ui/Modal'
import { useAuth } from '@/hooks/useAuth'
import { municipalityAdminApi } from '@/services/municipalityAdmin'
import { resolveInvitationUrl } from '@/utils'
import type {
  DepartmentOption,
  MunicipalityAdmin,
  MunicipalityAdminCreateRequest,
  MunicipalityAdminInvitationResponse,
  MunicipalityOption,
} from '@/types'

/** Transient, in-memory result of issuing/regenerating an invitation. Never persisted or logged. */
interface InvitationOutcome {
  adminName: string
  email: string
  municipalityName: string
  deliveryStatus: string | null | undefined
  invitationUrl: string | null | undefined
  rawToken?: string | null | undefined
}

export const MunicipalityAdminsView: React.FC = () => {
  const { user, hasRole, hasPermission } = useAuth()
  const [searchParams] = useSearchParams()

  const isNational = hasRole('superadmin') || hasRole('national_admin')
  const isDeptAdmin = hasRole('department_admin')
  const canProvision = hasPermission('municipality_admins:create') || isDeptAdmin || isNational
  const canUpdate = hasPermission('municipality_admins:update') || isDeptAdmin || isNational

  // Data states
  const [admins, setAdmins] = useState<MunicipalityAdmin[]>([])
  const [total, setTotal] = useState<number>(0)
  const [municipalities, setMunicipalities] = useState<MunicipalityOption[]>([])
  const [departments, setDepartments] = useState<DepartmentOption[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isOptionsLoading, setIsOptionsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedDeptFilter, setSelectedDeptFilter] = useState<string>(
    (!isNational && user?.scope.department_id) ? user.scope.department_id : ''
  )
  const [selectedMuniFilter, setSelectedMuniFilter] = useState<string>(
    searchParams.get('municipality_id') || ''
  )
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [page, setPage] = useState<number>(1)
  const pageSize = 12

  // Create Modal State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isCreating, setIsCreating] = useState<boolean>(false)
  const [createDeptId, setCreateDeptId] = useState<string>(
    (!isNational && user?.scope.department_id) ? user.scope.department_id : ''
  )
  const [createMuniId, setCreateMuniId] = useState<string>(
    searchParams.get('municipality_id') || ''
  )
  const [createForm, setCreateForm] = useState<MunicipalityAdminCreateRequest>({
    municipality_id: '',
    first_name: '',
    last_name: '',
    document_type: 'CC',
    document_number: '',
    email: '',
    username: '',
  })
  const [createError, setCreateError] = useState<string | null>(null)

  // Invitation outcome modal (one-time disclosure when SMTP is unavailable in development)
  const [invitationOutcome, setInvitationOutcome] = useState<InvitationOutcome | null>(null)
  const [linkCopied, setLinkCopied] = useState<boolean>(false)
  const [resendTarget, setResendTarget] = useState<MunicipalityAdmin | null>(null)
  const [isResending, setIsResending] = useState<boolean>(false)

  // Status Modal State
  const [statusTargetAdmin, setStatusTargetAdmin] = useState<MunicipalityAdmin | null>(null)
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<boolean>(false)
  const [statusReason, setStatusReason] = useState<string>('')

  // Reassign Modal State
  const [reassignAdmin, setReassignAdmin] = useState<MunicipalityAdmin | null>(null)
  const [reassignMuniId, setReassignMuniId] = useState<string>('')
  const [reassignReason, setReassignReason] = useState<string>('')
  const [isReassigning, setIsReassigning] = useState<boolean>(false)
  const [reassignError, setReassignError] = useState<string | null>(null)

  // Load Departments (for National Admin)
  useEffect(() => {
    if (isNational) {
      municipalityAdminApi.listDepartments().then(setDepartments).catch(() => {})
    }
  }, [isNational])

  // Load Municipalities for Filter & Create
  const loadMunicipalities = useCallback(async (deptId?: string) => {
    setIsOptionsLoading(true)
    try {
      const data = await municipalityAdminApi.listMunicipalities(deptId || undefined)
      setMunicipalities(data)
    } catch {
      // Scoped fallback
    } finally {
      setIsOptionsLoading(false)
    }
  }, [])

  useEffect(() => {
    const targetDept = isNational ? (selectedDeptFilter || undefined) : (user?.scope.department_id || undefined)
    loadMunicipalities(targetDept)
  }, [isNational, selectedDeptFilter, user?.scope.department_id, loadMunicipalities])

  // Synchronize URL search params with loaded canonical municipalities
  useEffect(() => {
    const rawParam = searchParams.get('municipality_id') || searchParams.get('municipality_code')
    if (rawParam && municipalities.length > 0) {
      const match = municipalities.find(
        (m) => m.id.toLowerCase() === rawParam.toLowerCase() || m.code === rawParam
      )
      if (match) {
        setSelectedMuniFilter(match.id)
      }
    }
  }, [searchParams, municipalities])

  // Load Municipality Admins
  const fetchAdmins = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const params = {
        department_id: isNational ? (selectedDeptFilter || undefined) : undefined,
        municipality_id: selectedMuniFilter || undefined,
        is_active: statusFilter === 'all' ? undefined : statusFilter === 'active',
        search: searchQuery.trim() || undefined,
        page,
        page_size: pageSize,
      }
      const res = await municipalityAdminApi.listMunicipalityAdmins(params)
      setAdmins(res.items)
      setTotal(res.total)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar administradores municipales.'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [isNational, selectedDeptFilter, selectedMuniFilter, statusFilter, searchQuery, page, pageSize])

  useEffect(() => {
    fetchAdmins()
  }, [fetchAdmins])

  // Check if target municipality in create form already has an active administrator
  const existingActiveAdminInTargetMuni = useMemo(() => {
    if (!createMuniId) return null
    return admins.find((a) => a.municipality_id === createMuniId && a.is_active) || null
  }, [createMuniId, admins])

  // Open Create Modal
  const handleOpenCreate = () => {
    setCreateError(null)
    const initialDept = (!isNational && user?.scope.department_id) ? user.scope.department_id : ''
    setCreateDeptId(initialDept)
    let initialMuni = selectedMuniFilter || ''
    if (initialMuni) {
      const match = municipalities.find(
        (m) => m.id.toLowerCase() === initialMuni.toLowerCase() || m.code === initialMuni
      )
      if (match) {
        initialMuni = match.id
      }
    }
    setCreateMuniId(initialMuni)
    setCreateForm({
      municipality_id: initialMuni,
      first_name: '',
      last_name: '',
      document_type: 'CC',
      document_number: '',
      email: '',
      username: '',
    })
    setIsCreateOpen(true)
  }

  // Handle Create Submit
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!createMuniId) {
      setCreateError('Debe seleccionar un municipio canónico.')
      return
    }

    // Ensure createMuniId is canonical UUID
    const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(createMuniId)
    let targetMuniId = createMuniId
    if (!isUuid) {
      const match = municipalities.find((m) => m.code === createMuniId || m.id === createMuniId)
      if (match) {
        targetMuniId = match.id
      } else {
        setCreateError('El municipio seleccionado debe ser un municipio canónico válido con identificador de sistema.')
        return
      }
    }

    if (!createForm.first_name.trim() || !createForm.last_name.trim()) {
      setCreateError('Los nombres y apellidos son obligatorios.')
      return
    }
    if (!createForm.email.trim() || !createForm.username.trim()) {
      setCreateError('El correo institucional y el nombre de usuario son obligatorios.')
      return
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(createForm.email.trim())) {
      setCreateError('El correo institucional no tiene un formato válido.')
      return
    }
    setIsCreating(true)
    setCreateError(null)
    try {
      // No credentials are part of the provisioning contract: the user sets their own
      // password through the secure invitation flow.
      const payload: MunicipalityAdminCreateRequest = {
        municipality_id: targetMuniId,
        first_name: createForm.first_name.trim(),
        last_name: createForm.last_name.trim(),
        document_type: createForm.document_type || 'CC',
        document_number: createForm.document_number?.trim() || undefined,
        email: createForm.email.trim().toLowerCase(),
        username: createForm.username.trim(),
      }

      const created = await municipalityAdminApi.createMunicipalityAdmin(payload)
      setSuccessMsg(
        `Cuenta de "${created.full_name}" creada para ${created.municipality_name}. ` +
          'La cuenta permanece inactiva hasta que el administrador complete su invitación.'
      )
      setIsCreateOpen(false)
      setLinkCopied(false)
      setInvitationOutcome({
        adminName: created.full_name,
        email: created.email,
        municipalityName: created.municipality_name,
        deliveryStatus: created.email_delivery_status,
        invitationUrl: created.invitation_url,
        rawToken: created.raw_invitation_token,
      })
      fetchAdmins()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al aprovisionar el administrador municipal.'
      setCreateError(msg)
    } finally {
      setIsCreating(false)
    }
  }

  // Handle invitation regeneration (invalidates any previous pending invitation)
  const handleResendConfirm = async () => {
    if (!resendTarget) return
    setIsResending(true)
    try {
      const res: MunicipalityAdminInvitationResponse = await municipalityAdminApi.resendInvitation(
        resendTarget.id
      )
      setLinkCopied(false)
      setInvitationOutcome({
        adminName: resendTarget.full_name,
        email: res.email,
        municipalityName: res.municipality_name,
        deliveryStatus: res.email_delivery_status,
        invitationUrl: res.invitation_url,
        rawToken: res.raw_invitation_token,
      })
      setResendTarget(null)
      fetchAdmins()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al regenerar la invitación.'
      setResendTarget(null)
      setError(msg)
    } finally {
      setIsResending(false)
    }
  }

  const fullInvitationLink = useMemo(() => {
    return resolveInvitationUrl(
      invitationOutcome?.invitationUrl,
      invitationOutcome?.rawToken
    )
  }, [invitationOutcome])

  const handleCopyInvitationLink = async () => {
    if (!fullInvitationLink) return
    try {
      await navigator.clipboard.writeText(fullInvitationLink.trim())
      setLinkCopied(true)
      setTimeout(() => {
        setLinkCopied(false)
      }, 3000)
    } catch {
      setLinkCopied(false)
    }
  }

  const handleCloseInvitationOutcome = () => {
    // Discard the one-time secret from memory as soon as the operator dismisses the dialog
    setInvitationOutcome(null)
    setLinkCopied(false)
  }

  // Handle Status Update
  const handleStatusSubmit = async () => {
    if (!statusTargetAdmin) return
    setIsUpdatingStatus(true)
    try {
      const newStatus = !statusTargetAdmin.is_active
      await municipalityAdminApi.updateStatus(statusTargetAdmin.id, {
        is_active: newStatus,
        reason: statusReason.trim() || undefined,
      })
      setSuccessMsg(
        `El estado de ${statusTargetAdmin.full_name} fue actualizado a ${newStatus ? 'Activo' : 'Inactivo'}.`
      )
      setStatusTargetAdmin(null)
      setStatusReason('')
      fetchAdmins()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al actualizar el estado del administrador.'
      setError(msg)
    } finally {
      setIsUpdatingStatus(false)
    }
  }

  // Handle Reassign Submit
  const handleReassignSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reassignAdmin || !reassignMuniId) {
      setReassignError('Debe seleccionar el nuevo municipio de destino.')
      return
    }

    setIsReassigning(true)
    setReassignError(null)
    try {
      await municipalityAdminApi.reassignMunicipality(reassignAdmin.id, {
        new_municipality_id: reassignMuniId,
        reason: reassignReason.trim() || undefined,
      })
      setSuccessMsg(`Administrador reasignado exitosamente al nuevo municipio.`)
      setReassignAdmin(null)
      setReassignMuniId('')
      setReassignReason('')
      fetchAdmins()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al reasignar el municipio.'
      setReassignError(msg)
    } finally {
      setIsReassigning(false)
    }
  }

  const handleClearFilters = () => {
    setSearchQuery('')
    if (isNational) setSelectedDeptFilter('')
    setSelectedMuniFilter('')
    setStatusFilter('all')
    setPage(1)
  }

  return (
    <div style={{ maxWidth: '1360px', margin: '0 auto', padding: '1.5rem 1rem' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <span style={{ fontSize: '1.5rem' }}>🏛️</span>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
              Administradores Municipales
            </h1>
          </div>
          <p style={{ color: '#64748B', fontSize: '0.875rem', margin: 0 }}>
            {isDeptAdmin
              ? `Gestión territorial y aprovisionamiento de administradores municipales para su departamento asignado.`
              : `Supervisión y asignación nacional de administradores municipales de educación (NTA-09).`}
          </p>
        </div>

        {canProvision && (
          <Button
            variant="primary"
            onClick={handleOpenCreate}
            style={{ backgroundColor: '#059669', borderColor: '#059669', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <span>➕</span> Asignar administrador municipal
          </Button>
        )}
      </div>

      {/* Notifications */}
      {successMsg && (
        <div style={{ marginBottom: '1rem' }}>
          <Alert variant="success" onClose={() => setSuccessMsg(null)}>
            {successMsg}
          </Alert>
        </div>
      )}
      {error && (
        <div style={{ marginBottom: '1rem' }}>
          <Alert variant="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      {/* Filter Toolbar */}
      <Card style={{ padding: '1rem', marginBottom: '1.5rem', backgroundColor: '#FFFFFF' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', alignItems: 'end' }}>
          {/* Search */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
              Buscar administrador
            </label>
            <input
              type="text"
              placeholder="Nombre, usuario, correo, documento..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setPage(1)
              }}
              style={{ width: '100%', padding: '0.45rem 0.65rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
            />
          </div>

          {/* Department Filter (Only for National/Superadmin) */}
          {isNational && (
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Seleccionar departamento
              </label>
              <select
                value={selectedDeptFilter}
                onChange={(e) => {
                  setSelectedDeptFilter(e.target.value)
                  setSelectedMuniFilter('')
                  setPage(1)
                }}
                style={{ width: '100%', padding: '0.45rem 0.65rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
              >
                <option value="">Todos los departamentos</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.code} — {d.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Municipality Filter */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
              Seleccionar municipio
            </label>
            <select
              value={selectedMuniFilter}
              onChange={(e) => {
                setSelectedMuniFilter(e.target.value)
                setPage(1)
              }}
              disabled={isOptionsLoading}
              style={{ width: '100%', padding: '0.45rem 0.65rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
            >
              <option value="">Todos los municipios</option>
              {municipalities.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.code} — {m.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
              Estado de la cuenta
            </label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as 'all' | 'active' | 'inactive')
                setPage(1)
              }}
              style={{ width: '100%', padding: '0.45rem 0.65rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
            >
              <option value="all">Todos los estados</option>
              <option value="active">Activos</option>
              <option value="inactive">Inactivos</option>
            </select>
          </div>

          {/* Clear Filters */}
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Button variant="secondary" size="sm" onClick={handleClearFilters} style={{ width: '100%' }}>
              Limpiar filtros
            </Button>
          </div>
        </div>
      </Card>

      {/* Directory Table */}
      {isLoading ? (
        <div style={{ padding: '3rem', display: 'flex', justifyContent: 'center' }}>
          <LoadingSpinner size="lg" />
        </div>
      ) : admins.length === 0 ? (
        <Card style={{ padding: '3rem', textAlign: 'center', backgroundColor: '#FFFFFF' }}>
          <EmptyState
            title="No se encontraron administradores municipales"
            description="No hay registros que coincidan con los criterios de búsqueda o territorio seleccionados."
            actionLabel={canProvision ? 'Asignar administrador municipal' : undefined}
            onAction={canProvision ? handleOpenCreate : undefined}
          />
        </Card>
      ) : (
        <Card style={{ backgroundColor: '#FFFFFF', overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8125rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0', color: '#475569', fontWeight: 700 }}>
                  <th style={{ padding: '0.75rem 1rem' }}>ADMINISTRADOR</th>
                  <th style={{ padding: '0.75rem 1rem' }}>MUNICIPIO</th>
                  <th style={{ padding: '0.75rem 1rem' }}>DEPARTAMENTO</th>
                  <th style={{ padding: '0.75rem 1rem' }}>DOCUMENTO</th>
                  <th style={{ padding: '0.75rem 1rem' }}>CORREO INSTITUCIONAL</th>
                  <th style={{ padding: '0.75rem 1rem' }}>ESTADO</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>ACCIONES</th>
                </tr>
              </thead>
              <tbody>
                {admins.map((admin) => (
                  <tr key={admin.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <div style={{ fontWeight: 700, color: '#0F172A' }}>{admin.full_name}</div>
                      <div style={{ fontSize: '0.75rem', color: '#64748B' }}>@{admin.username}</div>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <div style={{ fontWeight: 600, color: '#1E293B' }}>{admin.municipality_name}</div>
                      <div style={{ fontSize: '0.7rem', color: '#64748B', fontFamily: 'monospace' }}>
                        DIVIPOLA: {admin.municipality_code}
                      </div>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <div style={{ color: '#334155' }}>{admin.department_name}</div>
                      <div style={{ fontSize: '0.7rem', color: '#64748B', fontFamily: 'monospace' }}>
                        DANE: {admin.department_code}
                      </div>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: '#475569' }}>
                      <span style={{ fontWeight: 600 }}>{admin.document_type}</span> {admin.document_number}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: '#475569' }}>
                      <a href={`mailto:${admin.email}`} style={{ color: '#2563EB', textDecoration: 'none' }}>
                        {admin.email}
                      </a>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <Badge variant={admin.is_active ? 'success' : admin.is_verified ? 'neutral' : 'warning'}>
                        {admin.is_active
                          ? 'Activo'
                          : admin.is_verified
                          ? 'Inactivo'
                          : 'Inactivo / Pendiente de activación'}
                      </Badge>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                      {canUpdate && (
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                          {admin.is_active || admin.is_verified ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setStatusTargetAdmin(admin)
                                setStatusReason('')
                              }}
                              title={admin.is_active ? 'Desactivar cuenta' : 'Activar cuenta'}
                            >
                              {admin.is_active ? '🔴 Desactivar' : '🟢 Activar'}
                            </Button>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setResendTarget(admin)}
                              title="Regenerar invitación (invalida la anterior)"
                            >
                              ✉️ Regenerar invitación
                            </Button>
                          )}
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              setReassignAdmin(admin)
                              setReassignMuniId('')
                              setReassignReason('')
                              setReassignError(null)
                            }}
                            title="Reasignar a otro municipio"
                          >
                            🔄 Reasignar
                          </Button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div style={{ padding: '0.75rem 1rem', backgroundColor: '#F8FAFC', borderTop: '1px solid #E2E8F0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: '#64748B' }}>
            <span>Total registros: {total}</span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Anterior
              </Button>
              <span style={{ display: 'flex', alignItems: 'center', padding: '0 0.5rem' }}>
                Página {page} de {Math.max(1, Math.ceil(total / pageSize))}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={page * pageSize >= total}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* CREATE MODAL */}
      {isCreateOpen && (
        <Modal
          isOpen={isCreateOpen}
          onClose={() => !isCreating && setIsCreateOpen(false)}
          title="Asignar administrador municipal"
        >
          <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ margin: 0, fontSize: '0.8125rem', color: '#64748B' }}>
              Aprovisionamiento territorial en la estructura de gobernanza institucional PEVN.
            </p>

            {createError && (
              <Alert variant="error" onClose={() => setCreateError(null)}>
                {createError}
              </Alert>
            )}

            {/* Department Selection (For National Admins) */}
            {isNational && (
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#334155', marginBottom: '0.25rem' }}>
                  Seleccionar departamento *
                </label>
                <select
                  value={createDeptId}
                  onChange={(e) => {
                    const deptId = e.target.value
                    setCreateDeptId(deptId)
                    setCreateMuniId('')
                    loadMunicipalities(deptId || undefined)
                  }}
                  required
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
                >
                  <option value="">-- Seleccione un departamento --</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.code} — {d.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Municipality Selection */}
            <div>
              <label htmlFor="create-muni-select" style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#334155', marginBottom: '0.25rem' }}>
                Seleccionar municipio *
              </label>
              <select
                id="create-muni-select"
                value={createMuniId}
                onChange={(e) => {
                  setCreateMuniId(e.target.value)
                  setCreateForm((prev) => ({ ...prev, municipality_id: e.target.value }))
                }}
                required
                disabled={isOptionsLoading}
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
              >
                <option value="">-- Seleccione el municipio canónico --</option>
                {municipalities.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.code} — {m.name} ({m.department_name || 'Dpto'})
                  </option>
                ))}
              </select>
            </div>

            {/* Active Admin Conflict Warning */}
            {existingActiveAdminInTargetMuni && (
              <div style={{ backgroundColor: '#FEF3C7', border: '1px solid #F59E0B', borderRadius: '6px', padding: '0.75rem', fontSize: '0.75rem', color: '#92400E' }}>
                <strong>⚠️ Municipio con Administrador Activo:</strong> Este municipio ya tiene asignado a{' '}
                <strong>{existingActiveAdminInTargetMuni.full_name}</strong> ({existingActiveAdminInTargetMuni.email}). Verifique si requiere reasignación o reemplazo antes de continuar.
              </div>
            )}

            {/* Administrator Identity Fields */}
            <div style={{ borderTop: '1px solid #E2E8F0', paddingTop: '0.75rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#0F172A', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Datos del administrador
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label htmlFor="create-first-name" style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                  Nombres *
                </label>
                <input
                  id="create-first-name"
                  type="text"
                  required
                  value={createForm.first_name}
                  onChange={(e) => setCreateForm({ ...createForm, first_name: e.target.value })}
                  style={{ width: '100%', padding: '0.45rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
                />
              </div>
              <div>
                <label htmlFor="create-last-name" style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                  Apellidos *
                </label>
                <input
                  id="create-last-name"
                  type="text"
                  required
                  value={createForm.last_name}
                  onChange={(e) => setCreateForm({ ...createForm, last_name: e.target.value })}
                  style={{ width: '100%', padding: '0.45rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '0.75rem' }}>
              <div>
                <label htmlFor="create-doc-type" style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                  Tipo de documento
                </label>
                <select
                  id="create-doc-type"
                  value={createForm.document_type}
                  onChange={(e) => setCreateForm({ ...createForm, document_type: e.target.value })}
                  style={{ width: '100%', padding: '0.45rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
                >
                  <option value="CC">Cédula de Ciudadanía (CC)</option>
                  <option value="CE">Cédula de Extranjería (CE)</option>
                  <option value="PEP">PEP</option>
                  <option value="PASSPORT">Pasaporte</option>
                </select>
              </div>
              <div>
                <label htmlFor="create-doc-number" style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                  Número de documento
                </label>
                <input
                  id="create-doc-number"
                  type="text"
                  placeholder="Ej. 1012345678"
                  value={createForm.document_number}
                  onChange={(e) => setCreateForm({ ...createForm, document_number: e.target.value })}
                  style={{ width: '100%', padding: '0.45rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
                />
              </div>
            </div>

            <div>
              <label htmlFor="create-email" style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Correo institucional *
              </label>
              <input
                id="create-email"
                type="email"
                required
                placeholder="administrador@alcaldia.gov.co"
                value={createForm.email}
                onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                style={{ width: '100%', padding: '0.45rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
              />
            </div>

            <div>
              <label htmlFor="create-username" style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Nombre de usuario *
              </label>
              <input
                id="create-username"
                type="text"
                required
                placeholder="admin.municipio"
                value={createForm.username}
                onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
                style={{ width: '100%', padding: '0.45rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
              />
            </div>

            <div style={{ backgroundColor: '#ECFDF5', border: '1px solid #6EE7B7', borderRadius: '6px', padding: '0.75rem', fontSize: '0.75rem', color: '#065F46' }}>
              🔐 <strong>Activación segura por invitación:</strong> no se define ninguna contraseña en este formulario.
              La cuenta se crea <strong>inactiva y pendiente de activación</strong>. El administrador recibirá una invitación
              de un solo uso (vigencia de 48 horas) para establecer su propia contraseña; solo entonces la cuenta se activará.
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
              <Button variant="secondary" type="button" disabled={isCreating} onClick={() => setIsCreateOpen(false)}>
                Cancelar
              </Button>
              <Button
                variant="primary"
                type="submit"
                disabled={isCreating}
                style={{ backgroundColor: '#059669', borderColor: '#059669' }}
              >
                {isCreating ? 'Aprovisionando...' : 'Crear cuenta e invitar'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* INVITATION OUTCOME MODAL */}
      {invitationOutcome && (
        <Modal
          isOpen={Boolean(invitationOutcome)}
          onClose={handleCloseInvitationOutcome}
          title="Invitación de activación"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ margin: 0, fontSize: '0.875rem', color: '#334155' }}>
              Cuenta de <strong>{invitationOutcome.adminName}</strong> ({invitationOutcome.municipalityName}) en estado{' '}
              <strong>Inactivo / Pendiente de activación</strong>. Aún no puede iniciar sesión.
            </p>

            {invitationOutcome.deliveryStatus === 'EMAIL_SENT' ? (
              <Alert variant="success">
                La invitación fue enviada al correo institucional {invitationOutcome.email}. Vence en 48 horas y solo puede usarse una vez.
              </Alert>
            ) : (
              <Alert variant="warning">
                {invitationOutcome.deliveryStatus === 'EMAIL_SEND_FAILED'
                  ? 'El envío del correo falló.'
                  : 'El envío de correo no está disponible (SMTP no configurado).'}{' '}
                La invitación debe entregarse al administrador mediante un proceso manual seguro y aprobado.
              </Alert>
            )}

            {fullInvitationLink ? (
              <div style={{ backgroundColor: '#FEF3C7', border: '1px solid #F59E0B', borderRadius: '6px', padding: '0.75rem', fontSize: '0.75rem', color: '#92400E', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <strong>⚠️ Enlace de un solo uso (solo entorno de desarrollo)</strong>
                <span>
                  Este enlace se muestra una única vez y desaparecerá al cerrar este diálogo. Entréguelo únicamente a {invitationOutcome.email} por un canal seguro. Si lo pierde, regenere la invitación.
                </span>
                <input
                  type="text"
                  readOnly
                  aria-label="Enlace de invitación de un solo uso"
                  value={fullInvitationLink}
                  onFocus={(e) => e.currentTarget.select()}
                  style={{ width: '100%', padding: '0.45rem', border: '1px solid #F59E0B', borderRadius: '6px', fontSize: '0.75rem', fontFamily: 'monospace' }}
                />
                <div>
                  <Button variant="secondary" size="sm" onClick={handleCopyInvitationLink}>
                    {linkCopied ? '✅ Copiado' : '📋 Copiar enlace'}
                  </Button>
                </div>
              </div>
            ) : (
              <p style={{ margin: 0, fontSize: '0.75rem', color: '#64748B' }}>
                Por seguridad, el enlace de invitación no se muestra en este entorno.
              </p>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="primary" onClick={handleCloseInvitationOutcome}>
                Cerrar
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* RESEND INVITATION CONFIRMATION MODAL */}
      {resendTarget && (
        <Modal
          isOpen={Boolean(resendTarget)}
          onClose={() => !isResending && setResendTarget(null)}
          title="Regenerar invitación"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ margin: 0, fontSize: '0.875rem', color: '#334155' }}>
              ¿Desea regenerar la invitación de <strong>{resendTarget.full_name}</strong> ({resendTarget.municipality_name})?
            </p>
            <div style={{ backgroundColor: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: '6px', padding: '0.75rem', fontSize: '0.75rem', color: '#1E40AF' }}>
              ℹ️ <strong>Aviso de seguridad:</strong> la invitación anterior quedará invalidada de inmediato. La nueva vence en 48 horas y solo puede usarse una vez.
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button variant="secondary" disabled={isResending} onClick={() => setResendTarget(null)}>
                Cancelar
              </Button>
              <Button variant="primary" disabled={isResending} onClick={handleResendConfirm}>
                {isResending ? 'Generando...' : 'Regenerar invitación'}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* STATUS CHANGE MODAL */}
      {statusTargetAdmin && (
        <Modal
          isOpen={Boolean(statusTargetAdmin)}
          onClose={() => !isUpdatingStatus && setStatusTargetAdmin(null)}
          title={statusTargetAdmin.is_active ? 'Desactivar Administrador Municipal' : 'Activar Administrador Municipal'}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ margin: 0, fontSize: '0.875rem', color: '#334155' }}>
              ¿Está seguro de que desea {statusTargetAdmin.is_active ? 'desactivar' : 'activar'} la cuenta de{' '}
              <strong>{statusTargetAdmin.full_name}</strong> ({statusTargetAdmin.municipality_name})?
            </p>

            {statusTargetAdmin.is_active && (
              <div style={{ backgroundColor: '#FEF2F2', border: '1px solid #F87171', borderRadius: '6px', padding: '0.75rem', fontSize: '0.75rem', color: '#991B1B' }}>
                ℹ️ <strong>Aviso de seguridad:</strong> Al desactivar la cuenta, se revocarán automáticamente todas las sesiones y tokens de actualización activos.
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Motivo administrativo (opcional)
              </label>
              <textarea
                rows={2}
                placeholder="Justificación del cambio de estado..."
                value={statusReason}
                onChange={(e) => setStatusReason(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button variant="secondary" disabled={isUpdatingStatus} onClick={() => setStatusTargetAdmin(null)}>
                Cancelar
              </Button>
              <Button
                variant={statusTargetAdmin.is_active ? 'danger' : 'primary'}
                disabled={isUpdatingStatus}
                onClick={handleStatusSubmit}
              >
                {isUpdatingStatus
                  ? 'Guardando...'
                  : statusTargetAdmin.is_active
                  ? 'Confirmar desactivación'
                  : 'Confirmar activación'}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* REASSIGN MUNICIPALITY MODAL */}
      {reassignAdmin && (
        <Modal
          isOpen={Boolean(reassignAdmin)}
          onClose={() => !isReassigning && setReassignAdmin(null)}
          title="Reasignar Administrador a Nuevo Municipio"
        >
          <form onSubmit={handleReassignSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ margin: 0, fontSize: '0.875rem', color: '#334155' }}>
              Reasignar a <strong>{reassignAdmin.full_name}</strong> (Actualmente en {reassignAdmin.municipality_name}).
            </p>

            {reassignError && (
              <Alert variant="error" onClose={() => setReassignError(null)}>
                {reassignError}
              </Alert>
            )}

            <div style={{ backgroundColor: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: '6px', padding: '0.75rem', fontSize: '0.75rem', color: '#1E40AF' }}>
              ℹ️ <strong>Aviso de seguridad:</strong> La reasignación invalida inmediatamente las sesiones activas para que el nuevo alcance territorial se aplique en el siguiente inicio de sesión.
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#334155', marginBottom: '0.25rem' }}>
                Nuevo municipio de destino *
              </label>
              <select
                value={reassignMuniId}
                onChange={(e) => setReassignMuniId(e.target.value)}
                required
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
              >
                <option value="">-- Seleccione el nuevo municipio --</option>
                {municipalities
                  .filter((m) => m.id !== reassignAdmin.municipality_id)
                  .map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.code} — {m.name} ({m.department_name || 'Dpto'})
                    </option>
                  ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Motivo de la reasignación (opcional)
              </label>
              <textarea
                rows={2}
                placeholder="Resolución administrativa o justificación..."
                value={reassignReason}
                onChange={(e) => setReassignReason(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '0.8125rem' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button variant="secondary" type="button" disabled={isReassigning} onClick={() => setReassignAdmin(null)}>
                Cancelar
              </Button>
              <Button variant="primary" type="submit" disabled={isReassigning}>
                {isReassigning ? 'Reasignando...' : 'Confirmar reasignación'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
export default MunicipalityAdminsView
