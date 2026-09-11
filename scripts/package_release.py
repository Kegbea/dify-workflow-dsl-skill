#!/usr/bin/env python3
"""Build a deterministic release ZIP for this Skill."""
from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = "dify-workflow-dsl"
EXCLUDED_PARTS = {".git", ".idea", ".pytest_cache", ".venv", "__pycache__", "dist", "venv"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip", ".tar", ".gz"}


def skill_version() -> str:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r'^\s*version:\s*["\']?([^"\'\s]+)', text, flags=re.MULTILINE)
    if not match:
        raise RuntimeError("SKILL.md metadata.version is missing")
    return match.group(1)


def included_files() -> list[Path]:
    result = []
    for path in SKILL_ROOT.rglob("*"):
        relative = path.relative_to(SKILL_ROOT)
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        result.append(path)
    return sorted(result, key=lambda item: item.relative_to(SKILL_ROOT).as_posix())


def build(output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in included_files():
            relative = path.relative_to(SKILL_ROOT).as_posix()
            info = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    version = skill_version()
    output = args.output or SKILL_ROOT / "dist" / f"dify-workflow-dsl-{version}.zip"
    built = build(output)
    print(f"archive={built} files={len(included_files())}")


if __name__ == "__main__":
    main()
