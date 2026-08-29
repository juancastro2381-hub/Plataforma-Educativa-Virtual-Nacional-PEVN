/**
 * PEVN Frontend — Territorial Analytics Dashboard View
 *
 * Provides national and departmental territorial dashboards, key performance
 * indicators (KPIs), educational distribution tables, and provisioning rates.
 */

import React, { useState, useEffect } from 'react'
import { analyticsApi } from '@/services/analytics'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'
import type {
  DepartmentAnalyticsItem,
  MunicipalityAnalyticsItem,
  TerritorialSummaryResponse,
} from '@/types'

export const TerritorialAnalyticsView: React.FC = () => {
  const { user } = useAuth()
  const [summary, setSummary] = useState<TerritorialSummaryResponse | null>(null)
  const [departments, setDepartments] = useState<DepartmentAnalyticsItem[]>([])
  const [municipalities, setMunicipalities] = useState<MunicipalityAnalyticsItem[]>([])
  const [selectedDeptCode, setSelectedDeptCode] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const summaryData = await analyticsApi.getTerritorialSummary()
      setSummary(summaryData)

      try {
        const deptData = await analyticsApi.getDepartmentDistribution()
        setDepartments(deptData.items || [])
      } catch {
        // May be restricted if strictly scoped
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Error al cargar métricas de analítica territorial.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleDepartmentSelect = async (deptCode: string) => {
    setSelectedDeptCode(deptCode)
    if (!deptCode) {
      setMunicipalities([])
      return
    }
    try {
      const munData = await analyticsApi.getMunicipalityDistribution(deptCode)
      setMunicipalities(munData.items || [])
    } catch {
      setMunicipalities([])
    }
  }

  const filteredDepartments = departments.filter(
    (d) =>
      d.department_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.department_code.includes(searchTerm)
  )

  if (isLoading) {
    return (
      <div style={{ maxWidth: '1200px', margin: '3rem auto', textAlign: 'center' }}>
        <LoadingSpinner size="lg" />
        <p style={{ marginTop: '1rem', color: '#64748B' }}>Cargando analítica territorial nacional...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ maxWidth: '1200px', margin: '3rem auto', padding: '0 1rem' }}>
        <div
          role="alert"
          style={{
            backgroundColor: '#FEF2F2',
            border: '1px solid #FCA5A5',
            borderRadius: '12px',
            padding: '2rem',
            textAlign: 'center',
            color: '#991B1B',
          }}
        >
          <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>⚠️</div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            No fue posible cargar la analítica territorial
          </h2>
          <p style={{ fontSize: '0.875rem', marginBottom: '1.5rem' }}>{error}</p>
          <Button variant="primary" onClick={loadData}>
            Reintentar Consulta
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '2rem auto', padding: '0 1rem' }}>
      {/* Header Banner */}
      <div
        style={{
          backgroundColor: '#0F172A',
          color: '#FFFFFF',
          borderRadius: '16px',
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: '0 10px 15px -3px rgba(15, 23, 42, 0.15)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '2rem' }}>📊</span>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: 0 }}>
            Tablero de Analítica Territorial
          </h1>
        </div>
        <p style={{ color: '#94A3B8', fontSize: '0.9375rem', margin: '0 0 1rem 0' }}>
          Monitoreo y cobertura del Catálogo Educativo Oficial (MEN / DANE) y tasa de aprovisionamiento institucional.
        </p>
        <div
          style={{
            display: 'flex',
            gap: '1.5rem',
            fontSize: '0.8125rem',
            color: '#CBD5E1',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            paddingTop: '0.75rem',
            flexWrap: 'wrap',
          }}
        >
          <div>
            Jurisdicción: <strong>{summary?.jurisdiction_name || 'Nacional'}</strong>
          </div>
          <div>
            Alcance: <strong>{summary?.scope_level || (user?.scope.is_national ? 'Nacional' : 'Institucional')}</strong>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      {summary && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '1rem',
            marginBottom: '2rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '12px',
              padding: '1.25rem',
              border: '1px solid #E2E8F0',
              boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            }}
          >
            <div style={{ fontSize: '0.8125rem', color: '#64748B', fontWeight: 600 }}>
              ESTABLECIMIENTOS REGISTRADOS
            </div>
            <div style={{ fontSize: '1.875rem', fontWeight: 800, color: '#0F172A', marginTop: '0.25rem' }}>
              {summary.total_institutions.toLocaleString()}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#16A34A', marginTop: '0.25rem' }}>
              {summary.provisioned_institutions} aprovisionados ({summary.provisioning_rate_percent}%)
            </div>
          </div>

          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '12px',
              padding: '1.25rem',
              border: '1px solid #E2E8F0',
              boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            }}
          >
            <div style={{ fontSize: '0.8125rem', color: '#64748B', fontWeight: 600 }}>
              SEDES EDUCATIVAS
            </div>
            <div style={{ fontSize: '1.875rem', fontWeight: 800, color: '#2563EB', marginTop: '0.25rem' }}>
              {summary.total_campuses.toLocaleString()}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
              Sedes principales y adscritas
            </div>
          </div>

          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '12px',
              padding: '1.25rem',
              border: '1px solid #E2E8F0',
              boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            }}
          >
            <div style={{ fontSize: '0.8125rem', color: '#64748B', fontWeight: 600 }}>
              SECTOR EDUCATIVO
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', marginTop: '0.375rem' }}>
              🏛️ {summary.sector_breakdown.official.toLocaleString()} Oficial
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#64748B', marginTop: '0.25rem' }}>
              🏢 {summary.sector_breakdown.non_official.toLocaleString()} No Oficial
            </div>
          </div>

          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '12px',
              padding: '1.25rem',
              border: '1px solid #E2E8F0',
              boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            }}
          >
            <div style={{ fontSize: '0.8125rem', color: '#64748B', fontWeight: 600 }}>
              DISTRIBUCIÓN DE ZONA
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', marginTop: '0.375rem' }}>
              🏙️ {summary.zone_breakdown.urban.toLocaleString()} Urbana
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#64748B', marginTop: '0.25rem' }}>
              🌳 {summary.zone_breakdown.rural.toLocaleString()} Rural
            </div>
          </div>
        </div>
      )}

      {/* Department Breakdown Section */}
      {departments.length > 0 && (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '1.5rem',
            marginBottom: '2rem',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
              marginBottom: '1rem',
            }}
          >
            <div>
              <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0F172A', margin: 0 }}>
                Distribución por Entidades Territoriales Departamentales (SED)
              </h2>
              <p style={{ fontSize: '0.8125rem', color: '#64748B', margin: '0.25rem 0 0 0' }}>
                Haga clic en un departamento para desglosar sus municipios.
              </p>
            </div>
            <input
              type="text"
              placeholder="Buscar departamento..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                padding: '0.5rem 0.875rem',
                fontSize: '0.875rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                outline: 'none',
                minWidth: '240px',
              }}
            />
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '2px solid #E2E8F0', textAlign: 'left' }}>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Cód. DANE</th>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Departamento</th>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Municipios</th>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Establecimientos</th>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Sedes</th>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Aprovisionadas</th>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Acción</th>
                </tr>
              </thead>
              <tbody>
                {filteredDepartments.map((dept) => (
                  <tr
                    key={dept.department_code}
                    style={{
                      borderBottom: '1px solid #F1F5F9',
                      backgroundColor: selectedDeptCode === dept.department_code ? '#EFF6FF' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '0.75rem', fontWeight: 600 }}>{dept.department_code}</td>
                    <td style={{ padding: '0.75rem', fontWeight: 600, color: '#0F172A' }}>
                      {dept.department_name}
                    </td>
                    <td style={{ padding: '0.75rem' }}>{dept.total_municipalities}</td>
                    <td style={{ padding: '0.75rem' }}>{dept.total_institutions.toLocaleString()}</td>
                    <td style={{ padding: '0.75rem' }}>{dept.total_campuses.toLocaleString()}</td>
                    <td style={{ padding: '0.75rem' }}>
                      <span
                        style={{
                          backgroundColor: dept.provisioned_institutions > 0 ? '#DCFCE7' : '#F1F5F9',
                          color: dept.provisioned_institutions > 0 ? '#166534' : '#64748B',
                          padding: '0.25rem 0.5rem',
                          borderRadius: '6px',
                          fontWeight: 600,
                          fontSize: '0.75rem',
                        }}
                      >
                        {dept.provisioned_institutions}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      <button
                        type="button"
                        onClick={() => handleDepartmentSelect(dept.department_code)}
                        style={{
                          backgroundColor: selectedDeptCode === dept.department_code ? '#2563EB' : '#F1F5F9',
                          color: selectedDeptCode === dept.department_code ? '#FFFFFF' : '#334155',
                          border: 'none',
                          padding: '0.375rem 0.75rem',
                          borderRadius: '6px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        {selectedDeptCode === dept.department_code ? 'Seleccionado ✓' : 'Ver Municipios →'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Municipality Drilldown Table */}
      {selectedDeptCode && municipalities.length > 0 && (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '1.5rem',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0F172A', margin: 0 }}>
              Municipios en Departamento {selectedDeptCode} ({municipalities.length} entidades)
            </h2>
            <button
              type="button"
              onClick={() => handleDepartmentSelect('')}
              style={{
                backgroundColor: 'transparent',
                border: '1px solid #CBD5E1',
                color: '#64748B',
                padding: '0.25rem 0.75rem',
                borderRadius: '6px',
                fontSize: '0.75rem',
                cursor: 'pointer',
              }}
            >
              ✕ Cerrar Desglose
            </button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '2px solid #E2E8F0', textAlign: 'left' }}>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Cód. DANE</th>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Municipio</th>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Establecimientos</th>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Oficiales</th>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>No Oficiales</th>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Sedes</th>
                  <th style={{ padding: '0.75rem', color: '#475569' }}>Aprovisionadas</th>
                </tr>
              </thead>
              <tbody>
                {municipalities.map((mun) => (
                  <tr key={mun.municipality_code} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 600 }}>{mun.municipality_code}</td>
                    <td style={{ padding: '0.75rem', fontWeight: 600, color: '#0F172A' }}>
                      {mun.municipality_name}
                    </td>
                    <td style={{ padding: '0.75rem' }}>{mun.total_institutions}</td>
                    <td style={{ padding: '0.75rem' }}>{mun.official_institutions}</td>
                    <td style={{ padding: '0.75rem' }}>{mun.non_official_institutions}</td>
                    <td style={{ padding: '0.75rem' }}>{mun.total_campuses}</td>
                    <td style={{ padding: '0.75rem' }}>
                      <span
                        style={{
                          backgroundColor: mun.provisioned_institutions > 0 ? '#DCFCE7' : '#F1F5F9',
                          color: mun.provisioned_institutions > 0 ? '#166534' : '#64748B',
                          padding: '0.25rem 0.5rem',
                          borderRadius: '6px',
                          fontWeight: 600,
                          fontSize: '0.75rem',
                        }}
                      >
                        {mun.provisioned_institutions}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default TerritorialAnalyticsView
