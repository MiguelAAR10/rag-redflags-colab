# COLAB — Cómo entregar y correr el notebook

El entregable es `notebooks/redflags_rag_colab.ipynb`. Corre en **Google Colab con GPU T4**.

## 1. Subir el repo a GitHub
```bash
git init && git add -A
git commit -m "RAG agentico red flags (F0-F7) + notebook Colab"
git branch -M main
git remote add origin git@github-personal:MiguelAAR10/rag-redflags-colab.git
git push -u origin main
# Clonado en Colab (repo público): https://github.com/MiguelAAR10/rag-redflags-colab.git
```
> El PDF (`data/raw/`), los `.jsonl` procesados y el índice FAISS están **gitignored** → el notebook los **regenera** en Colab (por eso pide subir el PDF). No subas el PDF a un repo público (derechos de la guía OCP).

## 2. Abrir en Colab
1. Sube el `.ipynb` a Colab (o ábrelo desde GitHub: *File → Open notebook → GitHub*).
2. **Runtime → Change runtime type → GPU (T4)**.
3. **Edita la celda 1.2**: `REPO_URL = "https://github.com/TU_USUARIO/rag-redflags-colab.git"`.
4. **Secrets (🔑)**: añade `HF_TOKEN` con tu token de HuggingFace.
5. Cuando la celda 2.1 lo pida, **sube** `OCP2024-RedFlagProcurement-1.pdf`.
6. **Runtime → Run all.**

## 3. Para los slides (aparte)
- Captura: el diagrama del pipeline (celda 0), la tabla de chunking (3.1), la comparación de métodos (9.1) y la demo final (10.1).
- Estructura de 8 secciones en `docs/RUBRICA.md`.

## Notas
- BM25 se activa porque Colab instala `rank_bm25` (celda 1.1); en local estaba desactivado.
- Qwen2.5-3B y el grounding `embedding` dan ratios realistas en GPU (en local se usa fallback).
