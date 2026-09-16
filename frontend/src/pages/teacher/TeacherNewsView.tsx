/**
 * PEVN Frontend — Teacher News View (Phase 15 / B2)
 *
 * School newspaper, community highlights, academic achievements, and cultural events for educators.
 * Features:
 * - Institutional community bulletin feed
 * - Featured article spotlight banner
 * - Thematic category filtering & search
 * - Full article reading modal with publication metadata
 * - Loading, Empty, and Error states
 */

import React, { useEffect, useState } from 'react'
import { communicationApi } from '@/services/communication'
import type { InstitutionalNewsItem } from '@/types/communication'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

interface Props {
  teacherName?: string
}

const NEWS_CATEGORY_LABELS: Record<string, { label: string; icon: string }> = {
  LOGRO_ACADEMICO: { label: 'Logro Académico', icon: '🏆' },
  EVENTO_CULTURAL: { label: 'Evento Cultural', icon: '🎭' },
  EVENTO_DEPORTIVO: { label: 'Deportes', icon: '⚽' },
  PROYECTO_INSTITUCIONAL: { label: 'Proyecto Institucional', icon: '🚀' },
  NOTICIA_GENERAL: { label: 'General', icon: '📰' },
  ACADEMICA: { label: 'Académica', icon: '📖' },
  DEPORTES: { label: 'Deportes', icon: '🏅' },
  CULTURAL: { label: 'Cultural', icon: '🎨' },
  CIENCIA_TECNOLOGIA: { label: 'Ciencia y Tecnología', icon: '🔬' },
  COMUNIDAD: { label: 'Comunidad Educativa', icon: '🤝' },
  CONVOCATORIAS: { label: 'Convocatorias', icon: '📢' },
  LOGROS: { label: 'Logros', icon: '⭐' },
}

function getNewsCategoryInfo(category: string): { label: string; icon: string } {
  return (NEWS_CATEGORY_LABELS as Record<string, { label: string; icon: string } | undefined>)[category] ?? {
    label: category,
    icon: '📰',
  }
}

export const TeacherNewsView: React.FC<Props> = ({ teacherName: _teacherName }) => {
  const [news, setNews] = useState<InstitutionalNewsItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedArticle, setSelectedArticle] = useState<InstitutionalNewsItem | null>(null)

  const fetchNews = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await communicationApi.getTeacherNews()
      setNews(res.items)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar las noticias institucionales.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchNews()
  }, [])

  // Filtered news
  const filteredNews = news.filter((item) => {
    const matchesCategory = selectedCategory === 'ALL' || item.category === selectedCategory
    const matchesSearch =
      searchQuery.trim() === '' ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.summary && item.summary.toLowerCase().includes(searchQuery.toLowerCase())) ||
      item.content.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesSearch
  })

  // Featured article (first pinned/featured or most recent)
  const featured: InstitutionalNewsItem | undefined = news.find((n) => n.is_featured) ?? (news.length > 0 ? news[0] : undefined)

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
            <span style={{ fontSize: '1.5rem' }}>📰</span>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
              Noticias y Periódico Escolar
            </h2>
          </div>
          <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.875rem', color: '#64748B' }}>
            Acontecimientos, proyectos destacados y vida institucional de la comunidad educativa.
          </p>
        </div>

        <button
          onClick={() => void fetchNews()}
          style={{
            backgroundColor: '#F8FAFC',
            border: '1px solid #CBD5E1',
            borderRadius: '8px',
            padding: '0.5rem 1rem',
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

      {/* Featured Spotlight Banner (if exists and not filtered out) */}
      {!loading && !error && featured !== undefined && selectedCategory === 'ALL' && searchQuery.trim() === '' && (
        <div
          onClick={() => { setSelectedArticle(featured); }}
          style={{
            background: 'linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%)',
            color: '#FFFFFF',
            borderRadius: '16px',
            padding: '2rem',
            cursor: 'pointer',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
            transition: 'transform 150ms, box-shadow 150ms',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              style={{
                backgroundColor: '#F59E0B',
                color: '#000000',
                fontSize: '0.7rem',
                fontWeight: 800,
                padding: '0.2rem 0.6rem',
                borderRadius: '6px',
                textTransform: 'uppercase',
              }}
            >
              ★ Noticia Destacada
            </span>
            <span style={{ fontSize: '0.8125rem', color: '#CBD5E1' }}>
              {getNewsCategoryInfo(featured.category).label}
            </span>
          </div>

          <h3 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800, lineHeight: 1.3 }}>
            {featured.title}
          </h3>

          <p style={{ margin: 0, color: '#E2E8F0', fontSize: '0.9375rem', lineHeight: 1.6 }}>
            {featured.summary || featured.content.slice(0, 200) + '...'}
          </p>

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '0.8125rem',
              color: '#94A3B8',
              marginTop: '0.5rem',
            }}
          >
            <span>✍️ {featured.author_name}</span>
            <span>
              {featured.published_at
                ? new Date(featured.published_at).toLocaleDateString('es-CO')
                : ''}
            </span>
          </div>
        </div>
      )}

      {/* Filter and Search Controls */}
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
            placeholder="Buscar noticias por título o tema..."
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
            <option value="ALL">Todas las secciones</option>
            {Object.entries(NEWS_CATEGORY_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v.icon} {v.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Error state */}
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

      {/* Loading state */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
          <LoadingSpinner />
          <p style={{ color: '#64748B', fontSize: '0.9rem', marginTop: '1rem' }}>
            Cargando periódico escolar...
          </p>
        </div>
      ) : filteredNews.length === 0 ? (
        /* Empty state */
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '3.5rem 1.5rem',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🗞️</div>
          <h3 style={{ margin: '0 0 0.5rem 0', color: '#1E293B', fontWeight: 700 }}>
            No hay noticias en esta sección
          </h3>
          <p style={{ margin: 0, color: '#64748B', fontSize: '0.875rem' }}>
            Las publicaciones y crónicas escolares aparecerán aquí para toda la comunidad institucional.
          </p>
        </div>
      ) : (
        /* News Grid */
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: '1.25rem',
          }}
        >
          {filteredNews.map((item) => {
            const catInfo = getNewsCategoryInfo(item.category)

            return (
              <div
                key={item.id}
                onClick={() => { setSelectedArticle(item); }}
                style={{
                  backgroundColor: '#FFFFFF',
                  borderRadius: '14px',
                  border: '1px solid #E2E8F0',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                  cursor: 'pointer',
                  transition: 'transform 150ms, box-shadow 150ms',
                }}
              >
                <div>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '0.75rem',
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

                    {item.is_featured && (
                      <span
                        style={{
                          backgroundColor: '#FEF3C7',
                          color: '#B45309',
                          fontSize: '0.6875rem',
                          fontWeight: 800,
                          padding: '0.2rem 0.5rem',
                          borderRadius: '6px',
                          textTransform: 'uppercase',
                        }}
                      >
                        ★ Destacado
                      </span>
                    )}
                  </div>

                  <h3
                    style={{
                      margin: '0 0 0.5rem 0',
                      fontSize: '1.0625rem',
                      fontWeight: 800,
                      color: '#0F172A',
                      lineHeight: 1.35,
                    }}
                  >
                    {item.title}
                  </h3>

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

                <div
                  style={{
                    borderTop: '1px solid #F1F5F9',
                    paddingTop: '0.75rem',
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
              </div>
            )
          })}
        </div>
      )}

      {/* Article Detail Modal */}
      {selectedArticle && (
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
          onClick={() => { setSelectedArticle(null); }}
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
                  {getNewsCategoryInfo(selectedArticle.category).label}
                </span>
                <h2
                  style={{
                    margin: '0.5rem 0 0 0',
                    fontSize: '1.35rem',
                    fontWeight: 800,
                    color: '#0F172A',
                  }}
                >
                  {selectedArticle.title}
                </h2>
              </div>
              <button
                onClick={() => { setSelectedArticle(null); }}
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
                <strong>Redactado por:</strong> {selectedArticle.author_name}
              </span>
              <span>
                <strong>Fecha:</strong>{' '}
                {selectedArticle.published_at
                  ? new Date(selectedArticle.published_at).toLocaleDateString('es-CO')
                  : 'Borrador'}
              </span>
            </div>

            {/* Summary Lead if available */}
            {selectedArticle.summary && selectedArticle.summary !== selectedArticle.content && (
              <div
                style={{
                  backgroundColor: '#F1F5F9',
                  borderLeft: '4px solid #3B82F6',
                  padding: '0.75rem 1rem',
                  borderRadius: '0 8px 8px 0',
                  fontSize: '0.9375rem',
                  color: '#1E293B',
                  marginBottom: '1.5rem',
                  fontWeight: 500,
                  lineHeight: 1.6,
                }}
              >
                {selectedArticle.summary}
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
              {selectedArticle.content}
            </div>

            {/* Close Button */}
            <button
              onClick={() => { setSelectedArticle(null); }}
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
              Cerrar artículo
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default TeacherNewsView
