"""
RAG Core Chunkers — Chunking de unidades documentales con overlap.

Aplica chunking sobre las unidades lógicas (salida de loaders.py) preservando
metadata y procedencia. Soporta tamaños variables y overlap configurables.

Esquema de cada chunk:
    chunk_id, doc_id (unidad padre), source_file, page_start, page_end,
    family, indicator_code, indicator_name, block_type, chunk_index,
    n_chars, text
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List, Dict


def chunk_units(units: List[Dict], size: int, overlap: int) -> List[Dict]:
    """
    Trocea unidades documentales en chunks con overlap.

    Args:
        units: Lista de unidades (salida de loaders.py).
        size: Tamaño máximo de cada chunk en caracteres.
        overlap: Caracteres de solapamiento entre chunks consecutivos.

    Returns:
        Lista de chunks con metadata heredada del padre.
    """
    if size <= 0:
        raise ValueError("size debe ser > 0")
    if overlap < 0:
        raise ValueError("overlap debe ser >= 0")
    if overlap >= size:
        raise ValueError("overlap debe ser < size")

    chunks = []

    for unit in units:
        text = unit.get("text", "")
        if not text:
            continue

        # Si el texto cabe en un solo chunk, no troceamos
        if len(text) <= size:
            chunk = _make_chunk(unit, text, 0, 0)
            chunks.append(chunk)
            continue

        # Trocear con overlap
        chunk_index = 0
        start = 0

        while start < len(text):
            end = start + size
            chunk_text = text[start:end]

            # Ajustar a límite de palabra (hacia atrás) para no cortar palabras
            if end < len(text):
                last_space = chunk_text.rfind(" ")
                if last_space > 0 and last_space > size * 0.5:
                    end = start + last_space
                    chunk_text = text[start:end]

            chunk = _make_chunk(unit, chunk_text, chunk_index, start)
            chunks.append(chunk)

            chunk_index += 1
            # Avanzar considerando overlap
            next_start = end - overlap
            if next_start <= start:
                next_start = start + 1  # evitar bucle infinito
            start = next_start

    return chunks


def _make_chunk(unit: Dict, text: str, chunk_index: int, char_offset: int) -> Dict:
    """Construye un chunk a partir de una unidad padre."""
    # Hash del texto del chunk para identificación
    chunk_hash = hashlib.md5(text.encode()).hexdigest()[:12]
    parent_id = unit.get("doc_id", "unknown")
    chunk_id = f"{parent_id}_c{chunk_index}_{chunk_hash}"

    return {
        "chunk_id": chunk_id,
        "doc_id": parent_id,
        "source_file": unit.get("source_file", ""),
        "page_start": unit.get("page_start", 0),
        "page_end": unit.get("page_end", 0),
        "family": unit.get("family", ""),
        "indicator_code": unit.get("indicator_code"),
        "indicator_name": unit.get("indicator_name"),
        "block_type": unit.get("block_type", ""),
        "chunk_index": chunk_index,
        "char_offset": char_offset,
        "n_chars": len(text),
        "text": text,
    }


def load_units(path: Path) -> List[Dict]:
    """Carga unidades desde JSONL."""
    units = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                units.append(json.loads(line))
    return units


def save_chunks(chunks: List[Dict], path: Path) -> None:
    """Guarda chunks en JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def compare_chunk_configs(units: List[Dict], configs: List[tuple]) -> Dict:
    """
    Compara múltiples configuraciones de chunking.

    Args:
        units: Lista de unidades documentales.
        configs: Lista de tuplas (size, overlap, label).

    Returns:
        Reporte comparativo con métricas por configuración.
    """
    results = []

    for size, overlap, label in configs:
        chunks = chunk_units(units, size=size, overlap=overlap)

        # Métricas
        total_chunks = len(chunks)
        total_chars = sum(c["n_chars"] for c in chunks)
        avg_len = total_chars / total_chunks if total_chunks > 0 else 0
        max_len = max(c["n_chars"] for c in chunks) if chunks else 0
        min_len = min(c["n_chars"] for c in chunks) if chunks else 0

        # Fragmentación: % de unidades que se trozaron en >1 chunk
        unit_chunk_counts = {}
        for c in chunks:
            unit_chunk_counts[c["doc_id"]] = unit_chunk_counts.get(c["doc_id"], 0) + 1
        fragmented = sum(1 for v in unit_chunk_counts.values() if v > 1)
        fragmentation_pct = (fragmented / len(units) * 100) if units else 0

        # Overlap real promedio entre chunks consecutivos del mismo padre
        overlap_sums = []
        for doc_id, count in unit_chunk_counts.items():
            if count > 1:
                doc_chunks = [c for c in chunks if c["doc_id"] == doc_id]
                doc_chunks.sort(key=lambda c: c["chunk_index"])
                for i in range(1, len(doc_chunks)):
                    prev_text = doc_chunks[i - 1]["text"]
                    curr_text = doc_chunks[i]["text"]
                    # Buscar overlap real (texto compartido al final/inicio)
                    real_ovlp = 0
                    for ovl in range(min(len(prev_text), len(curr_text)), 0, -1):
                        if prev_text[-ovl:] == curr_text[:ovl]:
                            real_ovlp = ovl
                            break
                    overlap_sums.append(real_ovlp)
        avg_real_overlap = sum(overlap_sums) / len(overlap_sums) if overlap_sums else 0

        results.append({
            "label": label,
            "size": size,
            "overlap": overlap,
            "total_chunks": total_chunks,
            "avg_chunk_len": round(avg_len, 1),
            "max_chunk_len": max_len,
            "min_chunk_len": min_len,
            "fragmented_units": fragmented,
            "fragmentation_pct": round(fragmentation_pct, 1),
            "avg_real_overlap": round(avg_real_overlap, 1),
        })

    return {"configs": results, "total_units": len(units)}


if __name__ == "__main__":
    import sys

    # Ejecutar chunking sobre el dataset
    units_path = Path("data/processed/redflags_units.jsonl")
    if not units_path.exists():
        print(f"ERROR: No existe {units_path}", file=sys.stderr)
        sys.exit(1)

    units = load_units(units_path)
    print(f"Unidades cargadas: {len(units)}")

    # Configuraciones comparativas
    configs = [
        (512, 64, "small"),
        (1024, 128, "medium"),
        (2048, 256, "large"),
    ]

    report = compare_chunk_configs(units, configs)

    # Guardar chunks de la configuración recomendada (medium)
    recommended = chunk_units(units, size=1024, overlap=128)
    save_chunks(recommended, Path("data/processed/redflags_chunks.jsonl"))
    print(f"Chunks recomendados (1024/128): {len(recommended)}")

    # Guardar reporte
    report_path = Path("progress/evidence/fase2-chunking-report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReporte guardado en {report_path}")
    print(f"\nComparación de configuraciones:")
    for cfg in report["configs"]:
        print(f"  {cfg['label']}: size={cfg['size']}, overlap={cfg['overlap']} => "
              f"chunks={cfg['total_chunks']}, avg_len={cfg['avg_chunk_len']}, "
              f"fragmented={cfg['fragmented_units']} ({cfg['fragmentation_pct']}%)")