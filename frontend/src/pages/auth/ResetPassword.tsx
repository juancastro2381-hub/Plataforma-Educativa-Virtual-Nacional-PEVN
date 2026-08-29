/**
 * PEVN Frontend — Institutional Password Reset Execution Page
 *
 * Validates single-use cryptographic reset token and allows setting a new secure password.
 */

import React, { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { authApi } from '@/services/auth'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { AppApiError } from '@/services/api/client'

export const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [isValidatingToken, setIsValidatingToken] = useState(true)
  const [tokenValid, setTokenValid] = useState(false)
  const [tokenError, setTokenError] = useState<string | null>(null)

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) {
      setIsValidatingToken(false)
      setTokenValid(false)
      setTokenError('El enlace de recuperación no contiene un token válido.')
      return
    }

    const verifyToken = async () => {
      try {
        await authApi.verifyPasswordResetToken({ token })
        setTokenValid(true)
      } catch (err: unknown) {
        setTokenValid(false)
        if (err instanceof AppApiError) {
          setTokenError(err.message)
        } else {
          setTokenError('El token de restablecimiento es inválido o ha expirado.')
        }
      } finally {
        setIsValidatingToken(false)
      }
    }

    verifyToken()
  }, [token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitError(null)

    if (!token) {
      setSubmitError('Token no encontrado.')
      return
    }

    if (newPassword.length < 12) {
      setSubmitError('La nueva contraseña debe tener al menos 12 caracteres.')
      return
    }

    if (newPassword !== confirmPassword) {
      setSubmitError('Las contraseñas no coinciden.')
      return
    }

    setIsSubmitting(true)

    try {
      await authApi.confirmPasswordReset({
        token,
        new_password: newPassword,
      })
      setSuccess(true)
    } catch (err: unknown) {
      if (err instanceof AppApiError) {
        setSubmitError(err.message)
      } else if (err instanceof Error) {
        setSubmitError(err.message)
      } else {
        setSubmitError('Error al restablecer la contraseña. El token pudo haber expirado.')
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

        <div style={{ padding: '2rem' }}>
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                backgroundColor: '#EFF6FF',
                color: '#2563EB',
                fontSize: '1.5rem',
                marginBottom: '1rem',
              }}
            >
              🔒
            </div>
            <h1
              style={{
                fontSize: '1.375rem',
                fontWeight: 700,
                color: '#0F172A',
                margin: '0 0 0.5rem 0',
              }}
            >
              Nueva Contraseña
            </h1>
            <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
              Plataforma Educativa Virtual Nacional (PEvN)
            </p>
          </div>

          {isValidatingToken ? (
            <div style={{ textAlign: 'center', padding: '2rem 0' }}>
              <LoadingSpinner size="lg" />
              <p style={{ marginTop: '1rem', color: '#64748B', fontSize: '0.875rem' }}>
                Verificando validez del enlace...
              </p>
            </div>
          ) : !tokenValid ? (
            <div
              role="alert"
              style={{
                backgroundColor: '#FEF2F2',
                border: '1px solid #FCA5A5',
                borderRadius: '12px',
                padding: '1.5rem',
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>⚠️</div>
              <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#991B1B', marginBottom: '0.5rem' }}>
                Enlace No Válido o Expirado
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#B91C1C', lineHeight: 1.5, margin: '0 0 1.5rem 0' }}>
                {tokenError || 'El token de recuperación es inválido, ya fue utilizado o ha expirado.'}
              </p>
              <Link to="/auth/forgot-password" style={{ textDecoration: 'none' }}>
                <Button variant="primary" fullWidth>
                  Solicitar un Nuevo Enlace
                </Button>
              </Link>
            </div>
          ) : success ? (
            <div
              role="alert"
              style={{
                backgroundColor: '#ECFDF5',
                border: '1px solid #A7F3D0',
                borderRadius: '12px',
                padding: '1.5rem',
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✅</div>
              <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#065F46', marginBottom: '0.5rem' }}>
                Contraseña Actualizada
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#047857', lineHeight: 1.5, margin: '0 0 1.5rem 0' }}>
                Su contraseña ha sido restablecida exitosamente. Puede iniciar sesión con su nueva clave.
              </p>
              <Link to="/login" style={{ textDecoration: 'none' }}>
                <Button variant="primary" fullWidth>
                  Iniciar Sesión →
                </Button>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate>
              {submitError && (
                <div
                  role="alert"
                  style={{
                    backgroundColor: '#FEF2F2',
                    border: '1px solid #FCA5A5',
                    borderRadius: '8px',
                    padding: '0.75rem 1rem',
                    marginBottom: '1.25rem',
                    color: '#991B1B',
                    fontSize: '0.875rem',
                  }}
                >
                  {submitError}
                </div>
              )}

              <div style={{ marginBottom: '1.25rem' }}>
                <label
                  htmlFor="new-password"
                  style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#334155',
                    marginBottom: '0.375rem',
                  }}
                >
                  Nueva Contraseña (mínimo 12 caracteres)
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    id="new-password"
                    type={showPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    disabled={isSubmitting}
                    placeholder="••••••••••••"
                    style={{
                      width: '100%',
                      padding: '0.625rem 2.5rem 0.625rem 0.875rem',
                      fontSize: '0.9375rem',
                      borderRadius: '8px',
                      border: '1px solid #CBD5E1',
                      boxSizing: 'border-box',
                      outline: 'none',
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: 'absolute',
                      right: '0.75rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '1rem',
                    }}
                  >
                    {showPassword ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label
                  htmlFor="confirm-password"
                  style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#334155',
                    marginBottom: '0.375rem',
                  }}
                >
                  Confirmar Contraseña
                </label>
                <input
                  id="confirm-password"
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={isSubmitting}
                  placeholder="••••••••••••"
                  style={{
                    width: '100%',
                    padding: '0.625rem 0.875rem',
                    fontSize: '0.9375rem',
                    borderRadius: '8px',
                    border: '1px solid #CBD5E1',
                    boxSizing: 'border-box',
                    outline: 'none',
                  }}
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                fullWidth
                disabled={isSubmitting}
                style={{ marginBottom: '1rem' }}
              >
                {isSubmitting ? (
                  <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                    <LoadingSpinner size="sm" />
                    Restableciendo...
                  </span>
                ) : (
                  'Restablecer Contraseña'
                )}
              </Button>

              <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                <Link
                  to="/login"
                  style={{
                    fontSize: '0.875rem',
                    color: '#2563EB',
                    textDecoration: 'none',
                    fontWeight: 500,
                  }}
                >
                  ← Volver al Inicio de Sesión
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

export default ResetPassword
