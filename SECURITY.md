# Security

## Supported versions

Security fixes are applied to the latest tagged release and the current `main` branch.

## Reporting a vulnerability

Use GitHub's private vulnerability-reporting flow when it is available for this repository. Otherwise, open a minimal issue that describes the affected version and impact without including credentials, commercial game assets, title-specific keys, account tokens, license blobs, or exploit-ready private data.

Reports are most useful when they include a synthetic reproducer, the exact command, expected and observed results, and SHA-256 hashes for any public test fixture.

## Trust boundary

This plugin runs inside the DeepSeek Harness process and its bundled Python utilities can read paths supplied by the user. The project-audit and QA commands are read-only with respect to their input trees; report paths are the only requested outputs. Review the source, pin a release, and test with synthetic data before using it on an irreplaceable project.
