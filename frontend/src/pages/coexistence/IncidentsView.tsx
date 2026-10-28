/**
 * PEVN Frontend — School Coexistence Incidents View (Observador del Estudiante - Ley 1620)
 *
 * Professional inspection view for school coexistence cases, due-process guarantees,
 * restorative pedagogical commitments, and disciplinary monitoring.
 * Protected by RBAC permission: 'incidents:read'.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { communicationApi } from '@/services/communication'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Modal } from '@/components/ui/Modal'
import { useAuth } from '@/hooks/useAuth'
import type {
  CoexistenceSituationType,
  IncidentStatus,
  StudentIncidentItem,
} from '@/types/communication'

export const IncidentsView: React.FC = () => {
  const { user } = useAuth()

  const [incidents, setIncidents] = useState<StudentIncidentItem[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [situationFilter, setSituationFilter] = useState<CoexistenceSituationType | ''>('')
  const [statusFilter, setStatusFilter] = useState<IncidentStatus | ''>('')
  const [error, setError] = useState<string | null>(null)

  // Selected Incident Detail Modal
  const [selectedIncident, setSelectedIncident] = useState<StudentIncidentItem | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState<boolean>(false)
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false)

  const loadIncidents = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await communicationApi.getIncidents({
        situation_type: situationFilter || undefined,
        status: statusFilter || undefined,
      })
      setIncidents(res.items)
      setTotal(res.total)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cargar registros de convivencia.')
    } finally {
      setIsLoading(false)
    }
  }, [situationFilter, statusFilter])

  useEffect(() => {
    void loadIncidents()
  }, [loadIncidents])

  const handleOpenDetail = async (incidentId: string) => {
    setIsLoadingDetail(true)
    setIsDetailOpen(true)
    try {
      const detail = await communicationApi.getIncidentById(incidentId)
      setSelectedIncident(detail)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cargar detalle del incidente.')
      setIsDetailOpen(false)
    } finally {
      setIsLoadingDetail(false)
    }
  }

  const formatSituationBadge = (type: CoexistenceSituationType) => {
    switch (type) {
      case 'TIPO_I':
        return <Badge variant="warning">Tipo I (Conflicto Cotidiano)</Badge>
      case 'TIPO_II':
        return <Badge variant="danger">Tipo II (Acoso / Agresión)</Badge>
      case 'TIPO_III':
        return <Badge variant="danger">Tipo III (Vulneración Grave / Delito)</Badge>
      default:
        return <Badge variant="neutral">{type}</Badge>
    }
  }

  const formatStatusBadge = (status: IncidentStatus) => {
    switch (status) {
      case 'ABIERTO':
        return <Badge variant="warning">Abierto</Badge>
      case 'EN_SEGUIMIENTO':
        return <Badge variant="primary">En Seguimiento</Badge>
      case 'CERRADO':
        return <Badge variant="success">Cerrado / Resuelto</Badge>
      default:
        return <Badge variant="neutral">{status}</Badge>
    }
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '2rem auto', padding: '0 1rem' }} id="coexistence-incidents-page">
      {/* Header Banner */}
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
              Convivencia Escolar • Ley 1620 de 2013
            </span>
            {user?.scope.jurisdiction_name && (
              <Badge variant="neutral">
                Jurisdicción: {user.scope.jurisdiction_name}
              </Badge>
            )}
          </div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 800, margin: '0.25rem 0', color: '#FFFFFF' }}>
            Observador y Convivencia Escolar
          </h1>
          <p style={{ color: '#CBD5E1', fontSize: '0.9375rem', margin: 0, maxWidth: '650px' }}>
            Registro e inspección de situaciones de convivencia, rutas formativas y compromisos pedagógicos restaurativos.
          </p>
        </div>

        <div>
          <Button
            variant="secondary"
            onClick={() => void loadIncidents()}
            id="btn-refresh-incidents"
            style={{
              borderColor: '#475569',
              color: '#E2E8F0',
              fontWeight: 600,
              padding: '0.65rem 1.25rem',
            }}
          >
            🔄 Actualizar
          </Button>
        </div>
      </div>

      {error && (
        <div style={{ marginBottom: '1.5rem', color: '#DC2626', fontSize: '0.875rem' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Filters Card */}
      <Card style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ width: '250px' }}>
            <label
              htmlFor="situation-type-select"
              style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Tipo de Situación (Ley 1620)
            </label>
            <select
              id="situation-type-select"
              value={situationFilter}
              onChange={(e) => setSituationFilter(e.target.value as CoexistenceSituationType | '')}
              style={{
                width: '100%',
                padding: '0.55rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                color: '#0F172A',
              }}
            >
              <option value="">Todas las Situaciones</option>
              <option value="TIPO_I">Tipo I (Conflictos cotidianos)</option>
              <option value="TIPO_II">Tipo II (Acoso / Agresión física)</option>
              <option value="TIPO_III">Tipo III (Vulneración grave / Delito)</option>
            </select>
          </div>

          <div style={{ width: '200px' }}>
            <label
              htmlFor="incident-status-select"
              style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Estado del Caso
            </label>
            <select
              id="incident-status-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as IncidentStatus | '')}
              style={{
                width: '100%',
                padding: '0.55rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                backgroundColor: '#FFFFFF',
                color: '#0F172A',
              }}
            >
              <option value="">Todos los Estados</option>
              <option value="ABIERTO">Abierto</option>
              <option value="EN_SEGUIMIENTO">En Seguimiento</option>
              <option value="CERRADO">Cerrado</option>
            </select>
          </div>

          {(situationFilter || statusFilter) && (
            <Button
              variant="secondary"
              onClick={() => {
                setSituationFilter('')
                setStatusFilter('')
              }}
            >
              Limpiar Filtros
            </Button>
          )}
        </div>
      </Card>

      {/* Incidents Table */}
      <Card
        title="Casos y Situaciones Registradas"
        subtitle={`Total de registros en Observador: ${String(total)}`}
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando situaciones de convivencia...
            </p>
          </div>
        ) : incidents.length === 0 ? (
          <EmptyState
            icon="🤝"
            title="Sin situaciones registradas"
            description="No hay anotaciones de convivencia registradas para los filtros aplicados en esta institución."
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table
              id="incidents-table"
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '0.875rem',
                textAlign: 'left',
              }}
            >
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Fecha Hechos</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Estudiante / Grupo</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Clasificación Ley 1620</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Estado</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Docente Reportante</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((inc) => (
                  <tr
                    key={inc.id}
                    id={`incident-row-${inc.id}`}
                    style={{
                      borderBottom: '1px solid #F1F5F9',
                      transition: 'background-color 150ms',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8FAFC')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <td style={{ padding: '1rem', fontWeight: 600, color: '#0F172A' }}>
                      {inc.incident_date ? new Date(inc.incident_date).toLocaleDateString('es-CO') : 'N/A'}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ fontWeight: 700, color: '#0F172A' }}>{inc.student_name || 'Estudiante'}</div>
                      <div style={{ fontSize: '0.75rem', color: '#64748B' }}>{inc.student_document ? `Doc: ${inc.student_document}` : 'SIMAT'}</div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      {formatSituationBadge(inc.situation_type)}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      {formatStatusBadge(inc.status)}
                    </td>
                    <td style={{ padding: '1rem', color: '#475569', fontSize: '0.8125rem' }}>
                      {inc.reporter_name || 'Docente'}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      <Button
                        variant="ghost"
                        size="sm"
                        id={`btn-view-incident-${inc.id}`}
                        onClick={() => void handleOpenDetail(inc.id)}
                      >
                        👁️ Ver Expediente
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Incident Detail Modal */}
      {selectedIncident && (
        <Modal
          isOpen={isDetailOpen}
          onClose={() => {
            setIsDetailOpen(false)
            setSelectedIncident(null)
          }}
          title={`Expediente Convivencial: ${selectedIncident.student_name || 'Estudiante'}`}
          subtitle={`Fecha de los hechos: ${
            selectedIncident.incident_date ? new Date(selectedIncident.incident_date).toLocaleDateString('es-CO') : ''
          }`}
        >
          {isLoadingDetail ? (
            <div style={{ padding: '2rem', textAlign: 'center' }}>
              <LoadingSpinner size="md" />
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', fontSize: '0.875rem' }}>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                {formatSituationBadge(selectedIncident.situation_type)}
                {formatStatusBadge(selectedIncident.status)}
              </div>

              <div>
                <span style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#64748B', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
                  Relato de los Hechos (Observador)
                </span>
                <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px', border: '1px solid #E2E8F0', color: '#1E293B', lineHeight: 1.6 }}>
                  {selectedIncident.description}
                </div>
              </div>

              {selectedIncident.pedagogical_measures && (
                <div>
                  <span style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#64748B', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
                    Medidas Pedagógicas Aplicadas
                  </span>
                  <div style={{ backgroundColor: '#F0FDF4', padding: '0.75rem 1rem', borderRadius: '8px', borderLeft: '4px solid #10B981', color: '#166534' }}>
                    {selectedIncident.pedagogical_measures}
                  </div>
                </div>
              )}

              {selectedIncident.commitments && (
                <div>
                  <span style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#64748B', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
                    Compromisos Restaurativos y Pedagógicos
                  </span>
                  <div style={{ backgroundColor: '#EFF6FF', padding: '0.75rem 1rem', borderRadius: '8px', borderLeft: '4px solid #3B82F6', color: '#1E40AF' }}>
                    {selectedIncident.commitments}
                  </div>
                </div>
              )}

              {selectedIncident.follow_ups && selectedIncident.follow_ups.length > 0 && (
                <div>
                  <span style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#64748B', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                    Bitácora de Seguimientos Pedagógicos ({selectedIncident.follow_ups.length})
                  </span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {selectedIncident.follow_ups.map((fu, idx) => (
                      <div key={idx} style={{ padding: '0.75rem', borderRadius: '6px', backgroundColor: '#F8FAFC', border: '1px solid #E2E8F0' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748B', marginBottom: '0.25rem' }}>
                          <span>{fu.author_name || 'Orientador / Coordinador'}</span>
                          <span>{fu.created_at ? new Date(fu.created_at).toLocaleDateString('es-CO') : ''}</span>
                        </div>
                        <p style={{ margin: 0, color: '#1E293B' }}>{fu.notes}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Modal>
      )}
    </div>
  )
}

export default IncidentsView
