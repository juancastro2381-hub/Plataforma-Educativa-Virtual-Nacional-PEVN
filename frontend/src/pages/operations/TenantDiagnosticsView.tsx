/**
 * PEVN Frontend — Tenant Diagnostics & Institution Troubleshooting
 *
 * Dedicated institutional tenant diagnostics for SUPER_ADMIN (Level 100).
 * Provides audited, non-destructive diagnostic probes for individual educational tenants.
 */

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Button } from '@/components/ui/Button'
import { operationsApi, type TenantDiagnosticsResponse } from '@/services/operations'
import { institutionApi } from '@/services/institution'
import type { InstitutionResponse } from '@/types'

export const TenantDiagnosticsView: React.FC = () => {
  const { activeInstitutionId, activeInstitutionName, setActiveInstitutionContext } = useAuth()

  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<InstitutionResponse[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)

  const [diagnostics, setDiagnostics] = useState<TenantDiagnosticsResponse | null>(null)
  const [isLoadingDiagnostics, setIsLoadingDiagnostics] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Run diagnostics when activeInstitutionId changes
  useEffect(() => {
    if (!activeInstitutionId) {
      setDiagnostics(null)
      return
    }

    const runProbe = async () => {
      setIsLoadingDiagnostics(true)
      setError(null)
      try {
        const data = await operationsApi.getTenantDiagnostics(activeInstitutionId)
        setDiagnostics(data)
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Error al obtener diagnóstico del inquilino.'
        setError(msg)
      } finally {
        setIsLoadingDiagnostics(false)
      }
    }

    void runProbe()
  }, [activeInstitutionId])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmedQuery = searchQuery.trim()
    if (!trimmedQuery) {
      setSearchError('Por favor ingrese un nombre o código DANE para buscar.')
      return
    }
    setIsSearching(true)
    setSearchError(null)
    setSearchResults([])
    setHasSearched(false)
    try {
      const res = await institutionApi.listInstitutions({ search: trimmedQuery, page_size: 10 })
      setSearchResults(res.items || [])
      setHasSearched(true)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al buscar instituciones.'
      setSearchError(msg)
      setSearchResults([])
      setHasSearched(true)
    } finally {
      setIsSearching(false)
    }
  }

  const handleSelectInstitution = (inst: InstitutionResponse) => {
    setActiveInstitutionContext(inst.id, inst.name)
    setSearchResults([])
    setSearchQuery('')
    setHasSearched(false)
    setSearchError(null)
  }

  const handleExitContext = () => {
    setActiveInstitutionContext(null)
    setDiagnostics(null)
    setSearchResults([])
    setSearchQuery('')
    setHasSearched(false)
    setSearchError(null)
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '2rem auto', padding: '0 1.5rem', width: '100%' }}>
      {/* Header Banner */}
      <div
        style={{
          backgroundColor: '#0F172A',
          color: '#FFFFFF',
          borderRadius: '16px',
          padding: '2rem',
          marginBottom: '2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          boxShadow: '0 10px 25px -5px rgba(15, 23, 42, 0.4)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 800,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                backgroundColor: 'rgba(252, 209, 22, 0.2)',
                color: '#FCD116',
                padding: '0.2rem 0.6rem',
                borderRadius: '9999px',
                border: '1px solid rgba(252, 209, 22, 0.4)',
              }}
            >
              🏛 DIAGNÓSTICO DE INQUILINATO • L100
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0 0 0.5rem 0', color: '#FFFFFF' }}>
            Diagnóstico Operacional de Inquilino / Tenant
          </h1>
          <p style={{ color: '#CBD5E1', fontSize: '0.875rem', margin: 0, maxWidth: '750px' }}>
            Sondeo técnico y aislamiento de instituciones educativas. Requiere selección explícita y registra traza de auditoría obligatoria en cada ejecución.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {activeInstitutionId && (
            <Button
              variant="secondary"
              onClick={handleExitContext}
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                color: '#FCA5A5',
                border: '1px solid rgba(239, 68, 68, 0.4)',
              }}
            >
              ✕ Salir a Operaciones Globales
            </Button>
          )}
          <Link to="/dashboard">
            <Button
              variant="secondary"
              style={{
                backgroundColor: 'transparent',
                color: '#CBD5E1',
                border: '1px solid #475569',
              }}
            >
              ← Volver
            </Button>
          </Link>
        </div>
      </div>

      {/* Active Context Banner if selected */}
      {activeInstitutionId ? (
        <div
          style={{
            backgroundColor: '#EFF6FF',
            border: '1px solid #BFDBFE',
            borderRadius: '12px',
            padding: '1.25rem 1.5rem',
            marginBottom: '2rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#1E40AF', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              CONTEXTO INSTITUCIONAL ACTIVO
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1E3A8A', marginTop: '0.25rem' }}>
              🏛️ {activeInstitutionName || activeInstitutionId}
            </div>
            <div style={{ fontSize: '0.875rem', color: '#1D4ED8', marginTop: '0.25rem', fontWeight: 500 }}>
              UUID: <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{activeInstitutionId}</span> • Acceso Auditado
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                if (activeInstitutionId) {
                  setIsLoadingDiagnostics(true)
                  void operationsApi.getTenantDiagnostics(activeInstitutionId).then(setDiagnostics).finally(() => setIsLoadingDiagnostics(false))
                }
              }}
              disabled={isLoadingDiagnostics}
            >
              🔄 Re-sondear
            </Button>
            <Button variant="danger" size="sm" onClick={handleExitContext}>
              Cerrar Diagnóstico
            </Button>
          </div>
        </div>
      ) : (
        /* Institution Selector Box */
        <div style={{ backgroundColor: '#FFFFFF', borderRadius: '16px', border: '1px solid #E2E8F0', padding: '2rem', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.5rem' }}>
            Seleccionar Institución para Diagnóstico
          </h2>
          <p style={{ color: '#64748B', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
            Para realizar un diagnóstico de infraestructura y usuarios, ingrese el nombre o código DANE de la institución.
          </p>

          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.75rem', maxWidth: '600px', marginBottom: '1.5rem' }}>
            <input
              type="text"
              placeholder="Buscar por nombre o código DANE..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                if (searchError) setSearchError(null)
              }}
              aria-label="Buscar por nombre o código DANE"
              style={{ flex: 1, padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
            />
            <Button variant="primary" type="submit" disabled={isSearching}>
              {isSearching ? 'Buscando...' : 'Buscar'}
            </Button>
          </form>

          {searchError && (
            <div
              role="alert"
              style={{
                padding: '0.875rem 1rem',
                backgroundColor: '#FEF2F2',
                border: '1px solid #FCA5A5',
                borderRadius: '8px',
                color: '#991B1B',
                fontSize: '0.875rem',
                marginBottom: '1rem',
              }}
            >
              <strong>Error de búsqueda:</strong> {searchError}
            </div>
          )}

          {hasSearched && searchResults.length === 0 && !isSearching && !searchError && (
            <div
              role="status"
              style={{
                padding: '1.25rem',
                backgroundColor: '#F8FAFC',
                border: '1px solid #E2E8F0',
                borderRadius: '8px',
                color: '#64748B',
                fontSize: '0.875rem',
                textAlign: 'center',
              }}
            >
              No se encontraron instituciones para el criterio ingresado.
            </div>
          )}

          {searchResults.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', border: '1px solid #E2E8F0', borderRadius: '8px', padding: '0.75rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                Resultados encontrados ({searchResults.length}):
              </div>
              {searchResults.map((inst) => (
                <div
                  key={inst.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.75rem',
                    backgroundColor: '#F8FAFC',
                    borderRadius: '6px',
                    border: '1px solid #F1F5F9',
                  }}
                >
                  <div>
                    <strong style={{ color: '#0F172A', fontSize: '0.9375rem' }}>{inst.name}</strong>
                    <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                      DANE: {inst.dane_code} • Estado: {inst.is_active ? 'Activa' : 'Inactiva'}
                    </div>
                  </div>
                  <Button variant="secondary" size="sm" onClick={() => handleSelectInstitution(inst)}>
                    Diagnosticar →
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {error && (
        <div style={{ padding: '1rem 1.5rem', backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '12px', color: '#991B1B', marginBottom: '2rem' }}>
          <strong>Error de diagnóstico:</strong> {error}
        </div>
      )}

      {/* Diagnostics Results */}
      {isLoadingDiagnostics ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
          <LoadingSpinner size="lg" />
        </div>
      ) : diagnostics ? (
        <div>
          {/* Metrics Overview */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
            <div style={{ backgroundColor: '#FFFFFF', padding: '1.5rem', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
                Estado Operacional
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: diagnostics.is_active ? '#166534' : '#991B1B', marginTop: '0.25rem' }}>
                {diagnostics.is_active ? '✓ ACTIVA' : '✕ INACTIVA / SUSPENDIDA'}
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#64748B', marginTop: '0.5rem' }}>
                DANE: <strong>{diagnostics.dane_code}</strong>
              </div>
            </div>

            <div style={{ backgroundColor: '#FFFFFF', padding: '1.5rem', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
                Sedes Vinculadas
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0F172A', marginTop: '0.25rem' }}>
                {diagnostics.telemetry.campuses_count} sedes
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#64748B', marginTop: '0.5rem' }}>
                Infraestructura física registrada
              </div>
            </div>

            <div style={{ backgroundColor: '#FFFFFF', padding: '1.5rem', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
                Usuarios Registrados
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1E40AF', marginTop: '0.25rem' }}>
                {diagnostics.telemetry.total_users} cuentas
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#166534', marginTop: '0.5rem' }}>
                {diagnostics.telemetry.active_users} activos • {diagnostics.telemetry.locked_users} bloqueados
              </div>
            </div>

            <div style={{ backgroundColor: '#FFFFFF', padding: '1.5rem', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
                Configuración del Inquilino
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0F172A', marginTop: '0.25rem' }}>
                {diagnostics.telemetry.configuration_status}
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#64748B', marginTop: '0.5rem' }}>
                Auditado: {new Date(diagnostics.audited_at).toLocaleTimeString()}
              </div>
            </div>
          </div>

          {/* Campuses Detail Table */}
          <div style={{ backgroundColor: '#FFFFFF', borderRadius: '16px', border: '1px solid #E2E8F0', padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0F172A', marginBottom: '1rem' }}>
              Inventario de Sedes Registradas
            </h3>
            {diagnostics.telemetry.campuses.length === 0 ? (
              <p style={{ color: '#64748B', fontSize: '0.875rem' }}>No se registran sedes asociadas a esta institución.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {diagnostics.telemetry.campuses.map((c) => (
                  <div
                    key={c.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.75rem 1rem',
                      backgroundColor: '#F8FAFC',
                      borderRadius: '8px',
                      border: '1px solid #E2E8F0',
                    }}
                  >
                    <div>
                      <strong style={{ color: '#0F172A', fontSize: '0.875rem' }}>{c.name}</strong>
                      <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                        DANE Sede: {c.dane_code}
                      </div>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: '#64748B', fontFamily: 'monospace' }}>
                      ID: {c.id}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
