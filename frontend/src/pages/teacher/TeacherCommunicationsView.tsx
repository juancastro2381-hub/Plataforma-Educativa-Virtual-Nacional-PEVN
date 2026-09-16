/**
 * PEVN Frontend — Teacher Communications View (Phase 15 / B2)
 *
 * Official institutional circulars, administrative directives, and pedagogical bulletins for educators.
 * Features:
 * - Deterministic Active Feed adhering to teacher scope & institution tenant
 * - Read / Unread Visual Differentiation
 * - Category and Priority Badges with Expiration Indicators
 * - Full Content Modal Inspection
 * - Unforgeable Read & Formal Acknowledgment ("Confirmar Lectura") for mandatory circulars
 * - Loading, Empty, and Error States
 */

import React, { useEffect, useState } from 'react'
import { communicationApi } from '@/services/communication'
import type { InstitutionalCommunicationItem } from '@/types/communication'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

interface Props {
  teacherName?: string
}

const CATEGORY_LABELS: Record<string, { label: string; icon: string }> = {
  CIRCULAR_OFICIAL: { label: 'Circular Oficial', icon: '📜' },
  CIRCULAR_INFORMATIVA: { label: 'Circular Informativa', icon: '📄' },
  CONVOCATORIA_REUNION: { label: 'Convocatoria de Reunión', icon: '👥' },
  CONVOCATORIA_ACUDIENTES: { label: 'Convocatoria Familias', icon: '👨‍👩‍👧' },
  AVISO_ACADEMICO: { label: 'Aviso Académico', icon: '📚' },
  AVISO_ADMINISTRATIVO: { label: 'Aviso Administrativo', icon: '🏢' },
  RECORDATORIO: { label: 'Recordatorio Institucional', icon: '⏰' },
  EMERGENCIA_INSTITUCIONAL: { label: 'Emergencia Institucional', icon: '🚨' },
  RESOLUCION_RECTORAL: { label: 'Resolución Rectoral', icon: '⚖️' },
  CRONOGRAMA_ACADEMICO: { label: 'Cronograma Académico', icon: '📅' },
  EVENTO_INSTITUCIONAL: { label: 'Evento Institucional', icon: '🎉' },
  OTRO: { label: 'Otro Comunicado', icon: '📌' },
}

const PRIORITY_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  BAJA: { bg: '#F1F5F9', color: '#475569', border: '#CBD5E1' },
  MEDIA: { bg: '#EFF6FF', color: '#1D4ED8', border: '#BFDBFE' },
  ALTA: { bg: '#FEF3C7', color: '#B45309', border: '#FDE68A' },
  URGENTE: { bg: '#FEE2E2', color: '#B91C1C', border: '#FCA5A5' },
}

function getCategoryInfo(category: string): { label: string; icon: string } {
  return (CATEGORY_LABELS as Record<string, { label: string; icon: string } | undefined>)[category] ?? {
    label: category,
    icon: '📌',
  }
}

function getPriorityStyle(priority: string): { bg: string; color: string; border: string } {
  return (PRIORITY_STYLES as Record<string, { bg: string; color: string; border: string } | undefined>)[priority] ?? {
    bg: '#EFF6FF',
    color: '#1D4ED8',
    border: '#BFDBFE',
  }
}

export const TeacherCommunicationsView: React.FC<Props> = ({ teacherName: _teacherName }) => {
  const [communications, setCommunications] = useState<InstitutionalCommunicationItem[]>([])
  const [unreadCount, setUnreadCount] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL')
  const [selectedPriority, setSelectedPriority] = useState<string>('ALL')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedItem, setSelectedItem] = useState<InstitutionalCommunicationItem | null>(null)
  const [detailLoading, setDetailLoading] = useState<boolean>(false)
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null)
  const [ackSuccess, setAckSuccess] = useState<string | null>(null)

  const fetchCommunications = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await communicationApi.getTeacherCommunications()
      setCommunications(res.items)
      setUnreadCount(res.unread_count || 0)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar los comunicados institucionales.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchCommunications()
  }, [])

  const handleOpenDetail = async (item: InstitutionalCommunicationItem) => {
    setSelectedItem(item)
    setAckSuccess(null)
    // Fetch individual detail which idempotently registers read receipt on backend
    try {
      setDetailLoading(true)
      const detailed = await communicationApi.getTeacherCommunicationById(item.id)
      setSelectedItem(detailed)
      // Update item in local list as read
      setCommunications((prev) =>
        prev.map((c) =>
          c.id === item.id
            ? {
                ...c,
                has_read: true,
                is_read: true,
                read_at: detailed.read_at || new Date().toISOString(),
                acknowledged_at: detailed.acknowledged_at,
              }
            : c
        )
      )
      if (!item.has_read && !item.is_read) {
        setUnreadCount((prev) => Math.max(0, prev - 1))
      }
    } catch {
      // Keep selected item even if background detail refresh encounters minor issue
    } finally {
      setDetailLoading(false)
    }
  }

  const handleAcknowledge = async (item: InstitutionalCommunicationItem, e: React.MouseEvent) => {
    e.stopPropagation()
    setAcknowledgingId(item.id)
    setAckSuccess(null)
    try {
      const updated = await communicationApi.acknowledgeTeacherCommunication(item.id)
      const ackTimestamp = updated.acknowledged_at || new Date().toISOString()

      setCommunications((prev) =>
        prev.map((c) =>
          c.id === item.id
            ? {
                ...c,
                acknowledged_at: ackTimestamp,
                has_read: true,
                is_read: true,
                is_acknowledged: true,
              }
            : c
        )
      )

      if (selectedItem?.id === item.id) {
        setSelectedItem((prev) =>
          prev
            ? {
                ...prev,
                acknowledged_at: ackTimestamp,
                has_read: true,
                is_read: true,
                is_acknowledged: true,
              }
            : null
        )
      }

      setAckSuccess('Acuse de recibo registrado exitosamente.')
      setTimeout(() => { setAckSuccess(null); }, 4000)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al confirmar la lectura del comunicado.'
      alert(msg)
    } finally {
      setAcknowledgingId(null)
    }
  }

  // Filtering
  const filtered = communications.filter((item) => {
    const matchesCategory = selectedCategory === 'ALL' || item.category === selectedCategory
    const matchesPriority = selectedPriority === 'ALL' || item.priority === selectedPriority
    const matchesSearch =
      searchQuery.trim() === '' ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.summary && item.summary.toLowerCase().includes(searchQuery.toLowerCase())) ||
      item.content.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesPriority && matchesSearch
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Bar */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          border: '1px solid #E2E8F0',
          padding: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '1.5rem' }}>📢</span>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
              Comunicaciones Institucionales
            </h2>
            {unreadCount > 0 && (
              <span
                style={{
                  backgroundColor: '#EF4444',
                  color: '#FFFFFF',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '0.2rem 0.55rem',
                  borderRadius: '9999px',
                }}
              >
                {unreadCount} sin leer
              </span>
            )}
          </div>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#64748B' }}>
            Circulares oficiales, convocatorias y directrices emitidas por Rectoría y Coordinación para el cuerpo docente.
          </p>
        </div>

        <button
          onClick={() => void fetchCommunications()}
          disabled={loading}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#F8FAFC',
            border: '1px solid #CBD5E1',
            borderRadius: '8px',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: '#334155',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}
        >
          <span>🔄</span>
          <span>Actualizar</span>
        </button>
      </div>

      {/* Filters and Search Bar */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
          padding: '1rem 1.25rem',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '1rem',
          alignItems: 'center',
        }}
      >
        <div style={{ flex: '1 1 240px', minWidth: '220px' }}>
          <input
            type="text"
            placeholder="Buscar comunicado por título o contenido..."
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); }}
            style={{
              width: '100%',
              padding: '0.5rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              fontSize: '0.875rem',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#475569' }}>Categoría:</label>
          <select
            value={selectedCategory}
            onChange={(e) => { setSelectedCategory(e.target.value); }}
            style={{
              padding: '0.45rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              fontSize: '0.8125rem',
              backgroundColor: '#FFFFFF',
              color: '#334155',
              fontWeight: 500,
            }}
          >
            <option value="ALL">Todas las categorías</option>
            {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v.icon} {v.label}
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#475569' }}>Prioridad:</label>
          <select
            value={selectedPriority}
            onChange={(e) => { setSelectedPriority(e.target.value); }}
            style={{
              padding: '0.45rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              fontSize: '0.8125rem',
              backgroundColor: '#FFFFFF',
              color: '#334155',
              fontWeight: 500,
            }}
          >
            <option value="ALL">Todas las prioridades</option>
            <option value="URGENTE">Urgente</option>
            <option value="ALTA">Alta</option>
            <option value="MEDIA">Media</option>
            <option value="BAJA">Baja</option>
          </select>
        </div>
      </div>

      {/* Success Notification */}
      {ackSuccess && (
        <div
          style={{
            backgroundColor: '#DCFCE7',
            border: '1px solid #86EFAC',
            borderRadius: '10px',
            padding: '0.875rem 1.25rem',
            color: '#166534',
            fontSize: '0.875rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <span>✓</span>
          <span>{ackSuccess}</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div
          style={{
            backgroundColor: '#FEF2F2',
            border: '1px solid #FCA5A5',
            borderRadius: '10px',
            padding: '1rem 1.25rem',
            color: '#991B1B',
            fontSize: '0.875rem',
          }}
        >
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
          <LoadingSpinner />
          <p style={{ color: '#64748B', fontSize: '0.9rem', marginTop: '1rem' }}>
            Cargando comunicados institucionales...
          </p>
        </div>
      ) : filtered.length === 0 ? (
        /* Empty State */
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '3.5rem 1.5rem',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
          <h3 style={{ margin: '0 0 0.5rem 0', color: '#1E293B', fontWeight: 700 }}>
            No hay comunicados vigentes en esta selección
          </h3>
          <p style={{ margin: 0, color: '#64748B', fontSize: '0.875rem' }}>
            Los comunicados institucionales dirigidos a docentes aparecerán aquí cuando sean publicados por el equipo directivo.
          </p>
        </div>
      ) : (
        /* Cards Grid */
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
            gap: '1.25rem',
          }}
        >
          {filtered.map((item) => {
            const catInfo = getCategoryInfo(item.category)
            const pStyle = getPriorityStyle(item.priority)
            const isUnread = !item.has_read && !item.is_read
            const isAcknowledged = !!item.acknowledged_at || !!item.is_acknowledged
            const needsAck = item.requires_acknowledgment && !isAcknowledged

            return (
              <div
                key={item.id}
                onClick={() => void handleOpenDetail(item)}
                style={{
                  backgroundColor: '#FFFFFF',
                  borderRadius: '14px',
                  border: isUnread ? '2px solid #3B82F6' : '1px solid #E2E8F0',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: isUnread
                    ? '0 4px 12px rgba(59, 130, 246, 0.1)'
                    : '0 1px 3px rgba(0,0,0,0.04)',
                  cursor: 'pointer',
                  transition: 'transform 150ms, box-shadow 150ms',
                }}
              >
                <div>
                  {/* Top Badges */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '0.75rem',
                      flexWrap: 'wrap',
                      gap: '0.4rem',
                    }}
                  >
                    <span
                      style={{
                        backgroundColor: '#F1F5F9',
                        color: '#475569',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        padding: '0.25rem 0.55rem',
                        borderRadius: '6px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                      }}
                    >
                      {catInfo.icon} {catInfo.label}
                    </span>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      {isUnread && (
                        <span
                          style={{
                            backgroundColor: '#3B82F6',
                            color: '#FFFFFF',
                            fontSize: '0.6875rem',
                            fontWeight: 800,
                            padding: '0.2rem 0.5rem',
                            borderRadius: '9999px',
                            textTransform: 'uppercase',
                          }}
                        >
                          Nuevo
                        </span>
                      )}
                      <span
                        style={{
                          backgroundColor: pStyle.bg,
                          color: pStyle.color,
                          border: `1px solid ${pStyle.border}`,
                          fontSize: '0.6875rem',
                          fontWeight: 800,
                          padding: '0.2rem 0.5rem',
                          borderRadius: '6px',
                          textTransform: 'uppercase',
                        }}
                      >
                        {item.priority}
                      </span>
                    </div>
                  </div>

                  {/* Title */}
                  <h3
                    style={{
                      margin: '0 0 0.5rem 0',
                      fontSize: '1.0625rem',
                      fontWeight: 800,
                      color: '#0F172A',
                      lineHeight: 1.35,
                    }}
                  >
                    {item.is_pinned && <span style={{ marginRight: '0.3rem' }}>📌</span>}
                    {item.title}
                  </h3>

                  {/* Summary */}
                  <p
                    style={{
                      margin: '0 0 1rem 0',
                      fontSize: '0.875rem',
                      color: '#475569',
                      lineHeight: 1.5,
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}
                  >
                    {item.summary || item.content}
                  </p>
                </div>

                {/* Card Footer */}
                <div
                  style={{
                    borderTop: '1px solid #F1F5F9',
                    paddingTop: '0.75rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      fontSize: '0.75rem',
                      color: '#64748B',
                    }}
                  >
                    <span>✍️ {item.author_name}</span>
                    <span>
                      {item.published_at
                        ? new Date(item.published_at).toLocaleDateString('es-CO')
                        : 'Borrador'}
                    </span>
                  </div>

                  {/* Vigencia / Expiration if applicable */}
                  {item.expires_at && (
                    <div style={{ fontSize: '0.75rem', color: '#D97706' }}>
                      ⏳ Vigente hasta: {new Date(item.expires_at).toLocaleDateString('es-CO')}
                    </div>
                  )}

                  {/* Acknowledgment Action / Status */}
                  {needsAck ? (
                    <button
                      onClick={(e) => void handleAcknowledge(item, e)}
                      disabled={acknowledgingId === item.id}
                      style={{
                        marginTop: '0.25rem',
                        width: '100%',
                        backgroundColor: '#16A34A',
                        color: '#FFFFFF',
                        border: 'none',
                        borderRadius: '8px',
                        padding: '0.5rem',
                        fontSize: '0.8125rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.4rem',
                      }}
                    >
                      <span>✓</span>
                      <span>
                        {acknowledgingId === item.id
                          ? 'Registrando acuse...'
                          : 'Confirmar Lectura Obligatoria'}
                      </span>
                    </button>
                  ) : isAcknowledged ? (
                    <div
                      style={{
                        fontSize: '0.75rem',
                        color: '#16A34A',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        marginTop: '0.25rem',
                      }}
                    >
                      <span>✓</span>
                      <span>
                        Lectura confirmada
                        {item.acknowledged_at
                          ? ` el ${new Date(item.acknowledged_at).toLocaleDateString('es-CO')}`
                          : ''}
                      </span>
                    </div>
                  ) : null}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Detail Modal */}
      {selectedItem && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '1.25rem',
          }}
          onClick={() => { setSelectedItem(null); }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '20px',
              maxWidth: '720px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '2rem',
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)',
            }}
            onClick={(e) => { e.stopPropagation(); }}
          >
            {/* Modal Header */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '1rem',
                gap: '1rem',
              }}
            >
              <div>
                <span
                  style={{
                    backgroundColor: '#EFF6FF',
                    color: '#1D4ED8',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '0.25rem 0.6rem',
                    borderRadius: '6px',
                  }}
                >
                  {getCategoryInfo(selectedItem.category).label}
                </span>
                {detailLoading && (
                  <span style={{ fontSize: '0.75rem', color: '#64748B', marginLeft: '0.5rem' }}>
                    Sincronizando...
                  </span>
                )}
                <h2
                  style={{
                    margin: '0.5rem 0 0 0',
                    fontSize: '1.35rem',
                    fontWeight: 800,
                    color: '#0F172A',
                  }}
                >
                  {selectedItem.title}
                </h2>
              </div>
              <button
                onClick={() => { setSelectedItem(null); }}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.5rem',
                  color: '#94A3B8',
                  cursor: 'pointer',
                }}
              >
                ✕
              </button>
            </div>

            {/* Modal Metadata */}
            <div
              style={{
                backgroundColor: '#F8FAFC',
                borderRadius: '10px',
                padding: '0.75rem 1rem',
                fontSize: '0.8125rem',
                color: '#64748B',
                display: 'flex',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '0.5rem',
                marginBottom: '1.5rem',
              }}
            >
              <span>
                <strong>Emitido por:</strong> {selectedItem.author_name}
              </span>
              <span>
                <strong>Publicación:</strong>{' '}
                {selectedItem.published_at
                  ? new Date(selectedItem.published_at).toLocaleString('es-CO')
                  : 'Borrador'}
              </span>
              {selectedItem.expires_at && (
                <span>
                  <strong>Vence:</strong> {new Date(selectedItem.expires_at).toLocaleDateString('es-CO')}
                </span>
              )}
            </div>

            {/* Summary if distinct */}
            {selectedItem.summary && selectedItem.summary !== selectedItem.content && (
              <div
                style={{
                  backgroundColor: '#F0F9FF',
                  borderLeft: '4px solid #0284C7',
                  padding: '0.75rem 1rem',
                  borderRadius: '0 8px 8px 0',
                  fontSize: '0.875rem',
                  color: '#0369A1',
                  marginBottom: '1.5rem',
                  fontStyle: 'italic',
                }}
              >
                {selectedItem.summary}
              </div>
            )}

            {/* Full Content */}
            <div
              style={{
                fontSize: '0.9375rem',
                lineHeight: 1.7,
                color: '#334155',
                whiteSpace: 'pre-line',
                marginBottom: '2rem',
              }}
            >
              {selectedItem.content}
            </div>

            {/* Acknowledgment Bar inside Modal */}
            {selectedItem.requires_acknowledgment &&
              !selectedItem.acknowledged_at &&
              !selectedItem.is_acknowledged && (
                <button
                  onClick={(e) => void handleAcknowledge(selectedItem, e)}
                  disabled={acknowledgingId === selectedItem.id}
                  style={{
                    width: '100%',
                    backgroundColor: '#16A34A',
                    color: '#FFFFFF',
                    border: 'none',
                    borderRadius: '10px',
                    padding: '0.875rem',
                    fontSize: '0.9375rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    marginBottom: '1rem',
                  }}
                >
                  <span>✓</span>
                  <span>
                    {acknowledgingId === selectedItem.id
                      ? 'Registrando acuse de recibo...'
                      : 'Confirmar que he leído este comunicado'}
                  </span>
                </button>
              )}

            {selectedItem.acknowledged_at && (
              <div
                style={{
                  backgroundColor: '#DCFCE7',
                  border: '1px solid #86EFAC',
                  borderRadius: '10px',
                  padding: '0.75rem 1rem',
                  color: '#166534',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  marginBottom: '1rem',
                }}
              >
                <span>✓</span>
                <span>
                  Acuse registrado formalmente el{' '}
                  {new Date(selectedItem.acknowledged_at).toLocaleString('es-CO')}
                </span>
              </div>
            )}

            {/* Close Modal Button */}
            <button
              onClick={() => { setSelectedItem(null); }}
              style={{
                width: '100%',
                backgroundColor: '#0F172A',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '10px',
                padding: '0.75rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Cerrar comunicado
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default TeacherCommunicationsView
