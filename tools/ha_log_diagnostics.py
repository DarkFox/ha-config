#!/usr/bin/env python3
import os
import re
import sys

# ------- config via env -------
REWRITES = []
for pair in os.getenv("PATH_REWRITE", "").split(","):
    if "=" in pair:
        src, dst = pair.split("=", 1)
        REWRITES.append((src.rstrip("/"), dst.rstrip("/")))

# Comma-separated prefixes considered "yours"
USER_PREFIXES = [
    p.strip()
    for p in os.getenv(
        "USER_PREFIXES", "/config,/custom_components,/python_scripts"
    ).split(",")
    if p.strip()
]

# If true, suppress diagnostics unless a user frame exists
falseish = ("0", "false", "False")
REQUIRE_USER_FRAME = os.getenv("REQUIRE_USER_FRAME", "1") not in falseish

# Exclude these prefixes from being chosen when falling back
EXCLUDE_PREFIXES = [
    p.strip()
    for p in os.getenv(
        "EXCLUDE_PREFIXES", "/usr/src/homeassistant,/usr/local/lib/python"
    ).split(",")
    if p.strip()
]
# --------------------------------

re_tb_start = re.compile(r"^Traceback \(most recent call last\):\s*$")
re_frame = re.compile(r'^\s*File "([^"]+)", line (\d+), in (.*)\s*$')
re_exc = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_\.]*):\s*(.*)\s*$")

# Single-line matches that already look like file:line[:col]: msg
re_plain = re.compile(
    r"(?P<file>/(?:[^:\n])+):(?P<line>\d+)(?::(?P<col>\d+))?:\s*(?P<msg>.+)$"
)

frames = []
exception_line = None


def rewrite_path(p: str) -> str:
    for src, dst in REWRITES:
        if p == src or p.startswith(src + "/"):
            return dst + p[len(src):]
    return p


def is_under(prefixes, p: str) -> bool:
    p = p.rstrip("/")
    for pref in prefixes:
        if p == pref or p.startswith(pref.rstrip("/") + "/"):
            return True
    return False


def is_user_frame(p: str) -> bool:
    # Also accept relative paths that start with configured prefixes
    rp = p.lstrip("./")
    return is_under(USER_PREFIXES, p) or any(
        rp.startswith(pref.strip("/")) for pref in USER_PREFIXES
    )


def flush_block():
    global frames, exception_line
    if not frames or not exception_line:
        frames.clear()
        exception_line = None
        return

    # Prefer the deepest user frame (closest to the exception)
    user_frames = [f for f in frames if is_user_frame(f[0])]
    chosen = user_frames[-1] if user_frames else None

    # If no user frame and we require one, drop this block
    if chosen is None and REQUIRE_USER_FRAME:
        frames.clear()
        exception_line = None
        return

    # Otherwise, pick the deepest non-excluded frame
    if chosen is None:
        for f in reversed(frames):
            if not is_under(EXCLUDE_PREFIXES, f[0]):
                chosen = f
                break
        if chosen is None:
            # Everything excluded → drop
            frames.clear()
            exception_line = None
            return

    path, line, func = chosen
    path = rewrite_path(path)
    etype, emsg = exception_line
    print(f"{path}:{line}:1: [HA:{etype}] {emsg}")

    frames.clear()
    exception_line = None


# Single-line matches that already look like file:line[:col]: msg
re_plain = re.compile(
    r"(?P<file>/(?:[^:\n])+):(?P<line>\d+)(?::(?P<col>\d+))?:\s*(?P<msg>.+)$"
)

for raw in sys.stdin:
    line = raw.rstrip("\n")

    m_plain = re_plain.search(line)
    if m_plain:
        fpath = m_plain.group("file")
        # If we require a user frame, only pass through
        # if the file is in your prefixes
        if REQUIRE_USER_FRAME and not is_user_frame(fpath):
            continue
        # If we don't require user frame, still drop
        # explicitly excluded prefixes
        if not REQUIRE_USER_FRAME and is_under(EXCLUDE_PREFIXES, fpath):
            continue

        f = rewrite_path(fpath)
        ln = m_plain.group("line")
        col = m_plain.group("col") or "1"
        msg = m_plain.group("msg")
        print(f"{f}:{ln}:{col}: {msg}")
        continue

    if re_tb_start.match(line):
        flush_block()
        frames.clear()
        exception_line = None
        continue

    m = re_frame.match(line)
    if m:
        frames.append((m.group(1), int(m.group(2)), m.group(3)))
        continue

    m = re_exc.match(line)
    if m and frames:
        exception_line = (m.group(1), m.group(2))
        continue

    # Blank line ends a block in many HA logs
    if not line.strip():
        flush_block()

# EOF
flush_block()
