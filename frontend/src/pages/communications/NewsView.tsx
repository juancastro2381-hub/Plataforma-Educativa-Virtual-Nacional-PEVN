/**
 * PEVN Frontend — Institutional News & Bulletins View (Noticias y Vida Escolar)
 *
 * Professional news reader interface displaying institutional highlights,
 * pedagogical milestones, community announcements, and cultural achievements.
 * Protected by RBAC permission: 'news:read'.
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
import type { InstitutionalNewsItem } from '@/types/communication'

export const NewsView: React.FC = () => {
  const { user } = useAuth()

  const [newsList, setNewsList] = useState<InstitutionalNewsItem[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  // Selected News Modal State
  const [selectedArticle, setSelectedArticle] = useState<InstitutionalNewsItem | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState<boolean>(false)

  const loadNews = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await communicationApi.listNews({
        category: categoryFilter || undefined,
      })
      setNewsList(res.items)
      setTotal(res.total)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cargar noticias institucionales.')
    } finally {
      setIsLoading(false)
    }
  }, [categoryFilter])

  useEffect(() => {
    void loadNews()
  }, [loadNews])

  const formatCategory = (cat: string) => {
    const map: Record<string, string> = {
      ACADEMICA: 'Académica',
      CULTURAL: 'Cultural y Artística',
      DEPORTIVA: 'Deportes',
      INSTITUCIONAL: 'Institucional',
      CIENCIA_TECNOLOGIA: 'Ciencia y Tecnología',
      GENERAL: 'Vida Escolar',
    }
    return map[cat] || cat
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '2rem auto', padding: '0 1rem' }} id="news-bulletin-page">
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
              Comunicaciones • Periódico Mural Institucional
            </span>
            <Badge variant="neutral">
              {total} Publicaciones
            </Badge>
            {user?.scope.jurisdiction_name && (
              <Badge variant="neutral">
                Jurisdicción: {user.scope.jurisdiction_name}
              </Badge>
            )}
          </div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 800, margin: '0.25rem 0', color: '#FFFFFF' }}>
            Noticias y Vida Escolar
          </h1>
          <p style={{ color: '#CBD5E1', fontSize: '0.9375rem', margin: 0, maxWidth: '650px' }}>
            Novedades pedagógicas, logros estudiantiles y actividades de la comunidad educativa.
          </p>
        </div>

        <div>
          <Button
            variant="secondary"
            onClick={() => void loadNews()}
            id="btn-refresh-news"
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

      {/* Filter bar */}
      <Card style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ width: '250px' }}>
            <label
              htmlFor="news-category-select"
              style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Filtrar por Categoría
            </label>
            <select
              id="news-category-select"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
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
              <option value="ACADEMICA">Académica</option>
              <option value="CULTURAL">Cultural y Artística</option>
              <option value="DEPORTIVA">Deportes</option>
              <option value="INSTITUCIONAL">Institucional</option>
              <option value="CIENCIA_TECNOLOGIA">Ciencia y Tecnología</option>
              <option value="GENERAL">Vida Escolar</option>
            </select>
          </div>

          {categoryFilter && (
            <Button
              variant="secondary"
              onClick={() => setCategoryFilter('')}
              style={{ marginTop: '1.25rem' }}
            >
              Limpiar Filtro
            </Button>
          )}
        </div>
      </Card>

      {/* News Grid */}
      {isLoading ? (
        <div style={{ padding: '3rem', textAlign: 'center' }}>
          <LoadingSpinner size="lg" />
          <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
            Cargando boletín de noticias...
          </p>
        </div>
      ) : newsList.length === 0 ? (
        <Card>
          <EmptyState
            icon="📰"
            title="No hay noticias registradas"
            description="No se encontraron artículos o novedades en el período seleccionado."
          />
        </Card>
      ) : (
        <div
          id="news-cards-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
            gap: '1.5rem',
          }}
        >
          {newsList.map((item) => (
            <div
              key={item.id}
              id={`news-card-${item.id}`}
              style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '12px',
                border: '1px solid #E2E8F0',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
                transition: 'transform 150ms, box-shadow 150ms',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <Badge variant="primary">{formatCategory(item.category)}</Badge>
                  <span style={{ fontSize: '0.75rem', color: '#475569' }}>
                    {item.published_at ? new Date(item.published_at).toLocaleDateString('es-CO') : ''}
                  </span>
                </div>
                <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0F172A', margin: '0 0 0.5rem 0', lineHeight: 1.3 }}>
                  {item.title}
                </h3>
                {item.summary && (
                  <p style={{ fontSize: '0.875rem', color: '#475569', margin: '0 0 1rem 0', lineHeight: 1.5 }}>
                    {item.summary}
                  </p>
                )}
              </div>

              <div style={{ borderTop: '1px solid #F1F5F9', paddingTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="ghost"
                  size="sm"
                  id={`btn-read-news-${item.id}`}
                  onClick={() => {
                    setSelectedArticle(item)
                    setIsDetailOpen(true)
                  }}
                >
                  📖 Leer Noticia Completa
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Article Detail Modal */}
      {selectedArticle && (
        <Modal
          isOpen={isDetailOpen}
          onClose={() => {
            setIsDetailOpen(false)
            setSelectedArticle(null)
          }}
          title={selectedArticle.title}
          subtitle={`${formatCategory(selectedArticle.category)} • ${
            selectedArticle.published_at ? new Date(selectedArticle.published_at).toLocaleDateString('es-CO') : ''
          }`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.9375rem', lineHeight: 1.6, color: '#1E293B' }}>
            {selectedArticle.summary && (
              <div style={{ fontSize: '1rem', fontWeight: 500, color: '#334155', borderLeft: '3px solid #FCD116', paddingLeft: '1rem', fontStyle: 'italic' }}>
                {selectedArticle.summary}
              </div>
            )}
            <div style={{ whiteSpace: 'pre-wrap', color: '#0F172A' }}>
              {selectedArticle.content}
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

export default NewsView
