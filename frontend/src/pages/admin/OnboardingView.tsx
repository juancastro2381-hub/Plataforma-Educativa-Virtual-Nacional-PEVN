/**
 * PEVN Frontend — National Provisioning & Onboarding Workflow View (NTA-04)
 *
 * Professional SaaS administration interface for National and Departmental Administrators.
 * Features:
 *   1. Catalog Explorer: Official educational catalog with real-time PEVN status
 *      (AVAILABLE / INCORPORABLE, EN TRÁMITE, OPERACIONAL EN PEVN).
 *      Strict territorial locking for DEPARTMENT_ADMIN.
 *   2. Onboarding Filing Modal: Read-only catalog details card + operational tenant setup.
 *   3. Approval Queue: State machine management (SUBMITTED -> UNDER_REVIEW -> APPROVED -> PROVISIONED / REJECTED / CANCELLED).
 *   4. Atomic Provisioning Execution: One-click tenant, campus, and rector invitation materialization.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Modal } from '@/components/ui/Modal'
import { useAuth } from '@/hooks/useAuth'
import { departmentAdminApi } from '@/services/departmentAdmin'
import { onboardingApi } from '@/services/onboarding'
import type { DepartmentOption } from '@/types'
import type {
  CatalogExplorerItem,
  OnboardingProvisionResult,
  OnboardingRequestCreatePayload,
  OnboardingRequestDetail,
  OnboardingRequestStatus,
} from '@/types/onboarding'

export const OnboardingView: React.FC = () => {
  const { user, hasRole } = useAuth()

  const isNational = hasRole('superadmin') || hasRole('national_admin')
  const isDepartmentAdmin = hasRole('department_admin') && !isNational

  // User's department scope for Department Admin
  const userDepartmentId = user?.scope?.department_id || null

  // Active top-level view tab
  const [activeTab, setActiveTab] = useState<'catalog' | 'queue'>('catalog')

  // Territorial departments catalog
  const [departments, setDepartments] = useState<DepartmentOption[]>([])

  // ---------------------------------------------------------------------------
  // 1. Catalog Explorer State
  // ---------------------------------------------------------------------------
  const [catalogItems, setCatalogItems] = useState<CatalogExplorerItem[]>([])
  const [catalogTotal, setCatalogTotal] = useState<number>(0)
  const [catalogPage, setCatalogPage] = useState<number>(1)
  const [catalogPageSize] = useState<number>(15)
  const [catalogLoading, setCatalogLoading] = useState<boolean>(false)
  const [catalogSearch, setCatalogSearch] = useState<string>('')
  const [selectedDeptFilter, setSelectedDeptFilter] = useState<string>(
    isDepartmentAdmin && userDepartmentId ? userDepartmentId : ''
  )
  const [catalogStatusFilter, setCatalogStatusFilter] = useState<string>('')

  // ---------------------------------------------------------------------------
  // 2. Queue State
  // ---------------------------------------------------------------------------
  const [queueItems, setQueueItems] = useState<OnboardingRequestDetail[]>([])
  const [queueTotal, setQueueTotal] = useState<number>(0)
  const [queuePage, setQueuePage] = useState<number>(1)
  const [queuePageSize] = useState<number>(15)
  const [queueLoading, setQueueLoading] = useState<boolean>(false)
  const [queueStatusTab, setQueueStatusTab] = useState<string>('ALL')
  const [queueSearch, setQueueSearch] = useState<string>('')

  // Global alerts
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // ---------------------------------------------------------------------------
  // 3. Filing Modal State
  // ---------------------------------------------------------------------------
  const [isFilingModalOpen, setIsFilingModalOpen] = useState<boolean>(false)
  const [selectedCatalogItem, setSelectedCatalogItem] = useState<CatalogExplorerItem | null>(null)
  const [isSubmittingFiling, setIsSubmittingFiling] = useState<boolean>(false)
  const [filingForm, setFilingForm] = useState<OnboardingRequestCreatePayload>({
    catalog_institution_id: '',
    contact_email: '',
    contact_phone: '',
    proposed_rector_name: '',
    proposed_rector_email: '',
    proposed_rector_doc_type: 'CC',
    proposed_rector_doc_num: '',
    justification: '',
    is_draft: false,
  })
  const [filingError, setFilingError] = useState<string | null>(null)

  // ---------------------------------------------------------------------------
  // 4. Action Modals State (Review, Reject, Provision Result)
  // ---------------------------------------------------------------------------
  const [rejectModal, setRejectModal] = useState<{
    isOpen: boolean
    request: OnboardingRequestDetail | null
    reason: string
    isSubmitting: boolean
    error: string | null
  }>({
    isOpen: false,
    request: null,
    reason: '',
    isSubmitting: false,
    error: null,
  })

  const [provisionResultModal, setProvisionResultModal] = useState<{
    isOpen: boolean
    result: OnboardingProvisionResult | null
    copiedToken: boolean
  }>({
    isOpen: false,
    result: null,
    copiedToken: false,
  })

  const [isActionLoading, setIsActionLoading] = useState<boolean>(false)

  // ---------------------------------------------------------------------------
  // Data Fetching: Departments
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const depts = await departmentAdminApi.listDepartments()
        setDepartments(depts)
        if (isDepartmentAdmin && userDepartmentId) {
          setSelectedDeptFilter(userDepartmentId)
        }
      } catch (err: any) {
        console.error('Error fetching departments:', err)
      }
    }
    fetchDepartments()
  }, [isDepartmentAdmin, userDepartmentId])

  // ---------------------------------------------------------------------------
  // Data Fetching: Catalog Explorer
  // ---------------------------------------------------------------------------
  const fetchCatalog = useCallback(async () => {
    setCatalogLoading(true)
    setErrorMsg(null)
    try {
      const response = await onboardingApi.exploreCatalog({
        name: catalogSearch || undefined,
        department_id: isDepartmentAdmin ? userDepartmentId || undefined : (selectedDeptFilter || undefined),
        onboarding_status: catalogStatusFilter || undefined,
        page: catalogPage,
        page_size: catalogPageSize,
      })
      setCatalogItems(response.items)
      setCatalogTotal(response.total)
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al consultar el catálogo de establecimientos.')
    } finally {
      setCatalogLoading(false)
    }
  }, [catalogSearch, selectedDeptFilter, catalogStatusFilter, catalogPage, catalogPageSize, isDepartmentAdmin, userDepartmentId])

  useEffect(() => {
    if (activeTab === 'catalog') {
      fetchCatalog()
    }
  }, [activeTab, fetchCatalog])

  // ---------------------------------------------------------------------------
  // Data Fetching: Approval Queue
  // ---------------------------------------------------------------------------
  const fetchQueue = useCallback(async () => {
    setQueueLoading(true)
    setErrorMsg(null)
    try {
      const statusParam = queueStatusTab === 'ALL' ? undefined : queueStatusTab
      const response = await onboardingApi.listRequests({
        status: statusParam,
        department_id: isDepartmentAdmin ? userDepartmentId || undefined : undefined,
        search: queueSearch || undefined,
        page: queuePage,
        page_size: queuePageSize,
      })
      setQueueItems(response.items)
      setQueueTotal(response.total)
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al consultar la cola de solicitudes.')
    } finally {
      setQueueLoading(false)
    }
  }, [queueStatusTab, queueSearch, queuePage, queuePageSize, isDepartmentAdmin, userDepartmentId])

  useEffect(() => {
    if (activeTab === 'queue') {
      fetchQueue()
    }
  }, [activeTab, fetchQueue])

  // ---------------------------------------------------------------------------
  // Filing Modal Handlers
  // ---------------------------------------------------------------------------
  const openFilingModal = (item: CatalogExplorerItem) => {
    setSelectedCatalogItem(item)
    setFilingForm({
      catalog_institution_id: item.id,
      contact_email: '',
      contact_phone: '',
      proposed_rector_name: '',
      proposed_rector_email: '',
      proposed_rector_doc_type: 'CC',
      proposed_rector_doc_num: '',
      justification: '',
      is_draft: false,
    })
    setFilingError(null)
    setIsFilingModalOpen(true)
  }

  const handleFilingSubmit = async (asDraft: boolean) => {
    if (!selectedCatalogItem) return
    if (!filingForm.contact_email.trim()) {
      setFilingError('El correo institucional oficial es obligatorio.')
      return
    }

    setIsSubmittingFiling(true)
    setFilingError(null)
    try {
      const payload: OnboardingRequestCreatePayload = {
        ...filingForm,
        catalog_institution_id: selectedCatalogItem.id,
        is_draft: asDraft,
      }
      const result = await onboardingApi.createRequest(payload)
      setSuccessMsg(
        `Solicitud ${asDraft ? 'guardada como borrador' : 'radicada exitosamente'} con código ${result.request_number}.`
      )
      setIsFilingModalOpen(false)
      fetchCatalog()
    } catch (err: any) {
      setFilingError(err.message || 'Error al radicar la solicitud de incorporación.')
    } finally {
      setIsSubmittingFiling(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Queue Action Handlers
  // ---------------------------------------------------------------------------
  const handleStartReview = async (req: OnboardingRequestDetail) => {
    setIsActionLoading(true)
    setErrorMsg(null)
    try {
      await onboardingApi.startReview(req.id)
      setSuccessMsg(`Revisión técnica iniciada para solicitud ${req.request_number}.`)
      fetchQueue()
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al iniciar la revisión.')
    } finally {
      setIsActionLoading(false)
    }
  }

  const handleApprove = async (req: OnboardingRequestDetail) => {
    setIsActionLoading(true)
    setErrorMsg(null)
    try {
      await onboardingApi.approveRequest(req.id)
      setSuccessMsg(`Solicitud ${req.request_number} aprobada formalmente. Lista para aprovisionar.`)
      fetchQueue()
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al aprobar la solicitud.')
    } finally {
      setIsActionLoading(false)
    }
  }

  const handleOpenReject = (req: OnboardingRequestDetail) => {
    setRejectModal({
      isOpen: true,
      request: req,
      reason: '',
      isSubmitting: false,
      error: null,
    })
  }

  const handleConfirmReject = async () => {
    if (!rejectModal.request) return
    if (rejectModal.reason.trim().length < 10) {
      setRejectModal((prev) => ({
        ...prev,
        error: 'El motivo formal de rechazo debe contener al menos 10 caracteres explicativos.',
      }))
      return
    }

    setRejectModal((prev) => ({ ...prev, isSubmitting: true, error: null }))
    try {
      await onboardingApi.rejectRequest(rejectModal.request.id, {
        rejection_reason: rejectModal.reason.trim(),
      })
      setSuccessMsg(`Solicitud ${rejectModal.request.request_number} rechazada formalmente.`)
      setRejectModal({ isOpen: false, request: null, reason: '', isSubmitting: false, error: null })
      fetchQueue()
    } catch (err: any) {
      setRejectModal((prev) => ({
        ...prev,
        isSubmitting: false,
        error: err.message || 'Error al registrar el rechazo de la solicitud.',
      }))
    }
  }

  const handleProvision = async (req: OnboardingRequestDetail) => {
    if (!confirm(`¿Confirma el aprovisionamiento operacional del colegio '${req.institution_name}' en PEVN?`)) {
      return
    }

    setIsActionLoading(true)
    setErrorMsg(null)
    try {
      const result = await onboardingApi.provisionRequest(req.id)
      setProvisionResultModal({
        isOpen: true,
        result,
        copiedToken: false,
      })
      setSuccessMsg(`¡Colegio '${result.institution_name}' aprovisionado exitosamente en PEVN!`)
      fetchQueue()
    } catch (err: any) {
      setErrorMsg(err.message || 'Error durante el aprovisionamiento del colegio.')
    } finally {
      setIsActionLoading(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Helper: Status Badges
  // ---------------------------------------------------------------------------
  const renderCatalogBadge = (status: string, item: CatalogExplorerItem) => {
    switch (status) {
      case 'PROVISIONED':
        return (
          <Badge variant="info">
            OPERACIONAL EN PEVN
          </Badge>
        )
      case 'EN_TRAMITE':
        return (
          <Badge variant="warning">
            EN TRÁMITE {item.active_request_number ? `(${item.active_request_number})` : ''}
          </Badge>
        )
      case 'AVAILABLE':
      default:
        return (
          <Badge variant="success">
            INCORPORABLE
          </Badge>
        )
    }
  }

  const renderQueueBadge = (status: OnboardingRequestStatus) => {
    switch (status) {
      case 'DRAFT':
        return <Badge variant="neutral">BORRADOR</Badge>
      case 'SUBMITTED':
        return <Badge variant="warning">RADICADA</Badge>
      case 'UNDER_REVIEW':
        return <Badge variant="primary">EN REVISIÓN</Badge>
      case 'APPROVED':
        return <Badge variant="success">APROBADA</Badge>
      case 'PROVISIONED':
        return <Badge variant="info">APROVISIONADA</Badge>
      case 'REJECTED':
        return <Badge variant="danger">RECHAZADA</Badge>
      case 'CANCELLED':
        return <Badge variant="neutral">CANCELADA</Badge>
      default:
        return <Badge variant="neutral">{status}</Badge>
    }
  }

  return (
    <div className="space-y-6 p-4 sm:p-6 max-w-7xl mx-auto">
      {/* Top Banner (Institutional Header with WCAG 2.2 AAA Contrast) */}
      <div
        style={{
          backgroundColor: '#0F172A',
          color: '#FFFFFF',
          borderRadius: '16px',
          padding: '2rem',
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
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                color: '#34D399',
                border: '1px solid rgba(16, 185, 129, 0.4)',
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
              }}
            >
              NTA-04 Flujo Nacional
            </span>
            <span style={{ fontSize: '0.8125rem', color: '#CBD5E1' }}>
              {isDepartmentAdmin
                ? `Jurisdicción: ${user?.scope?.jurisdiction_name || 'Departamental'}`
                : 'Alcance Nacional (33 Departamentos)'}
            </span>
          </div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 800, margin: '0.25rem 0', color: '#FFFFFF' }}>
            Incorporación y Aprovisionamiento de Colegios
          </h1>
          <p style={{ color: '#CBD5E1', fontSize: '0.9375rem', margin: 0, maxWidth: '680px' }}>
            Transformación gobernada del catálogo oficial MEN/DANE en colegios operacionales con sedes y rectoría.
          </p>
        </div>

        {/* Top-Level Navigation Tabs */}
        <div
          style={{
            display: 'flex',
            backgroundColor: '#1E293B',
            border: '1px solid #334155',
            borderRadius: '10px',
            padding: '4px',
            gap: '4px',
          }}
        >
          <button
            onClick={() => setActiveTab('catalog')}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontWeight: 600,
              border: 'none',
              cursor: 'pointer',
              transition: 'all 150ms ease-in-out',
              backgroundColor: activeTab === 'catalog' ? '#059669' : 'transparent',
              color: activeTab === 'catalog' ? '#FFFFFF' : '#CBD5E1',
            }}
          >
            Explorador del Catálogo
          </button>
          <button
            onClick={() => setActiveTab('queue')}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontWeight: 600,
              border: 'none',
              cursor: 'pointer',
              transition: 'all 150ms ease-in-out',
              backgroundColor: activeTab === 'queue' ? '#059669' : 'transparent',
              color: activeTab === 'queue' ? '#FFFFFF' : '#CBD5E1',
            }}
          >
            Bandeja de Aprobación
          </button>
        </div>
      </div>

      {/* Global Alerts */}
      {errorMsg && (
        <Alert variant="error" onClose={() => setErrorMsg(null)}>
          {errorMsg}
        </Alert>
      )}
      {successMsg && (
        <Alert variant="success" onClose={() => setSuccessMsg(null)}>
          {successMsg}
        </Alert>
      )}

      {/* ===================================================================== */}
      {/* TAB 1: CATALOG EXPLORER                                               */}
      {/* ===================================================================== */}
      {activeTab === 'catalog' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <Card className="p-4 bg-white border border-slate-200 shadow-sm">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Buscar por Nombre o DANE</label>
                <input
                  type="text"
                  placeholder="Ej. Institución Educativa..."
                  value={catalogSearch}
                  onChange={(e) => setCatalogSearch(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:border-pevn-blue"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Departamento</label>
                <select
                  disabled={isDepartmentAdmin}
                  value={selectedDeptFilter}
                  onChange={(e) => setSelectedDeptFilter(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:border-pevn-blue disabled:bg-slate-100 disabled:text-slate-500"
                >
                  {!isDepartmentAdmin && <option value="">Todos los departamentos (33)</option>}
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.code} - {d.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Estado en PEVN</label>
                <select
                  value={catalogStatusFilter}
                  onChange={(e) => setCatalogStatusFilter(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:border-pevn-blue"
                >
                  <option value="">Todos los estados</option>
                  <option value="AVAILABLE">AVAILABLE / INCORPORABLE</option>
                  <option value="EN_TRAMITE">EN TRÁMITE</option>
                  <option value="PROVISIONED">OPERACIONAL EN PEVN</option>
                </select>
              </div>

              <div>
                <Button
                  variant="primary"
                  className="w-full font-semibold"
                  onClick={() => {
                    setCatalogPage(1)
                    fetchCatalog()
                  }}
                >
                  Filtrar Catálogo
                </Button>
              </div>
            </div>
          </Card>

          {/* Results Table */}
          <Card className="overflow-hidden border border-slate-200 bg-white shadow-sm p-0">
            {catalogLoading ? (
              <div className="py-20 flex flex-col items-center justify-center">
                <LoadingSpinner size="lg" />
                <p className="text-sm text-slate-600 mt-3 font-medium">Consultando catálogo oficial nacional...</p>
              </div>
            ) : catalogItems.length === 0 ? (
              <EmptyState
                title="No se encontraron colegios"
                description="Ajuste los filtros de búsqueda o consulte otro departamento."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-900 border-collapse">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-700 border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-4 font-bold">Establecimiento Oficial</th>
                      <th className="py-3 px-4 font-bold">Código DANE</th>
                      <th className="py-3 px-4 font-bold">Jurisdicción</th>
                      <th className="py-3 px-4 font-bold">Sedes</th>
                      <th className="py-3 px-4 font-bold">Estado en PEVN</th>
                      <th className="py-3 px-4 text-right font-bold">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {catalogItems.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="py-3.5 px-4 font-semibold text-slate-900">
                          <div>{item.name}</div>
                          <div className="text-xs text-slate-600 font-normal truncate max-w-xs mt-0.5">
                            {item.official_address || 'Sin dirección registrada'} • {item.sector || 'OFICIAL'}
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="font-mono text-xs font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                            {item.dane_code}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="text-slate-900 font-medium">{item.municipality_name}</div>
                          <div className="text-xs text-slate-600">{item.department_name}</div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="text-xs font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                            {item.campus_count} {item.campus_count === 1 ? 'sede' : 'sedes'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">{renderCatalogBadge(item.onboarding_status, item)}</td>
                        <td className="py-3.5 px-4 text-right">
                          {item.onboarding_status === 'AVAILABLE' ? (
                            <Button
                              size="sm"
                              variant="primary"
                              className="text-xs px-3 py-1.5"
                              onClick={() => openFilingModal(item)}
                            >
                              Iniciar Incorporación
                            </Button>
                          ) : item.onboarding_status === 'EN_TRAMITE' ? (
                            <Button
                              size="sm"
                              variant="secondary"
                              className="text-xs px-3 py-1.5"
                              onClick={() => {
                                setActiveTab('queue')
                                setQueueSearch(item.dane_code)
                              }}
                            >
                              Ver Trámite
                            </Button>
                          ) : (
                            <span className="text-xs text-slate-600 font-semibold inline-flex items-center gap-1">
                              ✓ Tenant Activo
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            <div className="p-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-700">
              <div>
                Total: <span className="text-slate-900 font-bold">{catalogTotal}</span> colegios en el catálogo
              </div>
              <div className="flex gap-2 items-center">
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={catalogPage <= 1}
                  onClick={() => setCatalogPage((p) => Math.max(1, p - 1))}
                >
                  Anterior
                </Button>
                <span className="px-2 py-1 text-slate-700 font-medium">Página {catalogPage}</span>
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={catalogPage * catalogPageSize >= catalogTotal}
                  onClick={() => setCatalogPage((p) => p + 1)}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 2: ONBOARDING APPROVAL QUEUE                                      */}
      {/* ===================================================================== */}
      {activeTab === 'queue' && (
        <div className="space-y-4">
          {/* Sub-tabs by status */}
          <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
            {[
              { id: 'ALL', label: 'Todas las Solicitudes' },
              { id: 'SUBMITTED', label: 'Pendientes de Revisión' },
              { id: 'UNDER_REVIEW', label: 'En Revisión' },
              { id: 'APPROVED', label: 'Aprobadas (Listas para Aprovisionar)' },
              { id: 'PROVISIONED', label: 'Aprovisionadas' },
              { id: 'REJECTED', label: 'Rechazadas' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setQueueStatusTab(tab.id)
                  setQueuePage(1)
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  queueStatusTab === tab.id
                    ? 'bg-slate-900 text-white border border-slate-800 shadow-sm'
                    : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Queue List Table */}
          <Card className="overflow-hidden border border-slate-200 bg-white shadow-sm p-0">
            {queueLoading ? (
              <div className="py-20 flex flex-col items-center justify-center">
                <LoadingSpinner size="lg" />
                <p className="text-sm text-slate-600 mt-3 font-medium">Consultando bandeja de solicitudes...</p>
              </div>
            ) : queueItems.length === 0 ? (
              <EmptyState
                title="Bandeja sin solicitudes"
                description="No existen solicitudes registradas para el filtro seleccionado."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-900 border-collapse">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-700 border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-4 font-bold">Radicado</th>
                      <th className="py-3 px-4 font-bold">Colegio Oficial</th>
                      <th className="py-3 px-4 font-bold">Territorio</th>
                      <th className="py-3 px-4 font-bold">Radicado Por</th>
                      <th className="py-3 px-4 font-bold">Estado</th>
                      <th className="py-3 px-4 text-right font-bold">Acciones de Gobernanza</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {queueItems.map((req) => (
                      <tr key={req.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="py-3.5 px-4 font-mono text-slate-900 font-bold text-xs">
                          <span className="bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">
                            {req.request_number}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-slate-900">{req.institution_name}</div>
                          <div className="text-xs text-slate-600 mt-0.5">DANE: {req.dane_code} • {req.contact_email}</div>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="text-slate-900 font-medium">{req.municipality_name}</div>
                          <div className="text-xs text-slate-600">{req.department_name}</div>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="text-slate-900 font-medium">{req.requester_name || req.requester_email}</div>
                          <div className="text-xs text-slate-600">{req.requester_role}</div>
                        </td>
                        <td className="py-3.5 px-4">{renderQueueBadge(req.status)}</td>
                        <td className="py-3.5 px-4 text-right space-x-1.5">
                          {req.status === 'SUBMITTED' && (
                            <>
                              <Button
                                size="sm"
                                variant="secondary"
                                className="text-xs px-2.5 py-1"
                                disabled={isActionLoading}
                                onClick={() => handleStartReview(req)}
                              >
                                Tomar Revisión
                              </Button>
                              <Button
                                size="sm"
                                variant="primary"
                                className="text-xs px-2.5 py-1"
                                disabled={isActionLoading}
                                onClick={() => handleApprove(req)}
                              >
                                Aprobar
                              </Button>
                              <Button
                                size="sm"
                                variant="danger"
                                className="text-xs px-2.5 py-1"
                                disabled={isActionLoading}
                                onClick={() => handleOpenReject(req)}
                              >
                                Rechazar
                              </Button>
                            </>
                          )}

                          {req.status === 'UNDER_REVIEW' && (
                            <>
                              <Button
                                size="sm"
                                variant="primary"
                                className="text-xs px-2.5 py-1"
                                disabled={isActionLoading}
                                onClick={() => handleApprove(req)}
                              >
                                Aprobar Dictamen
                              </Button>
                              <Button
                                size="sm"
                                variant="danger"
                                className="text-xs px-2.5 py-1"
                                disabled={isActionLoading}
                                onClick={() => handleOpenReject(req)}
                              >
                                Rechazar
                              </Button>
                            </>
                          )}

                          {req.status === 'APPROVED' && (
                            <Button
                              size="sm"
                              variant="primary"
                              className="text-xs px-3 py-1 font-bold"
                              disabled={isActionLoading}
                              onClick={() => handleProvision(req)}
                            >
                              Aprovisionar Ahora
                            </Button>
                          )}

                          {req.status === 'PROVISIONED' && (
                            <span className="text-xs text-emerald-800 font-bold inline-flex items-center gap-1">
                              ✓ Tenant Activo
                            </span>
                          )}

                          {req.status === 'REJECTED' && (
                            <span className="text-xs text-red-800 font-medium" title={req.rejection_reason || ''}>
                              Causal: {req.rejection_reason?.substring(0, 25)}...
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            <div className="p-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-700">
              <div>
                Total: <span className="text-slate-900 font-bold">{queueTotal}</span> solicitudes en cola
              </div>
              <div className="flex gap-2 items-center">
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={queuePage <= 1}
                  onClick={() => setQueuePage((p) => Math.max(1, p - 1))}
                >
                  Anterior
                </Button>
                <span className="px-2 py-1 text-slate-700 font-medium">Página {queuePage}</span>
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={queuePage * queuePageSize >= queueTotal}
                  onClick={() => setQueuePage((p) => p + 1)}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL 1: FILING ONBOARDING REQUEST                                    */}
      {/* ===================================================================== */}
      {isFilingModalOpen && selectedCatalogItem && (
        <Modal
          isOpen={isFilingModalOpen}
          onClose={() => setIsFilingModalOpen(false)}
          title="Radicar Solicitud de Incorporación Institucional"
          maxWidth="lg"
        >
          <div className="space-y-4">
            {filingError && <Alert variant="error">{filingError}</Alert>}

            {/* Catalog Info Card (Read-Only) */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs font-mono font-bold text-slate-800 bg-slate-200/80 px-2 py-0.5 rounded border border-slate-300">
                    DANE: {selectedCatalogItem.dane_code}
                  </span>
                  <h3 className="text-base font-bold text-slate-900 mt-1">{selectedCatalogItem.name}</h3>
                </div>
                <Badge variant="info">{selectedCatalogItem.sector || 'OFICIAL'}</Badge>
              </div>
              <div className="text-xs text-slate-700 grid grid-cols-2 gap-2 pt-2 border-t border-slate-200">
                <div>
                  <span className="text-slate-500 font-medium">Departamento:</span> <strong className="text-slate-900">{selectedCatalogItem.department_name}</strong>
                </div>
                <div>
                  <span className="text-slate-500 font-medium">Municipio:</span> <strong className="text-slate-900">{selectedCatalogItem.municipality_name}</strong>
                </div>
                <div>
                  <span className="text-slate-500 font-medium">Dirección:</span> <strong className="text-slate-900">{selectedCatalogItem.official_address || 'N/A'}</strong>
                </div>
                <div>
                  <span className="text-slate-500 font-medium">Sedes Registradas:</span> <strong className="text-slate-900">{selectedCatalogItem.campus_count}</strong>
                </div>
              </div>
            </div>

            {/* Operational Form */}
            <div className="space-y-3">
              <h4 className="text-xs uppercase tracking-wider font-bold text-slate-700">
                Datos Operacionales para PEVN
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Correo Institucional Oficial <span className="text-red-600 font-bold">*</span>
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="rectoria@colegio.edu.co"
                    value={filingForm.contact_email}
                    onChange={(e) => setFilingForm({ ...filingForm, contact_email: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:border-pevn-blue"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Teléfono Institucional</label>
                  <input
                    type="tel"
                    placeholder="(601) 3456789"
                    value={filingForm.contact_phone || ''}
                    onChange={(e) => setFilingForm({ ...filingForm, contact_phone: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:border-pevn-blue"
                  />
                </div>
              </div>

              {/* Proposed Rector Section */}
              <div className="border-t border-slate-200 pt-3 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs uppercase tracking-wider font-bold text-slate-700">
                    Designación de Rector Inicial (Opcional)
                  </h4>
                  <span className="text-xs text-slate-500 font-medium">Emite invitación criptográfica al aprovisionar</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Nombre Completo del Rector</label>
                    <input
                      type="text"
                      placeholder="Ej. Gabriel García Márquez"
                      value={filingForm.proposed_rector_name || ''}
                      onChange={(e) => setFilingForm({ ...filingForm, proposed_rector_name: e.target.value })}
                      className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:border-pevn-blue"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Correo Electrónico del Rector</label>
                    <input
                      type="email"
                      placeholder="rector@gmail.com"
                      value={filingForm.proposed_rector_email || ''}
                      onChange={(e) => setFilingForm({ ...filingForm, proposed_rector_email: e.target.value })}
                      className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:border-pevn-blue"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Tipo de Documento</label>
                    <select
                      value={filingForm.proposed_rector_doc_type || 'CC'}
                      onChange={(e) => setFilingForm({ ...filingForm, proposed_rector_doc_type: e.target.value })}
                      className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:border-pevn-blue"
                    >
                      <option value="CC">Cédula de Ciudadanía (CC)</option>
                      <option value="CE">Cédula de Extranjería (CE)</option>
                      <option value="PASSPORT">Pasaporte</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Número de Documento</label>
                    <input
                      type="text"
                      placeholder="12345678"
                      value={filingForm.proposed_rector_doc_num || ''}
                      onChange={(e) => setFilingForm({ ...filingForm, proposed_rector_doc_num: e.target.value })}
                      className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:border-pevn-blue"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Justificación Administrativa</label>
                <textarea
                  rows={2}
                  placeholder="Motivo del requerimiento de incorporación territorial..."
                  value={filingForm.justification || ''}
                  onChange={(e) => setFilingForm({ ...filingForm, justification: e.target.value })}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:border-pevn-blue"
                />
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex justify-end gap-2 pt-4 border-t border-slate-200">
              <Button
                variant="secondary"
                disabled={isSubmittingFiling}
                onClick={() => setIsFilingModalOpen(false)}
              >
                Cancelar
              </Button>
              <Button
                variant="secondary"
                disabled={isSubmittingFiling}
                onClick={() => handleFilingSubmit(true)}
              >
                Guardar Borrador
              </Button>
              <Button
                variant="primary"
                disabled={isSubmittingFiling}
                onClick={() => handleFilingSubmit(false)}
              >
                {isSubmittingFiling ? <LoadingSpinner size="sm" /> : 'Radicar Solicitud Oficial'}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ===================================================================== */}
      {/* MODAL 2: REJECT REASON                                                */}
      {/* ===================================================================== */}
      {rejectModal.isOpen && (
        <Modal
          isOpen={rejectModal.isOpen}
          onClose={() => setRejectModal({ isOpen: false, request: null, reason: '', isSubmitting: false, error: null })}
          title="Rechazar Solicitud de Incorporación"
          maxWidth="md"
        >
          <div className="space-y-4">
            <p className="text-sm text-slate-700">
              Indique la causal formal y fundamentada para el rechazo administrativo de la solicitud{' '}
              <span className="font-mono text-slate-900 font-bold bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded">
                {rejectModal.request?.request_number}
              </span>:
            </p>

            {rejectModal.error && <Alert variant="error">{rejectModal.error}</Alert>}

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Motivo Formal de Rechazo (Mínimo 10 caracteres) <span className="text-red-600 font-bold">*</span>
              </label>
              <textarea
                rows={3}
                required
                value={rejectModal.reason}
                onChange={(e) => setRejectModal({ ...rejectModal, reason: e.target.value })}
                placeholder="Explique el motivo del rechazo técnico o administrativo..."
                className="w-full bg-white border border-slate-300 rounded-lg p-3 text-sm text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-pevn-red focus:border-pevn-red"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
              <Button
                variant="secondary"
                disabled={rejectModal.isSubmitting}
                onClick={() => setRejectModal({ isOpen: false, request: null, reason: '', isSubmitting: false, error: null })}
              >
                Cancelar
              </Button>
              <Button
                variant="danger"
                disabled={rejectModal.isSubmitting}
                onClick={handleConfirmReject}
              >
                {rejectModal.isSubmitting ? <LoadingSpinner size="sm" /> : 'Confirmar Rechazo'}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ===================================================================== */}
      {/* MODAL 3: PROVISION SUCCESS RESULT                                     */}
      {/* ===================================================================== */}
      {provisionResultModal.isOpen && provisionResultModal.result && (
        <Modal
          isOpen={provisionResultModal.isOpen}
          onClose={() => setProvisionResultModal({ isOpen: false, result: null, copiedToken: false })}
          title="¡Tenant Institucional Aprovisionado Exitosamente!"
          maxWidth="md"
        >
          <div className="space-y-4">
            <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-200 text-center space-y-1">
              <div className="text-xs font-mono uppercase tracking-wider text-emerald-800 font-bold">
                Operacional en PEVN
              </div>
              <h3 className="text-lg font-black text-slate-900">{provisionResultModal.result.institution_name}</h3>
              <p className="text-xs text-slate-700 font-mono">DANE: {provisionResultModal.result.dane_code}</p>
              <p className="text-xs text-emerald-800 font-semibold">
                {provisionResultModal.result.campuses_created} sedes educativas materializadas
              </p>
            </div>

            {provisionResultModal.result.rector_invited ? (
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase font-bold text-slate-700">Invitación de Rector Generada</span>
                  <Badge variant="success">Token Seguro SHA-256</Badge>
                </div>
                <p className="text-xs text-slate-600">
                  Se ha generado un token criptográfico de un solo uso para que el Rector defina sus credenciales.
                </p>
                {provisionResultModal.result.raw_invitation_token && (
                  <div className="flex items-center gap-2 pt-2">
                    <input
                      type="text"
                      readOnly
                      value={provisionResultModal.result.raw_invitation_token}
                      className="bg-white border border-slate-300 rounded px-2.5 py-1 text-xs font-mono text-slate-900 font-bold flex-1 truncate"
                    />
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => {
                        if (provisionResultModal.result?.raw_invitation_token) {
                          navigator.clipboard.writeText(provisionResultModal.result.raw_invitation_token)
                          setProvisionResultModal((prev) => ({ ...prev, copiedToken: true }))
                        }
                      }}
                    >
                      {provisionResultModal.copiedToken ? 'Copiado' : 'Copiar Token'}
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-amber-50 p-3 rounded-lg border border-amber-200 text-xs text-amber-900">
                <strong className="text-amber-950">Rectoría Pendiente:</strong> El colegio fue aprovisionado sin rector asignado. Puede invitar al rector posteriormente desde el módulo de instituciones.
              </div>
            )}

            <div className="flex justify-end pt-2 border-t border-slate-200">
              <Button
                variant="primary"
                onClick={() => setProvisionResultModal({ isOpen: false, result: null, copiedToken: false })}
              >
                Entendido
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
