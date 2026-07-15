# Colab Dual RAG with Gemini Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the primary Colab notebook with an automatic OCP corpus, FAISS/Qwen as the academic default, and an opt-in Gemini API demo over either FAISS or Qdrant.

**Architecture:** Keep retrieval selection and result normalization in a small importable `notebook_rag` module. Reuse `make_vector_store`, `analyze`, Gemini embeddings, and the existing Google LLM adapter; the notebook only configures secrets and demonstrates the flows. Qdrant and Gemini remain optional so the default Colab `Run all` path continues to satisfy the Qwen/FAISS rubric.

**Tech Stack:** Python 3.12, Google Colab, nbformat, FAISS, Qdrant, google-genai, pytest.

---

## File Structure

- Create `packages/rag_core/notebook_rag.py`: notebook-specific backend selection, normalized retrieval contract, Qdrant preflight, and optional comparison helpers.
- Modify `packages/rag_core/vector_store.py`: expose normalized result handling and Qdrant collection validation without changing default FAISS behavior.
- Modify `packages/rag_core/tests/test_vector_store.py`: TDD coverage for normalization and Qdrant preflight.
- Create `packages/rag_core/tests/test_notebook_rag.py`: hermetic selector, skip, retrieval, and dual-flow tests.
- Modify `packages/rag_core/tests/test_notebook_smoke.py`: static notebook contract for automatic OCP loading and optional Gemini/Qdrant configuration.
- Modify `apps/api/app/adapters/google_llm.py`: injectable Gemini client and strict optional mode for notebook integration.
- Modify `apps/api/tests/test_google_llm.py`: Gemini adapter tests for configuration, empty response, and API failure.
- Modify `notebooks/redflags_rag_colab.ipynb`: dependency/config cells and opt-in dual RAG/Gemini demonstration.
- Modify `docs/COLAB.md`: exact Secrets and backend execution instructions.
- Modify `docs/CAVELOG.md` and `progress/`: evidence and handoff required by the project workflow.

### Task 1: Normalize vector results and validate Qdrant

**Files:**
- Modify: `packages/rag_core/vector_store.py:23-133`
- Modify: `packages/rag_core/tests/test_vector_store.py`

- [ ] **Step 1: Write failing normalization tests**

Add tests asserting that FAISS/Qdrant results always contain:

```python
EXPECTED_KEYS = {
    "chunk_id", "text", "score", "indicator_code", "indicator_name",
    "family", "page_start", "page_end",
}

def test_normalize_result_fills_optional_metadata():
    result = normalize_result({"text": "evidence", "score": "0.8"})
    assert set(result) == EXPECTED_KEYS
    assert result["score"] == 0.8
    assert result["indicator_code"] is None
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python3 -m pytest packages/rag_core/tests/test_vector_store.py -q`

Expected: failure because `normalize_result` and preflight do not exist.

- [ ] **Step 3: Implement minimal normalization**

Add `normalize_result()` and `normalize_results()` to `vector_store.py`. Reject empty text, cast scores to `float`, and fill absent metadata with `None`.

- [ ] **Step 4: Write failing Qdrant preflight tests**

Cover missing collection, zero points, wrong dimension, client failure, and a valid 768-dimensional cosine collection using an injected fake client.

- [ ] **Step 5: Run preflight tests and verify RED**

Run: `python3 -m pytest packages/rag_core/tests/test_vector_store.py -q`

Expected: failures because `preflight()` is absent.

- [ ] **Step 6: Implement `QdrantVectorStore.preflight()`**

Validate before embedding/querying and cache successful validation on the instance. Error messages must name the collection and problem without including URL or API key.

- [ ] **Step 7: Normalize both stores at their boundary**

Wrap `FaissVectorStore.search()` and `QdrantVectorStore.search()` outputs with `normalize_results()`.

- [ ] **Step 8: Run focused tests and verify GREEN**

Run: `python3 -m pytest packages/rag_core/tests/test_vector_store.py -q`

Expected: all vector-store tests pass with no network.

### Task 2: Add notebook dual-RAG orchestration helpers

**Files:**
- Create: `packages/rag_core/notebook_rag.py`
- Create: `packages/rag_core/tests/test_notebook_rag.py`

- [ ] **Step 1: Write failing selector tests**

```python
def test_make_notebook_store_defaults_to_faiss():
    assert isinstance(make_notebook_store("", chunks=[]), FaissVectorStore)

def test_make_notebook_store_rejects_unknown_backend():
    with pytest.raises(ValueError, match="faiss.*qdrant"):
        make_notebook_store("other")
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python3 -m pytest packages/rag_core/tests/test_notebook_rag.py -q`

Expected: import failure because `notebook_rag.py` does not exist.

- [ ] **Step 3: Implement backend selection and optional-secret state**

Expose:

```python
def make_notebook_store(backend="faiss", **kwargs) -> VectorStore: ...
def qdrant_configured(env=os.environ) -> bool: ...
def gemini_configured(env=os.environ) -> bool: ...
def retrieve(query, *, backend="faiss", k=5, store=None, **kwargs) -> list[dict]: ...
```

Use `make_vector_store`; do not duplicate FAISS, Qdrant, or embedding logic.

- [ ] **Step 4: Write failing hermetic retrieval tests**

Test a fake FAISS store and fake Qdrant store through `retrieve()`. Assert an unconfigured Qdrant path returns an explicit `SKIPPED` status through a small result object/helper and never constructs a client.

- [ ] **Step 5: Implement the minimal retrieval helper and verify GREEN**

Implement only enough selection/status behavior to pass Step 4, then run:

`python3 -m pytest packages/rag_core/tests/test_notebook_rag.py -q`

- [ ] **Step 6: Write failing comparison helper tests**

Test comparison on gold items with expected indicators, exclusion of traps, Recall@5, latency, timeout, retrieved indicator codes, per-query differences, and `PASS/SKIPPED/ERROR` statuses. Do not compare raw similarity scores.

- [ ] **Step 7: Run comparison tests and verify RED**

Run: `python3 -m pytest packages/rag_core/tests/test_notebook_rag.py -q`

Expected: failures because the comparison helper is absent.

- [ ] **Step 8: Implement the comparison helper**

Add the smallest implementation that reports both backends independently and converts timeout/exception into `ERROR` without hiding the other backend result.

- [ ] **Step 9: Write failing dual-evidence tests**

Add tests for `validate_dual_evidence(analysis, contract_text)` per generated
signal:

- accepted when a quoted contract fragment exists in the original input and an OCP citation exists;
- rejected when contract evidence is fabricated;
- rejected when OCP citation is absent;
- rejected when the OCP citation has no literal `standard_evidence.quote`;
- two signals are evaluated independently, so one complete signal cannot make
  another incomplete signal pass;
- explicit abstention and `requires_human_review=True` on rejection.

- [ ] **Step 10: Run dual-evidence tests and verify RED**

Run: `python3 -m pytest packages/rag_core/tests/test_notebook_rag.py -q`

Expected: failures because per-signal dual validation is absent.

- [ ] **Step 11: Implement dual-evidence validation**

Parse each generated signal and its `Evidencia del fragmento` field, verify its
normalized quote is contained in the contract text, and associate the matching
OCP citation produced by `analyze()`. Require a literal quote from the retrieved
OCP chunk in `standard_evidence.quote`. Return separate evidence objects per
signal and reject only the incomplete signal.

- [ ] **Step 12: Run focused tests and verify GREEN**

Run: `python3 -m pytest packages/rag_core/tests/test_notebook_rag.py packages/rag_core/tests/test_vector_store.py -q`

Expected: all tests pass without secrets or network.

### Task 3: Make the Gemini adapter testable and strict when requested

**Files:**
- Modify: `apps/api/app/adapters/google_llm.py:46-130`
- Modify: `apps/api/tests/test_google_llm.py`

- [ ] **Step 1: Write failing adapter tests**

Cover an injected fake client capturing `gemini-2.5-flash`, temperature `0.1`, output-token limit, valid response, empty response, API exception, and missing auth with `strict=True`.

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest apps/api/tests/test_google_llm.py -q`

Expected: failures because client injection and strict behavior do not exist.

- [ ] **Step 3: Implement client injection and strict mode**

Extend `make_google_generate_fn(..., client=None, strict=False)`. Preserve the existing production fallback when `strict=False`; with `strict=True`, missing SDK/auth or API/empty-response failures raise a controlled `RuntimeError` without credentials.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python3 -m pytest apps/api/tests/test_google_llm.py -q`

Expected: all adapter tests pass.

### Task 4: Add notebook contract tests before editing cells

**Files:**
- Modify: `packages/rag_core/tests/test_notebook_smoke.py:71-86`

- [ ] **Step 1: Write failing static tests**

Require visible notebook usage of:

```python
required = [
    "RAG_BACKEND", "RAG_GENERATOR", "RUN_QDRANT_DEMO",
    "make_notebook_store", "standard_kb", "make_google_generate_fn",
    "GEMINI_API_KEY", "QDRANT_URL", "QDRANT_API_KEY",
]
```

Also assert the notebook still contains Qwen, FAISS, `load_pdf`, the automatic public PDF fallback, and no `getpass()`/`files.upload()`.

- [ ] **Step 2: Run smoke tests and verify RED**

Run: `python3 -m pytest packages/rag_core/tests/test_notebook_smoke.py -q`

Expected: new dual-RAG assertions fail before notebook changes.

### Task 5: Update the Colab notebook

**Files:**
- Modify: `notebooks/redflags_rag_colab.ipynb`

- [ ] **Step 1: Extend the install cell**

Ensure `google-genai` and `qdrant-client` are installed while preserving current Qwen, E5, FAISS, reranker, RAGAS-local, and Gradio dependencies.

- [ ] **Step 2: Add non-interactive configuration after repository setup**

Read Colab Secrets with a safe helper, copy values into environment variables only when present, and define:

```python
RAG_BACKEND = os.getenv("RAG_BACKEND", "faiss").lower()
RAG_GENERATOR = os.getenv("RAG_GENERATOR", "qwen").lower()
RUN_QDRANT_DEMO = os.getenv("RUN_QDRANT_DEMO", "0") == "1"
RUN_DUAL_RAG_COMPARISON = os.getenv("RUN_DUAL_RAG_COMPARISON", "0") == "1"
```

Print only configured/not-configured states.

- [ ] **Step 3: Preserve automatic OCP loading**

Keep the existing repository file plus public-download fallback and assert the PDF is larger than 1 MB. Do not add upload widgets.

- [ ] **Step 4: Add an opt-in dual retrieval cell**

Use `make_notebook_store()` and `retrieve()` from the importable module. FAISS must run by default. Qdrant must print `SKIPPED` when the flag or credentials are absent.

- [ ] **Step 5: Add an opt-in Gemini generation cell**

Use `apps.api.app.adapters.google_llm.make_google_generate_fn` with `model_name="gemini-2.5-flash"`, `temperature=0.1`, `strict=True`, and the existing `analyze(..., retrieved_chunks=..., generate_fn=...)` seam. Pass the result through `validate_dual_evidence()` and display contract evidence and OCP citations separately. Do not replace the Qwen cells.

- [ ] **Step 6: Add optional FAISS/Qdrant comparison**

Run only when `RUN_DUAL_RAG_COMPARISON` is true and both backends are available. Reuse the gold set, exclude traps, and show Recall@5, latency, retrieved codes, differences, timeout, and status.

- [ ] **Step 7: Update notebook traceability markdown**

Document Qwen/FAISS as the academic path and Gemini/Qdrant as an optional cloud comparison. Do not claim the cloud path passed unless it was executed with real credentials.

- [ ] **Step 8: Run smoke tests and verify GREEN**

Run: `python3 -m pytest packages/rag_core/tests/test_notebook_smoke.py packages/rag_core/tests/test_notebook_rag.py packages/rag_core/tests/test_vector_store.py apps/api/tests/test_google_llm.py -q`

Expected: all focused tests pass.

### Task 6: Hermetic end-to-end flows

**Files:**
- Modify: `packages/rag_core/tests/test_notebook_rag.py`

- [ ] **Step 1: Write failing FAISS/Qwen-style flow test**

Inject a fake FAISS store and deterministic generator into `analyze()`. Assert retrieval, grounding, OCP citation, contract evidence, and human-review flag.

- [ ] **Step 2: Run FAISS flow test and verify RED**

Run: `python3 -m pytest packages/rag_core/tests/test_notebook_rag.py -q`

Expected: the new full-flow test fails before composition is implemented.

- [ ] **Step 3: Implement only missing composition seams**

Keep orchestration in `notebook_rag.py`; do not fork `agent.analyze()`.

- [ ] **Step 4: Write failing Qdrant/Gemini-style flow test**

Inject a fake Qdrant store and fake strict Gemini client. Cover successful dual evidence, empty retrieval, and API failure.

- [ ] **Step 5: Run Qdrant/Gemini flow tests and verify RED**

Run: `python3 -m pytest packages/rag_core/tests/test_notebook_rag.py apps/api/tests/test_google_llm.py -q`

Expected: failures for the new cloud-flow cases.

- [ ] **Step 6: Implement only missing error/status handling**

Return explicit `PASS`, `SKIPPED`, or `ERROR`; never report an unexecuted cloud path as passing.

- [ ] **Step 7: Run both flows and verify GREEN**

Run: `python3 -m pytest packages/rag_core/tests/test_notebook_rag.py apps/api/tests/test_google_llm.py -q`

Expected: all integration tests pass without network.

### Task 7: Documentation, real integration, and full verification

**Files:**
- Modify: `docs/COLAB.md`
- Modify: `docs/CAVELOG.md`
- Create: `progress/runs/<timestamp>-opencode-colab-dual-rag-gemini.md`
- Modify: `progress/HANDOFF.md`

- [ ] **Step 1: Document Colab Secrets and modes**

Document `GEMINI_API_KEY`, `QDRANT_URL`, and `QDRANT_API_KEY`; explain that the default is FAISS/Qwen and cloud demos are opt-in.

- [ ] **Step 2: Run complete verification**

Run: `bash scripts/verify.sh`

Expected: harness validation, compileall, and pytest complete with exit code 0.

- [ ] **Step 3: Run a real Qdrant + Gemini smoke when credentials exist**

Use the configured environment without printing values. Query `standard_kb`, generate one analysis with `gemini-2.5-flash`, and assert both contract and OCP evidence plus human-review language. If credentials are unavailable, record `BLOCKED`, not `PASS`.

- [ ] **Step 4: Run a fresh Colab T4 validation**

Open the public notebook, select T4, and execute `Runtime -> Run all` with default FAISS/Qwen. Record duration and generated RAGAS-local report. Then enable the cloud flags with Colab Secrets and execute the focused Qdrant/Gemini cells. If authentication prevents execution, record the exact human blocker.

- [ ] **Step 5: Record evidence honestly**

Add CAVELOG and handoff evidence for local, real API, and Colab validations. Any unexecuted validation remains explicitly pending or blocked.

- [ ] **Step 6: Generate required handoff**

Run: `bash scripts/handoff.sh "colab-dual-rag-gemini"`

Expected: a new run file under `progress/runs/` and updated `progress/HANDOFF.md`.

- [ ] **Step 7: Inspect final diff**

Run: `git diff --check` and `git status --short`.

Expected: no whitespace errors; only intended files are added or modified. Existing unrelated user changes remain untouched.

No commit or push is performed unless the user explicitly requests it.
