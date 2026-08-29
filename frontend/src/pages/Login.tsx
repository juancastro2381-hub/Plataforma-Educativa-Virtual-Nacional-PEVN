/**
 * PEVN Frontend — Institutional Login Page
 *
 * Government-grade authentication interface designed for Colombian public schools.
 * Accessible, secure, responsive, with robust form validation and error handling.
 */

import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { AppApiError } from '@/services/api/client'

export const Login: React.FC = () => {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Redirect destination after successful login
  const locationState = location.state as { from?: { pathname?: string } } | null
  const from = locationState?.from?.pathname ?? '/dashboard'

  // If already authenticated, redirect to destination
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, navigate, from])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    if (!username.trim()) {
      setErrorMessage('Por favor ingrese su usuario o correo institucional.')
      return
    }

    if (!password) {
      setErrorMessage('Por favor ingrese su contraseña.')
      return
    }

    setIsSubmitting(true)

    try {
      await login({
        username: username.trim(),
        password,
      })
      navigate(from, { replace: true })
    } catch (err: unknown) {
      if (err instanceof AppApiError) {
        setErrorMessage(err.message)
      } else if (err instanceof Error) {
        setErrorMessage(err.message)
      } else {
        setErrorMessage('Error al autenticar. Verifique sus credenciales.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '80vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem 1rem',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          boxShadow: '0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.05)',
          border: '1px solid #E2E8F0',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* Colombian Flag Header Accent Stripe */}
        <div style={{ height: '6px', width: '100%', display: 'flex' }}>
          <div style={{ flex: 2, backgroundColor: '#FCD116' }} />
          <div style={{ flex: 1, backgroundColor: '#003893' }} />
          <div style={{ flex: 1, backgroundColor: '#CE1126' }} />
        </div>

        <div style={{ padding: '2.5rem 2rem' }}>
          {/* Institution Header */}
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '56px',
                height: '56px',
                borderRadius: '14px',
                backgroundColor: '#0F172A',
                color: '#FFFFFF',
                fontWeight: 800,
                fontSize: '1.25rem',
                marginBottom: '1rem',
                letterSpacing: '0.05em',
              }}
            >
              PEVN
            </div>
            <h1
              style={{
                fontSize: '1.5rem',
                fontWeight: 800,
                color: '#0F172A',
                marginBottom: '0.35rem',
                letterSpacing: '-0.025em',
              }}
            >
              Inicio de Sesión
            </h1>
            <p style={{ fontSize: '0.875rem', color: '#64748B', lineHeight: 1.4 }}>
              Plataforma Educativa Virtual Nacional
            </p>
          </div>

          {/* Error Alert */}
          {errorMessage && (
            <div
              style={{
                marginBottom: '1.5rem',
                padding: '0.875rem 1rem',
                borderRadius: '8px',
                backgroundColor: '#FEF2F2',
                border: '1px solid #FCA5A5',
                color: '#991B1B',
                fontSize: '0.875rem',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.5rem',
              }}
              role="alert"
              aria-live="assertive"
            >
              <span style={{ fontWeight: 'bold' }}>!</span>
              <div style={{ flex: 1 }}>{errorMessage}</div>
            </div>
          )}

          {/* Form */}
          <form
            onSubmit={(e) => {
              void handleSubmit(e)
            }}
            noValidate
          >
            <div style={{ marginBottom: '1.25rem' }}>
              <label
                htmlFor="username"
                style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#1E293B',
                  marginBottom: '0.5rem',
                }}
              >
                Usuario o Correo Institucional
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value)
                }}
                placeholder="ej: usuario@pevn.edu.co o doc_cc123"
                disabled={isSubmitting}
                required
                autoComplete="username"
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem',
                  fontSize: '0.95rem',
                  border: '1px solid #CBD5E1',
                  borderRadius: '8px',
                  outline: 'none',
                  boxSizing: 'border-box',
                  transition: 'border-color 0.15s ease',
                }}
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.5rem',
                }}
              >
                <label
                  htmlFor="password"
                  style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#1E293B',
                  }}
                >
                  Contraseña
                </label>
                <Link
                  to="/auth/forgot-password"
                  style={{
                    fontSize: '0.8125rem',
                    color: '#2563EB',
                    textDecoration: 'none',
                    fontWeight: 500,
                  }}
                >
                  ¿Olvidó su contraseña?
                </Link>
              </div>
              <div style={{ position: 'relative' }}>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                  }}
                  placeholder="Ingrese su contraseña"
                  disabled={isSubmitting}
                  required
                  autoComplete="current-password"
                  style={{
                    width: '100%',
                    padding: '0.75rem 2.75rem 0.75rem 1rem',
                    fontSize: '0.95rem',
                    border: '1px solid #CBD5E1',
                    borderRadius: '8px',
                    outline: 'none',
                    boxSizing: 'border-box',
                    transition: 'border-color 0.15s ease',
                  }}
                />
                <button
                  type="button"
                  onClick={() => {
                    setShowPassword(!showPassword)
                  }}
                  aria-label={showPassword ? 'Ocultar contraseña' : 'Ver contraseña'}
                  style={{
                    position: 'absolute',
                    right: '0.75rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    color: '#64748B',
                    cursor: 'pointer',
                    fontSize: '0.8125rem',
                    padding: '0.25rem',
                  }}
                >
                  {showPassword ? 'Ocultar' : 'Ver'}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={isSubmitting}
              style={{
                width: '100%',
                justifyContent: 'center',
                fontWeight: 600,
                backgroundColor: '#0F172A',
              }}
            >
              {isSubmitting ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span style={{ marginLeft: '0.5rem' }}>Verificando credenciales...</span>
                </>
              ) : (
                'Iniciar Sesión'
              )}
            </Button>
          </form>

          {/* Footer Info */}
          <div
            style={{
              marginTop: '2rem',
              paddingTop: '1.5rem',
              borderTop: '1px solid #F1F5F9',
              textAlign: 'center',
              fontSize: '0.8125rem',
              color: '#94A3B8',
            }}
          >
            Sistema de Acceso Seguro por Diseño (Argon2id / HttpOnly Strict)
            <br />
            Ministerio de Educación Nacional — Colombia
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
