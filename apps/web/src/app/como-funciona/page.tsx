import type { Metadata } from "next";
import {
  FileInput,
  Database,
  Braces,
  Sparkles,
  ShieldCheck,
  Ban,
  GitCompareArrows,
  OctagonPause,
  TriangleAlert,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Cómo funciona — TDR Risk Auditor",
};

const STAGES = [
  {
    icon: FileInput,
    title: "Ingesta multi-formato",
    body: "PDF (PyMuPDF), DOCX (python-docx), TXT y Markdown. El texto se normaliza, se trocea en chunks y cada chunk recibe un hash de contenido.",
  },
  {
    icon: Database,
    title: "Base de conocimiento",
    body: "La guía OCP 2024 Red Flags in Public Procurement, segmentada en 299 chunks con metadata, vive en Qdrant Cloud (colección standard_kb). Los documentos del usuario se indexan aparte (subject_docs).",
  },
  {
    icon: Braces,
    title: "Embeddings",
    body: "gemini-embedding-001 a 768 dimensiones, tanto para el corpus como para las consultas. Misma geometría, comparación honesta.",
  },
  {
    icon: Sparkles,
    title: "Generación",
    body: "Gemini 2.5 Flash vía Vertex AI redacta las señales de riesgo candidatas usando exclusivamente los criterios recuperados y el texto del documento.",
  },
  {
    icon: ShieldCheck,
    title: "Verificación de grounding",
    body: "Cada frase de la respuesta se contrasta semánticamente contra las fuentes (multilingüe). El ratio de grounding se reporta en el dossier: 1.00 significa que todo lo afirmado está respaldado.",
  },
  {
    icon: Ban,
    title: "Crítico de evidencia",
    body: "El EvidenceCritic exige una cita literal del documento para cada señal. Las que no la tienen se rechazan y se muestran con su motivo — el gate anti-alucinación es visible, no un secreto.",
  },
  {
    icon: GitCompareArrows,
    title: "Reindexación inteligente",
    body: "Al subir una versión nueva (adenda, corrección), se hace diff por hash de chunk: solo lo modificado se re-embebe. Contenido idéntico = no-op.",
  },
  {
    icon: OctagonPause,
    title: "Abstención segura",
    body: "Taxonomía estructurada de rechazo: documento fuera de dominio o evidencia insuficiente. El sistema prefiere abstenerse antes que especular.",
  },
];

const LIMITS = [
  "La metadata (historial de documentos) usa SQLite efímero: se pierde al desplegar una nueva revisión del backend. Los embeddings en Qdrant sí persisten.",
  "El dossier señala riesgos potenciales según la guía OCP; no reemplaza un peritaje legal ni una auditoría formal.",
  "El análisis es síncrono y suele tardar 20–60 segundos por documento.",
];

export default function ComoFuncionaPage() {
  return (
    <div className="mx-auto max-w-4xl px-5 py-14">
      <h1 className="font-display text-4xl font-semibold tracking-tight sm:text-5xl">
        Cómo funciona
      </h1>
      <p className="mt-3 max-w-2xl leading-relaxed text-muted">
        Un pipeline RAG agéntico donde cada etapa existe para acotar la
        alucinación. Esta es la arquitectura real desplegada, sin adornos.
      </p>

      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        {STAGES.map((s) => (
          <div
            key={s.title}
            className="rounded-2xl border border-line bg-surface p-5 transition hover:border-flag/35"
          >
            <span className="grid size-9 place-items-center rounded-lg bg-flag/10 ring-1 ring-flag/25">
              <s.icon className="size-4.5 text-flag-soft" strokeWidth={1.9} />
            </span>
            <h3 className="mt-4 text-[15px] font-semibold">{s.title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-muted">{s.body}</p>
          </div>
        ))}
      </div>

      <div className="mt-12 rounded-2xl border border-amber/35 bg-amber/8 p-6">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <TriangleAlert className="size-5 text-amber" />
          Limitaciones declaradas
        </h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-relaxed text-muted">
          {LIMITS.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
