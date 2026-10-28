/**
 * PEVN Frontend — Security & Audit Log Stream
 *
 * Real-time operational security audit viewer for SUPER_ADMIN (Level 100).
 * Displays authentication events, authorization failures, suspicious activity,
 * and immutable administrative audit traces.
 */

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Button } from '@/components/ui/Button'
import { operationsApi, type AuditFeedItem, type AuditFeedResponse } from '@/services/operations'

export const SecurityAuditView: React.FC = () => {
  const [feedData, setFeedData] = useState<AuditFeedResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [onlySecurity, setOnlySecurity] = useState(true)
  const [selectedItem, setSelectedItem] = useState<AuditFeedItem | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const loadAuditFeed = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await operationsApi.getAuditFeed({
        limit: 100,
        only_security: onlySecurity,
      })
      setFeedData(data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al consultar el registro de auditoría de seguridad.'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadAuditFeed()
  }, [onlySecurity])

  const filteredItems = (feedData?.items || []).filter((item) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      item.event_type.toLowerCase().includes(q) ||
      (item.actor_ip && item.actor_ip.toLowerCase().includes(q)) ||
      (item.actor_id && item.actor_id.toLowerCase().includes(q)) ||
      (item.target_type && item.target_type.toLowerCase().includes(q)) ||
      (item.target_id && item.target_id.toLowerCase().includes(q))
    )
  })

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
              🛡 SEGURIDAD & AUDITORÍA • L100
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0 0 0.5rem 0', color: '#FFFFFF' }}>
            Transmisión de Eventos y Auditoría de Seguridad
          </h1>
          <p style={{ color: '#CBD5E1', fontSize: '0.875rem', margin: 0, maxWidth: '750px' }}>
            Inspección forense de intentos de acceso, violaciones de control de acceso RBAC, bloqueos de cuentas y trazas inmutables de operadores técnicos.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <Button
            variant="secondary"
            onClick={() => void loadAuditFeed()}
            disabled={isLoading}
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
              color: '#FFFFFF',
              border: '1px solid rgba(255, 255, 255, 0.3)',
            }}
          >
            {isLoading ? 'Sondeando...' : '🔄 Actualizar Traza'}
          </Button>
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

      {error && (
        <div style={{ padding: '1rem 1.5rem', backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '12px', color: '#991B1B', marginBottom: '1.5rem' }}>
          <strong>Error de consulta:</strong> {error}
        </div>
      )}

      {/* Summary KPI Cards */}
      {feedData?.summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
          <div style={{ backgroundColor: '#FFFFFF', padding: '1.25rem', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
              Eventos Consultados
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', marginTop: '0.25rem' }}>
              {feedData.summary.total_queried}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#475569', marginTop: '0.25rem' }}>
              Últimos registros en audit_logs
            </div>
          </div>

          <div style={{ backgroundColor: '#FFFFFF', padding: '1.25rem', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#D97706', textTransform: 'uppercase' }}>
              Intentos Fallidos de Inicio
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#D97706', marginTop: '0.25rem' }}>
              {feedData.summary.failed_logins}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#475569', marginTop: '0.25rem' }}>
              Contraseñas o credenciales erróneas
            </div>
          </div>

          <div style={{ backgroundColor: '#FFFFFF', padding: '1.25rem', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#DC2626', textTransform: 'uppercase' }}>
              Permisos Denegados (403)
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#DC2626', marginTop: '0.25rem' }}>
              {feedData.summary.permission_denied}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#475569', marginTop: '0.25rem' }}>
              Intentos de escalación / fuera de rol
            </div>
          </div>

          <div style={{ backgroundColor: '#FFFFFF', padding: '1.25rem', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7C3AED', textTransform: 'uppercase' }}>
              Alertas Sospechosas
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#7C3AED', marginTop: '0.25rem' }}>
              {feedData.summary.suspicious_events}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#475569', marginTop: '0.25rem' }}>
              Comportamiento anómalo detectado
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div style={{ backgroundColor: '#FFFFFF', padding: '1.25rem', borderRadius: '12px', border: '1px solid #E2E8F0', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            type="button"
            onClick={() => setOnlySecurity(true)}
            style={{
              padding: '0.4rem 0.85rem',
              borderRadius: '6px',
              fontSize: '0.8125rem',
              fontWeight: 700,
              cursor: 'pointer',
              border: onlySecurity ? '1px solid #1E40AF' : '1px solid #CBD5E1',
              backgroundColor: onlySecurity ? '#EFF6FF' : '#FFFFFF',
              color: onlySecurity ? '#1E40AF' : '#475569',
            }}
          >
            🔒 Solo Eventos de Seguridad
          </button>
          <button
            type="button"
            onClick={() => setOnlySecurity(false)}
            style={{
              padding: '0.4rem 0.85rem',
              borderRadius: '6px',
              fontSize: '0.8125rem',
              fontWeight: 700,
              cursor: 'pointer',
              border: !onlySecurity ? '1px solid #1E40AF' : '1px solid #CBD5E1',
              backgroundColor: !onlySecurity ? '#EFF6FF' : '#FFFFFF',
              color: !onlySecurity ? '#1E40AF' : '#475569',
            }}
          >
            📜 Todos los Eventos del Sistema
          </button>
        </div>

        <div>
          <input
            type="text"
            placeholder="Buscar por evento, IP o recurso..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ padding: '0.4rem 0.75rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem', minWidth: '280px' }}
          />
        </div>
      </div>

      {/* Audit Feed Table */}
      <div style={{ backgroundColor: '#FFFFFF', borderRadius: '16px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        {isLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
            <LoadingSpinner size="lg" />
          </div>
        ) : filteredItems.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#64748B' }}>
            <p style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>No hay eventos que coincidan con el criterio seleccionado.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0', color: '#475569', fontWeight: 700 }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Fecha / Hora</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Tipo de Evento</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Resultado</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Actor / Origen IP</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Recurso Afectado</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Institución Contexto</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Trazabilidad</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.75rem 1rem', color: '#64748B', fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                      {item.occurred_at ? new Date(item.occurred_at).toLocaleString() : 'Reciente'}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span
                        style={{
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '0.2rem 0.5rem',
                          borderRadius: '4px',
                          backgroundColor: item.event_type.includes('DENIED') || item.event_type.includes('FAILED') ? '#FEE2E2' : '#F1F5F9',
                          color: item.event_type.includes('DENIED') || item.event_type.includes('FAILED') ? '#991B1B' : '#1E293B',
                        }}
                      >
                        {item.event_type}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '0.2rem 0.5rem',
                          borderRadius: '9999px',
                          backgroundColor: item.success ? '#DCFCE7' : '#FEE2E2',
                          color: item.success ? '#15803D' : '#991B1B',
                        }}
                      >
                        {item.success ? '✓ ÉXITO' : '✕ DENEGADO'}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <div style={{ color: '#0F172A', fontWeight: 600, fontSize: '0.8125rem' }}>
                        {item.actor_ip || 'IP Interna'}
                      </div>
                      <div style={{ color: '#475569', fontSize: '0.7rem', fontFamily: 'monospace' }}>
                        {item.actor_id ? `ID: ${item.actor_id.substring(0, 12)}...` : 'Anónimo / Sistema'}
                      </div>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: '#475569', fontSize: '0.8125rem' }}>
                      {item.target_type ? `${item.target_type}: ${item.target_id || ''}` : 'Plataforma Global'}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: '#64748B', fontSize: '0.75rem', fontFamily: 'monospace' }}>
                      {item.institution_id ? item.institution_id.substring(0, 8) + '...' : 'Global'}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setSelectedItem(item)}
                      >
                        Ver Metadatos
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Metadata Detail Modal */}
      {selectedItem && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '1rem' }}>
          <div style={{ backgroundColor: '#FFFFFF', borderRadius: '16px', maxWidth: '600px', width: '100%', padding: '2rem', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: '0 0 0.5rem 0', color: '#0F172A' }}>
              Metadatos del Evento de Auditoría
            </h3>
            <p style={{ color: '#64748B', fontSize: '0.8125rem', margin: '0 0 1rem 0' }}>
              UUID: <span style={{ fontFamily: 'monospace' }}>{selectedItem.id}</span>
            </p>

            <div style={{ backgroundColor: '#0F172A', color: '#38BDF8', padding: '1rem', borderRadius: '8px', fontSize: '0.8125rem', fontFamily: 'monospace', overflowX: 'auto', maxHeight: '300px' }}>
              <pre style={{ margin: 0 }}>
                {JSON.stringify(selectedItem.metadata || {}, null, 2)}
              </pre>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
              <Button variant="primary" onClick={() => setSelectedItem(null)}>
                Entendido
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
