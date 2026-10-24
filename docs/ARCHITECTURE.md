# Architecture

Status: the archive, explicit relationships, portable bundles, local read-only workbench, evidence-note drafts, and passive repository inventory are implemented prototypes. Model integration, remote access, autonomous action, and the full permission architecture remain proposed. See ADR 0003 and the workbench guide.

## Roles and trust boundaries

Travel clients hold selected offline context and queued captures. An archive node preserves evidence. Compute workers run bounded tasks. A publishing service writes approved changes to a curated Markdown vault. A credential broker and permission gateway enforce action scope independently of the model. Backup administration has separate credentials.

Each integration receives a distinct identity, allowed data scopes, allowed operations, expiry, and audit trail. Private connectivity is one layer; applications must still authorize requests. Repository workers receive a checkout and minimal task context, not the whole personal archive.

## Prototype contract

`lamassu.conversation.v1` is an explicitly prepared interchange format, not a claimed ChatGPT or Claude export parser. Required keys: `schema`, `provider`, `external_id`, `messages`. Each message has `id`, `role`, and `text`; optional `at` is an ISO timestamp with an explicit offset. Roles: user, assistant, system, tool. Unknown keys, duplicate JSON keys and message IDs, empty identities, and invalid types are refused. Attachments and branches require a future contract; they must never be silently flattened.

The exact input bytes are retained in SQLite with their SHA-256 digest. The record identity combines provider, external ID, and digest. Identical bytes are idempotent. Changed bytes create another revision. Different formatting also creates a revision; semantic deduplication is not claimed. The local workbench uses an ephemeral access key; no multi-user authentication, data-scope authorization, or encryption is implemented. Search is bounded Unicode-aware literal substring matching and returns all matching revisions, not a current-truth view.

## Planned provenance and relationships

Give every source record, message, derived claim, synthesis, job, and scan a stable identifier. Derived objects cite exact source revisions and spans. Record observed time separately from claimed validity time and import time. Preserve speaker roles. Links have types such as continues, supports, contradicts, supersedes, implements, and derived-from. Machine-inferred links remain labeled and reviewable. Repetition across generated summaries does not count as independent evidence.

## Offline and job semantics

Planned clients submit stable event IDs. Requests and workers support retries without duplicate effects. Store queued/running/succeeded/failed/needs-review states, bounded attempts, heartbeat, and cancellation. Approvals bind to an exact action, target revision, scope, and expiry. Reconciliation never silently overwrites human edits. No distributed database or autonomous failover is required for the first deployment.

## Curated vault

Keep transcripts, vectors, model files, logs, and large attachments outside the synced vault. Start with a modest text-only synthesis budget and reserve space for version history. Use stable authenticated archive links, with useful offline titles and excerpts. Start with proposals in a dedicated inbox. Publishing checks the expected content hash and rejects stale writes. Agent processes must not bypass the publisher through unrestricted filesystem access.

## Code analysis

The initial private pilot is a monorepo; no company source or configuration belongs in this public repository. Record repo identity, commit, scanner/rule versions, coverage, finding status, and evidence. Separate architecture maps, deterministic security findings, and LLM interpretations. Redact potential credentials before intake. Running builds or tests is code execution and requires isolated, bounded workers. Routine scans never apply fixes or deploy. Published project syntheses should summarize meaningful changes rather than every finding.

## Portability and lifecycle

Design exports around original bytes, JSON metadata and relationships, Markdown syntheses, and standard scan formats where appropriate. Indexes and embeddings are reconstructible. Version contracts before migration. Forgetting needs a suppression record to prevent re-import plus deletion/invalidation across derived stores; backup retention must be explained. This prototype does not implement deletion or suppression and is unsuitable for records requiring that workflow.

## Implemented workbench and recovery

See [ADR 0003](decisions/0003-evidence-workbench.md), [the workbench guide](WORKBENCH.md), [portable evidence](PORTABILITY.md), and [passive repository inventory](CODEBASE_ANALYSIS.md). SQLite schema version 2 adds explicit source relationships with a transactional v1 migration. The desktop browser reads through a loopback-only service; downloaded Markdown notes remain drafts for manual review. No vault mutation API or model inference is implemented.
