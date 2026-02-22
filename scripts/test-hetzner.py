#!/usr/bin/env python3
"""Hetzner cloud VM test runner for salt-ssh."""

import atexit
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

VM_NAME = "server-salt-test"
MINION_ID = "test_hetzner_1"
REPO_DIR = Path(__file__).resolve().parent.parent
SECRETS_DIR = REPO_DIR / "salt" / "pillar" / "secrets"
ROSTER = REPO_DIR / "salt" / "roster"
ENV_FILE = REPO_DIR / ".hetzner.env"

USAGE = """\
Usage: test-hetzner.py [command]

Commands:
  create  Create Hetzner VM, wait for SSH
  check [state]  Apply a single state (default: base.hostname, creates VM if needed)
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
        f"{MINION_ID}:\n"
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
atexit.register(cleanup_vm_roster)


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

    with open(log_path, "w") as f:
        if result.stdout:
            f.write(result.stdout)
        if result.stderr:
            f.write("\n--- stderr ---\n")
            f.write(result.stderr)

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


def cmd_check(env, state="base.hostname"):
    if not vm_exists(env):
        cmd_create(env)
    ip = vm_ip(env)
    write_vm_roster(ip, env)
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
    if not vm_exists(env):
        cmd_create(env)
    ip = vm_ip(env)
    write_vm_roster(ip, env)
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

    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    args = sys.argv[2:]

    if cmd is None or cmd in ("help", "-h", "--help"):
        print(USAGE)
    elif cmd == "create":
        cmd_create(env)
    elif cmd == "check":
        cmd_check(env, *args)
    elif cmd == "test":
        cmd_test(env)
    elif cmd == "ssh":
        cmd_ssh(env)
    elif cmd == "delete":
        cmd_delete(env)
    elif cmd == "ip":
        cmd_ip(env)
    else:
        sys.exit(f"Unknown command: {cmd}\n{USAGE}")


if __name__ == "__main__":
    main()
