/**
 * PEVN Frontend — Institution Settings View (Configuración Institucional)
 *
 * Rector-controlled institutional administration interface.
 * Features:
 *   - Operational coordinator delegation feature flag toggle
 *   - Clear explanation of administrative delegation and security boundaries
 *   - Persistence per tenant with fail-secure defaults (disabled)
 *   - Role protection: strictly actionable for authenticated Rector (or SuperAdmin)
 */

import React, { useCallback, useEffect, useState } from 'react'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useAuth } from '@/hooks/useAuth'
import { institutionApi } from '@/services/institution'
import type { InstitutionResponse } from '@/types'

export const InstitutionSettingsView: React.FC = () => {
  const { hasRole, activeInstitutionId } = useAuth()
  const [institution, setInstitution] = useState<InstitutionResponse | null>(null)
  const [delegationEnabled, setDelegationEnabled] = useState<boolean>(false)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isSaving, setIsSaving] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const isRector = hasRole(['rector', 'superadmin'])

  const loadInstitutionData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      let inst: InstitutionResponse
      if (activeInstitutionId) {
        inst = await institutionApi.getInstitutionById(activeInstitutionId)
      } else {
        inst = await institutionApi.getMyInstitution()
      }
      setInstitution(inst)

      // Fetch persisted coordinator delegation setting
      const setting = await institutionApi.getCoordinatorDelegationSetting(inst.id)
      setDelegationEnabled(setting.coordinator_delegation_enabled)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar configuración institucional.'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [activeInstitutionId])

  useEffect(() => {
    void loadInstitutionData()
  }, [loadInstitutionData])

  const handleToggleDelegation = async (newVal: boolean) => {
    if (!institution) return
    setIsSaving(true)
    setError(null)
    setSuccessMsg(null)
    try {
      const updated = await institutionApi.updateCoordinatorDelegationSetting(institution.id, newVal)
      setDelegationEnabled(updated.coordinator_delegation_enabled)
      setSuccessMsg(
        updated.coordinator_delegation_enabled
          ? '✓ Delegación operativa habilitada. Los coordinadores de su institución ahora pueden gestionar docentes, estudiantes y acudientes.'
          : '✓ Delegación operativa inhabilitada. Las operaciones de gestión para coordinadores quedan restringidas.'
      )
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al actualizar configuración institucional.'
      setError(msg)
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!institution) {
    return (
      <Alert variant="warning" title="Contexto Institucional No Disponible">
        No se pudo identificar una institución educativa asociada a su sesión. Verifique su perfil directivo.
      </Alert>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '960px', margin: '0 auto' }}>
      {/* Header Info Banner */}
      <div
        style={{
          backgroundColor: '#0F172A',
          color: '#FFFFFF',
          borderRadius: '16px',
          padding: '1.75rem 2rem',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
          <Badge variant="info">Rectoría • Parámetros de Tenant</Badge>
          <span style={{ fontSize: '0.8rem', color: '#CBD5E1' }}>DANE: {institution.dane_code}</span>
        </div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, margin: '0.25rem 0', color: '#FFFFFF' }}>
          Configuración Institucional — {institution.name}
        </h1>
        <p style={{ fontSize: '0.875rem', color: '#CBD5E1', margin: 0 }}>
          Gobernanza directiva, delegación de facultades operativas y políticas de seguridad del establecimiento.
        </p>
      </div>

      {error && (
        <Alert variant="error" title="Error de Autorización o Comunicación">
          {error}
        </Alert>
      )}

      {successMsg && (
        <Alert variant="success" title="Configuración Actualizada Exitosamente">
          {successMsg}
        </Alert>
      )}

      {/* Coordinator Delegation Setting Card */}
      <Card>
        <div style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ maxWidth: '640px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '1.5rem' }}>🛡️</span>
                <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0F172A', margin: 0 }}>
                  Permitir a Coordinadores gestionar Docentes, Estudiantes y Acudientes
                </h2>
              </div>
              <p style={{ fontSize: '0.875rem', color: '#475569', lineHeight: 1.6, margin: '0 0 1rem 0' }}>
                Al habilitar esta opción, los Coordinadores Académicos y de Sede de su institución podrán registrar nuevos perfiles docentes, vincular y matricular estudiantes en SIMAT, registrar acudientes y asociar el parentesco familiar.
              </p>

              {/* Security Boundaries Explanation */}
              <div
                style={{
                  backgroundColor: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  borderRadius: '10px',
                  padding: '1rem',
                  fontSize: '0.8125rem',
                  color: '#334155',
                }}
              >
                <div style={{ fontWeight: 700, color: '#0F172A', marginBottom: '0.5rem' }}>
                  🔒 Límites de Seguridad e Invariantes del Sistema:
                </div>
                <ul style={{ margin: 0, paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <li>
                    <strong>Alcance estricto:</strong> Esta configuración aplica únicamente a su propia institución (aislamiento multi-tenant).
                  </li>
                  <li>
                    <strong>Sin escalación de privilegios:</strong> Los Coordinadores nunca pueden designar Rectores, crear otros Coordinadores, ni modificar administradores territoriales o nacionales.
                  </li>
                  <li>
                    <strong>Protección no destructiva:</strong> Inhabilitar esta opción revoca de inmediato la autorización de creación/modificación para Coordinadores, pero <em>no elimina ni altera</em> registros existentes, notas, matrículas ni cuentas activas.
                  </li>
                  <li>
                    <strong>Autonomía rectoral:</strong> Como Rector, usted siempre conserva la potestad plena de gestión independientemente del estado de este interruptor.
                  </li>
                </ul>
              </div>
            </div>

            {/* Current State & Action Control */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-end',
                gap: '1rem',
                minWidth: '200px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.8125rem', color: '#64748B', fontWeight: 600 }}>Estado Actual:</span>
                <Badge variant={delegationEnabled ? 'success' : 'neutral'}>
                  {delegationEnabled ? 'HABILITADA' : 'INHABILITADA'}
                </Badge>
              </div>

              {isRector ? (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  {delegationEnabled ? (
                    <Button
                      variant="danger"
                      size="sm"
                      disabled={isSaving}
                      onClick={() => void handleToggleDelegation(false)}
                      style={{ fontWeight: 600 }}
                    >
                      {isSaving ? <LoadingSpinner size="sm" /> : 'Inhabilitar Delegación'}
                    </Button>
                  ) : (
                    <Button
                      variant="primary"
                      size="sm"
                      disabled={isSaving}
                      onClick={() => void handleToggleDelegation(true)}
                      style={{ fontWeight: 600, backgroundColor: '#16A34A' }}
                    >
                      {isSaving ? <LoadingSpinner size="sm" /> : 'Habilitar Delegación'}
                    </Button>
                  )}
                </div>
              ) : (
                <span style={{ fontSize: '0.75rem', color: '#475569', fontStyle: 'italic', fontWeight: 500 }}>
                  Solo lectura (Requiere rol Rector)
                </span>
              )}
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default InstitutionSettingsView
