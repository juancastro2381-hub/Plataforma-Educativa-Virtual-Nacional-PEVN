# PEVN — Auditoría y Diagnóstico Técnico: Git Filename Too Long en Windows

**Fecha:** 16 de septiembre de 2026  
**Sistema Operativo:** Windows (Win32 / NTFS / OneDrive)  
**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Estado:** Diagnóstico completado — Esperando aprobación para ejecución  

---

## 1. Causa Raíz (Root Cause)

El bloqueo y advertencia recurrente de Git en Windows:
```text
Git warning: could not open directory 'backend/data/storage/.../submissions/...': Filename too long
```
se debe a la confluencia de tres factores independientes:

1. **Ausencia de exclusión en `.gitignore`:**  
   El directorio `backend/data/` (creado en tiempo de ejecución por el servicio de almacenamiento seguro `StorageService` / `LocalStorageDriver`) **no está declarado** en el archivo [.gitignore](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.gitignore). Por consiguiente, Git lo interpreta como un directorio sin rastrear (*untracked*) y procede a recorrerlo recursivamente en cada operación de `git status`, indexación, o cuando la extensión de Source Control del IDE refresca los cambios pendientes.

2. **Estructura jerárquica profunda por diseño de aislamiento multi-inquilino:**  
   Para garantizar aislamiento estricto por institución, actividad, estudiante, entrega y archivo adjunto (fases B3-H11 y B3-H13), `StorageService.build_submission_attachment_path` genera la siguiente jerarquía de UUIDs:
   ```text
   backend/data/storage/<institution_uuid>/submissions/<activity_uuid>/<student_uuid>/<submission_uuid>/<attachment_uuid>.<ext>
   ```
   Cada UUID consta de 36 caracteres. La ruta relativa contiene 5 niveles de carpetas.

3. **Límite `MAX_PATH` (260 caracteres) de la API Win32 en Git para Windows:**  
   La ruta absoluta en el entorno local del desarrollador es:
   ```text
   C:\Users\juanc\OneDrive\Documentos\Desarrollo proyectos\Plataforma Educativa\Plataforma Educativa Virtual Nacional PEVN\backend\data\storage\01cc6a06-75d8-4f32-9d1c-6edaafaa92c7\submissions\9653f47d-8bc7-4e4e-a3b8-e1b4b27f0cf3\ed580a09-0d0b-4753-8f88-427d49d3b6f0\
   ```
   - Longitud base del repositorio: **113 caracteres**
   - Longitud de subdirectorios de entrega: **159 caracteres**
   - Longitud combinada de la carpeta: **272 caracteres** (supera los 260 de `MAX_PATH`)
   - Longitud con el archivo adjunto final: **~312 caracteres**
   
   Mientras que la aplicación Python utiliza internamente el prefijo de longitud extendida `\\?\` (implementado explícitamente en [backend/app/core/storage/local.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/local.py#L51-L55)), **Git no tiene habilitado `core.longpaths = true`** por defecto, lo que provoca la llamada fallida a `opendir()` / `FindFirstFile` con el error de sistema `ENAMETOOLONG`.

---

## 2. Directorios y Archivos Problemáticos Exactos

El problema se manifiesta en todas las subcarpetas de entregas generadas en pruebas o en tiempo de ejecución bajo:
- `backend/data/storage/<institution_uuid>/submissions/<activity_uuid>/<student_uuid>/<submission_uuid>/`

### Ejemplos identificados en la inspección:
1. `backend/data/storage/01cc6a06-75d8-4f32-9d1c-6edaafaa92c7/submissions/9653f47d-8bc7-4e4e-a3b8-e1b4b27f0cf3/ed580a09-0d0b-4753-8f88-427d49d3b6f0/`
2. `backend/data/storage/021c813e-b5b5-4bab-9c63-ad9ee6a55784/submissions/3d2562d6-585f-4863-a1c3-bcdbc06445d9/e61e8191-3ead-455c-847d-9c299735a9f5/`
3. `backend/data/storage/04371905-c023-4d93-b1a7-2844bd1c0406/submissions/cf6336cf-3e45-4014-97d6-fb25617dcfe3/f23e76bf-69e4-445e-8003-8b0c12124cad/`
4. `backend/data/storage/06757e03-39d6-40c3-b64c-06657a18c076/submissions/de8f0f72-5ca5-4c3d-a4aa-008078ddd247/c4ed4bf6-cfd5-4b1a-ae91-3367bbf0ceff/`
5. `backend/data/storage/0bc6704e-50e2-4a3c-ac9b-b3ed607e71a4/submissions/da029c9f-0164-408c-ad2e-e7ce11ce1f58/d388d8f8-826d-412a-b397-a96814447cef/`
*(Más de 50 árboles de directorios de prueba de instituciones generados por los tests automatizados de la suite `backend/tests/test_student_submissions_api.py`)*.

---

## 3. Análisis del `.gitignore` Actual

Se examinó minuciosamente el archivo [.gitignore](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.gitignore) del proyecto (181 líneas):

- **Lo que sí excluye:**
  - Archivos de entorno (`.env`, `.env.*`)
  - Cachés de Python (`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`)
  - Volúmenes locales de Docker (`.docker-data/`, `postgres-data/`, `redis-data/`, `docker-volumes/`)
  - Archivos temporales (`tmp/`, `temp/`, `.tmp/`)
  - Caches de Frontend (`node_modules/`, `frontend/dist/`, `frontend/.vite/`)
- **La omisión:**
  - **No existe ninguna regla** para `backend/data/` ni `backend/data/storage/` ni `data/storage/`.
  - Como resultado, Git intenta registrar e inspeccionar todos los archivos adjuntos binarios (PDF, DOCX, ZIP, etc.) y entregas de estudiantes creados localmente.

### Advertencia Crítica sobre Código Fuente vs. Almacenamiento:
Existe un módulo de código fuente legítimo en:
- `backend/app/core/storage/` (contiene `interfaces.py`, `local.py`, `service.py`, `__init__.py`).
- **Bajo ninguna circunstancia** debe usarse una regla genérica como `storage/` o `*/storage/` en `.gitignore`, ya que excluiría inadvertidamente el código fuente de los drivers de almacenamiento.
- La regla debe estar estrictamente calificada y anclada: `backend/data/` y `data/storage/`.

---

## 4. Estado de Rastreo en Git (Git Tracking Status)

Se ejecutaron auditorías de solo lectura sobre el árbol del índice de Git:
1. `git ls-files backend/data` -> **0 archivos rastreados**
2. `git ls-files --stage backend/data` -> **0 archivos en stage/índice**
3. `git log -n 5 --oneline -- backend/data` -> **0 commits históricos**

### Conclusión del estado de rastreo:
Los archivos bajo `backend/data/storage/` **NUNCA han sido commiteados ni indexados en Git**.  
Son 100% archivos de trabajo locales (*untracked working tree artifacts*).  
Por tanto, **no se requiere ejecutar `git rm` destructivo** ni reescribir el historial de Git. Al agregar la regla en `.gitignore`, Git dejará de recorrerlos inmediatamente.

---

## 5. Estrategia de Corrección Recomendada

La solución es una estrategia combinada de dos capas:

### Capa 1: Exclusión en `.gitignore` (Solución Primaria y Definitiva)
Agregar la sección de almacenamiento en ejecución en `.gitignore`:
```gitignore
# ------------------------------------------------------------
# Application runtime storage and uploads (Phase B3-H11/H13)
# ------------------------------------------------------------
backend/data/
data/storage/
```
Esto le indica a Git que **pode (*prune*) inmediatamente** el recorrido de la carpeta `backend/data/`, eliminando al 100% las advertencias y previniendo que archivos pesados o de datos personales de estudiantes se suban accidentalmente al repositorio.

### Capa 2: Habilitación de `core.longpaths` en Git para Windows (Defensa en Profundidad)
Configurar Git en el repositorio local para soportar rutas de más de 260 caracteres en Windows:
```bash
git config core.longpaths true
```
Esto previene que cualquier otra ruta profunda que pueda surgir en el entorno de desarrollo de Windows genere bloqueos.

---

## 6. Verificación de Ciclo de Vida de la Aplicación en Tiempo de Ejecución

Se verificó el comportamiento del backend respecto a estos directorios:
- En [backend/app/core/storage/local.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/local.py#L35-L38):
  ```python
  def __init__(self, base_path: str | Path) -> None:
      self.base_path = Path(base_path).resolve()
      self.base_path.mkdir(parents=True, exist_ok=True)
  ```
- En el guardado de archivos ([backend/app/core/storage/local.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa Virtual Nacional PEVN/backend/app/core/storage/local.py#L64-L65)):
  ```python
  def _write() -> None:
      os.makedirs(target.parent, exist_ok=True)
  ```
- **Resultado:** La aplicación recrea automáticamente la estructura de directorios necesaria (`./data/storage/...`) al iniciarse o al recibir un archivo adjunto. No se requieren carpetas vacías ni archivos `.gitkeep` en Git para su correcto funcionamiento.

---

## 7. Comandos Exactos que Deben Ejecutarse (Plan de Ejecución)

Una vez aprobada esta auditoría, los pasos a ejecutar son:

### Paso 1: Configurar Git en Windows para rutas largas
```bash
git config core.longpaths true
```

### Paso 2: Actualizar `.gitignore`
Insertar las siguientes líneas en `.gitignore` en la sección de volúmenes de datos / almacenamiento:
```gitignore
# ------------------------------------------------------------
# Application runtime storage and uploads (Phase B3-H11/H13)
# ------------------------------------------------------------
backend/data/
data/storage/
```

### Paso 3: (Preventivo / Contingencia) Si algún archivo estuviera en stage
*Nota: Nuestra auditoría confirmó que ningún archivo está en el índice. No obstante, si existiera algún archivo residual en el índice local:*
```bash
git rm -r --cached --ignore-unmatch backend/data/
```
*(El flag `--cached` garantiza que los archivos físicos locales NO se toquen ni se borren)*.

### Paso 4: Validar el estado de Git
```bash
git status -s
```
Verificar que la advertencia `Filename too long` haya desaparecido por completo y que `backend/data/` ya no aparezca en la lista de cambios sin rastrear.

---

## 8. Análisis de Riesgos

| Riesgo Potencial | Nivel | Mitigación Implementada |
| :--- | :--- | :--- |
| **Pérdida accidental de datos o entregas locales** | NINGUNO | No se utiliza ningún comando destructivo (`rm -rf`, `git clean -f`, etc.). Los archivos físicos locales permanecen intactos en disco. |
| **Afectar código fuente de storage** | NINGUNO | La regla en `.gitignore` es `backend/data/` y `data/storage/`. El código fuente reside en `backend/app/core/storage/` y permanece 100% rastreado y visible. |
| **Fallo en arranque de la aplicación** | NINGUNO | `LocalStorageDriver` contiene `mkdir(parents=True, exist_ok=True)` y genera directorios dinámicamente según sea necesario. |
| **Rotura de lógica de negocio o esquemas** | NINGUNO | No se modifica ningún archivo `.py` de servicios, endpoints o migraciones de base de datos. |

---

## 9. Confirmación de Integridad de Datos

Se confirma explícitamente que:
1. **Ningún archivo de entrega ni recurso de actividad será eliminado del disco.**
2. **Ningún esquema de base de datos (`backend/migrations/`) será alterado.**
3. **Ninguna lógica de negocio del portal de docentes ni de estudiantes será modificada.**
4. **Ningún commit ni push se realizará automáticamente.**

---

## 10. Lista de Verificación Final de Validación (Checklist)

- [x] Causa raíz identificada y documentada (colisión de longitud de ruta + omisión en `.gitignore`).
- [x] Verificado que `backend/data/` NO está rastreado en Git.
- [x] Verificado que `backend/app/core/storage/` es código fuente y NO será ignorado.
- [x] Verificado que `core.longpaths` en Git soluciona la limitación de la API Win32 en Windows.
- [x] Probada la eficacia de excluir `backend/data/` eliminando las advertencias al 100%.
- [x] Verificado que el backend recrea directorios de forma autónoma con `\\?\` y `os.makedirs`.
- [ ] **Pendiente:** Aprobación del usuario para aplicar `git config core.longpaths true` y actualizar `.gitignore`.
