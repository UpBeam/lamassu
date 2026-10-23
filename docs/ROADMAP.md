# Roadmap

No dates or integration commitments are implied. Each stage needs a review before expanding privileges.

## 0 — Foundation (this repository)

- [x] Document boundaries, device roles, memory layers, and decisions.
- [x] Local neutral-record intake, evidence preservation, idempotence, and literal search.
- [x] Synthetic tests and CI definition.
- [ ] Publish repository and verify remote CI.

## 1 — Archive pilot

- [ ] Inspect actual provider export formats privately; publish only synthetic compatibility fixtures.
- [ ] Verify message counts, branching, timestamps, attachments, deduplication, and coverage reports.
- [ ] Add versioned portable export and restore checks.
- [ ] Implement deletion/suppression policy before broad personal intake.
- [ ] Compare existing archive tools against a fixed recall corpus.

Acceptance: repeat imports and a backup restore preserve verifiable source records; unsupported data is reported.

## 2 — Curated memory

- [ ] Trial read-only Markdown retrieval and a separate proposal inbox.
- [ ] Compare a small publisher with vault-memory; evaluate agent runtimes independently.
- [ ] Expected-hash publishing, provenance, expiry, source links, and storage budget.
- [ ] Test conflicting edits and correction propagation.

Acceptance: a user can inspect a synthesis, its source evidence, and the exact proposed edit.

## 3 — Monorepo pilot

- [ ] Private repo inventory and architecture baseline at a recorded commit.
- [ ] Local secret, dependency, and static analysis; redact evidence.
- [ ] Sandboxed code execution policy and commit-to-decision links.
- [ ] Incremental scans, reviewed baselines, and actionable-only alerts.

Acceptance: useful findings cite reproducible evidence; workers cannot reach private memory or production secrets.

## 4 — Roaming and recovery

- [ ] Offline captures, stable event IDs, reconciliation, and visible staleness.
- [ ] Device revocation, independent health monitoring, and backup restoration rehearsal.
- [ ] Recover after simulated loss of a phone and archive node.

## 5 — Bounded initiative

- [ ] Versioned skills and representative evaluations.
- [ ] Approval scopes, expiry, budgets, kill switch, and rollback.
- [ ] Review proposed self-improvements; never self-authorize more privileges.

Acceptance: replacement of the model or agent retains evidence and user-reviewed knowledge; improvement passes evaluations without permission expansion.
