# Portable evidence and recovery

The archive is useful only if its evidence can survive the software that created it. The prototype supports a bounded JSON bundle containing original input bytes, their identities and digests, original import timestamps, and explicit relationships.

## Export and restore

```sh
python3 -m lamassu --database /private/path/archive.sqlite verify
python3 -m lamassu --database /private/path/archive.sqlite export /private/path/archive-bundle.json
python3 -m lamassu --database /private/path/restored.sqlite restore /private/path/archive-bundle.json
python3 -m lamassu --database /private/path/restored.sqlite verify
```

The export writes to an owner-only temporary file and atomically publishes it with a no-replace hard link. An existing file or symlink is never replaced; a failed write leaves no partial final file. This requires an owner-controlled directory on a filesystem supporting hard links. Sources are base64 encoded to preserve their exact bytes. Export first verifies the stored source identities and projected messages. Restore validates the entire bundle before inserting records or relationships, then applies the changes in one transaction. An interruption during insertion rolls back that transaction. Repeating a restore is idempotent for matching source records and relationships.

On a new destination, a successful restore/export round trip is byte-identical to the bundle. Restoring into an existing archive merges the evidence; it does not remove destination records or change the import timestamp of a matching record already there. Bundles are self-contained: relationship endpoints must appear in the same bundle. Database initialization or migration is separate from the restore transaction; a rejected restore may leave an empty initialized database.

## Format and limits

- Schema: `lamassu.bundle.v1`.
- Required top-level fields: `schema`, `records`, `links`.
- Each record has `record_id`, `digest`, `imported_at`, and `raw_base64`.
- Each link has `link_id`, `source_id`, `target_id`, `relation`, `reason`, and `created_at`.
- The prototype limits a bundle to 64 MiB, 10,000 source revisions, and 10,000 relationships. Each original conversation is limited to 8 MiB.
- Original input formatting is significant: a reformatted export is a new revision, even if its meaning is unchanged.
- The archive has no concept of current truth. Search includes superseded or conflicting revisions.

A digest identifies bytes. It is not a signature or proof of who authored a source. Someone with database access can alter the archive, and a sufficiently coordinated alteration cannot be detected by an internal digest check alone. Use independent copies and a future authenticated provenance design where appropriate.

## What a bundle is not

This is not an encrypted backup, a hosted sync protocol, or a deletion mechanism. Private bundles contain full transcripts. Keep them outside the source checkout and away from public issues and artifact uploads. Losing a source and every independent backup cannot be repaired by reconstructing an embedding index.

Before broad real-data intake, implement correction, suppression against accidental re-import, derived-memory invalidation, and a documented backup retention policy. Those remain open work.
