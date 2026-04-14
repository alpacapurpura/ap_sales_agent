import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PersonaPreviewSummary } from "../persona-preview-summary";
import { PersonaPreviewSections } from "../persona-preview-sections";

// ── PersonaPreviewSummary ──────────────────────────────────────────────────

describe("PersonaPreviewSummary", () => {
  it("renders persona name and tagline", () => {
    render(
      <PersonaPreviewSummary
        data={{ name: "Ana Rodriguez", tagline: "Emprendedora digital" }}
        completenessScore={60}
      />,
    );
    expect(screen.getByText("Ana Rodriguez")).toBeInTheDocument();
    expect(screen.getByText("Emprendedora digital")).toBeInTheDocument();
  });

  it("renders avatar with first letter of name", () => {
    render(<PersonaPreviewSummary data={{ name: "Carlos Mendez" }} completenessScore={30} />);
    expect(screen.getByText("C")).toBeInTheDocument();
  });

  it("renders completeness score as percentage", () => {
    render(<PersonaPreviewSummary data={{ name: "Test" }} completenessScore={75} />);
    expect(screen.getByText("75%")).toBeInTheDocument();
  });

  it("renders placeholder when name is missing", () => {
    render(<PersonaPreviewSummary data={{}} completenessScore={0} />);
    expect(screen.getByText("Buyer Persona")).toBeInTheDocument();
    expect(screen.getByText("?")).toBeInTheDocument();
  });
});

// ── PersonaPreviewSections ─────────────────────────────────────────────────

describe("PersonaPreviewSections", () => {
  const fullData = {
    demographics: {
      age_range: "25-35",
      gender: "Femenino",
      location: "Lima, Peru",
      education: "Universitaria",
      income_level: "Medio-alto",
    },
    psychographics: {
      values: ["Libertad", "Creatividad"],
      interests: ["Marketing digital"],
      personality: "Extrovertida",
    },
    pain_points: [
      { description: "No tiene tiempo para marketing" },
      { description: "No sabe como crear contenido" },
    ],
    desires: [
      { description: "Automatizar su marketing" },
      { description: "Crecer en redes sociales" },
    ],
    objections: [{ description: "Es muy caro" }],
    channels: ["Instagram", "TikTok", "Email"],
    journey: {
      awareness: "Busca en Google",
      consideration: "Compara opciones",
    },
  };

  it("renders all 7 section headers", () => {
    render(
      <PersonaPreviewSections
        data={fullData}
        currentBlock="demographics"
        blocksCompleted={["demographics"]}
      />,
    );

    expect(screen.getByText("Demografía")).toBeInTheDocument();
    expect(screen.getByText("Psicografía")).toBeInTheDocument();
    expect(screen.getByText("Puntos de dolor")).toBeInTheDocument();
    expect(screen.getByText("Deseos")).toBeInTheDocument();
    expect(screen.getByText("Objeciones")).toBeInTheDocument();
    expect(screen.getByText("Canales")).toBeInTheDocument();
    expect(screen.getByText("Journey")).toBeInTheDocument();
  });

  it("renders pain points with data", () => {
    render(
      <PersonaPreviewSections
        data={fullData}
        currentBlock="pain_points"
        blocksCompleted={["demographics", "psychographics"]}
      />,
    );

    expect(screen.getByText("No tiene tiempo para marketing")).toBeInTheDocument();
    expect(screen.getByText("No sabe como crear contenido")).toBeInTheDocument();
  });

  it("renders desires with data", () => {
    render(<PersonaPreviewSections data={fullData} currentBlock="desires" blocksCompleted={[]} />);

    expect(screen.getByText("Automatizar su marketing")).toBeInTheDocument();
    expect(screen.getByText("Crecer en redes sociales")).toBeInTheDocument();
  });

  it("renders objections with data", () => {
    render(
      <PersonaPreviewSections data={fullData} currentBlock="objections" blocksCompleted={[]} />,
    );

    expect(screen.getByText("Es muy caro")).toBeInTheDocument();
  });

  it("shows 'Pendiente...' placeholder for empty sections", () => {
    render(<PersonaPreviewSections data={{}} currentBlock="" blocksCompleted={[]} />);

    const pendingItems = screen.getAllByText("Pendiente...");
    expect(pendingItems.length).toBeGreaterThan(0);
  });

  it("renders channels list", () => {
    render(<PersonaPreviewSections data={fullData} currentBlock="channels" blocksCompleted={[]} />);

    expect(screen.getByText("Instagram")).toBeInTheDocument();
    expect(screen.getByText("TikTok")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
  });
});
