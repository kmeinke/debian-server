# server-salt

SaltStack configuration for a Debian Bookworm server, managed via salt-ssh. Tested via Docker.

## Conversation Rules
- Do not imply I want to implement a change just because I ask a yes or no question.
- Never commit without asking me explicitly first.
- Before committing, review all changes and propose how to split them into logical commits.
- Before committing, ensure documentation (README.md, CLAUDE.md) is updated to reflect the changes.
- When researching security guidelines (CIS, ANSSI, etc.), check `reference/` for PDF documents before searching the web.
- We do not trust by default. Enforce explicit permissions, disable unnecessary features, and verify rather than assume secure defaults.

## Project Structure

```
salt/states/                   Salt state definitions, organized by function
salt/states/secure_linux/      Umbrella state — includes all hardening substates
salt/states/*/files/           Config file templates managed by states
salt/pillar/                   Pillar data (configuration values)
salt/pillar/defaults/          Base pillar values applied to all hosts
salt/pillar/hosts/             Per-host-group overrides (deep-merged over defaults)
salt/pillar/secrets/hosts/     SOPS-encrypted secrets per host group (*.sls.enc)
salt/master                    salt-ssh master config (shared by all runners)
salt/roster                    generated at runtime by test runners, gitignored
scripts/test-docker.py         Docker-based test runner (salt-ssh)
scripts/test-hetzner.py        Hetzner VM test runner (salt-ssh)
scripts/test-oci.py            Oracle OCI VM test runner (salt-ssh)
scripts/vm-userdata.yaml       Cloud-init bootstrap for VM admin user
.docker.env                    Docker config (gitignored, see README for template)
.hetzner.env                   Hetzner config (gitignored, see README for template)
.oci.env                       OCI config (gitignored, see README for template)
scripts/sops.py                SOPS helper (import/export/edit/rotate)
reference/                     CIS benchmarks, ANSSI guides (PDFs)
```

## Salt Conventions

- States are pillar-driven. Use `salt['pillar.get']('key', 'default')` with sensible defaults.
- Config file templates live in `salt/states/<category>/files/` and use Jinja2 templating.
- State dependencies: packages first, then files, then services. Use `require`, `watch`, and `watch_in`.
- Docker compatibility: guard systemd-dependent states with `onlyif: test -d /run/systemd/system`.
- State naming: dot notation matching directory structure (e.g., `security.firewall`).
- Pillar layout: `defaults/<domain>.sls` for all hosts, `hosts/<group>.sls` for per-group overrides.
- Minion ID naming convention: `<group>_<label>_<instance>` (e.g., `test_docker_1`, `kt_web_1`).

## Testing

Docker container boots with systemd as PID 1 (privileged mode), running sshd. salt-ssh connects from WSL to apply states.

```bash
./scripts/test-docker.py build   # remove container and rebuild image
./scripts/test-docker.py shell   # start container, open shell
./scripts/test-docker.py ssh     # start container, ssh into it as admin
./scripts/test-docker.py check   # start container, apply single state (fast smoke test)
./scripts/test-docker.py test    # start container, run highstate via salt-ssh
./scripts/test-docker.py clean   # remove container, image, and volumes
```

Container auto-starts and auto-builds if not already running. salt-ssh connects on port 2222 as admin user with sudo.

For higher-fidelity testing against a real VM (requires `.hetzner.env` or `.oci.env`):

```bash
./scripts/test-hetzner.py create   # create Hetzner VM, wait for SSH
./scripts/test-hetzner.py check    # apply single state (fast smoke test, creates VM if needed)
./scripts/test-hetzner.py test     # run highstate via salt-ssh (creates VM if needed)
./scripts/test-hetzner.py ssh      # ssh into VM as admin
./scripts/test-hetzner.py delete   # destroy VM

./scripts/test-oci.py create    # create OCI VM
./scripts/test-oci.py check     # apply single state (fast smoke test, creates VM if needed)
./scripts/test-oci.py test      # run highstate via salt-ssh
./scripts/test-oci.py ssh       # ssh into VM as admin
./scripts/test-oci.py delete    # terminate VM
```

The roster (`salt/roster`) is written dynamically at runtime by each test runner and gitignored.

## Authentication Policy

- Users have no passwords (locked). Authentication is SSH key only.
- Only root has a password (for console recovery).
- sudo is NOPASSWD for authorized users. su is restricted to the sudo group.

## File Conventions

- LF line endings enforced via .gitattributes.
- APT sources use DEB822 format (.sources files, not .list).
- Secrets are SOPS-encrypted with age in `salt/pillar/secrets/hosts/<group>.sls.enc`.
- Edit secrets via: `scripts/sops.py edit salt/pillar/secrets/hosts/test_docker.sls.enc`
- Decrypted `.sls` files are gitignored and cleaned up automatically after salt-ssh runs.
