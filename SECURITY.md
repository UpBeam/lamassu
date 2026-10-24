# Security

Lamassu is pre-alpha and has not received an independent security audit. Do not expose its database, bundles, or workbench to the public internet. Use synthetic data while evaluating it. Broad personal-data intake should wait for correction, deletion/suppression, and retention workflows.

## Implemented boundaries

The archive stores plaintext evidence locally. Imports validate a bounded neutral format and do not execute content. Newly created database and CLI output files use owner-only permissions where supported; existing file permissions are not changed. These measures do not replace encrypted storage.

The optional workbench binds to IPv4 loopback only. Its read-only archive APIs require a per-run access key and check the request Host and Origin. Browser assets are local and use a restrictive content-security policy. Imported text is rendered as text, and evidence excerpts are escaped in Markdown drafts. There are no server-side write endpoints.

The session link and local browser session can expose data to anyone who possesses them. Local processes, browser extensions, compromised devices, and people with filesystem access remain inside the trust boundary. This is not multi-user authentication or remote-service security. Do not place the workbench behind a tunnel, reverse proxy, or Tailscale Serve without a separate reviewed design.

CLI draft publication and export are atomic and create-only on filesystems supporting hard links. They refuse to replace an existing file or follow a final destination symlink. The parent directory is owner-controlled; this is not a sandbox against malicious filesystem races. The passive repository inventory uses bounded reads and standard exclusions but is not a vulnerability scanner or a hostile-filesystem sandbox.

Digest verification detects inconsistent evidence and projected messages; it does not prove authorship or resist coordinated changes by a database owner. Keep independent backups and test restoration. Portable bundles contain full plaintext conversations.

## Reporting

Use this repository's private vulnerability reporting facility if enabled. If it is unavailable, open a public issue asking for a private reporting channel, without exploit details, secrets, personal records, or sensitive code. A dedicated reporting address and response commitments are pending before any hosted release.

Only the current development revision is maintained. Include the revision, synthetic reproduction, impact, and a proposed mitigation where available. See [the threat model](docs/THREAT_MODEL.md) and [workbench limits](docs/WORKBENCH.md).
