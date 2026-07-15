/** Cliente tipado del backend tdr-api (FastAPI en Cloud Run). */

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Finding {
  title: string;
  severity: string;
  evidence_quote: string;
  explanation: string;
  citation: string;
}

export interface RejectedFinding {
  title: string;
  rejection_reason: string;
}

export interface Dossier {
  risk_level: string;
  risk_reason?: string;
  grounding_ratio: number;
  summary?: string;
  refusal?: string;
  evidence?: {
    accepted_count: number;
    rejected_count: number;
    status?: string;
  };
  findings?: Finding[];
  rejected_findings?: RejectedFinding[];
  uncertainty?: string[];
  next_steps?: string[];
  disclaimer?: string;
}

export interface UploadResult {
  tdr_id: number;
  char_count: number;
  sha256: string;
  reindex?: { chunks_total?: number };
  analysis_run_id?: number;
}

export interface TdrSummary {
  id: number;
  filename: string;
  risk_level?: string | null;
  latest_run_status?: string | null;
}

export interface TdrDetail {
  id?: number;
  filename?: string;
  char_count?: number;
  status?: string;
  sha256?: string;
  latest_run?: { id: number; status: string } | null;
}

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

async function unwrap<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* cuerpo no-JSON */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export async function uploadTdr(opts: {
  file?: File;
  pastedText?: string;
}): Promise<UploadResult> {
  const form = new FormData();
  if (opts.file) form.append("file", opts.file);
  if (opts.pastedText) form.append("pasted_text", opts.pastedText);
  form.append("auto_analyze", "false");
  const res = await fetch(`${API_URL}/api/tdrs/upload`, {
    method: "POST",
    body: form,
  });
  return unwrap<UploadResult>(res);
}

/** Bloquea hasta que el análisis termina (el backend es síncrono). */
export async function analyzeTdr(tdrId: number): Promise<{ run_id: number }> {
  const res = await fetch(`${API_URL}/api/tdrs/${tdrId}/analyze`, {
    method: "POST",
  });
  return unwrap<{ run_id: number }>(res);
}

export async function getDossier(tdrId: number): Promise<Dossier> {
  const res = await fetch(`${API_URL}/api/tdrs/${tdrId}/dossier`);
  return unwrap<Dossier>(res);
}

export async function listTdrs(): Promise<TdrSummary[]> {
  const res = await fetch(`${API_URL}/api/tdrs`);
  const body = await unwrap<{ tdrs: TdrSummary[] }>(res);
  return body.tdrs ?? [];
}

export async function getTdrDetail(tdrId: number): Promise<TdrDetail> {
  const res = await fetch(`${API_URL}/api/tdrs/${tdrId}`);
  return unwrap<TdrDetail>(res);
}
