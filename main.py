#!/usr/bin/env python3
"""Copy the one-line roast from entry.txt to the make.fun output directory."""

import hashlib
import os
import shutil
import sys
from pathlib import Path

EXPECTED_SHA256 = "9f2a99ef09e47cbcf2ce9ff53b538247e5e7f5f49718f6573657de0deaee3e36"

MIN_CHARS = 1
MAX_CHARS = 140


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    return 1


def main():
    entry_path = Path(__file__).resolve().parent / "entry.txt"

    try:
        raw = entry_path.read_bytes()
    except OSError as exc:
        return fail(f"cannot read {entry_path}: {exc}")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return fail(f"{entry_path} is not valid UTF-8: {exc}")

    body = text
    if body.endswith("\r\n"):
        body = body[:-2]
    elif body.endswith("\n"):
        body = body[:-1]
    if "\n" in body or "\r" in body:
        return fail("entry must be a single line")

    if not body.strip():
        return fail("entry must not be only whitespace")

    char_count = len(body)
    if char_count < MIN_CHARS or char_count > MAX_CHARS:
        return fail(f"entry must be {MIN_CHARS}-{MAX_CHARS} characters, got {char_count}")

    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        return fail(
            "sha256 mismatch: expected "
            f"{EXPECTED_SHA256}, got {actual_sha}"
        )

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    out_path = out_dir / "entry.txt"

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return fail(f"cannot create output directory {out_dir}: {exc}")

    if not os.access(out_dir, os.W_OK):
        return fail(f"output directory {out_dir} is not writable")

    if out_path.exists() and out_path.resolve() == entry_path.resolve():
        return fail(f"refusing to copy {entry_path} onto itself")

    src_stat = entry_path.stat()
    if out_path.exists():
        dst_stat = out_path.stat()
        if (src_stat.st_dev, src_stat.st_ino) == (dst_stat.st_dev, dst_stat.st_ino):
            return fail(f"refusing to copy {entry_path} onto itself")

    try:
        shutil.copyfile(entry_path, out_path)
    except shutil.SameFileError:
        return fail(f"refusing to copy {entry_path} onto itself")
    except OSError as exc:
        return fail(f"cannot write {out_path}: {exc}")

    print(f"entry: {body}")
    print(f"chars: {char_count}")
    print(f"sha256: {actual_sha}")
    print(f"wrote: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
