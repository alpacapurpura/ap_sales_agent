import { describe, it, expect } from "vitest";

import { buildSettingsCrumbs } from "./SettingsBreadcrumb";

describe("buildSettingsCrumbs", () => {
  it("returns only root crumb for empty path", () => {
    const crumbs = buildSettingsCrumbs("", "tenant-1");
    expect(crumbs).toHaveLength(1);
    expect(crumbs[0].label).toBe("Configuración");
  });

  it("returns root crumb for settings root path", () => {
    const crumbs = buildSettingsCrumbs("/tenant-1/settings", "tenant-1");
    expect(crumbs).toHaveLength(1);
    expect(crumbs[0].label).toBe("Configuración");
  });

  it("returns 2 crumbs for /settings/general", () => {
    const crumbs = buildSettingsCrumbs("/tenant-1/settings/general", "tenant-1");
    expect(crumbs).toHaveLength(2);
    expect(crumbs[0].label).toBe("Configuración");
    expect(crumbs[1].label).toBe("General");
  });

  it("returns correct label for perfil-negocio slug", () => {
    const crumbs = buildSettingsCrumbs("/tenant-1/settings/perfil-negocio", "tenant-1");
    expect(crumbs).toHaveLength(2);
    expect(crumbs[1].label).toBe("Perfil de negocio");
  });

  it("root crumb has correct href", () => {
    const crumbs = buildSettingsCrumbs("/tenant-1/settings/general", "tenant-1");
    expect(crumbs[0].href).toBe("/tenant-1/settings");
  });

  it("leaf crumb has no href (active page)", () => {
    const crumbs = buildSettingsCrumbs("/tenant-1/settings/general", "tenant-1");
    expect(crumbs[crumbs.length - 1].href).toBeUndefined();
  });

  it("returns correct label for agenda slug", () => {
    const crumbs = buildSettingsCrumbs("/tenant-1/settings/agenda", "tenant-1");
    expect(crumbs[1].label).toBe("Agenda");
  });

  it("falls back to slug for unknown sections", () => {
    const crumbs = buildSettingsCrumbs("/tenant-1/settings/unknown-section", "tenant-1");
    expect(crumbs[1].label).toBe("unknown-section");
  });
});
