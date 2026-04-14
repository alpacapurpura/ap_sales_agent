import { describe, it, expect } from "vitest";
import { CHANNEL_STAGE_MAP, getStageForChannel } from "../channel-stage-map";

describe("CHANNEL_STAGE_MAP", () => {
  it("maps meta-ads to atraccion-captura", () => {
    expect(CHANNEL_STAGE_MAP["meta-ads"]).toBe("atraccion-captura");
  });

  it("maps ig-organic to atraccion-captura", () => {
    expect(CHANNEL_STAGE_MAP["ig-organic"]).toBe("atraccion-captura");
  });

  it("maps yt-organic to atraccion-captura", () => {
    expect(CHANNEL_STAGE_MAP["yt-organic"]).toBe("atraccion-captura");
  });

  it("maps google-organic to atraccion-captura", () => {
    expect(CHANNEL_STAGE_MAP["google-organic"]).toBe("atraccion-captura");
  });

  it("maps google-ads to atraccion-captura", () => {
    expect(CHANNEL_STAGE_MAP["google-ads"]).toBe("atraccion-captura");
  });

  it("maps facebook-organic to atraccion-captura", () => {
    expect(CHANNEL_STAGE_MAP["facebook-organic"]).toBe("atraccion-captura");
  });

  it("maps email-nurture to nutricion-oportunidad", () => {
    expect(CHANNEL_STAGE_MAP["email-nurture"]).toBe("nutricion-oportunidad");
  });

  it("maps email-launch to nutricion-oportunidad", () => {
    expect(CHANNEL_STAGE_MAP["email-launch"]).toBe("nutricion-oportunidad");
  });

  it("maps email-sequences to nutricion-oportunidad", () => {
    expect(CHANNEL_STAGE_MAP["email-sequences"]).toBe("nutricion-oportunidad");
  });

  it("maps meta-retargeting to nutricion-oportunidad", () => {
    expect(CHANNEL_STAGE_MAP["meta-retargeting"]).toBe("nutricion-oportunidad");
  });
});

describe("getStageForChannel", () => {
  it("returns mapped stage for known channel", () => {
    expect(getStageForChannel("meta-ads")).toBe("atraccion-captura");
  });

  it("returns atraccion-captura as fallback for unknown channel", () => {
    expect(getStageForChannel("unknown-channel")).toBe("atraccion-captura");
  });
});
