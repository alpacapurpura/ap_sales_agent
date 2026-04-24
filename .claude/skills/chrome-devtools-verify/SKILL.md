---
name: chrome-devtools-verify
description: "Live verification of frontend changes in dev-app.nicolify.com using Chrome DevTools MCP from WSL2. Use when: verifying a frontend bug fix, reproducing a user-reported UI bug step-by-step, checking real-time SSE/polling behavior, validating card/form interactions, inspecting DOM or console or network live, or any task where 'me lo muestres en el navegador' would be cheaper than guessing. Triggers: 'verifica en el navegador', 'prueba con chrome-devtools', 'reproduce el bug en vivo', 'abrí el navegador', 'chrome-devtools-mcp', 'live test', 'verify UI fix'."
---

# Chrome DevTools MCP — Live Frontend Verification

Project memory: Nicolify (AISALESHT), Next.js 16 + React 19 + Clerk.
Chrome runs on **Windows host**, Claude Code runs in **WSL2**. Bridge needed.

## When to invoke this skill

- User reports a FE bug you're about to fix → ask first: "¿Querés que use chrome-devtools MCP para reproducir + verificar en vivo?" If yes → run Bootstrap.
- User asks to verify recent FE changes end-to-end.
- You need to see DOM / console / network / React state for a running app.
- Reproducing flows that touch SSE, polling, hydration, or server-emitted cards where traces alone aren't enough.

## When NOT to invoke

- Pure backend tasks.
- Unit tests suffice.
- User said "no necesito que pruebes, yo lo hago" explicitly.

## Bootstrap — first call per session

Check MCP reachable before assuming anything:

```bash
curl -sf http://127.0.0.1:9222/json/version | head -3
```

If it returns Chrome JSON → bridge alive, call `mcp__chrome-devtools__list_pages` and go.

If empty/timeout → bridge not up. Walk user through these exact steps (do NOT try to automate — user action required).

### Full setup (once per machine, survives reboots for bridge; Chrome must be relaunched each time)

**Step 1 — WSL, once:**
```bash
sudo apt-get install -y socat
```

**Step 2 — user closes all Chrome processes on Windows** (Task Manager kill all `chrome.exe`).

**Step 3 — WSL terminal (keeps running, separate tab):**
```bash
npx @dbalabka/chrome-wsl
```
Launches Windows Chrome with `--remote-debugging-port=9222` + `socat` bridge `WSL:9222 → Windows:9222`.

**Step 4 — Windows Chrome binds to IPv6 `::1` by default.** Portproxy needs `v4tov6`. Run in **PowerShell admin**:
```powershell
netsh interface portproxy delete v4tov4 listenaddress=<WSL_GATEWAY_IP> listenport=9222
netsh interface portproxy add v4tov6 listenport=9222 listenaddress=<WSL_GATEWAY_IP> connectport=9222 connectaddress=::1
New-NetFirewallRule -DisplayName "Chrome Debug 9222" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 9222
```
Get `<WSL_GATEWAY_IP>` via `ip route | grep default | awk '{print $3}'` in WSL.

**Step 5 — MCP registration (once, WSL):**
```bash
claude mcp remove chrome-devtools -s local 2>/dev/null
claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest --browser-url=http://127.0.0.1:9222
```

**Step 6 — user restarts Claude Code** (`/exit` + reopen). MCP subprocess captures args at startup; config changes require restart.

**Step 7 — user logs into `https://dev-app.nicolify.com` in the bridged Chrome.** Clerk session persists across tests.

## Common pitfalls (all hit in Nicolify session 2026-04-23)

1. **MCP subprocess cached.** Any `claude mcp add/remove` change needs `/exit` + reopen. Don't retry tool calls hoping the config reloaded.
2. **Chrome binds IPv6 only.** `netsh portproxy v4tov4 … connectaddress=127.0.0.1` silently fails with "Empty reply from server". Must be `v4tov6 … connectaddress=::1`.
3. **Headless mode breaks Clerk.** `--headless=true` works for static sites but Clerk sign-in has CF bot detection → painful. Use headful bridged Chrome, persist session.
4. **Page UIDs change per snapshot.** Save the latest snapshot's uid before clicking. If `click` times out, fall back to `evaluate_script` with `document.querySelectorAll('button').find(b => b.textContent === '…').click()`.
5. **`navigate_page` reload throws timeout ~10s** but page still reloads — follow with `wait_for` instead of trusting the error.
6. **UIDs renumber per tab prefix.** After dialog/nav the uid scope (e.g., `7_*` → `11_*`) resets. Always re-snapshot.

## Workflow template — reproducing a FE bug

```
1. list_pages             → find dev-app tab, confirm URL
2. take_snapshot          → get current UIDs
3. fill / click           → drive the user action that reproduces
4. wait_for + take_snapshot → confirm the visible state after
5. list_network_requests  → catch 4xx/5xx polls, wrong URLs
6. list_console_messages  → client errors
7. DB cross-check:
   - docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "SELECT … FROM copilot_trace_event WHERE conversation_id=…"
   - Pills land in `copilot_conversations.messages` as assistant msgs with `blocks[].card_kind`
8. Fix, restart affected container (brain/worker), hard reload tab:
   - navigate_page type=reload ignoreCache=true
9. Repeat 1–6 to verify.
```

## Useful evaluate_script snippets

```js
// Click by visible text (bypasses stale uids)
() => {
  const btn = Array.from(document.querySelectorAll('button'))
    .find(b => b.textContent?.trim() === 'Empezar desde cero');
  btn?.click();
  return btn ? 'clicked' : 'not found';
}

// Inspect Zustand copilot store from devtools
() => {
  const store = window.__COPILOT_STORE__;
  if (!store) return 'store not exposed';
  const s = store.getState();
  return {
    msgCount: s.messages.length,
    activeJobs: Object.keys(s.activeJobs),
    status: s.status,
  };
}

// Raw fetch with session cookie (bypasses auth helpers)
async () => {
  const res = await fetch('/api/v1/brand/tools/extract-full-brand/status/<jobId>', { credentials: 'include' });
  return { status: res.status, body: await res.text() };
}
```

## Bug-hunting cheat sheet (Nicolify 2026-04-23 patterns)

- **"pills no aparecen en real-time"** → first check `list_network_requests` for the poll endpoint. 404s = route mismatch (verify `/tools/` prefix). All 200s = FE invalidation issue.
- **"clarify buttons aparecen otra vez después del reload"** → backend never mutates `block.payload.card_status`. FE must auto-resolve historical cards (see `resolveHistoricalCards` in `CopilotChatPanel.tsx`).
- **"chip/progress no se muestra"** → `toolCalls` lost on hydration because wire `ConversationMessage` doesn't carry `tool_calls`. Render chip from `activeJobs` store via `ActiveJobsPoller`, not from `message.toolCalls`.
- **"He iniciado aparece duplicado"** → prompt bug. LLM wrote confirmation text alongside `clarify` call before extraction dispatched. Fix in `copilot_system.j2` — explicit rule: clarify only ⇒ no "inicié/comencé" text.
- **404 on poll** → router prefix. `brand_tools` mounted at `/api/v1/brand/tools/…`. Tool hardcodes `poll_endpoint` in `copilot/application/tools/extraction_tools.py` — must match the mount prefix.

## DB quick probes

```bash
# Latest conversation for tenant
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -t -A -F'|' -c \
  "SELECT id, LEFT(title,60) FROM copilot_conversations WHERE tenant_id='<uuid>' ORDER BY updated_at DESC LIMIT 3;"

# Trace events for a conversation
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -t -A -F'|' -c \
  "SELECT event_type, name, status, LEFT(data::text, 100) FROM copilot_trace_event WHERE conversation_id='<uuid>' ORDER BY created_at;"

# Check Redis progress key
docker exec visionarias_redis redis-cli -n 0 GET 'brand_extract:<tenant>:<job_id>'
```

## Post-session

When fix verified live, stop using MCP tools unless needed again. Don't leave polling loops running. If you ran a new conversation that littered DB, optionally note it in the summary — no cleanup required (dev env).

## References
- https://github.com/dbalabka/chrome-wsl — bridge helper
- https://github.com/ChromeDevTools/chrome-devtools-mcp — MCP upstream
- https://github.com/ChromeDevTools/chrome-devtools-mcp/issues/131 — WSL support thread
