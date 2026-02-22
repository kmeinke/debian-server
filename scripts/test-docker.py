#!/usr/bin/env python3
"""Docker-based test runner for salt-ssh."""

import atexit
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

CONTAINER = "server-salt"
MINION_ID = "test_docker_1"
REPO_DIR = Path(__file__).resolve().parent.parent
SECRETS_DIR = REPO_DIR / "salt" / "pillar" / "secrets"
ROSTER = REPO_DIR / "salt" / "roster"
ENV_FILE = REPO_DIR / ".docker.env"

USAGE = """\
Usage: test-docker.py [command]

Commands:
  build   Remove container and rebuild image
  shell   Start container, open shell
  ssh     Start container, ssh into it as admin
  check [state]  Start container, apply a single state (default: base.hostname)
  test    Start container, run highstate via salt-ssh (default)
  clean   Remove container and image\
"""


def load_env():
    """Load configuration from .docker.env."""
    if not ENV_FILE.exists():
        sys.exit(f"Missing config file: {ENV_FILE}")
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    required = ["DOCKER_SSH_PORT", "ADMIN_SSH_KEY"]
    missing = [k for k in required if not env.get(k)]
    if missing:
        sys.exit(f"Missing required values in {ENV_FILE}: {', '.join(missing)}")
    return env


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


def wait_for_sshd(port, timeout=30):
    """Wait until sshd is accepting connections."""
    print("Waiting for sshd...", end="", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                print(" ready.")
                return
        except OSError:
            print(".", end="", flush=True)
            time.sleep(1)
    sys.exit(f"\nsshd not ready after {timeout}s")


def ensure_running(env):
    """Start the container if not already running."""
    if not is_running():
        run(["docker", "compose", "up", "-d", "--build"])
        wait_for_sshd(int(env["DOCKER_SSH_PORT"]))


def write_roster(env):
    """Write the salt-ssh roster for the Docker container."""
    key = str(Path(env["ADMIN_SSH_KEY"]).expanduser())
    ROSTER.write_text(
        f"{MINION_ID}:\n"
        f"  host: localhost\n"
        f"  port: {env['DOCKER_SSH_PORT']}\n"
        f"  user: admin\n"
        f"  sudo: True\n"
        f"  priv: {key}\n"
    )


def cleanup_roster():
    """Remove the generated roster file."""
    if ROSTER.exists():
        ROSTER.unlink()


def decrypt_secrets():
    """Decrypt all *.sls.enc files to *.sls (recursively)."""
    for enc in SECRETS_DIR.rglob("*.sls.enc"):
        dec = enc.with_suffix("")  # strip .enc
        with open(dec, "w") as f:
            run(
                ["sops", "--input-type=yaml", "--output-type=yaml", "-d", str(enc)],
                stdout=f,
            )


def cleanup_secrets():
    """Remove all decrypted *.sls files (recursively)."""
    for sls in SECRETS_DIR.rglob("*.sls"):
        sls.unlink()


atexit.register(cleanup_secrets)
atexit.register(cleanup_roster)


def cmd_build():
    run(["docker", "compose", "down"])
    run(["docker", "compose", "build"])


def cmd_shell(env):
    ensure_running(env)
    run(["docker", "exec", "-it", CONTAINER, "bash"])


def parse_salt_output(output):
    """Parse salt-ssh output into a summary dict and list of failed state IDs."""
    summary = {}
    m = re.search(r"Succeeded:\s*(\d+)(?:\s*\(changed=(\d+)\))?", output)
    if m:
        summary["succeeded"] = int(m.group(1))
        summary["changed"] = int(m.group(2)) if m.group(2) else 0
    m = re.search(r"Failed:\s*(\d+)", output)
    if m:
        summary["failed"] = int(m.group(1))

    failed_ids = []
    if summary.get("failed"):
        # Each failed block has "Result: False" preceded by "ID: <name>"
        for block in re.split(r"(?=----------)", output):
            if "Result: False" in block:
                id_m = re.search(r"^\s+ID:\s+(.+)$", block, re.MULTILINE)
                if id_m:
                    failed_ids.append(id_m.group(1).strip())

    return summary, failed_ids


def run_with_spinner(cmd, label="Running"):
    """Run salt-ssh with a spinner, write full output to a log file, print summary."""
    log_dir = REPO_DIR / ".salt" / "tmp"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"salt-ssh-{int(time.time())}.log"

    stop = threading.Event()
    start = time.time()

    def spinner():
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while not stop.is_set():
            elapsed = int(time.time() - start)
            print(
                f"\r{chars[i % len(chars)]} {label}... {elapsed}s",
                end="",
                flush=True,
            )
            i += 1
            stop.wait(0.2)
        elapsed = int(time.time() - start)
        print(f"\r✓ Done in {elapsed}s    ")

    t = threading.Thread(target=spinner, daemon=True)
    t.start()
    result = subprocess.run(cmd, capture_output=True, text=True)
    stop.set()
    t.join()

    # Write full output to log
    with open(log_path, "w") as f:
        if result.stdout:
            f.write(result.stdout)
        if result.stderr:
            f.write("\n--- stderr ---\n")
            f.write(result.stderr)

    # Parse and print summary
    summary, failed_ids = parse_salt_output(result.stdout)
    if summary:
        succeeded = summary.get("succeeded", "?")
        changed = summary.get("changed", 0)
        failed = summary.get("failed", 0)
        parts = [f"succeeded={succeeded}"]
        if changed:
            parts.append(f"changed={changed}")
        if failed:
            parts.append(f"failed={failed}")
        status = "✓" if not failed else "✗"
        print(f"{status}  {', '.join(parts)}  — log: {log_path}")
        for fid in failed_ids:
            print(f"  FAILED: {fid}")
    else:
        # No summary found — print raw output (non-state commands)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        sys.exit(result.returncode)


def cmd_check(env, state="base.hostname"):
    ensure_running(env)
    write_roster(env)
    decrypt_secrets()
    run_with_spinner(
        [
            "salt-ssh",
            "-c", str(REPO_DIR / "salt"),
            "--ignore-host-keys",
            MINION_ID,
            "state.apply", state,
        ],
        label=f"Checking {state}",
    )


def cmd_test(env):
    ensure_running(env)
    write_roster(env)
    decrypt_secrets()
    run_with_spinner(
        [
            "salt-ssh",
            "-c", str(REPO_DIR / "salt"),
            "--ignore-host-keys",
            MINION_ID,
            "state.highstate",
        ],
        label="Running highstate",
    )


def cmd_ssh(env):
    ensure_running(env)
    key = str(Path(env["ADMIN_SSH_KEY"]).expanduser())
    run([
        "ssh",
        "-p", env["DOCKER_SSH_PORT"],
        "-i", key,
        "-o", "StrictHostKeyChecking=no",
        "admin@localhost",
    ])


def cmd_clean():
    run(["docker", "compose", "down", "--rmi", "all", "--volumes"])


def main():
    env = load_env()

    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    args = sys.argv[2:]

    if cmd is None or cmd in ("help", "-h", "--help"):
        print(USAGE)
    elif cmd == "build":
        cmd_build()
    elif cmd == "shell":
        cmd_shell(env)
    elif cmd == "check":
        cmd_check(env, *args)
    elif cmd == "test":
        cmd_test(env)
    elif cmd == "clean":
        cmd_clean()
    elif cmd == "ssh":
        cmd_ssh(env)
    else:
        sys.exit(f"Unknown command: {cmd}\n{USAGE}")


if __name__ == "__main__":
    main()
