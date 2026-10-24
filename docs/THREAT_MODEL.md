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

Plaintext SQLite, input files, and portable bundles; no data-scope authorization, encrypted backup, deletion workflow, autonomous execution, or tamper-proof audit. The loopback workbench has a per-run bearer key, Host/Origin checks, no write endpoints, and a restrictive content-security policy. It is a local development server, not a production remote interface. Local processes, browser extensions, and compromised host accounts are not isolated from private data.

SHA-256 identifies imported bytes but does not authenticate their origin. A process with database access can alter data. Inspection and export check source/projection consistency, while portable restore validates the complete bundle before a transaction applies its changes. Create-only note output avoids overwriting human files, but assumes an owner-controlled directory. The passive repository inventory skips symlinks and reads bounded manifests; it is not a filesystem sandbox or proof of code safety.

## Recovery design requirements

Separate routine backup credentials from retention/pruning credentials. Keep recovery instructions and key recovery material outside the system they recover. Test recovery regularly and after format changes. Two machines in the same home share physical risks.
