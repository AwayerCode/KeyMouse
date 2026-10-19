# Security Policy

KeyMouse handles system-global keyboard and mouse input. Security and privacy
defects can affect every application on a user's machine, so please report them
privately.

## Project Status

KeyMouse is pre-alpha and has no released package or supported binary. The
repository currently contains project decisions, research, and repository
automation only.

## Supported Versions

| Version | Security support |
| --- | --- |
| `main` | Best-effort security fixes while the project remains pre-alpha |
| Tagged releases | None; no releases have been published |

This table will be replaced with a release support policy before the first
public release.

## Reporting a Vulnerability

Use GitHub Private Vulnerability Reporting:

<https://github.com/AwayerCode/KeyMouse/security/advisories/new>

Do not open a public issue for a suspected vulnerability and do not attach
unredacted keystroke logs, pointer traces, window titles, application content,
credentials, personal information, or production configuration.

If the private advisory form is unavailable, contact the project owner through
the private contact method published on the
[@AwayerCode GitHub profile](https://github.com/AwayerCode). Do not disclose
the issue publicly before a fix and disclosure plan are agreed.

The maintainer aims to acknowledge a complete report within three business
days and provide an initial triage decision within ten business days. These are
best-effort targets, not warranties or a bug bounty program.

Please include:

- Affected commit, platform and architecture.
- KeyMouse version, runtime version, and backend.
- Required privileges, permissions, and configuration.
- Reproduction steps and a minimal proof of concept.
- Expected and actual impact.
- Whether the report may be credited publicly.

## Privacy Invariant

KeyMouse does not log, persist, or upload keystrokes, pointer movement, window
titles, application content, or derived input profiles by default. Diagnostics
and telemetry, if ever introduced, must be opt-in, documented, bounded,
inspectable, and disabled when consent cannot be established. A feature that
cannot meet this invariant must not ship as part of KeyMouse.

## Security Design Baseline

Implementation is expected to:

- Keep interception decisions synchronous and inside the native input path.
- Use bounded queues and explicit overflow behavior on every language or IPC
  boundary.
- Return a typed error when a required invariant cannot be maintained, and
  document that operating-system hooks may fail open rather than claiming
  guaranteed interception.
- Validate rule snapshots, configuration, IPC messages, and persisted state
  before use.
- Apply least privilege and never request broader permissions than a backend
  genuinely requires.
- Redact sensitive data from logs, crash reports, test fixtures, and CI
  artifacts.
- Pin CI dependencies, minimize workflow token permissions, and produce
  reviewable provenance for release artifacts.
- Treat hook injection, privilege escalation, driver loading, update
  integrity, rule bypass, event-loop starvation, and recovery after suspend or
  lock as explicit threat-model items.
- Add sanitizers, fuzzing, static analysis, and platform integration tests when
  corresponding native code exists.

These are requirements for future implementation. The current repository does
not yet provide the corresponding runtime guarantees.

## Disclosure

The maintainer will coordinate validation, remediation, release timing, and
public advisory content with the reporter. The target is to agree on a
disclosure date within 90 days, sooner when a fix is available and users need
mitigation. Complex platform or supply-chain issues may require more time; the
reason will be communicated in the private advisory.

## No Bug Bounty

The project does not currently offer monetary rewards. Good-faith reports are
still valued and will be credited when requested and appropriate.
