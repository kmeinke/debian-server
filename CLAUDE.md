# server-salt

SaltStack configuration for a Debian Bookworm server, managed via salt-ssh. Tested via Docker.

## Conversation Rules
- Do not imply I want to implement a change just because I ask a yes or no question.
- Never commit without asking me explicitly first.
- Before committing, review all changes and propose how to split them into logical commits.
- Before committing, ensure documentation (README.md, CLAUDE.md) is updated to reflect the changes.
- When researching security guidelines (CIS, ANSSI, etc.), check `reference/` for PDF documents before searching the web.

## Project Structure

```
salt/states/          Salt state definitions, organized by function
salt/states/*/files/  Config file templates managed by states
salt/pillar/          Pillar data (configuration values)
salt/pillar/secrets/  SOPS-encrypted secrets (*.sls.enc)
salt/master           salt-ssh config (file_roots, pillar_roots)
salt/roster           salt-ssh target host definitions
scripts/test.py       Docker-based test runner (salt-ssh)
scripts/sops.py       SOPS helper (import/export/edit/rotate)
reference/            CIS benchmarks, ANSSI guides (PDFs)
```

## Salt Conventions

- States are pillar-driven. Use `salt['pillar.get']('key', 'default')` with sensible defaults.
- Config file templates live in `salt/states/<category>/files/` and use Jinja2 templating.
- State dependencies: packages first, then files, then services. Use `require`, `watch`, and `watch_in`.
- Docker compatibility: guard systemd-dependent states with `onlyif: test -d /run/systemd/system`.
- State naming: dot notation matching directory structure (e.g., `security.firewall`).
- One pillar file per domain (network.sls, users.sls, ssh.sls, logging.sls, etc.).

## Testing

Docker container boots with systemd as PID 1 (privileged mode), running sshd. salt-ssh connects from WSL to apply states.

```bash
./scripts/test.py build   # remove container and rebuild image
./scripts/test.py shell   # start container, open shell
./scripts/test.py test    # start container, run highstate via salt-ssh
./scripts/test.py clean   # remove container, image, and volumes
```

Container auto-starts and auto-builds if not already running. salt-ssh connects on port 2222 as admin user with sudo.

## Authentication Policy

- Users have no passwords (locked). Authentication is SSH key only.
- Only root has a password (for console recovery).
- sudo is NOPASSWD for authorized users. su is restricted to the sudo group.

## File Conventions

- LF line endings enforced via .gitattributes.
- APT sources use DEB822 format (.sources files, not .list).
- Secrets are SOPS-encrypted with age in `salt/pillar/secrets/*.sls.enc`.
- Edit secrets via: `scripts/sops.py edit salt/pillar/secrets/server.sls.enc`
- Decrypted `.sls` files are gitignored and cleaned up automatically after salt-ssh runs.
