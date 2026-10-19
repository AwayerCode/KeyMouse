#!/usr/bin/env python3
"""Require DCO sign-off on every non-merge commit in a pull request."""

from __future__ import annotations

import re
import subprocess
import sys

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SIGNOFF_RE = re.compile(
    r"^Signed-off-by:\s+.+\s+<[^<>\s]+@[^<>\s]+>\s*$",
    re.MULTILINE,
)


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout.decode("utf-8")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: check_dco.py BASE_SHA HEAD_SHA", file=sys.stderr)
        return 2

    base_sha, head_sha = sys.argv[1], sys.argv[2]
    if SHA_RE.fullmatch(base_sha) is None or SHA_RE.fullmatch(head_sha) is None:
        print("base and head must be full lowercase commit SHAs", file=sys.stderr)
        return 2

    commits = [
        line.strip()
        for line in git(
            "rev-list", "--reverse", "--no-merges", f"{base_sha}..{head_sha}"
        ).splitlines()
        if line.strip()
    ]
    if not commits:
        print("No non-merge commits found in the pull request range.")
        return 0

    missing: list[tuple[str, str]] = []
    for commit in commits:
        message = git("show", "-s", "--format=%B", commit)
        if SIGNOFF_RE.search(message) is None:
            subject = message.splitlines()[0] if message.splitlines() else "(no subject)"
            missing.append((commit[:12], subject))

    if missing:
        print("DCO sign-off missing from one or more commits:", file=sys.stderr)
        for short_sha, subject in missing:
            print(f"  - {short_sha} {subject}", file=sys.stderr)
        print(
            "Amend each commit with `git commit --amend -s` or use "
            "`git rebase --signoff <base>`.",
            file=sys.stderr,
        )
        return 1

    print(f"DCO sign-off verified for {len(commits)} non-merge commit(s).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from error
