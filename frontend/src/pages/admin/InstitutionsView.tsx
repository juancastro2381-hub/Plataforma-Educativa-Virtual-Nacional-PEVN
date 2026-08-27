/**
 * PEVN Frontend — National Institutions & Rector Provisioning View
 *
 * Professional SaaS administration interface for NATIONAL_ADMIN / SUPERADMIN users.
 * Features:
 *   - National institutional catalog listing, searching, filtering, and pagination
 *   - New institution provisioning with 12-digit DANE validation & automatic Sede Principal
 *   - Operational status lifecycle transitions (active / suspended) with confirmation
 *   - Cryptographically secure single-use Rector invitation generation & URL copying
 *   - Zero-password creation by administrators (Rector sets own password via invitation)
 */

import React, { useCallback, useEffect, useState } from 'react'
import { institutionApi, type ListInstitutionsParams } from '@/services/institution'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Modal } from '@/components/ui/Modal'
import { useAuth } from '@/hooks/useAuth'
import type {
  DocumentType,
  InstitutionCreateRequest,
  InstitutionResponse,
  OfficialCatalogSyncStatus,
  OfficialInstitutionResolution,
  RectorInvitationCreateRequest,
  RectorInvitationResponse,
} from '@/types'

export const InstitutionsView: React.FC = () => {
  const { user, hasRole } = useAuth()

  // Master List State
  const [institutions, setInstitutions] = useState<InstitutionResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [page, setPage] = useState<number>(1)
  const [pageSize] = useState<number>(10)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Official Catalog Sync Status
  const [catalogSyncStatus, setCatalogSyncStatus] = useState<OfficialCatalogSyncStatus | null>(null)
  const [isSyncingCatalog, setIsSyncingCatalog] = useState<boolean>(false)

  // Provisioning Modal State & Official DANE Resolution
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isCreating, setIsCreating] = useState<boolean>(false)
  const [isResolvingDane, setIsResolvingDane] = useState<boolean>(false)
  const [resolvedOfficialData, setResolvedOfficialData] = useState<OfficialInstitutionResolution | null>(null)
  const [resolutionError, setResolutionError] = useState<string | null>(null)
  const [isManualOverride, setIsManualOverride] = useState<boolean>(false)
  const [createForm, setCreateForm] = useState<InstitutionCreateRequest>({
    dane_code: '',
    name: '',
    email: '',
    phone: '',
    address: '',
    municipality_id: '11001', // Default Bogotá D.C. or resolved
    main_campus_name: 'Sede Principal',
  })
  const [createError, setCreateError] = useState<string | null>(null)

  // Rector Invitation Modal State
  const [selectedInstForInvite, setSelectedInstForInvite] = useState<InstitutionResponse | null>(null)
  const [isInviteOpen, setIsInviteOpen] = useState<boolean>(false)
  const [isInviting, setIsInviting] = useState<boolean>(false)
  const [inviteForm, setInviteForm] = useState<RectorInvitationCreateRequest>({
    first_name: '',
    last_name: '',
    document_type: 'CC' as DocumentType,
    document_number: '',
    email: '',
    phone_number: '',
  })
  const [inviteError, setInviteError] = useState<string | null>(null)

  // Generated Invitation Result Modal
  const [generatedInvitation, setGeneratedInvitation] = useState<RectorInvitationResponse | null>(null)
  const [isResultModalOpen, setIsResultModalOpen] = useState<boolean>(false)
  const [copiedLink, setCopiedLink] = useState<boolean>(false)

  // Status Change Confirmation Modal State
  const [statusConfirmModal, setStatusConfirmModal] = useState<{
    isOpen: boolean
    institution: InstitutionResponse | null
    newStatus: boolean
  }>({
    isOpen: false,
    institution: null,
    newStatus: false,
  })
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<boolean>(false)

  // Data Loader
  const fetchInstitutions = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const params: ListInstitutionsParams = {
        page,
        page_size: pageSize,
      }
      if (searchQuery.trim()) {
        params.search = searchQuery.trim()
      }
      if (statusFilter === 'active') {
        params.is_active = true
      } else if (statusFilter === 'inactive') {
        params.is_active = false
      }

      const res = await institutionApi.listInstitutions(params)
      setInstitutions(res.items)
      setTotal(res.total)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar catálogo de instituciones.'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [page, pageSize, searchQuery, statusFilter])

  const fetchCatalogStatus = useCallback(async () => {
    try {
      const statusRes = await institutionApi.getCatalogSyncStatus()
      setCatalogSyncStatus(statusRes)
    } catch {
      // Non-blocking catalog status check
    }
  }, [])

  useEffect(() => {
    void fetchInstitutions()
    void fetchCatalogStatus()
  }, [fetchInstitutions, fetchCatalogStatus])

  // Handlers
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    void fetchInstitutions()
  }

  const handleClearFilters = () => {
    setSearchQuery('')
    setStatusFilter('all')
    setPage(1)
  }

  // Handle National Catalog Manual Ingestion/Sync
  const handleSyncCatalog = async () => {
    setIsSyncingCatalog(true)
    setError(null)
    setSuccessMsg(null)
    try {
      const res = await institutionApi.syncNationalCatalog()
      setSuccessMsg(
        `✓ Sincronización exitosa [Quality Gates: ${res.quality_gate_status} | Bloques: ${res.processed_chunks || 1}/${res.total_chunks || 1}]: ${res.institutions_synced} instituciones y ${res.campuses_synced} sedes actualizadas en ${res.departments_covered} departamentos.`
      )
      await fetchCatalogStatus()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al sincronizar catálogo nacional.'
      setError(msg)
    } finally {
      setIsSyncingCatalog(false)
    }
  }

  // Handle DANE Resolution Lookup
  const handleResolveDane = async (daneCode: string) => {
    const clean = daneCode.trim()
    if (clean.length !== 12 || !/^\d{12}$/.test(clean)) {
      setResolutionError('El Código DANE debe contener exactamente 12 dígitos.')
      setResolvedOfficialData(null)
      return
    }

    setIsResolvingDane(true)
    setResolutionError(null)
    setCreateError(null)
    try {
      const data = await institutionApi.resolveDaneInstitution(clean)
      setResolvedOfficialData(data)
      setCreateForm((prev) => ({
        ...prev,
        dane_code: data.dane_code,
        name: data.name,
        email: data.official_email || prev.email || '',
        phone: data.official_phone || prev.phone || '',
        address: data.official_address || prev.address || '',
        municipality_id: data.municipality_code,
        main_campus_name: data.campuses.find((c) => c.is_main)?.name || 'Sede Principal',
      }))
      setIsManualOverride(false)
    } catch {
      setResolvedOfficialData(null)
      setResolutionError('No encontramos un registro oficial asociado a este Código DANE en el catálogo nacional.')
    } finally {
      setIsResolvingDane(false)
    }
  }

  const handleDaneInputChange = (rawVal: string) => {
    const clean = rawVal.replace(/\D/g, '').slice(0, 12)
    setCreateForm((prev) => ({ ...prev, dane_code: clean }))
    setResolvedOfficialData(null)
    setResolutionError(null)
    setIsManualOverride(false)
  }

  // Handle Provisioning Submit
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreateError(null)

    // Strict client-side validation
    const dane = createForm.dane_code.trim()
    if (!/^\d{12}$/.test(dane)) {
      setCreateError('El código DANE institucional debe contener exactamente 12 dígitos numéricos.')
      return
    }
    if (!resolvedOfficialData && !isManualOverride) {
      setCreateError('Debe consultar un Código DANE oficial o habilitar la excepción administrativa.')
      return
    }
    if (!createForm.name.trim()) {
      setCreateError('El nombre de la institución es obligatorio.')
      return
    }
    if (!createForm.email.trim() || !createForm.email.includes('@')) {
      setCreateError('Debe ingresar un correo electrónico institucional válido para PEvN.')
      return
    }

    setIsCreating(true)
    try {
      await institutionApi.createInstitution({
        ...createForm,
        dane_code: dane,
        name: createForm.name.trim(),
        email: createForm.email.trim(),
        phone: createForm.phone?.trim() || null,
        address: createForm.address?.trim() || null,
        main_campus_name: createForm.main_campus_name?.trim() || 'Sede Principal',
      })
      setSuccessMsg(`Institución "${createForm.name}" aprovisionada exitosamente con sus sedes oficiales.`)
      setIsCreateOpen(false)
      setResolvedOfficialData(null)
      setResolutionError(null)
      setIsManualOverride(false)
      setCreateForm({
        dane_code: '',
        name: '',
        email: '',
        phone: '',
        address: '',
        municipality_id: '11001',
        main_campus_name: 'Sede Principal',
      })
      void fetchInstitutions()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al aprovisionar institución.'
      setCreateError(msg)
    } finally {
      setIsCreating(false)
    }
  }

  // Handle Invite Rector Submit
  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedInstForInvite) return
    setInviteError(null)

    if (!inviteForm.first_name.trim() || !inviteForm.last_name.trim()) {
      setInviteError('Los nombres y apellidos del Rector son obligatorios.')
      return
    }
    if (!inviteForm.document_number.trim()) {
      setInviteError('El número de documento de identidad es obligatorio.')
      return
    }
    if (!inviteForm.email.trim() || !inviteForm.email.includes('@')) {
      setInviteError('Debe ingresar un correo electrónico válido para el Rector.')
      return
    }

    setIsInviting(true)
    try {
      const res = await institutionApi.inviteRector(selectedInstForInvite.id, {
        first_name: inviteForm.first_name.trim(),
        last_name: inviteForm.last_name.trim(),
        document_type: inviteForm.document_type,
        document_number: inviteForm.document_number.trim(),
        email: inviteForm.email.trim(),
        phone_number: inviteForm.phone_number?.trim() || null,
      })

      setIsInviteOpen(false)
      setGeneratedInvitation(res)
      setCopiedLink(false)
      setIsResultModalOpen(true)
      setSuccessMsg(`Invitación generada exitosamente para ${inviteForm.first_name} ${inviteForm.last_name}.`)
      setInviteForm({
        first_name: '',
        last_name: '',
        document_type: 'CC',
        document_number: '',
        email: '',
        phone_number: '',
      })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al generar invitación para el Rector.'
      setInviteError(msg)
    } finally {
      setIsInviting(false)
    }
  }

  // Handle Status Toggle Submit
  const handleStatusToggleSubmit = async () => {
    if (!statusConfirmModal.institution) return
    setIsUpdatingStatus(true)
    try {
      await institutionApi.updateInstitutionStatus(
        statusConfirmModal.institution.id,
        statusConfirmModal.newStatus
      )
      setSuccessMsg(
        `Estado de "${statusConfirmModal.institution.name}" actualizado a ${
          statusConfirmModal.newStatus ? 'ACTIVA' : 'SUSPENDIDA'
        }.`
      )
      setStatusConfirmModal({ isOpen: false, institution: null, newStatus: false })
      void fetchInstitutions()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al actualizar estado.'
      setError(msg)
    } finally {
      setIsUpdatingStatus(false)
    }
  }

  // Copy Link to Clipboard
  const handleCopyLink = () => {
    if (!generatedInvitation) return
    const url =
      generatedInvitation.invitation_url ||
      `${window.location.origin}/auth/accept-invitation?token=${generatedInvitation.raw_invitation_token || ''}`

    void navigator.clipboard.writeText(url)
    setCopiedLink(true)
    setTimeout(() => {
      setCopiedLink(false)
    }, 3000)
  }

  const isNationalAdmin = hasRole(['national_admin', 'superadmin']) || user?.scope.is_national

  return (
    <div style={{ maxWidth: '1280px', margin: '2rem auto', padding: '0 1rem' }}>
      {/* Top Banner */}
      <div
        style={{
          backgroundColor: '#0F172A',
          color: '#FFFFFF',
          borderRadius: '16px',
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: '0 10px 15px -3px rgba(15, 23, 42, 0.15)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1.5rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                backgroundColor: 'rgba(252, 209, 22, 0.2)',
                color: '#FCD116',
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
              }}
            >
              Nivel Nacional • Ministerio de Educación
            </span>
            {catalogSyncStatus?.catalog_status === 'DEVELOPMENT_SEED' && (
              <Badge variant="warning">
                Catálogo Semilla ({catalogSyncStatus.total_institutions} EE / {catalogSyncStatus.total_campuses} Sedes)
              </Badge>
            )}
            {catalogSyncStatus?.catalog_status === 'NATIONAL_CATALOG_INCOMPLETE' && (
              <Badge variant="warning">
                Catálogo Nacional Incompleto (Línea Base: {catalogSyncStatus.total_institutions} EE / {catalogSyncStatus.total_campuses} Sedes / {catalogSyncStatus.departments_covered}/33 Dptos)
              </Badge>
            )}
            {catalogSyncStatus?.catalog_status === 'NATIONAL_CATALOG_SYNCED' && (
              <Badge variant="success">
                Catálogo Nacional Completo ({catalogSyncStatus.total_institutions} EE / {catalogSyncStatus.total_campuses} Sedes)
              </Badge>
            )}
            {!catalogSyncStatus && <Badge variant="neutral">Catálogo Oficial DANE</Badge>}
          </div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 800, margin: '0.25rem 0', color: '#FFFFFF' }}>
            Aprovisionamiento de Instituciones
          </h1>
          <p style={{ color: '#94A3B8', fontSize: '0.9375rem', margin: 0, maxWidth: '650px' }}>
            Registro de colegios con validación DANE de 12 dígitos, creación de sedes principales y emisión segura de invitaciones criptográficas para Rectores.
          </p>
        </div>

        {isNationalAdmin && (
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="secondary"
              disabled={isSyncingCatalog}
              onClick={handleSyncCatalog}
              style={{
                borderColor: '#475569',
                color: '#E2E8F0',
                fontWeight: 600,
                padding: '0.75rem 1.25rem',
              }}
            >
              {isSyncingCatalog ? '⏳ Sincronizando Catálogo...' : '🔄 Sincronizar Catálogo'}
            </Button>

            <Button
              variant="primary"
              onClick={() => {
                setCreateError(null)
                setIsCreateOpen(true)
              }}
              style={{
                backgroundColor: '#2563EB',
                fontWeight: 700,
                padding: '0.75rem 1.5rem',
                boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.4)',
              }}
            >
              + Aprovisionar Institución
            </Button>
          </div>
        )}
      </div>

      {/* Staleness Warning Alert */}
      {catalogSyncStatus?.is_stale && catalogSyncStatus.freshness_warning && (
        <div style={{ marginBottom: '1.5rem' }}>
          <Alert variant="warning" title="Aviso de Actualización del Catálogo">
            {catalogSyncStatus.freshness_warning}
          </Alert>
        </div>
      )}

      {/* Global Alerts */}
      {error && (
        <div style={{ marginBottom: '1.5rem' }}>
          <Alert variant="error" title="Error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      {successMsg && (
        <div style={{ marginBottom: '1.5rem' }}>
          <Alert variant="success" title="Operación Exitosa" onClose={() => setSuccessMsg(null)}>
            {successMsg}
          </Alert>
        </div>
      )}

      {/* Filter & Search Bar */}
      <Card style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
        <form
          onSubmit={handleSearchSubmit}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1, minWidth: '280px' }}>
            <div style={{ position: 'relative', width: '100%', maxWidth: '400px' }}>
              <input
                type="text"
                placeholder="Buscar por Nombre, DANE o Correo..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.625rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid #CBD5E1',
                  fontSize: '0.875rem',
                  outline: 'none',
                }}
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as 'all' | 'active' | 'inactive')
                setPage(1)
              }}
              style={{
                padding: '0.625rem 1rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                outline: 'none',
              }}
            >
              <option value="all">Todos los Estados</option>
              <option value="active">Activas</option>
              <option value="inactive">Suspendidas</option>
            </select>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Button type="submit" variant="secondary">
              🔍 Filtrar
            </Button>
            {(searchQuery || statusFilter !== 'all') && (
              <Button type="button" variant="ghost" onClick={handleClearFilters}>
                Limpiar
              </Button>
            )}
          </div>
        </form>
      </Card>

      {/* Catalog Table */}
      <Card style={{ padding: 0 }}>
        {isLoading ? (
          <div style={{ padding: '4rem 1rem', display: 'flex', justifyContent: 'center' }}>
            <LoadingSpinner size="lg" label="Cargando catálogo nacional de instituciones..." />
          </div>
        ) : institutions.length === 0 ? (
          <div style={{ padding: '3rem 1rem' }}>
            <EmptyState
              title="No se encontraron instituciones"
              description={
                searchQuery
                  ? 'No hay instituciones que coincidan con los criterios de búsqueda.'
                  : 'Aún no se han aprovisionado instituciones educativas en la plataforma.'
              }
              actionLabel={isNationalAdmin ? 'Aprovisionar Primera Institución' : undefined}
              onAction={isNationalAdmin ? () => setIsCreateOpen(true) : undefined}
            />
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                textAlign: 'left',
                fontSize: '0.875rem',
              }}
            >
              <thead>
                <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '1rem', fontWeight: 700 }}>Código DANE</th>
                  <th style={{ padding: '1rem', fontWeight: 700 }}>Institución Educativa</th>
                  <th style={{ padding: '1rem', fontWeight: 700 }}>Sede Principal</th>
                  <th style={{ padding: '1rem', fontWeight: 700 }}>Contacto</th>
                  <th style={{ padding: '1rem', fontWeight: 700, textAlign: 'center' }}>Estado</th>
                  <th style={{ padding: '1rem', fontWeight: 700, textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {institutions.map((inst) => {
                  const mainCampus = inst.campuses?.find((c) => c.is_main) || inst.campuses?.[0]
                  return (
                    <tr
                      key={inst.id}
                      style={{
                        borderBottom: '1px solid #F1F5F9',
                        transition: 'background-color 150ms',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8FAFC')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                    >
                      <td style={{ padding: '1rem' }}>
                        <span
                          style={{
                            fontFamily: 'monospace',
                            fontWeight: 700,
                            color: '#1E293B',
                            backgroundColor: '#E2E8F0',
                            padding: '0.2rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.8125rem',
                          }}
                        >
                          {inst.dane_code}
                        </span>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ fontWeight: 700, color: '#0F172A' }}>{inst.name}</div>
                        <div style={{ fontSize: '0.75rem', color: '#64748B' }}>{inst.email}</div>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ fontWeight: 600, color: '#334155' }}>
                          {mainCampus?.name || 'Sede Principal'}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#94A3B8', fontFamily: 'monospace' }}>
                          DANE Sede: {mainCampus?.dane_sede_code || `${inst.dane_code}01`}
                        </div>
                      </td>
                      <td style={{ padding: '1rem', color: '#475569' }}>
                        <div>{inst.phone || 'Sin teléfono'}</div>
                        <div style={{ fontSize: '0.75rem', color: '#64748B' }}>{inst.address || 'Sin dirección'}</div>
                      </td>
                      <td style={{ padding: '1rem', textAlign: 'center' }}>
                        <Badge variant={inst.is_active ? 'success' : 'danger'}>
                          {inst.is_active ? 'Activa' : 'Suspendida'}
                        </Badge>
                      </td>
                      <td style={{ padding: '1rem', textAlign: 'right' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                          {isNationalAdmin && inst.is_active && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSelectedInstForInvite(inst)
                                setInviteError(null)
                                setIsInviteOpen(true)
                              }}
                              title="Generar invitación criptográfica para el Rector"
                            >
                              ✉️ Invitar Rector
                            </Button>
                          )}
                          {isNationalAdmin && (
                            <Button
                              variant={inst.is_active ? 'ghost' : 'secondary'}
                              size="sm"
                              onClick={() =>
                                setStatusConfirmModal({
                                  isOpen: true,
                                  institution: inst,
                                  newStatus: !inst.is_active,
                                })
                              }
                            >
                              {inst.is_active ? 'Suspender' : 'Reactivar'}
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {total > pageSize && (
          <div
            style={{
              padding: '1rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderTop: '1px solid #E2E8F0',
              backgroundColor: '#F8FAFC',
              fontSize: '0.875rem',
            }}
          >
            <div style={{ color: '#64748B' }}>
              Mostrando {institutions.length} de {total} instituciones
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Anterior
              </Button>
              <span style={{ alignSelf: 'center', fontWeight: 600, color: '#334155' }}>
                Página {page} de {Math.ceil(total / pageSize)}
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

      {/* ===================================================================== */}
      {/* 1. Modal de Aprovisionamiento Institucional                            */}
      {/* ===================================================================== */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false)
          setResolvedOfficialData(null)
          setResolutionError(null)
          setIsManualOverride(false)
        }}
        title="Aprovisionar Nueva Institución Educativa"
      >
        <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {createError && <Alert variant="error">{createError}</Alert>}

          {/* DANE Code Lookup Section */}
          <div>
            <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
              Código DANE del Establecimiento Educativo (12 Dígitos) *
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                maxLength={12}
                placeholder="Ej: 111001012345"
                value={createForm.dane_code}
                onChange={(e) => handleDaneInputChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    if (createForm.dane_code.length === 12 && !isResolvingDane) {
                      void handleResolveDane(createForm.dane_code)
                    }
                  }
                }}
                required
                style={{
                  width: '100%',
                  padding: '0.625rem',
                  borderRadius: '6px',
                  border: resolvedOfficialData
                    ? '2px solid #22C55E'
                    : resolutionError
                    ? '2px solid #EF4444'
                    : '1px solid #CBD5E1',
                  fontSize: '0.9375rem',
                  fontFamily: 'monospace',
                  fontWeight: 600,
                  backgroundColor: '#FFFFFF',
                }}
              />
              <Button
                type="button"
                variant="secondary"
                disabled={createForm.dane_code.length !== 12 || isResolvingDane}
                onClick={() => void handleResolveDane(createForm.dane_code)}
              >
                {isResolvingDane ? 'Consultando...' : '🔎 Consultar información oficial'}
              </Button>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.35rem' }}>
              Ingrese los 12 dígitos del DANE y pulse <strong>Consultar</strong> o presione <strong>Enter</strong> para resolver la identidad oficial.
            </div>
          </div>

          {/* State: Searching Indicator */}
          {isResolvingDane && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '1rem', backgroundColor: '#EFF6FF', borderRadius: '8px', border: '1px solid #BFDBFE' }}>
              <LoadingSpinner size="sm" />
              <span style={{ fontSize: '0.875rem', color: '#1E40AF', fontWeight: 600 }}>
                Consultando catálogo oficial MEN/DANE...
              </span>
            </div>
          )}

          {/* State: Not Found Alert + Manual Override Option */}
          {resolutionError && !resolvedOfficialData && !isManualOverride && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', padding: '1.25rem', backgroundColor: '#FEF2F2', borderRadius: '8px', border: '1px solid #FECACA' }}>
              <div style={{ color: '#991B1B', fontSize: '0.9375rem', fontWeight: 700 }}>
                ⚠️ El código DANE no fue encontrado en el catálogo oficial MEN/DANE.
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#7F1D1D', lineHeight: 1.5 }}>
                El establecimiento no puede aprovisionarse automáticamente porque su identidad oficial no pudo ser verificada en el Directorio Único de Establecimientos (DUE) / DANE.
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setIsManualOverride(true)}
                style={{ alignSelf: 'flex-start', color: '#991B1B', fontWeight: 700, backgroundColor: '#FEE2E2', padding: '0.4rem 0.75rem', borderRadius: '6px' }}
              >
                ⚙️ Habilitar excepción manual para Administrador Nacional
              </Button>
            </div>
          )}

          {/* State: Resolved Official Record (Read-only + Provenance) */}
          {resolvedOfficialData && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Provenance Header Banner */}
              <div
                style={{
                  backgroundColor: '#F0FDF4',
                  border: '1px solid #BBF7D0',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                }}
              >
                <div style={{ color: '#166534', fontWeight: 700, fontSize: '0.875rem' }}>
                  ✓ Establecimiento Educativo Verificado
                </div>
                <div style={{ fontSize: '0.75rem', color: '#15803D' }}>
                  Fuente oficial: <strong>MEN/DANE</strong> • Última actualización: <strong>{new Date(resolvedOfficialData.provenance.source_updated_at || resolvedOfficialData.provenance.synced_at).toISOString().split('T')[0]}</strong>
                </div>
              </div>

              {/* Official Section: INFORMACIÓN OFICIAL */}
              <div style={{ backgroundColor: '#F8FAFC', padding: '1.25rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                <div style={{ fontSize: '0.8125rem', fontWeight: 800, color: '#1E293B', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem' }}>
                  INFORMACIÓN OFICIAL
                </div>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                    gap: '1rem',
                  }}
                >
                  <div style={{ gridColumn: '1 / -1' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>🔒 Nombre oficial</div>
                    <div style={{ fontSize: '1rem', fontWeight: 800, color: '#0F172A' }}>
                      {resolvedOfficialData.name}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>🔒 Código DANE</div>
                    <code style={{ fontSize: '0.9375rem', color: '#0F172A', fontWeight: 700 }}>
                      {resolvedOfficialData.dane_code}
                    </code>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>🔒 Departamento</div>
                    <div style={{ fontSize: '0.875rem', color: '#1E293B', fontWeight: 600 }}>
                      {resolvedOfficialData.department_name} ({resolvedOfficialData.department_code})
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>🔒 Municipio</div>
                    <div style={{ fontSize: '0.875rem', color: '#1E293B', fontWeight: 600 }}>
                      {resolvedOfficialData.municipality_name} ({resolvedOfficialData.municipality_code})
                    </div>
                  </div>

                  <div style={{ gridColumn: '1 / -1' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>🔒 Secretaría de Educación (ETC)</div>
                    <div style={{ fontSize: '0.875rem', color: '#1E293B' }}>
                      {resolvedOfficialData.secretaria_name || 'Entidad Territorial Certificada'}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>🔒 Sector</div>
                    <div style={{ fontSize: '0.875rem', color: '#1E293B', fontWeight: 600 }}>
                      {resolvedOfficialData.sector}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>🔒 Zona</div>
                    <div style={{ fontSize: '0.875rem', color: '#1E293B', fontWeight: 600 }}>
                      {resolvedOfficialData.zone}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>🔒 Calendario</div>
                    <div style={{ fontSize: '0.875rem', color: '#1E293B', fontWeight: 600 }}>
                      Calendario {resolvedOfficialData.calendar}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>🔒 Modalidad</div>
                    <div style={{ fontSize: '0.875rem', color: '#1E293B', fontWeight: 600 }}>
                      {resolvedOfficialData.academic_character}
                    </div>
                  </div>

                  <div style={{ gridColumn: '1 / -1' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>🔒 Dirección oficial</div>
                    <div style={{ fontSize: '0.875rem', color: '#1E293B' }}>
                      {resolvedOfficialData.official_address || 'No registrada en fuente oficial'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Section: SEDES EDUCATIVAS OFICIALES */}
              <div style={{ backgroundColor: '#F8FAFC', padding: '1.25rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                <div style={{ fontSize: '0.8125rem', fontWeight: 800, color: '#1E293B', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
                  SEDES EDUCATIVAS OFICIALES ({resolvedOfficialData.campuses.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {resolvedOfficialData.campuses.map((campus) => (
                    <div
                      key={campus.dane_sede_code}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.625rem 0.875rem',
                        backgroundColor: '#FFFFFF',
                        borderRadius: '6px',
                        border: campus.is_main ? '1.5px solid #93C5FD' : '1px solid #E2E8F0',
                        fontSize: '0.875rem',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span
                          style={{
                            padding: '0.2rem 0.6rem',
                            borderRadius: '9999px',
                            fontSize: '0.6875rem',
                            fontWeight: 800,
                            textTransform: 'uppercase',
                            backgroundColor: campus.is_main ? '#DBEAFE' : '#F1F5F9',
                            color: campus.is_main ? '#1D4ED8' : '#475569',
                          }}
                        >
                          {campus.is_main ? 'Principal' : 'Adscrita'}
                        </span>
                        <div>
                          <div style={{ fontWeight: 700, color: '#0F172A' }}>{campus.name}</div>
                          <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                            {campus.address || 'Sin dirección registrada'} • {campus.zone}
                          </div>
                        </div>
                      </div>
                      <code style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#334155', backgroundColor: '#F8FAFC', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                        DANE Sede: {campus.dane_sede_code}
                      </code>
                    </div>
                  ))}
                </div>
              </div>

              {/* PEvN Operational Data Form */}
              <div style={{ borderTop: '1px solid #E2E8F0', paddingTop: '1rem' }}>
                <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.75rem' }}>
                  Datos Operativos PEvN
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontWeight: 700, fontSize: '0.8125rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                      Correo Institucional PEvN *
                    </label>
                    <input
                      type="email"
                      placeholder="rectoria@colegio.edu.co"
                      value={createForm.email}
                      onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                      required
                      style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
                    />
                    <span style={{ fontSize: '0.6875rem', color: '#64748B' }}>
                      {resolvedOfficialData.official_email
                        ? 'Prellenado desde la base de datos oficial'
                        : 'Requerido para la operatividad en PEvN'}
                    </span>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontWeight: 700, fontSize: '0.8125rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                      Teléfono de Contacto
                    </label>
                    <input
                      type="text"
                      placeholder="+57 601 3241000"
                      value={createForm.phone || ''}
                      onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
                      style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
                    />
                  </div>
                </div>
              </div>

              {/* Provenance Metadata Footer */}
              <div style={{ fontSize: '0.6875rem', color: '#94A3B8', borderTop: '1px solid #F1F5F9', paddingTop: '0.5rem' }}>
                Dataset: <code>{resolvedOfficialData.provenance.source_dataset}</code> • Catálogo PEvN sincronizado:{' '}
                {new Date(resolvedOfficialData.provenance.synced_at).toLocaleDateString()}
              </div>
            </div>
          )}

          {/* State: Manual Override Form (When DANE is not in official catalog) */}
          {isManualOverride && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ backgroundColor: '#FEF3C7', border: '1px solid #FDE68A', padding: '0.75rem', borderRadius: '6px', fontSize: '0.8125rem', color: '#92400E' }}>
                ⚠️ <strong>Excepción de Aprovisionamiento Manual:</strong> Esta institución será registrada como ingreso manual no verificado en DUE. La acción quedará registrada en la pista de auditoría nacional.
              </div>

              <div>
                <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                  Nombre Oficial de la Institución *
                </label>
                <input
                  type="text"
                  placeholder="Ej: Institución Educativa Departamental San Juan"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  required
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                    Correo Institucional *
                  </label>
                  <input
                    type="email"
                    placeholder="rectoria@sanjuan.edu.co"
                    value={createForm.email}
                    onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                    required
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                    Teléfono
                  </label>
                  <input
                    type="text"
                    placeholder="+57 300 1234567"
                    value={createForm.phone || ''}
                    onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                  Dirección Física
                </label>
                <input
                  type="text"
                  placeholder="Carrera 7 # 32-10"
                  value={createForm.address || ''}
                  onChange={(e) => setCreateForm({ ...createForm, address: e.target.value })}
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                  Nombre de Sede Principal
                </label>
                <input
                  type="text"
                  placeholder="Sede Principal San Juan"
                  value={createForm.main_campus_name || ''}
                  onChange={(e) => setCreateForm({ ...createForm, main_campus_name: e.target.value })}
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
                />
              </div>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setIsCreateOpen(false)
                setResolvedOfficialData(null)
                setResolutionError(null)
                setIsManualOverride(false)
              }}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isCreating || isResolvingDane || (!resolvedOfficialData && !isManualOverride)}
            >
              {isCreating ? 'Aprovisionando...' : 'Confirmar y Aprovisionar'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ===================================================================== */}
      {/* 2. Modal de Emisión de Invitación a Rector                             */}
      {/* ===================================================================== */}
      <Modal
        isOpen={isInviteOpen}
        onClose={() => setIsInviteOpen(false)}
        title={`Invitar Rector — ${selectedInstForInvite?.name || ''}`}
      >
        <form onSubmit={handleInviteSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {inviteError && <Alert variant="error">{inviteError}</Alert>}

          <div
            style={{
              backgroundColor: '#FEF3C7',
              border: '1px solid #FDE68A',
              borderRadius: '8px',
              padding: '0.75rem 1rem',
              fontSize: '0.8125rem',
              color: '#92400E',
            }}
          >
            🔒 <strong>Principio de Seguridad Cero-Contraseña:</strong> Como Administrador Nacional, usted <strong>NO</strong> define la clave del Rector. Se generará un enlace tokenizado de un solo uso con vigencia de 48 horas mediante el cual el Rector definirá su clave secreta con cifrado Argon2id.
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                Nombres del Rector *
              </label>
              <input
                type="text"
                placeholder="Ej: Gabriel"
                value={inviteForm.first_name}
                onChange={(e) => setInviteForm({ ...inviteForm, first_name: e.target.value })}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                Apellidos del Rector *
              </label>
              <input
                type="text"
                placeholder="Ej: García Márquez"
                value={inviteForm.last_name}
                onChange={(e) => setInviteForm({ ...inviteForm, last_name: e.target.value })}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                Tipo Doc. *
              </label>
              <select
                value={inviteForm.document_type}
                onChange={(e) => setInviteForm({ ...inviteForm, document_type: e.target.value as DocumentType })}
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem', backgroundColor: '#FFFFFF' }}
              >
                <option value="CC">Cédula (CC)</option>
                <option value="CE">Cédula Ext. (CE)</option>
                <option value="PASSPORT">Pasaporte</option>
                <option value="PEP">PEP</option>
                <option value="PPT">PPT</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                Número de Documento *
              </label>
              <input
                type="text"
                placeholder="Ej: 19876543"
                value={inviteForm.document_number}
                onChange={(e) => setInviteForm({ ...inviteForm, document_number: e.target.value })}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
              Correo Electrónico Oficial del Rector *
            </label>
            <input
              type="email"
              placeholder="rector@sanjose.edu.co"
              value={inviteForm.email}
              onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
              required
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
              Teléfono Celular (Opcional)
            </label>
            <input
              type="text"
              placeholder="+57 301 5554433"
              value={inviteForm.phone_number || ''}
              onChange={(e) => setInviteForm({ ...inviteForm, phone_number: e.target.value })}
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button type="button" variant="ghost" onClick={() => setIsInviteOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={isInviting}>
              {isInviting ? 'Generando Invitación...' : 'Generar Enlace Seguro'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ===================================================================== */}
      {/* 3. Modal de Despacho de Enlace de Invitación Generado                 */}
      {/* ===================================================================== */}
      <Modal
        isOpen={isResultModalOpen}
        onClose={() => setIsResultModalOpen(false)}
        title="Enlace de Invitación Generado"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div
            style={{
              backgroundColor: '#F0FDF4',
              border: '1px solid #BBF7D0',
              borderRadius: '8px',
              padding: '1rem',
              color: '#166534',
              fontSize: '0.875rem',
            }}
          >
            ✅ <strong>Invitación Criptográfica Creada:</strong> Envíe el siguiente enlace de activación al Rector. Este enlace es de un solo uso y expirará en 48 horas.
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
              Enlace de Activación para el Rector:
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                readOnly
                value={
                  generatedInvitation?.invitation_url ||
                  `${window.location.origin}/auth/accept-invitation?token=${generatedInvitation?.raw_invitation_token || ''}`
                }
                style={{
                  width: '100%',
                  padding: '0.625rem',
                  borderRadius: '6px',
                  border: '1px solid #CBD5E1',
                  backgroundColor: '#F8FAFC',
                  fontSize: '0.8125rem',
                  fontFamily: 'monospace',
                  color: '#0F172A',
                }}
              />
              <Button variant="primary" onClick={handleCopyLink}>
                {copiedLink ? '¡Copiado! ✓' : 'Copiar'}
              </Button>
            </div>
          </div>

          <div
            style={{
              backgroundColor: '#F8FAFC',
              borderRadius: '8px',
              border: '1px solid #E2E8F0',
              padding: '1rem',
              fontSize: '0.8125rem',
              color: '#475569',
            }}
          >
            <div><strong>Destinatario:</strong> {generatedInvitation?.email}</div>
            <div><strong>Expiración:</strong> 48 horas desde su emisión</div>
            <div style={{ marginTop: '0.5rem', color: '#64748B', fontSize: '0.75rem' }}>
              * El token se almacena en la base de datos únicamente como hash SHA-256. Este enlace no volverá a ser mostrado en texto plano por motivos de seguridad.
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
            <Button variant="primary" onClick={() => setIsResultModalOpen(false)}>
              Entendido y Cerrar
            </Button>
          </div>
        </div>
      </Modal>

      {/* ===================================================================== */}
      {/* 4. Modal de Confirmación de Cambio de Estado (Activar/Suspender)       */}
      {/* ===================================================================== */}
      <Modal
        isOpen={statusConfirmModal.isOpen}
        onClose={() => setStatusConfirmModal({ isOpen: false, institution: null, newStatus: false })}
        title={statusConfirmModal.newStatus ? 'Confirmar Reactivación' : 'Confirmar Suspensión'}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <p style={{ color: '#334155', fontSize: '0.9375rem', margin: 0 }}>
            ¿Está seguro de que desea {statusConfirmModal.newStatus ? 'reactivar' : 'suspender'} la institución{' '}
            <strong>{statusConfirmModal.institution?.name}</strong>?
          </p>
          {!statusConfirmModal.newStatus && (
            <div
              style={{
                backgroundColor: '#FEF2F2',
                border: '1px solid #FECACA',
                borderRadius: '8px',
                padding: '0.75rem',
                fontSize: '0.8125rem',
                color: '#991B1B',
              }}
            >
              ⚠️ Al suspender la institución, ningún usuario institucional (Rector, Docentes o Estudiantes) podrá realizar operaciones académicas ni matricular nuevos alumnos.
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button
              variant="ghost"
              onClick={() => setStatusConfirmModal({ isOpen: false, institution: null, newStatus: false })}
            >
              Cancelar
            </Button>
            <Button
              variant={statusConfirmModal.newStatus ? 'primary' : 'danger'}
              onClick={() => void handleStatusToggleSubmit()}
              disabled={isUpdatingStatus}
            >
              {isUpdatingStatus
                ? 'Actualizando...'
                : statusConfirmModal.newStatus
                ? 'Confirmar Reactivación'
                : 'Confirmar Suspensión'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default InstitutionsView
