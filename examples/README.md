# Synthetic examples

Every conversation, identity, message, and relationship here is synthetic.

- `conversation.json`: the small neutral input example.
- `demo-bundle.json`: a portable archive of the six demo conversations and their explicit relationships. Restore it into a new private database to explore the bundle format.
- `evidence-note.md`: a draft showing an explicitly supplied interpretation, concrete source revisions, original message roles, and a review checklist.

```sh
python3 -m lamassu --database /tmp/lamassu-restored-demo.sqlite restore examples/demo-bundle.json
python3 -m lamassu --database /tmp/lamassu-restored-demo.sqlite verify
python3 -m lamassu --database /tmp/lamassu-restored-demo.sqlite serve
```

The bundle and note illustrate the evidence contract. They are not model-generated conclusions, provider export fixtures, or records of actual events.
