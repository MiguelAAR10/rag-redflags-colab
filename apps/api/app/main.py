import sys
from pathlib import Path

# Ensure the repo root is on sys.path so `packages.rag_core` resolves
# when uvicorn is started from apps/api/.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routes.tdrs import router as tdrs_router


app = FastAPI(title="TDR Risk Review API")

# El frontend Next.js (Vercel) consume /api/* directamente desde el navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


app.include_router(tdrs_router)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
