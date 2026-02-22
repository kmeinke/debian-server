#!/usr/bin/env python3
"""Oracle Cloud VM test runner for salt-ssh."""

import atexit
import base64
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import oci

VM_NAME = "server-salt-test"
MINION_ID = "test_oci_1"
REPO_DIR = Path(__file__).resolve().parent.parent
SECRETS_DIR = REPO_DIR / "salt" / "pillar" / "secrets"
ROSTER = REPO_DIR / "salt" / "roster"
ENV_FILE = REPO_DIR / ".oci.env"

USAGE = """\
Usage: test-oci.py [command]

Commands:
  auth          Test OCI authentication (config + key fingerprint)
  upload-image  Upload qcow2 to Object Storage and import as custom image
  create        Create Oracle Cloud VM, wait for SSH
  check [state] Apply a single state (default: base.hostname, creates VM if needed)
  test          Run highstate via salt-ssh against VM (creates if needed, default)
  ssh           SSH into VM as admin
  delete        Delete VM
  ip            Print VM's current IP\
"""


def load_env():
    """Load configuration from .oci.env."""
    if not ENV_FILE.exists():
        sys.exit(f"Missing config file: {ENV_FILE}\nCopy .oci.env.example and fill in your values.")
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    required = [
        "OCI_COMPARTMENT_OCID",
        "OCI_IMAGE_OCID",
        "OCI_SUBNET_OCID",
        "OCI_BUCKET_NAME",
        "OCI_SHAPE",
        "ADMIN_SSH_KEY",
    ]
    missing = [k for k in required if not env.get(k)]
    if missing:
        sys.exit(f"Missing required values in {ENV_FILE}: {', '.join(missing)}")
    return env


def oci_clients():
    """Return authenticated OCI compute, network, and object storage clients."""
    config = oci.config.from_file()
    compute = oci.core.ComputeClient(config)
    network = oci.core.VirtualNetworkClient(config)
    object_storage = oci.object_storage.ObjectStorageClient(config)
    return compute, network, object_storage


def run(cmd, **kwargs):
    """Run a command, exit on failure."""
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        sys.exit(result.returncode)


def get_instance(compute, env):
    """Return the test VM instance if it exists, else None."""
    instances = oci.pagination.list_call_get_all_results(
        compute.list_instances,
        env["OCI_COMPARTMENT_OCID"],
    ).data
    for instance in instances:
        if instance.display_name == VM_NAME and instance.lifecycle_state not in (
            "TERMINATED",
            "TERMINATING",
        ):
            return instance
    return None


def vm_ip(compute, network, env):
    """Get the public IPv4 of the test VM."""
    instance = get_instance(compute, env)
    if not instance:
        sys.exit(f"No VM '{VM_NAME}' found.")
    vnics = oci.pagination.list_call_get_all_results(
        compute.list_vnic_attachments,
        env["OCI_COMPARTMENT_OCID"],
        instance_id=instance.id,
    ).data
    for vnic_attachment in vnics:
        vnic = network.get_vnic(vnic_attachment.vnic_id).data
        if vnic.public_ip:
            return vnic.public_ip
    sys.exit("No public IP found for VM.")


def wait_for_sshd(host, port=22, timeout=180):
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


def cmd_auth():
    """Test OCI authentication: verify key fingerprint and make a live API call."""
    import hashlib
    import os

    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        PublicFormat,
        load_pem_private_key,
    )

    config = oci.config.from_file()
    key_path = os.path.expanduser(config["key_file"])

    with open(key_path, "rb") as f:
        key_data = f.read()
    key = load_pem_private_key(key_data, password=None)
    pub_der = key.public_key().public_bytes(
        Encoding.DER, PublicFormat.SubjectPublicKeyInfo
    )
    md5 = hashlib.md5(pub_der).hexdigest()
    computed_fp = ":".join(md5[i : i + 2] for i in range(0, 32, 2))

    config_fp = config["fingerprint"]
    fp_ok = config_fp == computed_fp
    print(f"config fingerprint:   {config_fp}")
    print(f"key fingerprint:      {computed_fp}")
    print(f"fingerprint match:    {'OK' if fp_ok else 'MISMATCH'}")
    if not fp_ok:
        sys.exit(
            "\nFingerprint mismatch — update ~/.oci/config or re-upload the key in the OCI Console."
        )

    print("Testing API call (get_namespace)...", end=" ", flush=True)
    _, _, object_storage = oci_clients()
    try:
        ns = object_storage.get_namespace().data
        print(f"OK (namespace: {ns})")
    except oci.exceptions.ServiceError as e:
        print(f"FAILED\n{e.status} {e.code}: {e.message}")
        sys.exit(1)


def cmd_upload_image(env):
    """Upload qcow2 to Object Storage and import it as a custom image."""
    image_file = REPO_DIR / "debian-12-genericcloud-amd64.qcow2"
    if not image_file.exists():
        sys.exit(f"Image file not found: {image_file}")

    compute, _, object_storage = oci_clients()
    namespace = object_storage.get_namespace().data
    bucket = env["OCI_BUCKET_NAME"]
    image_object_name = image_file.name

    file_size = image_file.stat().st_size
    uploaded = [0]

    def progress(bytes_uploaded):
        uploaded[0] += bytes_uploaded
        pct = uploaded[0] * 100 // file_size
        print(
            f"\r  Uploading... {pct}%"
            f" ({uploaded[0] // 1024 // 1024} / {file_size // 1024 // 1024} MiB)",
            end="",
            flush=True,
        )

    print(f"Uploading {image_file.name} to bucket '{bucket}'...")
    upload_manager = oci.object_storage.UploadManager(object_storage)
    upload_manager.upload_file(
        namespace,
        bucket,
        image_object_name,
        str(image_file),
        progress_callback=progress,
    )
    print(f"\r  Upload complete.{' ' * 50}")

    print("Importing as custom image...")
    image = compute.create_image(
        oci.core.models.CreateImageDetails(
            compartment_id=env["OCI_COMPARTMENT_OCID"],
            display_name="debian-12-genericcloud-amd64",
            image_source_details=oci.core.models.ImageSourceViaObjectStorageTupleDetails(
                source_type="objectStorageTuple",
                namespace_name=namespace,
                bucket_name=bucket,
                object_name=image_object_name,
                source_image_type="QCOW2",
                operating_system="Debian GNU/Linux",
                operating_system_version="12",
            ),
        )
    ).data

    print("Waiting for image to become available...", end="", flush=True)
    oci.wait_until(
        compute,
        compute.get_image(image.id),
        "lifecycle_state",
        "AVAILABLE",
        max_wait_seconds=1200,
        succeed_on_not_found=False,
    )
    print(" done.")
    print(f"\nImage OCID: {image.id}")
    print(f"\nUpdate OCI_IMAGE_OCID in .oci.env to:\n  {image.id}")


def cmd_create(env):
    compute, network, _ = oci_clients()
    if get_instance(compute, env):
        print(f"VM '{VM_NAME}' already exists. IP: {vm_ip(compute, network, env)}")
        return

    userdata = (REPO_DIR / "scripts" / "vm-userdata.yaml").read_text()
    userdata_b64 = base64.b64encode(userdata.encode()).decode()

    config = oci.config.from_file()
    identity = oci.identity.IdentityClient(config)
    ad = None
    for candidate in identity.list_availability_domains(env["OCI_COMPARTMENT_OCID"]).data:
        shapes = oci.pagination.list_call_get_all_results(
            compute.list_shapes, env["OCI_COMPARTMENT_OCID"],
            availability_domain=candidate.name,
        ).data
        if any(s.shape == env["OCI_SHAPE"] for s in shapes):
            ad = candidate.name
            break
    if not ad:
        sys.exit(f"Shape '{env['OCI_SHAPE']}' not available in any AD in this region.")

    print(f"Creating VM '{VM_NAME}' in {ad}...")
    instance = compute.launch_instance(
        oci.core.models.LaunchInstanceDetails(
            compartment_id=env["OCI_COMPARTMENT_OCID"],
            availability_domain=ad,
            display_name=VM_NAME,
            shape=env["OCI_SHAPE"],
            image_id=env["OCI_IMAGE_OCID"],
            create_vnic_details=oci.core.models.CreateVnicDetails(
                subnet_id=env["OCI_SUBNET_OCID"],
                assign_public_ip=True,
            ),
            metadata={
                "user_data": userdata_b64,
            },
        )
    ).data

    print("Waiting for instance to start...", end="", flush=True)
    oci.wait_until(
        compute,
        compute.get_instance(instance.id),
        "lifecycle_state",
        "RUNNING",
        max_wait_seconds=300,
        succeed_on_not_found=False,
    )
    print(" running.")

    ip = vm_ip(compute, network, env)
    print(f"VM created. IP: {ip}")
    wait_for_sshd(ip)


def cmd_check(env, state="base.hostname"):
    compute, network, _ = oci_clients()
    if not get_instance(compute, env):
        cmd_create(env)
    ip = vm_ip(compute, network, env)
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
    compute, network, _ = oci_clients()
    if not get_instance(compute, env):
        cmd_create(env)
    ip = vm_ip(compute, network, env)
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
    compute, network, _ = oci_clients()
    if not get_instance(compute, env):
        sys.exit(f"No VM '{VM_NAME}' found. Run: test-vm-oci.py create")
    ip = vm_ip(compute, network, env)
    key = str(Path(env["ADMIN_SSH_KEY"]).expanduser())
    run(
        [
            "ssh",
            "-i", key,
            "-o", "StrictHostKeyChecking=no",
            f"admin@{ip}",
        ]
    )


def cmd_delete(env):
    compute, network, _ = oci_clients()
    instance = get_instance(compute, env)
    if not instance:
        print(f"No VM named '{VM_NAME}' found.")
        return
    compute.terminate_instance(instance.id)
    print(f"VM '{VM_NAME}' terminating.")


def cmd_ip(env):
    compute, network, _ = oci_clients()
    if not get_instance(compute, env):
        sys.exit(f"No VM '{VM_NAME}' exists.")
    print(vm_ip(compute, network, env))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else None

    if cmd is None or cmd in ("help", "-h", "--help"):
        print(USAGE)
        return

    if cmd == "auth":
        cmd_auth()
        return

    env = load_env()

    if cmd == "upload-image":
        cmd_upload_image(env)
        return

    args = sys.argv[2:]

    if cmd == "create":
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
