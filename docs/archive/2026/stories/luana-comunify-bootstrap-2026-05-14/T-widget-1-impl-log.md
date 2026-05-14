# T-widget-1 impl-log

**Ticket:** T-widget-1 — Vite UMD bundle
**Tools:** Write (widget entry, components, vite config, postmessage protocol)
**Iterations:** 1 (tsc clean; widget uses separate tsconfig to avoid Next.js JSX transform conflicts)
**Notes:** UMD build uses `lib.entry = 'src/widget-entry.tsx'` + `lib.name = 'ComunifyWidget'` + `lib.formats = ['umd']`. React and ReactDOM are externalized (host page expected to provide them or bundled via rollupOptions). postmessage-protocol.ts is isomorphic (no browser globals) so it can be imported in both widget and parent page TypeScript.
