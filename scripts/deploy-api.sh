#!/usr/bin/env bash
# Despliega el backend FastAPI (JSON API) como servicio Cloud Run `tdr-api`.
# Reutiliza el mismo Dockerfile del contenedor Streamlit, con command override
# a uvicorn, y copia las env vars (Vertex + Qdrant) del servicio existente
# `tdr-risk-auditor` sin exponerlas en la terminal.
set -euo pipefail

REGION="us-central1"
PROJECT="rag-redflags-v2"
ENV_FILE="$(mktemp /tmp/tdr-api-env.XXXXXX.yaml)"
trap 'rm -f "$ENV_FILE"' EXIT

gcloud run services describe tdr-risk-auditor \
  --region "$REGION" --project "$PROJECT" --format=json \
  | jq -r '.spec.template.spec.containers[0].env | map("\(.name): \"\(.value)\"") | .[]' \
  > "$ENV_FILE"

gcloud run deploy tdr-api \
  --source . \
  --region "$REGION" --project "$PROJECT" \
  --allow-unauthenticated \
  --memory 1Gi --cpu 1 --timeout 300 \
  --command sh \
  --args '^|^-c|uvicorn app.main:app --app-dir apps/api --host 0.0.0.0 --port ${PORT:-8080}' \
  --env-vars-file "$ENV_FILE" \
  --quiet

echo
echo "URL del API:"
gcloud run services describe tdr-api --region "$REGION" --project "$PROJECT" \
  --format="value(status.url)"
