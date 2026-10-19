## Summary

Describe the problem and the smallest change that addresses it.

## Scope and Evidence

- Capability affected: listen / register / intercept / replace / repository
- Platforms and architectures tested:
- Runtime and versions, if applicable:
- Permission or privilege state:
- Source revisions or external references used:

Separate verified behavior from assumptions and planned work. Do not claim
platform support without real-system evidence.

## Validation

List the commands and manual checks that were actually run. If no build or
runtime test exists yet, state that explicitly.

- [ ] `python3 .github/scripts/check_repository.py`
- [ ] Relevant unit, replay, or platform tests
- [ ] Documentation and internal links checked
- [ ] Security and privacy impact reviewed

## Compatibility and Risk

- Public API, event semantics, or native ABI impact:
- Hook lifecycle, permissions, suspend, lock-screen, or recovery impact:
- Rollback or failure behavior:
- Known limitations:

## Licensing and Privacy

- [ ] Every non-merge commit has a DCO `Signed-off-by` line.
- [ ] I agree that this contribution is licensed under `MIT OR Apache-2.0`.
- [ ] I did not copy incompatible code, data, assets, or generated content.
- [ ] This change contains no credentials, raw input data, window titles,
      application content, or other sensitive user information.
- [ ] I reviewed and tested any AI-assisted content included in this change.

## Checklist

- [ ] The change is focused and documented.
- [ ] Public capability claims match current evidence.
- [ ] `CHANGELOG.md` is updated when behavior or policy changes.
- [ ] Security-sensitive details will be coordinated privately, not discussed
      in this public pull request.
