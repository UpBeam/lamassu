# Threat model

This is a design target, not a claim that mitigations are implemented.

| Threat | Intended boundary | Verification before deployment |
| --- | --- | --- |
| Instructions inside imported chats or code | Content is data; external permission gateway enforces scope | Injection fixtures cannot authorize actions |
| Compromised scan worker | Isolated checkout, no private archive credentials, bounded network and resources | Worker cannot read vault, host secrets, or backups |
| Lost travel device | Device revocation, encrypted disk, limited cached data and credentials | Revoke a test device and recover from another |
| Home outage or hardware loss | Offline briefs and independent encrypted backup | Restore onto an empty replacement machine |
| Compromised archive writer | Restricted writes and append-only backup destination where supported | Writer cannot prune or overwrite protected backups |
| Model-provider disclosure | Local processing by default; explicit data routing policy | Observe outbound traffic and verify task context |
| Memory poisoning and inference loops | Original evidence, authorship, confidence and review status | Derived repetition never upgrades source trust |
| Conflicting edits | Expected-hash publishing and visible conflicts | Concurrent human edit is preserved |
| Supply-chain compromise | Pinned reviewed dependencies and sandboxed execution | Upgrade and rollback rehearsal |
| Growing data footprint | Quotas, retention, disposable cache inventory | Pressure never deletes original evidence |

## Current prototype limits

Plaintext SQLite and input files; no user authentication, service isolation, access policy, durable backup, redaction, deletion workflow, or tamper-proof audit. SHA-256 detects identity of imported bytes but does not authenticate their origin. An owner or process with database access can modify it. Import limits reduce accidental resource exhaustion but are not hostile-input isolation. SQLite is a local single-node choice, not a distributed sync mechanism.

## Recovery design requirements

Separate routine backup credentials from retention/pruning credentials. Keep recovery instructions and key recovery material outside the system they recover. Test recovery regularly and after format changes. Two machines in the same home share physical risks.
