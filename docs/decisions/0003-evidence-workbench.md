# ADR 0003: Read-only workbench and portable evidence

Date: 2026-10-24
Status: accepted for the experimental prototype

## Context

The initial archive needs to demonstrate an end-to-end path from original evidence to a reviewed note without prematurely coupling it to a model, vault plugin, or production agent runtime. Repository ownership now belongs to UpBeam.

## Decision

Add a local read-only workbench, source inspection, explicit record relationships, verified portable export/restore, create-only Markdown draft output, and a bounded passive repository inventory. Use only the Python standard library at runtime. Browser assets are packaged locally with no CDN, remote font, analytics, or model API.

Schema version 2 adds relationships and an index. Initialize and migrate in an explicit transaction under a write lock. Read-only operations do not create databases or migrate schemas. Preserve the v1 source identity function and original bytes.

The workbench binds to IPv4 loopback only, checks Host and Origin, requires a random bearer key for archive APIs, sets a restrictive content-security policy, and offers no write endpoints. Client note preparation is a local download; CLI note output creates a new generated filename and never overwrites a human note. Source excerpts are escaped in Markdown. The user supplies the interpretation explicitly.

## Consequences

The prototype is more useful and testable without granting autonomous powers. It remains plaintext, single-user, and unsuitable for remote exposure or broad sensitive-data intake. Model synthesis, provider adapters, secure remote access, expected-hash updates to curated notes, deletion/suppression, and real code security scanning remain separate milestones.

The package remains alpha and is not published to a package registry. The local service uses Python's development HTTP server, not a production server. Portable bundles are bounded and unencrypted. Integrity checks detect inconsistent bytes/projections but do not authenticate authors or resist a database owner who alters all related evidence consistently.
