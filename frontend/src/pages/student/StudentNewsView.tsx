/**
 * PEVN Frontend — Student News View (Phase 15)
 *
 * Institutional news, school bulletin board, student achievements, and extracurriculars
 * for the authenticated student portal.
 */

import React, { useEffect, useState } from 'react'
import { communicationApi } from '@/services/communication'
import type {
  InstitutionalNewsItem,
  NewsCategory,
} from '@/types/communication'

interface Props {
  onBackToDashboard?: () => void
}

const NEWS_CATEGORY_LABELS: Record<NewsCategory, { label: string; icon: string; color: string }> = {
  LOGRO_ACADEMICO: { label: 'Logros Académicos', icon: '🏆', color: '#CA8A04' },
  EVENTO_CULTURAL: { label: 'Eventos Culturales', icon: '🎨', color: '#9333EA' },
  EVENTO_DEPORTIVO: { label: 'Deportes', icon: '⚽', color: '#16A34A' },
  PROYECTO_INSTITUCIONAL: { label: 'Proyectos Institucionales', icon: '🔬', color: '#0284C7' },
  NOTICIA_GENERAL: { label: 'Noticias Generales', icon: '📰', color: '#1D4ED8' },
  // Compatibilidad con aliases previos
  ACADEMICA: { label: 'Académica', icon: '🎓', color: '#1D4ED8' },
  DEPORTES: { label: 'Deportes', icon: '⚽', color: '#16A34A' },
  CULTURAL: { label: 'Cultural', icon: '🎨', color: '#9333EA' },
  CIENCIA_TECNOLOGIA: { label: 'Ciencia y Tecnología', icon: '🔬', color: '#0284C7' },
  COMUNIDAD: { label: 'Comunidad', icon: '🤝', color: '#D97706' },
  CONVOCATORIAS: { label: 'Convocatorias', icon: '📣', color: '#EA580C' },
  LOGROS: { label: 'Logros y Reconocimientos', icon: '🏆', color: '#CA8A04' },
}

export const StudentNewsView: React.FC<Props> = ({ onBackToDashboard: _onBackToDashboard }) => {
  const [newsList, setNewsList] = useState<InstitutionalNewsItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL')
  const [selectedArticle, setSelectedArticle] = useState<InstitutionalNewsItem | null>(null)

  const fetchNews = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await communicationApi.getStudentNews()
      setNewsList(res.items)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar las noticias estudiantiles.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchNews()
  }, [])

  const filteredNews = selectedCategory === 'ALL'
    ? newsList
    : newsList.filter((n) => n.category === selectedCategory)

  const featured = newsList.find((n) => n.is_featured)

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
              Periódico Escolar y Novedades
            </h2>
          </div>
          <p style={{ margin: '0.35rem 0 0 0', color: '#64748B', fontSize: '0.875rem' }}>
            Noticias, eventos deportivos, convocatorias culturales y vida estudiantil.
          </p>
        </div>

        <button
          onClick={() => void fetchNews()}
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
            backgroundColor: selectedCategory === 'ALL' ? '#0F172A' : '#FFFFFF',
            color: selectedCategory === 'ALL' ? '#FFFFFF' : '#475569',
            border: `1px solid ${selectedCategory === 'ALL' ? '#0F172A' : '#E2E8F0'}`,
            borderRadius: '9999px',
            padding: '0.4rem 1rem',
            fontSize: '0.8125rem',
            fontWeight: 600,
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          Todas ({newsList.length})
        </button>
        {Object.entries(NEWS_CATEGORY_LABELS).map(([catKey, catVal]) => {
          const count = newsList.filter((n) => n.category === catKey).length
          if (count === 0) return null
          const isSel = selectedCategory === catKey
          return (
            <button
              key={catKey}
              onClick={() => setSelectedCategory(catKey)}
              style={{
                backgroundColor: isSel ? '#0F172A' : '#FFFFFF',
                color: isSel ? '#FFFFFF' : '#475569',
                border: `1px solid ${isSel ? '#0F172A' : '#E2E8F0'}`,
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

      {/* Error Banner */}
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

      {/* Featured Banner */}
      {selectedCategory === 'ALL' && featured && !error && (
        <div
          onClick={() => setSelectedArticle(featured)}
          style={{
            backgroundColor: '#0F172A',
            color: '#FFFFFF',
            borderRadius: '16px',
            padding: '2rem',
            cursor: 'pointer',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
            boxShadow: '0 10px 25px -5px rgba(15, 23, 42, 0.3)',
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
              ★ Destacado
            </span>
            <span style={{ fontSize: '0.8125rem', color: '#94A3B8' }}>
              {NEWS_CATEGORY_LABELS[featured.category]?.label || featured.category}
            </span>
          </div>

          <h3 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800, lineHeight: 1.3 }}>
            {featured.title}
          </h3>

          <p style={{ margin: 0, color: '#CBD5E1', fontSize: '0.9375rem', lineHeight: 1.6 }}>
            {featured.summary}
          </p>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', color: '#64748B', marginTop: '0.5rem' }}>
            <span>✍️ {featured.author_name}</span>
            <span>{featured.published_at ? new Date(featured.published_at).toLocaleDateString('es-CO') : ''}</span>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#64748B' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>⏳</div>
          <p>Cargando noticias...</p>
        </div>
      ) : error ? null : filteredNews.length === 0 ? (
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
            Revisa más tarde para enterarte de nuevos eventos y publicaciones de la comunidad.
          </p>
        </div>
      ) : (
        /* Cards Grid */
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1.25rem' }}>
          {filteredNews.map((article) => {
            const catInfo = NEWS_CATEGORY_LABELS[article.category] || { label: article.category, icon: '📰', color: '#475569' }

            return (
              <div
                key={article.id}
                onClick={() => setSelectedArticle(article)}
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
                  transition: 'all 0.15s ease',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <span
                      style={{
                        backgroundColor: '#F8FAFC',
                        color: catInfo.color,
                        border: `1px solid ${catInfo.color}30`,
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        padding: '0.2rem 0.6rem',
                        borderRadius: '6px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                      }}
                    >
                      {catInfo.icon} {catInfo.label}
                    </span>

                    <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>
                      {article.published_at ? new Date(article.published_at).toLocaleDateString('es-CO') : ''}
                    </span>
                  </div>

                  <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.05rem', fontWeight: 800, color: '#0F172A', lineHeight: 1.35 }}>
                    {article.title}
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
                    {article.summary}
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
                  <span>Por {article.author_name}</span>
                  <span style={{ color: '#1D4ED8', fontWeight: 700 }}>Leer artículo →</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Read Article Modal */}
      {selectedArticle && (
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
          onClick={() => setSelectedArticle(null)}
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
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <span
                  style={{
                    backgroundColor: '#F1F5F9',
                    color: '#0F172A',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '0.25rem 0.6rem',
                    borderRadius: '6px',
                  }}
                >
                  {NEWS_CATEGORY_LABELS[selectedArticle.category]?.label || selectedArticle.category}
                </span>
                <h2 style={{ margin: '0.5rem 0 0 0', fontSize: '1.4rem', fontWeight: 800, color: '#0F172A' }}>
                  {selectedArticle.title}
                </h2>
              </div>
              <button
                onClick={() => setSelectedArticle(null)}
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
              <span><strong>Redactado por:</strong> {selectedArticle.author_name}</span>
              <span><strong>Fecha:</strong> {selectedArticle.published_at ? new Date(selectedArticle.published_at).toLocaleDateString('es-CO') : 'Borrador'}</span>
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
              {selectedArticle.content}
            </div>

            <button
              onClick={() => setSelectedArticle(null)}
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
