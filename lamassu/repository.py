"""Bounded passive repository inventory. Never runs code or reads source bodies."""

import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path

SKIP_DIRS = {
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "target",
    "__pycache__",
    "venv",
    "env",
    "site-packages",
}
SKIP_FILES = {
    "credentials",
    "id_rsa",
    "id_ed25519",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "uv.lock",
    "poetry.lock",
}
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keystore", ".sqlite", ".db"}
LANGUAGES = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".c": "C/C++",
    ".cpp": "C/C++",
    ".h": "C/C++",
    ".html": "HTML",
    ".css": "CSS",
    ".sql": "SQL",
    ".sh": "Shell",
}
MANIFEST_LIMIT = 256 * 1024


def _regular_read(path, maximum):
    """Read a bounded regular file without following its final symlink."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    import stat

    with os.fdopen(fd, "rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise ValueError("not a regular file")
        raw = source.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("file exceeds inventory limit")
    return raw


def _commit_hint(root):
    git = root / ".git"
    if not git.is_dir() or git.is_symlink():
        return None
    try:
        head = _regular_read(git / "HEAD", 1024).decode("ascii").strip()
        if head.startswith("ref: "):
            ref = head[5:]
            if not ref.startswith("refs/") or ".." in ref or "\\" in ref:
                return None
            path = git / ref
            if any(
                parent.is_symlink()
                for parent in [path, *path.parents]
                if parent != git.parent
            ):
                return None
            head = _regular_read(path, 1024).decode("ascii").strip()
        return head if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head) else None
    except (OSError, ValueError, UnicodeError):
        return None


def inspect_repository(root, max_files=5000):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("repository must be an existing directory, not a symlink")
    if type(max_files) is not int or not 1 <= max_files <= 100000:
        raise ValueError("max-files must be 1 to 100000")
    root = root.resolve()
    languages, extensions, areas = Counter(), Counter(), Counter()
    manifests, skipped, errors = [], Counter(), []
    files = 0
    directories = 0
    truncated = False

    def on_error(error):
        errors.append("directory could not be read")

    for directory, dirs, names in os.walk(
        root, topdown=True, onerror=on_error, followlinks=False
    ):
        base = Path(directory)
        directories += 1
        if directories > 20000:
            truncated = True
            break
        if len(base.relative_to(root).parts) >= 24:
            if dirs:
                truncated = True
            dirs[:] = []
        kept = []
        for name in sorted(dirs):
            if name.startswith(".") or name in SKIP_DIRS or (base / name).is_symlink():
                skipped["directories"] += 1
            else:
                kept.append(name)
        dirs[:] = kept
        for name in sorted(names):
            path = base / name
            if (
                name.startswith(".")
                or name in SKIP_FILES
                or path.suffix.lower() in SECRET_SUFFIXES
                or path.is_symlink()
            ):
                skipped["files"] += 1
                continue
            if files >= max_files:
                truncated = True
                break
            files += 1
            relative = path.relative_to(root).as_posix()
            extension = path.suffix.lower() or "(no extension)"
            extensions[extension] += 1
            if extension in LANGUAGES:
                languages[LANGUAGES[extension]] += 1
            areas[relative.split("/")[0] if "/" in relative else "(root)"] += 1
            if name == "package.json":
                try:
                    raw = _regular_read(path, MANIFEST_LIMIT)
                    package = json.loads(raw)
                    if not isinstance(package, dict):
                        raise ValueError("manifest is not an object")
                    value = dict(path=relative, sha256=hashlib.sha256(raw).hexdigest())
                    package_name = package.get("name")
                    if isinstance(package_name, str) and len(package_name) <= 214:
                        value["name"] = package_name
                    for field in (
                        "dependencies",
                        "devDependencies",
                        "peerDependencies",
                    ):
                        dependencies = package.get(field, {})
                        # Counts only: dependency values can contain private URLs or tokens.
                        value[field] = (
                            len(dependencies)
                            if isinstance(dependencies, dict)
                            else None
                        )
                    value["private"] = package.get("private") is True
                    manifests.append(value)
                except (OSError, ValueError, RecursionError):
                    errors.append(f"{relative}: manifest could not be inventoried")
        if truncated:
            break
    return dict(
        schema="lamassu.repository-map.v1",
        mode="passive-working-copy",
        repository=root.name,
        commit_hint=_commit_hint(root),
        files_counted=files,
        directories_visited=directories,
        truncated=truncated,
        languages=dict(sorted(languages.items())),
        extensions=dict(sorted(extensions.items())),
        areas=dict(sorted(areas.items())),
        packages=manifests,
        skipped=dict(skipped),
        errors=errors,
        limitations=[
            "Working copy may differ from commit_hint; dirty status is not checked.",
            "Not a vulnerability scan or architectural proof.",
            "Standard exclusions only; repository-specific ignore rules are not interpreted.",
            "Only package.json contents are inspected; source bodies, scripts, secrets, and lockfiles are not read.",
            "Metadata and paths can still be sensitive. Keep private repository reports private.",
            "A local inventory is not a hostile-filesystem sandbox.",
        ],
    )
