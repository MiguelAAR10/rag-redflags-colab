"use client";

import { useState } from "react";
import type { Dossier, Finding, RejectedFinding } from "@/lib/api";
import {
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  CircleHelp,
  ChevronDown,
  Quote,
  Compass,
  Ban,
  Download,
  Scale,
} from "lucide-react";

const RISK_STYLES: Record<
  string,
  { bar: string; chip: string; icon: typeof ShieldAlert }
> = {
  Alto: {
    bar: "from-flag/25 to-transparent border-flag/50",
    chip: "bg-flag/15 text-flag-soft ring-flag/40",
    icon: ShieldAlert,
  },
  Medio: {
    bar: "from-amber/20 to-transparent border-amber/50",
    chip: "bg-amber/15 text-amber ring-amber/40",
    icon: AlertTriangle,
  },
  Bajo: {
    bar: "from-jade/15 to-transparent border-jade/50",
    chip: "bg-jade/15 text-jade ring-jade/40",
    icon: ShieldCheck,
  },
  "Evidencia insuficiente": {
    bar: "from-slate-risk/15 to-transparent border-slate-risk/50",
    chip: "bg-slate-risk/15 text-slate-risk ring-slate-risk/40",
    icon: CircleHelp,
  },
};

const SEVERITY_CHIP: Record<string, string> = {
  alta: "bg-flag/15 text-flag-soft ring-flag/35",
  media: "bg-amber/15 text-amber ring-amber/35",
  baja: "bg-jade/15 text-jade ring-jade/35",
};

function severityChip(sev: string) {
  return (
    SEVERITY_CHIP[sev?.toLowerCase()] ??
    "bg-slate-risk/15 text-slate-risk ring-slate-risk/35"
  );
}

function FindingCard({ f, index }: { f: Finding; index: number }) {
  return (
    <article className="rounded-2xl border border-line bg-surface p-5 transition hover:border-flag/35">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h4 className="text-[15px] font-semibold leading-snug">
          <span className="mr-2 font-mono text-[13px] text-faint">
            {String(index + 1).padStart(2, "0")}
          </span>
          {f.title}
        </h4>
        <span
          className={`rounded-full px-2.5 py-1 text-[12px] font-medium capitalize ring-1 ${severityChip(
            f.severity
          )}`}
        >
          severidad {f.severity || "—"}
        </span>
      </div>

      {f.evidence_quote && (
        <blockquote className="mt-4 flex gap-2.5 rounded-xl border border-line bg-ink/60 p-4">
          <Quote className="mt-0.5 size-4 shrink-0 text-flag-soft" />
          <p className="text-sm leading-relaxed text-fg/90">
            {f.evidence_quote}
          </p>
        </blockquote>
      )}

      {f.explanation && (
        <p className="mt-3 text-sm leading-relaxed text-muted">
          <span className="font-medium text-fg/80">Por qué importa: </span>
          {f.explanation}
        </p>
      )}

      {f.citation && (
        <p className="mt-3 font-mono text-[12px] text-faint">📎 {f.citation}</p>
      )}
    </article>
  );
}

function RejectedList({ items }: { items: RejectedFinding[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-2xl border border-line bg-surface">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-5 py-4 text-left"
      >
        <span className="inline-flex items-center gap-2.5 text-sm font-medium">
          <Ban className="size-4 text-slate-risk" />
          Señales rechazadas por el crítico de evidencia ({items.length})
        </span>
        <ChevronDown
          className={`size-4 text-muted transition ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <div className="space-y-3 border-t border-line px-5 py-4">
          <p className="text-[13px] text-faint">
            El EvidenceCritic descarta toda señal sin cita literal del
            documento — el gate anti-alucinación visible del sistema.
          </p>
          {items.map((r, i) => (
            <div
              key={i}
              className="rounded-xl border border-line/70 bg-ink/50 p-4"
            >
              <p className="text-sm font-medium text-fg/80">{r.title}</p>
              <p className="mt-1 text-[13px] text-muted">
                Motivo del rechazo: {r.rejection_reason}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function DossierView({ dossier }: { dossier: Dossier }) {
  const style =
    RISK_STYLES[dossier.risk_level] ?? RISK_STYLES["Evidencia insuficiente"];
  const RiskIcon = style.icon;
  const ev = dossier.evidence ?? { accepted_count: 0, rejected_count: 0 };
  const findings = dossier.findings ?? [];
  const rejected = dossier.rejected_findings ?? [];

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(dossier, null, 2)], {
      type: "application/json",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "dossier-tdr.json";
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <div className="space-y-5">
      {/* Banner de riesgo */}
      <div
        className={`rounded-2xl border bg-gradient-to-r p-6 ${style.bar}`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <span
              className={`grid size-12 place-items-center rounded-xl ring-1 ${style.chip}`}
            >
              <RiskIcon className="size-6" strokeWidth={1.9} />
            </span>
            <div>
              <p className="text-[12px] uppercase tracking-widest text-muted">
                Riesgo preliminar
              </p>
              <p className="font-display text-3xl font-bold leading-none">
                {dossier.risk_level || "—"}
              </p>
            </div>
          </div>
          <button
            onClick={downloadJson}
            className="inline-flex items-center gap-2 rounded-lg border border-line bg-surface px-3.5 py-2 text-[13px] text-muted transition hover:text-fg"
          >
            <Download className="size-3.5" /> Dossier JSON
          </button>
        </div>
        {dossier.risk_reason && (
          <p className="mt-4 max-w-3xl text-sm leading-relaxed text-muted">
            {dossier.risk_reason}
          </p>
        )}
      </div>

      {/* Métricas */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          {
            label: "Grounding",
            value: (dossier.grounding_ratio ?? 0).toFixed(2),
          },
          { label: "Señales aceptadas", value: String(ev.accepted_count ?? 0) },
          { label: "Señales rechazadas", value: String(ev.rejected_count ?? 0) },
          {
            label: "Evidencia",
            value: (ev.status ?? "—").replace(/^./, (c) => c.toUpperCase()),
          },
        ].map((m) => (
          <div
            key={m.label}
            className="rounded-2xl border border-line bg-surface p-4"
          >
            <p className="text-[12px] text-muted">{m.label}</p>
            <p className="mt-1 font-display text-2xl font-bold">{m.value}</p>
          </div>
        ))}
      </div>

      {dossier.refusal && (
        <div className="flex items-start gap-3 rounded-2xl border border-slate-risk/40 bg-slate-risk/10 p-5">
          <ShieldCheck className="mt-0.5 size-5 shrink-0 text-slate-risk" />
          <div>
            <p className="text-sm font-semibold">Abstención segura del sistema</p>
            <p className="mt-1 text-sm leading-relaxed text-muted">
              {dossier.refusal}
            </p>
          </div>
        </div>
      )}

      {dossier.summary && (
        <p className="rounded-2xl border border-line bg-surface p-5 text-sm leading-relaxed text-fg/90">
          <span className="font-semibold">Resumen: </span>
          {dossier.summary}
        </p>
      )}

      {findings.length > 0 && (
        <section className="space-y-3">
          <h3 className="flex items-center gap-2 pt-2 text-lg font-semibold">
            <AlertTriangle className="size-5 text-flag-soft" />
            Señales de riesgo con evidencia ({findings.length})
          </h3>
          {findings.map((f, i) => (
            <FindingCard key={i} f={f} index={i} />
          ))}
        </section>
      )}

      {rejected.length > 0 && <RejectedList items={rejected} />}

      {(dossier.uncertainty?.length ?? 0) > 0 && (
        <div className="rounded-2xl border border-line bg-surface p-5">
          <h4 className="flex items-center gap-2 text-sm font-semibold">
            <CircleHelp className="size-4 text-amber" /> Incertidumbre declarada
          </h4>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-muted">
            {dossier.uncertainty!.map((u, i) => (
              <li key={i}>{u}</li>
            ))}
          </ul>
        </div>
      )}

      {(dossier.next_steps?.length ?? 0) > 0 && (
        <div className="rounded-2xl border border-line bg-surface p-5">
          <h4 className="flex items-center gap-2 text-sm font-semibold">
            <Compass className="size-4 text-jade" /> Próximos pasos sugeridos
          </h4>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-muted">
            {dossier.next_steps!.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {dossier.disclaimer && (
        <p className="flex items-start gap-2.5 border-t border-line pt-5 text-[12.5px] leading-relaxed text-faint">
          <Scale className="mt-0.5 size-4 shrink-0" />
          {dossier.disclaimer}
        </p>
      )}
    </div>
  );
}
