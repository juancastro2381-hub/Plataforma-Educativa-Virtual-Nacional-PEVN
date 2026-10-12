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
import { Link, useSearchParams } from 'react-router-dom'
import { institutionApi, type ListInstitutionsParams } from '@/services/institution'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Modal } from '@/components/ui/Modal'
import { useAuth } from '@/hooks/useAuth'
import { resolveInvitationUrl } from '@/utils'
import type {
  DocumentType,
  InstitutionCreateRequest,
  InstitutionResponse,
  OfficialCatalogItem,
  OfficialCatalogSummary,
  OfficialCatalogSyncStatus,
  OfficialInstitutionResolution,
  RectorInvitationCreateRequest,
  RectorInvitationResponse,
} from '@/types'

export const InstitutionsView: React.FC = () => {
  const { user, hasRole, activeInstitutionId, setActiveInstitutionContext } = useAuth()
  const [searchParams] = useSearchParams()
  const isContextRequired = searchParams.get('contextRequired') === 'true'

  // Role resolution
  const isNationalAdmin = hasRole(['national_admin', 'superadmin']) || Boolean(user?.scope?.is_national)
  const isDepartmentAdmin = (hasRole('department_admin') || Boolean(user?.scope?.is_department)) && !isNationalAdmin
  const isMunicipalityAdmin = (hasRole('municipality_admin') || Boolean(user?.scope?.is_municipality)) && !isNationalAdmin && !isDepartmentAdmin
  const isTerritorialAdmin = isNationalAdmin || isDepartmentAdmin || isMunicipalityAdmin
  const isRector = hasRole(['rector', 'institution_admin']) && !isTerritorialAdmin
  const canSetContext = isTerritorialAdmin
  const canManageRectors = isTerritorialAdmin

  // Rector-Specific Institutional Portal State
  const [rectorInstitution, setRectorInstitution] = useState<InstitutionResponse | null>(null)
  const [isRectorLoading, setIsRectorLoading] = useState<boolean>(true)
  const [rectorError, setRectorError] = useState<string | null>(null)
  const [rectorTab, setRectorTab] = useState<'profile' | 'settings' | 'academic'>('profile')
  const [isDelegationSaving, setIsDelegationSaving] = useState<boolean>(false)
  const [delegationSuccess, setDelegationSuccess] = useState<string | null>(null)
  const [delegationError, setDelegationError] = useState<string | null>(null)

  const fetchRectorInstitution = useCallback(async () => {
    setIsRectorLoading(true)
    setRectorError(null)
    try {
      let inst: InstitutionResponse
      if (activeInstitutionId && !user?.institution_id) {
        inst = await institutionApi.getInstitutionById(activeInstitutionId)
      } else {
        inst = await institutionApi.getMyInstitution()
      }
      setRectorInstitution(inst)
      if (inst?.id && inst?.name) {
        setActiveInstitutionContext(inst.id, inst.name)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'No se pudo cargar la información de su institución educativa asignada.'
      setRectorError(msg)
    } finally {
      setIsRectorLoading(false)
    }
  }, [user, activeInstitutionId, setActiveInstitutionContext])

  const handleToggleRectorDelegation = async (newVal: boolean) => {
    if (!rectorInstitution) return
    setIsDelegationSaving(true)
    setDelegationError(null)
    setDelegationSuccess(null)
    try {
      const updated = await institutionApi.updateCoordinatorDelegationSetting(rectorInstitution.id, newVal)
      setRectorInstitution((prev) =>
        prev ? { ...prev, coordinator_delegation_enabled: updated.coordinator_delegation_enabled } : prev
      )
      setDelegationSuccess(
        updated.coordinator_delegation_enabled
          ? '✓ Delegación operativa habilitada. Los coordinadores de su institución ahora pueden gestionar docentes, estudiantes y acudientes.'
          : '✓ Delegación operativa inhabilitada. Las facultades de gestión para coordinadores quedan restringidas.'
      )
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al actualizar delegación para coordinadores.'
      setDelegationError(msg)
    } finally {
      setIsDelegationSaving(false)
    }
  }

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

  // View Mode: 'catalog' for official MEN/DANE territorial catalog, 'tenants' for provisioned operational institutions
  const [activeTab, setActiveTab] = useState<'catalog' | 'tenants'>('catalog')

  // Official Catalog Explorer State
  const [catalogItems, setCatalogItems] = useState<OfficialCatalogItem[]>([])
  const [catalogSummary, setCatalogSummary] = useState<OfficialCatalogSummary | null>(null)
  const [catalogTotal, setCatalogTotal] = useState<number>(0)
  const [catalogPage, setCatalogPage] = useState<number>(1)
  const [catalogPageSize] = useState<number>(10)
  const [isCatalogLoading, setIsCatalogLoading] = useState<boolean>(true)
  const [catalogSearchQuery, setCatalogSearchQuery] = useState<string>('')
  const [catalogStatusFilter, setCatalogStatusFilter] = useState<string>('all')

  // Catalog Provisioning Modal State
  const [provisionModal, setProvisionModal] = useState<{
    isOpen: boolean
    item: OfficialCatalogItem | null
    email: string
    phone: string
    isSubmitting: boolean
    error: string | null
  }>({
    isOpen: false,
    item: null,
    email: '',
    phone: '',
    isSubmitting: false,
    error: null,
  })

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

  const fetchOfficialCatalog = useCallback(async () => {
    setIsCatalogLoading(true)
    try {
      const params: Parameters<typeof institutionApi.listOfficialCatalog>[0] = {
        page: catalogPage,
        page_size: catalogPageSize,
      }
      if (catalogSearchQuery.trim()) {
        params.search = catalogSearchQuery.trim()
      }
      if (catalogStatusFilter !== 'all') {
        params.status_filter = catalogStatusFilter
      }
      const res = await institutionApi.listOfficialCatalog(params)
      setCatalogItems(res.items)
      setCatalogTotal(res.total)
      setCatalogSummary(res.summary)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar el catálogo oficial de instituciones.'
      setError(msg)
    } finally {
      setIsCatalogLoading(false)
    }
  }, [catalogPage, catalogPageSize, catalogSearchQuery, catalogStatusFilter])

  useEffect(() => {
    if (isRector) {
      void fetchRectorInstitution()
    } else {
      void fetchInstitutions()
      void fetchCatalogStatus()
      void fetchOfficialCatalog()
    }
  }, [isRector, fetchRectorInstitution, fetchInstitutions, fetchCatalogStatus, fetchOfficialCatalog])

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
      if (selectedInstForInvite) {
        setInstitutions((prev) =>
          prev.map((item) =>
            item.id === selectedInstForInvite.id
              ? { ...item, has_pending_invitation: true, has_active_rector: false }
              : item
          )
        )
      }
      void fetchOfficialCatalog()
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

  // Absolute Invitation URL Resolver
  const getAbsoluteInvitationUrl = (invitation: RectorInvitationResponse | null) => {
    if (!invitation) return ''
    return resolveInvitationUrl(invitation.invitation_url, invitation.raw_invitation_token) || ''
  }

  // Copy Link to Clipboard
  const handleCopyLink = () => {
    if (!generatedInvitation) return
    const url = getAbsoluteInvitationUrl(generatedInvitation)
    if (!url) return

    void navigator.clipboard.writeText(url)
    setCopiedLink(true)
    setTimeout(() => {
      setCopiedLink(false)
    }, 3000)
  }

  // Handle Resend Rector Invitation
  const handleResendInvite = async (inst: InstitutionResponse) => {
    setIsInviting(true)
    setError(null)
    setInviteError(null)
    try {
      const res = await institutionApi.resendRectorInvitation(inst.id)
      setSelectedInstForInvite(inst)
      setGeneratedInvitation(res)
      setCopiedLink(false)
      setIsResultModalOpen(true)
      setSuccessMsg(`Nueva invitación generada para el Rector de "${inst.name}".`)
      setInstitutions((prev) =>
        prev.map((item) =>
          item.id === inst.id
            ? { ...item, has_pending_invitation: true, has_active_rector: false }
            : item
        )
      )
      void fetchOfficialCatalog()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al reenviar invitación para el Rector.'
      setError(msg)
    } finally {
      setIsInviting(false)
    }
  }

  // Catalog Handlers
  const handleCatalogSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setCatalogPage(1)
    void fetchOfficialCatalog()
  }

  const handleClearCatalogFilters = () => {
    setCatalogSearchQuery('')
    setCatalogStatusFilter('all')
    setCatalogPage(1)
  }

  const handleOpenProvisionModal = (item: OfficialCatalogItem) => {
    setProvisionModal({
      isOpen: true,
      item,
      email: item.official_email || `contacto.${item.dane_code}@colegio.edu.co`,
      phone: item.official_phone || '',
      isSubmitting: false,
      error: null,
    })
  }

  const handleConfirmCatalogProvision = async () => {
    if (!provisionModal.item) return
    setProvisionModal((prev) => ({ ...prev, isSubmitting: true, error: null }))
    try {
      const newInst = await institutionApi.provisionFromCatalog({
        dane_code: provisionModal.item.dane_code,
        contact_email: provisionModal.email.trim() || undefined,
        contact_phone: provisionModal.phone.trim() || undefined,
      })
      setSuccessMsg(
        `✓ Establecimiento "${newInst.name}" (DANE: ${newInst.dane_code}) aprovisionado exitosamente en PEVN con sus ${provisionModal.item.campus_count} sedes registradas.`
      )
      setProvisionModal({ isOpen: false, item: null, email: '', phone: '', isSubmitting: false, error: null })
      await fetchOfficialCatalog()
      await fetchInstitutions()

      // Prompt to invite Rector immediately
      setSelectedInstForInvite(newInst)
      setInviteForm({
        first_name: '',
        last_name: '',
        document_type: 'CC',
        document_number: '',
        email: newInst.email || '',
        phone_number: newInst.phone || '',
      })
      setInviteError(null)
      setIsInviteOpen(true)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al aprovisionar establecimiento educativo.'
      setProvisionModal((prev) => ({ ...prev, isSubmitting: false, error: msg }))
    }
  }

  const handleOpenInviteFromCatalog = (catItem: OfficialCatalogItem) => {
    if (!catItem.institution_id) return
    const existing = institutions.find((i) => i.id === catItem.institution_id)
    const instObj: InstitutionResponse = existing || {
      id: catItem.institution_id,
      municipality_id: catItem.municipality_code,
      dane_code: catItem.dane_code,
      name: catItem.name,
      email: catItem.official_email || '',
      phone: catItem.official_phone || null,
      address: catItem.official_address || null,
      is_active: true,
      campuses: [],
      has_active_rector: catItem.has_active_rector,
      has_pending_invitation: catItem.has_pending_invitation,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    setSelectedInstForInvite(instObj)
    setInviteForm({
      first_name: '',
      last_name: '',
      document_type: 'CC',
      document_number: '',
      email: catItem.official_email || '',
      phone_number: catItem.official_phone || '',
    })
    setInviteError(null)
    setIsInviteOpen(true)
  }

  const handleResendInviteFromCatalog = async (catItem: OfficialCatalogItem) => {
    if (!catItem.institution_id) return
    const existing = institutions.find((i) => i.id === catItem.institution_id)
    const instObj: InstitutionResponse = existing || {
      id: catItem.institution_id,
      municipality_id: catItem.municipality_code,
      dane_code: catItem.dane_code,
      name: catItem.name,
      email: catItem.official_email || '',
      phone: catItem.official_phone || null,
      address: catItem.official_address || null,
      is_active: true,
      campuses: [],
      has_active_rector: catItem.has_active_rector,
      has_pending_invitation: catItem.has_pending_invitation,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    await handleResendInvite(instObj)
    await fetchOfficialCatalog()
  }

  // Rector-Specific Institutional Experience (NTA-10-R3)
  if (isRector) {
    if (isRectorLoading) {
      return (
        <div style={{ maxWidth: '1280px', margin: '3rem auto', padding: '0 1rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
          <LoadingSpinner size="lg" />
          <p style={{ color: '#64748B', fontSize: '0.95rem' }}>Cargando portal institucional del Rector...</p>
        </div>
      )
    }

    if (rectorError || !rectorInstitution) {
      return (
        <div style={{ maxWidth: '1280px', margin: '2rem auto', padding: '0 1rem' }}>
          <Card style={{ padding: '2rem', border: '1px solid #FECDD3', backgroundColor: '#FFF1F2' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
              <div style={{ fontSize: '2rem' }}>⚠️</div>
              <div>
                <h2 style={{ margin: '0 0 0.5rem 0', color: '#9F1239', fontSize: '1.25rem', fontWeight: 700 }}>
                  No se pudo cargar la información de su institución educativa
                </h2>
                <p style={{ margin: '0 0 1rem 0', color: '#881337', fontSize: '0.9rem', lineHeight: '1.5' }}>
                  {rectorError || 'No se encontró un registro institucional asociado a su cuenta de Rector.'}
                </p>
                <div style={{ fontSize: '0.8rem', color: '#9F1239', backgroundColor: '#FFE4E6', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontFamily: 'monospace' }}>
                  <div><strong>ID Institución en Sesión:</strong> {activeInstitutionId || user?.institution_id || 'No asignado'}</div>
                  <div><strong>Usuario Autenticado:</strong> {user?.email} ({user?.first_name} {user?.last_name})</div>
                  <div><strong>Rol Activo:</strong> {user?.roles?.[0] || 'rector'}</div>
                </div>
                <Button variant="primary" onClick={() => void fetchRectorInstitution()}>
                  🔄 Reintentar Carga
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )
    }

    return (
      <div style={{ maxWidth: '1280px', margin: '2rem auto', padding: '0 1rem' }}>
        {/* Rector Institutional Header Banner */}
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
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '9999px',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  backgroundColor: '#1E293B',
                  color: '#93C5FD',
                  border: '1px solid #3B82F6',
                }}
              >
                🏛️ Portal del Rector
              </span>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '9999px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  backgroundColor: '#064E3B',
                  color: '#A7F3D0',
                }}
              >
                DANE: {rectorInstitution.dane_code}
              </span>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '9999px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  backgroundColor: rectorInstitution.is_active ? '#064E3B' : '#7F1D1D',
                  color: rectorInstitution.is_active ? '#6EE7B7' : '#FCA5A5',
                }}
              >
                {rectorInstitution.is_active ? '● Estado: Activa' : '○ Estado: Inactiva'}
              </span>
            </div>
            <h1 style={{ fontSize: '1.875rem', fontWeight: 800, margin: '0 0 0.5rem 0', letterSpacing: '-0.025em' }}>
              {rectorInstitution.name}
            </h1>
            <p style={{ margin: 0, color: '#94A3B8', fontSize: '0.95rem', maxWidth: '700px' }}>
              Gestión directiva e institucional del establecimiento educativo oficial bajo la jurisdicción de la Secretaría de Educación correspondiente.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <Link
              to="/dashboard"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                backgroundColor: '#1E293B',
                color: '#E2E8F0',
                border: '1px solid #334155',
                padding: '0.6rem 1rem',
                borderRadius: '8px',
                fontSize: '0.875rem',
                fontWeight: 600,
                textDecoration: 'none',
              }}
            >
              📊 Tablero General
            </Link>
            <Link
              to="/admin/users"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                backgroundColor: '#2563EB',
                color: '#FFFFFF',
                padding: '0.6rem 1.25rem',
                borderRadius: '8px',
                fontSize: '0.875rem',
                fontWeight: 600,
                textDecoration: 'none',
              }}
            >
              👥 Docentes y Personal
            </Link>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #E2E8F0', paddingBottom: '0.5rem' }}>
          <button
            type="button"
            onClick={() => setRectorTab('profile')}
            style={{
              padding: '0.6rem 1.2rem',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.9rem',
              backgroundColor: rectorTab === 'profile' ? '#2563EB' : 'transparent',
              color: rectorTab === 'profile' ? '#FFFFFF' : '#64748B',
              transition: 'all 0.2s',
            }}
          >
            🏛️ Información y Sedes
          </button>
          <button
            type="button"
            onClick={() => setRectorTab('settings')}
            style={{
              padding: '0.6rem 1.2rem',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.9rem',
              backgroundColor: rectorTab === 'settings' ? '#2563EB' : 'transparent',
              color: rectorTab === 'settings' ? '#FFFFFF' : '#64748B',
              transition: 'all 0.2s',
            }}
          >
            ⚙️ Delegación Operativa
          </button>
          <button
            type="button"
            onClick={() => setRectorTab('academic')}
            style={{
              padding: '0.6rem 1.2rem',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.9rem',
              backgroundColor: rectorTab === 'academic' ? '#2563EB' : 'transparent',
              color: rectorTab === 'academic' ? '#FFFFFF' : '#64748B',
              transition: 'all 0.2s',
            }}
          >
            📚 Accesos Académicos
          </button>
        </div>

        {/* Tab Content: Profile & Campuses */}
        {rectorTab === 'profile' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* Identity & Basic Info Card */}
            <Card style={{ padding: '1.75rem', border: '1px solid #E2E8F0' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', margin: '0 0 1.25rem 0' }}>
                Ficha Técnica del Establecimiento Educativo
              </h2>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                  gap: '1.25rem',
                  fontSize: '0.9rem',
                }}
              >
                <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                  <span style={{ display: 'block', color: '#64748B', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>
                    Código DANE Oficial
                  </span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0F172A', fontFamily: 'monospace' }}>
                    {rectorInstitution.dane_code}
                  </span>
                </div>
                <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                  <span style={{ display: 'block', color: '#64748B', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>
                    Rector Titular Asignado
                  </span>
                  <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#1E40AF' }}>
                    {rectorInstitution.active_rector_name || `${user?.first_name || ''} ${user?.last_name || ''}`.trim() || 'Rector Activo'}
                  </span>
                  {rectorInstitution.active_rector_email && (
                    <span style={{ display: 'block', fontSize: '0.8rem', color: '#64748B' }}>
                      {rectorInstitution.active_rector_email}
                    </span>
                  )}
                </div>
                <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                  <span style={{ display: 'block', color: '#64748B', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>
                    Correo Institucional
                  </span>
                  <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#334155' }}>
                    {rectorInstitution.email || 'No registrado'}
                  </span>
                </div>
                <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                  <span style={{ display: 'block', color: '#64748B', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>
                    Teléfono Institucional
                  </span>
                  <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#334155' }}>
                    {rectorInstitution.phone || 'No registrado'}
                  </span>
                </div>
                <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px', border: '1px solid #E2E8F0', gridColumn: 'span 2' }}>
                  <span style={{ display: 'block', color: '#64748B', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>
                    Dirección Institucional
                  </span>
                  <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#334155' }}>
                    {rectorInstitution.address || 'Sin dirección registrada en el catálogo oficial'}
                  </span>
                </div>
                <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                  <span style={{ display: 'block', color: '#64748B', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>
                    Identificador de Inquilino (Tenant ID)
                  </span>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B', fontFamily: 'monospace' }}>
                    {rectorInstitution.id}
                  </span>
                </div>
              </div>
            </Card>

            {/* Campuses Section */}
            <Card style={{ padding: '1.75rem', border: '1px solid #E2E8F0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
                    Sedes Educativas Registradas
                  </h2>
                  <p style={{ margin: 0, color: '#64748B', fontSize: '0.85rem' }}>
                    Sedes asociadas y habilitadas bajo la matrícula institucional del establecimiento.
                  </p>
                </div>
                <Badge variant="primary">
                  {rectorInstitution.campuses?.length || 0} {(rectorInstitution.campuses?.length === 1) ? 'Sede' : 'Sedes'}
                </Badge>
              </div>

              {!rectorInstitution.campuses || rectorInstitution.campuses.length === 0 ? (
                <EmptyState
                  title="No hay sedes registradas"
                  description="No se encontraron sedes anexas asociadas a la institución educativa en este momento."
                />
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
                  {rectorInstitution.campuses.map((campus) => (
                    <div
                      key={campus.id}
                      style={{
                        padding: '1.25rem',
                        borderRadius: '12px',
                        border: campus.is_main ? '2px solid #3B82F6' : '1px solid #E2E8F0',
                        backgroundColor: campus.is_main ? '#F8FAFC' : '#FFFFFF',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        gap: '0.75rem',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', marginBottom: '0.5rem' }}>
                          {campus.is_main ? (
                            <span
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                padding: '0.2rem 0.5rem',
                                borderRadius: '9999px',
                                fontSize: '0.7rem',
                                fontWeight: 700,
                                backgroundColor: '#DBEAFE',
                                color: '#1D4ED8',
                              }}
                            >
                              ★ Sede Principal
                            </span>
                          ) : (
                            <span
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                padding: '0.2rem 0.5rem',
                                borderRadius: '9999px',
                                fontSize: '0.7rem',
                                fontWeight: 600,
                                backgroundColor: '#F1F5F9',
                                color: '#475569',
                              }}
                            >
                              Sede Anexa
                            </span>
                          )}
                          <span
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              padding: '0.15rem 0.45rem',
                              borderRadius: '9999px',
                              fontSize: '0.7rem',
                              fontWeight: 600,
                              backgroundColor: campus.is_active ? '#DCFCE7' : '#FEE2E2',
                              color: campus.is_active ? '#15803D' : '#B91C1C',
                            }}
                          >
                            {campus.is_active ? 'Activa' : 'Inactiva'}
                          </span>
                        </div>
                        <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.05rem', fontWeight: 700, color: '#0F172A' }}>
                          {campus.name}
                        </h3>
                        <div style={{ fontSize: '0.825rem', color: '#64748B', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                          <div><strong>DANE Sede:</strong> <span style={{ fontFamily: 'monospace' }}>{campus.dane_sede_code}</span></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Tab Content: Settings & Coordinator Delegation */}
        {rectorTab === 'settings' && (
          <Card style={{ padding: '2rem', border: '1px solid #E2E8F0' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', margin: '0 0 0.5rem 0' }}>
              Delegación Operativa para Coordinadores (NTA-10-R1)
            </h2>
            <p style={{ margin: '0 0 1.5rem 0', color: '#64748B', fontSize: '0.9rem', lineHeight: '1.6' }}>
              Como Rector titular de la institución, usted puede facultar o restringir a los coordinadores académicos y disciplinarios registrados para gestionar la creación, modificación y administración de docentes, estudiantes y acudientes.
            </p>

            {delegationSuccess && (
              <div style={{ marginBottom: '1.5rem' }}>
                <Alert variant="success" message={delegationSuccess} />
              </div>
            )}
            {delegationError && (
              <div style={{ marginBottom: '1.5rem' }}>
                <Alert variant="error" message={delegationError} />
              </div>
            )}

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '1.5rem',
                backgroundColor: '#F8FAFC',
                borderRadius: '12px',
                border: '1px solid #E2E8F0',
                gap: '1.5rem',
                flexWrap: 'wrap',
              }}
            >
              <div style={{ maxWidth: '650px' }}>
                <div style={{ fontWeight: 700, color: '#0F172A', fontSize: '1rem', marginBottom: '0.25rem' }}>
                  {rectorInstitution.coordinator_delegation_enabled
                    ? 'Delegación Operativa Activa'
                    : 'Delegación Operativa Desactivada'}
                </div>
                <div style={{ color: '#64748B', fontSize: '0.85rem', lineHeight: '1.5' }}>
                  {rectorInstitution.coordinator_delegation_enabled
                    ? 'Los coordinadores tienen permisos para administrar altas y ediciones de docentes y estudiantes en esta institución.'
                    : 'Solo el Rector y administradores territoriales pueden realizar altas y modificaciones del personal institucional.'}
                </div>
              </div>
              <Button
                variant={rectorInstitution.coordinator_delegation_enabled ? 'danger' : 'primary'}
                disabled={isDelegationSaving}
                onClick={() => void handleToggleRectorDelegation(!rectorInstitution.coordinator_delegation_enabled)}
              >
                {isDelegationSaving
                  ? 'Guardando...'
                  : rectorInstitution.coordinator_delegation_enabled
                  ? 'Deshabilitar Delegación'
                  : 'Habilitar Delegación'}
              </Button>
            </div>
          </Card>
        )}

        {/* Tab Content: Academic Modules */}
        {rectorTab === 'academic' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            <Card style={{ padding: '1.75rem', border: '1px solid #E2E8F0', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>👥</div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0F172A', margin: '0 0 0.5rem 0' }}>
                  Gestión de Usuarios y Personal
                </h3>
                <p style={{ color: '#64748B', fontSize: '0.875rem', lineHeight: '1.5', margin: '0 0 1.25rem 0' }}>
                  Consulte y administre el cuerpo docente, coordinadores, directores de grupo y personal vinculado a {rectorInstitution.name}.
                </p>
              </div>
              <Link
                to="/admin/users"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '0.6rem 1rem',
                  backgroundColor: '#2563EB',
                  color: '#FFFFFF',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                }}
              >
                Ir a Usuarios Institucionales →
              </Link>
            </Card>

            <Card style={{ padding: '1.75rem', border: '1px solid #E2E8F0', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>📊</div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0F172A', margin: '0 0 0.5rem 0' }}>
                  Tablero de Control Institucional
                </h3>
                <p style={{ color: '#64748B', fontSize: '0.875rem', lineHeight: '1.5', margin: '0 0 1.25rem 0' }}>
                  Revise los indicadores operativos, métricas de actividad y estado de la plataforma para su institución.
                </p>
              </div>
              <Link
                to="/dashboard"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '0.6rem 1rem',
                  backgroundColor: '#0F172A',
                  color: '#FFFFFF',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                }}
              >
                Ver Tablero General →
              </Link>
            </Card>
          </div>
        )}
      </div>
    )
  }

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
                backgroundColor: isMunicipalityAdmin
                  ? 'rgba(16, 185, 129, 0.2)'
                  : isDepartmentAdmin
                  ? 'rgba(56, 189, 248, 0.2)'
                  : 'rgba(252, 209, 22, 0.2)',
                color: isMunicipalityAdmin
                  ? '#34D399'
                  : isDepartmentAdmin
                  ? '#38BDF8'
                  : '#FCD116',
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
              }}
            >
              {isMunicipalityAdmin
                ? `Nivel Municipal • Secretaría de Educación Municipal (${user?.scope.jurisdiction_name || user?.scope.municipality_code || 'Territorial'})`
                : isDepartmentAdmin
                ? `Nivel Departamental • Secretaría de Educación (DANE ${user?.scope.department_id || 'Territorial'})`
                : hasRole('superadmin')
                ? 'Nivel Global • Operador Técnico de Plataforma'
                : 'Nivel Nacional • Ministerio de Educación'}
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
            {isMunicipalityAdmin
              ? 'Supervisión Municipal de Instituciones Educativas'
              : isDepartmentAdmin
              ? 'Supervisión de Instituciones Educativas'
              : 'Aprovisionamiento de Instituciones'}
          </h1>
          <p style={{ color: '#94A3B8', fontSize: '0.9375rem', margin: 0, maxWidth: '650px' }}>
            {isMunicipalityAdmin
              ? 'Inspección y supervisión de colegios oficiales y sedes educativas del municipio asignado.'
              : isDepartmentAdmin
              ? 'Inspección y supervisión territorial de colegios oficiales y sedes en la jurisdicción del departamento.'
              : 'Registro de colegios con validación DANE de 12 dígitos, creación de sedes principales y emisión segura de invitaciones criptográficas para Rectores.'}
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
              variant="secondary"
              onClick={() => (window.location.href = '/admin/onboarding')}
              style={{
                borderColor: '#059669',
                color: '#34D399',
                fontWeight: 600,
                padding: '0.75rem 1.25rem',
              }}
            >
              📋 Flujo de Incorporación NTA-04
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

      {/* Context Selection Required Prompt */}
      {isContextRequired && !activeInstitutionId && (
        <div style={{ marginBottom: '1.5rem' }}>
          <Alert variant="info" title="Selección de Contexto Requerida">
            Para acceder a los módulos de Gestión Académica y Aulas Virtuales, seleccione una institución activa de su jurisdicción territorial haciendo clic en el botón <strong>🏛️ Contexto</strong> de la lista inferior.
          </Alert>
        </div>
      )}

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

      {/* View Mode Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '0.75rem',
          marginBottom: '1.5rem',
          borderBottom: '2px solid #E2E8F0',
          paddingBottom: '0.75rem',
          flexWrap: 'wrap',
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab('catalog')}
          style={{
            padding: '0.625rem 1.25rem',
            borderRadius: '8px',
            fontWeight: 700,
            fontSize: '0.875rem',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: activeTab === 'catalog' ? '#0F172A' : '#F1F5F9',
            color: activeTab === 'catalog' ? '#FFFFFF' : '#475569',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'all 0.15s ease',
          }}
        >
          <span>🏛️</span>
          <span>Catálogo Oficial Territorial (DANE/MEN)</span>
          {catalogSummary && (
            <span
              style={{
                fontSize: '0.75rem',
                padding: '0.125rem 0.5rem',
                borderRadius: '9999px',
                backgroundColor: activeTab === 'catalog' ? '#3B82F6' : '#CBD5E1',
                color: activeTab === 'catalog' ? '#FFFFFF' : '#1E293B',
                fontWeight: 700,
              }}
            >
              {catalogSummary.total_catalog}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('tenants')}
          style={{
            padding: '0.625rem 1.25rem',
            borderRadius: '8px',
            fontWeight: 700,
            fontSize: '0.875rem',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: activeTab === 'tenants' ? '#0F172A' : '#F1F5F9',
            color: activeTab === 'tenants' ? '#FFFFFF' : '#475569',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'all 0.15s ease',
          }}
        >
          <span>🏢</span>
          <span>Colegios Aprovisionados (Tenants)</span>
          <span
            style={{
              fontSize: '0.75rem',
              padding: '0.125rem 0.5rem',
              borderRadius: '9999px',
              backgroundColor: activeTab === 'tenants' ? '#10B981' : '#CBD5E1',
              color: activeTab === 'tenants' ? '#FFFFFF' : '#1E293B',
              fontWeight: 700,
            }}
          >
            {total}
          </span>
        </button>
      </div>

      {/* ===================================================================== */}
      {/* TAB 1: CATÁLOGO OFICIAL TERRITORIAL (DANE / MEN)                       */}
      {/* ===================================================================== */}
      {activeTab === 'catalog' && (
        <>
          {/* Summary Metric KPI Cards */}
          {catalogSummary && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1rem',
                marginBottom: '1.5rem',
              }}
            >
              <Card style={{ padding: '1rem', borderLeft: '4px solid #3B82F6' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>
                  Catálogo Oficial DANE
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', marginTop: '0.25rem' }}>
                  {catalogSummary.total_catalog}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
                  Establecimientos en jurisdicción
                </div>
              </Card>

              <Card style={{ padding: '1rem', borderLeft: '4px solid #06B6D4' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>
                  Disponibles para Aprovisionar
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0891B2', marginTop: '0.25rem' }}>
                  {catalogSummary.available}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
                  Listos para ser incorporados
                </div>
              </Card>

              <Card style={{ padding: '1rem', borderLeft: '4px solid #10B981' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>
                  Colegios Aprovisionados
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#059669', marginTop: '0.25rem' }}>
                  {catalogSummary.provisioned}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
                  Tenants activos en PEVN
                </div>
              </Card>

              <Card style={{ padding: '1rem', borderLeft: '4px solid #F59E0B' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>
                  Invitación Rector Pendiente
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#D97706', marginTop: '0.25rem' }}>
                  {catalogSummary.pending_invite}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
                  En proceso de activación (48h)
                </div>
              </Card>

              <Card style={{ padding: '1rem', borderLeft: '4px solid #8B5CF6' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>
                  Rector Titular Activo
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#7C3AED', marginTop: '0.25rem' }}>
                  {catalogSummary.active_rector}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
                  Titular con acceso operativo
                </div>
              </Card>
            </div>
          )}

          {/* Filter & Search Bar for Catalog */}
          <Card style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
            <form
              onSubmit={handleCatalogSearchSubmit}
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
                    placeholder="Buscar por Nombre oficial o Código DANE..."
                    value={catalogSearchQuery}
                    onChange={(e) => setCatalogSearchQuery(e.target.value)}
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
                  value={catalogStatusFilter}
                  onChange={(e) => {
                    setCatalogStatusFilter(e.target.value)
                    setCatalogPage(1)
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
                  <option value="DISPONIBLE_PARA_APROVISIONAR">Disponible para aprovisionar</option>
                  <option value="APROVISIONADA_SIN_RECTOR">Aprovisionada — Sin Rector</option>
                  <option value="INVITACION_RECTOR_PENDIENTE">Invitación de Rector pendiente</option>
                  <option value="RECTOR_ACTIVO">Rector activo</option>
                  <option value="INACTIVA">Inactiva</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <Button type="submit" variant="secondary">
                  🔍 Filtrar Catálogo
                </Button>
                {(catalogSearchQuery || catalogStatusFilter !== 'all') && (
                  <Button type="button" variant="ghost" onClick={handleClearCatalogFilters}>
                    Limpiar
                  </Button>
                )}
              </div>
            </form>
          </Card>

          {/* Official Catalog Table */}
          <Card style={{ padding: 0, marginBottom: '2rem' }}>
            {isCatalogLoading ? (
              <div style={{ padding: '4rem 1rem', display: 'flex', justifyContent: 'center' }}>
                <LoadingSpinner size="lg" label="Cargando catálogo oficial de establecimientos y sedes..." />
              </div>
            ) : catalogItems.length === 0 ? (
              <div style={{ padding: '3rem 1rem' }}>
                <EmptyState
                  title="No se encontraron establecimientos en el catálogo"
                  description={
                    catalogSearchQuery
                      ? 'No hay registros oficiales que coincidan con los criterios de búsqueda.'
                      : 'No se encontraron establecimientos registrados para esta jurisdicción territorial.'
                  }
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
                      <th style={{ padding: '1rem', fontWeight: 700 }}>Establecimiento Educativo Oficial</th>
                      <th style={{ padding: '1rem', fontWeight: 700 }}>Sedes Registradas</th>
                      <th style={{ padding: '1rem', fontWeight: 700 }}>Jurisdicción</th>
                      <th style={{ padding: '1rem', fontWeight: 700, textAlign: 'center' }}>Estado PEVN / Rector</th>
                      <th style={{ padding: '1rem', fontWeight: 700, textAlign: 'right' }}>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {catalogItems.map((item) => (
                      <tr
                        key={item.id}
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
                            {item.dane_code}
                          </span>
                        </td>
                        <td style={{ padding: '1rem' }}>
                          <div style={{ fontWeight: 700, color: '#0F172A' }}>{item.name}</div>
                          <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                            Sector: {item.sector || 'OFICIAL'} • {item.official_email || 'Sin correo oficial'}
                          </div>
                          {item.official_address && (
                            <div style={{ fontSize: '0.75rem', color: '#94A3B8' }}>{item.official_address}</div>
                          )}
                        </td>
                        <td style={{ padding: '1rem' }}>
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', backgroundColor: '#EFF6FF', color: '#1D4ED8', padding: '0.2rem 0.6rem', borderRadius: '6px', fontWeight: 700, fontSize: '0.8125rem' }}>
                            🏛️ {item.campus_count} {item.campus_count === 1 ? 'sede oficial' : 'sedes oficiales'}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
                            Sede Principal {item.campus_count > 1 ? `+ ${item.campus_count - 1} anexas` : ''}
                          </div>
                        </td>
                        <td style={{ padding: '1rem', color: '#475569' }}>
                          <div style={{ fontWeight: 600 }}>{item.municipality_name} ({item.municipality_code})</div>
                          <div style={{ fontSize: '0.75rem', color: '#64748B' }}>{item.department_name}</div>
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'center' }}>
                          {item.lifecycle_status === 'DISPONIBLE_PARA_APROVISIONAR' && (
                            <Badge variant="info">⚡ Disponible para aprovisionar</Badge>
                          )}
                          {item.lifecycle_status === 'APROVISIONADA_SIN_RECTOR' && (
                            <Badge variant="warning">⚠️ Aprovisionada — Sin Rector</Badge>
                          )}
                          {item.lifecycle_status === 'INVITACION_RECTOR_PENDIENTE' && (
                            <div>
                              <Badge variant="warning">⏳ Invitación de Rector pendiente</Badge>
                              <div style={{ fontSize: '0.75rem', color: '#B45309', marginTop: '0.25rem' }}>
                                Esperando activación (48h)
                              </div>
                            </div>
                          )}
                          {item.lifecycle_status === 'RECTOR_ACTIVO' && (
                            <div>
                              <Badge variant="success">✓ Rector activo</Badge>
                              {item.active_rector_name && (
                                <div style={{ fontWeight: 600, color: '#0F172A', fontSize: '0.8125rem', marginTop: '0.25rem' }}>
                                  {item.active_rector_name}
                                </div>
                              )}
                              {item.active_rector_email && (
                                <div style={{ fontSize: '0.75rem', color: '#64748B' }}>{item.active_rector_email}</div>
                              )}
                            </div>
                          )}
                          {item.lifecycle_status === 'INACTIVA' && (
                            <Badge variant="neutral">Inactiva</Badge>
                          )}
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'right' }}>
                          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', alignItems: 'center' }}>
                            {item.lifecycle_status === 'DISPONIBLE_PARA_APROVISIONAR' && (
                              <Button
                                variant="primary"
                                size="sm"
                                onClick={() => handleOpenProvisionModal(item)}
                                title="Aprovisionar este establecimiento educativo oficial como tenant PEVN"
                                style={{ backgroundColor: '#0284C7', fontWeight: 600 }}
                              >
                                ⚡ Aprovisionar
                              </Button>
                            )}

                            {item.lifecycle_status === 'APROVISIONADA_SIN_RECTOR' && canManageRectors && (
                              <Button
                                variant="primary"
                                size="sm"
                                onClick={() => handleOpenInviteFromCatalog(item)}
                                title="Generar invitación para el Rector titular de esta institución"
                              >
                                ✉️ Invitar Rector
                              </Button>
                            )}

                            {item.lifecycle_status === 'INVITACION_RECTOR_PENDIENTE' && canManageRectors && (
                              <Button
                                variant="ghost"
                                size="sm"
                                disabled={isInviting}
                                onClick={() => void handleResendInviteFromCatalog(item)}
                                title="Reenviar enlace de activación al Rector"
                                style={{ color: '#D97706', borderColor: '#FDE68A' }}
                              >
                                🔄 Reenviar
                              </Button>
                            )}

                            {item.lifecycle_status === 'RECTOR_ACTIVO' && (
                              <span
                                style={{
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  color: '#16A34A',
                                  padding: '0.25rem 0.5rem',
                                  backgroundColor: '#DCFCE7',
                                  borderRadius: '4px',
                                }}
                              >
                                ✓ Titular Asignado
                              </span>
                            )}

                            {item.institution_id && canSetContext && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setActiveInstitutionContext(item.institution_id!, item.name)
                                  setSuccessMsg(`Contexto establecido en "${item.name}".`)
                                }}
                                title="Fijar como contexto institucional activo"
                              >
                                🏛️ Contexto
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination Bar for Catalog */}
            {catalogTotal > catalogPageSize && (
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
                  Mostrando {catalogItems.length} de {catalogTotal} establecimientos oficiales
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={catalogPage <= 1}
                    onClick={() => setCatalogPage((p) => Math.max(1, p - 1))}
                  >
                    Anterior
                  </Button>
                  <span style={{ alignSelf: 'center', fontWeight: 600, color: '#334155' }}>
                    Página {catalogPage} de {Math.ceil(catalogTotal / catalogPageSize)}
                  </span>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={catalogPage >= Math.ceil(catalogTotal / catalogPageSize)}
                    onClick={() => setCatalogPage((p) => p + 1)}
                  >
                    Siguiente
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </>
      )}

      {/* ===================================================================== */}
      {/* TAB 2: COLEGIOS APROVISIONADOS (OPERATIONAL TENANTS)                   */}
      {/* ===================================================================== */}
      {activeTab === 'tenants' && (
        <>
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

          {/* Tenants Table */}
          <Card style={{ padding: 0 }}>
            {isLoading ? (
              <div style={{ padding: '4rem 1rem', display: 'flex', justifyContent: 'center' }}>
                <LoadingSpinner size="lg" label="Cargando catálogo nacional de instituciones..." />
              </div>
            ) : institutions.length === 0 ? (
              <div style={{ padding: '3rem 1rem' }}>
                <EmptyState
                  title="No se encontraron instituciones aprovisionadas"
                  description={
                    searchQuery
                      ? 'No hay instituciones que coincidan con los criterios de búsqueda.'
                      : 'Aún no se han aprovisionado instituciones educativas en la plataforma.'
                  }
                  actionLabel="Explorar Catálogo Oficial para Aprovisionar"
                  onAction={() => setActiveTab('catalog')}
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
                      <th style={{ padding: '1rem', fontWeight: 700 }}>Rector</th>
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
                          <td style={{ padding: '1rem' }}>
                            {inst.has_active_rector ? (
                              <div>
                                <Badge variant="success">✓ Titular Activo</Badge>
                                <div style={{ fontWeight: 600, color: '#0F172A', fontSize: '0.8125rem', marginTop: '0.25rem' }}>
                                  {inst.active_rector_name || 'Rector Titular'}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: '#64748B' }}>{inst.active_rector_email}</div>
                              </div>
                            ) : inst.has_pending_invitation ? (
                              <div>
                                <Badge variant="warning">⏳ Invitación Pendiente</Badge>
                                <div style={{ fontSize: '0.75rem', color: '#B45309', marginTop: '0.25rem' }}>
                                  En espera de activación
                                </div>
                              </div>
                            ) : (
                              <div>
                                <Badge variant="neutral">⚠️ Sin Rector</Badge>
                                <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '0.25rem' }}>
                                  Titularidad vacante
                                </div>
                              </div>
                            )}
                          </td>
                          <td style={{ padding: '1rem', textAlign: 'center' }}>
                            <Badge variant={inst.is_active ? 'success' : 'danger'}>
                              {inst.is_active ? 'Activa' : 'Suspendida'}
                            </Badge>
                          </td>
                          <td style={{ padding: '1rem', textAlign: 'right' }}>
                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', alignItems: 'center' }}>
                              {canSetContext && inst.is_active && (
                                activeInstitutionId === inst.id ? (
                                  <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => {
                                      setActiveInstitutionContext(null)
                                      setSuccessMsg(`Contexto institucional removido.`)
                                    }}
                                    title="Desmarcar contexto institucional"
                                    style={{ backgroundColor: '#FEF08A', color: '#854D0E', borderColor: '#FACC15', fontWeight: 600 }}
                                  >
                                    ✓ Activo
                                  </Button>
                                ) : (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      setActiveInstitutionContext(inst.id, inst.name)
                                      setSuccessMsg(`Contexto institucional establecido en "${inst.name}". Ahora puede acceder a Gestión Académica y Aulas Virtuales para esta institución.`)
                                    }}
                                    title="Seleccionar esta institución como contexto de trabajo para inspección"
                                  >
                                    🏛️ Contexto
                                  </Button>
                                )
                              )}
                              {canManageRectors && inst.is_active && (
                                <>
                                  {!inst.has_active_rector && !inst.has_pending_invitation && (
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
                                  {inst.has_pending_invitation && !inst.has_active_rector && (
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      disabled={isInviting}
                                      onClick={() => void handleResendInvite(inst)}
                                      title="Reenviar enlace de activación al Rector pendiente"
                                      style={{ color: '#D97706', borderColor: '#FDE68A' }}
                                    >
                                      🔄 Reenviar
                                    </Button>
                                  )}
                                  {inst.has_active_rector && (
                                    <span
                                      style={{
                                        fontSize: '0.75rem',
                                        fontWeight: 600,
                                        color: '#16A34A',
                                        padding: '0.25rem 0.5rem',
                                        backgroundColor: '#DCFCE7',
                                        borderRadius: '4px',
                                      }}
                                      title="La institución ya cuenta con un Rector titular activo"
                                    >
                                      ✓ Titular Asignado
                                    </span>
                                  )}
                                </>
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
        </>
      )}

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
            🔒 <strong>Principio de Seguridad Cero-Contraseña:</strong> Como operador administrativo, usted <strong>NO</strong> define la clave del Rector. Se generará un enlace tokenizado de un solo uso con vigencia de 48 horas mediante el cual el Rector definirá su clave secreta con cifrado Argon2id.
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
          {/* Status Feedback */}
          {generatedInvitation?.email_delivery_status === 'EMAIL_SENT' && (
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
              ✅ <strong>Rector invitado correctamente:</strong> La invitación fue enviada al correo institucional.
            </div>
          )}

          {(!generatedInvitation?.email_delivery_status || generatedInvitation?.email_delivery_status === 'EMAIL_NOT_CONFIGURED') && (
            <div
              style={{
                backgroundColor: '#EFF6FF',
                border: '1px solid #93C5FD',
                borderRadius: '8px',
                padding: '1rem',
                color: '#1E40AF',
                fontSize: '0.875rem',
              }}
            >
              ℹ️ <strong>Rector aprovisionado correctamente:</strong> El correo electrónico no está configurado todavía. La invitación segura fue generada y es válida durante 48 horas.
            </div>
          )}

          {generatedInvitation?.email_delivery_status === 'EMAIL_SEND_FAILED' && (
            <div
              style={{
                backgroundColor: '#FEF2F2',
                border: '1px solid #FECACA',
                borderRadius: '8px',
                padding: '1rem',
                color: '#991B1B',
                fontSize: '0.875rem',
              }}
            >
              ⚠️ <strong>Rector aprovisionado correctamente:</strong> No fue posible enviar el correo electrónico.
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
              Enlace de activación:
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                readOnly
                value={getAbsoluteInvitationUrl(generatedInvitation)}
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
                {copiedLink ? '¡Copiado! ✓' : 'Copiar enlace'}
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

      {/* ===================================================================== */}
      {/* 5. Modal de Aprovisionamiento desde Catálogo Oficial Ministerial      */}
      {/* ===================================================================== */}
      <Modal
        isOpen={provisionModal.isOpen}
        onClose={() => setProvisionModal((prev) => ({ ...prev, isOpen: false }))}
        title="Aprovisionar Establecimiento Educativo Oficial"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {provisionModal.error && <Alert variant="error">{provisionModal.error}</Alert>}

          <div
            style={{
              backgroundColor: '#EFF6FF',
              border: '1px solid #BFDBFE',
              borderRadius: '8px',
              padding: '1rem',
              fontSize: '0.875rem',
              color: '#1E40AF',
            }}
          >
            🏛️ <strong>Aprovisionamiento Territorial Oficial:</strong> Este proceso registrará el establecimiento oficial en la base de datos de PEVN como un tenant operacional completo, incorporando automáticamente todas sus sedes oficiales registradas ante el MEN/DANE.
          </div>

          <div
            style={{
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              borderRadius: '8px',
              padding: '1rem',
              fontSize: '0.8125rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
            }}
          >
            <div><strong>Código DANE Institucional:</strong> <span style={{ fontFamily: 'monospace', fontWeight: 700 }}>{provisionModal.item?.dane_code}</span></div>
            <div><strong>Nombre Oficial:</strong> {provisionModal.item?.name}</div>
            <div><strong>Municipio / Departamento:</strong> {provisionModal.item?.municipality_name} ({provisionModal.item?.municipality_code}), {provisionModal.item?.department_name}</div>
            <div><strong>Sedes Oficiales a Registrar:</strong> <span style={{ fontWeight: 700, color: '#2563EB' }}>{provisionModal.item?.campus_count} sedes (Sede Principal + {Math.max(0, (provisionModal.item?.campus_count || 1) - 1)} anexas)</span></div>
            <div><strong>Sector:</strong> {provisionModal.item?.sector || 'OFICIAL'}</div>
            {provisionModal.item?.official_address && (
              <div><strong>Dirección Oficial:</strong> {provisionModal.item.official_address}</div>
            )}
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
              Correo Electrónico Institucional de Contacto *
            </label>
            <input
              type="email"
              value={provisionModal.email}
              onChange={(e) => setProvisionModal({ ...provisionModal, email: e.target.value })}
              required
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
              Teléfono de Contacto (Opcional)
            </label>
            <input
              type="text"
              value={provisionModal.phone}
              onChange={(e) => setProvisionModal({ ...provisionModal, phone: e.target.value })}
              placeholder="+57 8 555 1234"
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setProvisionModal((prev) => ({ ...prev, isOpen: false }))}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              variant="primary"
              disabled={provisionModal.isSubmitting || !provisionModal.email.trim()}
              onClick={handleConfirmCatalogProvision}
            >
              {provisionModal.isSubmitting ? 'Aprovisionando...' : '⚡ Confirmar Aprovisionamiento'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default InstitutionsView
