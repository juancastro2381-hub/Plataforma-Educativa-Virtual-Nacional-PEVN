/**
 * PEVN Frontend — Student Communications View (Phase 15)
 *
 * Official institutional circulars, academic notices, and student bulletins.
 * Features:
 * - Deterministic Active / Expiration Feed (DECISION-15-02)
 * - Category and Priority Badges
 * - Idempotent Acknowledgment ("Confirmar Lectura") for mandatory circulars
 * - Detailed Read Modal
 */

import React, { useEffect, useState } from 'react'
import { communicationApi } from '@/services/communication'
import type {
  CommunicationCategory,
  InstitutionalCommunicationItem,
} from '@/types/communication'

interface Props {
  onBackToDashboard?: () => void
}

const CATEGORY_LABELS: Record<CommunicationCategory, { label: string; icon: string }> = {
  CIRCULAR_INFORMATIVA: { label: 'Circular Informativa', icon: '📄' },
  CONVOCATORIA_ACUDIENTES: { label: 'Convocatoria a Acudientes', icon: '👥' },
  RESOLUCION_RECTORAL: { label: 'Resolución Rectoral', icon: '📜' },
  CRONOGRAMA_ACADEMICO: { label: 'Cronograma Académico', icon: '📅' },
  EMERGENCIA_SANITARIA: { label: 'Alerta / Emergencia', icon: '🚨' },
  EVENTO_INSTITUCIONAL: { label: 'Evento Institucional', icon: '🎉' },
  OTRO: { label: 'Otro Comunicado', icon: '📌' },
}

const PRIORITY_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  BAJA: { bg: '#F1F5F9', color: '#475569', border: '#CBD5E1' },
  MEDIA: { bg: '#EFF6FF', color: '#1D4ED8', border: '#BFDBFE' },
  ALTA: { bg: '#FEF3C7', color: '#B45309', border: '#FDE68A' },
  URGENTE: { bg: '#FEE2E2', color: '#B91C1C', border: '#FCA5A5' },
}

export const StudentCommunicationsView: React.FC<Props> = ({ onBackToDashboard: _onBackToDashboard }) => {
  const [communications, setCommunications] = useState<InstitutionalCommunicationItem[]>([])
  const [unreadCount, setUnreadCount] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL')
  const [selectedItem, setSelectedItem] = useState<InstitutionalCommunicationItem | null>(null)
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null)

  const fetchCommunications = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await communicationApi.getStudentCommunications()
      setCommunications(res.items)
      setUnreadCount(res.unread_count)
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

  const handleAcknowledge = async (item: InstitutionalCommunicationItem, e: React.MouseEvent) => {
    e.stopPropagation()
    setAcknowledgingId(item.id)
    try {
      const updated = await communicationApi.acknowledgeStudentCommunication(item.id)
      setCommunications((prev) =>
        prev.map((c) => (c.id === item.id ? { ...c, acknowledged_at: updated.acknowledged_at, has_read: true } : c))
      )
      if (selectedItem?.id === item.id) {
        setSelectedItem((prev) => (prev ? { ...prev, acknowledged_at: updated.acknowledged_at, has_read: true } : null))
      }
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al confirmar la lectura del comunicado.'
      alert(msg)
    } finally {
      setAcknowledgingId(null)
    }
  }

  const filtered = selectedCategory === 'ALL'
    ? communications
    : communications.filter((c) => c.category === selectedCategory)

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
              Mis Comunicados Institucionales
            </h2>
            {unreadCount > 0 && (
              <span
                style={{
                  backgroundColor: '#EF4444',
                  color: '#FFFFFF',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  padding: '0.2rem 0.6rem',
                  borderRadius: '9999px',
                }}
              >
                {unreadCount} sin leer
              </span>
            )}
          </div>
          <p style={{ margin: '0.35rem 0 0 0', color: '#64748B', fontSize: '0.875rem' }}>
            Avisos de rectoría, circulares y directrices oficiales de la institución educativa.
          </p>
        </div>

        <button
          onClick={() => void fetchCommunications()}
          disabled={loading}
          style={{
            backgroundColor: '#F8FAFC',
            border: '1px solid #CBD5E1',
            borderRadius: '8px',
            padding: '0.5rem 1rem',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: '#334155',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}
        >
          <span>🔄</span> Actualizar
        </button>
      </div>

      {/* Category Filter Pills */}
      <div style={{ display: 'flex', gap: '0.5rem', overflowX: 'auto', paddingBottom: '0.25rem' }}>
        <button
          onClick={() => setSelectedCategory('ALL')}
          style={{
            backgroundColor: selectedCategory === 'ALL' ? '#1D4ED8' : '#FFFFFF',
            color: selectedCategory === 'ALL' ? '#FFFFFF' : '#475569',
            border: `1px solid ${selectedCategory === 'ALL' ? '#1D4ED8' : '#E2E8F0'}`,
            borderRadius: '9999px',
            padding: '0.4rem 1rem',
            fontSize: '0.8125rem',
            fontWeight: 600,
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          Todos ({communications.length})
        </button>
        {Object.entries(CATEGORY_LABELS).map(([catKey, catVal]) => {
          const count = communications.filter((c) => c.category === catKey).length
          if (count === 0) return null
          const isSel = selectedCategory === catKey
          return (
            <button
              key={catKey}
              onClick={() => setSelectedCategory(catKey)}
              style={{
                backgroundColor: isSel ? '#1D4ED8' : '#FFFFFF',
                color: isSel ? '#FFFFFF' : '#475569',
                border: `1px solid ${isSel ? '#1D4ED8' : '#E2E8F0'}`,
                borderRadius: '9999px',
                padding: '0.4rem 1rem',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              {catVal.icon} {catVal.label} ({count})
            </button>
          )
        })}
      </div>

      {/* Error state */}
      {error && (
        <div
          style={{
            backgroundColor: '#FEE2E2',
            border: '1px solid #FCA5A5',
            color: '#991B1B',
            borderRadius: '12px',
            padding: '1rem',
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#64748B' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>⏳</div>
          <p>Cargando comunicados...</p>
        </div>
      ) : error ? null : filtered.length === 0 ? (
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
            No hay comunicados vigentes en esta categoría
          </h3>
          <p style={{ margin: 0, color: '#64748B', fontSize: '0.875rem' }}>
            Los comunicados institucionales vigentes aparecerán aquí tan pronto como sean emitidos.
          </p>
        </div>
      ) : (
        /* Cards Grid */
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1rem' }}>
          {filtered.map((item) => {
            const catInfo = CATEGORY_LABELS[item.category] || { label: item.category, icon: '📌' }
            const pStyle = PRIORITY_STYLES[item.priority] || PRIORITY_STYLES.MEDIA
            const isUnread = !item.has_read
            const needsAck = item.requires_acknowledgment && !item.acknowledged_at

            return (
              <div
                key={item.id}
                onClick={() => setSelectedItem(item)}
                style={{
                  backgroundColor: '#FFFFFF',
                  borderRadius: '14px',
                  border: isUnread ? '2px solid #3B82F6' : '1px solid #E2E8F0',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: isUnread ? '0 4px 12px rgba(59, 130, 246, 0.1)' : '0 1px 3px rgba(0,0,0,0.04)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
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

                    <span
                      style={{
                        backgroundColor: pStyle.bg,
                        color: pStyle.color,
                        border: `1px solid ${pStyle.border}`,
                        fontSize: '0.7rem',
                        fontWeight: 800,
                        padding: '0.2rem 0.5rem',
                        borderRadius: '6px',
                        textTransform: 'uppercase',
                      }}
                    >
                      {item.priority}
                    </span>
                  </div>

                  <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.05rem', fontWeight: 800, color: '#0F172A', lineHeight: 1.3 }}>
                    {item.is_pinned && <span style={{ marginRight: '0.3rem' }}>📌</span>}
                    {item.title}
                  </h3>

                  <p
                    style={{
                      margin: '0 0 1rem 0',
                      color: '#475569',
                      fontSize: '0.875rem',
                      lineHeight: 1.5,
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}
                  >
                    {item.content}
                  </p>
                </div>

                <div>
                  <div
                    style={{
                      borderTop: '1px solid #F1F5F9',
                      paddingTop: '0.75rem',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      fontSize: '0.75rem',
                      color: '#94A3B8',
                    }}
                  >
                    <span>✍️ {item.author_name}</span>
                    <span>{item.published_at ? new Date(item.published_at).toLocaleDateString('es-CO') : ''}</span>
                  </div>

                  {needsAck ? (
                    <button
                      onClick={(e) => void handleAcknowledge(item, e)}
                      disabled={acknowledgingId === item.id}
                      style={{
                        marginTop: '0.75rem',
                        width: '100%',
                        backgroundColor: '#16A34A',
                        color: '#FFFFFF',
                        border: 'none',
                        borderRadius: '8px',
                        padding: '0.5rem',
                        fontSize: '0.8125rem',
                        fontWeight: 700,
                        cursor: acknowledgingId === item.id ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.4rem',
                      }}
                    >
                      {acknowledgingId === item.id ? 'Confirmando...' : '✓ Confirmar lectura obligatoria'}
                    </button>
                  ) : item.acknowledged_at ? (
                    <div
                      style={{
                        marginTop: '0.75rem',
                        backgroundColor: '#F0FDF4',
                        border: '1px solid #BBF7D0',
                        color: '#166534',
                        borderRadius: '8px',
                        padding: '0.35rem 0.6rem',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        textAlign: 'center',
                      }}
                    >
                      ✓ Lectura confirmada el {new Date(item.acknowledged_at).toLocaleDateString('es-CO')}
                    </div>
                  ) : null}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Read Detail Modal */}
      {selectedItem && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
          onClick={() => setSelectedItem(null)}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '20px',
              maxWidth: '680px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '2rem',
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
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
                  {CATEGORY_LABELS[selectedItem.category]?.label || selectedItem.category}
                </span>
                <h2 style={{ margin: '0.5rem 0 0 0', fontSize: '1.35rem', fontWeight: 800, color: '#0F172A' }}>
                  {selectedItem.title}
                </h2>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
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

            <div
              style={{
                backgroundColor: '#F8FAFC',
                borderRadius: '10px',
                padding: '0.75rem 1rem',
                fontSize: '0.8125rem',
                color: '#64748B',
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: '1.5rem',
              }}
            >
              <span><strong>Emitido por:</strong> {selectedItem.author_name}</span>
              <span><strong>Fecha:</strong> {selectedItem.published_at ? new Date(selectedItem.published_at).toLocaleString('es-CO') : 'Borrador'}</span>
            </div>

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

            {selectedItem.requires_acknowledgment && !selectedItem.acknowledged_at && (
              <button
                onClick={(e) => void handleAcknowledge(selectedItem, e)}
                disabled={acknowledgingId === selectedItem.id}
                style={{
                  width: '100%',
                  backgroundColor: '#16A34A',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: '10px',
                  padding: '0.75rem',
                  fontSize: '0.9375rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  marginBottom: '1rem',
                }}
              >
                {acknowledgingId === selectedItem.id ? 'Registrando...' : '✓ Confirmar recepción y lectura de este comunicado'}
              </button>
            )}

            <button
              onClick={() => setSelectedItem(null)}
              style={{
                width: '100%',
                backgroundColor: '#F1F5F9',
                color: '#475569',
                border: 'none',
                borderRadius: '10px',
                padding: '0.65rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
