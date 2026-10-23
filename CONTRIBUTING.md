# Contributing

Start with the roadmap and architecture decisions. Discuss a new dependency or trust boundary before implementing it. Use an issue to state the problem, acceptance criteria, data involved, and failure behavior.

Develop on a `codex/` or other descriptive feature branch. Keep pull requests focused. Describe the resulting behavior, tests, and limitations. Never claim an integration works until it has been exercised against supported, documented inputs.

Run `python3 -m unittest discover -s tests -v`. CI exercises supported Python versions. All fixtures must be synthetic, including failures and security examples. Do not attach real chat records or raw security findings to public issues.

Database changes need an explicit version and migration/rollback plan. The prototype currently supports schema version 1 only and refuses other versions.
