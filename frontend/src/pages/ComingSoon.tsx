/**
 * PEVN Frontend — Public Landing Page (Current-State View)
 *
 * The official landing page for the PEVN platform.
 * Communicates the platform's educational purpose, multi-tenant architecture,
 * and certified implementation state in a professional, institutional manner.
 *
 * Design intent:
 *   - Deep institutional blue conveys trust and authority
 *   - Gold accent communicates achievement and excellence
 *   - Clean, uncluttered layout works on all devices
 *   - Mobile-first: responsive and accessible
 *   - Neutral public sector presentation compliant with government standards
 */

import type { ComponentType } from 'react'

export function ComingSoon() {
  return (
    <div className="flex-1 flex flex-col">
      {/* Hero Section */}
      <section
        className="flex-1 bg-gradient-to-br from-pevn-blue via-pevn-blue-700 to-pevn-blue-800 text-white relative overflow-hidden"
        aria-labelledby="hero-heading"
      >
        {/* Subtle background decoration */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full translate-x-32 -translate-y-32" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-pevn-gold/10 rounded-full -translate-x-16 translate-y-16" />
        </div>

        <div className="relative max-w-5xl mx-auto px-6 py-16 sm:py-24 lg:py-28 text-center">
          {/* Status badge */}
          <div className="inline-flex items-center gap-2 bg-emerald-500/20 border border-emerald-400/40 text-emerald-200 rounded-full px-4 py-2 text-sm font-medium mb-8 animate-fade-in">
            <span
              className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse-soft"
              aria-hidden="true"
            />
            Plataforma Integral · Gestión Académica, Portales, SIEE y Convivencia Implementados
          </div>

          {/* Main heading */}
          <h1
            id="hero-heading"
            className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight mb-6 animate-slide-up"
          >
            Plataforma Educativa
            <br />
            <span className="text-pevn-gold">Virtual Nacional</span>
          </h1>

          {/* Subtitle */}
          <p className="text-xl sm:text-2xl text-white/80 font-light mb-4 max-w-2xl mx-auto animate-slide-up">
            Sistema de Gestión Educativa para las Instituciones Públicas de Colombia
          </p>

          <p className="text-base text-white/60 mb-12 max-w-2xl mx-auto leading-relaxed animate-fade-in">
            Una plataforma educativa soberana, accesible y moderna para docentes, estudiantes,
            familias, directivos y administradores del sistema educativo colombiano.
          </p>

          {/* Feature highlights */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-12 animate-fade-in">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-5 text-left hover:bg-white/15 transition-colors"
              >
                <div
                  className="w-10 h-10 bg-pevn-gold/20 rounded-lg flex items-center justify-center mb-3"
                  aria-hidden="true"
                >
                  <feature.Icon className="w-5 h-5 text-pevn-gold" />
                </div>
                <h2 className="font-semibold text-white mb-1 text-sm">{feature.title}</h2>
                <p className="text-white/60 text-xs leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>

          {/* Development status note */}
          <div className="inline-flex items-center gap-3 bg-white/10 border border-white/20 rounded-xl px-6 py-4 text-sm max-w-3xl text-left sm:text-center">
            <svg
              className="w-5 h-5 text-pevn-gold flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-white/80">
              Plataforma en evolución continua. Las principales funcionalidades académicas, evaluación SIEE,
              portales por rol y convivencia escolar se encuentran implementadas y verificadas.
            </span>
          </div>
        </div>
      </section>

      {/* Phase roadmap section */}
      <section className="bg-white py-14 px-6" aria-labelledby="roadmap-heading">
        <div className="max-w-6xl mx-auto">
          <h2 id="roadmap-heading" className="text-2xl font-bold text-pevn-blue text-center mb-8">
            Estado y Capacidades de la Plataforma
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {PHASES.map((phase, index) => (
              <div
                key={phase.phase}
                className={`rounded-xl p-5 border-2 flex flex-col justify-between ${
                  phase.status === 'complete'
                    ? 'border-emerald-500 bg-emerald-50/60 shadow-sm'
                    : phase.status === 'software_ready'
                      ? 'border-blue-500 bg-blue-50/50 shadow-sm'
                      : 'border-gray-200 bg-gray-50/70'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center ${
                        phase.status === 'complete'
                          ? 'bg-emerald-600 text-white'
                          : phase.status === 'software_ready'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-300 text-gray-600'
                      }`}
                      aria-label={`Módulo ${String(index + 1)}`}
                    >
                      {phase.status === 'complete' ? '✓' : phase.status === 'software_ready' ? '⚡' : String(index + 1)}
                    </span>
                    <span
                      className={`text-xs font-semibold uppercase tracking-wide ${
                        phase.status === 'complete'
                          ? 'text-emerald-700 font-bold'
                          : phase.status === 'software_ready'
                            ? 'text-blue-700 font-bold'
                            : 'text-gray-500'
                      }`}
                    >
                      {phase.statusLabel}
                    </span>
                  </div>

                  {phase.statusDetail && (
                    <div className="mb-2">
                      <span className="inline-block text-[10px] font-medium leading-tight text-amber-800 bg-amber-100/80 border border-amber-300/60 rounded px-1.5 py-0.5">
                        {phase.statusDetail}
                      </span>
                    </div>
                  )}

                  <h3 className="font-semibold text-pevn-blue text-sm mb-1">{phase.phase}</h3>
                  <p className="text-xs text-gray-600 leading-relaxed">{phase.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

interface Feature {
  title: string
  description: string
  Icon: ComponentType<{ className?: string }>
}

interface PhaseItem {
  phase: string
  description: string
  status: 'complete' | 'software_ready' | 'pending'
  statusLabel: string
  statusDetail?: string
}

function ShieldIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
      />
    </svg>
  )
}

function UsersIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"
      />
    </svg>
  )
}

function DeviceIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18h3"
      />
    </svg>
  )
}

const FEATURES: Feature[] = [
  {
    title: 'Seguridad por Diseño',
    description:
      'Arquitectura basada en controles rigurosos: hashing Argon2id, tokens efímeros en memoria, aislamiento multi-inquilino y auditoría inmutable.',
    Icon: ShieldIcon,
  },
  {
    title: 'Arquitectura Multi-Institucional',
    description:
      'Diseñada para gestionar instituciones educativas, sedes y sus comunidades de forma aislada, soberana y segura.',
    Icon: UsersIcon,
  },
  {
    title: 'Accesible y Móvil',
    description:
      'Diseñada con criterios de accesibilidad, interfaz responsiva y optimizada para dispositivos móviles y conexiones estándar.',
    Icon: DeviceIcon,
  },
]

const PHASES: PhaseItem[] = [
  {
    phase: '1. Fundación, Seguridad e Identidad',
    description: 'Arquitectura base, autenticación Argon2id, tokens efímeros, control de acceso RBAC y auditoría inmutable.',
    status: 'complete',
    statusLabel: '✓ Implementada',
  },
  {
    phase: '2. Estructura Institucional y Matrícula',
    description: 'Catálogo DANE/DUE de sedes, años lectivos, períodos, grupos, matrícula SIMAT y control de cupos.',
    status: 'complete',
    statusLabel: '✓ Implementada',
  },
  {
    phase: '3. Gestión Académica y Portales Soberanos',
    description: 'Portales dedicados para directivos, docentes, estudiantes y acudientes con asignaciones académicas.',
    status: 'complete',
    statusLabel: '✓ Implementada',
  },
  {
    phase: '4. Actividades Pedagógicas y Asistencia',
    description: 'Gestión de tareas, entregas de estudiantes con archivos o texto, planilla de asistencia y planeación.',
    status: 'complete',
    statusLabel: '✓ Implementada',
  },
  {
    phase: '5. Evaluación SIEE y Promoción Escolar',
    description: 'Políticas autónomas (Decreto 1290), planillas periódicas, nivelaciones con tope legal y actas de promoción.',
    status: 'complete',
    statusLabel: '✓ Implementada',
  },
  {
    phase: '6. Comunicaciones y Convivencia Escolar',
    description: 'Circulares oficiales con acuse de recibo digital, periódico escolar y observador formativo (Ley 1620).',
    status: 'complete',
    statusLabel: '✓ Implementada',
  },
  {
    phase: '7. Aulas Virtuales Sincrónicas',
    description: 'Software y adaptador BBB con firmas criptográficas SHA integrados. Comisionamiento de servidor físico en curso.',
    status: 'software_ready',
    statusLabel: '● Software Integrado',
    statusDetail: 'Validación de infraestructura BBB real pendiente',
  },
  {
    phase: '8. Validación en Campo y Despliegue',
    description: 'Aprovisionamiento de infraestructura de producción pública, dominio .gov.co y pruebas de carga masiva.',
    status: 'pending',
    statusLabel: 'En Alistamiento',
  },
]

export default ComingSoon
