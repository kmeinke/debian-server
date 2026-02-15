# server-salt

Masterless SaltStack configuration for a Debian Bookworm server. Tested via Docker.

## conversation rules
- do not imply i want implement change just because i ask you a yes or no question.

## Project Structure

```
salt/states/       Salt state definitions, organized by function
salt/states/*/files/  Config file templates managed by states
salt/pillar/       Pillar data (configuration values)
salt/minion.d/     Masterless minion config
scripts/test.sh    Docker-based test runner
secrets/           Not committed (.gitignore)
```

## Salt Conventions

- States are pillar-driven. Use `salt['pillar.get']('key', 'default')` with sensible defaults.
- Config file templates live in `salt/states/<category>/files/` and use Jinja2 templating.
- State dependencies: packages first, then files, then services. Use `require`, `watch`, and `watch_in`.
- Docker compatibility: guard systemd-dependent states with `onlyif: test -d /run/systemd/system`.
- State naming: dot notation matching directory structure (e.g., `security.firewall`).
- One pillar file per domain (network.sls, users.sls, ssh.sls, etc.).

## Testing

Docker container boots with systemd as PID 1 (privileged mode), allowing full testing of services, timers, and hostname.

```bash
./scripts/test.sh build   # remove container and rebuild image
./scripts/test.sh shell   # start container, open shell
./scripts/test.sh test    # start container, run highstate (default)
./scripts/test.sh clean   # remove container, image, and volumes
```

Container auto-starts and auto-builds if not already running. States and pillars are mounted read-only.

## File Conventions

- LF line endings enforced via .gitattributes.
- APT sources use DEB822 format (.sources files, not .list).
- Secrets go in /secrets/ (gitignored).
