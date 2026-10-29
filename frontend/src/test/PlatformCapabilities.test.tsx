/**
 * PEVN Frontend — Platform Capabilities and Homepage Status Unit Tests
 *
 * Verifies that the public landing page (ComingSoon) and its centralized
 * capabilities configuration accurately reflect the audited platform status:
 *   - 8 capability cards render with distinct, evidence-based statuses
 *   - Card 1 reflects RBAC separation of administrative roles from academic management
 *   - Card 2 reflects reference catalog data and internal SIMAT structure
 *   - Card 3 reflects sovereign portals with preserved institutional academic powers
 *   - Card 7 reflects software ready with real physical infrastructure pending
 *   - Card 8 reflects field validation and deployment in preparation
 */

import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ComingSoon } from '@pages/ComingSoon'
import {
  PLATFORM_CAPABILITIES,
  HERO_STATUS_BADGE,
  EVOLUTION_NOTICE_TEXT,
} from '@config/platformCapabilities'

describe('Homepage — Estado y Capacidades de la Plataforma', () => {
  it('contains exactly 8 platform capability cards in the centralized configuration', () => {
    expect(PLATFORM_CAPABILITIES).toHaveLength(8)
    expect(PLATFORM_CAPABILITIES.map((c) => c.id)).toEqual([1, 2, 3, 4, 5, 6, 7, 8])
  })

  it('renders the section heading and all 8 capability cards on the homepage', () => {
    render(
      <MemoryRouter>
        <ComingSoon />
      </MemoryRouter>
    )

    expect(
      screen.getByRole('heading', { name: /estado y capacidades de la plataforma/i })
    ).toBeInTheDocument()

    // Verify all 8 card headings exist
    expect(screen.getByText('1. Fundación, Seguridad e Identidad')).toBeInTheDocument()
    expect(screen.getByText('2. Estructura Institucional y Matrícula')).toBeInTheDocument()
    expect(screen.getByText('3. Gestión Académica y Portales Soberanos')).toBeInTheDocument()
    expect(screen.getByText('4. Actividades Pedagógicas y Asistencia')).toBeInTheDocument()
    expect(screen.getByText('5. Evaluación SIEE y Promoción Escolar')).toBeInTheDocument()
    expect(screen.getByText('6. Comunicaciones y Convivencia Escolar')).toBeInTheDocument()
    expect(screen.getByText('7. Aulas Virtuales Sincrónicas')).toBeInTheDocument()
    expect(screen.getByText('8. Validación en Campo y Despliegue')).toBeInTheDocument()
  })

  it('Card 1 accurately reflects RBAC separation of administrative roles and verified security', () => {
    const card1 = PLATFORM_CAPABILITIES.find((c) => c.id === 1)
    expect(card1).toBeDefined()
    expect(card1?.status).toBe('IMPLEMENTADA_Y_VERIFICADA')
    expect(card1?.statusLabel).toContain('Implementada y Verificada')
    expect(card1?.description).toContain('Argon2id')
    expect(card1?.description).toContain('RBAC verificado')
    expect(card1?.description).toContain('roles administrativos externos')
    expect(card1?.description).toContain('autonomía institucional')
  })

  it('Card 2 distinguishes reference catalog from live government API integration', () => {
    const card2 = PLATFORM_CAPABILITIES.find((c) => c.id === 2)
    expect(card2).toBeDefined()
    expect(card2?.status).toBe('IMPLEMENTADA_Y_VERIFICADA')
    expect(card2?.description).toContain('Catálogo referencial DANE')
    expect(card2?.description).toContain('SIMAT')
    expect(card2?.description).toContain('sin enlace transaccional directo en tiempo real')
    expect(card2?.statusDetail).toContain('Sin enlace en tiempo real al MEN')
  })

  it('Card 3 confirms sovereign portals and preserved institutional educational powers', () => {
    const card3 = PLATFORM_CAPABILITIES.find((c) => c.id === 3)
    expect(card3).toBeDefined()
    expect(card3?.status).toBe('IMPLEMENTADA_Y_VERIFICADA')
    expect(card3?.description).toContain('Portales soberanos')
    expect(card3?.description).toContain('Rector')
    expect(card3?.description).toContain('Fronteras RBAC blindadas')
  })

  it('Card 7 preserves software-ready status with real physical infrastructure pending', () => {
    const card7 = PLATFORM_CAPABILITIES.find((c) => c.id === 7)
    expect(card7).toBeDefined()
    expect(card7?.status).toBe('SOFTWARE_INTEGRADO_INFRAESTRUCTURA_PENDIENTE')
    expect(card7?.statusLabel).toContain('Software Integrado')
    expect(card7?.statusDetail).toContain('Validación de infraestructura BBB real')
    expect(card7?.description).toContain('BigBlueButton')
    expect(card7?.description).toContain('Servidores físicos de videoconferencia')
    expect(card7?.description).toContain('pendientes')
  })

  it('Card 8 maintains in-preparation status for field validation and public deployment', () => {
    const card8 = PLATFORM_CAPABILITIES.find((c) => c.id === 8)
    expect(card8).toBeDefined()
    expect(card8?.status).toBe('EN_ALISTAMIENTO')
    expect(card8?.statusLabel).toContain('En Alistamiento')
    expect(card8?.statusDetail).toContain('Pendiente autorización formal de piloto')
    expect(card8?.description).toContain('dominio gubernamental .gov.co')
    expect(card8?.description).toContain('pruebas de carga masiva')
  })

  it('renders consistent hero status badge and evolution notice without overstatements', () => {
    render(
      <MemoryRouter>
        <ComingSoon />
      </MemoryRouter>
    )

    expect(screen.getByText(HERO_STATUS_BADGE.text)).toBeInTheDocument()
    expect(screen.getByText(EVOLUTION_NOTICE_TEXT)).toBeInTheDocument()
  })
})

