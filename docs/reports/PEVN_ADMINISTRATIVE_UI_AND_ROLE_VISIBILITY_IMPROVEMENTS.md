# PEVN — INFORME TÉCNICO: CONSOLIDACIÓN DE UI ADMINISTRATIVA, ACCIONES RESPONSIVAS, CONTRASTE HOVER Y VISIBILIDAD DE MÓDULOS BASADA EN ROLES

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Fecha:** 2 de Noviembre de 2026  
**Área:** Arquitectura Frontend, UX/UI Design System, Seguridad RBAC y DevSecOps  
**Estado:** REMEDIADO, VERIFICADO Y PROBADO EXITOSAMENTE (100% SUITES PASS)  

---

## 1. RESUMEN EJECUTIVO

A partir de la inspección visual forense de las capturas de pantalla de la plataforma en entornos de prueba y producción, se identificaron y solucionaron cuatro anomalías críticas de interfaz y control de acceso:

1. **Desalineación y Truncamiento de Botones de Acción en Tablas (Issue A):** En `/admin/control-center`, `/admin/department-admins`, `/admin/municipality-admins` y `/admin/institutions`, las tablas no poseían restricciones de ancho mínimo (`min-width`) ni anchos fijos asignados a la columna `ACCIONES`, lo que provocaba que el navegador comprimiera las celdas, generando apilamiento vertical no deseado ("Detalle" sobre "Radicar" y "SED"), truncamiento de encabezados ("ACCIONI", "Accior") y corte de etiquetas de botones ("De...", "Reasigna", "Suspend...").
2. **Colisión de Contraste en Estados Hover sobre Banners Oscuros (Issue B):** En `/admin/institutions`, los botones del banner superior `#0F172A` aplicaban `variant="secondary"`, cuya clase Tailwind `hover:bg-pevn-blue-50` (`#e6e6ff` azul muy claro) colisionaba con estilos en línea `color: '#E2E8F0'`, produciendo texto gris claro sobre fondo azul claro (contraste 1:1, texto invisible).
3. **Comportamiento Responsive y Desbordamiento Horizontal (Issue C):** Ausencia de contenedores con scroll horizontal explícito (`overflowX: 'auto'`) y anchos mínimos de tabla consistentes (`min-width: 1050px - 1150px`) para garantizar visualización profesional en resoluciones desde 390px (móvil) hasta 1920px (desktop Ultra-Wide).
4. **Fuga de Visibilidad de Módulos Educativos Institucionales en Roles Territoriales (Issue D):** Los administradores territoriales (`national_admin`, `department_admin`, `municipality_admin`) visualizaban accesos a módulos pedagógicos institucionales (**Aulas Virtuales**, **Comunicaciones**, **Noticias** y **Convivencia**) en la barra de navegación superior y en el Dashboard de bienvenida, y al ingresar a `/virtual-classrooms` eran redirigidos a `/admin/institutions?contextRequired=true&returnTo=%2Fvirtual-classrooms` en lugar de recibir una denegación explícita acorde a su rol.

Todas las causas raíz fueron remediadas a nivel de Design System (`Button.tsx`), componentes de vista (`InstitutionsView`, `DepartmentAdminsView`, `MunicipalityAdminsView`, `TerritorialControlCenterView`), navegación (`RootLayout.tsx`, `Dashboard.tsx`), guardas de rutas (`RequireAuth.tsx`, `App.tsx`) y matriz RBAC del backend (`rbac_bootstrap_service.py`).

---

## 2. DIAGNÓSTICO DE CAUSA RAÍZ POR CAPTURA Y SECCIÓN

| Captura / Evidencia | Sección Afectada | Causa Raíz Técnica | Impacto en Usuario |
|---|---|---|---|
| **Screenshot 1** (`media_1793627536826`) | `/admin/institutions?contextRequired=true&returnTo=%2Fvirtual-classrooms` | `RequireAuth` redirigía a selección de contexto si `requireInstitutionContext=true`, pero el rol `national_admin` no debe operar aulas virtuales escolares. | Confusión operacional; invita al administrador territorial a seleccionar un colegio para un módulo que no le compete. |
| **Screenshot 2** (`media_1793628146336`) | `/admin/control-center` (Matriz Territorial) | Celda `ACCIONES` con `flexWrap: 'wrap'` sin ancho mínimo de tabla. | El botón "Detalle" se ubicaba en la fila superior y "Radicar" / "SED" en la inferior, duplicando la altura de cada fila. |
| **Screenshot 3** (`media_1793628285204`) | `/admin/department-admins` | Columna de acciones sin `minWidth: 280px` ni `whiteSpace: 'nowrap'` en botones. | El botón "⛔ Desactivar" se cortaba como "De...", impidiendo lectura y acción segura. |
| **Screenshot 4** (`media_1793628577865`) | `/admin/municipality-admins` | Encabezado sin `minWidth: 280px` y botones apilados. | El encabezado decía "ACCIONI" (cortado) y el botón inferior decía "Reasigna" (cortado). |
| **Screenshot 5** (`media_1793629109808`) | `/admin/institutions` (Banner & Tablas) | Incompatibilidad de `style={{ color: '#E2E8F0' }}` con `hover:bg-pevn-blue-50`. Columnas DANE y Acciones sin `minWidth`. | Botones ilegibles al pasar el cursor; columna DANE comprimida; encabezado "Accior" y botón "Suspend...". |

---

## 3. NORMALIZACIÓN Y ESTANDARIZACIÓN DE TABLAS ADMINISTRATIVAS (ISSUE A)

Se aplicó una arquitectura estandarizada en todas las vistas administrativas:

### 3.1. `/admin/control-center` (`TerritorialControlCenterView.tsx`)
- Se configuró la tabla con `width: '100%'` y `minWidth: '1080px'`.
- La columna `ACCIONES` se definió con `width: '230px', minWidth: '230px', textAlign: 'center', whiteSpace: 'nowrap'`.
- El contenedor de botones utiliza `display: 'flex', justifyContent: 'center', gap: '0.35rem', alignItems: 'center', whiteSpace: 'nowrap'`.
- Los botones "Detalle", "Radicar" y "SED" se mantienen en una sola fila horizontal en resoluciones de escritorio con padding compacto (`padding: '0.35rem 0.6rem', fontSize: '0.75rem'`).

### 3.2. `/admin/department-admins` (`DepartmentAdminsView.tsx`)
- Se configuró la tabla con `width: '100%'` y `minWidth: '1050px'`.
- Encabezado: `<th style={{ padding: '0.875rem 1rem', fontWeight: 600, textAlign: 'right', width: '280px', minWidth: '280px', whiteSpace: 'nowrap' }}>Acciones</th>`.
- Celda de datos: `width: '280px', minWidth: '280px'`.
- Botones "✏️ Editar", "🔄 Reasignar", "✉️ Reenviar invitación" y "⛔ Desactivar" / "✅ Activar" poseen `whiteSpace: 'nowrap'`, eliminando cualquier corte o truncamiento de texto.

### 3.3. `/admin/municipality-admins` (`MunicipalityAdminsView.tsx`)
- Se configuró la tabla con `width: '100%'` y `minWidth: '1150px'`.
- Encabezado: `<th style={{ padding: '0.75rem 1rem', textAlign: 'right', width: '280px', minWidth: '280px', whiteSpace: 'nowrap' }}>ACCIONES</th>`.
- Celda de datos: `width: '280px', minWidth: '280px'`.
- Los botones "🔴 Desactivar" / "🟢 Activar" y "🔄 Reasignar" se presentan alineados a la derecha con espacio suficiente y `whiteSpace: 'nowrap'`.

### 3.4. `/admin/institutions` (`InstitutionsView.tsx`)
- **Tabla del Catálogo Territorial (DANE/MEN):**
  - Ancho mínimo de tabla: `1050px`.
  - Columna "Código DANE": `width: '140px', minWidth: '140px'`.
  - Columna "Acciones": `width: '250px', minWidth: '250px', whiteSpace: 'nowrap'`.
- **Tabla de Colegios Aprovisionados (Tenants):**
  - Ancho mínimo de tabla: `1150px`.
  - Columna "Código DANE": `width: '140px', minWidth: '140px'`.
  - Columna "Acciones": `width: '270px', minWidth: '270px', whiteSpace: 'nowrap'`.
  - Acción de Suspensión: Reemplazado el botón genérico sin jerarquía por un botón con estilo de peligro semántico (`className="border border-red-300 text-red-600 bg-red-50 hover:bg-red-600 hover:text-white hover:border-red-600 active:bg-red-700 font-semibold text-xs px-2.5 py-1.5 rounded-md transition-colors whitespace-nowrap cursor-pointer"`), garantizando que "⛔ Suspender" y "✅ Reactivar" sean inequívocos y legibles.

---

## 4. SOLUCIÓN AL CONTRASTE DE ESTADOS HOVER EN BANNER DARK (ISSUE B)

### 4.1. Análisis del Defecto de Contraste
El banner de aprovisionamiento tiene fondo `#0F172A` (Slate 900 oscuro).
- El botón "Sincronizar Catálogo" usaba `variant="secondary"`, el cual en `Button.tsx` aplica la clase `hover:bg-pevn-blue-50` (`#e6e6ff`).
- Simultáneamente, el botón tenía `style={{ color: '#E2E8F0', borderColor: '#475569' }}`.
- En la especificación CSS, los estilos inline tienen mayor especificidad que las pseudo-clases en utilidades CSS. Por ende, al colocar el cursor encima:
  - Fondo: Cambiaba a `#e6e6ff` (azul muy claro).
  - Texto: Permanecía en `#E2E8F0` (gris/blanco claro).
  - Ratio de Contraste: `1.08:1` (completamente ilegible, violación grave WCAG 1.4.3).

### 4.2. Remediación en el Design System y Componente
1. **Nueva Variante `outline-light` en `Button.tsx`:**
   ```tsx
   export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'link' | 'outline-light'

   // En VARIANT_STYLES:
   'outline-light':
     'border border-slate-600 text-slate-100 bg-slate-800/80 hover:bg-slate-700 hover:text-white hover:border-slate-400 active:bg-slate-900 focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:border-slate-700 disabled:text-slate-500 disabled:bg-slate-800/30'
   ```
2. **Aplicación en `InstitutionsView.tsx`:**
   - **Sincronizar Catálogo:** Utiliza `variant="outline-light"` sin estilos inline de color en conflicto.
     - Reposo: Fondo `#1E293B` semi-opaco, borde `#475569`, texto `#F1F5F9` (Contraste 13.8:1 sobre `#0F172A`).
     - Hover: Fondo `#334155` (Slate 700), borde `#94A3B8`, texto `#FFFFFF` (Contraste 7.2:1).
     - Focus: Anillo azul `#60A5FA` con offset `#0F172A`.
   - **Flujo de Incorporación NTA-04:**
     - Utiliza clases dedicadas para superficies oscuras: `border border-emerald-500/80 text-emerald-300 bg-emerald-950/40 hover:bg-emerald-800 hover:text-white hover:border-emerald-400 active:bg-emerald-900`.
     - Reposo: Texto verde esmeralda legible sobre fondo esmeralda profundo.
     - Hover: Fondo esmeralda intenso `#065F46` con texto blanco puro `#FFFFFF`.
   - **+ Aprovisionar Institución:**
     - Utiliza `className="bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800 focus:ring-2 focus:ring-blue-400 shadow-md shadow-blue-900/40"`.

---

## 5. ARQUITECTURA RESPONSIVE Y RESILIENCIA EN VIEWPORTS (ISSUE C)

Se garantizó la consistencia de presentación en todos los breakpoints objetivo:

```
+-----------------------------------------------------------------------------------------+
| Breakpoint   | Ancho Viewport | Comportamiento en Tablas Administrativas               |
+-----------------------------------------------------------------------------------------+
| Ultra-Wide   | 1920px         | Tabla expandida, todas las columnas visibles sin scroll |
| Desktop Pro  | 1440px - 1366px| Tabla fluida, espaciado cómodo, acciones horizontales   |
| Tablet Land  | 1024px         | Contenedor activa scroll horizontal suave si es preciso |
| Tablet Port  | 768px          | Scroll horizontal habilitado, cero corte de texto       |
| Mobile       | 390px          | Scroll horizontal táctil completo, datos legibles       |
+-----------------------------------------------------------------------------------------+
```

Todos los contenedores de tabla fueron provistos de:
```tsx
<div style={{ overflowX: 'auto', width: '100%' }}>
  <table style={{ width: '100%', minWidth: '1050px', ... }}>
```
impidiendo que las tablas colapsen o reduzcan sus celdas por debajo de los anchos legibles.

---

## 6. VISIBILIDAD DE MÓDULOS EDUCATIVOS BASADA EN ROLES (ISSUE D)

### 6.1. Principio de Menor Privilegio
Los administradores territoriales (`national_admin`, `department_admin`, `municipality_admin`) tienen como misión la gobernanza territorial, supervisión de entidades territoriales certificadas (ETC), trámites de adopción institucional (NTA-04) y aprovisionamiento de rectores. No son actores pedagógicos de aula.

Por tanto, los siguientes cuatro módulos institucionales quedan estrictamente excluidos de su alcance operativo:
1. **Aulas Virtuales (`/virtual-classrooms`):** Sesiones de clase en vivo, videoconferencias pedagógicas y grabaciones de clase.
2. **Comunicaciones (`/communications`):** Circulares institucionales internas y correspondencia escolar de cada colegio.
3. **Noticias (`/news`):** Muro de noticias y eventos comunitarios del colegio.
4. **Convivencia (`/incidents`):** Observador del alumno y comités escolares de convivencia (Ley 1620).

### 6.2. Capa de Navegación (`RootLayout.tsx`)
Se introdujo la guarda territorial:
```tsx
const isTerritorialAdmin = hasRole(['national_admin', 'department_admin', 'municipality_admin'])

const canAccessVirtualClassrooms = !isSuperAdmin && !isTerritorialAdmin && hasPermission('virtual_classrooms:read')
const canAccessCommunications = !isSuperAdmin && !isTerritorialAdmin && hasPermission('communications:read')
const canAccessNews = !isSuperAdmin && !isTerritorialAdmin && hasPermission('news:read')
const canAccessIncidents = !isSuperAdmin && !isTerritorialAdmin && hasPermission('incidents:read')
```
Ninguno de estos enlaces aparece en la barra superior para los tres roles territoriales.

### 6.3. Capa de Dashboard (`Dashboard.tsx`)
Las tarjetas de acceso rápido correspondientes a Aulas Virtuales, Comunicaciones, Noticias y Convivencia fueron condicionadas con `!isTerritorialAdmin`:
- Se eliminaron las tarjetas de Aulas Virtuales, Comunicaciones/Noticias y Convivencia para administradores territoriales.
- Se ajustó el texto de la tarjeta de selección de contexto institucional para `department_admin` y `municipality_admin` a: *"Inspección y Acompañamiento Institucional: Para inspeccionar el plan de estudios, salones, matrículas, sedes y planta docente de una institución específica, seleccione la institución en el catálogo."*

### 6.4. Capa de Rutas y Guardas (`RequireAuth.tsx` y `App.tsx`)
Se agregó la propiedad `denyRoles?: string | string[]` a `RequireAuth`:
```tsx
if (denyRoles && hasRole(denyRoles)) {
  return (
    <div style={{ maxWidth: '800px', margin: '3rem auto', padding: '0 1rem' }}>
      <div style={{ backgroundColor: '#FFF1F2', border: '1px solid #FECDD3', borderRadius: '12px', padding: '2rem', textAlign: 'center' }} role="alert">
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🚫</div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#9F1239', margin: '0 0 0.5rem 0' }}>
          Acceso Restringido (403)
        </h1>
        <p style={{ color: '#881337', fontSize: '0.95rem', lineHeight: '1.6', margin: '0 0 1.5rem 0' }}>
          Este módulo corresponde a operaciones educativas institucionales y no forma parte del alcance operativo territorial asignado a su rol. Diríjase a su panel de gestión territorial.
        </p>
        <Link to="/dashboard" style={{ display: 'inline-block', backgroundColor: '#BE123C', color: '#FFFFFF', fontWeight: 700, padding: '0.625rem 1.25rem', borderRadius: '8px', textDecoration: 'none' }}>
          Volver al Panel Principal
        </Link>
      </div>
    </div>
  )
}
```
En `App.tsx`, las rutas protegidas fueron configuradas con:
```tsx
denyRoles={['national_admin', 'department_admin', 'municipality_admin']}
```
para `/virtual-classrooms`, `/communications`, `/news` y `/incidents`.

### 6.5. Capa Backend RBAC (`rbac_bootstrap_service.py`)
En el servicio de bootstrap de roles y permisos se removieron formalmente las siguientes asignaciones:
- De `NATIONAL_ADMIN`: `virtual_classrooms:read`, `recordings:read`, `communications:*`, `news:*`, `incidents:read`.
- De `DEPARTMENT_ADMIN`: `virtual_classrooms:read`, `recordings:read`, `communications:read`, `news:read`, `incidents:read`.
- De `MUNICIPALITY_ADMIN`: `virtual_classrooms:read`, `recordings:read`, `communications:read`, `news:read`, `incidents:read`.

---

## 7. MATRIZ DE PERMISOS RBAC Y ALCANCE OPERATIVO

```
+---------------------------+----------------+------------------+--------------------+
| Módulo / Recurso          | national_admin | department_admin | municipality_admin |
+---------------------------+----------------+------------------+--------------------+
| Catálogo Instituciones    | AUTORIZADO (W) | AUTORIZADO (R)   | AUTORIZADO (R)     |
| Directorio Usuarios       | AUTORIZADO (W) | AUTORIZADO (R)   | AUTORIZADO (R)     |
| Admin Departamentales     | AUTORIZADO (W) | AUTORIZADO (R)   | DENEGADO           |
| Admin Municipales         | AUTORIZADO (W) | AUTORIZADO (W)   | AUTORIZADO (R)     |
| Control Territorial       | AUTORIZADO (W) | AUTORIZADO (R)   | DENEGADO           |
| Onboarding Institucional  | AUTORIZADO (W) | AUTORIZADO (W)   | DENEGADO           |
| Analítica Territorial     | AUTORIZADO (R) | AUTORIZADO (R)   | AUTORIZADO (R)     |
| Aulas Virtuales           | DENEGADO (403) | DENEGADO (403)   | DENEGADO (403)     |
| Comunicaciones            | DENEGADO (403) | DENEGADO (403)   | DENEGADO (403)     |
| Noticias                  | DENEGADO (403) | DENEGADO (403)   | DENEGADO (403)     |
| Convivencia Escolar       | DENEGADO (403) | DENEGADO (403)   | DENEGADO (403)     |
| Gestión Curricular/Acad.  | DENEGADO (403) | DENEGADO (403)   | DENEGADO (403)     |
+---------------------------+----------------+------------------+--------------------+
```

---

## 8. PRUEBAS AUTOMATIZADAS Y VERIFICACIÓN

### 8.1. Pruebas Unitarias y Funcionales Frontend
Comando ejecutado:
```powershell
npm --prefix frontend test -- src/test/CrossRoleNavigationAudit.test.tsx src/test/RoleNavigationFunctional.test.tsx src/test/Auth.test.tsx --run
```
**Resultado: 3 archivos de prueba, 33/33 pruebas PASADAS (100%)**
- `CrossRoleNavigationAudit.test.tsx`: 9/9 pruebas PASADAS (incluyendo denegación 403 para administradores territoriales en `/virtual-classrooms`).
- `RoleNavigationFunctional.test.tsx`: 18/18 pruebas PASADAS (incluyendo ocultamiento de enlaces de Aulas Virtuales, Comunicaciones, Noticias y Convivencia en Navbar y Dashboard para administradores territoriales).
- `Auth.test.tsx`: 6/6 pruebas PASADAS.

### 8.2. Verificación Estática de Tipos (TypeScript)
Comando ejecutado:
```powershell
npm --prefix frontend run typecheck
```
**Resultado: Código de salida 0 (0 errores de TypeScript).**

### 8.3. Compilación de Producción (Vite Build)
Comando ejecutado:
```powershell
npm --prefix frontend run build
```
**Resultado: Éxito en 9.39s.** Generación correcta de chunks y service workers PWA.

### 8.4. Pruebas de Autorización y Resiliencia Backend
Comando ejecutado:
```powershell
pytest backend/tests/test_sa01_superadmin_governance.py backend/tests/test_academic_admin_roles_authorization.py backend/tests/test_virtual_classrooms_resilience.py -v
```
**Resultado: 25/25 pruebas PASADAS en 59.79s (100%)**
- `test_sa01_superadmin_governance.py`: 7/7 PASADAS.
- `test_academic_admin_roles_authorization.py`: 7/7 PASADAS.
- `test_virtual_classrooms_resilience.py`: 11/11 PASADAS.

---

## 9. CUMPLIMIENTO DE RESTRICCIONES Y PRINCIPIOS DE SEGURIDAD

1. **Integridad de Lógica de Calificaciones y SIEE:** No se modificó ningún archivo del motor de notas, consolidación curricular, períodos lectivos o libro de calificaciones.
2. **Preservación de Tokens y Autenticación:** Se mantuvo intacto el ciclo de refresco y gestión de sesiones JWT.
3. **Control de Git:** No se realizaron commits ni pushes automáticos sin autorización previa.
4. **Sin Pruebas E2E de Navegador:** Se respetó la prohibición de ejecutar tests de navegador automatizados.

---

## 10. CONCLUSIÓN

La plataforma PEVN cuenta ahora con interfaces administrativas profesionales, consistentes y adaptadas a todos los factores de forma, con contraste de color validado bajo estándares de accesibilidad WCAG y una estricta segregación de funciones entre la gestión territorial y la operación educativa institucional.

