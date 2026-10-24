# ADR 0004: Intake preflight before provider adapters

Date: 2026-10-24
Status: accepted for the experimental prototype

Add a read-only `preview` command that does not require or open an archive. Its
versioned JSON report contains a SHA-256 fingerprint, byte size, structural format
hint, counts, warnings, and an explicit import-readiness flag. No conversation text,
titles, identifiers, or filenames are included in the report. Input is bounded to
64 MiB; duplicate JSON keys are rejected.

Only validated neutral v1 conversations are import-ready. ChatGPT mapping arrays
and Claude chat-message arrays are recognized as structural hints, not verified
provider compatibility. Counts include mapping message nodes across branches,
not a selected conversational path. Claude counts list entries, even when the
entries are not valid messages. Empty arrays cannot identify a provider.

The command does not convert or preserve native exports in the archive. ZIP files,
attachments, completeness validation, native adapters, and provenance-preserving
conversion remain unimplemented. Original files must be retained independently.
No storage migration or network access is introduced.
