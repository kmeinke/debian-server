#!/usr/bin/env python3
"""Docker-based test runner for salt-ssh."""

import atexit
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

CONTAINER = "server-salt"
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
        f"server:\n"
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
atexit.register(cleanup_roster)


def cmd_build():
    run(["docker", "compose", "down"])
    run(["docker", "compose", "build"])


def cmd_shell(env):
    ensure_running(env)
    run(["docker", "exec", "-it", CONTAINER, "bash"])


def run_with_spinner(cmd):
    """Run a command with an elapsed time spinner."""
    stop = threading.Event()
    start = time.time()

    def spinner():
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while not stop.is_set():
            elapsed = int(time.time() - start)
            print(
                f"\r{chars[i % len(chars)]} Running highstate... {elapsed}s",
                end="",
                flush=True,
            )
            i += 1
            stop.wait(0.2)
        elapsed = int(time.time() - start)
        print(f"\r✓ Highstate completed in {elapsed}s    ")

    t = threading.Thread(target=spinner, daemon=True)
    t.start()
    result = subprocess.run(cmd, capture_output=True, text=True)
    stop.set()
    t.join()

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        sys.exit(result.returncode)


def cmd_test(env):
    ensure_running(env)
    write_roster(env)
    decrypt_secrets()
    run_with_spinner([
        "salt-ssh",
        "-c", str(REPO_DIR / "salt"),
        "--ignore-host-keys",
        "server",
        "state.highstate",
    ])


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

    commands = {
        "build": lambda: cmd_build(),
        "shell": lambda: cmd_shell(env),
        "test": lambda: cmd_test(env),
        "clean": lambda: cmd_clean(),
        "ssh": lambda: cmd_ssh(env),
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
