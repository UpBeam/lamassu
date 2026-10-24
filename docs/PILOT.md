# First private pilot

Start with a small set of conversations about Lamassu. Keep personal data outside
this public checkout. The current archive and portable bundles are plaintext;
use an encrypted volume and an independent encrypted backup before real intake.
Do not expose the development workbench over Tailscale.

1. Retain the original provider export unchanged in private storage. Start with
   the extracted JSON file, not the ZIP; Lamassu does not extract archives.
2. Run `python -m lamassu preview /absolute/private/export.json`. The command
   reads the file and prints metadata only. A successful preview means the report
   was produced, not that import is supported: check `import_ready` and warnings.
3. Native ChatGPT and Claude adapters are still pending. Do not flatten branches
   or discard attachments to make a file pass neutral-schema validation.
4. For a supported neutral conversation, import into a new private database,
   verify it, export a portable bundle, restore into a second database, and verify
   that restored archive before expanding the pilot. See PORTABILITY.md.
5. Prepare a source-backed draft for an existing private Obsidian inbox. Review
   it manually. Keep originals, databases, bundles, and indexes outside the vault.

Before unattended operation, test recovery from an independent backup and add
correction/suppression controls. No native provider adapter or importer dependency
has been selected or validated against a real personal export yet.

For the home machines, first establish working Tailscale connectivity, identify
the intended hosts, and inspect OS, free storage, memory, service ownership, and
backup status. Service installation and model cleanup are separate changes.

For mWater, select the exact checkout and begin with the passive `inspect-repo`
inventory. Keep reports private. Inventory does not execute code and is not a
security scan.
