"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  listTdrs,
  getDossier,
  analyzeTdr,
  type TdrSummary,
  type Dossier,
} from "@/lib/api";
import { DossierView } from "@/components/DossierView";
import {
  FileText,
  Loader2,
  ChevronDown,
  Inbox,
  AlertCircle,
  Play,
  Download,
} from "lucide-react";

type DemoDocument = {
  filename: string;
  title: string;
  source: string;
  description: string;
};

const DEMO_PDF_BASE =
  "https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples";

const DEMO_DOCUMENTS = [
  {
    filename: "tdr-tce-01626-2023-essalud-comite-nulo.pdf",
    title: "EsSalud: conformación del comité",
    source: "Tribunal de Contrataciones del Estado · Resolución 01626-2023",
    description:
      "Fuente pública con un hallazgo oficial documentado sobre la conformación del comité de selección.",
  },
  {
    filename:
      "tdr-tce-00132-2022-hospital-lambayeque-registro-sanitario.pdf",
    title: "Hospital Lambayeque: registro sanitario",
    source: "Tribunal de Contrataciones del Estado · Resolución 00132-2022",
    description:
      "Fuente pública para revisar requisitos de registro sanitario consignados en el procedimiento.",
  },
  {
    filename: "tdr-tce-04185-2022-fospeme-certificado-incumplido.pdf",
    title: "Fospeme: certificado presentado",
    source: "Tribunal de Contrataciones del Estado · Resolución 04185-2022",
    description:
      "Fuente pública con un hallazgo oficial documentado sobre la evaluación de un certificado.",
  },
  {
    filename: "tdr-contraloria-bid-seguimiento-contractual.pdf",
    title: "Seguimiento contractual BID",
    source: "Contraloría General de la República",
    description:
      "Documento público para explorar señales vinculadas al seguimiento de la ejecución contractual.",
  },
  {
    filename: "tdr-predes-zona-segura-los-olivos.pdf",
    title: "Zona Segura Los Olivos",
    source: "PREDES",
    description:
      "Documento público de demostración para revisar condiciones y alcance de una contratación.",
  },
  {
    filename: "tdr-pronied-infraestructura-educativa.pdf",
    title: "Infraestructura educativa PRONIED",
    source: "PRONIED",
    description:
      "Documento público de demostración para revisar requisitos de infraestructura educativa.",
  },
] satisfies readonly DemoDocument[];

const RISK_DOT: Record<string, string> = {
  Alto: "bg-flag",
  Medio: "bg-amber",
  Bajo: "bg-jade",
};

function TdrRow({ tdr }: { tdr: TdrSummary }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [dossier, setDossier] = useState<Dossier | null>(null);
  const [error, setError] = useState("");

  const load = async () => {
    if (open) {
      setOpen(false);
      return;
    }
    setOpen(true);
    if (dossier) return;
    setLoading(true);
    setError("");
    try {
      setDossier(await getDossier(tdr.id));
    } catch {
      setError("Este documento aún no tiene un dossier completado.");
    } finally {
      setLoading(false);
    }
  };

  const analyze = async () => {
    setLoading(true);
    setError("");
    try {
      await analyzeTdr(tdr.id);
      setDossier(await getDossier(tdr.id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo analizar.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-surface">
      <button
        onClick={load}
        className="flex w-full items-center gap-4 px-5 py-4 text-left transition hover:bg-surface-2"
      >
        <FileText className="size-5 shrink-0 text-muted" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{tdr.filename}</p>
          <p className="mt-0.5 font-mono text-[12px] text-faint">
            TDR #{tdr.id} · {tdr.latest_run_status ?? "sin análisis"}
          </p>
        </div>
        <span className="inline-flex items-center gap-2 text-[13px] text-muted">
          <span
            className={`size-2 rounded-full ${
              RISK_DOT[tdr.risk_level ?? ""] ?? "bg-slate-risk"
            }`}
          />
          {tdr.risk_level ?? "—"}
        </span>
        <ChevronDown
          className={`size-4 text-muted transition ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="border-t border-line p-5">
          {loading ? (
            <p className="flex items-center gap-2 text-sm text-muted">
              <Loader2 className="size-4 animate-spin" /> Cargando dossier…
            </p>
          ) : dossier ? (
            <DossierView dossier={dossier} />
          ) : (
            <div className="text-sm text-muted">
              <p className="flex items-center gap-2">
                <AlertCircle className="size-4 text-amber" /> {error}
              </p>
              <button
                onClick={analyze}
                className="mt-3 inline-flex items-center gap-2 rounded-lg border border-line bg-surface-2 px-4 py-2 text-sm text-fg transition hover:border-flag/40"
              >
                <Play className="size-4" /> Ejecutar análisis ahora
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function DocumentosPage() {
  const [tdrs, setTdrs] = useState<TdrSummary[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    listTdrs()
      .then(setTdrs)
      .catch((e) =>
        setError(e instanceof Error ? e.message : "No se pudo conectar al API.")
      );
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-5 py-14">
      <h1 className="font-display text-4xl font-semibold tracking-tight sm:text-5xl">
        Documentos de demostración
      </h1>
      <p className="mt-3 text-muted">
        Descarga uno de los casos públicos para conocer el tipo de documento
        que puede procesar la aplicación.
      </p>

      <p className="mt-6 rounded-2xl border border-amber/40 bg-amber/10 p-4 text-sm leading-relaxed text-fg">
        {"Estas son fuentes públicas de demostración para revisar señales de riesgo potenciales. "}
        Todo resultado requiere revisión humana.
      </p>

      <section className="mt-8 grid gap-4 sm:grid-cols-2">
        {DEMO_DOCUMENTS.map((document) => (
          <article
            key={document.filename}
            className="flex flex-col rounded-2xl border border-line bg-surface p-5"
          >
            <p className="font-mono text-[11px] leading-relaxed text-faint">
              {document.filename}
            </p>
            <h2 className="mt-3 font-display text-xl font-semibold">
              {document.title}
            </h2>
            <p className="mt-1 text-xs font-medium uppercase tracking-wide text-flag-soft">
              {document.source}
            </p>
            <p className="mt-3 flex-1 text-sm leading-relaxed text-muted">
              {document.description}
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <a
                href={`${DEMO_PDF_BASE}/${document.filename}`}
                aria-label={`Descargar PDF: ${document.title}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-lg border border-line bg-surface-2 px-3.5 py-2 text-sm font-medium text-fg transition hover:border-flag/40"
              >
                <Download className="size-4" /> Descargar PDF
              </a>
              <Link
                href="/analizar"
                aria-label={`Analizar documento: ${document.title}`}
                className="inline-flex items-center rounded-lg bg-flag px-3.5 py-2 text-sm font-semibold text-white transition hover:bg-flag-deep"
              >
                Analizar un documento
              </Link>
            </div>
          </article>
        ))}
      </section>

      <section className="mt-14">
        <h2 className="font-display text-2xl font-semibold tracking-tight">
          Historial de documentos revisados
        </h2>
        <p className="mt-2 text-sm text-muted">
          La metadata de esta instancia es efímera entre despliegues
          (limitación declarada de la demo).
        </p>

        <div className="mt-6 space-y-3">
          {error && (
            <p className="flex items-center gap-2 rounded-2xl border border-flag/40 bg-flag/10 p-4 text-sm text-flag-soft">
              <AlertCircle className="size-4" /> {error}
            </p>
          )}
          {!error && tdrs === null && (
            <p className="flex items-center gap-2 text-sm text-muted">
              <Loader2 className="size-4 animate-spin" /> Cargando documentos…
            </p>
          )}
          {tdrs?.length === 0 && (
            <div className="grid place-items-center rounded-2xl border border-dashed border-line bg-surface px-6 py-16 text-center">
              <Inbox className="size-9 text-muted" strokeWidth={1.5} />
              <p className="mt-4 font-medium">Aún no hay documentos</p>
              <p className="mt-1 text-sm text-muted">
                Sube el primero desde la página de análisis.
              </p>
              <Link
                href="/analizar"
                className="mt-5 rounded-lg bg-flag px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-flag-deep"
              >
                Analizar un documento
              </Link>
            </div>
          )}
          {tdrs?.map((t) => (
            <TdrRow key={t.id} tdr={t} />
          ))}
        </div>
      </section>
    </div>
  );
}
