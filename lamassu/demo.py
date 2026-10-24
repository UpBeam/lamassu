"""Synthetic evidence corpus, never a representation of anyone's real history."""

import json

CONVERSATIONS = [
    (
        "field-notes",
        "2026-10-01",
        [
            (
                "user",
                "I need my project notes when travelling, even when the home server is offline. Keep a small reviewed brief on the laptop and phone.",
            ),
            (
                "assistant",
                "Proposal: separate offline curated notes from the full archive. Reconcile new captures with stable event identifiers when connectivity returns.",
            ),
            (
                "user",
                "Agreed. A stale brief should display its review date. Never imply the full archive was searched while offline.",
            ),
        ],
    ),
    (
        "archive-design",
        "2026-10-03",
        [
            (
                "user",
                "The archive should preserve original conversation bytes, speaker roles, and revisions. My memory must outlive any particular model.",
            ),
            (
                "assistant",
                "Use independent evidence storage and reconstructible indexes. A digest identifies bytes, but it does not authenticate the author.",
            ),
            (
                "user",
                "Keep working memory separate from reviewed Markdown. A generated inference must retain links to original evidence.",
            ),
        ],
    ),
    (
        "permission-boundaries",
        "2026-10-06",
        [
            (
                "user",
                "The guardian can prepare drafts and check health. Sending messages, publishing, and granting access need explicit authority.",
            ),
            (
                "assistant",
                "Enforce those permissions outside the model. Imported chats and repository instructions are untrusted content, not permission changes.",
            ),
            (
                "tool",
                "Synthetic fixture only: no services were contacted and no real permissions were changed.",
            ),
        ],
    ),
    (
        "code-review-plan",
        "2026-10-09",
        [
            (
                "user",
                "A monorepo scan should explain the component map, dependency changes, and risks at an exact commit. Do not run build scripts during intake.",
            ),
            (
                "assistant",
                "Keep static findings distinct from model interpretations. Use isolated workers for code execution and redact potential credentials before indexing reports.",
            ),
            (
                "user",
                "A scan worker receives a checkout and narrow task context. It must not receive my personal archive or backup administration credentials.",
            ),
        ],
    ),
    (
        "recovery-rehearsal",
        "2026-10-12",
        [
            (
                "user",
                "A second machine in the same home is not enough protection. I want an independent encrypted backup and a recovery runbook.",
            ),
            (
                "assistant",
                "Test restoring onto an empty machine. Separate normal backup writing from retention and deletion authority.",
            ),
            (
                "user",
                "Preserve the original evidence in a portable format. Rebuild indexes after restore and compare record digests.",
            ),
        ],
    ),
    (
        "reviewed-memory",
        "2026-10-15",
        [
            (
                "user",
                "My Markdown vault should hold project maps, decisions and their reasons, and reusable lessons. It should not become a transcript dump.",
            ),
            (
                "assistant",
                "Prepare a draft with concrete evidence links. Keep uncertain interpretations labeled. Reviewed preferences can expire or be superseded.",
            ),
            (
                "user",
                "Only publish useful changes. Frequent rewrites consume attention and sync history. Keep model files and embeddings outside the vault.",
            ),
        ],
    ),
]


def populate(archive):
    ids = {}
    for name, day, messages in CONVERSATIONS:
        record = dict(
            schema="lamassu.conversation.v1",
            provider="synthetic",
            external_id=name,
            messages=[
                dict(
                    id=f"m{i + 1}",
                    role=role,
                    text=text,
                    at=f"{day}T12:{i:02d}:00+00:00",
                )
                for i, (role, text) in enumerate(messages)
            ],
        )
        result = archive.ingest(json.dumps(record, indent=2).encode())
        ids[name] = result["record_id"]
    for source, target, relation, reason in [
        (
            "reviewed-memory",
            "archive-design",
            "derived-from",
            "This synthetic design note develops the archive/curated-memory distinction.",
        ),
        (
            "recovery-rehearsal",
            "archive-design",
            "supports",
            "Portable evidence enables a restore rehearsal.",
        ),
        (
            "code-review-plan",
            "permission-boundaries",
            "implements",
            "The proposed worker boundary applies the recorded permission principle.",
        ),
        (
            "reviewed-memory",
            "field-notes",
            "continues",
            "Curated notes can provide a small offline working set.",
        ),
    ]:
        archive.link(ids[source], ids[target], relation, reason)
    return archive.stats()
