import "@testing-library/jest-dom";

import { vi } from "vitest";

/**
 * Global mock for ``next/navigation``.
 *
 * The form-runtime layer relies on ``useActiveField`` which in turn calls
 * ``usePathname`` + ``useSearchParams``. Under happy-dom no App Router is
 * mounted, so the real hooks throw "invariant expected app router to be
 * mounted". Every test that renders a ``FormRuntimeProvider`` (directly
 * or via ``UniversalEditableSection``) would otherwise have to declare
 * its own mock.
 *
 * This global mock wires sensible defaults. Individual tests may call
 * ``vi.mocked(useParams).mockReturnValue(...)`` (or friends) to customise
 * return values for a specific case.
 */
vi.mock("next/navigation", () => ({
  useParams: vi.fn(() => ({})),
  usePathname: vi.fn(() => "/"),
  useSearchParams: vi.fn(() => new URLSearchParams()),
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  })),
  redirect: vi.fn(),
  notFound: vi.fn(),
}));
