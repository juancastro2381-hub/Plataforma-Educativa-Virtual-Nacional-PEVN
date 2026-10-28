/**
 * PEVN Frontend — Institutional Communications View (Comunicaciones Oficiales)
 *
 * Professional circular and institutional announcements inspection interface.
 * Protected by RBAC permission: 'communications:read'.
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
  CommunicationCategory,
  CommunicationPriority,
  InstitutionalCommunicationDetail,
  InstitutionalCommunicationItem,
} from '@/types/communication'

export const CommunicationsView: React.FC = () => {
  const { user } = useAuth()

  const [communications, setCommunications] = useState<InstitutionalCommunicationItem[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [categoryFilter, setCategoryFilter] = useState<CommunicationCategory | ''>('')
  const [priorityFilter, setPriorityFilter] = useState<CommunicationPriority | ''>('')
  const [error, setError] = useState<string | null>(null)

  // Selected Detail Modal
  const [selectedComm, setSelectedComm] = useState<InstitutionalCommunicationDetail | null>(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false)
  const [isDetailOpen, setIsDetailOpen] = useState<boolean>(false)

  const loadCommunications = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await communicationApi.listCommunications({
        category: categoryFilter || undefined,
        priority: priorityFilter || undefined,
      })
      setCommunications(res.items)
      setTotal(res.total)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cargar comunicados institucionales.')
    } finally {
      setIsLoading(false)
    }
  }, [categoryFilter, priorityFilter])

  useEffect(() => {
    void loadCommunications()
  }, [loadCommunications])

  const handleOpenDetail = async (commId: string) => {
    setIsLoadingDetail(true)
    setIsDetailOpen(true)
    try {
      const detail = await communicationApi.getCommunicationById(commId)
      setSelectedComm(detail)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cargar detalle del comunicado.')
      setIsDetailOpen(false)
    } finally {
      setIsLoadingDetail(false)
    }
  }

  const formatPriority = (p: CommunicationPriority) => {
    switch (p) {
      case 'URGENTE':
        return <Badge variant="danger">🔴 Urgente</Badge>
      case 'ALTA':
        return <Badge variant="warning">🟠 Alta</Badge>
      case 'MEDIA':
        return <Badge variant="primary">🟡 Media</Badge>
      case 'BAJA':
        return <Badge variant="neutral">⚪ Baja</Badge>
      default:
        return <Badge variant="neutral">{p}</Badge>
    }
  }

  const formatCategory = (cat: CommunicationCategory) => {
    const map: Record<CommunicationCategory, string> = {
      CIRCULAR_INFORMATIVA: 'Circular Informativa',
      CONVOCATORIA_ACUDIENTES: 'Convocatoria a Padres',
      RESOLUCION_RECTORAL: 'Resolución Rectoral',
      CRONOGRAMA_ACADEMICO: 'Cronograma Académico',
      EMERGENCIA_SANITARIA: 'Emergencia / Contingencia',
      EVENTO_INSTITUCIONAL: 'Evento Institucional',
      OTRO: 'General',
    }
    return map[cat] || cat
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '2rem auto', padding: '0 1rem' }} id="communications-page">
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
              Comunicaciones • Circulares Oficiales
            </span>
            {user?.scope.jurisdiction_name && (
              <Badge variant="neutral">
                Jurisdicción: {user.scope.jurisdiction_name}
              </Badge>
            )}
          </div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 800, margin: '0.25rem 0', color: '#FFFFFF' }}>
            Comunicaciones y Circulares
          </h1>
          <p style={{ color: '#CBD5E1', fontSize: '0.9375rem', margin: 0, maxWidth: '650px' }}>
            Supervisión y consulta de comunicados oficiales, directivas y convocatorias emitidas a la comunidad.
          </p>
        </div>

        <div>
          <Button
            variant="secondary"
            onClick={() => void loadCommunications()}
            id="btn-refresh-communications"
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
              htmlFor="comm-category-select"
              style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Categoría
            </label>
            <select
              id="comm-category-select"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value as CommunicationCategory | '')}
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
              <option value="">Todas las Categorías</option>
              <option value="CIRCULAR_INFORMATIVA">Circular Informativa</option>
              <option value="CONVOCATORIA_ACUDIENTES">Convocatoria a Padres</option>
              <option value="RESOLUCION_RECTORAL">Resolución Rectoral</option>
              <option value="CRONOGRAMA_ACADEMICO">Cronograma Académico</option>
              <option value="EMERGENCIA_SANITARIA">Emergencia / Contingencia</option>
              <option value="EVENTO_INSTITUCIONAL">Evento Institucional</option>
              <option value="OTRO">General</option>
            </select>
          </div>

          <div style={{ width: '200px' }}>
            <label
              htmlFor="comm-priority-select"
              style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Prioridad
            </label>
            <select
              id="comm-priority-select"
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value as CommunicationPriority | '')}
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
              <option value="">Todas las Prioridades</option>
              <option value="URGENTE">Urgente</option>
              <option value="ALTA">Alta</option>
              <option value="MEDIA">Media</option>
              <option value="BAJA">Baja</option>
            </select>
          </div>

          {(categoryFilter || priorityFilter) && (
            <Button
              variant="secondary"
              onClick={() => {
                setCategoryFilter('')
                setPriorityFilter('')
              }}
            >
              Limpiar Filtros
            </Button>
          )}
        </div>
      </Card>

      {/* Communications Table */}
      <Card
        title="Circulares y Comunicados Emitidos"
        subtitle={`Total de comunicados registrados: ${String(total)}`}
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando comunicados oficiales...
            </p>
          </div>
        ) : communications.length === 0 ? (
          <EmptyState
            icon="📢"
            title="No se encontraron comunicados"
            description="No hay circulares o comunicaciones oficiales registradas con los filtros seleccionados."
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table
              id="communications-table"
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '0.875rem',
                textAlign: 'left',
              }}
            >
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Título</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Categoría</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Prioridad</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Publicación</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Acuse Obligatorio</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {communications.map((c) => (
                  <tr
                    key={c.id}
                    id={`comm-row-${c.id}`}
                    style={{
                      borderBottom: '1px solid #F1F5F9',
                      transition: 'background-color 150ms',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8FAFC')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <td style={{ padding: '1rem', fontWeight: 700, color: '#0F172A' }}>
                      <div>{c.title}</div>
                      {c.summary && (
                        <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 400, marginTop: '0.2rem' }}>
                          {c.summary}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '1rem', color: '#334155' }}>
                      {formatCategory(c.category)}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      {formatPriority(c.priority)}
                    </td>
                    <td style={{ padding: '1rem', color: '#475569', fontSize: '0.8125rem' }}>
                      {c.published_at ? new Date(c.published_at).toLocaleDateString('es-CO') : 'Borrador'}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'center' }}>
                      <Badge variant={c.requires_acknowledgment ? 'warning' : 'neutral'}>
                        {c.requires_acknowledgment ? 'Sí (Obligatorio)' : 'No'}
                      </Badge>
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      <Button
                        variant="ghost"
                        size="sm"
                        id={`btn-view-comm-${c.id}`}
                        onClick={() => void handleOpenDetail(c.id)}
                      >
                        👁️ Leer Circular
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Detail Modal */}
      {isDetailOpen && (
        <Modal
          isOpen={isDetailOpen}
          onClose={() => {
            setIsDetailOpen(false)
            setSelectedComm(null)
          }}
          title={selectedComm?.title || 'Detalle del Comunicado'}
          subtitle={selectedComm?.category ? formatCategory(selectedComm.category) : undefined}
        >
          {isLoadingDetail || !selectedComm ? (
            <div style={{ padding: '2rem', textAlign: 'center' }}>
              <LoadingSpinner size="md" />
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', fontSize: '0.875rem' }}>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                {formatPriority(selectedComm.priority)}
                <Badge variant={selectedComm.status === 'PUBLICADO' ? 'success' : 'neutral'}>
                  {selectedComm.status}
                </Badge>
                {selectedComm.published_at && (
                  <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                    Publicado: {new Date(selectedComm.published_at).toLocaleString('es-CO')}
                  </span>
                )}
              </div>

              {selectedComm.summary && (
                <div style={{ backgroundColor: '#F8FAFC', padding: '0.75rem 1rem', borderRadius: '8px', borderLeft: '4px solid #3B82F6', fontStyle: 'italic', color: '#334155' }}>
                  {selectedComm.summary}
                </div>
              )}

              <div>
                <span style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#64748B', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                  Contenido Oficial
                </span>
                <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, color: '#0F172A', backgroundColor: '#FFFFFF', padding: '1rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                  {selectedComm.content}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', borderTop: '1px solid #E2E8F0', paddingTop: '1rem' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>DESTINATARIOS / AUDIENCIAS</span>
                  <p style={{ margin: '0.25rem 0', fontWeight: 600, color: '#0F172A' }}>
                    {selectedComm.audiences?.length || 0} segmentos configurados
                  </p>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>MÉTRICAS DE LECTURA</span>
                  <p style={{ margin: '0.25rem 0', fontWeight: 600, color: '#0F172A' }}>
                    {selectedComm.acknowledgments_count ?? 0} acuses ({selectedComm.reads_count ?? 0} lecturas)
                  </p>
                </div>
              </div>
            </div>
          )}
        </Modal>
      )}
    </div>
  )
}

export default CommunicationsView
