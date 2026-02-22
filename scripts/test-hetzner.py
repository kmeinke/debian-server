#!/usr/bin/env python3
"""Hetzner cloud VM test runner for salt-ssh."""

import atexit
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

VM_NAME = "server-salt-test"
REPO_DIR = Path(__file__).resolve().parent.parent
SECRETS_DIR = REPO_DIR / "salt" / "pillar" / "secrets"
ROSTER = REPO_DIR / "salt" / "roster"
ENV_FILE = REPO_DIR / ".hetzner.env"

USAGE = """\
Usage: test-hetzner.py [command]

Commands:
  create  Create Hetzner VM, wait for SSH
  test    Run highstate via salt-ssh against VM (creates if needed, default)
  ssh     SSH into VM as admin
  delete  Delete VM
  ip      Print VM's current IP\
"""


def load_env():
    """Load configuration from .hetzner.env."""
    if not ENV_FILE.exists():
        sys.exit(f"Missing config file: {ENV_FILE}\nCopy .hetzner.env.example and fill in your values.")
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    required = ["HCLOUD_TOKEN", "HETZNER_SERVER_TYPE", "HETZNER_LOCATION", "ADMIN_SSH_KEY"]
    missing = [k for k in required if not env.get(k)]
    if missing:
        sys.exit(f"Missing required values in {ENV_FILE}: {', '.join(missing)}")
    return env


def run(cmd, **kwargs):
    """Run a command, exit on failure."""
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        sys.exit(result.returncode)


def hcloud(env, *args, capture=False):
    """Run an hcloud command, exit on failure."""
    cmd = ["hcloud", *args]
    hcloud_env = {**os.environ, "HCLOUD_TOKEN": env["HCLOUD_TOKEN"]}
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True, env=hcloud_env)
        if result.returncode != 0:
            sys.exit(f"hcloud error: {result.stderr.strip()}")
        return result.stdout.strip()
    run(cmd, env=hcloud_env)


def vm_exists(env):
    """Check if the test VM exists in Hetzner."""
    hcloud_env = {**os.environ, "HCLOUD_TOKEN": env["HCLOUD_TOKEN"]}
    result = subprocess.run(
        ["hcloud", "server", "list", "-o", "json"],
        capture_output=True,
        text=True,
        env=hcloud_env,
    )
    if result.returncode != 0:
        return False
    servers = json.loads(result.stdout)
    return any(s["name"] == VM_NAME for s in servers)


def vm_ip(env):
    """Get the public IPv4 of the test VM."""
    out = hcloud(
        env,
        "server", "describe", VM_NAME,
        "-o", "format={{.PublicNet.IPv4.IP}}",
        capture=True,
    )
    return out.strip()


def wait_for_sshd(host, port=22, timeout=120):
    """Wait until sshd is accepting connections."""
    print("Waiting for sshd...", end="", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(" ready.")
                return
        except OSError:
            print(".", end="", flush=True)
            time.sleep(2)
    sys.exit(f"\nsshd not ready after {timeout}s")


def write_vm_roster(ip, env):
    """Write a salt-ssh roster file pointing at the VM."""
    key = str(Path(env["ADMIN_SSH_KEY"]).expanduser())
    ROSTER.write_text(
        f"server:\n"
        f"  host: {ip}\n"
        f"  port: 22\n"
        f"  user: admin\n"
        f"  sudo: True\n"
        f"  priv: {key}\n"
    )


def cleanup_vm_roster():
    """Remove the dynamic roster file."""
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
atexit.register(cleanup_vm_roster)


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


def cmd_create(env):
    if vm_exists(env):
        print(f"VM '{VM_NAME}' already exists. IP: {vm_ip(env)}")
        return
    print(f"Creating VM '{VM_NAME}'...")
    hcloud(
        env,
        "server", "create",
        "--name", VM_NAME,
        "--image", "debian-12",
        "--type", env["HETZNER_SERVER_TYPE"],
        "--location", env["HETZNER_LOCATION"],
        "--user-data-from-file", str(REPO_DIR / "scripts" / "vm-userdata.yaml"),
    )
    ip = vm_ip(env)
    print(f"VM created. IP: {ip}")
    wait_for_sshd(ip)


def cmd_test(env):
    if not vm_exists(env):
        cmd_create(env)
    ip = vm_ip(env)
    write_vm_roster(ip, env)
    decrypt_secrets()
    run_with_spinner([
        "salt-ssh",
        "-c", str(REPO_DIR / "salt"),
        "--ignore-host-keys",
        "server",
        "state.highstate",
    ])


def cmd_ssh(env):
    if not vm_exists(env):
        sys.exit(f"No VM '{VM_NAME}' found. Run: test-hetzner.py create")
    ip = vm_ip(env)
    key = str(Path(env["ADMIN_SSH_KEY"]).expanduser())
    run([
        "ssh",
        "-i", key,
        "-o", "StrictHostKeyChecking=no",
        f"admin@{ip}",
    ])


def cmd_delete(env):
    if not vm_exists(env):
        print(f"No VM named '{VM_NAME}' found.")
        return
    hcloud(env, "server", "delete", VM_NAME)
    print(f"VM '{VM_NAME}' deleted.")


def cmd_ip(env):
    if not vm_exists(env):
        sys.exit(f"No VM '{VM_NAME}' exists.")
    print(vm_ip(env))


def main():
    env = load_env()

    commands = {
        "create": cmd_create,
        "test": cmd_test,
        "ssh": cmd_ssh,
        "delete": cmd_delete,
        "ip": cmd_ip,
    }

    cmd = sys.argv[1] if len(sys.argv) > 1 else "test"

    if cmd in ("help", "-h", "--help"):
        print(USAGE)
    elif cmd in commands:
        commands[cmd](env)
    else:
        sys.exit(f"Unknown command: {cmd}\n{USAGE}")


if __name__ == "__main__":
    main()
