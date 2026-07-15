"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  uploadTdr,
  analyzeTdr,
  getDossier,
  type Dossier,
  type UploadResult,
} from "@/lib/api";
import { DossierView } from "@/components/DossierView";
import {
  UploadCloud,
  FileText,
  Type,
  X,
  Loader2,
  CheckCircle2,
  Circle,
  AlertCircle,
  RotateCcw,
} from "lucide-react";

const ACCEPTED = [".pdf", ".docx", ".txt", ".md"];
const MAX_MB = 20;
const MIN_TEXT = 200;

type Phase = "idle" | "uploading" | "analyzing" | "done" | "error";

const ANALYSIS_STEPS = [
  "Extracción de texto y chunking",
  "Recuperación de criterios OCP 2024 (Qdrant)",
  "Generación de señales con Gemini 2.5 Flash",
  "Verificación de grounding por frase",
  "Crítico de evidencia (citas literales)",
];

function AnalysisProgress({ uploaded }: { uploaded: UploadResult | null }) {
  const [step, setStep] = useState(0);
  useEffect(() => {
    // El backend es síncrono: animamos pasos estimados mientras responde.
    const timer = setInterval(
      () => setStep((s) => Math.min(s + 1, ANALYSIS_STEPS.length - 1)),
      7000
    );
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="rounded-2xl border border-line bg-surface p-6">
      {uploaded && (
        <p className="mb-5 font-mono text-[12.5px] text-faint">
          TDR #{uploaded.tdr_id} · {uploaded.char_count.toLocaleString("es")}{" "}
          caracteres · {uploaded.reindex?.chunks_total ?? 0} chunks · sha{" "}
          {uploaded.sha256.slice(0, 12)}…
        </p>
      )}
      <ul className="space-y-3.5">
        {ANALYSIS_STEPS.map((label, i) => (
          <li key={label} className="flex items-center gap-3 text-sm">
            {i < step ? (
              <CheckCircle2 className="size-4.5 shrink-0 text-jade" />
            ) : i === step ? (
              <Loader2 className="size-4.5 shrink-0 animate-spin text-flag-soft" />
            ) : (
              <Circle className="size-4.5 shrink-0 text-faint" />
            )}
            <span className={i <= step ? "text-fg" : "text-faint"}>{label}</span>
          </li>
        ))}
      </ul>
      <div className="shimmer mt-6 h-1.5 rounded-full" />
      <p className="mt-4 text-[13px] text-muted">
        El análisis completo suele tardar entre 20 y 60 segundos.
      </p>
    </div>
  );
}

export default function AnalizarPage() {
  const [mode, setMode] = useState<"file" | "text">("file");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [dragging, setDragging] = useState(false);
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState("");
  const [uploaded, setUploaded] = useState<UploadResult | null>(null);
  const [dossier, setDossier] = useState<Dossier | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  const pickFile = (f: File | undefined | null) => {
    if (!f) return;
    const ext = "." + (f.name.split(".").pop() ?? "").toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setError(`Formato no soportado (${ext}). Usa ${ACCEPTED.join(", ")}.`);
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setError(`El archivo supera ${MAX_MB} MB.`);
      return;
    }
    setError("");
    setFile(f);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    pickFile(e.dataTransfer.files?.[0]);
  }, []);

  const canSubmit =
    phase === "idle" || phase === "error"
      ? mode === "file"
        ? !!file
        : text.trim().length >= MIN_TEXT
      : false;

  const run = async () => {
    setError("");
    setDossier(null);
    try {
      setPhase("uploading");
      const up = await uploadTdr(
        mode === "file" ? { file: file! } : { pastedText: text.trim() }
      );
      setUploaded(up);
      setPhase("analyzing");
      await analyzeTdr(up.tdr_id);
      const d = await getDossier(up.tdr_id);
      setDossier(d);
      setPhase("done");
      setTimeout(
        () => resultRef.current?.scrollIntoView({ behavior: "smooth" }),
        80
      );
    } catch (e) {
      setPhase("error");
      setError(e instanceof Error ? e.message : "Error inesperado.");
    }
  };

  const reset = () => {
    setPhase("idle");
    setFile(null);
    setText("");
    setUploaded(null);
    setDossier(null);
    setError("");
  };

  const busy = phase === "uploading" || phase === "analyzing";

  return (
    <div className="mx-auto max-w-4xl px-5 py-14">
      <h1 className="font-display text-4xl font-semibold tracking-tight sm:text-5xl">
        Auditar un documento
      </h1>
      <p className="mt-3 max-w-2xl text-muted">
        Sube el TDR, contrato o licitación — o pega un extracto — y el sistema
        lo contrastará con la guía OCP 2024 de red flags.
      </p>

      {/* Selector de modo */}
      {!busy && phase !== "done" && (
        <div className="mt-8">
          <div className="inline-flex rounded-xl border border-line bg-surface p-1">
            {(
              [
                { key: "file", label: "Subir archivo", icon: FileText },
                { key: "text", label: "Pegar texto", icon: Type },
              ] as const
            ).map((t) => (
              <button
                key={t.key}
                onClick={() => setMode(t.key)}
                className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm transition ${
                  mode === t.key
                    ? "bg-surface-2 text-fg shadow-sm"
                    : "text-muted hover:text-fg"
                }`}
              >
                <t.icon className="size-4" />
                {t.label}
              </button>
            ))}
          </div>

          {mode === "file" ? (
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => inputRef.current?.click()}
              className={`mt-4 grid cursor-pointer place-items-center rounded-2xl border-2 border-dashed px-6 py-16 text-center transition ${
                dragging
                  ? "border-flag bg-flag/10"
                  : "border-line bg-surface hover:border-flag/50 hover:bg-surface-2"
              }`}
            >
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPTED.join(",")}
                className="hidden"
                onChange={(e) => pickFile(e.target.files?.[0])}
              />
              {file ? (
                <div className="flex items-center gap-3">
                  <FileText className="size-8 text-flag-soft" />
                  <div className="text-left">
                    <p className="font-medium">{file.name}</p>
                    <p className="text-[13px] text-muted">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                    }}
                    className="ml-2 rounded-lg border border-line p-1.5 text-muted hover:text-fg"
                    aria-label="Quitar archivo"
                  >
                    <X className="size-4" />
                  </button>
                </div>
              ) : (
                <>
                  <UploadCloud className="size-10 text-muted" strokeWidth={1.5} />
                  <p className="mt-4 font-medium">
                    Arrastra el documento aquí o haz clic para elegirlo
                  </p>
                  <p className="mt-1.5 text-[13px] text-muted">
                    PDF, DOCX, TXT o MD · máximo {MAX_MB} MB
                  </p>
                </>
              )}
            </div>
          ) : (
            <div className="mt-4">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={10}
                placeholder="Ej.: Contrato de obra pública por 5M USD adjudicado a un solo oferente, con 3 días entre publicación y apertura de ofertas…"
                className="w-full resize-y rounded-2xl border border-line bg-surface p-5 text-sm leading-relaxed outline-none transition placeholder:text-faint focus:border-flag/60"
              />
              <p
                className={`mt-2 text-right text-[12.5px] ${
                  text.trim().length >= MIN_TEXT ? "text-jade" : "text-faint"
                }`}
              >
                {text.trim().length.toLocaleString("es")} / mín. {MIN_TEXT}{" "}
                caracteres
              </p>
            </div>
          )}

          {error && phase !== "error" && (
            <p className="mt-3 flex items-center gap-2 text-sm text-flag-soft">
              <AlertCircle className="size-4" /> {error}
            </p>
          )}

          <button
            onClick={run}
            disabled={!canSubmit}
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-flag px-7 py-3.5 text-[15px] font-semibold text-white transition enabled:hover:bg-flag-deep disabled:cursor-not-allowed disabled:opacity-40"
          >
            Analizar con el RAG
          </button>
        </div>
      )}

      {/* Progreso */}
      {busy && (
        <div className="mt-8">
          <AnalysisProgress uploaded={uploaded} />
        </div>
      )}

      {/* Error */}
      {phase === "error" && (
        <div className="mt-8 rounded-2xl border border-flag/40 bg-flag/10 p-5">
          <p className="flex items-center gap-2 font-medium text-flag-soft">
            <AlertCircle className="size-5" /> El análisis no se completó
          </p>
          <p className="mt-2 text-sm text-muted">{error}</p>
          <button
            onClick={run}
            disabled={!canSubmit}
            className="mt-4 inline-flex items-center gap-2 rounded-lg border border-line bg-surface px-4 py-2 text-sm transition hover:bg-surface-2"
          >
            <RotateCcw className="size-4" /> Reintentar
          </button>
        </div>
      )}

      {/* Resultado */}
      {phase === "done" && dossier && (
        <div ref={resultRef} className="mt-10">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              Dossier — TDR #{uploaded?.tdr_id}
            </h2>
            <button
              onClick={reset}
              className="inline-flex items-center gap-2 rounded-lg border border-line bg-surface px-4 py-2 text-sm text-muted transition hover:text-fg"
            >
              <RotateCcw className="size-4" /> Analizar otro documento
            </button>
          </div>
          <DossierView dossier={dossier} />
        </div>
      )}
    </div>
  );
}
