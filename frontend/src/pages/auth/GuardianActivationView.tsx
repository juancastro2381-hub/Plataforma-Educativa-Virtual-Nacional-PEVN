/**
 * PEVN Frontend — Guardian Account Self-Activation View
 *
 * Public onboarding interface for legal guardians (Acudientes) to verify their
 * single-use cryptographic activation token, establish their account password,
 * or request activation for enrolled students.
 */

import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import authApi from '@/services/auth'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import type { DocumentType, VerifyGuardianTokenResponse } from '@/types'

export const GuardianActivationView: React.FC = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const urlToken = searchParams.get('token') || ''

  // Mode: 'redeem' (has token or entering token) or 'request' (requesting token)
  const [activeTab, setActiveTab] = useState<'redeem' | 'request'>(urlToken ? 'redeem' : 'redeem')

  // Redeem State
  const [tokenInput, setTokenInput] = useState<string>(urlToken)
  const [isVerifying, setIsVerifying] = useState<boolean>(false)
  const [tokenData, setTokenData] = useState<VerifyGuardianTokenResponse | null>(null)
  const [verifyError, setVerifyError] = useState<string | null>(null)

  // Password Setup State
  const [password, setPassword] = useState<string>('')
  const [passwordConfirmation, setPasswordConfirmation] = useState<string>('')
  const [showPassword, setShowPassword] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSuccess, setIsSuccess] = useState<boolean>(false)

  // Request Activation State
  const [reqSimat, setReqSimat] = useState<string>('')
  const [reqDocType, setReqDocType] = useState<DocumentType>('CC')
  const [reqDocNumber, setReqDocNumber] = useState<string>('')
  const [reqEmail, setReqEmail] = useState<string>('')
  const [isRequesting, setIsRequesting] = useState<boolean>(false)
  const [requestSuccessMsg, setRequestSuccessMsg] = useState<string | null>(null)
  const [requestErrorMsg, setRequestErrorMsg] = useState<string | null>(null)

  // Verify token when urlToken changes
  useEffect(() => {
    if (urlToken && urlToken.trim()) {
      setTokenInput(urlToken.trim())
      void verifyToken(urlToken.trim())
    }
  }, [urlToken])

  const verifyToken = async (tok: string) => {
    if (!tok || !tok.trim()) {
      setVerifyError('Por favor ingrese un token de activación.')
      return
    }
    setIsVerifying(true)
    setVerifyError(null)
    setTokenData(null)
    try {
      const data = await authApi.verifyGuardianToken(tok.trim())
      if (data.valid) {
        setTokenData(data)
      } else {
        setVerifyError('El enlace de activación no es válido, ya fue utilizado o ha expirado.')
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'El enlace o token de activación ha expirado, ya fue utilizado o no es válido.'
      setVerifyError(msg)
    } finally {
      setIsVerifying(false)
    }
  }

  const handleManualVerify = (e: React.FormEvent) => {
    e.preventDefault()
    void verifyToken(tokenInput)
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
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
      await authApi.acceptGuardianActivation({
        token: tokenInput.trim(),
        password,
        password_confirmation: passwordConfirmation,
      })
      setIsSuccess(true)
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Error al activar la cuenta de acudiente. Por favor intente nuevamente o solicite un nuevo enlace.'
      setSubmitError(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRequestSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setRequestErrorMsg(null)
    setRequestSuccessMsg(null)

    if (!reqSimat.trim() || !reqDocNumber.trim() || !reqEmail.trim()) {
      setRequestErrorMsg('Por favor complete todos los campos obligatorios.')
      return
    }

    setIsRequesting(true)
    try {
      const res = await authApi.requestGuardianActivation({
        student_code_simat: reqSimat.trim(),
        guardian_document_type: reqDocType,
        guardian_document_number: reqDocNumber.trim(),
        email: reqEmail.trim(),
      })
      setRequestSuccessMsg(res.message || 'Si los datos coinciden con un acudiente vinculado, se enviará el enlace de activación a su correo.')
      if (res.raw_activation_token) {
        setTokenInput(res.raw_activation_token)
        setActiveTab('redeem')
        void verifyToken(res.raw_activation_token)
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Si los datos corresponden a un acudiente y estudiante matriculado, recibirá instrucciones en su correo.'
      setRequestErrorMsg(msg)
    } finally {
      setIsRequesting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="flex justify-center mb-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white font-bold text-xl">
            👪
          </div>
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Plataforma Educativa Virtual Nacional
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Activación y Configuración de Cuenta para Acudientes
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-lg">
        {/* Navigation Tabs */}
        {!isSuccess && (
          <div className="flex bg-slate-800/80 p-1 rounded-t-xl border-t border-x border-slate-700/60 max-w-lg mx-auto">
            <button
              type="button"
              onClick={() => setActiveTab('redeem')}
              className={`flex-1 py-2.5 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'redeem'
                  ? 'bg-cyan-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              🔑 Canjear Token / Enlace
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('request')}
              className={`flex-1 py-2.5 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'request'
                  ? 'bg-cyan-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              🛡️ Solicitar Activación
            </button>
          </div>
        )}

        <Card className="bg-slate-800/90 border-slate-700/80 shadow-2xl p-6 sm:p-8 rounded-b-xl rounded-t-none">
          {/* SUCCESS SCREEN */}
          {isSuccess ? (
            <div className="text-center py-4 space-y-4">
              <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/30 rounded-full flex items-center justify-center mx-auto text-emerald-400 text-2xl font-bold">
                ✓
              </div>
              <h3 className="text-xl font-semibold text-white">
                ¡Cuenta de Acudiente Activada!
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed">
                Su contraseña ha sido definida con seguridad <strong>Argon2id</strong>. Ahora puede
                iniciar sesión en el portal institucional de acudientes y supervisar a sus hijos o acudidos.
              </p>
              <div className="pt-4">
                <Button
                  type="button"
                  variant="primary"
                  className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-medium py-2.5"
                  onClick={() => navigate('/login')}
                >
                  Iniciar Sesión como Acudiente
                </Button>
              </div>
            </div>
          ) : activeTab === 'redeem' ? (
            /* TAB 1: REDEEM TOKEN & SET PASSWORD */
            <div>
              {/* Step A: If token is not yet verified */}
              {!tokenData ? (
                <form onSubmit={handleManualVerify} className="space-y-4">
                  <div className="text-center pb-2">
                    <h3 className="text-base font-semibold text-slate-200">
                      Ingrese su Token de Activación
                    </h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Si recibió un enlace o token por parte de la institución o por correo, ingréselo a continuación.
                    </p>
                  </div>

                  {verifyError && (
                    <Alert variant="error" className="text-xs">
                      {verifyError}
                    </Alert>
                  )}

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Token Criptográfico de Activación
                    </label>
                    <input
                      type="text"
                      required
                      value={tokenInput}
                      onChange={(e) => setTokenInput(e.target.value)}
                      placeholder="pevn_act_..."
                      className="w-full px-3.5 py-2.5 bg-slate-900/90 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 font-mono"
                    />
                  </div>

                  <Button
                    type="submit"
                    variant="primary"
                    className="w-full bg-cyan-600 hover:bg-cyan-500 text-white py-2.5 text-sm"
                    disabled={isVerifying || !tokenInput.trim()}
                  >
                    {isVerifying ? (
                      <span className="flex items-center justify-center gap-2">
                        <LoadingSpinner size="sm" /> Validando Token...
                      </span>
                    ) : (
                      'Validar Token y Continuar'
                    )}
                  </Button>
                </form>
              ) : (
                /* Step B: Token Verified -> Password Setup Form */
                <form onSubmit={handlePasswordSubmit} className="space-y-5">
                  <div className="bg-slate-900/80 border border-cyan-500/30 rounded-xl p-4 space-y-2">
                    <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
                      🛡️ Activación Verificada
                    </div>
                    <div className="text-sm text-slate-200 font-medium">
                      {tokenData.guardian_name}
                    </div>
                    <div className="text-xs text-slate-400">
                      Estudiante:{' '}
                      <span className="text-slate-300 font-medium">
                        {tokenData.student_name}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400">
                      Institución:{' '}
                      <span className="text-slate-300 font-medium">
                        {tokenData.institution_name}
                      </span>
                    </div>
                  </div>

                  {submitError && (
                    <Alert variant="error" className="text-xs">
                      {submitError}
                    </Alert>
                  )}

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Nueva Contraseña
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        required
                        minLength={8}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Mínimo 8 caracteres"
                        className="w-full px-3.5 py-2.5 bg-slate-900/90 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-2.5 text-xs text-slate-400 hover:text-slate-200"
                      >
                        {showPassword ? 'Ocultar' : 'Ver'}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Confirmar Contraseña
                    </label>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      minLength={8}
                      value={passwordConfirmation}
                      onChange={(e) => setPasswordConfirmation(e.target.value)}
                      placeholder="Repita su contraseña"
                      className="w-full px-3.5 py-2.5 bg-slate-900/90 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>

                  <div className="pt-2">
                    <Button
                      type="submit"
                      variant="primary"
                      className="w-full bg-cyan-600 hover:bg-cyan-500 text-white py-2.5 text-sm font-medium"
                      disabled={isSubmitting || !password || !passwordConfirmation}
                    >
                      {isSubmitting ? (
                        <span className="flex items-center justify-center gap-2">
                          <LoadingSpinner size="sm" /> Activando Cuenta...
                        </span>
                      ) : (
                        'Establecer Contraseña y Activar Cuenta'
                      )}
                    </Button>
                  </div>
                </form>
              )}
            </div>
          ) : (
            /* TAB 2: REQUEST ACTIVATION */
            <form onSubmit={handleRequestSubmit} className="space-y-4">
              <div className="text-center pb-2">
                <h3 className="text-base font-semibold text-slate-200">
                  Solicitud de Activación para Acudiente
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Ingrese el código SIMAT de su hijo(a) y su documento de identidad registrado para solicitar su enlace de acceso.
                </p>
              </div>

              {requestSuccessMsg && (
                <Alert variant="success" className="text-xs">
                  {requestSuccessMsg}
                </Alert>
              )}

              {requestErrorMsg && (
                <Alert variant="warning" className="text-xs">
                  {requestErrorMsg}
                </Alert>
              )}

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Código SIMAT del Estudiante *
                </label>
                <input
                  type="text"
                  required
                  value={reqSimat}
                  onChange={(e) => setReqSimat(e.target.value)}
                  placeholder="Ej: SIMAT-2026-001"
                  className="w-full px-3 py-2 bg-slate-900/90 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-1">
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Tipo Doc. *
                  </label>
                  <select
                    value={reqDocType}
                    onChange={(e) => setReqDocType(e.target.value as DocumentType)}
                    className="w-full px-3 py-2 bg-slate-900/90 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="CC">CC</option>
                    <option value="TI">TI</option>
                    <option value="CE">CE</option>
                    <option value="PASSPORT">Pasaporte</option>
                    <option value="PEP">PEP</option>
                    <option value="PPT">PPT</option>
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Número de Documento del Acudiente *
                  </label>
                  <input
                    type="text"
                    required
                    value={reqDocNumber}
                    onChange={(e) => setReqDocNumber(e.target.value)}
                    placeholder="Ej: 1020304050"
                    className="w-full px-3 py-2 bg-slate-900/90 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Correo Electrónico de Contacto *
                </label>
                <input
                  type="email"
                  required
                  value={reqEmail}
                  onChange={(e) => setReqEmail(e.target.value)}
                  placeholder="acudiente@ejemplo.com"
                  className="w-full px-3 py-2 bg-slate-900/90 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>

              <div className="pt-2">
                <Button
                  type="submit"
                  variant="primary"
                  className="w-full bg-cyan-600 hover:bg-cyan-500 text-white py-2.5 text-sm font-medium"
                  disabled={isRequesting || !reqSimat.trim() || !reqDocNumber.trim() || !reqEmail.trim()}
                >
                  {isRequesting ? (
                    <span className="flex items-center justify-center gap-2">
                      <LoadingSpinner size="sm" /> Procesando Solicitud...
                    </span>
                  ) : (
                    'Solicitar Enlace de Activación'
                  )}
                </Button>
              </div>
            </form>
          )}

          <div className="mt-6 text-center border-t border-slate-700/60 pt-4">
            <Link
              to="/login"
              className="text-xs text-slate-400 hover:text-cyan-400 transition-colors"
            >
              ¿Ya tiene una cuenta activa? Inicie sesión aquí
            </Link>
          </div>
        </Card>
      </div>
    </div>
  )
}

export default GuardianActivationView
