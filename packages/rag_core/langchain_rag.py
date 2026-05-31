"""
Fase 9 — Vía LangChain para consultar/validar la data desde el notebook.

RAG alternativo construido con LangChain sobre los MISMOS chunks y el MISMO
modelo de embeddings (intfloat/multilingual-e5-base) que `rag_core`.

¿Dónde se guardan los embeddings?
- rag_core (crudo):   data/index/redflags_flatip.index + chunk_id_mapping.json
- LangChain (aquí):   data/index/langchain_faiss/  (index.faiss + index.pkl)

Las dependencias de LangChain se importan de forma perezosa (lazy) para que el
módulo se pueda importar sin tenerlas instaladas (el gate hace skip en local;
en Colab se instalan y corre de verdad).
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_MODEL = "intfloat/multilingual-e5-base"
DEFAULT_PERSIST_DIR = "data/index/langchain_faiss"

# Prompt con lenguaje seguro (mismo criterio que agent.py)
SAFE_SYSTEM = (
    "Eres un asistente que analiza riesgos en contratación pública. "
    "Responde SOLO con base en el contexto. NUNCA afirmes corrupción ni fraude "
    "comprobado: usa 'señal de riesgo' / 'red flag potencial'. Cita los indicadores. "
    "Si el contexto no soporta la respuesta, di 'no hay evidencia suficiente'. "
    "Termina con 'Requiere revisión humana.'"
)


def _doc_payload(chunk: Dict) -> Dict:
    """Convierte un chunk (dict) en (page_content, metadata). Pura, sin LangChain.

    Testeable siempre (no requiere langchain instalado).
    """
    meta_keys = (
        "chunk_id",
        "family",
        "indicator_code",
        "indicator_name",
        "block_type",
        "page_start",
        "page_end",
    )
    metadata = {k: chunk.get(k) for k in meta_keys}
    return {"page_content": chunk.get("text", ""), "metadata": metadata}


def chunks_to_documents(chunks: List[Dict]) -> List:
    """Lista de chunks -> lista de langchain_core.documents.Document."""
    from langchain_core.documents import Document

    return [Document(**_doc_payload(c)) for c in chunks]


def get_embeddings(model_name: str = DEFAULT_MODEL):
    """HuggingFaceEmbeddings normalizados (coseno via IP)."""
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=model_name,
        encode_kwargs={"normalize_embeddings": True},
    )


def build_vectorstore(
    chunks: List[Dict],
    persist_dir: str = DEFAULT_PERSIST_DIR,
    model_name: str = DEFAULT_MODEL,
):
    """Construye un FAISS de LangChain desde los chunks y lo guarda con save_local."""
    from langchain_community.vectorstores import FAISS

    docs = chunks_to_documents(chunks)
    vs = FAISS.from_documents(docs, get_embeddings(model_name))
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    vs.save_local(persist_dir)
    return vs


def load_vectorstore(
    persist_dir: str = DEFAULT_PERSIST_DIR,
    model_name: str = DEFAULT_MODEL,
):
    """Carga el FAISS de LangChain persistido."""
    from langchain_community.vectorstores import FAISS

    return FAISS.load_local(
        persist_dir,
        get_embeddings(model_name),
        allow_dangerous_deserialization=True,  # archivo propio, generado por nosotros
    )


def get_retriever(vectorstore, k: int = 5, family: Optional[str] = None):
    """Retriever top-k; si se pasa `family`, filtra por metadata."""
    search_kwargs: Dict = {"k": k}
    if family:
        search_kwargs["filter"] = {"family": family}
    return vectorstore.as_retriever(search_kwargs=search_kwargs)


def quick_query(query: str, k: int = 5, family: Optional[str] = None,
                persist_dir: str = DEFAULT_PERSIST_DIR) -> List[Dict]:
    """Validación rápida de la data: top-k documentos (sin LLM)."""
    vs = load_vectorstore(persist_dir)
    docs = get_retriever(vs, k=k, family=family).invoke(query)
    return [{"text": d.page_content, **d.metadata} for d in docs]


def build_qa_chain(retriever, llm):
    """RAG con LLM: create_retrieval_chain (devuelve answer + context/fuentes).

    Compatible con varias versiones de LangChain (import con fallback).
    """
    from langchain_core.prompts import ChatPromptTemplate

    try:
        from langchain.chains import create_retrieval_chain
        from langchain.chains.combine_documents import create_stuff_documents_chain
    except Exception:  # versiones nuevas mueven a langchain_classic
        from langchain_classic.chains import create_retrieval_chain
        from langchain_classic.chains.combine_documents import (
            create_stuff_documents_chain,
        )

    prompt = ChatPromptTemplate.from_messages(
        [("system", SAFE_SYSTEM + "\n\nContexto:\n{context}"), ("human", "{input}")]
    )
    combine = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, combine)


def get_qwen_llm(model_id: str = "Qwen/Qwen2.5-3B-Instruct", max_new_tokens: int = 512):
    """LLM local Qwen vía HuggingFacePipeline (úsalo en Colab con GPU)."""
    from langchain_huggingface import HuggingFacePipeline

    return HuggingFacePipeline.from_model_id(
        model_id=model_id,
        task="text-generation",
        pipeline_kwargs={"max_new_tokens": max_new_tokens, "do_sample": False},
    )


def get_minimax_llm(model: Optional[str] = None, base_url: Optional[str] = None):
    """LLM MiniMax vía API OpenAI-compatible (OPCIONAL / bonus, NO es el principal).

    Qwen sigue siendo el LLM obligatorio del proyecto; MiniMax es una "segunda
    opinión" opcional. Config por entorno (según tu plan MiniMax):
      MINIMAX_API_KEY   (requerido)
      MINIMAX_BASE_URL  (default https://api.minimax.io/v1)
      MINIMAX_MODEL     (default MiniMax-Text-01)
    """
    import os

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model or os.environ.get("MINIMAX_MODEL", "MiniMax-Text-01"),
        base_url=base_url or os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1"),
        api_key=os.environ.get("MINIMAX_API_KEY", ""),
        temperature=0.2,
    )
