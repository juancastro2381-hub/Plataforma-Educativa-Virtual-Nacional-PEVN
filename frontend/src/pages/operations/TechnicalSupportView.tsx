/**
 * PEVN Frontend — Technical Support & Incident Center
 *
 * Dedicated operational incident management for SUPER_ADMIN (Level 100).
 * Handles support tickets, triage, severity escalation, and resolution tracking.
 */

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Button } from '@/components/ui/Button'
import {
  operationsApi,
  type TechnicalIncident,
  type TechnicalIncidentCreatePayload,
} from '@/services/operations'

export const TechnicalSupportView: React.FC = () => {
  const [incidents, setIncidents] = useState<TechnicalIncident[]>([])
  const [openCount, setOpenCount] = useState(0)
  const [criticalCount, setCriticalCount] = useState(0)
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [severityFilter, setSeverityFilter] = useState<string>('')

  // Create Modal State
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState<TechnicalIncidentCreatePayload>({
    title: '',
    category: 'INFRASTRUCTURE',
    severity: 'MEDIUM',
    affected_service: 'api_gateway',
    description: '',
    assigned_operator: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Resolve / Status Update Modal State
  const [selectedIncident, setSelectedIncident] = useState<TechnicalIncident | null>(null)
  const [updateStatus, setUpdateStatus] = useState<string>('')
  const [resolutionNotes, setResolutionNotes] = useState<string>('')

  const loadIncidents = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await operationsApi.listSupportCases({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
      })
      setIncidents(data.items)
      setOpenCount(data.open_count)
      setCriticalCount(data.critical_count)
      setTotal(data.total)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar incidentes técnicos.'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadIncidents()
  }, [statusFilter, severityFilter])

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!createForm.title || !createForm.description) return
    setIsSubmitting(true)
    try {
      await operationsApi.createSupportCase(createForm)
      setIsCreateOpen(false)
      setCreateForm({
        title: '',
        category: 'INFRASTRUCTURE',
        severity: 'MEDIUM',
        affected_service: 'api_gateway',
        description: '',
        assigned_operator: '',
      })
      await loadIncidents()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al registrar el incidente.'
      setError(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdateStatus = async () => {
    if (!selectedIncident) return
    setIsSubmitting(true)
    try {
      await operationsApi.updateSupportCase(selectedIncident.id, {
        status: updateStatus || undefined,
        resolution_notes: resolutionNotes || undefined,
      })
      setSelectedIncident(null)
      await loadIncidents()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al actualizar el estado.'
      setError(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return { bg: '#FEE2E2', text: '#991B1B', border: '#FCA5A5' }
      case 'HIGH':
        return { bg: '#FFEDD5', text: '#C2410C', border: '#FDBA74' }
      case 'MEDIUM':
        return { bg: '#FEF9C3', text: '#854D0E', border: '#FDE047' }
      case 'LOW':
      default:
        return { bg: '#E0F2FE', text: '#0369A1', border: '#7DD3FC' }
    }
  }

  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'OPEN':
        return { bg: '#FEE2E2', text: '#B91C1C' }
      case 'INVESTIGATING':
        return { bg: '#FEF3C7', text: '#B45309' }
      case 'MITIGATED':
        return { bg: '#DBEAFE', text: '#1D4ED8' }
      case 'RESOLVED':
      case 'CLOSED':
        return { bg: '#DCFCE7', text: '#15803D' }
      default:
        return { bg: '#F1F5F9', text: '#475569' }
    }
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
              🛠 CENTRO DE SOPORTE TÉCNICO • L100
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0 0 0.5rem 0', color: '#FFFFFF' }}>
            Mesa de Ayuda Técnica e Incidentes de Plataforma
          </h1>
          <p style={{ color: '#94A3B8', fontSize: '0.875rem', margin: 0, maxWidth: '750px' }}>
            Gestión de incidencias operacionales, degradación de servicios, tickets de soporte de infraestructura y ciclo de vida de mitigación.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <Button
            variant="secondary"
            onClick={() => void loadIncidents()}
            disabled={isLoading}
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
              color: '#FFFFFF',
              border: '1px solid rgba(255, 255, 255, 0.3)',
            }}
          >
            {isLoading ? 'Cargando...' : '🔄 Refrescar'}
          </Button>
          <Button
            variant="primary"
            onClick={() => setIsCreateOpen(true)}
            data-testid="btn-open-create-incident"
          >
            + Registrar Incidente
          </Button>
          <Link to="/dashboard">
            <Button
              variant="secondary"
              style={{
                backgroundColor: 'transparent',
                color: '#94A3B8',
                border: '1px solid #334155',
              }}
            >
              ← Volver
            </Button>
          </Link>
        </div>
      </div>

      {error && (
        <div style={{ padding: '1rem 1.5rem', backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '12px', color: '#991B1B', marginBottom: '1.5rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* KPI Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        <div style={{ backgroundColor: '#FFFFFF', padding: '1.25rem', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
            Total Tickets Registrados
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', marginTop: '0.25rem' }}>
            {total}
          </div>
        </div>

        <div style={{ backgroundColor: '#FFFFFF', padding: '1.25rem', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#B91C1C', textTransform: 'uppercase' }}>
            Incidentes Abiertos / En Curso
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#B91C1C', marginTop: '0.25rem' }}>
            {openCount}
          </div>
        </div>

        <div style={{ backgroundColor: '#FFFFFF', padding: '1.25rem', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#991B1B', textTransform: 'uppercase' }}>
            Severidad Crítica Activa
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: criticalCount > 0 ? '#991B1B' : '#166534', marginTop: '0.25rem' }}>
            {criticalCount}
          </div>
        </div>
      </div>

      {/* Controls / Filter Bar */}
      <div style={{ backgroundColor: '#FFFFFF', padding: '1.25rem', borderRadius: '12px', border: '1px solid #E2E8F0', marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <div>
          <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#475569', marginRight: '0.5rem' }}>
            Estado:
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ padding: '0.4rem 0.75rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
          >
            <option value="">Todos los Estados</option>
            <option value="OPEN">OPEN (Abierto)</option>
            <option value="INVESTIGATING">INVESTIGATING (En Investigación)</option>
            <option value="MITIGATED">MITIGATED (Mitigado)</option>
            <option value="RESOLVED">RESOLVED (Resuelto)</option>
            <option value="CLOSED">CLOSED (Cerrado)</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#475569', marginRight: '0.5rem' }}>
            Severidad:
          </label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{ padding: '0.4rem 0.75rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
          >
            <option value="">Todas las Severidades</option>
            <option value="CRITICAL">CRÍTICA</option>
            <option value="HIGH">ALTA</option>
            <option value="MEDIUM">MEDIA</option>
            <option value="LOW">BAJA</option>
          </select>
        </div>
      </div>

      {/* Incidents Table */}
      <div style={{ backgroundColor: '#FFFFFF', borderRadius: '16px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        {isLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
            <LoadingSpinner size="lg" />
          </div>
        ) : incidents.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#64748B' }}>
            <p style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>No hay incidentes técnicos que coincidan con el filtro.</p>
            <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.875rem' }}>Todos los servicios operan dentro de los parámetros esperados.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0', color: '#475569', fontWeight: 700 }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Ticket</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Severidad</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Título / Asunto</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Servicio</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Estado</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Operador</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Fecha</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((inc) => {
                  const sevStyle = getSeverityStyle(inc.severity)
                  const stStyle = getStatusStyle(inc.status)
                  return (
                    <tr key={inc.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                      <td style={{ padding: '0.75rem 1rem', fontFamily: 'monospace', fontWeight: 700, color: '#0F172A' }}>
                        {inc.ticket_number}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span
                          style={{
                            padding: '0.2rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            backgroundColor: sevStyle.bg,
                            color: sevStyle.text,
                            border: `1px solid ${sevStyle.border}`,
                          }}
                        >
                          {inc.severity}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem', maxWidth: '300px' }}>
                        <div style={{ fontWeight: 600, color: '#0F172A' }}>{inc.title}</div>
                        <div style={{ fontSize: '0.75rem', color: '#64748B', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {inc.description}
                        </div>
                      </td>
                      <td style={{ padding: '0.75rem 1rem', color: '#475569' }}>
                        <span style={{ backgroundColor: '#F1F5F9', padding: '0.2rem 0.4rem', borderRadius: '4px', fontSize: '0.75rem' }}>
                          {inc.affected_service}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span
                          style={{
                            padding: '0.2rem 0.5rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            backgroundColor: stStyle.bg,
                            color: stStyle.text,
                          }}
                        >
                          {inc.status}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem', color: '#475569' }}>
                        {inc.assigned_operator || 'Sin asignar'}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', color: '#64748B', fontSize: '0.75rem' }}>
                        {new Date(inc.created_at).toLocaleString()}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            setSelectedIncident(inc)
                            setUpdateStatus(inc.status)
                            setResolutionNotes(inc.resolution_notes || '')
                          }}
                        >
                          Gestionar
                        </Button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {isCreateOpen && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '1rem' }}>
          <div style={{ backgroundColor: '#FFFFFF', borderRadius: '16px', maxWidth: '540px', width: '100%', padding: '2rem', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: '0 0 1rem 0', color: '#0F172A' }}>
              Registrar Nuevo Incidente Técnico
            </h3>
            <form onSubmit={handleCreateTicket} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Título del Incidente *
                </label>
                <input
                  type="text"
                  required
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  placeholder="Ej: Latencia elevada en endpoints de autenticación"
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Severidad *
                  </label>
                  <select
                    value={createForm.severity}
                    onChange={(e) => setCreateForm({ ...createForm, severity: e.target.value })}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                  >
                    <option value="CRITICAL">CRITICAL (Crítica)</option>
                    <option value="HIGH">HIGH (Alta)</option>
                    <option value="MEDIUM">MEDIUM (Media)</option>
                    <option value="LOW">LOW (Baja)</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Categoría *
                  </label>
                  <select
                    value={createForm.category}
                    onChange={(e) => setCreateForm({ ...createForm, category: e.target.value })}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                  >
                    <option value="INFRASTRUCTURE">INFRASTRUCTURE</option>
                    <option value="SECURITY">SECURITY</option>
                    <option value="PERFORMANCE">PERFORMANCE</option>
                    <option value="INTEGRATION">INTEGRATION</option>
                    <option value="DATABASE">DATABASE</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Servicio Afectado *
                  </label>
                  <input
                    type="text"
                    required
                    value={createForm.affected_service}
                    onChange={(e) => setCreateForm({ ...createForm, affected_service: e.target.value })}
                    placeholder="api_gateway, db_primary, etc."
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                    Operador Asignado
                  </label>
                  <input
                    type="text"
                    value={createForm.assigned_operator || ''}
                    onChange={(e) => setCreateForm({ ...createForm, assigned_operator: e.target.value })}
                    placeholder="ops-oncall@pevn.gov.co"
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Descripción Técnica Sanitizada *
                </label>
                <textarea
                  required
                  rows={4}
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  placeholder="Detalles técnicos, logs anonimizados, síntomas observados..."
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <Button variant="secondary" type="button" onClick={() => setIsCreateOpen(false)}>
                  Cancelar
                </Button>
                <Button variant="primary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Registrando...' : 'Confirmar Registro'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Update / Resolve Modal */}
      {selectedIncident && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '1rem' }}>
          <div style={{ backgroundColor: '#FFFFFF', borderRadius: '16px', maxWidth: '540px', width: '100%', padding: '2rem', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: '0 0 0.5rem 0', color: '#0F172A' }}>
              Gestión de Incidente {selectedIncident.ticket_number}
            </h3>
            <p style={{ color: '#64748B', fontSize: '0.875rem', margin: '0 0 1rem 0' }}>
              {selectedIncident.title}
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Actualizar Estado Operacional
                </label>
                <select
                  value={updateStatus}
                  onChange={(e) => setUpdateStatus(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                >
                  <option value="OPEN">OPEN (Abierto)</option>
                  <option value="INVESTIGATING">INVESTIGATING (En Investigación)</option>
                  <option value="MITIGATED">MITIGATED (Mitigado)</option>
                  <option value="RESOLVED">RESOLVED (Resuelto)</option>
                  <option value="CLOSED">CLOSED (Cerrado)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Notas de Mitigación / Resolución
                </label>
                <textarea
                  rows={4}
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="Detalles de la causa raíz, acciones correctivas aplicadas y evidencia..."
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <Button variant="secondary" type="button" onClick={() => setSelectedIncident(null)}>
                  Cerrar
                </Button>
                <Button variant="primary" type="button" onClick={() => void handleUpdateStatus()} disabled={isSubmitting}>
                  {isSubmitting ? 'Guardando...' : 'Actualizar Incidente'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
