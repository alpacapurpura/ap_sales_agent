import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerLocationSchema } from "../location.schema";

describe("offerLocationSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerLocationSchema)).not.toThrow();
  });

  it("declares mixed scope (venues offer-level, specific-venue edition-level)", () => {
    expect(offerLocationSchema.scope).toBe("mixed");
    expect(offerLocationSchema.key).toBe("offer.location");
  });

  it("every field in a mixed section declares its owner", () => {
    for (const field of offerLocationSchema.fields) {
      expect(field.owner, `field ${field.id} missing owner`).toBeTruthy();
    }
  });

  it("references Scheduling module via scheduling-event-type-picker action (no duplicate booking UI)", () => {
    const field = offerLocationSchema.fields.find((f) => f.id === "scheduling_event_type_id");
    expect(field?.type).toBe("custom");
    expect(field?.action).toBe("scheduling-event-type-picker");
  });

  it("keeps the WhatsApp fallback for tenants that haven't wired Scheduling yet", () => {
    const field = offerLocationSchema.fields.find((f) => f.id === "booking_fallback_whatsapp");
    expect(field).toBeTruthy();
    expect(field?.type).toBe("text");
  });

  it("exposes the edition-level override slot for itinerant events", () => {
    const field = offerLocationSchema.fields.find((f) => f.id === "event_specific_venue");
    expect(field?.owner).toBe("edition");
  });

  it("does not duplicate booking mechanics owned by the Scheduling module", () => {
    const ids = offerLocationSchema.fields.map((f) => f.id);
    // These lived here pre-cleanup; after pre-sale consolidation they live
    // in backend/src/modules/scheduling exclusively.
    expect(ids).not.toContain("booking_channels");
    expect(ids).not.toContain("booking_lead_time_hours");
    expect(ids).not.toContain("confirmation_method");
    expect(ids).not.toContain("no_show_policy");
  });
});
