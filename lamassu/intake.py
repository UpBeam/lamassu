"""Read-only intake preflight. No conversion, extraction, or archive writes."""

import hashlib

from .archive import MAX_BUNDLE_BYTES, _json, parse


def preview(raw):
    value = _json(raw, limit=MAX_BUNDLE_BYTES)
    report = dict(
        schema="lamassu.intake-preview.v1",
        sha256=hashlib.sha256(raw).hexdigest(),
        bytes=len(raw),
        format="unrecognized-json",
        import_ready=False,
        conversations=None,
        message_entries=None,
        warnings=[],
    )
    if isinstance(value, dict) and value.get("schema") == "lamassu.conversation.v1":
        record = parse(raw)
        report.update(
            format="lamassu.conversation.v1",
            import_ready=True,
            conversations=1,
            message_entries=len(record["messages"]),
        )
    elif (
        isinstance(value, list)
        and value
        and all(
            isinstance(c, dict) and isinstance(c.get("mapping"), dict) for c in value
        )
    ):
        nodes = [node for c in value for node in c["mapping"].values()]
        if not all(isinstance(node, dict) for node in nodes):
            raise ValueError("invalid mapping entries")
        report.update(
            format="chatgpt-shaped-json",
            conversations=len(value),
            message_entries=sum(isinstance(n.get("message"), dict) for n in nodes),
        )
        report["warnings"].append(
            "Structural recognition only. Branches, attachments, tool messages, and "
            "timestamps have not been validated; no native import is available."
        )
    elif (
        isinstance(value, list)
        and value
        and all(
            isinstance(c, dict) and isinstance(c.get("chat_messages"), list)
            for c in value
        )
    ):
        report.update(
            format="claude-shaped-json",
            conversations=len(value),
            message_entries=sum(len(c["chat_messages"]) for c in value),
        )
        report["warnings"].append(
            "Structural recognition only. Content blocks, attachments, authorship, "
            "and timestamps have not been validated; no native import is available."
        )
    else:
        report["warnings"].append("No supported conversation format recognized.")
    return report
