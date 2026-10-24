# A cautious beginning for codebase analysis

Lamassu now includes a **passive working-copy inventory**. It is an initial building block for the future monorepo pilot, not a vulnerability scanner or autonomous coding agent.

```sh
python3 -m lamassu inspect-repo /private/path/repository --output /private/path/repository-map.json
```

No database is needed. The output path must be new. A report records source-file counts by language and top-level area, selected package manifest metadata, coverage limits, and an optional Git commit hint.

## What it reads

It walks the explicitly selected directory. It counts file paths and extensions, reads bounded regular `package.json` files, and may read plain Git HEAD/ref files. Package scripts and dependency version values are not copied to the report. Source bodies, lockfile contents, hidden files, and selected secret-file types are not read. The scanner does not execute Git, package managers, scripts, builds, tests, or repository instructions. It makes no network requests.

Standard generated directories and symlinks are skipped. The default limit is 5,000 files, with a maximum configurable limit of 100,000, a depth limit of 24, and a directory budget of 20,000. Coverage limits and parse failures are reported. Repository-specific ignore rules are not interpreted. Packed Git refs, worktree Git pointers, and unusual Git layouts may produce no commit hint.

The commit hint is not a snapshot guarantee: a working copy can have uncommitted changes. Source paths, package names, and structure can themselves be confidential. Keep private reports private. The inventory is not a sandbox for an actively hostile filesystem.

## Next stages

1. Select a permitted private monorepo and document its actual languages and build boundaries.
2. Establish reproducible snapshots and reviewed exclusions.
3. Integrate independently evaluated secret, dependency, and static-analysis tools.
4. Record tool/rule versions, coverage, false-positive status, and evidence.
5. Connect meaningful implementation changes to recorded architectural decisions.
6. Run any code execution in isolated workers without personal-archive or production credentials.

The current public test corpus consists of temporary synthetic repositories. No company repository has been scanned by this implementation.
