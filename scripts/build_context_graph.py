#!/usr/bin/env python3
"""
build_context_graph.py — Grafo determinista de la documentación/harness.

Escanea los archivos de conocimiento del repo (docs, specs, progress, agentes,
tasks, código) y genera:
  - progress/context-graph.json : nodos (archivos) + aristas (referencias).
    Lo lee CUALQUIER CLI (Claude/Codex/OpenCode) para navegar sin cargar todo.
  - docs/CONTEXT_GRAPH.md        : diagrama Mermaid + tabla para humanos.

Sin dependencias externas (solo stdlib). "Si no está en un archivo, no existe":
este grafo ES un archivo, no memoria del modelo.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Carpetas/archivos que forman la "memoria" del proyecto.
INCLUDE_GLOBS = [
    "AGENTS.md", "CLAUDE.md", "README.md",
    "docs/*.md", "specs/*.md", "progress/*.md",
    ".claude/agents/*.md", ".opencode/agent/*.md",
    ".codex/skills/*/SKILL.md",
    "tasks/*.json",
    "packages/**/*.py", "apps/**/*.py",
]

KIND_BY_PREFIX = [
    ("docs/", "doc"), ("specs/", "spec"), ("progress/runs/", "run"),
    ("progress/reviews/", "review"), ("progress/", "state"),
    (".claude/agents/", "agent"), (".opencode/agent/", "agent"),
    (".codex/skills/", "skill"), ("tasks/", "task"),
    ("packages/", "code"), ("apps/", "code"),
]


def kind_of(rel: str) -> str:
    for prefix, kind in KIND_BY_PREFIX:
        if rel.startswith(prefix):
            return kind
    return "root"


def title_of(path: Path, rel: str) -> str:
    if path.suffix == ".md":
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if s.startswith("# "):
                return s[2:].strip()
    return rel


def collect_files() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for pattern in INCLUDE_GLOBS:
        for p in sorted(ROOT.glob(pattern)):
            if p.is_file() and p not in seen:
                seen.add(p)
                out.append(p)
    return out


def main() -> int:
    files = collect_files()
    rels = [str(p.relative_to(ROOT)) for p in files]
    relset = set(rels)
    basenames = {Path(r).name: r for r in rels}

    nodes = []
    for p, rel in zip(files, rels):
        text = p.read_text(encoding="utf-8", errors="ignore")
        nodes.append({
            "id": rel,
            "title": title_of(p, rel),
            "kind": kind_of(rel),
            "lines": text.count("\n") + 1,
        })

    # Aristas: una arista A->B si el texto de A referencia la ruta o el nombre de B.
    edges = []
    wikilink = re.compile(r"\[\[([^\]]+)\]\]")
    for p, rel in zip(files, rels):
        text = p.read_text(encoding="utf-8", errors="ignore")
        targets: set[str] = set()
        for other in relset:
            if other == rel:
                continue
            if other in text:                       # ruta relativa explícita
                targets.add(other)
        for m in wikilink.findall(text):            # [[wikilink]] por nombre
            cand = m.strip()
            if cand in relset:
                targets.add(cand)
            elif cand in basenames:
                targets.add(basenames[cand])
        for t in sorted(targets):
            edges.append({"from": rel, "to": t})

    # Huérfanos: sin aristas entrantes ni salientes.
    linked = {e["from"] for e in edges} | {e["to"] for e in edges}
    orphans = sorted(r for r in rels if r not in linked)

    graph = {
        "generated_by": "scripts/build_context_graph.py",
        "note": "Grafo determinista del harness. Regenerar tras cambios: bash scripts/build-context-graph.sh",
        "counts": {"nodes": len(nodes), "edges": len(edges), "orphans": len(orphans)},
        "nodes": nodes,
        "edges": edges,
        "orphans": orphans,
    }

    out_json = ROOT / "progress" / "context-graph.json"
    out_json.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Mermaid para humanos.
    def nid(r: str) -> str:
        return "n_" + re.sub(r"[^a-zA-Z0-9]", "_", r)

    lines = ["# CONTEXT_GRAPH (generado)", "",
             "> Generado por `scripts/build_context_graph.py`. **No editar a mano.**",
             f"> Nodos: {len(nodes)} · Aristas: {len(edges)} · Huérfanos: {len(orphans)}",
             "> Regenerar: `bash scripts/build-context-graph.sh`", "",
             "```mermaid", "graph LR"]
    for n in nodes:
        lines.append(f'  {nid(n["id"])}["{n["id"]}"]')
    for e in edges:
        lines.append(f'  {nid(e["from"])} --> {nid(e["to"])}')
    lines.append("```")
    if orphans:
        lines += ["", "## Huérfanos (sin referencias entrantes/salientes)", ""]
        lines += [f"- `{o}`" for o in orphans]
    (ROOT / "docs" / "CONTEXT_GRAPH.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"context-graph: {len(nodes)} nodos, {len(edges)} aristas, {len(orphans)} huérfanos")
    print(f"  -> progress/context-graph.json")
    print(f"  -> docs/CONTEXT_GRAPH.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
