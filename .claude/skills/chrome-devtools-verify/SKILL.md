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

If it returns Chrome JSON (`"Browser": "Chrome/..."`) → bridge alive, call `mcp__chrome-devtools__list_pages` and go.

If empty/timeout/reset → bridge not up. Use **STABLE PATH** below. **Do NOT use `@dbalabka/chrome-wsl` (v4tov4 portproxy points to wrong address, silently fails with "Empty reply" — confirmed broken on every Nicolify session).**

### STABLE PATH: WSL2 Mirrored Networking + Start-Process launch

Verified working 2026-04-24. Zero portproxy, zero socat, zero admin PowerShell after initial `.wslconfig` setup. Only prerequisite: Windows 11 22H2+.

**One-time setup (survives reboot):**

1. Edit `%USERPROFILE%\.wslconfig` (Notepad, create if missing):
   ```ini
   [wsl2]
   networkingMode=mirrored
   dnsTunneling=true
   autoProxy=true
   firewall=true
   ```
2. PowerShell (normal):
   ```powershell
   wsl --shutdown
   ```
   Wait 10s, reopen WSL. Mirrored mode now active — Windows `localhost:PORT` = WSL `localhost:PORT`.
3. Register MCP (WSL, once):
   ```bash
   claude mcp remove chrome-devtools -s local 2>/dev/null
   claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest --browser-url=http://127.0.0.1:9222
   ```
4. `/exit` + reopen Claude Code (MCP subprocess captures args at startup).

**Per-session (user runs this, PowerShell normal, NOT admin):**

```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList '--remote-debugging-port=9222','--user-data-dir=C:\Temp\chrome-debug-profile','https://dev-app.nicolify.com'
```

Profile at `C:\Temp\chrome-debug-profile` isolates session (Chrome 136+ refuses remote debugging on default profile). Clerk session persists across restarts in this profile — login once, reuse.

**WSL verification:**
```bash
curl -s http://127.0.0.1:9222/json/version | head -3
```
Expected: JSON with `"Browser": "Chrome/..."`.

### Why this config (and why the alternatives fail)

| Attempt | Outcome | Root cause |
|---|---|---|
| `npx @dbalabka/chrome-wsl` | "Empty reply from server" | Sets `portproxy v4tov4 → 127.0.0.1`. Chrome Windows bindes `::1` IPv6. Connect reaches nothing. |
| Manual `portproxy v4tov6 → ::1` | Works temporarily | Requires PowerShell admin every reboot; brittle; breaks if Chrome relaunched on different address. |
| `--remote-debugging-address=0.0.0.0` + firewall rule | Works but requires admin firewall setup | Extra attack surface, still needs portproxy if Windows < 22H2. |
| `.wslconfig networkingMode=mirrored` (this path) | **Stable, zero-admin per session** | Mirrored mode makes Windows `localhost` directly reachable from WSL. Requires Win 11 22H2+ only. |

### PowerShell gotchas (PS 5.1 parser quirks)

- `& "path with spaces" -flag=value` — WORKS when `&` is first token.
- `"path with spaces" --flag=value` — FAILS: PS reads the string as literal, interprets `--flag` as operator. Use `Start-Process` or prefix `&`.
- `$env:TEMP\chrome-debug-profile` inside a double-quoted PowerShell argument gets expanded differently than inside a single-quoted one. Prefer literal paths (`C:\Temp\chrome-debug-profile`) — immune to expansion surprises.
- `Start-Process ... -ArgumentList '--flag=val','--flag2=val2','url'` — the cleanest cross-PS-version spawn. Use this over raw `& chrome.exe`.

### Fallback: Windows < 22H2 (no mirrored mode)

Only use if `wsl --version` shows Windows < 22H2. Launch Chrome with `--remote-debugging-address=0.0.0.0`, open firewall, hit `http://$WIN_GW_IP:9222` from WSL (where `WIN_GW_IP=$(ip route show default | awk '{print $3}')`). Not recommended for repeat use.

## Common pitfalls (all hit and resolved in Nicolify sessions)

1. **MCP subprocess cached.** Any `claude mcp add/remove` change needs `/exit` + reopen. Don't retry tool calls hoping the config reloaded.
2. **PowerShell parser rejects bare chrome.exe + flags.** Must use `Start-Process -ArgumentList` or `& chrome.exe ...`.
3. **Chrome 136+ refuses remote debugging on default user profile.** Always pass `--user-data-dir=C:\Temp\chrome-debug-profile` (or similar isolated path).
4. **Headless mode breaks Clerk.** `--headless=new` works for static sites but Clerk sign-in has CF bot detection → painful. Use headful bridged Chrome, persist session via user-data-dir.
5. **`npx @dbalabka/chrome-wsl` portproxy is wrong.** Sets v4tov4 → 127.0.0.1; Chrome Windows listens on `::1`. Result: "Empty reply from server". Do NOT use this helper — use STABLE PATH above.
6. **Page UIDs change per snapshot.** Save the latest snapshot's uid before clicking. If `click` times out, fall back to `evaluate_script` with `document.querySelectorAll('button').find(b => b.textContent === '…').click()`.
7. **`navigate_page` reload throws timeout ~10s** but page still reloads — follow with `wait_for` instead of trusting the error.
8. **UIDs renumber per tab prefix.** After dialog/nav the uid scope (e.g., `7_*` → `11_*`) resets. Always re-snapshot.

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
