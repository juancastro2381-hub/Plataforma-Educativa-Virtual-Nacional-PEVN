/**
 * PEVN Frontend — Rector Invitation Acceptance & Password Definition
 *
 * Public onboarding screen where an invited Rector verifies their single-use
 * token and securely establishes their personal account password with Argon2id.
 */

import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import authApi from '@/services/auth'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import type { VerifyInvitationResponse } from '@/types'

export const AcceptInvitation: React.FC = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token') || ''

  // Verification State
  const [isVerifying, setIsVerifying] = useState<boolean>(true)
  const [invitationData, setInvitationData] = useState<VerifyInvitationResponse | null>(null)
  const [verifyError, setVerifyError] = useState<string | null>(null)

  // Form State
  const [password, setPassword] = useState<string>('')
  const [passwordConfirmation, setPasswordConfirmation] = useState<string>('')
  const [showPassword, setShowPassword] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSuccess, setIsSuccess] = useState<boolean>(false)

  // Step 1: Verify token on load
  useEffect(() => {
    if (!token || !token.trim()) {
      setIsVerifying(false)
      setVerifyError('No se suministró un token de invitación válido en el enlace.')
      return
    }

    const verify = async () => {
      setIsVerifying(true)
      setVerifyError(null)
      try {
        const data = await authApi.verifyInvitation(token.trim())
        if (data.valid) {
          setInvitationData(data)
        } else {
          setVerifyError('La invitación no es válida o ha sido revocada.')
        }
      } catch (err: unknown) {
        const msg =
          err instanceof Error
            ? err.message
            : 'El enlace de invitación ha expirado, ya fue utilizado o no es válido.'
        setVerifyError(msg)
      } finally {
        setIsVerifying(false)
      }
    }

    void verify()
  }, [token])

  // Step 2: Handle password onboarding submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitError(null)

    if (password.length < 8) {
      setSubmitError('La contraseña debe contener al menos 8 caracteres.')
      return
    }

    if (password !== passwordConfirmation) {
      setSubmitError('Las contraseñas ingresadas no coinciden.')
      return
    }

    setIsSubmitting(true)
    try {
      await authApi.acceptInvitation({
        token: token.trim(),
        password,
        password_confirmation: passwordConfirmation,
      })
      setIsSuccess(true)
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Error al activar la cuenta. Por favor intente nuevamente o solicite una nueva invitación.'
      setSubmitError(msg)
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
      <div style={{ width: '100%', maxWidth: '480px' }}>
        {/* Verification Loader */}
        {isVerifying && (
          <Card style={{ textAlign: 'center', padding: '3rem 1.5rem' }}>
            <LoadingSpinner size="lg" label="Validando token de invitación..." />
            <p style={{ marginTop: '1.5rem', color: '#64748B', fontSize: '0.875rem' }}>
              Verificando credencial de acceso institucional...
            </p>
          </Card>
        )}

        {/* Invalid / Expired State */}
        {!isVerifying && verifyError && (
          <Card style={{ textAlign: 'center', padding: '2.5rem 1.5rem' }}>
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                backgroundColor: '#FEF2F2',
                color: '#DC2626',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.75rem',
                margin: '0 auto 1.5rem',
              }}
            >
              ⚠️
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0F172A', marginBottom: '0.75rem' }}>
              Enlace de Invitación No Válido
            </h2>
            <p style={{ color: '#64748B', fontSize: '0.875rem', lineHeight: 1.5, marginBottom: '1.5rem' }}>
              {verifyError}
            </p>
            <div
              style={{
                backgroundColor: '#F8FAFC',
                borderRadius: '8px',
                border: '1px solid #E2E8F0',
                padding: '1rem',
                fontSize: '0.8125rem',
                color: '#475569',
                marginBottom: '1.5rem',
                textAlign: 'left',
              }}
            >
              💡 <strong>¿Qué debe hacer?</strong>
              <ul style={{ margin: '0.5rem 0 0 1.25rem', padding: 0 }}>
                <li>Los enlaces de invitación tienen una vigencia de 48 horas.</li>
                <li>Cada enlace solo puede ser utilizado una única vez.</li>
                <li>Comuníquese con el Administrador Nacional para solicitar la reemisión de su invitación.</li>
              </ul>
            </div>
            <Link to="/login" style={{ textDecoration: 'none' }}>
              <Button variant="primary" fullWidth>
                Ir a Iniciar Sesión
              </Button>
            </Link>
          </Card>
        )}

        {/* Success State */}
        {!isVerifying && isSuccess && (
          <Card style={{ textAlign: 'center', padding: '2.5rem 1.5rem' }}>
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                backgroundColor: '#F0FDF4',
                color: '#16A34A',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '2rem',
                margin: '0 auto 1.5rem',
              }}
            >
              ✓
            </div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0F172A', marginBottom: '0.5rem' }}>
              ¡Cuenta Activada Exitosamente!
            </h2>
            <p style={{ color: '#64748B', fontSize: '0.875rem', lineHeight: 1.5, marginBottom: '1.5rem' }}>
              Su contraseña ha sido cifrada y almacenada con seguridad. Su cuenta de Rector institucional está lista para operar.
            </p>
            <div
              style={{
                backgroundColor: '#F8FAFC',
                borderRadius: '8px',
                border: '1px solid #E2E8F0',
                padding: '1rem',
                fontSize: '0.8125rem',
                color: '#334155',
                marginBottom: '1.5rem',
                textAlign: 'left',
              }}
            >
              <div><strong>Institución:</strong> {invitationData?.institution_name}</div>
              <div><strong>Usuario:</strong> {invitationData?.email}</div>
            </div>
            <Button
              variant="primary"
              fullWidth
              onClick={() => navigate('/login')}
              style={{ backgroundColor: '#2563EB', fontWeight: 700 }}
            >
              Iniciar Sesión Ahora →
            </Button>
          </Card>
        )}

        {/* Active Onboarding Form */}
        {!isVerifying && !verifyError && !isSuccess && invitationData && (
          <Card style={{ padding: '2rem' }}>
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <div
                style={{
                  display: 'inline-block',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  backgroundColor: 'rgba(37, 99, 235, 0.1)',
                  color: '#2563EB',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '9999px',
                  marginBottom: '0.5rem',
                }}
              >
                Onboarding de Rector • PEVN
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0F172A', margin: '0.25rem 0' }}>
                Bienvenido, {invitationData.first_name}
              </h2>
              <p style={{ color: '#64748B', fontSize: '0.875rem', margin: 0 }}>
                {invitationData.institution_name}
              </p>
            </div>

            <div
              style={{
                backgroundColor: '#F8FAFC',
                borderRadius: '8px',
                border: '1px solid #E2E8F0',
                padding: '0.875rem',
                fontSize: '0.8125rem',
                color: '#475569',
                marginBottom: '1.25rem',
              }}
            >
              <div><strong>Correo Asignado:</strong> {invitationData.email}</div>
              <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>
                Establezca su contraseña personal para activar su acceso rectoral.
              </div>
            </div>

            {submitError && (
              <div style={{ marginBottom: '1rem' }}>
                <Alert variant="error">{submitError}</Alert>
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                  Definir Contraseña *
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Mínimo 8 caracteres"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                    style={{
                      width: '100%',
                      padding: '0.625rem 2.5rem 0.625rem 0.75rem',
                      borderRadius: '6px',
                      border: '1px solid #CBD5E1',
                      fontSize: '0.875rem',
                      outline: 'none',
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: 'absolute',
                      right: '0.5rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      color: '#64748B',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                    }}
                  >
                    {showPassword ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontWeight: 700, fontSize: '0.875rem', color: '#1E293B', marginBottom: '0.35rem' }}>
                  Confirmar Contraseña *
                </label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Repita la contraseña"
                  value={passwordConfirmation}
                  onChange={(e) => setPasswordConfirmation(e.target.value)}
                  required
                  minLength={8}
                  style={{
                    width: '100%',
                    padding: '0.625rem 0.75rem',
                    borderRadius: '6px',
                    border: '1px solid #CBD5E1',
                    fontSize: '0.875rem',
                    outline: 'none',
                  }}
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                fullWidth
                disabled={isSubmitting || password.length < 8 || password !== passwordConfirmation}
                style={{
                  backgroundColor: '#2563EB',
                  fontWeight: 700,
                  padding: '0.75rem',
                  marginTop: '0.5rem',
                }}
              >
                {isSubmitting ? 'Activando Cuenta...' : 'Activar Cuenta de Rector'}
              </Button>
            </form>
          </Card>
        )}
      </div>
    </div>
  )
}

export default AcceptInvitation
