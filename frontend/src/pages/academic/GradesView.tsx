/**
 * PEVN Frontend — National Grades Catalog View (Catálogo Nacional de Grados)
 *
 * Professional view displaying the standardized Colombian educational grades
 * defined by the Ministry of National Education (MEN).
 * Protected by RBAC permission: 'grades:read'.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { academicApi } from '@/services/academic'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import type { GradeResponse } from '@/types'

export const GradesView: React.FC = () => {
  const [grades, setGrades] = useState<GradeResponse[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadGrades = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await academicApi.listGrades()
      setGrades(data.items)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cargar catálogo de grados.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadGrades()
  }, [loadGrades])

  const formatLevel = (level: string) => {
    const map: Record<string, { label: string; variant: 'primary' | 'success' | 'warning' | 'neutral' }> = {
      PREESCOLAR: { label: 'Preescolar', variant: 'warning' },
      PRIMARIA: { label: 'Básica Primaria (1° - 5°)', variant: 'primary' },
      SECUNDARIA: { label: 'Básica Secundaria (6° - 9°)', variant: 'success' },
      MEDIA: { label: 'Media Académica (10° - 11°)', variant: 'neutral' },
    }
    return map[level] || { label: level, variant: 'neutral' }
  }

  return (
    <div id="grades-catalog-view">
      <Card
        title="Catálogo Oficial de Grados Curriculares (MEN)"
        subtitle="Estructura curricular formal estandarizada según la Ley General de Educación (Ley 115 de 1994)."
        action={
          <Button variant="secondary" size="sm" onClick={() => void loadGrades()} id="btn-refresh-grades">
            🔄 Refrescar
          </Button>
        }
      >
        {error && (
          <div style={{ marginBottom: '1rem', color: '#DC2626', fontSize: '0.875rem' }}>
            ⚠️ {error}
          </div>
        )}

        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando catálogo estandarizado de grados...
            </p>
          </div>
        ) : grades.length === 0 ? (
          <EmptyState
            icon="🎓"
            title="No se encontraron grados"
            description="El catálogo de grados curriculares no está disponible en este momento."
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table
              id="grades-table"
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '0.875rem',
                textAlign: 'left',
              }}
            >
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Orden</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Grado Curricular</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Nivel Educativo</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Código / Identificador</th>
                </tr>
              </thead>
              <tbody>
                {grades.map((g) => {
                  const levelInfo = formatLevel(g.level)
                  return (
                    <tr
                      key={g.id}
                      style={{
                        borderBottom: '1px solid #F1F5F9',
                        transition: 'background-color 150ms',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8FAFC')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                    >
                      <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                        #{g.ordinal_order}
                      </td>
                      <td style={{ padding: '0.875rem 1rem', fontWeight: 600, color: '#1E293B' }}>
                        {g.name}
                      </td>
                      <td style={{ padding: '0.875rem 1rem' }}>
                        <Badge variant={levelInfo.variant}>{levelInfo.label}</Badge>
                      </td>
                      <td style={{ padding: '0.875rem 1rem', color: '#64748B', fontFamily: 'monospace', fontSize: '0.8125rem' }}>
                        <code>{g.id}</code>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

export default GradesView
