import { render, screen } from "@testing-library/react";
import * as React from "react";
import { describe, it, expect } from "vitest";

import { IdentityList } from "../IdentityList";

import type { ContactIdentity } from "../../types";

const identities: ContactIdentity[] = [
  {
    type: "email",
    value: "ana@example.com",
    is_primary: true,
    verification_status: "verified",
    last_seen_at: "2026-04-01T00:00:00Z",
  },
  {
    type: "telegram",
    value: "@ana_ar",
    is_primary: false,
    verification_status: "pending",
    last_seen_at: "2026-04-10T00:00:00Z",
  },
];

describe("IdentityList", () => {
  it("renders all identities", () => {
    render(<IdentityList identities={identities} />);
    expect(screen.getByText("ana@example.com")).toBeInTheDocument();
    expect(screen.getByText("@ana_ar")).toBeInTheDocument();
  });

  it("shows empty message when no identities", () => {
    render(<IdentityList identities={[]} />);
    expect(screen.getByText(/Sin identidades registradas/)).toBeInTheDocument();
  });

  it("renders as list element", () => {
    const { container } = render(<IdentityList identities={identities} />);
    expect(container.querySelector("ul")).toBeInTheDocument();
  });
});
