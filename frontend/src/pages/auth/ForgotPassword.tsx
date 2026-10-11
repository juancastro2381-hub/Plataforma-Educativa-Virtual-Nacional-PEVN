/**
 * PEVN Frontend — Institutional Password Recovery (Forgot Password) Page
 *
 * Accessible, secure interface for requesting password reset instructions.
 * Implements anti-enumeration constant feedback.
 */

import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { authApi } from '@/services/auth'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { AppApiError } from '@/services/api/client'

export const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [devRecoveryUrl, setDevRecoveryUrl] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    if (!email.trim()) {
      setErrorMessage('Por favor ingrese su correo electrónico registrado.')
      return
    }

    setIsSubmitting(true)

    try {
      const response = await authApi.requestPasswordReset({ email: email.trim() })
      const devUrl =
        response?.development_recovery_url ||
        response?.development_recovery_link ||
        null
      setDevRecoveryUrl(devUrl)
      setSubmitted(true)
    } catch (err: unknown) {
      if (err instanceof AppApiError) {
        setErrorMessage(err.message)
      } else if (err instanceof Error) {
        setErrorMessage(err.message)
      } else {
        setErrorMessage('Ocurrió un error al procesar la solicitud. Intente nuevamente.')
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
              🔑
            </div>
            <h1
              style={{
                fontSize: '1.375rem',
                fontWeight: 700,
                color: '#0F172A',
                margin: '0 0 0.5rem 0',
              }}
            >
              Recuperación de Contraseña
            </h1>
            <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
              Plataforma Educativa Virtual Nacional (PEvN)
            </p>
          </div>

          {submitted ? (
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
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✉️</div>
              <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#065F46', marginBottom: '0.5rem' }}>
                Instrucciones Enviadas
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#047857', lineHeight: 1.5, margin: '0 0 1.5rem 0' }}>
                Si la dirección de correo electrónico se encuentra registrada y activa, recibirá un enlace seguro con instrucciones para restablecer su contraseña.
              </p>
              <Link to="/login" style={{ textDecoration: 'none' }}>
                <Button variant="primary" fullWidth>
                  ← Volver al Inicio de Sesión
                </Button>
              </Link>

              {devRecoveryUrl && (
                <div
                  role="region"
                  aria-label="Enlace de Desarrollo"
                  style={{
                    marginTop: '1.5rem',
                    padding: '1.25rem',
                    backgroundColor: '#FFFBEB',
                    border: '2px dashed #D97706',
                    borderRadius: '12px',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '1.25rem' }}>🛠️</span>
                    <span
                      style={{
                        fontWeight: 700,
                        fontSize: '0.8125rem',
                        color: '#92400E',
                        letterSpacing: '0.05em',
                        textTransform: 'uppercase',
                      }}
                    >
                      ENLACE DE DESARROLLO
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: '#B45309', margin: '0 0 0.875rem 0', lineHeight: 1.4 }}>
                    SMTP no está configurado. Este enlace se muestra únicamente para pruebas locales y nunca estará disponible en producción.
                  </p>
                  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.875rem' }}>
                    <input
                      type="text"
                      readOnly
                      value={devRecoveryUrl}
                      aria-label="URL de recuperación para desarrollo"
                      style={{
                        flex: 1,
                        padding: '0.5rem 0.625rem',
                        fontSize: '0.75rem',
                        fontFamily: 'monospace',
                        backgroundColor: '#FFFFFF',
                        border: '1px solid #D97706',
                        borderRadius: '6px',
                        color: '#1E293B',
                        outline: 'none',
                      }}
                    />
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => {
                        navigator.clipboard.writeText(devRecoveryUrl)
                        setCopied(true)
                        setTimeout(() => setCopied(false), 2500)
                      }}
                      style={{ whiteSpace: 'nowrap', fontSize: '0.75rem', padding: '0.5rem 0.75rem' }}
                    >
                      {copied ? '¡Copiado!' : 'Copiar'}
                    </Button>
                  </div>
                  <a
                    href={devRecoveryUrl}
                    style={{ textDecoration: 'none', display: 'block' }}
                  >
                    <Button
                      type="button"
                      variant="primary"
                      fullWidth
                      style={{
                        backgroundColor: '#D97706',
                        borderColor: '#B45309',
                        fontWeight: 600,
                      }}
                    >
                      Probar recuperación →
                    </Button>
                  </a>
                </div>
              )}
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate>
              {errorMessage && (
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
                  {errorMessage}
                </div>
              )}

              <p style={{ fontSize: '0.875rem', color: '#475569', lineHeight: 1.5, marginBottom: '1.25rem' }}>
                Ingrese su dirección de correo electrónico institucional registrada. Le enviaremos un enlace de un solo uso válido por 1 hora.
              </p>

              <div style={{ marginBottom: '1.5rem' }}>
                <label
                  htmlFor="email"
                  style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#334155',
                    marginBottom: '0.375rem',
                  }}
                >
                  Correo Electrónico
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="usuario@colegio.edu.co"
                  required
                  disabled={isSubmitting}
                  style={{
                    width: '100%',
                    padding: '0.625rem 0.875rem',
                    fontSize: '0.9375rem',
                    borderRadius: '8px',
                    border: '1px solid #CBD5E1',
                    boxSizing: 'border-box',
                    outline: 'none',
                    transition: 'border-color 150ms',
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
                    Enviando enlace...
                  </span>
                ) : (
                  'Enviar Enlace de Recuperación'
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

export default ForgotPassword
