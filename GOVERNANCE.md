# Governance

## Current Model

KeyMouse currently uses an explicit single-maintainer, benevolent dictator for
life (BDFL) model. The project owner is the final decision maker for technical,
security, release, licensing, and community matters until this document is
formally changed.

Single-maintainer governance is a bootstrap mechanism, not the target end
state. The project must add at least one independent maintainer and document
shared decision-making before a v1.0 release.

## Roles

### Contributors

Anyone who reports an issue, improves documentation, proposes a design, tests a
platform behavior, or submits a pull request. Contributions are accepted under
`MIT OR Apache-2.0` with a DCO sign-off.

### Maintainers

Maintainers triage issues, review changes, manage releases, and protect the
project's technical and community standards. Permissions are granted only for
the areas a maintainer is expected to own and review.

### Project Owner

The project owner appoints maintainers, resolves deadlocks, controls repository
and release access, and is accountable for security and legal decisions. The
current owner is listed in [MAINTAINERS.md](MAINTAINERS.md).

## Decisions

- Routine changes are decided through issues and pull requests.
- Maintainers seek consensus and use lazy consensus for low-risk decisions.
- If consensus cannot be reached, the project owner makes and records the final
  decision with rationale.
- Changes to public behavior, native ABI, platform support, security policy,
  licensing, release process, or governance require a public issue or
  decision-record pull request before implementation.
- Security reports remain private until coordinated disclosure.

Decisions must consider verified platform evidence, privacy, compatibility,
maintenance cost, and the synchronous native interception invariant. A
maintainer with a material conflict of interest must disclose it and avoid
sole review or decision-making on the affected matter.

## Adding Maintainers

A contributor may be invited as a maintainer after sustained, high-quality
contributions and demonstrated judgment in one or more areas, including:

- Native input implementation and platform-specific recovery behavior.
- Node-API or Python binding and packaging expertise.
- Security review, privacy engineering, or release engineering.
- Community moderation and documentation.

Candidate criteria and scope will be public unless a security or privacy reason
requires a private discussion. The project owner approves the role, permissions,
and review scope. The appointment is recorded in [MAINTAINERS.md](MAINTAINERS.md)
and [.github/CODEOWNERS](.github/CODEOWNERS).

Before v1.0, maintainer onboarding, removal, inactive-maintainer handling, and
succession must be documented and exercised. Release and security access must
not depend on one person's account.

## Releases and Security

The project owner and maintainers may prepare releases, but releases must follow
the documented build, review, provenance, and signing process. A release cannot
be made from an unreviewed working tree. Security embargoes may restrict
technical detail, but not the existence of the policy or the final advisory.

## Conflicts and Enforcement

Code of Conduct enforcement is handled by maintainers not directly involved in
the incident. When no independent maintainer is available, the project owner
must seek an appropriate external reviewer. The private reporting route is
documented in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Licensing Changes

The current license expression is `MIT OR Apache-2.0`. Any future license
change requires a public proposal, a review of contributor rights, and approval
by the project owner. Contributions accepted under the current expression
cannot be unilaterally relicensed contrary to those rights.

## Amendments

Governance changes are proposed through a public pull request or issue. The
project owner approves changes while the single-maintainer model remains in
effect. After additional maintainers are appointed, amendments require
consensus of the maintainers and a public comment period.

## Succession

The project owner must nominate a successor before transferring repository,
package, signing, or security access. If the owner becomes unavailable,
maintainers may pause changes and releases while preserving the repository and
recovering access through GitHub. No contributor receives release or security
authority merely by being a frequent contributor.
