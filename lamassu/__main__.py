"""Explicit local operations; no credentials or background automation."""

import argparse
import json
import sqlite3
from pathlib import Path
from .archive import Archive, MAX_BYTES, MAX_BUNDLE_BYTES, RELATIONS, parse
from .notes import publish_draft, write_new


def main():
    parser = argparse.ArgumentParser(
        description="Lamassu — evidence, memory, and bounded authority"
    )
    parser.add_argument(
        "--database",
        type=Path,
        help="private SQLite archive path; required except for inspect-repo",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    intake = sub.add_parser("import", help="import a neutral v1 conversation")
    intake.add_argument("file", type=Path)
    search = sub.add_parser(
        "search", help="literal Unicode-aware search across all revisions"
    )
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    sub.add_parser("status", help="initialize/migrate archive and show counts")
    inspect = sub.add_parser(
        "inspect-repo", help="passive working-copy inventory; no code execution"
    )
    inspect.add_argument("directory", type=Path)
    inspect.add_argument("--output", type=Path, required=True)
    inspect.add_argument("--max-files", type=int, default=5000)
    sub.add_parser("verify", help="check bytes, identities, and message projections")
    show = sub.add_parser("show", help="inspect one source revision")
    show.add_argument("record_id")
    export = sub.add_parser(
        "export", help="create a portable bundle without replacing a file"
    )
    export.add_argument("file", type=Path)
    restore = sub.add_parser(
        "restore", help="validate and atomically restore a portable bundle"
    )
    restore.add_argument("file", type=Path)
    link = sub.add_parser("link", help="record an explicit user-authored relationship")
    link.add_argument("source_id")
    link.add_argument("relation", choices=sorted(RELATIONS))
    link.add_argument("target_id")
    link.add_argument("--reason", required=True)
    draft = sub.add_parser(
        "draft", help="write a source-backed Markdown draft into an existing inbox"
    )
    draft.add_argument("--record", action="append", required=True)
    draft.add_argument("--title", required=True)
    draft.add_argument(
        "--statement",
        required=True,
        help="your proposed understanding; no AI generation",
    )
    draft.add_argument("--inbox", type=Path, required=True)
    sub.add_parser(
        "demo", help="create a new archive containing synthetic conversations only"
    )
    serve = sub.add_parser("serve", help="start a loopback-only, read-only workbench")
    serve.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.command != "inspect-repo" and args.database is None:
        parser.error("--database is required for this command")
    try:
        if args.command == "inspect-repo":
            from .repository import inspect_repository

            report = inspect_repository(args.directory, args.max_files)
            raw_report = (
                json.dumps(report, ensure_ascii=True, indent=2).encode() + b"\n"
            )
            write_new(args.output, raw_report)
            print(
                json.dumps(
                    dict(
                        path=str(args.output),
                        files_counted=report["files_counted"],
                        truncated=report["truncated"],
                    )
                )
            )
            return
        if args.command == "serve":
            from .server import serve as run_server

            run_server(args.database, args.port)
            return
        if args.command == "demo" and args.database.exists():
            raise ValueError(
                "demo requires a new database path; existing data is never replaced"
            )
        raw = None
        if args.command in ("import", "restore"):
            maximum = MAX_BYTES if args.command == "import" else MAX_BUNDLE_BYTES
            with args.file.open("rb") as source:
                raw = source.read(maximum + 1)
            if len(raw) > maximum:
                raise ValueError("input exceeds size limit")
            if args.command == "import":
                parse(raw)
        readonly = args.command in ("search", "show", "verify", "export", "draft")
        with Archive(args.database, readonly=readonly) as archive:
            if args.command == "import":
                result = archive.ingest(raw)
            elif args.command == "search":
                result = archive.search(args.query, args.limit)
            elif args.command == "status":
                result = archive.stats()
            elif args.command == "verify":
                result = archive.verify()
                if not result["ok"]:
                    print(json.dumps(result, indent=2))
                    parser.exit(1)
            elif args.command == "show":
                result = archive.get(args.record_id)
            elif args.command == "export":
                bundle = archive.export()
                write_new(args.file, bundle)
                result = dict(path=str(args.file), bytes=len(bundle))
            elif args.command == "restore":
                result = archive.restore(raw)
            elif args.command == "link":
                result = archive.link(
                    args.source_id, args.target_id, args.relation, args.reason
                )
            elif args.command == "draft":
                result = publish_draft(
                    archive, args.inbox, args.record, args.title, args.statement
                )
            elif args.command == "demo":
                from .demo import populate

                result = populate(archive)
        print(json.dumps(result, ensure_ascii=True, indent=2))
    except (OSError, ValueError, sqlite3.Error) as exc:
        parser.exit(2, f"lamassu: {exc}\n")


if __name__ == "__main__":
    main()
