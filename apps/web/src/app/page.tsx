import Link from "next/link";
import Image from "next/image";
import { ArrowRight, BadgeCheck } from "lucide-react";

const STATS = [
  { value: "299", label: "criterios OCP 2024 indexados" },
  { value: "1.00", label: "grounding en el E2E de cierre" },
  { value: "100%", label: "señales con cita literal exigida" },
  { value: "2", label: "vías de abstención segura" },
];

const STEPS = [
  {
    n: "01",
    title: "Sube el documento",
    body: "PDF, DOCX, TXT o Markdown — o pega un extracto del TDR, contrato o licitación. El texto se extrae, se trocea y se indexa con diff por hash: solo lo nuevo se re-embebe.",
  },
  {
    n: "02",
    title: "El RAG contrasta con la guía OCP",
    body: "Cada fragmento se compara contra los 299 criterios de la guía OCP 2024 Red Flags en Qdrant Cloud, y Gemini 2.5 Flash redacta las señales de riesgo candidatas.",
  },
  {
    n: "03",
    title: "Un crítico verifica la evidencia",
    body: "El EvidenceCritic rechaza toda señal sin cita literal del documento y el grounding se mide frase a frase. Lo que no se sostiene, se descarta y se muestra por qué.",
  },
];

const PIPELINE = [
  { stage: "Ingesta multi-formato", tech: "PyMuPDF · python-docx · TXT/MD" },
  { stage: "Base de conocimiento", tech: "Guía OCP 2024 Red Flags — Qdrant Cloud" },
  { stage: "Embeddings", tech: "gemini-embedding-001 (768d)" },
  { stage: "Generación", tech: "Gemini 2.5 Flash · Vertex AI" },
  { stage: "Verificación", tech: "Grounding semántico por frase + citas" },
  { stage: "Anti-alucinación", tech: "EvidenceCritic: sin cita literal, no hay señal" },
];

export default function Home() {
  return (
    <div>
      {/* Hero */}
      <section className="hero-glow relative overflow-hidden border-b border-line">
        <div className="grid-bg pointer-events-none absolute inset-0" />
        <Image
          src="/uni-escudo-negro.png"
          alt=""
          width={520}
          height={689}
          priority
          className="pointer-events-none absolute -right-16 -top-10 hidden w-[26rem] opacity-[0.045] lg:block"
        />
        <div className="relative mx-auto max-w-6xl px-5 pb-24 pt-24 sm:pt-32">
          <p className="rise flex items-center gap-3 text-[13px] text-muted">
            <Image
              src="/uni-escudo-guinda.png"
              alt="Escudo de la Universidad Nacional de Ingeniería"
              width={30}
              height={40}
              className="h-10 w-auto"
            />
            <span className="font-medium leading-tight">Proyecto UNI</span>
          </p>

          <h1 className="rise rise-1 mt-10 max-w-3xl font-display text-5xl font-semibold leading-[1.04] tracking-tight sm:text-7xl">
            Lee el contrato como lo leería{" "}
            <span className="text-flag">un auditor</span>.
          </h1>

          <p className="rise rise-2 mt-6 max-w-2xl text-lg leading-relaxed text-muted">
            Sube un TDR, contrato o licitación — en PDF o como texto — y recibe
            un dossier con señales de riesgo potenciales, cada una con su cita
            literal, su criterio OCP de respaldo y su nivel de severidad.
            Sin evidencia, no hay señal.
          </p>

          <div className="rise rise-3 mt-10 flex flex-wrap items-center gap-5">
            <Link
              href="/analizar"
              className="inline-flex items-center gap-2 rounded-lg bg-flag px-6 py-3.5 text-[15px] font-semibold text-white transition hover:bg-flag-deep"
            >
              Auditar un documento
              <ArrowRight className="size-4" />
            </Link>
            <Link
              href="/como-funciona"
              className="group inline-flex items-center gap-1.5 text-[15px] font-medium text-fg transition hover:text-flag"
            >
              Ver la arquitectura
              <ArrowRight className="size-4 transition group-hover:translate-x-0.5" />
            </Link>
          </div>

          {/* Stats — hairlines, sin cajas */}
          <div className="rise rise-3 mt-20 grid grid-cols-2 gap-y-10 border-t border-line pt-8 sm:grid-cols-4">
            {STATS.map((s, i) => (
              <div
                key={s.label}
                className={`pr-6 ${i > 0 ? "sm:border-l sm:border-line sm:pl-6" : ""}`}
              >
                <div className="font-display text-4xl font-bold text-flag">{s.value}</div>
                <div className="mt-1.5 text-[13px] leading-snug text-muted">
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pasos */}
      <section className="mx-auto max-w-6xl px-5 py-24">
        <h2 className="max-w-xl font-display text-3xl font-semibold tracking-tight sm:text-4xl">
          Del documento al dossier, con evidencia
        </h2>
        <div className="mt-14 grid gap-12 md:grid-cols-3 md:gap-8">
          {STEPS.map((s) => (
            <div key={s.n} className="border-t-2 border-flag/80 pt-6">
              <span className="font-mono text-[13px] font-medium text-flag">
                {s.n}
              </span>
              <h3 className="mt-3 text-[17px] font-semibold tracking-tight">
                {s.title}
              </h3>
              <p className="mt-2.5 text-[15px] leading-relaxed text-muted">
                {s.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Pipeline */}
      <section className="border-y border-line bg-surface">
        <div className="mx-auto grid max-w-6xl gap-12 px-5 py-24 lg:grid-cols-[1fr_1.1fr] lg:items-start">
          <div>
            <p className="font-mono text-[12px] font-medium uppercase tracking-[0.18em] text-flag">
              Pipeline
            </p>
            <h2 className="mt-4 font-display text-3xl font-semibold tracking-tight sm:text-4xl">
              Diseñado para no inventar
            </h2>
            <p className="mt-5 max-w-md leading-relaxed text-muted">
              Cada etapa existe para acotar la alucinación: recuperación sobre
              una guía curada, citas obligatorias, grounding medido por frase y
              abstención explícita cuando el documento está fuera de dominio o
              la evidencia es insuficiente.
            </p>
            <p className="mt-7 flex items-center gap-2 text-sm text-muted">
              <BadgeCheck className="size-4 text-jade" />
              209 tests en verde en el gate de verificación del repo
            </p>
          </div>
          <div>
            {PIPELINE.map((row) => (
              <div
                key={row.stage}
                className="flex items-baseline justify-between gap-6 border-b border-line py-4 text-sm first:border-t"
              >
                <span className="font-medium">{row.stage}</span>
                <span className="text-right font-mono text-[12.5px] text-muted">
                  {row.tech}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA final */}
      <section className="mx-auto max-w-6xl px-5 py-28 text-center">
        <h2 className="mx-auto max-w-2xl font-display text-3xl font-semibold leading-tight tracking-tight sm:text-5xl">
          “Señales de riesgo potenciales,
          <br /> nunca acusaciones.”
        </h2>
        <p className="mx-auto mt-6 max-w-xl text-muted">
          El dossier siempre declara su incertidumbre y exige revisión humana.
          Esa honestidad es parte del diseño, no una disculpa.
        </p>
        <Link
          href="/analizar"
          className="mt-10 inline-flex items-center gap-2 rounded-lg bg-flag px-7 py-4 text-[15px] font-semibold text-white transition hover:bg-flag-deep"
        >
          Empezar ahora
          <ArrowRight className="size-4" />
        </Link>
      </section>
    </div>
  );
}
