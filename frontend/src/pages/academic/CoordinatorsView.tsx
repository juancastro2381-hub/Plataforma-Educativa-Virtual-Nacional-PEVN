/**
 * PEVN Frontend — Academic Coordinators Management View
 *
 * Authoritative institutional management screen for Rectors:
 *   - Lists coordinators assigned to the institution with campus scope
 *   - Displays active account and invitation status (pending, accepted, expired)
 *   - Allows inviting new coordinators (institution-wide or campus-specific)
 *   - Re-sending/regenerating 48-hour invitation links
 *   - Suspending or activating accounts with session invalidation
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
import { coordinatorApi } from '@/services/coordinator'
import { resolveInvitationUrl } from '@/utils'
import type {
  CoordinatorCampusOption,
  CoordinatorCreateRequest,
  CoordinatorResponse,
} from '@/types'

interface InvitationOutcomeModalState {
  isOpen: boolean
  coordinatorName: string
  email: string
  campusName: string | null
  invitationUrl: string | null
  deliveryStatus: string | null
  copied: boolean
}

export const CoordinatorsView: React.FC = () => {
  const { hasRole, hasPermission } = useAuth()

  const isRector = hasRole(['rector', 'institution_admin'])
  const isSuper = hasRole(['superadmin', 'super_admin'])
  const canCreate = hasPermission('coordinators:create') || isRector || isSuper
  const canUpdate = hasPermission('coordinators:update') || isRector || isSuper

  // State
  const [coordinators, setCoordinators] = useState<CoordinatorResponse[]>([])
  const [campuses, setCampuses] = useState<CoordinatorCampusOption[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Filters
  const [search, setSearch] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive' | 'pending'>('all')

  // Create Modal
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [createForm, setCreateForm] = useState<CoordinatorCreateRequest>({
    first_name: '',
    last_name: '',
    document_type: 'CC',
    document_number: '',
    email: '',
    campus_id: null,
  })
  const [scopeType, setScopeType] = useState<'institution' | 'campus'>('institution')

  // Outcome Modal
  const [outcomeModal, setOutcomeModal] = useState<InvitationOutcomeModalState>({
    isOpen: false,
    coordinatorName: '',
    email: '',
    campusName: null,
    invitationUrl: null,
    deliveryStatus: null,
    copied: false,
  })

  // Status Action Modal
  const [statusModal, setStatusModal] = useState<{
    isOpen: boolean
    target: CoordinatorResponse | null
    isActivating: boolean
    reason: string
    isSubmitting: boolean
  }>({
    isOpen: false,
    target: null,
    isActivating: false,
    reason: '',
    isSubmitting: false,
  })

  // Resend State
  const [resendingId, setResendingId] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const filterActive = statusFilter === 'active' ? true : statusFilter === 'inactive' ? false : undefined
      const [listRes, campusList] = await Promise.all([
        coordinatorApi.listCoordinators({
          is_active: filterActive,
          search: search.trim() || undefined,
        }),
        coordinatorApi.listCampuses().catch(() => []),
      ])
      setCoordinators(listRes.items)
      setCampuses(campusList)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cargar la lista de coordinadores.')
    } finally {
      setIsLoading(false)
    }
  }, [search, statusFilter])

  useEffect(() => {
    void loadData()
  }, [loadData])

  // NTA-10-R10 Exclusivity Policy Evaluation
  const effectiveCoordinators = coordinators.filter(
    c => c.is_active || c.invitation_status === 'pending'
  )
  const effectiveGlobalCoord = effectiveCoordinators.find(c => c.campus_id === null)
  const hasEffectiveGlobal = !!effectiveGlobalCoord
  const effectiveCampusCoords = effectiveCoordinators.filter(c => c.campus_id !== null)
  const hasEffectiveCampus = effectiveCampusCoords.length > 0

  const occupiedCampusMap = new Map<string, string>()
  effectiveCampusCoords.forEach(c => {
    if (c.campus_id) {
      occupiedCampusMap.set(c.campus_id, c.full_name)
    }
  })

  const handleOpenCreate = () => {
    setCreateForm({
      first_name: '',
      last_name: '',
      document_type: 'CC',
      document_number: '',
      email: '',
      campus_id: null,
    })
    // If campus coordinators already exist, default to campus scope since global scope is prohibited
    if (hasEffectiveCampus) {
      setScopeType('campus')
    } else {
      setScopeType('institution')
    }
    setCreateError(null)
    setIsCreateOpen(true)
  }

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreateError(null)

    if (!createForm.first_name.trim() || !createForm.last_name.trim()) {
      setCreateError('Por favor complete los nombres y apellidos del coordinador.')
      return
    }
    if (!createForm.email.trim()) {
      setCreateError('Por favor ingrese el correo electrónico institucional.')
      return
    }
    if (!createForm.document_number.trim()) {
      setCreateError('Por favor ingrese el número de documento de identidad.')
      return
    }

    const payload: CoordinatorCreateRequest = {
      ...createForm,
      first_name: createForm.first_name.trim(),
      last_name: createForm.last_name.trim(),
      email: createForm.email.trim().toLowerCase(),
      document_number: createForm.document_number.trim(),
      campus_id: scopeType === 'campus' && createForm.campus_id ? createForm.campus_id : null,
    }

    setIsSubmitting(true)
    try {
      const created = await coordinatorApi.createCoordinator(payload)
      setIsCreateOpen(false)
      setSuccessMsg(`Invitación emitida exitosamente para ${created.full_name}.`)

      const resolvedUrl = resolveInvitationUrl(created.invitation_url, created.raw_invitation_token)

      setOutcomeModal({
        isOpen: true,
        coordinatorName: created.full_name,
        email: created.email,
        campusName: created.campus_name || 'Institución Completa',
        invitationUrl: resolvedUrl,
        deliveryStatus: created.email_delivery_status || 'EMAIL_NOT_CONFIGURED',
        copied: false,
      })

      void loadData()
    } catch (err: unknown) {
      setCreateError(err instanceof Error ? err.message : 'Error al aprovisionar el coordinador.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleResend = async (coord: CoordinatorResponse) => {
    setResendingId(coord.id)
    setError(null)
    setSuccessMsg(null)
    try {
      const res = await coordinatorApi.resendInvitation(coord.id)
      setSuccessMsg(`Nueva invitación generada para ${coord.full_name}.`)

      const resolvedUrl = resolveInvitationUrl(res.invitation_url, res.raw_invitation_token)

      setOutcomeModal({
        isOpen: true,
        coordinatorName: coord.full_name,
        email: coord.email,
        campusName: coord.campus_name || 'Institución Completa',
        invitationUrl: resolvedUrl,
        deliveryStatus: res.email_delivery_status,
        copied: false,
      })
      void loadData()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al reenviar la invitación.')
    } finally {
      setResendingId(null)
    }
  }

  const handleOpenStatusModal = (coord: CoordinatorResponse) => {
    setStatusModal({
      isOpen: true,
      target: coord,
      isActivating: !coord.is_active,
      reason: '',
      isSubmitting: false,
    })
  }

  const handleStatusSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!statusModal.target) return

    setStatusModal(prev => ({ ...prev, isSubmitting: true }))
    try {
      await coordinatorApi.updateCoordinatorStatus(
        statusModal.target.id,
        statusModal.isActivating,
        statusModal.reason.trim() || undefined
      )
      setSuccessMsg(
        `El coordinador ${statusModal.target.full_name} ha sido ${statusModal.isActivating ? 'activado' : 'suspendido'} exitosamente.`
      )
      setStatusModal(prev => ({ ...prev, isOpen: false }))
      void loadData()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al modificar el estado del coordinador.')
    } finally {
      setStatusModal(prev => ({ ...prev, isSubmitting: false }))
    }
  }

  const handleCopyLink = () => {
    if (outcomeModal.invitationUrl) {
      void navigator.clipboard.writeText(outcomeModal.invitationUrl)
      setOutcomeModal(prev => ({ ...prev, copied: true }))
      setTimeout(() => {
        setOutcomeModal(prev => ({ ...prev, copied: false }))
      }, 3000)
    }
  }

  return (
    <div style={{ padding: '0.5rem 0' }}>
      {/* Header Bar */}
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
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
            Coordinación Académica e Institucional
          </h2>
          <p style={{ color: '#64748B', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Aprovisionamiento, asignación por sedes educativas y gestión del ciclo de vida de Coordinadores.
          </p>
        </div>
        {canCreate && (
          <Button
            variant="primary"
            onClick={handleOpenCreate}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700 }}
          >
            <span>➕</span> Invitar Coordinador
          </Button>
        )}
      </div>

      {/* Global Alerts */}
      {error && (
        <div style={{ marginBottom: '1.25rem' }}>
          <Alert variant="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}
      {successMsg && (
        <div style={{ marginBottom: '1.25rem' }}>
          <Alert variant="success" onClose={() => setSuccessMsg(null)}>
            {successMsg}
          </Alert>
        </div>
      )}

      {/* Filter and Search Bar */}
      <Card style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
          <div style={{ flex: '1 1 240px' }}>
            <input
              type="text"
              placeholder="Buscar por nombre, documento o correo..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{
                width: '100%',
                padding: '0.55rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
              }}
            />
          </div>
          <div>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value as any)}
              style={{
                padding: '0.55rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
              }}
            >
              <option value="all">Todos los estados</option>
              <option value="active">Solo Activos</option>
              <option value="inactive">Solo Inactivos / Suspendidos</option>
            </select>
          </div>
          <Button variant="secondary" onClick={() => void loadData()} style={{ fontSize: '0.875rem' }}>
            🔄 Actualizar
          </Button>
        </div>
      </Card>

      {/* Content Area */}
      {isLoading ? (
        <Card style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <LoadingSpinner size="lg" label="Cargando nómina de coordinadores..." />
        </Card>
      ) : coordinators.length === 0 ? (
        <EmptyState
          icon="👔"
          title="No hay coordinadores registrados"
          description={
            search
              ? 'No se encontraron coordinadores que coincidan con los criterios de búsqueda.'
              : 'La institución no cuenta aún con coordinadores asignados. Inicie invitando a un nuevo coordinador académico.'
          }
          actionLabel={canCreate ? '➕ Invitar Primer Coordinador' : undefined}
          onAction={canCreate ? handleOpenCreate : undefined}
        />
      ) : (
        <Card style={{ overflow: 'hidden', padding: 0 }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>Coordinador</th>
                  <th style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>Identificación</th>
                  <th style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>Alcance Territorial</th>
                  <th style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>Estado de Cuenta</th>
                  <th style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>Invitación</th>
                  <th style={{ padding: '0.85rem 1.25rem', fontWeight: 700, textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {coordinators.map(coord => (
                  <tr
                    key={coord.id}
                    style={{
                      borderBottom: '1px solid #F1F5F9',
                      transition: 'background-color 0.15s',
                    }}
                  >
                    <td style={{ padding: '1rem 1.25rem' }}>
                      <div style={{ fontWeight: 700, color: '#0F172A' }}>{coord.full_name}</div>
                      <div style={{ fontSize: '0.8125rem', color: '#64748B' }}>{coord.email}</div>
                    </td>
                    <td style={{ padding: '1rem 1.25rem', color: '#334155' }}>
                      <span style={{ fontWeight: 600 }}>{coord.document_type}</span> {coord.document_number}
                    </td>
                    <td style={{ padding: '1rem 1.25rem' }}>
                      {coord.campus_name ? (
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            backgroundColor: '#F3E8FF',
                            color: '#6B21A8',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            padding: '0.25rem 0.65rem',
                            borderRadius: '9999px',
                          }}
                        >
                          🏛️ Sede: {coord.campus_name}
                        </span>
                      ) : (
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            backgroundColor: '#E0F2FE',
                            color: '#0369A1',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            padding: '0.25rem 0.65rem',
                            borderRadius: '9999px',
                          }}
                        >
                          🌐 Institución Completa
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '1rem 1.25rem' }}>
                      {coord.is_active ? (
                        <Badge variant="success">Activo</Badge>
                      ) : coord.is_verified ? (
                        <Badge variant="danger">Suspendido</Badge>
                      ) : (
                        <Badge variant="warning">Inactivo (Pendiente)</Badge>
                      )}
                    </td>
                    <td style={{ padding: '1rem 1.25rem' }}>
                      {coord.is_verified ? (
                        <Badge variant="success">Cuenta Activada</Badge>
                      ) : coord.invitation_status === 'pending' ? (
                        <Badge variant="warning">Invitación Pendiente</Badge>
                      ) : coord.invitation_status === 'expired' ? (
                        <Badge variant="danger">Invitación Expirada</Badge>
                      ) : coord.invitation_status === 'revoked' ? (
                        <Badge variant="neutral">Revocada</Badge>
                      ) : (
                        <Badge variant="neutral">Directo</Badge>
                      )}
                    </td>
                    <td style={{ padding: '1rem 1.25rem', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.5rem', alignItems: 'center' }}>
                        {!coord.is_verified && canCreate && (
                          <Button
                            variant="secondary"
                            size="sm"
                            disabled={resendingId === coord.id}
                            onClick={() => void handleResend(coord)}
                            style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                          >
                            {resendingId === coord.id ? 'Reenviando...' : '📨 Reenviar Enlace'}
                          </Button>
                        )}
                        {canUpdate && coord.is_verified && (
                          <Button
                            variant={coord.is_active ? 'secondary' : 'primary'}
                            size="sm"
                            onClick={() => handleOpenStatusModal(coord)}
                            style={{
                              fontSize: '0.75rem',
                              padding: '0.3rem 0.6rem',
                              borderColor: coord.is_active ? '#DC2626' : undefined,
                              color: coord.is_active ? '#DC2626' : undefined,
                            }}
                          >
                            {coord.is_active ? '🚫 Suspender' : '✅ Activar'}
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Modal: Invitar Coordinador */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Invitar Coordinador Académico"
        maxWidth="md"
      >
        <form onSubmit={handleCreateSubmit}>
          {createError && (
            <div style={{ marginBottom: '1rem' }}>
              <Alert variant="error">{createError}</Alert>
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, marginBottom: '0.3rem' }}>
                  Nombres *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ej. Carlos Alberto"
                  value={createForm.first_name}
                  onChange={e => setCreateForm({ ...createForm, first_name: e.target.value })}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, marginBottom: '0.3rem' }}>
                  Apellidos *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ej. Gómez Restrepo"
                  value={createForm.last_name}
                  onChange={e => setCreateForm({ ...createForm, last_name: e.target.value })}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, marginBottom: '0.3rem' }}>
                  Tipo Doc. *
                </label>
                <select
                  value={createForm.document_type}
                  onChange={e => setCreateForm({ ...createForm, document_type: e.target.value as any })}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                >
                  <option value="CC">CC</option>
                  <option value="CE">CE</option>
                  <option value="PAS">PAS</option>
                  <option value="PEP">PEP</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, marginBottom: '0.3rem' }}>
                  Número de Identificación *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Número de cédula o documento"
                  value={createForm.document_number}
                  onChange={e => setCreateForm({ ...createForm, document_number: e.target.value })}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, marginBottom: '0.3rem' }}>
                Correo Electrónico Institucional *
              </label>
              <input
                type="email"
                required
                placeholder="coordinador@institucion.edu.co"
                value={createForm.email}
                onChange={e => setCreateForm({ ...createForm, email: e.target.value })}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
              />
              <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
                Se emitirá un enlace único y criptográfico de activación a esta dirección.
              </span>
            </div>

            {/* Exclusivity Warning if Global Coordinator already exists */}
            {hasEffectiveGlobal && (
              <div
                style={{
                  padding: '0.85rem',
                  backgroundColor: '#FEF2F2',
                  border: '1px solid #FCA5A5',
                  borderRadius: '8px',
                  fontSize: '0.8125rem',
                  color: '#991B1B',
                  lineHeight: 1.45,
                }}
              >
                <strong>🔒 Exclusividad Institucional Activa:</strong> La institución ya cuenta con un Coordinador Académico de alcance global (<strong>{effectiveGlobalCoord?.full_name}</strong>). De acuerdo con la normativa PEVN NTA-10-R10, no es posible designar coordinadores adicionales mientras exista una coordinación general activa.
              </div>
            )}

            {/* Scope Selector */}
            <div
              style={{
                backgroundColor: '#F8FAFC',
                border: '1px solid #E2E8F0',
                borderRadius: '8px',
                padding: '0.85rem',
              }}
            >
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, marginBottom: '0.35rem' }}>
                Alcance y Jurisdicción de Coordinación *
              </label>
              <p style={{ margin: '0 0 0.75rem 0', fontSize: '0.75rem', color: '#64748B' }}>
                ℹ️ <strong>Regla de Exclusividad (NTA-10-R10):</strong> Se permite <strong>un único Coordinador Institucional (Global)</strong>, O BIEN <strong>un único Coordinador por cada sede educativa</strong> (mutuamente excluyentes).
              </p>

              <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '0.75rem' }}>
                <label
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    fontSize: '0.875rem',
                    cursor: hasEffectiveCampus || hasEffectiveGlobal ? 'not-allowed' : 'pointer',
                    color: hasEffectiveCampus || hasEffectiveGlobal ? '#94A3B8' : '#0F172A',
                  }}
                >
                  <input
                    type="radio"
                    name="scopeType"
                    disabled={hasEffectiveCampus || hasEffectiveGlobal}
                    checked={scopeType === 'institution'}
                    onChange={() => {
                      setScopeType('institution')
                      setCreateForm(prev => ({ ...prev, campus_id: null }))
                    }}
                  />
                  <span>Toda la Institución (Global)</span>
                </label>

                <label
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    fontSize: '0.875rem',
                    cursor: hasEffectiveGlobal ? 'not-allowed' : 'pointer',
                    color: hasEffectiveGlobal ? '#94A3B8' : '#0F172A',
                  }}
                >
                  <input
                    type="radio"
                    name="scopeType"
                    disabled={hasEffectiveGlobal}
                    checked={scopeType === 'campus'}
                    onChange={() => setScopeType('campus')}
                  />
                  <span>Sede Específica</span>
                </label>
              </div>

              {hasEffectiveCampus && (
                <div style={{ margin: '0 0 0.75rem 0', fontSize: '0.75rem', color: '#B45309' }}>
                  ⚠️ <em>Alcance global deshabilitado:</em> Ya existen {effectiveCampusCoords.length} coordinador(es) asignado(s) a sedes particulares. Para designar un coordinador global, no deben existir coordinaciones por sede.
                </div>
              )}

              {scopeType === 'campus' && !hasEffectiveGlobal && (
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                    Seleccione la Sede Educativa Asignada:
                  </label>
                  <select
                    aria-label="Seleccionar sede educativa"
                    value={createForm.campus_id || ''}
                    onChange={e => setCreateForm({ ...createForm, campus_id: e.target.value || null })}
                    required={scopeType === 'campus'}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
                  >
                    <option value="">-- Seleccione una sede --</option>
                    {campuses.map(c => {
                      const assignedCoordinator = occupiedCampusMap.get(c.id)
                      const isOccupied = !!assignedCoordinator
                      return (
                        <option key={c.id} value={c.id} disabled={isOccupied}>
                          {c.name} (DANE {c.dane_sede_code}) {isOccupied ? `— [Asignada a: ${assignedCoordinator}]` : ''}
                        </option>
                      )
                    })}
                  </select>
                  {campuses.length > 0 && campuses.every(c => occupiedCampusMap.has(c.id)) && (
                    <p style={{ margin: '0.35rem 0 0', fontSize: '0.75rem', color: '#DC2626' }}>
                      Todas las sedes educativas de la institución ya cuentan con un coordinador asignado.
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
            <Button variant="secondary" type="button" onClick={() => setIsCreateOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              type="submit"
              disabled={isSubmitting || hasEffectiveGlobal || (scopeType === 'campus' && (!createForm.campus_id || occupiedCampusMap.has(createForm.campus_id)))}
            >
              {isSubmitting ? 'Generando Invitación...' : '✉️ Emitir Invitación'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Enlace de Invitación Generado */}
      <Modal
        isOpen={outcomeModal.isOpen}
        onClose={() => setOutcomeModal(prev => ({ ...prev, isOpen: false }))}
        title="Invitación Criptográfica Generada"
        maxWidth="md"
      >
        <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              backgroundColor: '#F0FDF4',
              color: '#15803D',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.75rem',
              margin: '0 auto 1rem',
            }}
          >
            ✉️
          </div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
            Invitación Lista para Activación
          </h3>
          <p style={{ color: '#64748B', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Se ha creado la credencial segura para {outcomeModal.coordinatorName}.
          </p>
        </div>

        <div
          style={{
            backgroundColor: '#F8FAFC',
            borderRadius: '8px',
            border: '1px solid #E2E8F0',
            padding: '1rem',
            fontSize: '0.8125rem',
            color: '#334155',
            marginBottom: '1.25rem',
          }}
        >
          <div><strong>Destinatario:</strong> {outcomeModal.email}</div>
          <div style={{ marginTop: '0.25rem' }}><strong>Alcance:</strong> {outcomeModal.campusName}</div>
          <div style={{ marginTop: '0.25rem' }}>
            <strong>Vigencia:</strong> 48 horas (un solo uso criptográfico)
          </div>
        </div>

        {outcomeModal.invitationUrl ? (
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, marginBottom: '0.35rem' }}>
              Enlace Seguro de Activación (Desarrollo / Pruebas):
            </label>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
              <input
                type="text"
                readOnly
                value={outcomeModal.invitationUrl}
                style={{
                  flex: 1,
                  padding: '0.5rem',
                  fontSize: '0.8125rem',
                  borderRadius: '6px',
                  border: '1px solid #CBD5E1',
                  backgroundColor: '#F1F5F9',
                  fontFamily: 'monospace',
                }}
              />
              <Button
                variant="primary"
                onClick={handleCopyLink}
                style={{ whiteSpace: 'nowrap' }}
              >
                {outcomeModal.copied ? '✓ Copiado' : '📋 Copiar'}
              </Button>
            </div>
            <p style={{ fontSize: '0.75rem', color: '#64748B', margin: 0 }}>
              💡 Copie este enlace y ábralo para simular la aceptación de la invitación y la definición de contraseña del coordinador.
            </p>
          </div>
        ) : (
          <p style={{ fontSize: '0.875rem', color: '#475569', textAlign: 'center' }}>
            El enlace ha sido despachado por correo electrónico al coordinador. En entorno de producción, las credenciales no son reveladas en pantalla por seguridad.
          </p>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
          <Button variant="primary" onClick={() => setOutcomeModal(prev => ({ ...prev, isOpen: false }))}>
            Entendido
          </Button>
        </div>
      </Modal>

      {/* Modal: Confirmar Activación / Suspensión */}
      <Modal
        isOpen={statusModal.isOpen}
        onClose={() => setStatusModal(prev => ({ ...prev, isOpen: false }))}
        title={statusModal.isActivating ? 'Activar Coordinador' : 'Suspender Coordinador'}
        maxWidth="sm"
      >
        <form onSubmit={handleStatusSubmit}>
          <p style={{ fontSize: '0.875rem', color: '#475569', lineHeight: 1.5, margin: '0 0 1rem' }}>
            {statusModal.isActivating
              ? `¿Está seguro de activar al coordinador ${statusModal.target?.full_name}? Podrá acceder a la plataforma de inmediato.`
              : `¿Está seguro de suspender al coordinador ${statusModal.target?.full_name}? Se invalidarán sus sesiones activas de inmediato.`}
          </p>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, marginBottom: '0.35rem' }}>
              Motivo (opcional):
            </label>
            <input
              type="text"
              placeholder="Ej. Fin de periodo académico, reasignación, etc."
              value={statusModal.reason}
              onChange={e => setStatusModal({ ...statusModal, reason: e.target.value })}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <Button variant="secondary" type="button" onClick={() => setStatusModal(prev => ({ ...prev, isOpen: false }))}>
              Cancelar
            </Button>
            <Button
              variant={statusModal.isActivating ? 'primary' : 'danger'}
              type="submit"
              disabled={statusModal.isSubmitting}
            >
              {statusModal.isSubmitting ? 'Procesando...' : statusModal.isActivating ? 'Confirmar Activación' : 'Confirmar Suspensión'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
