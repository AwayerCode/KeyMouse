# GitHub Repository Settings

## Status

This checklist covers settings that are not stored in the repository and cannot
be treated as complete merely because a file exists. Status is tracked as of
2026-10-19.

The public repository currently has no installable release. The workflow files
define the intended automation, but an administrator must still verify and
enable the settings below in the GitHub UI or API.

## Repository Metadata

- [ ] Keep the repository public only after reviewing the security and licensing
      baseline.
- [ ] Set the About description to a factual pre-alpha description mentioning
      the C++ core and TypeScript/Python bindings.
- [ ] Add stable topics such as `keyboard`, `mouse`, `input`,
      `global-hook`, `input-interception`, `cpp`, `node-api`, `python`,
      `electron`, `windows`, `macos`, `linux`, and `wayland`.
- [ ] Leave the Website field empty until a maintained documentation site and
      final brand name exist.
- [ ] Defer the logo, social preview, and final visual identity until trademark
      and registry verification is complete.
- [ ] Enable Issues.
- [ ] Enable Discussions only when there is capacity to moderate and maintain
      it; otherwise continue directing public support to Issues.

## Access and Identity

- [ ] Require multi-factor authentication for the owner account.
- [ ] Review personal access tokens, SSH keys, deploy keys, GitHub Apps, and
      collaborator access.
- [ ] Create at least one independent administrator before v1.0.
- [ ] Use organization-owned access with named roles if the repository moves to
      an organization.
- [ ] Record a repository owner succession and recovery process.

## Branch and Tag Rules

Create a ruleset targeting `main`:

- [ ] Require a pull request before merging.
- [ ] Require the `Repository checks` status check after the workflow has run
      successfully once.
- [ ] Require conversation resolution.
- [ ] Dismiss stale approvals when new commits are pushed.
- [ ] Require Code Owner review for sensitive paths.
- [ ] Require at least one approval once a second maintainer is available.
- [ ] Block force pushes.
- [ ] Block branch deletion.
- [ ] Require linear history if merge strategy permits it.
- [ ] Limit bypass to recorded break-glass situations; do not use routine admin
      bypass.

Create a release-tag ruleset when the first release is prepared:

- [ ] Protect `v*` tags from update and deletion.
- [ ] Require the release commit to be reachable from `main`.
- [ ] Require signed or verified tags if the release process supports them.

GitHub rulesets are under **Settings > Rules**. Verify that the actual ruleset
matches this list; documenting a rule is not enforcement.

## Actions Policy

- [ ] Set the default `GITHUB_TOKEN` permission to read-only.
- [ ] Allow only required GitHub-owned and reviewed third-party actions,
      including the explicitly approved OpenSSF Scorecard action.
- [ ] Require approval for first-time contributors.
- [ ] Require approval for workflows from forks when appropriate.
- [ ] Do not allow Actions to create or approve pull requests unless a specific
      trusted automation requires it.
- [ ] Keep every external action pinned to a full 40-character commit SHA,
      including Dependabot updates.
- [ ] Review workflow changes as security-sensitive changes.

The repository checks and Scorecard workflows use explicit least-privilege
permissions, but the repository-level policy still needs administrator
verification.

## Security Features

- [ ] Enable Private Vulnerability Reporting:
      <https://github.com/AwayerCode/KeyMouse/security/advisories/new>
- [ ] Enable Dependabot alerts.
- [ ] Enable Dependabot security updates.
- [ ] Enable secret scanning.
- [ ] Enable push protection.
- [ ] Enable CodeQL default or advanced setup once compilable source exists.
- [ ] Review CodeQL language support and build requirements for C++, Python,
      and TypeScript before promising code-scanning coverage.
- [ ] Configure security alert notifications for the owner and future
      maintainers.
- [ ] Verify that the Scorecard workflow can upload SARIF and publish results.
- [ ] Review Scorecard findings as engineering risks, not as proof of security.

Code scanning is intentionally not configured before source code and a real
build entry point exist. A workflow that scans no code would create a false
assurance signal.

## Dependabot

- [ ] Confirm the `github-actions` ecosystem is active.
- [ ] Add `npm`, `pip`, `cargo`, or other ecosystems only after the corresponding
      manifests and lockfiles exist.
- [ ] Require CI and review for dependency updates.
- [ ] Review major updates manually.
- [ ] Remove unused dependency ecosystems promptly.

## Releases and Package Registries

- [ ] Enable immutable releases before publishing release artifacts.
- [ ] Restrict release creation to maintainers and trusted workflows.
- [ ] Configure protected environments for npm and PyPI publishing.
- [ ] Use npm and PyPI Trusted Publishing instead of long-lived API tokens.
- [ ] Produce checksums, provenance/attestations, and an SBOM with release
      artifacts.
- [ ] Publish a supported-platform matrix and known limitations.
- [ ] Confirm the final package name, trademark, maintainer MFA, and repository
      association before uploading any package.

## Community Operations

- [ ] Create labels for platform, binding, capability, type, status, and
      good-first-issue categories.
- [ ] Add a dedicated confidential conduct contact before recruiting external
      contributors.
- [ ] Verify that `@AwayerCode` in `CODEOWNERS` has the required access.
- [ ] Review issue forms and the pull request template after the first real
      implementation lands.
- [ ] Keep `README.md`, support claims, and platform evidence synchronized.

## Verification

After changing repository settings:

1. Open a probe pull request and confirm that the required status check,
   CODEOWNERS review, conversation resolution, and DCO check behave as intended.
2. Confirm that force-pushing and deleting `main` are rejected.
3. Confirm that the secret-scanning and private-reporting links work.
4. Run the Scorecard workflow and inspect both the artifact and code-scanning
   result.
5. Record any unavailable setting, administrator bypass, or accepted risk.

GitHub settings can change independently of this repository. Recheck them before
each public release and whenever repository ownership or access changes.
