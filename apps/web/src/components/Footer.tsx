import Image from "next/image";
import { Scale } from "lucide-react";

export const DISCLAIMER =
  "Este sistema identifica señales de riesgo potenciales basadas en la guía OCP 2024 de red flags en contratación pública. No prueba corrupción, responsabilidad ni delito. Todo hallazgo requiere revisión humana y contraste con las fuentes originales.";

export function Footer() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto max-w-6xl px-5 py-12">
        <div className="flex items-start gap-3 border-l-2 border-flag/70 pl-4">
          <Scale className="mt-0.5 size-4 shrink-0 text-muted" />
          <p className="text-[13px] leading-relaxed text-muted">{DISCLAIMER}</p>
        </div>
        <div className="mt-10 flex flex-col items-start justify-between gap-5 border-t border-line pt-7 sm:flex-row sm:items-center">
          <div className="flex items-center gap-3">
            <Image
              src="/uni-escudo-guinda.png"
              alt="Escudo de la Universidad Nacional de Ingeniería"
              width={27}
              height={36}
              className="h-9 w-auto"
            />
            <div className="text-[13px] font-medium leading-tight text-muted">
              Proyecto UNI
            </div>
          </div>
          <span className="font-mono text-[12px] text-faint">
            RAG · Qdrant · Gemini 2.5 Flash · Vertex AI
          </span>
        </div>
      </div>
    </footer>
  );
}
