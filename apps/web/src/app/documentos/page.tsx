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
} from "lucide-react";

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
        Documentos analizados
      </h1>
      <p className="mt-3 text-muted">
        Historial de TDRs auditados en esta instancia. La metadata es efímera
        entre despliegues (limitación declarada de la demo).
      </p>

      <div className="mt-9 space-y-3">
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
              Auditar un TDR
            </Link>
          </div>
        )}
        {tdrs?.map((t) => (
          <TdrRow key={t.id} tdr={t} />
        ))}
      </div>
    </div>
  );
}
