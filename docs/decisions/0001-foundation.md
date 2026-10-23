# ADR 0001: Evidence first, replaceable agents

Date: 2026-10-24
Status: accepted for the experimental foundation

## Context

The system must survive changes in devices, model providers, and agent frameworks. A public project must remain separate from private deployments and company code.

## Decision

Use Lamassu as a working name and MIT for newly authored project code. Keep original evidence, working memory, and reviewed Markdown syntheses distinct. Start with a Python standard-library archive prototype using SQLite, explicit input validation, and synthetic tests. Add integrations only after evaluating existing implementations. Keep all real data and deployment configuration outside this repository.

## Consequences

The first release is intentionally small. It cannot autonomously act, parse vendor exports, synchronize devices, or secure a production deployment. SQLite gives a simple local starting point; schema migrations and portable exports must precede broader adoption. Obsidian remains optional and third-party components require separate license review. An agent's identity never owns the archive.
