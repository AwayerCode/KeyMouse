#!/usr/bin/env python3
"""Run repository checks that do not require a project build."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PATHS = (
    "AGENTS.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "LICENSE",
    "LICENSE-APACHE-2.0",
    "LICENSE-MIT",
    "MAINTAINERS.md",
    "NOTICE",
    "README.md",
    "SECURITY.md",
    "SUPPORT.md",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/pull_request_template.md",
    ".github/workflows/repository-checks.yml",
    ".github/workflows/scorecard.yml",
    "docs/open-source-strategy.md",
    "docs/repository-settings.md",
    "docs/research.md",
)

MARKDOWN_LINK_RE = re.compile(
    r"!?\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^)\s]+))(?:\s+[^)]*)?\)"
)
CONFLICT_START_RE = re.compile(r"^<<<<<<<(?: |$)")
CONFLICT_END_RE = re.compile(r"^>>>>>>>(?: |$)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
ACTION_USE_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*['\"]?([^'\"\s#]+)")
EXTERNAL_TARGET_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def git_files() -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git ls-files failed: {message}")

    files: list[Path] = []
    for raw_name in result.stdout.split(b"\0"):
        if not raw_name:
            continue
        name = raw_name.decode("utf-8")
        path = ROOT / name
        if path.is_file() or path.is_symlink():
            files.append(path)
    return sorted(set(files))


def read_utf8(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\0" in data:
        return None
    return data.decode("utf-8")


def markdown_outside_code(text: str) -> list[str]:
    result: list[str] = []
    fence: str | None = None

    for line in text.splitlines():
        stripped = line.lstrip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            result.append("")
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
            result.append("")
            continue
        result.append(re.sub(r"`[^`\n]*`", "", line))

    return result


def github_anchor(heading: str) -> str:
    heading = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    heading = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", heading)
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = heading.strip().lower()
    heading = re.sub(r"[^\w\s-]", "", heading, flags=re.UNICODE)
    heading = re.sub(r"[-\s]+", "-", heading)
    return heading.strip("-")


def markdown_anchors(path: Path) -> set[str]:
    text = read_utf8(path)
    if text is None:
        return set()

    anchors: set[str] = set()
    duplicate_counts: dict[str, int] = {}
    for line in markdown_outside_code(text):
        match = HEADING_RE.match(line)
        if match is None:
            continue
        base = github_anchor(match.group(2))
        if not base:
            continue
        occurrence = duplicate_counts.get(base, 0)
        anchors.add(base if occurrence == 0 else f"{base}-{occurrence}")
        duplicate_counts[base] = occurrence + 1
    return anchors


def check_markdown_links(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}

    for line_number, line in enumerate(markdown_outside_code(text), start=1):
        for match in MARKDOWN_LINK_RE.finditer(line):
            target = match.group(1) or match.group(2)
            target = target.strip()
            if not target or target.startswith("#"):
                continue
            if target.startswith("//") or EXTERNAL_TARGET_RE.match(target):
                continue

            path_part, separator, fragment = target.partition("#")
            if not path_part:
                continue
            path_part = unquote(path_part)

            if path_part.startswith("/"):
                target_path = (ROOT / path_part.lstrip("/")).resolve()
            else:
                target_path = (path.parent / path_part).resolve()

            try:
                target_path.relative_to(ROOT)
            except ValueError:
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: "
                    f"link escapes the repository: {target}"
                )
                continue

            if not target_path.exists():
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: "
                    f"missing internal link target: {target}"
                )
                continue

            if separator and fragment and target_path.suffix.lower() == ".md":
                if target_path not in anchor_cache:
                    anchor_cache[target_path] = markdown_anchors(target_path)
                if unquote(fragment) not in anchor_cache[target_path]:
                    errors.append(
                        f"{path.relative_to(ROOT)}:{line_number}: "
                        f"missing Markdown anchor: {target}"
                    )

    return errors


def check_action_pins(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = ACTION_USE_RE.match(line)
        if match is None:
            continue
        action = match.group(1)
        if action.startswith("./"):
            continue
        if action.startswith("docker://"):
            if "@sha256:" not in action:
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: "
                    f"Docker action is not pinned by digest: {action}"
                )
            continue
        if "@" not in action:
            errors.append(
                f"{path.relative_to(ROOT)}:{line_number}: "
                f"action is not pinned: {action}"
            )
            continue
        reference = action.rsplit("@", 1)[1]
        if re.fullmatch(r"[0-9a-f]{40}", reference) is None:
            errors.append(
                f"{path.relative_to(ROOT)}:{line_number}: "
                f"action is not pinned to a full commit SHA: {action}"
            )
    return errors


def main() -> int:
    errors: list[str] = []

    for relative_path in REQUIRED_PATHS:
        if not (ROOT / relative_path).is_file():
            errors.append(f"missing required file: {relative_path}")

    try:
        files = git_files()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    text_file_count = 0
    internal_link_count = 0

    for path in files:
        relative_path = path.relative_to(ROOT)
        if path.is_symlink():
            continue
        try:
            text = read_utf8(path)
        except UnicodeDecodeError:
            errors.append(f"{relative_path}: file is not valid UTF-8")
            continue
        if text is None:
            continue

        text_file_count += 1
        if "\r" in text:
            errors.append(f"{relative_path}: use LF line endings")
        if text and not text.endswith("\n"):
            errors.append(f"{relative_path}: missing final newline")

        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.rstrip(" \t") != line:
                errors.append(f"{relative_path}:{line_number}: trailing whitespace")
            if CONFLICT_START_RE.match(line) or CONFLICT_END_RE.match(line):
                errors.append(f"{relative_path}:{line_number}: conflict marker")

        if path.suffix.lower() == ".md":
            link_errors = check_markdown_links(path, text)
            errors.extend(link_errors)
            internal_link_count += 1

        if (
            len(relative_path.parts) >= 3
            and relative_path.parts[0] == ".github"
            and relative_path.parts[1] == "workflows"
            and path.suffix.lower() in {".yml", ".yaml"}
        ):
            errors.extend(check_action_pins(path, text))

    if errors:
        print("Repository checks failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(
        f"Repository checks passed: {len(files)} files, "
        f"{text_file_count} text files, {internal_link_count} Markdown files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
