#!/usr/bin/env python3
"""SOPS helper for managing encrypted secrets with base64 file support."""

import base64
import subprocess
import sys
from pathlib import Path

USAGE = """\
Usage: sops.py <command> [args]

Commands:
  import <sops-file> <key> <file>   Base64-encode file and store in SOPS yaml
  export <sops-file> <key> <file>   Extract base64 value from SOPS yaml and decode to file
  edit   <sops-file>                Open SOPS file in editor (decrypts/re-encrypts)
  rotate <sops-file>                Rotate data encryption keys

Keys use dot notation: ssh.admin_ed25519\
"""


def dot_to_bracket(key):
    """Convert dot notation (ssh.admin_ed25519) to SOPS bracket notation (["ssh"]["admin_ed25519"])."""
    return "".join(f'["{part}"]' for part in key.split("."))


def sops(*args):
    """Run a sops command, raising on failure."""
    result = subprocess.run(["sops", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"sops error: {result.stderr.strip()}")
    return result.stdout


def cmd_import(sops_file, key, input_file):
    path = Path(input_file)
    if not path.exists():
        sys.exit(f"Error: {input_file} not found")
    encoded = base64.b64encode(path.read_bytes()).decode()
    bracket_key = dot_to_bracket(key)
    sops("--set", f'{bracket_key} "{encoded}"', sops_file)
    print(f"Imported {input_file} -> {sops_file} {key}")


def cmd_export(sops_file, key, output_file):
    bracket_key = dot_to_bracket(key)
    encoded = sops("-d", "--extract", bracket_key, sops_file)
    Path(output_file).write_bytes(base64.b64decode(encoded.strip()))
    print(f"Exported {sops_file} {key} -> {output_file}")


def cmd_edit(sops_file):
    subprocess.run(["sops", sops_file])


def cmd_rotate(sops_file):
    sops("--rotate", "--in-place", sops_file)
    print(f"Rotated data keys in {sops_file}")


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return

    cmd, args = sys.argv[1], sys.argv[2:]

    commands = {
        "import": (cmd_import, 3),
        "export": (cmd_export, 3),
        "edit":   (cmd_edit, 1),
        "rotate": (cmd_rotate, 1),
    }

    if cmd in ("help", "-h", "--help"):
        print(USAGE)
    elif cmd in commands:
        func, nargs = commands[cmd]
        if len(args) != nargs:
            sys.exit(f"Usage: sops.py {cmd} " + " ".join(["<arg>"] * nargs))
        func(*args)
    else:
        sys.exit(f"Unknown command: {cmd}\n{USAGE}")


if __name__ == "__main__":
    main()
