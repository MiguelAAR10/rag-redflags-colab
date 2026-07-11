# TDR Risk Auditor — contenedor de producción (F21/F22, spec 007)
# Liviano a propósito: SIN torch/sentence-transformers/faiss. El retrieval es
# Qdrant Cloud + embeddings Gemini por API; la generación es Vertex AI.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

RUN pip install --no-cache-dir \
    streamlit \
    fastapi uvicorn jinja2 python-multipart \
    pydantic pydantic-settings sqlmodel \
    google-genai qdrant-client python-docx pymupdf numpy

COPY apps/ apps/
COPY packages/ packages/
COPY .streamlit/ .streamlit/

# Defaults de producción (los secretos llegan por Cloud Run env/secrets)
ENV RAG_VECTOR_STORE=qdrant \
    RAG_GROUNDING_METHOD=gemini \
    RAG_INDEX_SUBJECT_DOCS=1 \
    RAG_USE_GOOGLE_LLM=1 \
    RAG_GEMINI_MODEL=gemini-2.5-flash \
    UPLOAD_DIR=/tmp/uploads \
    DATABASE_URL=sqlite:////tmp/tdr_review.db

EXPOSE 8080

# Cloud Run inyecta $PORT
CMD ["sh", "-c", "streamlit run apps/web_streamlit/app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true"]
