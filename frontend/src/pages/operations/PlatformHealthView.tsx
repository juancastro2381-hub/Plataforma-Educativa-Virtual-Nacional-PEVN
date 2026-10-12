/**
 * PEVN Frontend — Platform Health & Infrastructure Observability
 *
 * Real-time operational health telemetry, dependency probes, and latency metrics
 * for SUPER_ADMIN (Level 100).
 */

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Button } from '@/components/ui/Button'
import { operationsApi, type PlatformHealthResponse, type PlatformOverviewResponse } from '@/services/operations'

export const PlatformHealthView: React.FC = () => {
  const [overview, setOverview] = useState<PlatformOverviewResponse | null>(null)
  const [health, setHealth] = useState<PlatformHealthResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string>('')

  const fetchHealthData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [ovData, hlData] = await Promise.all([
        operationsApi.getOverview(),
        operationsApi.getHealth(),
      ])
      setOverview(ovData)
      setHealth(hlData)
      setLastUpdated(new Date().toLocaleTimeString())
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al consultar la telemetría del sistema.'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void fetchHealthData()
  }, [])

  return (
    <div style={{ maxWidth: '1280px', margin: '2rem auto', padding: '0 1.5rem', width: '100%' }}>
      {/* Header Bar */}
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
              🌐 OBSERVABILIDAD TÉCNICA • L100
            </span>
            {overview && (
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  backgroundColor: overview.overall_status === 'OPERATIONAL' ? 'rgba(74, 222, 128, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                  color: overview.overall_status === 'OPERATIONAL' ? '#4ADE80' : '#F87171',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '9999px',
                  border: `1px solid ${overview.overall_status === 'OPERATIONAL' ? 'rgba(74, 222, 128, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
                }}
              >
                ● {overview.overall_status}
              </span>
            )}
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0 0 0.5rem 0', color: '#FFFFFF' }}>
            Salud e Infraestructura de la Plataforma
          </h1>
          <p style={{ color: '#94A3B8', fontSize: '0.875rem', margin: 0, maxWidth: '750px' }}>
            Monitoreo en tiempo real de conectividad a bases de datos, latencia de procesamiento, estado de clusters Redis y adaptadores de datos abiertos del Estado.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <Button
            variant="secondary"
            onClick={() => void fetchHealthData()}
            disabled={isLoading}
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
              color: '#FFFFFF',
              border: '1px solid rgba(255, 255, 255, 0.3)',
            }}
          >
            {isLoading ? 'Sondeando...' : '🔄 Actualizar Estado'}
          </Button>
          <Link to="/dashboard">
            <Button variant="primary">Panel Principal →</Button>
          </Link>
        </div>
      </div>

      {error && (
        <div style={{ padding: '1rem 1.5rem', backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '12px', color: '#991B1B', marginBottom: '2rem' }}>
          <strong>Error de sondeo:</strong> {error}
        </div>
      )}

      {/* KPI Cards */}
      {overview && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
          <div style={{ backgroundColor: '#FFFFFF', padding: '1.5rem', borderRadius: '12px', border: '1px solid #E2E8F0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Base de Datos Primaria (PostgreSQL)
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: overview.database.status === 'ok' ? '#166534' : '#991B1B', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>{overview.database.status === 'ok' ? '✓ Operativa' : '⚠ Falla'}</span>
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#475569', marginTop: '0.5rem' }}>
              Latencia de consulta: <strong>{overview.database.latency_ms} ms</strong>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '0.25rem' }}>
              Pool: {overview.database.pool_size} conexiones reservadas
            </div>
          </div>

          <div style={{ backgroundColor: '#FFFFFF', padding: '1.5rem', borderRadius: '12px', border: '1px solid #E2E8F0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Caché Distribuida (Redis)
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: overview.redis.status === 'ok' ? '#166534' : '#D97706', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>{overview.redis.status === 'ok' ? '✓ Conectado' : '⚡ Tolerancia Fallo'}</span>
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#475569', marginTop: '0.5rem' }}>
              Modo de operación: <strong>{overview.redis.mode}</strong>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '0.25rem' }}>
              Aislamiento de sesiones y rate limit activo
            </div>
          </div>

          <div style={{ backgroundColor: '#FFFFFF', padding: '1.5rem', borderRadius: '12px', border: '1px solid #E2E8F0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Seguridad & Auditoría (24h)
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1E40AF' }}>
              {overview.metrics.security_events_24h} eventos
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#475569', marginTop: '0.5rem' }}>
              Incidentes abiertos: <strong>{overview.metrics.active_incidents}</strong>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '0.25rem' }}>
              Registro inmutable en audit_logs activo
            </div>
          </div>

          <div style={{ backgroundColor: '#FFFFFF', padding: '1.5rem', borderRadius: '12px', border: '1px solid #E2E8F0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Entorno y Sonda
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0F172A' }}>
              {overview.environment.toUpperCase()}
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#475569', marginTop: '0.5rem' }}>
              Última lectura: <strong>{lastUpdated || 'En curso'}</strong>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '0.25rem' }}>
              Versión plataforma: v{overview.version}
            </div>
          </div>
        </div>
      )}

      {/* Services Breakdown List */}
      <div style={{ backgroundColor: '#FFFFFF', padding: '1.75rem', borderRadius: '16px', border: '1px solid #E2E8F0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', marginBottom: '1rem' }}>
          Inventario de Subsistemas y Dependencias de Infraestructura
        </h2>

        {isLoading && !health ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem' }}>
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {health?.services.map((svc) => (
              <div
                key={svc.name}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '1rem',
                  borderRadius: '10px',
                  backgroundColor: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: 700, color: '#0F172A', fontSize: '0.9375rem' }}>{svc.name}</span>
                    <span style={{ fontSize: '0.7rem', color: '#64748B', backgroundColor: '#E2E8F0', padding: '0.1rem 0.4rem', borderRadius: '4px', textTransform: 'uppercase' }}>
                      {svc.type}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: '#64748B', marginTop: '0.25rem' }}>
                    {svc.details}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      padding: '0.25rem 0.65rem',
                      borderRadius: '9999px',
                      backgroundColor: svc.status === 'operational' ? '#DCFCE7' : '#FEF3C7',
                      color: svc.status === 'operational' ? '#15803D' : '#B45309',
                      border: `1px solid ${svc.status === 'operational' ? '#86EFAC' : '#FDE68A'}`,
                    }}
                  >
                    ● {svc.status.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
