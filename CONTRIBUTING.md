# Contributing

Start with the roadmap and architecture decisions. Discuss a new dependency or trust boundary before implementing it. Use an issue to state the problem, acceptance criteria, data involved, and failure behavior.

Develop on a `codex/` or other descriptive feature branch. Keep pull requests focused. Describe the resulting behavior, tests, and limitations. Never claim an integration works until it has been exercised against supported, documented inputs.

Run `python3 -m unittest discover -s tests -v`. CI exercises supported Python versions. All fixtures must be synthetic, including failures and security examples. Do not attach real chat records or raw security findings to public issues.

Database changes need an explicit version and migration/rollback plan. The prototype currently writes schema version 2 and transactionally migrates version 1. Read-only access refuses migration. Unknown versions are refused.

Development tooling is optional: `uvx ruff@0.14.0 format lamassu tests` and `uvx ruff@0.14.0 check lamassu tests`. Runtime dependencies remain empty. Browser-service tests bind only a temporary loopback port. Never upload a wheel, report, or screenshot containing real user data.
