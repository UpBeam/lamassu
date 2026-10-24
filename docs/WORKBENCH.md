# The guardian workbench

The workbench is a local, read-only interface to the evidence archive. It provides conversation search, a source viewer, an explicit relationship map, and a Markdown draft composer. No model inference, remote API, autonomous execution, or vault synchronization is involved.

## Start with the synthetic demo

From a source checkout with Python 3.10 or newer:

```sh
# Choose a NEW path outside the source checkout.
python3 -m lamassu --database /tmp/lamassu-demo.sqlite demo
python3 -m lamassu --database /tmp/lamassu-demo.sqlite serve
```

The server prints a local access link. Open that complete link in a browser. The link contains a temporary access key in its fragment; keep it private. It changes on each server start. The workbench listens on `127.0.0.1` only. Stop it with Ctrl+C.

If the demo path already exists, choose another path. The demo command deliberately refuses to replace any existing file. It creates six clearly synthetic conversations, eighteen messages, and four explicit relationships.

## A five-minute tour

1. From Overview, select **Offline continuity**. Search finds exact text, not inferred semantic similarity.
2. Inspect a conversation. The source viewer shows speaker roles, original timestamps, the source revision, and the original-bytes digest. Inspection checks that the source and projected messages agree.
3. Open Connections. Select a source node or the names in the relationship list. Each link has a type and an explicitly recorded reason; it is not independent evidence.
4. From a conversation, choose **Create an evidence note**. Write your own proposed understanding. Prepare a preview and download the Markdown draft.
5. Review the draft in an inbox before moving a useful synthesis into your curated vault.

All archive text is displayed as text, never inserted as HTML. Source excerpts in downloaded Markdown are escaped so imported image syntax or HTML does not become active content. The proposed understanding is explicitly authored by the user; it is not an automated summary.

## Existing archives

The database schema is now version 2. Before serving an archive created by the initial version, make a backup and run:

```sh
python3 -m lamassu --database /private/path/archive.sqlite status
python3 -m lamassu --database /private/path/archive.sqlite verify
```

`status` initializes or transactionally migrates a version-1 database, preserving evidence. Read-only commands refuse to initialize or migrate. A database with an unsupported version is refused.

## Limits and boundaries

- The data is plaintext. Use an encrypted disk and independent backups for private experiments.
- Access keys are a local-session boundary, not multi-user authentication or a production authorization system.
- The browser stores its session access key in session storage. The original link can remain in browser history; do not share it.
- No network bind address option is offered. Do not expose the workbench through a reverse proxy, port forwarding, Tailscale Serve, or a public tunnel without a separate security design.
- Other processes with access to the local machine or browser session remain inside the trust boundary. There is no defense against a compromised host.
- Overview lists the most recent 100 source revisions. Search spans the entire archive and returns at most 50 messages; excerpts are limited to 1,200 characters, with full text available in source inspection.
- The diagram shows up to 12 connected source nodes; the relationship list includes up to 250 links. More links remain in the archive.
- Draft downloads do not write to a vault or authorize publication. Browser download locations are controlled by the browser.
- The interface adapts to narrow screens, but remote phone access and disconnected capture are future work.

## Screenshots

The screenshots in `assets/` show synthetic evidence only. They demonstrate the local workbench, not a hosted service.
