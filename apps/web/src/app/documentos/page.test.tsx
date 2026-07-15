import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import DocumentosPage from "./page";

const DEMO_PDF_BASE =
  "https://raw.githubusercontent.com/MiguelAAR10/rag-redflags-colab/main/data/samples";
const DEMO_DOCUMENTS = [
  {
    filename: "tdr-tce-01626-2023-essalud-comite-nulo.pdf",
    title: "EsSalud: conformación del comité",
  },
  {
    filename:
      "tdr-tce-00132-2022-hospital-lambayeque-registro-sanitario.pdf",
    title: "Hospital Lambayeque: registro sanitario",
  },
  {
    filename: "tdr-tce-04185-2022-fospeme-certificado-incumplido.pdf",
    title: "Fospeme: certificado presentado",
  },
  {
    filename: "tdr-contraloria-bid-seguimiento-contractual.pdf",
    title: "Seguimiento contractual BID",
  },
  {
    filename: "tdr-predes-zona-segura-los-olivos.pdf",
    title: "Zona Segura Los Olivos",
  },
  {
    filename: "tdr-pronied-infraestructura-educativa.pdf",
    title: "Infraestructura educativa PRONIED",
  },
] as const;

vi.mock("@/lib/api", () => ({
  analyzeTdr: vi.fn(),
  getDossier: vi.fn(),
  listTdrs: vi.fn(() => Promise.reject(new Error("API no disponible"))),
}));

describe("DocumentosPage", () => {
  it("keeps all demo downloads available when the history API fails", async () => {
    render(<DocumentosPage />);

    expect(await screen.findByText("API no disponible")).toBeVisible();
    expect(screen.getByText(/fuentes públicas de demostración/i)).toBeVisible();
    expect(screen.getByText(/señales de riesgo potenciales/i)).toBeVisible();
    expect(screen.getByText(/requiere revisión humana/i)).toBeVisible();

    for (const { filename, title } of DEMO_DOCUMENTS) {
      const card = screen.getByText(filename).closest("article");
      expect(card).not.toBeNull();

      const download = within(card!).getByRole("link", {
        name: `Descargar PDF: ${title}`,
      });
      expect(download).toHaveAttribute(
        "href",
        `${DEMO_PDF_BASE}/${filename}`,
      );
      expect(download).toHaveAttribute("target", "_blank");
      expect(download).toHaveAttribute("rel", "noreferrer");

      expect(
        within(card!).getByRole("link", {
          name: `Analizar documento: ${title}`,
        }),
      ).toHaveAttribute("href", "/analizar");
    }

    expect(screen.getAllByRole("article")).toHaveLength(6);
  });
});
