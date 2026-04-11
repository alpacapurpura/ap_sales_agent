import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { AssetsView } from "../assets/assets-view";
import { CampaignsView } from "../campaigns/campaigns-view";
import { KnowledgeView } from "../knowledge/knowledge-view";

const OFFER_ID = "offer-42";

describe("Tab placeholder views", () => {
  describe("AssetsView", () => {
    it("renders with a labelled region and Spanish copy", () => {
      render(<AssetsView offerId={OFFER_ID} />);
      const region = screen.getByRole("region", {
        name: /biblioteca de assets/i,
      });
      expect(region).toBeInTheDocument();
      expect(screen.getByText(/Biblioteca de assets/i)).toBeInTheDocument();
      expect(
        screen.getByText(/galería, filtros, CRUD/i),
      ).toBeInTheDocument();
      expect(screen.getByText(/Oferta: offer-42/)).toBeInTheDocument();
    });
  });

  describe("CampaignsView", () => {
    it("renders with a labelled region and Spanish copy with tildes", () => {
      render(<CampaignsView offerId={OFFER_ID} />);
      const region = screen.getByRole("region", {
        name: /campañas de la oferta/i,
      });
      expect(region).toBeInTheDocument();
      // Heading uses the "ñ" character
      expect(
        screen.getByRole("heading", { name: /Campañas/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/asociación con la oferta/i),
      ).toBeInTheDocument();
      expect(screen.getByText(/Oferta: offer-42/)).toBeInTheDocument();
    });
  });

  describe("KnowledgeView", () => {
    it("renders with a labelled region and Spanish copy with tildes", () => {
      render(<KnowledgeView offerId={OFFER_ID} />);
      const region = screen.getByRole("region", {
        name: /base de conocimiento/i,
      });
      expect(region).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /Base de conocimiento/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/ingestión, documentos, estado/i),
      ).toBeInTheDocument();
      expect(screen.getByText(/Oferta: offer-42/)).toBeInTheDocument();
    });
  });
});
