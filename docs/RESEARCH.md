# Research candidates

Initial discovery: 2026-10-24. These links are starting points, not endorsements or tested compatibility claims. Re-check current source, license, maintenance, data routing, and security before adoption. No third-party source is vendored.

| Candidate | Role to evaluate | Primary source |
| --- | --- | --- |
| Hermes Agent | Persistent agent, skills, scheduled work | https://github.com/NousResearch/hermes-agent |
| IronClaw | Capability-oriented execution and credentials | https://github.com/nearai/ironclaw |
| Letta Code | Stateful agent and reflection; inspect local/cloud boundary | https://github.com/letta-ai/letta-code |
| MyChatArchive | Provider imports and local archive retrieval | https://github.com/1ch1n/mychatarchive |
| OpenSelf | Scoped context and provenance | https://github.com/Open-Self/Open-Self |
| vault-memory | Markdown retrieval and guarded publication | https://github.com/owrede/vault-memory |
| Graphiti | Time-aware relationships if simpler indexing proves insufficient | https://github.com/getzep/graphiti |
| Gitleaks | Secret detection | https://github.com/gitleaks/gitleaks |
| Syft / Grype | Component inventory and vulnerability findings | https://github.com/anchore/syft and https://github.com/anchore/grype |
| Restic | Backup and restoration | https://github.com/restic/restic |

Obsidian integration references: [headless Sync](https://obsidian.md/help/sync/headless), [storage limits](https://obsidian.md/help/sync/plans). Obsidian is an optional proprietary client/service over user-owned Markdown; Lamassu's core must remain usable without it.

## Comparison protocol

Use synthetic or explicitly permitted private records. Evaluate exact recall, source attribution, time/conflict handling, import coverage, export/restore, scoped retrieval, unsafe tool requests, offline reconciliation, and operating effort. Record tested revision and environment. Feature lists and popularity do not establish reliability. The local archive prototype exists to make the evidence contract concrete, not to preselect a replacement for established importers.
