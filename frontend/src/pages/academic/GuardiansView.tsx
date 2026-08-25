/**
 * PEVN Frontend — Guardians View
 *
 * Legal guardians (Acudientes), decoupled civil identities,
 * and student family associations.
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
  AssociateGuardianRequest,
  DocumentType,
  GuardianCreateRequest,
  GuardianRelationshipType,
  GuardianResponse,
} from '@/types'

export const GuardiansView: React.FC = () => {
  const { hasPermission } = useAuth()

  const [guardians, setGuardians] = useState<GuardianResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [docSearch, setDocSearch] = useState<string>('')
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Create Guardian Modal
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [firstName, setFirstName] = useState<string>('')
  const [lastName, setLastName] = useState<string>('')
  const [docType, setDocType] = useState<DocumentType>('CC')
  const [docNumber, setDocNumber] = useState<string>('')
  const [phone, setPhone] = useState<string>('')
  const [email, setEmail] = useState<string>('')
  const [address, setAddress] = useState<string>('')
  const [relationshipType, setRelationshipType] = useState<GuardianRelationshipType>('MADRE')

  // Associate to Student Modal
  const [linkModal, setLinkModal] = useState<{
    isOpen: boolean
    guardian: GuardianResponse | null
    studentId: string
    relType: GuardianRelationshipType
    isPrimary: boolean
    isAuthorizedPickup: boolean
  }>({
    isOpen: false,
    guardian: null,
    studentId: '',
    relType: 'MADRE',
    isPrimary: false,
    isAuthorizedPickup: true,
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

  useEffect(() => {
    void loadGuardians()
  }, [loadGuardians])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    void loadGuardians()
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
    }

    try {
      await academicApi.createGuardian(payload)
      setSuccessMsg(`Acudiente ${payload.first_name} ${payload.last_name} registrado exitosamente.`)
      setIsCreateOpen(false)
      setFirstName('')
      setLastName('')
      setDocNumber('')
      setPhone('')
      setEmail('')
      setAddress('')
      await loadGuardians()
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al registrar acudiente'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleLinkStudent = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!linkModal.guardian || !linkModal.studentId) return
    setIsSubmitting(true)
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
        linkModal.studentId.trim(),
        payload
      )
      setSuccessMsg('Acudiente vinculado exitosamente al estudiante.')
      setLinkModal({
        isOpen: false,
        guardian: null,
        studentId: '',
        relType: 'MADRE',
        isPrimary: false,
        isAuthorizedPickup: true,
      })
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error('Error al vincular acudiente'))
    } finally {
      setIsSubmitting(false)
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
        title="Registro Civil de Acudientes"
        subtitle={`Total de acudientes registrados: ${String(total)}`}
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
                  <th style={{ padding: '0.75rem 1rem' }}>Correo Electrónico</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Parentesco</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {guardians.map((g) => (
                  <tr key={g.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                      {g.first_name} {g.last_name}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#1E40AF' }}>
                      <code>{g.document_type} {g.document_number}</code>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#475569' }}>{g.phone}</td>
                    <td style={{ padding: '0.875rem 1rem', color: '#64748B' }}>
                      {g.email || <span style={{ fontStyle: 'italic', color: '#94A3B8' }}>Sin correo</span>}
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      <Badge variant="info" size="sm">{g.relationship_type}</Badge>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      {hasPermission('guardians:link_student') && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            setLinkModal({
                              isOpen: true,
                              guardian: g,
                              studentId: '',
                              relType: g.relationship_type,
                              isPrimary: false,
                              isAuthorizedPickup: true,
                            })
                          }}
                        >
                          Vincular a Estudiante
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Link to Student Modal */}
      <Modal
        isOpen={linkModal.isOpen}
        onClose={() => {
          setLinkModal({
            isOpen: false,
            guardian: null,
            studentId: '',
            relType: 'MADRE',
            isPrimary: false,
            isAuthorizedPickup: true,
          })
        }}
        title={`Vincular Acudiente — ${linkModal.guardian?.first_name ?? ''} ${linkModal.guardian?.last_name ?? ''}`}
        subtitle="Asocie este acudiente a un estudiante especificando roles y autorizaciones."
      >
        <form onSubmit={(e) => void handleLinkStudent(e)}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              ID de Estudiante (Student UUID) *
            </label>
            <input
              type="text"
              value={linkModal.studentId}
              onChange={(e) => {
                setLinkModal({ ...linkModal, studentId: e.target.value })
              }}
              required
              placeholder="UUID del estudiante institucional"
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Tipo de Relación / Parentesco *
            </label>
            <select
              value={linkModal.relType}
              onChange={(e) => {
                setLinkModal({ ...linkModal, relType: e.target.value as GuardianRelationshipType })
              }}
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            >
              <option value="MADRE">Madre</option>
              <option value="PADRE">Padre</option>
              <option value="ABUELO">Abuelo</option>
              <option value="ABUELA">Abuela</option>
              <option value="TIO">Tío</option>
              <option value="TIA">Tía</option>
              <option value="HERMANO">Hermano</option>
              <option value="HERMANA">Hermana</option>
              <option value="TUTOR_LEGAL">Tutor Legal</option>
              <option value="OTRO">Otro</option>
            </select>
          </div>

          <div style={{ marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: '#334155', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={linkModal.isPrimary}
                onChange={(e) => {
                  setLinkModal({ ...linkModal, isPrimary: e.target.checked })
                }}
              />
              <strong>Contacto Principal de Emergencia</strong>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: '#334155', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={linkModal.isAuthorizedPickup}
                onChange={(e) => {
                  setLinkModal({ ...linkModal, isAuthorizedPickup: e.target.checked })
                }}
              />
              <strong>Autorizado para Retiro del Plantel Educativo</strong>
            </label>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setLinkModal({
                  isOpen: false,
                  guardian: null,
                  studentId: '',
                  relType: 'MADRE',
                  isPrimary: false,
                  isAuthorizedPickup: true,
                })
              }}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Confirmar Vinculación'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Create Guardian Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false)
        }}
        title="Registrar Acudiente"
        subtitle="Identificación civil y datos de contacto del responsable familiar."
      >
        <form onSubmit={(e) => void handleCreateGuardian(e)}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Nombres *
              </label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => {
                  setFirstName(e.target.value)
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Apellidos *
              </label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => {
                  setLastName(e.target.value)
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Tipo Doc. *
              </label>
              <select
                value={docType}
                onChange={(e) => {
                  setDocType(e.target.value as DocumentType)
                }}
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              >
                <option value="CC">CC</option>
                <option value="TI">TI</option>
                <option value="CE">CE</option>
                <option value="PASSPORT">Pasaporte</option>
                <option value="PEP">PEP</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Número de Documento *
              </label>
              <input
                type="text"
                value={docNumber}
                onChange={(e) => {
                  setDocNumber(e.target.value)
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Teléfono de Contacto *
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => {
                  setPhone(e.target.value)
                }}
                required
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Correo Electrónico (Opcional)
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                }}
                placeholder="acudiente@ejemplo.com"
                style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Dirección Residencial
            </label>
            <input
              type="text"
              value={address}
              onChange={(e) => {
                setAddress(e.target.value)
              }}
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
              Parentesco por Defecto
            </label>
            <select
              value={relationshipType}
              onChange={(e) => {
                setRelationshipType(e.target.value as GuardianRelationshipType)
              }}
              style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
            >
              <option value="MADRE">Madre</option>
              <option value="PADRE">Padre</option>
              <option value="ABUELO">Abuelo/a</option>
              <option value="TUTOR_LEGAL">Tutor Legal</option>
              <option value="OTRO">Otro</option>
            </select>
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
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Guardar Acudiente'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default GuardiansView
