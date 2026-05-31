"""
RAG Core Agent — Full RAG pipeline: retrieve, rerank, generate (Qwen/LLM),
verify grounding, build citations.

Orchestrates:
    query → hybrid_search top-20 → rerank top-5 → generate answer
    → verify grounding → build citations → result dict

Qwen is the runtime LLM (runs in Colab/GPU). Accepts generate_fn injection
for deterministic unit tests without GPU.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Eres un AUDITOR SENIOR en contratación pública, integridad y control gubernamental, "
    "especializado en la guía OCP/OCDS de red flags. Analizas un fragmento de contrato, TDR "
    "o licitación basándote ÚNICAMENTE en los fragmentos recuperados que se te proporcionan.\n\n"
    "REGLAS OBLIGATORIAS:\n"
    "1. NUNCA afirmes corrupción, fraude ni ilegalidad comprobada. "
    "Usa exclusivamente: 'señal de riesgo', 'red flag potencial', "
    "'posible irregularidad a revisar'.\n"
    "2. Cada observación DEBE sustentarse en: (a) evidencia del fragmento del usuario, "
    "(b) el indicador/criterio recuperado de la guía, (c) página/referencia si está disponible.\n"
    "3. Si los fragmentos no alcanzan, dilo: 'no hay evidencia suficiente'.\n"
    "4. No inventes normas, páginas, cifras ni indicadores. No des asesoría legal definitiva.\n"
    "5. Sé breve, técnico y útil para un comité de revisión.\n"
    "6. Termina SIEMPRE con 'Requiere revisión humana.'\n\n"
    "FORMATO DE RESPUESTA (obligatorio):\n"
    "### Evaluación preliminar\n"
    "Riesgo general: Bajo / Medio / Alto\n\n"
    "### Señales de riesgo identificadas\n"
    "1. Señal: ...\n"
    "   - Evidencia del fragmento: ...\n"
    "   - Por qué importa: ...\n"
    "   - Sustento recuperado: (Indicador: nombre, p.XX)\n\n"
    "### Qué faltaría validar\n- ...\n\n"
    "### Conclusión\n"
    "No se determina corrupción; son señales de riesgo potenciales. Requiere revisión humana."
)

# Alias explícito para reutilizar el mismo prompt con otros LLMs (p. ej. MiniMax).
AUDITOR_SYSTEM_PROMPT = SYSTEM_PROMPT

REFUSAL_MESSAGE = (
    "No hay evidencia suficiente en los documentos recuperados "
    "para emitir observaciones fundamentadas. "
    "Requiere revisión humana."
)


def _build_context(chunks: List[Dict]) -> str:
    return "\n\n".join(
        f"[Fuente: {c.get('indicator_name') or 'Desconocida'} "
        f"({c.get('indicator_code') or 'N/A'}, "
        f"p.{c.get('page_start', '?')}-{c.get('page_end', '?')})] "
        f"{c.get('text', '')}"
        for c in chunks
    )


def _build_prompt(query: str, chunks: List[Dict], system_prompt: str) -> str:
    # El system_prompt va en el rol 'system' del chat template; aquí solo el contenido de usuario.
    return (
        f'Fragmento a evaluar:\n"""\n{query}\n"""\n\n'
        f"Evidencia recuperada (guía OCP/OCDS):\n{_build_context(chunks)}\n\n"
        f"Genera el análisis con el FORMATO obligatorio."
    )


@lru_cache(maxsize=1)
def _load_qwen(model_name: str = "Qwen/Qwen2.5-3B-Instruct"):
    """Carga (y CACHEA) tokenizer+model de Qwen. Se carga UNA sola vez.

    Evita recargar el modelo (~6GB) en cada llamada a analyze() → menos tiempo
    y menor riesgo de OOM en Colab.
    """
    import os

    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    kwargs = {"device_map": "auto", "trust_remote_code": True}

    # Cuantización 4-bit opcional (RAG_QWEN_4BIT=1) para Colab T4 → menos memoria/OOM.
    if os.environ.get("RAG_QWEN_4BIT") == "1":
        try:
            import torch
            from transformers import BitsAndBytesConfig

            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.float16,
            )
            logger.info("Qwen en 4-bit (NF4) vía bitsandbytes.")
        except Exception as exc:
            logger.warning("bitsandbytes 4-bit no disponible (%s); carga normal.", exc)
            kwargs["torch_dtype"] = "auto"
    else:
        kwargs["torch_dtype"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(model_name, **kwargs)
    return tokenizer, model


def _qwen_generate(
    query: str, chunks: List[Dict], system_prompt: str
) -> str:
    """Generate answer with Qwen2.5-3B locally via transformers (modelo cacheado)."""
    model_name = "Qwen/Qwen2.5-3B-Instruct"
    prompt = _build_prompt(query, chunks, system_prompt)

    tokenizer, model = _load_qwen(model_name)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        do_sample=False,
    )
    generated = outputs[0][len(inputs.input_ids[0]):]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def analyze(
    query: str,
    generate_fn: Optional[Callable[[str, List[Dict], str], str]] = None,
    retrieved_chunks: Optional[List[Dict]] = None,
    grounding_method: str = "lexical",
    grounding_threshold: float = 0.25,
) -> Dict:
    """
    Full RAG pipeline: retrieve → rerank → generate → verify → cite.

    Args:
        query: the user query / contract description to analyze.
        generate_fn: if provided, called as `fn(query, chunks, system_prompt) -> str`.
            Use for tests with a fake LLM.
        retrieved_chunks: if provided, skip retrieval+reranking (for tests).
        grounding_method: 'lexical' (default, deterministic) or 'embedding'.
        grounding_threshold: minimum similarity to consider a sentence supported.

    Returns:
        {
            "answer": str,
            "sentences": [{"text": str, "supported": bool}, ...],
            "citations": [{"sentence": str, "chunk_id": str, ...}, ...],
            "grounding_ratio": float,
            "refusal": str or "",
            "retrieved": [chunk dicts, ...],
        }
    """
    from packages.rag_core.verifier import (
        split_sentences,
        verify_grounding,
        refusal_check,
    )
    from packages.rag_core.citations import build_citations

    # 1. Retrieve + Rerank (or use provided chunks)
    if retrieved_chunks is None:
        retrieved_chunks = _retrieve_and_rerank(query, k_retrieve=20, n_rerank=5)

    # 2. Generate answer
    if generate_fn is not None:
        answer = generate_fn(query, retrieved_chunks, SYSTEM_PROMPT)
    else:
        try:
            answer = _qwen_generate(query, retrieved_chunks, SYSTEM_PROMPT)
        except Exception as exc:
            logger.warning("Qwen no disponible (%s). Usando fallback simple.", exc)
            answer = _minimal_analysis(query, retrieved_chunks)

    # 3. Verify grounding
    sentences = split_sentences(answer)
    grounding = verify_grounding(sentences, retrieved_chunks, threshold=grounding_threshold, method=grounding_method)

    # 4. Refusal check
    refusal = refusal_check(grounding)

    # 5. Citations
    citations = build_citations(grounding["sentences"], retrieved_chunks)

    return {
        "answer": answer,
        "sentences": [
            {"text": s["text"], "supported": s["supported"]}
            for s in grounding["sentences"]
        ],
        "citations": citations,
        "grounding_ratio": grounding["grounding_ratio"],
        "refusal": refusal,
        "retrieved": retrieved_chunks,
    }


def _retrieve_and_rerank(
    query: str, k_retrieve: int = 20, n_rerank: int = 5
) -> List[Dict]:
    """Retrieve with hybrid_search + rerank top-n."""
    from packages.rag_core.retrievers import hybrid_search, load_chunks

    chunks = load_chunks()

    # hybrid_search: uses FAISS (BM25 optional); returns filtered by family if route_family detects one
    candidates = hybrid_search(query, k=k_retrieve, chunks=chunks)

    if not candidates:
        return []

    from packages.rag_core.rerankers import rerank

    return rerank(query, candidates, top_n=n_rerank)


def _minimal_analysis(query: str, chunks: List[Dict], system_prompt: str = "") -> str:
    """Fallback analysis when Qwen is not available (ignores system_prompt)."""
    if not chunks:
        return REFUSAL_MESSAGE

    lines = [
        "Análisis preliminar (sin modelo de lenguaje — requiere Qwen en Colab):",
        "",
    ]
    for i, c in enumerate(chunks[:5]):
        lines.append(
            f"{i + 1}. Señal de riesgo potencial: {c.get('indicator_name', 'Desconocida')} "
            f"({c.get('indicator_code', 'N/A')}, "
            f"p.{c.get('page_start', '?')}-{c.get('page_end', '?')}). "
            "Requiere revisión humana."
        )

    return "\n".join(lines)


if __name__ == "__main__":
    print("agent.py loaded OK")
    print(f"SYSTEM_PROMPT length: {len(SYSTEM_PROMPT)}")
