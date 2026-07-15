# Demo PDF Downloads Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Exponer los seis PDFs públicos de demostración desde `/documentos` con descargas raw de GitHub y lenguaje seguro.

**Architecture:** Mantener un catálogo tipado y estático en la página existente, independiente del estado de Cloud Run/SQLite. Los binarios permanecen en `data/samples`; Vercel solo renderiza enlaces externos y el CTA hacia `/analizar`.

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS, pytest para contrato estático, GitHub raw.

---

### Task 0: Preflight y activación

**Files:**
- Modify: `progress/NEXT_ACTION.md`

- [ ] **Step 1: Validate the harness**

Run from repo root: `bash scripts/init.sh`
Expected: `Init OK`.

- [ ] **Step 2: Activate this closure task**

Actualizar temporalmente la acción única para reflejar la integración del trabajo externo, la recuperación de artefactos Colab y las descargas de demo.

### Task 1: Contrato de assets de demostración

**Files:**
- Create: `packages/rag_core/tests/test_demo_assets.py`
- Create: `apps/web/src/app/documentos/page.test.tsx`
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/src/test/setup.ts`
- Modify: `apps/web/package.json`
- Modify: `.github/workflows/ci.yml`
- Test: `packages/rag_core/tests/test_demo_assets.py`
- Test: `apps/web/src/app/documentos/page.test.tsx`

- [ ] **Step 1: Write the failing test**

Validar exactamente seis PDFs, nombres únicos y tamaños mayores que cero. En Vitest, mockear `listTdrs()` con rechazo y comprobar que las seis tarjetas siguen visibles, con seis URLs raw, acciones externas seguras y CTA a `/analizar`.

- [ ] **Step 2: Run test to verify it fails**

Run from repo root: `python3 -m pytest -q packages/rag_core/tests/test_demo_assets.py && npm --prefix apps/web test`
Expected: FAIL porque la página aún no contiene el catálogo.

- [ ] **Step 3: Keep the test minimal**

Usar Vitest 4 + jsdom + React Testing Library; no añadir Playwright ni snapshots.

### Task 2: Catálogo y UI de descarga

**Files:**
- Modify: `apps/web/src/app/documentos/page.tsx`
- Test: `packages/rag_core/tests/test_demo_assets.py`

- [ ] **Step 1: Add typed catalog**

Definir `DEMO_PDF_BASE` y seis objetos con `filename`, `title`, `source` y descripción prudente.

- [ ] **Step 2: Render independent section**

Mostrar la sección antes del historial dinámico, con aviso visible de fuentes públicas, señales potenciales y revisión humana.

Reemplazar “TDRs auditados” por “documentos revisados” y “Auditar un TDR” por “Analizar un documento”.

- [ ] **Step 3: Add safe actions**

Cada tarjeta incluye descarga externa (`target="_blank"`, `rel="noreferrer"`) y CTA a `/analizar`.

- [ ] **Step 4: Run targeted test**

Run from repo root: `python3 -m pytest -q packages/rag_core/tests/test_demo_assets.py && npm --prefix apps/web test`
Expected: PASS.

- [ ] **Step 5: Add frontend tests to CI**

Añadir `npm test` entre `npm ci` y lint/build en `.github/workflows/ci.yml`, con `working-directory: apps/web`.

### Task 3: Verificación integrada

**Files:**
- Modify only if verification finds a defect.

- [ ] **Step 1: Frontend quality gates**

Run from repo root: `npm --prefix apps/web run lint && npm --prefix apps/web run build`
Expected: exit 0 and static routes generated.

- [ ] **Step 2: Project gate**

Run from repo root: `bash scripts/verify.sh`
Expected: all tests pass, only documented optional skips.

- [ ] **Step 3: Remote smoke after push**

Run from repo root a read-only HTTP loop that checks `https://tdr-risk-auditor.vercel.app/documentos` and these six exact URLs, requiring HTTP 200:

- `https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/tdr-tce-01626-2023-essalud-comite-nulo.pdf`
- `https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/tdr-tce-00132-2022-hospital-lambayeque-registro-sanitario.pdf`
- `https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/tdr-tce-04185-2022-fospeme-certificado-incumplido.pdf`
- `https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/tdr-contraloria-bid-seguimiento-contractual.pdf`
- `https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/tdr-predes-zona-segura-los-olivos.pdf`
- `https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples/tdr-pronied-infraestructura-educativa.pdf`

Do not claim availability before all checks pass.

- [ ] **Step 4: Close project memory**

Actualizar `docs/CAVELOG.md`, `progress/CURRENT_STATE.md`, restaurar `progress/NEXT_ACTION.md` a Colab T4 y ejecutar desde la raíz `bash scripts/handoff.sh "demo-pdf-downloads"`.
