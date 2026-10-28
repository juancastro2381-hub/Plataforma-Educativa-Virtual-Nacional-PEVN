/**
 * PEVN Frontend — Territorial Control Center View (NTA-05)
 *
 * Authoritative Operational Intelligence & Territorial Control Center.
 * Implements the 4-Tier telemetry architecture:
 *   TIER 1: Catálogo Oficial (DANE / MEN DIVIPOLA)
 *   TIER 2: Pipeline de Adopción (NTA-04 Radicaciones y Trámites)
 *   TIER 3: Tenencia PEVN (Instituciones Operativas, Vínculos Oficiales y Fixtures)
 *   TIER 4: Gobernanza SED (Cobertura de Secretarías de Educación y Administradores Departamentales)
 *
 * Includes:
 *   - 33-Department Interactive Governance Matrix
 *   - Municipal Detail Drill-down Drawer / Modal
 *   - Role-adaptive view isolation for DEPARTMENT_ADMIN (scoped strictly to assigned jurisdiction)
 *   - Dynamic runtime metrics (0 hardcoded values)
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Modal } from '@/components/ui/Modal'
import { useAuth } from '@/hooks/useAuth'
import { analyticsApi } from '@/services/analytics'
import type {
  DepartmentAdminStatus,
  DepartmentDetailControlCenterResponse,
  TerritorialControlCenterResponse,
} from '@/types'

export const TerritorialControlCenterView: React.FC = () => {
  const navigate = useNavigate()
  const { hasRole } = useAuth()

  const isNational = hasRole('superadmin') || hasRole('national_admin')

  // Data State
  const [data, setData] = useState<TerritorialControlCenterResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<'ALL' | DepartmentAdminStatus>('ALL')

  // Department Drilldown Modal State
  const [selectedDeptCode, setSelectedDeptCode] = useState<string | null>(null)
  const [deptDetail, setDeptDetail] = useState<DepartmentDetailControlCenterResponse | null>(null)
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [muniSearchTerm, setMuniSearchTerm] = useState<string>('')

  // Load Main Control Center Data
  const loadControlCenter = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await analyticsApi.getTerritorialControlCenter()
      setData(response)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al cargar datos del Centro de Control Territorial'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadControlCenter()
  }, [loadControlCenter])

  // Load Department Detail when requested
  const handleOpenDetail = useCallback(async (deptCode: string) => {
    setSelectedDeptCode(deptCode)
    setLoadingDetail(true)
    setDetailError(null)
    setMuniSearchTerm('')
    try {
      const detail = await analyticsApi.getDepartmentControlCenterDetail(deptCode)
      setDeptDetail(detail)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al obtener el detalle departamental'
      setDetailError(message)
    } finally {
      setLoadingDetail(false)
    }
  }, [])

  const handleCloseDetail = useCallback(() => {
    setSelectedDeptCode(null)
    setDeptDetail(null)
    setDetailError(null)
  }, [])

  // Filtered Department Rows (for National scope)
  const filteredDepartments = useMemo(() => {
    if (!data?.department_matrix) return []
    return data.department_matrix.filter((dept) => {
      const matchesSearch =
        dept.department_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        dept.department_code.includes(searchTerm)
      const matchesStatus =
        statusFilter === 'ALL' || dept.governance_status === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [data?.department_matrix, searchTerm, statusFilter])

  // Filtered Municipalities for detail drawer
  const filteredMunicipalities = useMemo(() => {
    if (!deptDetail?.municipalities) return []
    return deptDetail.municipalities.filter((muni) =>
      muni.municipality_name.toLowerCase().includes(muniSearchTerm.toLowerCase()) ||
      muni.municipality_code.includes(muniSearchTerm)
    )
  }, [deptDetail?.municipalities, muniSearchTerm])

  // Status Badge Helper
  const renderStatusBadge = (status: string | DepartmentAdminStatus) => {
    switch (status) {
      case 'COVERED':
        return (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.2rem 0.6rem',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: 700,
              backgroundColor: '#DCFCE7',
              color: '#166534',
              border: '1px solid #86EFAC',
            }}
          >
            <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#16A34A' }} />
            CUBIERTO
          </span>
        )
      case 'INVITED':
        return (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.2rem 0.6rem',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: 700,
              backgroundColor: '#FEF3C7',
              color: '#92400E',
              border: '1px solid #FCD34D',
            }}
          >
            <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#D97706' }} />
            INVITADO
          </span>
        )
      case 'VACANT':
      default:
        return (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.2rem 0.6rem',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: 700,
              backgroundColor: '#F1F5F9',
              color: '#475569',
              border: '1px solid #CBD5E1',
            }}
          >
            <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#64748B' }} />
            VACANTE
          </span>
        )
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: '1rem' }}>
        <LoadingSpinner size="lg" />
        <p style={{ color: '#64748B', fontWeight: 500 }}>Cargando Centro de Control Territorial...</p>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div style={{ maxWidth: '1200px', margin: '2rem auto', padding: '0 1rem' }}>
        <Alert variant="error">
          <strong>Error de inicialización:</strong> {error || 'No se pudieron recuperar las métricas del Centro de Control Territorial.'}
        </Alert>
        <div style={{ marginTop: '1rem' }}>
          <Button onClick={loadControlCenter} variant="primary">
            Reintentar
          </Button>
        </div>
      </div>
    )
  }

  const { tier1_catalog, tier2_pipeline, tier3_tenancy, tier4_governance } = data

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '1.5rem 1rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* HEADER SECTION */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '1rem',
          paddingBottom: '1rem',
          borderBottom: '1px solid #E2E8F0',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
              Centro de Control Territorial
            </h1>
            <span
              style={{
                backgroundColor: data.scope_level === 'NATIONAL' ? '#EFF6FF' : '#F0FDF4',
                color: data.scope_level === 'NATIONAL' ? '#1D4ED8' : '#15803D',
                border: `1px solid ${data.scope_level === 'NATIONAL' ? '#BFDBFE' : '#BBF7D0'}`,
                padding: '0.2rem 0.65rem',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Ámbito {data.scope_level === 'NATIONAL' ? 'Nacional' : 'Departamental'}
            </span>
          </div>
          <p style={{ color: '#64748B', fontSize: '0.925rem', marginTop: '0.35rem', marginBottom: 0 }}>
            {data.scope_level === 'NATIONAL'
              ? 'Consolidado Estratégico Nacional — 33 Entidades Territoriales Certificadas (DIVIPOLA / MEN)'
              : `Jurisdicción Departamental: ${data.jurisdiction_name}`}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.75rem', color: '#475569' }}>
            Calculado: {new Date(data.computed_at).toLocaleTimeString('es-CO')}
          </span>
          <Button variant="secondary" size="sm" onClick={loadControlCenter}>
            ↻ Actualizar Telemetría
          </Button>
          {isNational && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/admin/onboarding')}
            >
              + Radicar Onboarding
            </Button>
          )}
        </div>
      </div>

      {/* 4-TIER TELEMETRY GRID */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1rem',
        }}
      >
        {/* TIER 1: CATÁLOGO OFICIAL */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            border: '1px solid #E2E8F0',
            borderTop: '4px solid #2563EB',
            padding: '1.25rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#2563EB', letterSpacing: '0.05em' }}>
              TIER 1 • CATÁLOGO OFICIAL
            </span>
            <span style={{ fontSize: '0.8125rem', color: '#334155', backgroundColor: '#F1F5F9', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 600 }}>
              DANE / MEN
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
            <span style={{ fontSize: '2rem', fontWeight: 800, color: '#0F172A' }}>
              {(tier1_catalog?.total_establishments ?? 0).toLocaleString('es-CO')}
            </span>
            <span style={{ fontSize: '0.85rem', color: '#64748B', fontWeight: 500 }}>
              Establecimientos
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid #F1F5F9' }}>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#475569', display: 'block' }}>Sedes Educativas</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                {(tier1_catalog?.total_campuses ?? 0).toLocaleString('es-CO')}
              </span>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#475569', display: 'block' }}>
                {data.scope_level === 'NATIONAL' ? 'Departamentos' : 'Municipios'}
              </span>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                {data.scope_level === 'NATIONAL'
                  ? `${tier1_catalog?.total_departments ?? 0} dptos.`
                  : `${tier1_catalog?.total_municipalities ?? 0} mun.`}
              </span>
            </div>
          </div>
        </div>

        {/* TIER 2: PIPELINE DE ADOPCIÓN */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            border: '1px solid #E2E8F0',
            borderTop: '4px solid #6366F1',
            padding: '1.25rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#6366F1', letterSpacing: '0.05em' }}>
              TIER 2 • PIPELINE DE ADOPCIÓN
            </span>
            <span style={{ fontSize: '0.8125rem', color: '#334155', backgroundColor: '#F1F5F9', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 600 }}>
              NTA-04
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
            <span style={{ fontSize: '2rem', fontWeight: 800, color: '#0F172A' }}>
              {(tier2_pipeline?.total_requests ?? 0).toLocaleString('es-CO')}
            </span>
            <span style={{ fontSize: '0.85rem', color: '#64748B', fontWeight: 500 }}>
              Trámites Totales
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.4rem', paddingTop: '0.5rem', borderTop: '1px solid #F1F5F9' }}>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#D97706', display: 'block' }}>Radicados</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                {tier2_pipeline?.submitted ?? 0}
              </span>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#2563EB', display: 'block' }}>En Revisión</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                {tier2_pipeline?.under_review ?? 0}
              </span>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#16A34A', display: 'block' }}>Aprobados</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                {tier2_pipeline?.approved ?? 0}
              </span>
            </div>
          </div>
        </div>

        {/* TIER 3: TENENCIA OPERATIVA PEVN */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            border: '1px solid #E2E8F0',
            borderTop: '4px solid #059669',
            padding: '1.25rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#059669', letterSpacing: '0.05em' }}>
              TIER 3 • TENENCIA OPERATIVA
            </span>
            <span style={{ fontSize: '0.8125rem', color: '#334155', backgroundColor: '#F1F5F9', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 600 }}>
              SaaS PEVN
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
            <span style={{ fontSize: '2rem', fontWeight: 800, color: '#0F172A' }}>
              {(tier3_tenancy?.total_institutions ?? 0).toLocaleString('es-CO')}
            </span>
            <span style={{ fontSize: '0.85rem', color: '#64748B', fontWeight: 500 }}>
              Colegios Operativos
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.4rem', paddingTop: '0.5rem', borderTop: '1px solid #F1F5F9' }}>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#059669', display: 'block' }}>Catálogo MEN</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                {tier3_tenancy?.catalog_linked_institutions ?? 0}
              </span>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#64748B', display: 'block' }}>Fixtures</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                {tier3_tenancy?.synthetic_fixture_institutions ?? 0}
              </span>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#0284C7', display: 'block' }}>Sedes Activas</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                {tier3_tenancy?.active_operational_campuses ?? 0}
              </span>
            </div>
          </div>
        </div>

        {/* TIER 4: GOBERNANZA SED */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            border: '1px solid #E2E8F0',
            borderTop: '4px solid #D97706',
            padding: '1.25rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#D97706', letterSpacing: '0.05em' }}>
              TIER 4 • GOBERNANZA SED
            </span>
            <span style={{ fontSize: '0.8125rem', color: '#334155', backgroundColor: '#F1F5F9', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 600 }}>
              Admin Dptal.
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
            <span style={{ fontSize: '2rem', fontWeight: 800, color: '#0F172A' }}>
              {tier4_governance?.coverage_percentage ?? 0}%
            </span>
            <span style={{ fontSize: '0.85rem', color: '#64748B', fontWeight: 500 }}>
              Cobertura Nacional
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.4rem', paddingTop: '0.5rem', borderTop: '1px solid #F1F5F9' }}>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#16A34A', display: 'block' }}>Cubiertos</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                {tier4_governance?.covered_departments ?? 0}
              </span>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#D97706', display: 'block' }}>Invitados</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                {tier4_governance?.pending_invitations ?? 0}
              </span>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#DC2626', display: 'block' }}>Vacantes</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1E293B' }}>
                {tier4_governance?.vacant_departments ?? 0}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* DEPARTMENTAL MATRIX / DEPARTMENT SPECIFIC PANEL */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
          overflow: 'hidden',
        }}
      >
        {/* Table Toolbar */}
        <div
          style={{
            padding: '1.25rem',
            borderBottom: '1px solid #F1F5F9',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0F172A', margin: 0 }}>
              {data.scope_level === 'NATIONAL'
                ? 'Matriz Territorial Nacional (33 Departamentos)'
                : `Jurisdicción Asignada: ${data.jurisdiction_name}`}
            </h2>
            <p style={{ color: '#64748B', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
              {data.scope_level === 'NATIONAL'
                ? 'Supervisión integral de cobertura, trámites de adopción y asignaciones de Secretarías de Educación'
                : 'Métricas exclusivas y delegación operativa para su entidad territorial'}
            </p>
          </div>

          {data.scope_level === 'NATIONAL' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
              {/* Search Box */}
              <input
                type="text"
                placeholder="Buscar departamento o código..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  padding: '0.45rem 0.75rem',
                  fontSize: '0.85rem',
                  border: '1px solid #CBD5E1',
                  borderRadius: '6px',
                  outline: 'none',
                  minWidth: '220px',
                }}
              />

              {/* Status Filter */}
              <div style={{ display: 'flex', gap: '0.25rem', backgroundColor: '#F8FAFC', padding: '0.2rem', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
                {(['ALL', 'COVERED', 'INVITED', 'VACANT'] as const).map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    style={{
                      border: 'none',
                      background: statusFilter === st ? '#FFFFFF' : 'transparent',
                      color: statusFilter === st ? '#0F172A' : '#64748B',
                      boxShadow: statusFilter === st ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                      fontWeight: statusFilter === st ? 700 : 500,
                      fontSize: '0.75rem',
                      padding: '0.3rem 0.6rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                    }}
                  >
                    {st === 'ALL' ? 'Todos' : st === 'COVERED' ? 'Cubiertos' : st === 'INVITED' ? 'Invitados' : 'Vacantes'}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Table Content */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0', color: '#475569' }}>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>CÓDIGO</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>DEPARTAMENTO</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>CATÁLOGO MEN</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>TENANCY PEVN</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>PIPELINE</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>GOBERNANZA SED</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>ADMINISTRADOR</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>TASA</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600, textAlign: 'center' }}>ACCIONES</th>
              </tr>
            </thead>
            <tbody>
              {filteredDepartments.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ padding: '3rem 1rem', textAlign: 'center', color: '#475569' }}>
                    No se encontraron departamentos que coincidan con los filtros aplicados.
                  </td>
                </tr>
              ) : (
                filteredDepartments.map((dept) => (
                  <tr
                    key={dept.department_code}
                    style={{
                      borderBottom: '1px solid #F1F5F9',
                      transition: 'background-color 0.15s ease',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8FAFC')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <td style={{ padding: '0.85rem 1rem', fontFamily: 'monospace', fontWeight: 600, color: '#64748B' }}>
                      {dept.department_code}
                    </td>
                    <td style={{ padding: '0.85rem 1rem', fontWeight: 700, color: '#0F172A' }}>
                      {dept.department_name}
                    </td>
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontWeight: 600, color: '#1E293B' }}>
                          {(dept.total_establishments ?? 0).toLocaleString('es-CO')} establ.
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
                          {(dept.total_campuses ?? 0).toLocaleString('es-CO')} sedes
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '0.15rem 0.5rem',
                          borderRadius: '4px',
                          fontWeight: 700,
                          backgroundColor: dept.active_institutions > 0 ? '#ECFDF5' : '#F1F5F9',
                          color: dept.active_institutions > 0 ? '#059669' : '#475569',
                        }}
                      >
                        {dept.active_institutions} {dept.active_institutions === 1 ? 'colegio' : 'colegios'}
                      </span>
                    </td>
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '0.15rem 0.5rem',
                          borderRadius: '4px',
                          fontWeight: 700,
                          backgroundColor: dept.pipeline_in_progress > 0 ? '#EEF2FF' : '#F8FAFC',
                          color: dept.pipeline_in_progress > 0 ? '#4F46E5' : '#475569',
                        }}
                      >
                        {dept.pipeline_in_progress} en trámite
                      </span>
                    </td>
                    <td style={{ padding: '0.85rem 1rem' }}>
                      {renderStatusBadge(dept.governance_status)}
                    </td>
                    <td style={{ padding: '0.85rem 1rem' }}>
                      {dept.admin_name ? (
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <span style={{ fontWeight: 600, color: '#1E293B', fontSize: '0.8rem' }}>
                            {dept.admin_name}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
                            {dept.admin_email}
                          </span>
                        </div>
                      ) : (
                        <span style={{ color: '#475569', fontStyle: 'italic', fontSize: '0.8rem' }}>
                          Sin Administrador
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '0.85rem 1rem', fontWeight: 600, color: '#334155' }}>
                      {dept.provisioning_rate_percent}%
                    </td>
                    <td style={{ padding: '0.85rem 1rem', textAlign: 'center' }}>
                      <div style={{ display: 'flex', justifyContent: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleOpenDetail(dept.department_code)}
                          title="Ver desglose municipal y analítica"
                        >
                          Detalle
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => navigate(`/admin/onboarding?department_code=${dept.department_code}`)}
                          title="Radicar adopción en este departamento"
                        >
                          Radicar
                        </Button>
                        {isNational && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/admin/department-admins?department_code=${dept.department_code}`)}
                            title="Gestionar administrador SED"
                          >
                            SED
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* DEPARTMENT DETAIL DRILLDOWN MODAL / DRAWER */}
      {selectedDeptCode && (
        <Modal
          isOpen={Boolean(selectedDeptCode)}
          onClose={handleCloseDetail}
          title={`Detalle Territorial: ${deptDetail?.department_name || selectedDeptCode}`}
          maxWidth="xl"
        >
          {loadingDetail ? (
            <div style={{ padding: '3rem', textAlign: 'center' }}>
              <LoadingSpinner size="md" />
              <p style={{ marginTop: '0.75rem', color: '#64748B' }}>Cargando desglose municipal...</p>
            </div>
          ) : detailError ? (
            <Alert variant="error">{detailError}</Alert>
          ) : deptDetail ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Department Summary Header Card */}
              <div
                style={{
                  backgroundColor: '#F8FAFC',
                  borderRadius: '8px',
                  border: '1px solid #E2E8F0',
                  padding: '1rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#0F172A' }}>
                      {deptDetail.department_name}
                    </h3>
                    <span style={{ fontSize: '0.8rem', color: '#64748B', fontFamily: 'monospace' }}>
                      (DANE: {deptDetail.department_code})
                    </span>
                  </div>
                  <div style={{ marginTop: '0.25rem' }}>
                    {deptDetail.admin_name ? (
                      <span style={{ fontSize: '0.8rem', color: '#334155' }}>
                        Secretario / Administrador SED: <strong>{deptDetail.admin_name}</strong> ({deptDetail.admin_email})
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.8rem', color: '#D97706', fontWeight: 500 }}>
                        Secretaría de Educación sin Administrador Departamental asignado
                      </span>
                    )}
                  </div>
                </div>
                <div>{renderStatusBadge(deptDetail.governance_status)}</div>
              </div>

              {/* Department Mini 3-Tier Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
                <div style={{ backgroundColor: '#EFF6FF', padding: '0.75rem', borderRadius: '6px', border: '1px solid #BFDBFE' }}>
                  <span style={{ fontSize: '0.7rem', color: '#1D4ED8', fontWeight: 700, display: 'block' }}>CATÁLOGO MEN</span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1E3A8A' }}>
                    {(deptDetail.total_establishments ?? 0).toLocaleString('es-CO')}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: '#475569', display: 'block' }}>
                    Establecimientos ({(deptDetail.total_campuses ?? 0).toLocaleString('es-CO')} sedes)
                  </span>
                </div>
                <div style={{ backgroundColor: '#EEF2FF', padding: '0.75rem', borderRadius: '6px', border: '1px solid #C7D2FE' }}>
                  <span style={{ fontSize: '0.7rem', color: '#4338CA', fontWeight: 700, display: 'block' }}>PIPELINE NTA-04</span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#312E81' }}>
                    {deptDetail.pipeline_in_progress ?? 0}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: '#475569', display: 'block' }}>
                    Solicitudes en trámite
                  </span>
                </div>
                <div style={{ backgroundColor: '#ECFDF5', padding: '0.75rem', borderRadius: '6px', border: '1px solid #A7F3D0' }}>
                  <span style={{ fontSize: '0.7rem', color: '#047857', fontWeight: 700, display: 'block' }}>TENENCIA PEVN</span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#064E3B' }}>
                    {deptDetail.active_institutions ?? 0}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: '#475569', display: 'block' }}>
                    Colegios Activos
                  </span>
                </div>
              </div>

              {/* Municipalities List */}
              <div style={{ border: '1px solid #E2E8F0', borderRadius: '8px', overflow: 'hidden' }}>
                <div style={{ padding: '0.75rem 1rem', backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.875rem', color: '#0F172A' }}>
                    Desglose Municipal ({deptDetail.municipalities?.length ?? 0} Municipios)
                  </span>
                  <input
                    type="text"
                    placeholder="Filtrar municipios..."
                    value={muniSearchTerm}
                    onChange={(e) => setMuniSearchTerm(e.target.value)}
                    style={{
                      padding: '0.35rem 0.6rem',
                      fontSize: '0.8rem',
                      border: '1px solid #CBD5E1',
                      borderRadius: '4px',
                      outline: 'none',
                    }}
                  />
                </div>
                <div style={{ maxHeight: '340px', overflowY: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                    <thead style={{ position: 'sticky', top: 0, backgroundColor: '#F1F5F9' }}>
                      <tr style={{ color: '#475569', borderBottom: '1px solid #CBD5E1' }}>
                        <th style={{ padding: '0.5rem 0.75rem' }}>CÓDIGO</th>
                        <th style={{ padding: '0.5rem 0.75rem' }}>MUNICIPIO</th>
                        <th style={{ padding: '0.5rem 0.75rem' }}>CATÁLOGO MEN</th>
                        <th style={{ padding: '0.5rem 0.75rem' }}>PEVN TENANTS</th>
                        <th style={{ padding: '0.5rem 0.75rem' }}>PIPELINE</th>
                        <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right' }}>ACCIÓN</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredMunicipalities.map((muni) => (
                        <tr key={muni.municipality_code} style={{ borderBottom: '1px solid #F1F5F9' }}>
                          <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'monospace', color: '#64748B' }}>
                            {muni.municipality_code}
                          </td>
                          <td style={{ padding: '0.5rem 0.75rem', fontWeight: 600, color: '#0F172A' }}>
                            {muni.municipality_name}
                          </td>
                          <td style={{ padding: '0.5rem 0.75rem', color: '#334155' }}>
                            {(muni.total_establishments ?? 0)} est. / {(muni.total_campuses ?? 0)} sedes
                          </td>
                          <td style={{ padding: '0.5rem 0.75rem' }}>
                            <span style={{ fontWeight: 700, color: muni.active_institutions > 0 ? '#059669' : '#475569' }}>
                              {muni.active_institutions ?? 0}
                            </span>
                          </td>
                          <td style={{ padding: '0.5rem 0.75rem' }}>
                            <span style={{ fontWeight: 700, color: muni.pipeline_in_progress > 0 ? '#4F46E5' : '#475569' }}>
                              {muni.pipeline_in_progress ?? 0}
                            </span>
                          </td>
                          <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right' }}>
                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.35rem' }}>
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => {
                                  handleCloseDetail()
                                  navigate(`/admin/municipality-admins?municipality_id=${muni.municipality_id}&municipality_code=${muni.municipality_code}`)
                                }}
                                title="Gestionar Administrador Municipal"
                              >
                                Admin Mpal.
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  handleCloseDetail()
                                  navigate(`/admin/onboarding?department_code=${deptDetail.department_code}&municipality_code=${muni.municipality_code}`)
                                }}
                                title="Radicar Institución"
                              >
                                Radicar
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Modal Footer Actions */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', paddingTop: '0.5rem', borderTop: '1px solid #E2E8F0' }}>
                <Button variant="secondary" onClick={handleCloseDetail}>
                  Cerrar
                </Button>
                <Button
                  variant="primary"
                  onClick={() => {
                    handleCloseDetail()
                    navigate(`/admin/onboarding?department_code=${deptDetail.department_code}`)
                  }}
                >
                  Radicar Onboarding en {deptDetail.department_name}
                </Button>
              </div>
            </div>
          ) : null}
        </Modal>
      )}
    </div>
  )
}

export default TerritorialControlCenterView
