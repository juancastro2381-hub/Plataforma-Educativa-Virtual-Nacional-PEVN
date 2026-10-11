/**
 * PEVN Frontend — Department Administrators & Territorial Provisioning View
 *
 * Professional SaaS administration interface for SUPER_ADMIN & NATIONAL_ADMIN users.
 * Features:
 *   - Departmental administrator listing with search, department filter, and status filter
 *   - Real-time KPI summary cards (Total, Departamentos Asignados, Activos, Inactivos)
 *   - Dynamic Colombian department selector populated strictly from backend API (never hardcoded)
 *   - Transactional provisioning of DEPARTMENT_ADMIN with canonical department binding
 *   - Profile editing (first name, last name, email, username)
 *   - Controlled department reassignment with automatic active session invalidation
 *   - Controlled activation/deactivation with instant session revocation
 */

import React, { useCallback, useEffect, useState } from 'react'
import { departmentAdminApi } from '@/services/departmentAdmin'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Modal } from '@/components/ui/Modal'
import { resolveInvitationUrl } from '@/utils'
import type {
  DepartmentAdmin,
  DepartmentAdminCreateRequest,
  DepartmentAdminKPIs,
  DepartmentAdminUpdateRequest,
  DepartmentOption,
  EmailDeliveryStatus,
} from '@/types'

export const DepartmentAdminsView: React.FC = () => {
  // Data states
  const [admins, setAdmins] = useState<DepartmentAdmin[]>([])
  const [departments, setDepartments] = useState<DepartmentOption[]>([])
  const [total, setTotal] = useState<number>(0)
  const [kpis, setKpis] = useState<DepartmentAdminKPIs>({
    total: 0,
    active: 0,
    inactive: 0,
    departments_covered: 0,
    total_canonical_departments: 33,
  })
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isDeptLoading, setIsDeptLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Filters & Pagination
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedDeptFilter, setSelectedDeptFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [page, setPage] = useState<number>(1)
  const pageSize = 10

  // Create Modal State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isCreating, setIsCreating] = useState<boolean>(false)
  const [createForm, setCreateForm] = useState<DepartmentAdminCreateRequest>({
    first_name: '',
    last_name: '',
    email: '',
    username: '',
    department_id: '',
  })
  const [createError, setCreateError] = useState<string | null>(null)

  // Edit Modal State
  const [editingAdmin, setEditingAdmin] = useState<DepartmentAdmin | null>(null)
  const [isEditing, setIsEditing] = useState<boolean>(false)
  const [editForm, setEditForm] = useState<DepartmentAdminUpdateRequest>({
    first_name: '',
    last_name: '',
    email: '',
    username: '',
  })
  const [editError, setEditError] = useState<string | null>(null)

  // Reassign Modal State
  const [reassigningAdmin, setReassigningAdmin] = useState<DepartmentAdmin | null>(null)
  const [isReassigning, setIsReassigning] = useState<boolean>(false)
  const [newDepartmentId, setNewDepartmentId] = useState<string>('')
  const [reassignError, setReassignError] = useState<string | null>(null)

  // Status Change Modal State
  const [statusTargetAdmin, setStatusTargetAdmin] = useState<DepartmentAdmin | null>(null)
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<boolean>(false)

  // Invitation Delivery Fallback & Result Modal State
  interface InvitationResultModalData {
    username: string
    email: string
    deliveryStatus: EmailDeliveryStatus
    activationUrl: string
    isResend: boolean
  }
  const [invitationResult, setInvitationResult] = useState<InvitationResultModalData | null>(null)
  const [copiedLink, setCopiedLink] = useState<boolean>(false)

  const handleCopyLink = () => {
    if (!invitationResult) return
    void navigator.clipboard.writeText(invitationResult.activationUrl)
    setCopiedLink(true)
    setTimeout(() => setCopiedLink(false), 3000)
  }

  const maskEmail = (email: string) => {
    if (!email || !email.includes('@')) return email
    const [local, domain] = email.split('@')
    if (local.length <= 2) return `${local[0]}***@${domain}`
    return `${local[0]}***${local[local.length - 1]}@${domain}`
  }

  // ---------------------------------------------------------------------------
  // Data Loaders
  // ---------------------------------------------------------------------------

  const loadDepartments = useCallback(async () => {
    setIsDeptLoading(true)
    try {
      const data = await departmentAdminApi.listDepartments()
      setDepartments(data)
    } catch (err: unknown) {
      console.error('Error fetching departments:', err)
      setError('No se pudo cargar la lista canónica de departamentos desde el backend.')
    } finally {
      setIsDeptLoading(false)
    }
  }, [])

  const loadAdmins = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const params: Parameters<typeof departmentAdminApi.listDepartmentAdmins>[0] = {
        page,
        page_size: pageSize,
      }
      if (selectedDeptFilter) params.department_id = selectedDeptFilter
      if (statusFilter === 'active') params.is_active = true
      if (statusFilter === 'inactive') params.is_active = false
      if (searchQuery.trim()) params.search = searchQuery.trim()

      const res = await departmentAdminApi.listDepartmentAdmins(params)
      setAdmins(res.items)
      setTotal(res.total)
      if (res.kpis) {
        setKpis(res.kpis)
      }
    } catch (err: unknown) {
      console.error('Error fetching department admins:', err)
      setError('Error al obtener la lista de administradores departamentales.')
    } finally {
      setIsLoading(false)
    }
  }, [page, pageSize, selectedDeptFilter, statusFilter, searchQuery])

  useEffect(() => {
    loadDepartments()
  }, [loadDepartments])

  useEffect(() => {
    loadAdmins()
  }, [loadAdmins])

  // ---------------------------------------------------------------------------
  // Handlers: Create
  // ---------------------------------------------------------------------------
  const handleOpenCreate = () => {
    setCreateForm({
      first_name: '',
      last_name: '',
      email: '',
      username: '',
      department_id: departments.length > 0 ? departments[0].id : '',
    })
    setCreateError(null)
    setIsCreateOpen(true)
  }

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreateError(null)

    if (!createForm.department_id) {
      setCreateError('Debe seleccionar un departamento válido.')
      return
    }
    if (!createForm.username || !createForm.email || !createForm.first_name || !createForm.last_name) {
      setCreateError('Todos los campos son obligatorios.')
      return
    }

    setIsCreating(true)
    try {
      const created = await departmentAdminApi.createDepartmentAdmin(createForm)
      setIsCreateOpen(false)

      const rawToken = created.raw_invitation_token || ''
      const fallbackUrl = resolveInvitationUrl(created.invitation_url, rawToken) || ''

      setInvitationResult({
        username: created.username,
        email: created.email,
        deliveryStatus: created.email_delivery_status || 'EMAIL_NOT_CONFIGURED',
        activationUrl: fallbackUrl,
        isResend: false,
      })
      setCopiedLink(false)
      loadAdmins()
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.message || 'Error al crear el administrador'
      setCreateError(msg)
    } finally {
      setIsCreating(false)
    }
  }

  const handleResendInvitation = async (adm: DepartmentAdmin) => {
    try {
      const res = await departmentAdminApi.resendInvitation(adm.id)
      const rawToken = res.raw_invitation_token || ''
      const fallbackUrl = resolveInvitationUrl(res.invitation_url, rawToken) || ''

      setInvitationResult({
        username: adm.username,
        email: adm.email,
        deliveryStatus: res.email_delivery_status || 'EMAIL_NOT_CONFIGURED',
        activationUrl: fallbackUrl,
        isResend: true,
      })
      setCopiedLink(false)
      loadAdmins()
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.message || 'Error al reenviar la invitación'
      setError(msg)
    }
  }

  // ---------------------------------------------------------------------------
  // Handlers: Edit Profile
  // ---------------------------------------------------------------------------
  const handleOpenEdit = (admin: DepartmentAdmin) => {
    setEditingAdmin(admin)
    setEditForm({
      first_name: admin.first_name,
      last_name: admin.last_name,
      email: admin.email,
      username: admin.username,
    })
    setEditError(null)
  }

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingAdmin) return
    setEditError(null)
    setIsEditing(true)
    try {
      const updated = await departmentAdminApi.updateDepartmentAdmin(editingAdmin.id, editForm)
      setEditingAdmin(null)
      setSuccessMsg(`Perfil del administrador '${updated.username}' actualizado correctamente.`)
      loadAdmins()
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.message || 'Error al actualizar el perfil'
      setEditError(msg)
    } finally {
      setIsEditing(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Handlers: Reassign Department
  // ---------------------------------------------------------------------------
  const handleOpenReassign = (admin: DepartmentAdmin) => {
    setReassigningAdmin(admin)
    setNewDepartmentId(admin.department_id)
    setReassignError(null)
  }

  const handleReassignSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reassigningAdmin) return
    setReassignError(null)

    if (newDepartmentId === reassigningAdmin.department_id) {
      setReassignError('Debe seleccionar un departamento diferente al actual.')
      return
    }

    setIsReassigning(true)
    try {
      const updated = await departmentAdminApi.reassignDepartment(reassigningAdmin.id, {
        new_department_id: newDepartmentId,
      })
      setReassigningAdmin(null)
      setSuccessMsg(
        `Jurisdicción del administrador '${updated.username}' reasignada exitosamente a ${updated.department_code} — ${updated.department_name}. Las sesiones activas previas han sido revocadas.`
      )
      loadAdmins()
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.message || 'Error al reasignar departamento'
      setReassignError(msg)
    } finally {
      setIsReassigning(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Handlers: Status Toggle (Activate / Deactivate)
  // ---------------------------------------------------------------------------
  const handleOpenStatusToggle = (admin: DepartmentAdmin) => {
    setStatusTargetAdmin(admin)
  }

  const handleStatusToggleConfirm = async () => {
    if (!statusTargetAdmin) return
    const newStatus = !statusTargetAdmin.is_active
    setIsUpdatingStatus(true)
    try {
      const updated = await departmentAdminApi.updateStatus(statusTargetAdmin.id, {
        is_active: newStatus,
      })
      setStatusTargetAdmin(null)
      setSuccessMsg(
        `Administrador '${updated.username}' ${updated.is_active ? 'activado' : 'desactivado'} exitosamente.`
      )
      loadAdmins()
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.message || 'Error al cambiar estado'
      setError(msg)
    } finally {
      setIsUpdatingStatus(false)
    }
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '2rem 1rem' }}>
      {/* Header section */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '2rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '1.5rem' }}>🏛️</span>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
              Administradores Departamentales
            </h1>
          </div>
          <p style={{ color: '#64748B', margin: 0, fontSize: '0.95rem' }}>
            Aprovisionamiento y ciclo de vida territorial de secretarías de educación departamentales en PEVN.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={handleOpenCreate}
          style={{
            backgroundColor: '#0F172A',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.625rem 1.25rem',
            fontWeight: 600,
          }}
        >
          <span>➕</span> Nuevo Administrador Departamental
        </Button>
      </div>

      {/* Global Alerts */}
      {successMsg && (
        <div style={{ marginBottom: '1.5rem' }}>
          <Alert variant="success" onClose={() => setSuccessMsg(null)}>
            {successMsg}
          </Alert>
        </div>
      )}

      {error && (
        <div style={{ marginBottom: '1.5rem' }}>
          <Alert variant="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      {/* KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
          marginBottom: '2rem',
        }}
      >
        <Card style={{ padding: '1.25rem', borderLeft: '4px solid #3B82F6' }}>
          <div style={{ color: '#64748B', fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase' }}>
            Total Administradores
          </div>
          <div style={{ fontSize: '1.875rem', fontWeight: 800, color: '#0F172A', marginTop: '0.25rem' }}>
            {kpis.total}
          </div>
          <div style={{ color: '#94A3B8', fontSize: '0.75rem', marginTop: '0.25rem' }}>
            Registrados a nivel nacional
          </div>
        </Card>

        <Card style={{ padding: '1.25rem', borderLeft: '4px solid #F59E0B' }}>
          <div style={{ color: '#64748B', fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase' }}>
            Departamentos con Cobertura
          </div>
          <div style={{ fontSize: '1.875rem', fontWeight: 800, color: '#0F172A', marginTop: '0.25rem' }}>
            {kpis.departments_covered} de {kpis.total_canonical_departments || 33}
          </div>
          <div style={{ color: '#94A3B8', fontSize: '0.75rem', marginTop: '0.25rem' }}>
            Entidades territoriales canónicas
          </div>
        </Card>

        <Card style={{ padding: '1.25rem', borderLeft: '4px solid #10B981' }}>
          <div style={{ color: '#64748B', fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase' }}>
            Activos
          </div>
          <div style={{ fontSize: '1.875rem', fontWeight: 800, color: '#059669', marginTop: '0.25rem' }}>
            {kpis.active}
          </div>
          <div style={{ color: '#94A3B8', fontSize: '0.75rem', marginTop: '0.25rem' }}>
            Con acceso operacional habilitado
          </div>
        </Card>

        <Card style={{ padding: '1.25rem', borderLeft: '4px solid #EF4444' }}>
          <div style={{ color: '#64748B', fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase' }}>
            Inactivos
          </div>
          <div style={{ fontSize: '1.875rem', fontWeight: 800, color: '#DC2626', marginTop: '0.25rem' }}>
            {kpis.inactive}
          </div>
          <div style={{ color: '#94A3B8', fontSize: '0.75rem', marginTop: '0.25rem' }}>
            Sesión y accesos bloqueados
          </div>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <Card style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '1rem',
            alignItems: 'flex-end',
          }}
        >
          {/* Search */}
          <div>
            <label
              htmlFor="search-admin"
              style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Buscar Administrador
            </label>
            <input
              id="search-admin"
              type="text"
              placeholder="Nombre, usuario o correo..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setPage(1)
              }}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                border: '1px solid #CBD5E1',
                borderRadius: '6px',
                fontSize: '0.875rem',
                outline: 'none',
              }}
            />
          </div>

          {/* Department Filter (Loaded strictly from backend) */}
          <div>
            <label
              htmlFor="filter-dept"
              style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Filtrar por Departamento
            </label>
            <select
              id="filter-dept"
              value={selectedDeptFilter}
              onChange={(e) => {
                setSelectedDeptFilter(e.target.value)
                setPage(1)
              }}
              disabled={isDeptLoading}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                border: '1px solid #CBD5E1',
                borderRadius: '6px',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                outline: 'none',
              }}
            >
              <option value="">Todos los departamentos ({departments.length})</option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.id}>
                  {dept.code} — {dept.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label
              htmlFor="filter-status"
              style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Estado de Cuenta
            </label>
            <select
              id="filter-status"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as any)
                setPage(1)
              }}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                border: '1px solid #CBD5E1',
                borderRadius: '6px',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                outline: 'none',
              }}
            >
              <option value="all">Todos los estados</option>
              <option value="active">Activos</option>
              <option value="inactive">Inactivos</option>
            </select>
          </div>

          {/* Reset Filters */}
          <div>
            <Button
              variant="secondary"
              onClick={() => {
                setSearchQuery('')
                setSelectedDeptFilter('')
                setStatusFilter('all')
                setPage(1)
              }}
              style={{ width: '100%', padding: '0.5rem 0.75rem', fontSize: '0.875rem' }}
            >
              Limpiar Filtros
            </Button>
          </div>
        </div>
      </Card>

      {/* Main Table */}
      <Card style={{ overflow: 'hidden', padding: 0 }}>
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '1rem', color: '#64748B', fontSize: '0.9rem' }}>
              Cargando administradores departamentales...
            </p>
          </div>
        ) : admins.length === 0 ? (
          <div style={{ padding: '3rem' }}>
            <EmptyState
              title="No se encontraron administradores departamentales"
              description="No hay registros que coincidan con los filtros aplicados o aún no se han aprovisionado administradores."
              actionLabel="Aprovisionar Primer Administrador"
              onAction={handleOpenCreate}
            />
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#F1F5F9', borderBottom: '1px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.875rem 1rem', fontWeight: 600 }}>Nombre Completo</th>
                  <th style={{ padding: '0.875rem 1rem', fontWeight: 600 }}>Usuario</th>
                  <th style={{ padding: '0.875rem 1rem', fontWeight: 600 }}>Correo Institucional</th>
                  <th style={{ padding: '0.875rem 1rem', fontWeight: 600 }}>Departamento (DANE)</th>
                  <th style={{ padding: '0.875rem 1rem', fontWeight: 600 }}>Estado</th>
                  <th style={{ padding: '0.875rem 1rem', fontWeight: 600, textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {admins.map((adm) => (
                  <tr
                    key={adm.id}
                    style={{
                      borderBottom: '1px solid #E2E8F0',
                      backgroundColor: adm.is_active ? '#FFFFFF' : '#F8FAFC',
                      transition: 'background-color 0.15s ease',
                    }}
                  >
                    <td style={{ padding: '1rem', fontWeight: 600, color: '#0F172A' }}>
                      {adm.full_name}
                      <div style={{ fontSize: '0.75rem', color: '#94A3B8', fontWeight: 400 }}>
                        ID: {adm.id.slice(0, 8)}...
                      </div>
                    </td>
                    <td style={{ padding: '1rem', color: '#334155', fontFamily: 'monospace' }}>
                      {adm.username}
                    </td>
                    <td style={{ padding: '1rem', color: '#334155' }}>{adm.email}</td>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span
                          style={{
                            padding: '0.2rem 0.45rem',
                            backgroundColor: '#E0F2FE',
                            color: '#0369A1',
                            borderRadius: '4px',
                            fontWeight: 700,
                            fontSize: '0.75rem',
                            fontFamily: 'monospace',
                          }}
                        >
                          {adm.department_code}
                        </span>
                        <span style={{ fontWeight: 600, color: '#1E293B' }}>{adm.department_name}</span>
                      </div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <Badge variant={adm.is_active ? 'success' : 'neutral'}>
                        {adm.is_active ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenEdit(adm)}
                          title="Editar información de perfil"
                          style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
                        >
                          ✏️ Editar
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenReassign(adm)}
                          title="Reasignar departamento territorial"
                          style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem', color: '#D97706' }}
                        >
                          🔄 Reasignar
                        </Button>
                        {!adm.is_active && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleResendInvitation(adm)}
                            title="Reenviar invitación de activación al correo"
                            style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem', color: '#2563EB' }}
                          >
                            ✉️ Reenviar invitación
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenStatusToggle(adm)}
                          title={adm.is_active ? 'Desactivar acceso' : 'Activar acceso'}
                          style={{
                            fontSize: '0.8rem',
                            padding: '0.25rem 0.5rem',
                            color: adm.is_active ? '#DC2626' : '#16A34A',
                          }}
                        >
                          {adm.is_active ? '⛔ Desactivar' : '✅ Activar'}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Controls */}
        {total > 0 && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '1rem',
              borderTop: '1px solid #E2E8F0',
              fontSize: '0.875rem',
              color: '#64748B',
              flexWrap: 'wrap',
              gap: '0.5rem',
            }}
          >
            <div>
              Mostrando {admins.length} de {total} administradores
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Anterior
              </Button>
              <span style={{ fontWeight: 600, padding: '0 0.5rem' }}>
                Página {page} de {Math.max(1, Math.ceil(total / pageSize))}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={page >= Math.ceil(total / pageSize)}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* ------------------------------------------------------------------- */}
      {/* Modal: Create Department Administrator                               */}
      {/* ------------------------------------------------------------------- */}
      {isCreateOpen && (
        <Modal
          isOpen={isCreateOpen}
          onClose={() => setIsCreateOpen(false)}
          title="Aprovisionar Administrador Departamental"
        >
          <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ fontSize: '0.85rem', color: '#64748B' }}>
              Se creará una cuenta con rol <strong>DEPARTMENT_ADMIN</strong> (17 permisos de solo lectura,
              ámbito estrictamente confinado a la secretaría seleccionada).
            </div>

            {createError && <Alert variant="error">{createError}</Alert>}

            {/* Department Selection (Loaded from backend) */}
            <div>
              <label
                htmlFor="create-department"
                style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
              >
                Departamento Asignado (Jurisdicción) *
              </label>
              <select
                id="create-department"
                required
                value={createForm.department_id}
                onChange={(e) => setCreateForm({ ...createForm, department_id: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  border: '1px solid #CBD5E1',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  backgroundColor: '#FFFFFF',
                }}
              >
                <option value="" disabled>
                  Seleccione un departamento...
                </option>
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.code} — {dept.name}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label
                  htmlFor="create-firstname"
                  style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
                >
                  Nombres *
                </label>
                <input
                  id="create-firstname"
                  type="text"
                  required
                  placeholder="Ej. Carlos"
                  value={createForm.first_name}
                  onChange={(e) => setCreateForm({ ...createForm, first_name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    border: '1px solid #CBD5E1',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                  }}
                />
              </div>

              <div>
                <label
                  htmlFor="create-lastname"
                  style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
                >
                  Apellidos *
                </label>
                <input
                  id="create-lastname"
                  type="text"
                  required
                  placeholder="Ej. Gómez"
                  value={createForm.last_name}
                  onChange={(e) => setCreateForm({ ...createForm, last_name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    border: '1px solid #CBD5E1',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                  }}
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="create-email"
                style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
              >
                Correo Institucional *
              </label>
              <input
                id="create-email"
                type="email"
                required
                placeholder="ejemplo@sed.gov.co"
                value={createForm.email}
                onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  border: '1px solid #CBD5E1',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                }}
              />
            </div>

            <div>
              <label
                htmlFor="create-username"
                style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
              >
                Nombre de Usuario *
              </label>
              <input
                id="create-username"
                type="text"
                required
                placeholder="Ej. admin.atlantico"
                value={createForm.username}
                onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  border: '1px solid #CBD5E1',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                }}
              />
            </div>

            <div
              style={{
                backgroundColor: '#EFF6FF',
                borderRadius: '8px',
                border: '1px solid #BFDBFE',
                padding: '0.875rem 1rem',
                fontSize: '0.8125rem',
                color: '#1E40AF',
                lineHeight: 1.5,
              }}
            >
              ✉️ <strong>Flujo de Invitación y Activación Segura:</strong>
              <div style={{ marginTop: '0.25rem', color: '#1E3A8A' }}>
                Se enviará una invitación segura al correo institucional. El administrador establecerá su propia contraseña al activar la cuenta mediante un enlace de un solo uso con vigencia de 48 horas.
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
              <Button type="button" variant="secondary" onClick={() => setIsCreateOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" variant="primary" disabled={isCreating}>
                {isCreating ? 'Enviando Invitación...' : 'Crear y Enviar Invitación'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* Modal: Edit Profile                                                 */}
      {/* ------------------------------------------------------------------- */}
      {editingAdmin && (
        <Modal
          isOpen={Boolean(editingAdmin)}
          onClose={() => setEditingAdmin(null)}
          title={`Editar Perfil: ${editingAdmin.username}`}
        >
          <form onSubmit={handleEditSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {editError && <Alert variant="error">{editError}</Alert>}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label
                  htmlFor="edit-firstname"
                  style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
                >
                  Nombres
                </label>
                <input
                  id="edit-firstname"
                  type="text"
                  value={editForm.first_name || ''}
                  onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    border: '1px solid #CBD5E1',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                  }}
                />
              </div>

              <div>
                <label
                  htmlFor="edit-lastname"
                  style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
                >
                  Apellidos
                </label>
                <input
                  id="edit-lastname"
                  type="text"
                  value={editForm.last_name || ''}
                  onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    border: '1px solid #CBD5E1',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                  }}
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="edit-email"
                style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
              >
                Correo Institucional
              </label>
              <input
                id="edit-email"
                type="email"
                value={editForm.email || ''}
                onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  border: '1px solid #CBD5E1',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                }}
              />
            </div>

            <div>
              <label
                htmlFor="edit-username"
                style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
              >
                Nombre de Usuario
              </label>
              <input
                id="edit-username"
                type="text"
                value={editForm.username || ''}
                onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  border: '1px solid #CBD5E1',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
              <Button type="button" variant="secondary" onClick={() => setEditingAdmin(null)}>
                Cancelar
              </Button>
              <Button type="submit" variant="primary" disabled={isEditing}>
                {isEditing ? 'Guardando...' : 'Guardar Cambios'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* Modal: Reassign Department                                          */}
      {/* ------------------------------------------------------------------- */}
      {reassigningAdmin && (
        <Modal
          isOpen={Boolean(reassigningAdmin)}
          onClose={() => setReassigningAdmin(null)}
          title={`Reasignar Departamento Territorial`}
        >
          <form onSubmit={handleReassignSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div
              style={{
                backgroundColor: '#FEF3C7',
                border: '1px solid #F59E0B',
                borderRadius: '6px',
                padding: '0.75rem',
                fontSize: '0.85rem',
                color: '#92400E',
              }}
            >
              ⚠️ <strong>Atención de Seguridad:</strong> Esta operación modifica la jurisdicción territorial de{' '}
              <strong>{reassigningAdmin.full_name}</strong>. Para evitar retención de alcance caducado, las sesiones activas
              y tokens de actualización asociados serán revocados de inmediato.
            </div>

            {reassignError && <Alert variant="error">{reassignError}</Alert>}

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Departamento Actual
              </label>
              <div
                style={{
                  padding: '0.5rem 0.75rem',
                  backgroundColor: '#F1F5F9',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#475569',
                }}
              >
                {reassigningAdmin.department_code} — {reassigningAdmin.department_name}
              </div>
            </div>

            <div>
              <label
                htmlFor="reassign-new-dept"
                style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}
              >
                Nuevo Departamento Asignado *
              </label>
              <select
                id="reassign-new-dept"
                required
                value={newDepartmentId}
                onChange={(e) => setNewDepartmentId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  border: '1px solid #CBD5E1',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  backgroundColor: '#FFFFFF',
                }}
              >
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id} disabled={dept.id === reassigningAdmin.department_id}>
                    {dept.code} — {dept.name} {dept.id === reassigningAdmin.department_id ? '(Actual)' : ''}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
              <Button type="button" variant="secondary" onClick={() => setReassigningAdmin(null)}>
                Cancelar
              </Button>
              <Button type="submit" variant="primary" disabled={isReassigning} style={{ backgroundColor: '#D97706' }}>
                {isReassigning ? 'Reasignando...' : 'Confirmar Reasignación'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* Modal: Status Confirmation (Activate / Deactivate)                  */}
      {/* ------------------------------------------------------------------- */}
      {statusTargetAdmin && (
        <Modal
          isOpen={Boolean(statusTargetAdmin)}
          onClose={() => setStatusTargetAdmin(null)}
          title={`${statusTargetAdmin.is_active ? 'Desactivar' : 'Activar'} Administrador Departamental`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ fontSize: '0.9rem', color: '#334155', margin: 0 }}>
              ¿Está seguro de que desea {statusTargetAdmin.is_active ? 'desactivar' : 'activar'} la cuenta de{' '}
              <strong>{statusTargetAdmin.full_name}</strong> (<code>{statusTargetAdmin.username}</code>)?
            </p>

            {statusTargetAdmin.is_active && (
              <div
                style={{
                  backgroundColor: '#FEE2E2',
                  border: '1px solid #EF4444',
                  borderRadius: '6px',
                  padding: '0.75rem',
                  fontSize: '0.85rem',
                  color: '#991B1B',
                }}
              >
                El usuario perderá acceso inmediato a la plataforma y todas sus sesiones activas serán invalidadas.
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
              <Button type="button" variant="secondary" onClick={() => setStatusTargetAdmin(null)}>
                Cancelar
              </Button>
              <Button
                type="button"
                variant={statusTargetAdmin.is_active ? 'danger' : 'primary'}
                onClick={handleStatusToggleConfirm}
                disabled={isUpdatingStatus}
              >
                {isUpdatingStatus
                  ? 'Procesando...'
                  : statusTargetAdmin.is_active
                  ? 'Confirmar Desactivación'
                  : 'Confirmar Activación'}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* Modal: Invitation Result & Fallback Link                            */}
      {/* ------------------------------------------------------------------- */}
      {invitationResult && (
        <Modal
          isOpen={Boolean(invitationResult)}
          onClose={() => setInvitationResult(null)}
          title={invitationResult.isResend ? 'Resultado de Reenvío de Invitación' : 'Administrador Creado Exitosamente'}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Status Feedback Messages */}
            {!invitationResult.isResend ? (
              // Creation Feedback
              <>
                {invitationResult.deliveryStatus === 'EMAIL_SENT' && (
                  <div
                    style={{
                      backgroundColor: '#ECFDF5',
                      border: '1px solid #10B981',
                      borderRadius: '6px',
                      padding: '1rem',
                      color: '#065F46',
                    }}
                  >
                    <p style={{ margin: 0, fontWeight: 600, fontSize: '0.95rem' }}>
                      Administrador creado correctamente.
                    </p>
                    <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem' }}>
                      La invitación fue enviada al correo institucional.
                    </p>
                  </div>
                )}

                {invitationResult.deliveryStatus === 'EMAIL_NOT_CONFIGURED' && (
                  <div
                    style={{
                      backgroundColor: '#EFF6FF',
                      border: '1px solid #3B82F6',
                      borderRadius: '6px',
                      padding: '1rem',
                      color: '#1E40AF',
                    }}
                  >
                    <p style={{ margin: 0, fontWeight: 600, fontSize: '0.95rem' }}>
                      Administrador creado correctamente.
                    </p>
                    <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem' }}>
                      El correo electrónico no está configurado todavía.
                    </p>
                    <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem' }}>
                      La invitación segura fue generada y es válida durante 48 horas.
                    </p>
                  </div>
                )}

                {invitationResult.deliveryStatus === 'EMAIL_SEND_FAILED' && (
                  <div
                    style={{
                      backgroundColor: '#FEF2F2',
                      border: '1px solid #EF4444',
                      borderRadius: '6px',
                      padding: '1rem',
                      color: '#991B1B',
                    }}
                  >
                    <p style={{ margin: 0, fontWeight: 600, fontSize: '0.95rem' }}>
                      Administrador creado correctamente.
                    </p>
                    <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem' }}>
                      No fue posible enviar el correo electrónico.
                    </p>
                  </div>
                )}
              </>
            ) : (
              // Resend Feedback
              <>
                {invitationResult.deliveryStatus === 'EMAIL_SENT' && (
                  <div
                    style={{
                      backgroundColor: '#ECFDF5',
                      border: '1px solid #10B981',
                      borderRadius: '6px',
                      padding: '1rem',
                      color: '#065F46',
                    }}
                  >
                    <p style={{ margin: 0, fontWeight: 600, fontSize: '0.95rem' }}>
                      Invitación reenviada correctamente a {maskEmail(invitationResult.email)}.
                    </p>
                  </div>
                )}

                {invitationResult.deliveryStatus === 'EMAIL_NOT_CONFIGURED' && (
                  <div
                    style={{
                      backgroundColor: '#EFF6FF',
                      border: '1px solid #3B82F6',
                      borderRadius: '6px',
                      padding: '1rem',
                      color: '#1E40AF',
                    }}
                  >
                    <p style={{ margin: 0, fontWeight: 600, fontSize: '0.95rem' }}>
                      Nueva invitación generada. El correo no está configurado.
                    </p>
                  </div>
                )}

                {invitationResult.deliveryStatus === 'EMAIL_SEND_FAILED' && (
                  <div
                    style={{
                      backgroundColor: '#FEF2F2',
                      border: '1px solid #EF4444',
                      borderRadius: '6px',
                      padding: '1rem',
                      color: '#991B1B',
                    }}
                  >
                    <p style={{ margin: 0, fontWeight: 600, fontSize: '0.95rem' }}>
                      No fue posible enviar la invitación.
                    </p>
                  </div>
                )}
              </>
            )}

            {/* Enlace de activación fallback / copy block */}
            {invitationResult.activationUrl && (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                  padding: '1rem',
                  backgroundColor: '#F8FAFC',
                  borderRadius: '6px',
                  border: '1px solid #E2E8F0',
                }}
              >
                <label
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: '#334155',
                  }}
                >
                  Enlace de activación
                </label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input
                    type="text"
                    readOnly
                    value={invitationResult.activationUrl}
                    style={{
                      flex: 1,
                      padding: '0.5rem 0.75rem',
                      fontSize: '0.85rem',
                      fontFamily: 'monospace',
                      backgroundColor: '#FFFFFF',
                      border: '1px solid #CBD5E1',
                      borderRadius: '6px',
                      color: '#1E293B',
                    }}
                    onClick={(e) => (e.target as HTMLInputElement).select()}
                  />
                  <Button
                    type="button"
                    variant="primary"
                    onClick={handleCopyLink}
                    style={{ minWidth: '130px' }}
                  >
                    {copiedLink
                      ? '✓ Copiado'
                      : invitationResult.isResend
                      ? 'Copiar nuevo enlace'
                      : invitationResult.deliveryStatus === 'EMAIL_SENT'
                      ? 'Copiar enlace de invitación'
                      : 'Copiar enlace'}
                  </Button>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              <Button type="button" variant="secondary" onClick={() => setInvitationResult(null)}>
                Cerrar
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

