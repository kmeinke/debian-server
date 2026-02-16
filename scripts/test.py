#!/usr/bin/env python3
"""Docker-based test runner for salt-ssh."""

import atexit
import subprocess
import sys
import time
from pathlib import Path

CONTAINER = "server-salt"
REPO_DIR = Path("/mnt/c/Code/server-salt")
SECRETS_DIR = REPO_DIR / "salt" / "pillar" / "secrets"

USAGE = """\
Usage: test.py [command]

Commands:
  build   Remove container and rebuild image
  shell   Start container, open shell
  test    Start container, run highstate via salt-ssh (default)
  clean   Remove container and image\
"""


def run(cmd, **kwargs):
    """Run a command, exit on failure."""
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        sys.exit(result.returncode)


def is_running():
    """Check if the container is running."""
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and "true" in result.stdout


def ensure_running():
    """Start the container if not already running."""
    if not is_running():
        run(["docker", "compose", "up", "-d", "--build"])
        print("Waiting for systemd to boot...")
        time.sleep(3)


def decrypt_secrets():
    """Decrypt all *.sls.enc files to *.sls."""
    for enc in SECRETS_DIR.glob("*.sls.enc"):
        dec = enc.with_suffix("")  # strip .enc
        with open(dec, "w") as f:
            run(
                ["sops", "--input-type=yaml", "--output-type=yaml", "-d", str(enc)],
                stdout=f,
            )


def cleanup_secrets():
    """Remove all decrypted *.sls files."""
    for sls in SECRETS_DIR.glob("*.sls"):
        sls.unlink()


atexit.register(cleanup_secrets)


def cmd_build():
    run(["docker", "compose", "down"])
    run(["docker", "compose", "build"])


def cmd_shell():
    ensure_running()
    run(["docker", "exec", "-it", CONTAINER, "bash"])


def cmd_test():
    ensure_running()
    decrypt_secrets()
    run(
        [
            "salt-ssh",
            "-c",
            str(REPO_DIR / "salt"),
            "--ignore-host-keys",
            "server",
            "state.highstate",
        ]
    )


def cmd_clean():
    run(["docker", "compose", "down", "--rmi", "all", "--volumes"])


def main():
    commands = {
        "build": cmd_build,
        "shell": cmd_shell,
        "test": cmd_test,
        "clean": cmd_clean,
    }

    cmd = sys.argv[1] if len(sys.argv) > 1 else "test"

    if cmd in ("help", "-h", "--help"):
        print(USAGE)
    elif cmd in commands:
        commands[cmd]()
    else:
        sys.exit(f"Unknown command: {cmd}\n{USAGE}")


if __name__ == "__main__":
    main()
