---
name: tessl-context
description: Manage Tessl tiles — search, install, update, and list versioned docs for project dependencies
user_invocable: true
---

# Tessl Context Manager

Manage the Tessl tile registry for curated, versioned documentation of project dependencies.

## Priority Rule

**CLAUDE.md always wins.** If a Tessl tile contradicts a rule in CLAUDE.md or `.claude/rules/`, follow CLAUDE.md. Tiles provide library reference docs, not project conventions.

## Commands

### Search for a library's tile
```bash
tessl search <library-name>
```

### Install a tile
```bash
tessl install <tile-id> --agent claude-code --yes
```

### List installed tiles
```bash
tessl list
```

### Check for outdated tiles
```bash
tessl outdated
```

### Update all tiles
```bash
tessl update
```

### Health check
```bash
tessl doctor
```

### Security review
```bash
tessl review
```

## Notes

- Tessl CLI runs on the **host** (not inside Docker containers)
- The MCP server (`tessl mcp start`) provides automatic context — this skill is for manual management
- `tessl.json` is the shared manifest (committed to git)
- `.tessl/` is the local cache (gitignored)
- Tiles complement context7 (live web docs) with curated, version-pinned documentation
