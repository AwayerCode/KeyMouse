# Contributing to KeyMouse

Thank you for helping improve KeyMouse. The project is currently pre-alpha:
there is no installable release, public API, build entry point, or automated
platform test suite yet. Documentation, API design, platform research, threat
modeling, and carefully scoped prototypes are the most useful contributions at
this stage.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Before You Start

- Read [README.md](README.md) and the relevant research in
  [docs/research.md](docs/research.md).
- Search existing issues and pull requests before opening a new one.
- Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).
  Never disclose a suspected vulnerability in a public issue.
- Do not post raw keystroke logs, pointer traces, window titles, application
  content, credentials, or other sensitive input data in an issue or pull
  request.

## Useful Contributions

- Source-verified research about Windows, macOS, Linux X11, or Wayland input
  behavior, including exact versions, configuration, and observed limitations.
- Event-model, rule-snapshot, error, lifecycle, and native ABI proposals that
  preserve the synchronous native interception invariant.
- Reproducible platform experiments with permission, recovery, hot-plug,
  suspend, lock-screen, layout, and input-method evidence.
- Documentation, diagrams, accessibility improvements, and test fixtures that
  contain no private user input.
- Build, packaging, compatibility, and supply-chain work once implementation
  entry points exist.

Do not present a capability as supported for a platform without evidence from
that platform. Global listening, shortcut registration, selective
interception, and event replacement are separate capabilities.

## Licensing and Sign-Off

KeyMouse is licensed under `MIT OR Apache-2.0`. By submitting a contribution,
you agree that it may be distributed under both license options, at the
recipient's choice.

Every non-merge commit in a pull request must include a Developer Certificate
of Origin sign-off:

```text
Signed-off-by: Full Name <email@example.org>
```

Create the sign-off with:

```sh
git commit -s
```

The sign-off certifies that you have the right to submit the contribution
under the project's license. See the
[Developer Certificate of Origin](https://developercertificate.org/) for the
full statement. The project does not currently require a contributor license
agreement.

You retain copyright in your contribution. Do not copy code, data, assets, or
generated content from another project unless its license is compatible and
the source and license are documented in the pull request. You are responsible
for reviewing and testing any AI-assisted contribution before submission.

## Pull Requests

Keep changes focused and explain why they are needed. A pull request should:

- State the user problem, current behavior, and proposed behavior.
- Separate verified facts from assumptions and planned work.
- List the platforms and runtime versions actually tested.
- Include reproducible tests when implementation code exists.
- Update user-facing documentation and [CHANGELOG.md](CHANGELOG.md) when the
  change affects behavior or project policy.
- Describe privacy, security, compatibility, and migration impact.
- Include a DCO sign-off on every non-merge commit.

Native input changes must not wait for JavaScript, Python, or another language
runtime to make an interception decision. Changes must define ownership,
threading, shutdown, failure recovery, and behavior when a required permission
is unavailable.

## Review

Maintainers review contributions for correctness, security, privacy,
maintainability, platform boundaries, and consistency with the documented
scope. Review is best effort. A passing CI run does not establish that a global
input feature works on a real system.

Questions about this process can be raised through [SUPPORT.md](SUPPORT.md).
