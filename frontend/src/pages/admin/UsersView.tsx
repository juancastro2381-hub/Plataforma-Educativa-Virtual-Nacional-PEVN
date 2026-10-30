/**
 * PEVN Frontend — Institutional & Territorial Users Directory View
 *
 * Professional read-only directory interface for exploring users within
 * the authenticated user's territorial or institutional scope.
 * Protected by RBAC permission: 'users:read'.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { usersApi } from '@/services/users'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Modal } from '@/components/ui/Modal'
import { useAuth } from '@/hooks/useAuth'
import type { UserResponse } from '@/types'

export const UsersView: React.FC = () => {
  const { user } = useAuth()

  const [users, setUsers] = useState<UserResponse[]>([])
  const [total, setTotal] = useState<number>(0)
  const [page, setPage] = useState<number>(1)
  const [pageSize] = useState<number>(15)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [error, setError] = useState<string | null>(null)

  // Selected User Detail Modal
  const [selectedUser, setSelectedUser] = useState<UserResponse | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState<boolean>(false)

  const fetchUsers = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const params: {
        search?: string
        is_active?: boolean
        page: number
        page_size: number
      } = {
        page,
        page_size: pageSize,
      }

      if (searchQuery.trim()) {
        params.search = searchQuery.trim()
      }
      if (statusFilter === 'active') {
        params.is_active = true
      } else if (statusFilter === 'inactive') {
        params.is_active = false
      }

      const res = await usersApi.searchUsers(params)
      setUsers(res.items)
      setTotal(res.total)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar directorio de usuarios.'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [page, pageSize, searchQuery, statusFilter])

  useEffect(() => {
    void fetchUsers()
  }, [fetchUsers])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    void fetchUsers()
  }

  const handleClearFilters = () => {
    setSearchQuery('')
    setStatusFilter('all')
    setPage(1)
  }

  const formatRoleName = (role: string) => {
    const map: Record<string, string> = {
      superadmin: 'Super Administrador',
      national_admin: 'Administrador Nacional',
      department_admin: 'Administrador Departamental',
      municipality_admin: 'Administrador Municipal',
      rector: 'Rector / Director',
      institution_admin: 'Admin Institucional',
      coordinator: 'Coordinador',
      academic_coordinator: 'Coordinador Académico',
      teacher: 'Docente',
      student: 'Estudiante',
      guardian: 'Acudiente / Tutor',
    }
    return map[role] || role
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '2rem auto', padding: '0 1rem' }} id="users-directory-page">
      {/* Top Banner */}
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
              Gestión Educativa • Directorio de Usuarios
            </span>
            {user?.scope.jurisdiction_name && (
              <Badge variant="neutral">
                Jurisdicción: {user.scope.jurisdiction_name}
              </Badge>
            )}
          </div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 800, margin: '0.25rem 0', color: '#FFFFFF' }}>
            Directorio de Usuarios
          </h1>
          <p style={{ color: '#CBD5E1', fontSize: '0.9375rem', margin: 0, maxWidth: '650px' }}>
            Consulta e inspección de identidades, credenciales institucionales y roles activos en su jurisdicción.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <Button
            variant="secondary"
            onClick={() => void fetchUsers()}
            id="btn-refresh-users"
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
        <div style={{ marginBottom: '1.5rem' }}>
          <div
            role="alert"
            style={{
              backgroundColor: '#FEF2F2',
              border: '1px solid #FCA5A5',
              borderRadius: '8px',
              padding: '1rem',
              color: '#991B1B',
              fontSize: '0.875rem',
            }}
          >
            ⚠️ {error}
          </div>
        </div>
      )}

      {/* Filters Card */}
      <Card style={{ marginBottom: '1.5rem' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ flex: '1 1 300px' }}>
            <label
              htmlFor="user-search-input"
              style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Buscar por Nombre, Cédula, Correo o Usuario
            </label>
            <input
              id="user-search-input"
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Ej. Carlos Pérez, 1085234567, carlos@pevn.edu.co"
              style={{
                width: '100%',
                padding: '0.55rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                color: '#0F172A',
              }}
            />
          </div>

          <div style={{ width: '200px' }}>
            <label
              htmlFor="user-status-select"
              style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}
            >
              Estado de Cuenta
            </label>
            <select
              id="user-status-select"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as 'all' | 'active' | 'inactive')
                setPage(1)
              }}
              style={{
                width: '100%',
                padding: '0.55rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.875rem',
                color: '#0F172A',
                backgroundColor: '#FFFFFF',
              }}
            >
              <option value="all">Todos los Estados</option>
              <option value="active">Solo Activos</option>
              <option value="inactive">Solo Inactivos</option>
            </select>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Button type="submit" variant="primary" id="btn-search-users">
              🔍 Buscar
            </Button>
            {(searchQuery || statusFilter !== 'all') && (
              <Button type="button" variant="secondary" onClick={handleClearFilters} id="btn-clear-users">
                Limpiar
              </Button>
            )}
          </div>
        </form>
      </Card>

      {/* Users Table */}
      <Card
        title="Usuarios en Jurisdicción"
        subtitle={`Total de usuarios registrados: ${String(total)}`}
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size="lg" />
            <p style={{ marginTop: '0.75rem', color: '#64748B', fontSize: '0.875rem' }}>
              Cargando directorio de usuarios...
            </p>
          </div>
        ) : users.length === 0 ? (
          <EmptyState
            icon="👥"
            title="No se encontraron usuarios"
            description="No hay usuarios que coincidan con los criterios de búsqueda en su jurisdicción territorial."
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table
              id="users-table"
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '0.875rem',
                textAlign: 'left',
              }}
            >
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Documento</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Nombre Completo</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Usuario / Correo</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Roles Asignados</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Estado</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Detalle</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr
                    key={u.id}
                    id={`user-row-${u.id}`}
                    style={{
                      borderBottom: '1px solid #F1F5F9',
                      transition: 'background-color 150ms',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8FAFC')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <td style={{ padding: '1rem' }}>
                      <span
                        style={{
                          fontFamily: 'monospace',
                          fontWeight: 700,
                          color: '#1E293B',
                          backgroundColor: '#E2E8F0',
                          padding: '0.2rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.8125rem',
                        }}
                      >
                        {u.document_type ? `${u.document_type} ` : ''}{u.document_number || 'N/A'}
                      </span>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ fontWeight: 700, color: '#0F172A' }}>
                        {u.first_name} {u.last_name}
                      </div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ fontWeight: 600, color: '#334155' }}>@{u.username}</div>
                      <div style={{ fontSize: '0.75rem', color: '#64748B' }}>{u.email}</div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                        {Array.isArray(u.roles) && u.roles.length > 0 ? (
                          u.roles.map((r: string) => (
                            <Badge key={r} variant="neutral">
                              {formatRoleName(r)}
                            </Badge>
                          ))
                        ) : Array.isArray(u.roles) && u.roles.length === 0 ? (
                          <span style={{ color: '#94A3B8', fontSize: '0.75rem' }}>Sin roles</span>
                        ) : (
                          <span style={{ color: '#E11D48', fontSize: '0.75rem' }}>Error en formato de roles</span>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <Badge variant={u.is_active ? 'success' : 'danger'}>
                        {u.is_active ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      <Button
                        variant="ghost"
                        size="sm"
                        id={`btn-view-user-${u.id}`}
                        onClick={() => {
                          setSelectedUser(u)
                          setIsDetailOpen(true)
                        }}
                      >
                        👁️ Ver Ficha
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {total > pageSize && (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '1rem 0',
                  marginTop: '1rem',
                  borderTop: '1px solid #E2E8F0',
                  fontSize: '0.875rem',
                  color: '#64748B',
                }}
              >
                <div>
                  Mostrando página {page} de {Math.ceil(total / pageSize)} ({total} registros)
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={page >= Math.ceil(total / pageSize)}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Siguiente
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* User Details Modal */}
      {selectedUser && (
        <Modal
          isOpen={isDetailOpen}
          onClose={() => {
            setIsDetailOpen(false)
            setSelectedUser(null)
          }}
          title={`Ficha de Usuario: ${selectedUser.first_name} ${selectedUser.last_name}`}
          subtitle={`Identificador único de sistema: ${selectedUser.id}`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.875rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <span style={{ color: '#64748B', fontSize: '0.75rem', fontWeight: 600 }}>DOCUMENTO</span>
                <p style={{ margin: '0.25rem 0', fontWeight: 700, color: '#0F172A' }}>
                  {selectedUser.document_type} {selectedUser.document_number}
                </p>
              </div>
              <div>
                <span style={{ color: '#64748B', fontSize: '0.75rem', fontWeight: 600 }}>NOMBRE DE USUARIO</span>
                <p style={{ margin: '0.25rem 0', fontWeight: 700, color: '#0F172A' }}>
                  @{selectedUser.username}
                </p>
              </div>
              <div>
                <span style={{ color: '#64748B', fontSize: '0.75rem', fontWeight: 600 }}>CORREO ELECTRÓNICO</span>
                <p style={{ margin: '0.25rem 0', fontWeight: 700, color: '#0F172A' }}>
                  {selectedUser.email}
                </p>
              </div>
              <div>
                <span style={{ color: '#64748B', fontSize: '0.75rem', fontWeight: 600 }}>TELÉFONO</span>
                <p style={{ margin: '0.25rem 0', fontWeight: 700, color: '#0F172A' }}>
                  {selectedUser.phone_number || 'No registrado'}
                </p>
              </div>
            </div>

            <div>
              <span style={{ color: '#64748B', fontSize: '0.75rem', fontWeight: 600 }}>ROLES ATÓMICOS ASIGNADOS</span>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.35rem' }}>
                {Array.isArray(selectedUser.roles) && selectedUser.roles.length > 0 ? (
                  selectedUser.roles.map((r: string) => (
                    <Badge key={r} variant="primary">
                      {formatRoleName(r)}
                    </Badge>
                  ))
                ) : Array.isArray(selectedUser.roles) && selectedUser.roles.length === 0 ? (
                  <span style={{ color: '#94A3B8', fontSize: '0.8125rem' }}>Sin roles</span>
                ) : (
                  <span style={{ color: '#E11D48', fontSize: '0.8125rem' }}>Error en formato de roles</span>
                )}
              </div>
            </div>

            <div>
              <span style={{ color: '#64748B', fontSize: '0.75rem', fontWeight: 600 }}>ESTADO DE CUENTA</span>
              <div style={{ marginTop: '0.35rem' }}>
                <Badge variant={selectedUser.is_active ? 'success' : 'danger'}>
                  {selectedUser.is_active ? 'Cuenta Activa' : 'Cuenta Inactiva / Suspendida'}
                </Badge>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

export default UsersView
