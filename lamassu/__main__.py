import argparse
import json
import sqlite3
from pathlib import Path
from .archive import Archive, MAX_BYTES, parse


def main():
    parser = argparse.ArgumentParser(description='Lamassu experimental local archive')
    parser.add_argument('--database', required=True, type=Path)
    sub = parser.add_subparsers(dest='command', required=True)
    intake = sub.add_parser('import')
    intake.add_argument('file', type=Path)
    search = sub.add_parser('search')
    search.add_argument('query')
    search.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    archive = None
    try:
        raw = None
        if args.command == 'import':
            with args.file.open('rb') as source:
                raw = source.read(MAX_BYTES + 1)
            parse(raw)
        archive = Archive(args.database)
        result = archive.ingest(raw) if raw is not None else archive.search(args.query, args.limit)
        print(json.dumps(result, ensure_ascii=True, indent=2))
    except (OSError, ValueError, sqlite3.Error) as exc:
        parser.exit(2, f'lamassu: {exc}\n')
    finally:
        if archive is not None:
            archive.close()


if __name__ == '__main__':
    main()
